import os
import secrets
import string
import smtplib
import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import List, Optional
from enum import Enum
import pytz # Import pytz for timezone handling
import requests
import json
import hmac
import httpx
import pyotp  # Added for 2FA support
from collections import defaultdict
import time
import logging
import random
import asyncio
import uuid
import cloudinary
import cloudinary.uploader

# FastAPI and related imports
from fastapi import FastAPI, Depends, WebSocket, HTTPException, status, Request, Query, Body, Form, UploadFile, File
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Header
from fastapi.responses import RedirectResponse
from fastapi_utils.tasks import repeat_every
from slowapi import Limiter, _rate_limit_exceeded_handler  # Added rate limiting
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles

# Database imports
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, UniqueConstraint, create_engine, and_, or_, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.types import DECIMAL as SQLDecimal
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from fastapi import APIRouter  # Needed to create a router
from sqlalchemy import exists

# Authentication imports
from passlib.context import CryptContext
from jose import JWTError, jwt

# Email imports
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# Pydantic imports
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from jinja2 import Environment, FileSystemLoader

from user_agents import parse

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================
required_env_vars = [
    "DATABASE_URL",
    "SECRET_KEY",
    "FROM_EMAIL",
    "FROM_NAME",
    "BASE_URL",
    "FRONTEND_BASE_URL",
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
    "ADMIN_PIN",
    "APP_SECRET",
    "EMAIL_API_URL",        # URL of the serverless email function
    "EMAIL_API_AUTH_TOKEN"  # Token to authorize backend requests
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")


# Database & Security
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
RATE_LIMIT_STORAGE = defaultdict(list)

# Email Configuration (Serverless API)
EMAIL_API_URL = os.getenv("EMAIL_API_URL")  # URL of your serverless email function
EMAIL_API_AUTH_TOKEN = os.getenv("EMAIL_API_AUTH_TOKEN")  # Token to authorize backend requests
FROM_EMAIL = os.getenv("FROM_EMAIL")  # Default sender email
FROM_NAME = os.getenv("FROM_NAME")    # Default sender name

# Base URLs
BASE_URL = os.getenv("BASE_URL")  # Backend URL
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL")  # Frontend URL

# App Secrets
APP_SECRET = os.getenv("APP_SECRET")

# Admin Credentials
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_PIN = os.getenv("ADMIN_PIN")

BTC_API_URL = "https://api.coinpaprika.com/v1/tickers/btc-bitcoin"
ETH_API_URL = "https://api.coinpaprika.com/v1/tickers/eth-ethereum"

# =============================================================================
# DATABASE SETUP
# =============================================================================

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)


logger = logging.getLogger("uvicorn.error")

# =============================================================================
# ENUMS
# =============================================================================

class UserStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"

class WithdrawalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"

class CryptoType(str, Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"

class DepositStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"  # <-- add this
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

# =============================================================================
# DATABASE MODELS (Ordered to resolve forward references)
# =============================================================================

class AdminSettings(Base):
    __tablename__ = "admin_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    bitcoin_rate_usd = Column(SQLDecimal(10, 2), default=50000.00)  # Bitcoin price in USD
    ethereum_rate_usd = Column(SQLDecimal(10, 2), default=3000.00)  # Ethereum price in USD
    global_mining_rate = Column(Float, default=0.70)  # Default 70% mining rate
    bitcoin_deposit_qr = Column(String, nullable=True)  # QR code image path
    ethereum_deposit_qr = Column(String, nullable=True)  # QR code image path
    bitcoin_wallet_address = Column(String, nullable=True)
    ethereum_wallet_address = Column(String, nullable=True)

    # Referral reward settings (percentage-based)
    referral_reward_enabled = Column(Boolean, default=True)
    referral_reward_type = Column(String, default="bitcoin")  # bitcoin or ethereum
    referrer_reward_percent = Column(Float, default=5.0)  # % reward for the person who referred

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(10), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    pin_hash = Column(String, nullable=False)
    status = Column(String, default=UserStatus.PENDING)
    is_admin = Column(Boolean, default=False)
    is_agent = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    usd_balance = Column(SQLDecimal(10, 2), default=0)
    referral_code = Column(String, unique=True, nullable=True)
    referred_by_code = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False)
    birthday_day = Column(Integer, nullable=True)
    birthday_month = Column(Integer, nullable=True)
    birthday_year = Column(Integer, nullable=True)
    gender = Column(String(1), nullable=True)
    user_country_code = Column(String(2), nullable=True)
    zip_code = Column(String, nullable=True)
    bitcoin_wallet = Column(String, nullable=True)
    ethereum_wallet = Column(String, nullable=True)
    bitcoin_balance = Column(SQLDecimal(18, 8), default=0)
    ethereum_balance = Column(SQLDecimal(18, 8), default=0)
    personal_mining_rate = Column(Float, nullable=True)  # Personal rate set by admin
    two_fa_secret = Column(String, nullable=True)
    two_fa_enabled = Column(Boolean, default=False)
    account_locked = Column(Boolean, default=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_suspended = Column(Boolean, default=False)
    mining_paused = Column(Boolean, default=False)
    withdrawal_suspended = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    devices = relationship("UserDevice", back_populates="user")
    sent_transfers = relationship("CryptoTransfer", foreign_keys="CryptoTransfer.from_user_id", back_populates="from_user")
    received_transfers = relationship("CryptoTransfer", foreign_keys="CryptoTransfer.to_user_id", back_populates="to_user")
    withdrawals = relationship("Withdrawal", back_populates="user", foreign_keys="Withdrawal.user_id")
    approvals = relationship("UserApproval", back_populates="user", foreign_keys="UserApproval.user_id")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    deposits = relationship("CryptoDeposit", back_populates="user", foreign_keys="CryptoDeposit.user_id")
    confirmed_deposits = relationship("CryptoDeposit", back_populates="confirmed_by_user", foreign_keys="CryptoDeposit.confirmed_by")
    mining_sessions = relationship("MiningSession", back_populates="user")
    admin_logs = relationship("AdminActionLog", back_populates="admin")

class ReferralReward(Base):
    __tablename__ = "referral_rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_type = Column(String, nullable=False)  # bitcoin or ethereum
    reward_amount = Column(SQLDecimal(18, 8), nullable=False)
    status = Column(String, default="pending")  # pending, paid
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    referrer = relationship("User", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])

class EmailNotification(Base):
    __tablename__ = "email_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    template_type = Column(String, nullable=False)  # deposit_confirmed, login_alert, etc.
    status = Column(String, default="pending")  # pending, sent, failed
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class TransactionHistory(Base):
    __tablename__ = "transaction_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(String, nullable=False)  # deposit, withdrawal, transfer, mining, referral_reward
    crypto_type = Column(String, nullable=True)  # bitcoin, ethereum
    amount = Column(SQLDecimal(18, 8), nullable=False)
    description = Column(String, nullable=False)
    reference_id = Column(String, nullable=True)  # Reference to related record
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=True)  # user, deposit, settings, etc.
    target_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    admin = relationship("User")


class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)             # e.g. "Deleted User", "Approved Agent"
    target_type = Column(String, nullable=True)         # e.g. "User", "Survey", "Reward"
    target_id = Column(String, nullable=True)           # ID of the affected entity
    details = Column(String, nullable=True)             # Extra info
    ip_address = Column(String, nullable=True)          # IP of the admin
    user_agent = Column(String, nullable=True)          # ✅ Browser/device info
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to User
    admin = relationship("User", back_populates="admin_logs")

class CryptoDeposit(Base):
    __tablename__ = "crypto_deposits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_type = Column(String, nullable=False)  # bitcoin or ethereum
    amount = Column(SQLDecimal(18, 8), nullable=False)  # crypto amount
    usd_amount = Column(SQLDecimal(18, 2), nullable=False)  # USD equivalent
    status = Column(String, default=DepositStatus.PENDING)
    transaction_hash = Column(String, nullable=True)
    evidence_url = Column(String, nullable=True)  # URL to uploaded evidence
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="deposits", foreign_keys=[user_id])
    confirmed_by_user = relationship("User", back_populates="confirmed_deposits", foreign_keys=[confirmed_by])
    
class MiningRate(Base):
    __tablename__ = "mining_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    crypto_type = Column(String, nullable=False)  # bitcoin or ethereum
    global_rate = Column(Float, nullable=False)  # Global mining rate percentage
    duration_hours = Column(Integer, default=24)  # Duration for the rate
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DepositQRCode(Base):
    __tablename__ = "deposit_qr_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    crypto_type = Column(String, nullable=False)  # bitcoin or ethereum
    qr_code_url = Column(String, nullable=False)  # URL to uploaded QR code image
    wallet_address = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserDevice(Base):
    __tablename__ = "user_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_fingerprint = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="devices")
    
    __table_args__ = (UniqueConstraint('user_id', 'device_fingerprint', name='unique_user_device'),)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., "USER_LOGIN", "DEPOSIT_MADE"
    details = Column(Text)
    ip_address = Column(String)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")

class SecurityLog(Base):
    __tablename__ = "security_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String, nullable=False)  # failed_login, successful_login, 2fa_enabled, etc.
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FraudFlag(Base):
    __tablename__ = "fraud_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="fraud_flag")

class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    otp_code = Column(String, nullable=False)
    purpose = Column(String, nullable=False) # signup, password_reset, pin_reset
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CryptoTransfer(Base):
    __tablename__ = "crypto_transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"))  # back to integer FK
    to_user_id = Column(Integer, ForeignKey("users.id"))    # back to integer FK
    crypto_type = Column(String, nullable=False)  # Bitcoin or Ethereum
    amount = Column(SQLDecimal(18, 8), nullable=False)
    usd_amount = Column(SQLDecimal(18, 2), nullable=False)  # store equivalent in USD
    transaction_hash = Column(String, unique=True, index=True, nullable=False)  # unique reference
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_transfers")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_transfers")
    
class MiningSession(Base):
    __tablename__ = "mining_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deposit_id = Column(Integer, ForeignKey("crypto_deposits.id"), nullable=False)
    crypto_type = Column(String, nullable=False)  # bitcoin or ethereum
    deposited_amount = Column(SQLDecimal(18, 8), nullable=False)
    mining_rate = Column(Float, nullable=False)  # Rate used for this session
    mined_amount = Column(SQLDecimal(18, 8), default=0)
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paused_at = Column(DateTime(timezone=True), nullable=True)
    last_mined = Column(DateTime(timezone=True), nullable=True, server_default=func.now())

    user = relationship("User", back_populates="mining_sessions")

class Withdrawal(Base):
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    crypto_type = Column(String, nullable=False)
    amount = Column(SQLDecimal(18, 8), nullable=False)
    wallet_address = Column(String, nullable=False)
    status = Column(String, default=WithdrawalStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    transaction_hash = Column(String, nullable=True)  # optional, default None
    
    user = relationship("User", back_populates="withdrawals")

class UserApproval(Base):
    __tablename__ = "user_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", foreign_keys=[user_id], back_populates="approvals")


class EmailService:
    def __init__(self):
        self.api_url = EMAIL_API_URL  # e.g., your serverless email API
        self.api_token = EMAIL_API_AUTH_TOKEN  # Bearer token
        self.from_email = FROM_EMAIL
        self.from_name = FROM_NAME

    @staticmethod
    async def upload_to_cloud(file: UploadFile, public_id: str = None) -> str:
        """Uploads a file to Cloudinary and returns the secure URL."""
        file_bytes = await file.read()
        result = cloudinary.uploader.upload(
            file_bytes,
            resource_type="auto",
            public_id=public_id,
            overwrite=True
        )
        return result.get("secure_url")

    def _prepare_email_body(self, body: str, attachment_url: str = None):
        """Attach evidence/attachment if provided."""
        if attachment_url:
            body += f"<br><br>📎 Attachment: <a href='{attachment_url}' target='_blank'>{attachment_url}</a>"
        return body

    # === Original engine: main email sender ===
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        attachment_url: str = None,
        text: str = None
    ) -> bool:
        """
        Send email through serverless API.
        """
        try:
            body = self._prepare_email_body(body, attachment_url)
            payload = {
                "to": to_email,
                "subject": subject,
                "html": body,
                "text": text or ""
            }
            headers = {"Authorization": f"Bearer {self.api_token}"}

            response = httpx.post(self.api_url, json=payload, headers=headers, timeout=15)

            if response.status_code == 200:
                return True
            else:
                print(f"Failed to send email: {response.text}")
                return False
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    # === New general-purpose template-based sender ===
    def send_template_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_vars: dict = None,
        attachment_url: str = None
    ) -> bool:
        """
        Send any Jinja2 template-based email alert.
        Can be used for login alerts, deposit approval, withdrawal, transfers, password/pin changes, etc.
        """
        try:
            template_vars = template_vars or {}
            template = env.get_template(template_name)
            body = template.render(**template_vars)
            return self.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=True,
                attachment_url=attachment_url
            )
        except Exception as e:
            print(f"Failed to send template email: {e}")
            return False

    # === OTP email (uses template engine) ===
    def send_otp_email(self, to_email: str, otp_code: str, purpose: str):
        subject = f"Your OTP Code for {purpose.replace('_', ' ').title()}"
        return self.send_template_email(
            to_email=to_email,
            subject=subject,
            template_name="otp_email.html",
            template_vars={"otp_code": otp_code, "purpose": purpose}
        )

    # === Agent approval email (uses template engine) ===
    def send_agent_approval_email(
        self, agent_email: str, user_name: str, user_email: str, approval_token: str
    ):
        approve_url = f"{BASE_URL}/api/agent/approve/{approval_token}?action=approve"
        reject_url = f"{BASE_URL}/api/agent/approve/{approval_token}?action=reject"

        subject = "New User Approval Request"
        template_vars = {
            "user_name": user_name,
            "user_email": user_email,
            "approve_url": approve_url,
            "reject_url": reject_url
        }
        return self.send_template_email(
            to_email=agent_email,
            subject=subject,
            template_name="agent_approval.html",
            template_vars=template_vars
        )


# Initialize email service
email_service = EmailService()


# =============================================================================
# UTILITY FUNCTIONS (Defined before use)
# =============================================================================

def generate_user_id():
    """Generate a unique 10-digit user ID"""
    # Generate 10-digit number (no leading zero)
    return ''.join([str(random.randint(1, 9))] + [str(random.randint(0, 9)) for _ in range(9)])

def generate_otp():
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def generate_referral_code():
    """Generate a unique referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_2fa_secret():
    """Generate a new 2FA secret key"""
    return pyotp.random_base32()

def verify_2fa_token(secret: str, token: str) -> bool:
    """Verify 2FA token"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)

def get_2fa_qr_url(secret: str, email: str, issuer: str = "Crypto Mining Platform") -> str:
    """Generate QR code URL for 2FA setup"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(email, issuer_name=issuer)

def check_rate_limit(identifier: str, max_requests: int, window_seconds: int) -> bool:
    """Check if request is within rate limit"""
    now = time.time()
    requests = RATE_LIMIT_STORAGE[identifier]
    
    # Remove old requests outside the window
    RATE_LIMIT_STORAGE[identifier] = [req_time for req_time in requests if now - req_time < window_seconds]
    
    # Check if under limit
    if len(RATE_LIMIT_STORAGE[identifier]) < max_requests:
        RATE_LIMIT_STORAGE[identifier].append(now)
        return True
    return False

def log_security_event(db: Session, user_id: Optional[int], event_type: str, details: str, ip_address: str):
    """Log security-related events"""
    security_log = SecurityLog(
        user_id=user_id,
        event_type=event_type,
        details=details,
        ip_address=ip_address
    )
    db.add(security_log)
    db.commit()

def is_account_locked(db: Session, email: str) -> bool:
    """Check if account is locked due to failed login attempts"""
    lockout_time = datetime.utcnow() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    
    failed_attempts = db.query(SecurityLog).filter(
        SecurityLog.event_type == "failed_login",
        SecurityLog.details.contains(email),
        SecurityLog.created_at > lockout_time
    ).count()
    
    return failed_attempts >= MAX_LOGIN_ATTEMPTS

def get_admin_settings(db: Session):
    """Get or create admin settings"""
    settings = db.query(AdminSettings).first()
    if not settings:
        settings = AdminSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def calculate_usd_values(user: User, admin_settings: AdminSettings):
    """Calculate USD values for user's crypto balances"""
    bitcoin_balance = user.bitcoin_balance or 0
    ethereum_balance = user.ethereum_balance or 0

    bitcoin_balance_usd = bitcoin_balance * admin_settings.bitcoin_rate_usd
    ethereum_balance_usd = ethereum_balance * admin_settings.ethereum_rate_usd
    total_balance_usd = bitcoin_balance_usd + ethereum_balance_usd
    
    return {
        "bitcoin_balance_usd": bitcoin_balance_usd,
        "ethereum_balance_usd": ethereum_balance_usd,
        "total_balance_usd": total_balance_usd
    }

def log_activity(db: Session, user_id: int, action: str, details: str = None, ip_address: str = None):
    """Log user activity"""
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.add(activity)
    db.commit()

def log_transaction(db: Session, user_id: int, transaction_type: str, crypto_type: str, amount: Decimal, description: str, reference_id: str = None):
    """Log transaction history"""
    transaction = TransactionHistory(
        user_id=user_id,
        transaction_type=transaction_type,
        crypto_type=crypto_type,
        amount=amount,
        description=description,
        reference_id=reference_id
    )
    db.add(transaction)
    db.commit()


def process_referral_rewards(db: Session, new_user: User, deposit_amount: float, deposit_type: str):
    """
    Process referral rewards when a new user makes a deposit using a referral code.
    Rewards are given only to the referrer based on admin settings.
    """

    if not new_user.referred_by_code:
        return

    referrer = db.query(User).filter(User.referral_code == new_user.referred_by_code).first()
    if not referrer:
        return

    settings = get_admin_settings(db)
    if not settings.referral_reward_enabled:
        return

    # ✅ Ensure both deposit_amount and reward_percent are Decimal
    try:
        deposit_amount_dec = Decimal(deposit_amount)
        reward_percent = Decimal(settings.referrer_reward_percent) / Decimal(100)
        reward_amount = deposit_amount_dec * reward_percent
    except (InvalidOperation, TypeError) as e:
        logger.error(f"Failed to calculate referral reward: {e}")
        return

    # Create referral reward record
    referrer_reward = ReferralReward(
        referrer_id=referrer.id,
        referred_id=new_user.id,
        reward_type=deposit_type,
        reward_amount=reward_amount,
        status="paid"
    )
    db.add(referrer_reward)

    # Add reward to referrer's balance
    if deposit_type == "bitcoin":
        referrer.bitcoin_balance += reward_amount
    elif deposit_type == "ethereum":
        referrer.ethereum_balance += reward_amount
    else:
        logger.error(f"Unsupported crypto type: {deposit_type}")
        return

    # Log transaction
    try:
        log_transaction(
            db=db,
            user_id=referrer.id,
            transaction_type="referral_reward",
            crypto_type=deposit_type,
            amount=reward_amount,
            description=f"Referral reward for referring user {new_user.id}"
        )
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log referral reward transaction: {e}")
        db.rollback()
        return

    # Notify referrer
    try:
        template_vars = {
            "referrer_name": referrer.name or referrer.email,
            "new_user_email": new_user.email,
            "crypto_type": deposit_type,
            "reward_amount": reward_amount,
            "percent": settings.referrer_reward_percent,
        }
        email_service.send_template_email(
            to_email=referrer.email,
            subject="🎉 Referral Reward Credited",
            template_name="referral_reward_alert.html",
            template_vars=template_vars
        )
    except Exception as e:
        logger.error(f"Failed to send referral reward email to referrer {referrer.email}: {e}")

# =============================================================================
# AUTHENTICATION
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def get_user_from_ws_token(token: Optional[str], db: Session) -> User:
    """
    Decode JWT token from WebSocket query param (plain string) and return User object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_exception

    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def log_admin_action(
    db,
    admin_id: int,
    action: str,
    target_type: str = None,
    target_id: str = None,
    details: str = None,
    ip_address: str = None,
    user_agent: str = None,
    request: Request = None  # new optional param
):
    """
    Logs an action performed by an admin user.
    """
    try:
        if request:
            ip_address = request.client.host
            user_agent = request.headers.get("user-agent")

        log_entry = AdminActionLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Admin Action Log Error] {str(e)}")

def get_location_from_ip(ip: str) -> str:
    try:
        response = httpx.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            country = data.get("country_name", "")
            return country or "Unknown"
    except Exception as e:
        print(f"Failed to get location: {e}")
    return "Unknown"


def get_readable_device(user_agent: str) -> str:
    """
    Parse a full user-agent string into a minimal readable format.
    Example output: "Android Mobile • Chrome"
    """
    if not user_agent:
        return "Unknown Device"
    
    ua = parse(user_agent)
    
    device = ""
    
    # Determine device type
    if ua.is_mobile:
        device = "Mobile"
    elif ua.is_tablet:
        device = "Tablet"
    elif ua.is_pc:
        device = "PC"
    elif ua.is_bot:
        device = "Bot"
    else:
        device = "Unknown Device"
    
    # Browser name
    browser = ua.browser.family or "Unknown Browser"
    
    # OS name
    os_name = ua.os.family or "Unknown OS"
    
    return f"{os_name} {device} • {browser}"

# =============================================================================
# PYDANTIC SCHEMAS (Ordered to resolve forward references)
# =============================================================================

# Base schemas first
class BasicUserInfo(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str
    pin: str
    referral_code: Optional[str] = None
    device_fingerprint: str
    ip_address: str
    user_agent: Optional[str] = None
    birthday_day: Optional[int] = None
    birthday_month: Optional[int] = None
    birthday_year: Optional[int] = None
    gender: Optional[str] = None
    user_country_code: Optional[str] = None
    zip_code: Optional[str] = None
    bitcoin_wallet: Optional[str] = None
    ethereum_wallet: Optional[str] = None

class UserResponse(UserBase):
    id: int
    user_id: str
    name: str
    status: UserStatus
    is_admin: bool
    is_agent: bool
    is_flagged: bool
    usd_balance: Decimal
    bitcoin_balance: Decimal
    ethereum_balance: Decimal
    bitcoin_balance_usd: Optional[Decimal] = None
    ethereum_balance_usd: Optional[Decimal] = None
    total_balance_usd: Optional[Decimal] = None
    bitcoin_wallet: Optional[str] = None
    ethereum_wallet: Optional[str] = None
    personal_mining_rate: Optional[float] = None
    referral_code: Optional[str]
    email_verified: bool
    birthday_day: Optional[int] = None
    birthday_month: Optional[int] = None
    birthday_year: Optional[int] = None
    gender: Optional[str] = None
    user_country_code: Optional[str] = None
    zip_code: Optional[str] = None
    created_at: datetime
    referred_users_count: Optional[int] = None

    class Config:
        from_attributes = True
        
        
# Authentication Schemas
class UserLogin(BaseModel):
    email: str
    password: str
    device_fingerprint: str = None
    ip_address: str = None
    user_agent: str = None


class UserPinVerify(BaseModel):
    pin: str

# Password and PIN Schemas
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PinChangeRequest(BaseModel):
    current_pin: str
    new_pin: str

class PasswordResetRequest(BaseModel):
    email: str
    otp_code: str
    new_password: str

class PinResetRequest(BaseModel):
    email: str
    otp_code: str
    new_pin: str

# 2FA Schemas
class TwoFASetupResponse(BaseModel):
    secret: str
    qr_code_url: str
    backup_codes: List[str]

class TwoFAVerifyRequest(BaseModel):
    token: str

class TwoFAStatusResponse(BaseModel):
    enabled: bool
    backup_codes_remaining: Optional[int] = None

class SecuritySettingsResponse(BaseModel):
    two_fa_enabled: bool
    account_locked: bool
    failed_login_attempts: int
    last_login: Optional[datetime] = None

# OTP Schemas
class OTPRequest(BaseModel):
    email: EmailStr
    purpose: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str
    purpose: str

# Crypto Transfer Schemas
class CryptoTransferCreate(BaseModel):
    to_email: Optional[EmailStr] = None
    to_user_id: Optional[str] = None  # <-- now matches the DB type
    crypto_type: CryptoType
    amount: Decimal

    @field_validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @model_validator(mode="after")
    def either_email_or_user_id(self):
        if not self.to_email and not self.to_user_id:
            raise ValueError('Either to_email or to_user_id must be provided')
        if self.to_email and self.to_user_id:
            raise ValueError('Provide either to_email or to_user_id, not both')
        return self


class CryptoTransferResponse(BaseModel):
    id: int
    crypto_type: str
    amount: float
    usd_amount: float
    transaction_hash: str
    created_at: str
    from_user: BasicUserInfo
    to_user: BasicUserInfo
    direction: Optional[str] = None  # "sent" or "received", optional

    class Config:
        from_attributes = True

# Deposit Schemas
class DepositCreate(BaseModel):
    crypto_type: CryptoType
    amount: Optional[Decimal] = None  # crypto amount
    usd_amount: Optional[Decimal] = None  # USD amount
    transaction_hash: Optional[str] = None

class DepositEvidenceUpload(BaseModel):
    deposit_id: int
    evidence_file: str  # base64 encoded image or file URL

class DepositResponse(BaseModel):
    id: int
    crypto_type: str
    amount: Decimal
    usd_amount: Decimal
    status: str
    qr_code_url: str
    wallet_address: str

    class Config:
        from_attributes = True

# Withdrawal Schemas
class WithdrawalCreate(BaseModel):
    crypto_type: CryptoType
    amount: Decimal
    wallet_address: str
    
    @field_validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class WithdrawalResponse(BaseModel):
    id: int
    crypto_type: str
    amount: float
    usd_amount: float
    wallet_address: str
    status: str
    transaction_hash: Optional[str] = None
    created_at: str  # ISO formatted datetime

    class Config:
        from_attributes = True

class AdminWithdrawalResponse(BaseModel):
    id: int
    crypto_type: str
    amount: Decimal
    status: WithdrawalStatus
    created_at: datetime
    user_id: int
    user_email: str
    wallet_address: str

    class Config:
        from_attributes = True

# Mining Schemas
class MiningRateCreate(BaseModel):
    crypto_type: CryptoType
    global_rate: float
    duration_hours: int = 24

class MiningRateResponse(BaseModel):
    id: int
    crypto_type: str
    global_rate: float
    duration_hours: int
    is_active: bool

    class Config:
        from_attributes = True

# QR Code Schemas
class QRCodeCreate(BaseModel):
    crypto_type: CryptoType
    qr_code_url: str
    wallet_address: str

class QRCodeResponse(BaseModel):
    id: int
    crypto_type: str
    qr_code_url: str
    wallet_address: str
    is_active: bool

    class Config:
        from_attributes = True

# Admin Schemas
class UserStatusUpdate(BaseModel):
    status: UserStatus

class AgentAssignment(BaseModel):
    user_id: int
    is_agent: bool

class SystemSettingUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class BulkUserStatusUpdate(BaseModel):
    user_ids: List[int]
    status: UserStatus

class AdminSettingsResponse(BaseModel):
    bitcoin_rate_usd: Decimal
    ethereum_rate_usd: Decimal
    global_mining_rate: float
    bitcoin_deposit_qr: Optional[str] = None
    ethereum_deposit_qr: Optional[str] = None
    bitcoin_wallet_address: Optional[str] = None
    ethereum_wallet_address: Optional[str] = None
    referral_reward_enabled: bool
    referral_reward_type: str
    referral_reward_amount: Decimal
    referrer_reward_amount: Decimal

class AdminSettingsUpdate(BaseModel):
    bitcoin_rate_usd: Optional[Decimal] = None
    ethereum_rate_usd: Optional[Decimal] = None
    global_mining_rate: Optional[float] = None
    bitcoin_wallet_address: Optional[str] = None
    ethereum_wallet_address: Optional[str] = None
    referral_reward_enabled: Optional[bool] = None
    referral_reward_type: Optional[str] = None
    referral_reward_amount: Optional[Decimal] = None
    referrer_reward_amount: Optional[Decimal] = None

class AdminCryptoTransferRequest(BaseModel):
    from_user_email: Optional[EmailStr] = None
    to_user_email: EmailStr
    crypto_type: CryptoType
    amount: Decimal

    @field_validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

# Transaction and History Schemas
class TransactionHistoryResponse(BaseModel):
    id: int
    transaction_type: str
    crypto_type: Optional[str] = None
    amount: Decimal
    description: str
    reference_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class TransactionFilter(BaseModel):
    transaction_type: Optional[str] = None
    crypto_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

class AdminAuditLogResponse(BaseModel):
    id: int
    admin_id: int
    admin_name: str
    admin_email: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Referral Schemas
class ReferralRewardResponse(BaseModel):
    id: int
    referrer_id: int
    referred_id: int
    reward_type: str
    reward_amount: Decimal
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None

# Fraud and Security Schemas
class FraudFlagResponse(BaseModel):
    user: BasicUserInfo
    reason: str
    created_at: datetime

    class Config:
        orm_mode = True

class FraudRuleUpdate(BaseModel):
    rule_key: str
    limit_value: int
    action: str
    description: Optional[str] = None

class FraudRulePatch(BaseModel):
    limit_value: int
    action: str

# Dashboard and Analytics Schemas
class DashboardStats(BaseModel):
    usd_balance: Decimal
    bitcoin_balance: Decimal
    ethereum_balance: Decimal
    active_mining_sessions: int
    total_deposits: int
    pending_withdrawals: int
    is_flagged: bool

class AdminDashboardStats(BaseModel):
    total_users: int
    total_deposits: int
    total_crypto_distributed: Decimal
    pending_withdrawals: int
    active_mining_sessions: int

class TransferHistory(BaseModel):
    transfers: List[CryptoTransferResponse]

class UserAnalyticsResponse(BaseModel):
    portfolio_overview: dict
    mining_performance: dict
    earnings_history: dict
    transaction_analytics: dict
    referral_performance: dict
    growth_metrics: dict

class MiningPerformanceData(BaseModel):
    daily_earnings: List[dict]
    weekly_summary: dict
    monthly_trends: dict
    efficiency_metrics: dict

class PortfolioAnalytics(BaseModel):
    current_value: dict
    historical_performance: List[dict]
    asset_allocation: dict
    growth_rate: dict

class DepositConvertRequest(BaseModel):
    crypto_type: CryptoType
    amount: Optional[Decimal] = None
    usd_amount: Optional[Decimal] = None

class EarningsBreakdown(BaseModel):
    mining_earnings: Decimal
    referral_earnings: Decimal
    total_earnings: Decimal
    earnings_by_period: List[dict]

# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================

env = Environment(loader=FileSystemLoader('template'))

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Crypto Mining API",
    description="Crypto Mining Platform API Backend",
    version="1.0.0",
    docs_url=None,       # Disable Swagger UI (/docs)
    redoc_url=None,      # Disable ReDoc (/redoc)
    openapi_url=None     # Disable OpenAPI schema (/openapi.json)
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cryptomining.com",
        "https://api.cryptomining.com",
        "https://mining-frontend.netlify.app",
        "https://chainminer.onrender.com",
        "https://chainminer.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# =============================================================================
# AUTHENTICATION
# =============================================================================



# =============================================================================
# ENHANCED AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/api/login")
async def login_user(
    request: Request,
    user_login: UserLogin,  # Using the non-2FA schema
    db: Session = Depends(get_db)
):
    # 1️⃣ Fetch user
    user = db.query(User).filter(User.email == user_login.email).first()

    # 2️⃣ Log login attempt (default: failed until proven successful)
    login_attempt = LoginAttempt(
        email=user_login.email,
        ip_address=request.client.host,
        success=False,
        user_agent=request.headers.get("user-agent")
    )

    # 3️⃣ Verify credentials
    if not user or not verify_password(user_login.password, user.password_hash):
        log_security_event(
            db, user.id if user else None, "failed_login",
            f"Failed login attempt for {user_login.email}",
            request.client.host
        )
        db.add(login_attempt)
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # 4️⃣ Suspended account check
    if user.is_suspended:
        log_security_event(
            db, user.id, "suspended_login_attempt",
            f"Login attempt by suspended user {user.email}",
            request.client.host
        )
        db.add(login_attempt)
        db.commit()
        raise HTTPException(status_code=403, detail="Account suspended")

    # 5️⃣ Successful login
    login_attempt.success = True
    log_activity(
        db, user.id, "USER_LOGIN",
        f"User logged in from {request.client.host}",
        request.client.host
    )
    log_security_event(
        db, user.id, "successful_login",
        f"Successful login for {user.email}",
        request.client.host
    )

    db.add(login_attempt)
    db.commit()

    # 6️⃣ Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # 7️⃣ Return response
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@app.post("/api/register")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if hasattr(request, "client") else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown")

    try:
        # 1️⃣ Check if email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2️⃣ Hash password and PIN
        hashed_password = pwd_context.hash(user_data.password)
        hashed_pin = pwd_context.hash(user_data.pin)

        # 3️⃣ Always generate a new referral code for THIS user
        personal_referral_code = generate_referral_code()

        # 4️⃣ Generate a unique 10-digit user_id
        max_attempts = 10
        for _ in range(max_attempts):
            user_id = generate_user_id()
            if not db.query(User).filter(User.user_id == user_id).first():
                break
        else:
            raise HTTPException(status_code=500, detail="Failed to generate unique user ID")

        # 5️⃣ Create user instance
        new_user = User(
            user_id=user_id,
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            pin_hash=hashed_pin,
            referral_code=personal_referral_code,   # 👈 their own referral code
            birthday_day=user_data.birthday_day,
            birthday_month=user_data.birthday_month,
            birthday_year=user_data.birthday_year,
            gender=user_data.gender,
            user_country_code=user_data.user_country_code,
            zip_code=user_data.zip_code,
            bitcoin_wallet=user_data.bitcoin_wallet,
            ethereum_wallet=user_data.ethereum_wallet,
            created_at=datetime.utcnow()
        )

        # 6️⃣ Save user
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 7️⃣ If they entered a referral code → link to referrer (case-insensitive)
        if user_data.referral_code:
            referrer = (
                db.query(User)
                .filter(func.lower(User.referral_code) == user_data.referral_code.lower())
                .first()
            )
            if referrer:
                new_user.referred_by = referrer.id
                new_user.referred_by_code = referrer.referral_code  # new line
                db.commit()

                # 📩 Notify referrer
                try:
                    referral_template_vars = {
                        "referrer_name": referrer.name,
                        "new_user_name": new_user.name,
                        "new_user_email": new_user.email,
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    }
                    email_service.send_template_email(
                        to_email=referrer.email,
                        subject="📢 Someone used your referral code!",
                        template_name="referral_notification.html",
                        template_vars=referral_template_vars
                    )
                except Exception as e:
                    logger.error(f"Failed to send referral notification email: {e}")

                # 🛡️ Log referral usage
                log_security_event(
                    db,
                    referrer.id,
                    "referral_used",
                    f"{new_user.email} registered using {referrer.email}'s referral code",
                    ip_address
                )

        # 8️⃣ Log account creation
        log_security_event(
            db,
            new_user.id,
            "account_created",
            f"New account created for {new_user.email}",
            ip_address
        )

        # 9️⃣ Send registration email to new user
        try:
            template_vars = {
                "name": new_user.name,
                "email": new_user.email,
                "account_id": new_user.user_id,
                "referral_code": new_user.referral_code,  # their own new code
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": ip_address,
                "device_info": get_readable_device(user_agent)
            }
            email_service.send_template_email(
                to_email=new_user.email,
                subject="🎉 Welcome to CryptoMine!",
                template_name="registration_success.html",
                template_vars=template_vars
            )
        except Exception as e:
            logger.error(f"Failed to send registration email: {e}")

        # 🔟 Return response
        return {
            "message": "Account created successfully",
            "user_id": new_user.user_id,
            "email": new_user.email,
            "referral_code": new_user.referral_code
        }

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create account")
        

@app.post("/api/security/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup 2FA for user account"""
    if current_user.two_fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled")
    
    # Generate new secret
    secret = generate_2fa_secret()
    qr_url = get_2fa_qr_url(secret, current_user.email)
    
    # Generate backup codes
    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
    
    # Store secret temporarily (not enabled until verified)
    current_user.two_fa_secret = secret
    db.commit()
    
    log_security_event(
        db, current_user.id, "2fa_setup_initiated",
        "User initiated 2FA setup",
        "system"
    )
    
    return TwoFASetupResponse(
        secret=secret,
        qr_code_url=qr_url,
        backup_codes=backup_codes
    )

@app.post("/api/security/2fa/verify")
async def verify_2fa_setup(
    verify_request: TwoFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify and enable 2FA"""
    if not current_user.two_fa_secret:
        raise HTTPException(status_code=400, detail="2FA setup not initiated")
    
    if not verify_2fa_token(current_user.two_fa_secret, verify_request.token):
        raise HTTPException(status_code=400, detail="Invalid 2FA token")
    
    # Enable 2FA
    current_user.two_fa_enabled = True
    db.commit()
    
    log_security_event(
        db, current_user.id, "2fa_enabled",
        "User successfully enabled 2FA",
        "system"
    )
    
    return {"message": "2FA enabled successfully"}

@app.post("/api/security/2fa/disable")
async def disable_2fa(
    verify_request: TwoFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA"""
    if not current_user.two_fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    
    if not verify_2fa_token(current_user.two_fa_secret, verify_request.token):
        raise HTTPException(status_code=400, detail="Invalid 2FA token")
    
    # Disable 2FA
    current_user.two_fa_enabled = False
    current_user.two_fa_secret = None
    db.commit()
    
    log_security_event(
        db, current_user.id, "2fa_disabled",
        "User disabled 2FA",
        "system"
    )
    
    return {"message": "2FA disabled successfully"}

@app.get("/api/security/2fa/status", response_model=TwoFAStatusResponse)
async def get_2fa_status(
    current_user: User = Depends(get_current_user)
):
    """Get 2FA status"""
    return TwoFAStatusResponse(
        enabled=current_user.two_fa_enabled
    )

@app.get("/api/security/settings", response_model=SecuritySettingsResponse)
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user security settings"""
    # Get last successful login
    last_login = db.query(SecurityLog).filter(
        SecurityLog.user_id == current_user.id,
        SecurityLog.event_type == "successful_login"
    ).order_by(SecurityLog.created_at.desc()).first()
    
    return SecuritySettingsResponse(
        two_fa_enabled=current_user.two_fa_enabled,
        account_locked=current_user.account_locked,
        failed_login_attempts=current_user.failed_login_attempts,
        last_login=last_login.created_at if last_login else None
    )

@app.get("/api/admin/security/logs")
async def get_security_logs(
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    user_email: Optional[str] = None,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get security logs for admin"""
    query = db.query(SecurityLog).options(joinedload(SecurityLog.user))
    
    if event_type:
        query = query.filter(SecurityLog.event_type == event_type)
    
    if user_email:
        query = query.join(User).filter(User.email.ilike(f"%{user_email}%"))
    
    logs = query.order_by(SecurityLog.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return [
        {
            "id": log.id,
            "user_email": log.user.email if log.user else "Unknown",
            "event_type": log.event_type,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        }
        for log in logs
    ]

@app.post("/api/admin/security/unlock-account")
async def unlock_user_account(
    user_email: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Unlock a user account"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.account_locked = False
    user.locked_until = None
    user.failed_login_attempts = 0
    
    log_security_event(
        db, user.id, "account_unlocked",
        f"Account unlocked by admin {admin_user.email}",
        "admin"
    )
    
    db.commit()
    return {"message": f"Account unlocked for {user_email}"}

@app.get("/api/admin/security/stats")
async def get_security_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get security statistics"""
    # Get stats for last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    failed_logins = db.query(SecurityLog).filter(
        SecurityLog.event_type == "failed_login",
        SecurityLog.created_at >= yesterday
    ).count()
    
    successful_logins = db.query(SecurityLog).filter(
        SecurityLog.event_type == "successful_login",
        SecurityLog.created_at >= yesterday
    ).count()
    
    locked_accounts = db.query(User).filter(User.account_locked == True).count()
    
    users_with_2fa = db.query(User).filter(User.two_fa_enabled == True).count()
    total_users = db.query(User).count()
    
    return {
        "last_24_hours": {
            "failed_logins": failed_logins,
            "successful_logins": successful_logins
        },
        "current_status": {
            "locked_accounts": locked_accounts,
            "users_with_2fa": users_with_2fa,
            "total_users": total_users,
            "2fa_adoption_rate": (users_with_2fa / total_users * 100) if total_users > 0 else 0
        }
    }


@app.post("/api/request-otp")
def request_otp(
    body: OTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request OTP for password reset, PIN reset, or account verification (signup).
    Handles signup even if user does not exist yet.
    """
    try:
        # Normalize email
        email_normalized = body.email.strip().lower()

        # Fetch user if exists
        user = db.query(User).filter(func.lower(User.email) == email_normalized).first()

        # Only enforce user existence for non-signup purposes
        if body.purpose != "signup" and not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check rate limiting (max 3 OTPs per 5 minutes)
        recent_otps = db.query(OTP).filter(
            func.lower(OTP.email) == email_normalized,
            OTP.created_at > datetime.utcnow() - timedelta(minutes=5)
        ).count()
        if recent_otps >= 3:
            raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait 5 minutes.")

        # Delete old OTPs for this email & purpose
        db.query(OTP).filter(
            and_(func.lower(OTP.email) == email_normalized, OTP.purpose == body.purpose)
        ).delete()
        db.commit()

        # Generate new OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Save OTP to database
        otp_record = OTP(
            email=email_normalized,
            otp_code=otp_code,
            purpose=body.purpose,
            expires_at=expires_at
        )
        db.add(otp_record)
        db.commit()

        # Send OTP email safely
        try:
            email_service.send_otp_email(email_normalized, otp_code, body.purpose)
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email_normalized}: {e}")

        # Log security event only if user exists
        if user:
            log_security_event(
                db, user.id, "otp_requested",
                f"OTP requested for {body.purpose}",
                request.client.host
            )

        return {"message": "OTP sent successfully", "expires_in": 600}

    except HTTPException:
        # Re-raise known HTTP errors
        raise
    except Exception as e:
        logger.error(f"Error requesting OTP for {body.email}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")
        

@app.post("/api/verify-otp")
def verify_otp(otp_verify: OTPVerify, db: Session = Depends(get_db), request: Request = None):
    """Verify OTP code"""
    try:
        # 1️⃣ Normalize email
        email_normalized = otp_verify.email.strip().lower()
        ip_address = request.client.host if hasattr(request, "client") else "unknown"

        # 2️⃣ Find valid OTP
        otp_record = db.query(OTP).filter(
            OTP.email == email_normalized,
            OTP.otp_code == otp_verify.otp_code,
            OTP.purpose == otp_verify.purpose,
            OTP.expires_at > datetime.utcnow(),
            OTP.used == False
        ).first()

        if not otp_record:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        # 3️⃣ Mark OTP as used
        otp_record.used = True
        otp_record.used_at = datetime.utcnow()
        db.commit()

        # 4️⃣ Get user (optional, might be None if purpose is signup)
        user = db.query(User).filter(User.email == email_normalized).first()

        # 5️⃣ Log security event
        log_security_event(
            db,
            user.id if user else None,
            "otp_verified",
            f"OTP verified for {otp_verify.purpose}",
            ip_address
        )

        # 6️⃣ Return response
        return {"message": "OTP verified successfully", "verified": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP for {otp_verify.email}: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


@app.post("/api/change-password")
async def change_password(
    request: Request,
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password with alert email and security logging"""
    ip_address = request.client.host if hasattr(request, "client") else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown")

    # Get location from IP
    location = get_location_from_ip(ip_address)

    try:
        # Verify current password
        if not verify_password(body.current_password, current_user.password_hash):
            log_security_event(
                db, current_user.id,
                "password_change_failed",
                "Failed password change attempt",
                ip_address
            )
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Hash and update new password
        current_user.password_hash = get_password_hash(body.new_password)
        current_user.updated_at = datetime.utcnow()
        db.commit()

        # Log successful password change
        log_security_event(
            db, current_user.id,
            "password_changed",
            "Password changed successfully",
            ip_address
        )

        # Send password change alert email
        try:
            template_vars = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": ip_address,
                "location": location,
                "device_info": get_readable_device(user_agent)
            }
            email_service.send_template_email(
                to_email=current_user.email,
                subject="🔐 Password Change Alert",
                template_name="password_change_alert.html",
                template_vars=template_vars
            )
        except Exception as e:
            logger.error(f"Failed to send password change alert email: {e}")

        return {"message": "Password changed successfully"}

    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password")

@app.post("/api/change-pin")
async def change_pin(
    request: Request,
    body: PinChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user PIN with alert email and security logging"""
    ip_address = request.client.host if hasattr(request, "client") else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown")

    # Get location from IP
    location = get_location_from_ip(ip_address)

    try:
        # Verify current PIN
        if not current_user.pin_hash or not verify_password(body.current_pin, current_user.pin_hash):
            log_security_event(
                db, current_user.id,
                "pin_change_failed",
                "Failed PIN change attempt",
                ip_address
            )
            raise HTTPException(status_code=400, detail="Current PIN is incorrect")

        # Hash and update new PIN
        current_user.pin_hash = get_password_hash(body.new_pin)
        current_user.updated_at = datetime.utcnow()
        db.commit()

        # Log successful PIN change
        log_security_event(
            db, current_user.id,
            "pin_changed",
            "PIN changed successfully",
            ip_address
        )

        # Send PIN change alert email
        try:
            template_vars = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": ip_address,
                "location": location,
                "device_info": get_readable_device(user_agent)
            }
            email_service.send_template_email(
                to_email=current_user.email,
                subject="🔐 PIN Change Alert",
                template_name="pin_change_alert.html",
                template_vars=template_vars
            )
        except Exception as e:
            logger.error(f"Failed to send PIN change alert email: {e}")

        return {"message": "PIN changed successfully"}

    except Exception as e:
        logger.error(f"Error changing PIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change PIN")

@app.post("/api/reset-password")
async def reset_password(
    reset_data: PasswordResetRequest,  # email, OTP (for frontend), new password
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset password directly after OTP has been verified"""

    ip_address = request.client.host if hasattr(request, "client") else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    location = get_location_from_ip(ip_address)

    try:
        # Fetch user
        user = db.query(User).filter(User.email == reset_data.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch OTP (ignore `used` because it was already verified)
        otp_record = db.query(OTP).filter_by(
            email=reset_data.email,
            otp_code=reset_data.otp_code,
            purpose="password_reset"
        ).first()
        if not otp_record:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Update password
        user.password_hash = get_password_hash(reset_data.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        # Delete OTP to prevent reuse
        db.delete(otp_record)
        db.commit()

        # Log security event
        log_security_event(
            db, user.id, "password_reset",
            f"Password reset successfully from IP {ip_address}", ip_address
        )

        # Send password reset alert email
        try:
            template_vars = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": ip_address,
                "location": location,
                "device_info": get_readable_device(user_agent)
            }
            email_service.send_template_email(
                to_email=user.email,
                subject="🔐 Password Reset Alert",
                template_name="password_reset_alert.html",
                template_vars=template_vars
            )
        except Exception as e:
            logger.error(f"Failed to send password reset alert email: {e}")

        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset password")
        

@app.post("/api/reset-pin")
async def reset_pin(
    pin_data: PinResetRequest,  # email, OTP (from frontend), new_pin
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset PIN directly after OTP has been verified"""

    ip_address = request.client.host if hasattr(request, "client") else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    location = get_location_from_ip(ip_address)

    try:
        # Fetch user
        user = db.query(User).filter(User.email == pin_data.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch OTP (ignore `used` because it was already verified)
        otp_record = db.query(OTP).filter_by(
            email=pin_data.email,
            otp_code=pin_data.otp_code,
            purpose="pin_reset"
        ).first()
        if not otp_record:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Update PIN
        user.pin_hash = get_password_hash(pin_data.new_pin)
        user.updated_at = datetime.utcnow()
        db.commit()

        # Delete OTP to prevent reuse
        db.delete(otp_record)
        db.commit()

        # Log security event
        log_security_event(
            db, user.id, "pin_reset",
            f"PIN reset successfully from IP {ip_address}", ip_address
        )

        # Send PIN reset alert email
        try:
            template_vars = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": ip_address,
                "location": location,
                "device_info": get_readable_device(user_agent)
            }
            email_service.send_template_email(
                to_email=user.email,
                subject="🔐 PIN Reset Alert",
                template_name="pin_reset_alert.html",
                template_vars=template_vars
            )
        except Exception as e:
            logger.error(f"Failed to send PIN reset alert email: {e}")

        return {"message": "PIN reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting PIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset PIN")

@app.post("/api/verify-pin")
async def verify_pin(
    request: Request,
    body: UserPinVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if hasattr(request, "client") else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown")

    # Get location from IP
    location = get_location_from_ip(ip_address)

    try:
        if not current_user.pin_hash:
            raise HTTPException(status_code=400, detail="PIN not set for this account")
        
        if not verify_password(body.pin, current_user.pin_hash):
            log_security_event(db, current_user.id, "pin_verification_failed", "Failed PIN verification attempt", ip_address)
            raise HTTPException(status_code=400, detail="Invalid PIN")

        log_security_event(db, current_user.id, "pin_verified", "PIN verified successfully", ip_address)

        # Send login alert email with exact IP, device, and location
        try:
            template_vars = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": ip_address,
                "location": location,
                "device_info": get_readable_device(user_agent)
            }
            email_service.send_template_email(
                to_email=current_user.email,
                subject="🔐 Dashboard Access Alert",
                template_name="login_alert.html",
                template_vars=template_vars
            )
        except Exception as e:
            logger.error(f"Failed to send login alert email: {e}")
        
        dashboard_token = create_access_token(
            data={"sub": current_user.email, "type": "dashboard_access"},
            expires_delta=timedelta(hours=1)
        )
        
        return {
            "message": "PIN verified successfully",
            "dashboard_token": dashboard_token,
            "expires_in": 3600
        }
        
    except Exception as e:
        logger.error(f"Error verifying PIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify PIN")

# =============================================================================
# CRYPTO DEPOSIT ENDPOINTS
# =============================================================================

def get_or_create_admin_settings(db: Session):
    """Get or create admin settings"""
    settings = db.query(AdminSettings).first()
    if not settings:
        settings = AdminSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.put("/api/admin/wallet-addresses")
def update_wallet_addresses(
    wallet_data: dict,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update Bitcoin and Ethereum wallet addresses"""
    settings = get_or_create_admin_settings(db)
    
    if "bitcoin_wallet_address" in wallet_data:
        old_bitcoin = settings.bitcoin_wallet_address
        settings.bitcoin_wallet_address = wallet_data["bitcoin_wallet_address"]
        log_admin_action(
            db=db,
            admin_id=admin_user.id,
            action="update_bitcoin_wallet",
            target_type="admin_settings",
            target_id="1",
            details=f"Updated Bitcoin wallet address from {old_bitcoin} to {wallet_data['bitcoin_wallet_address']}"
        )
    
    if "ethereum_wallet_address" in wallet_data:
        old_ethereum = settings.ethereum_wallet_address
        settings.ethereum_wallet_address = wallet_data["ethereum_wallet_address"]
        log_admin_action(
            db=db,
            admin_id=admin_user.id,
            action="update_ethereum_wallet",
            target_type="admin_settings",
            target_id="1",
            details=f"Updated Ethereum wallet address from {old_ethereum} to {wallet_data['ethereum_wallet_address']}"
        )
    
    db.commit()
    db.refresh(settings)
    
    return {
        "message": "Wallet addresses updated successfully",
        "bitcoin_wallet_address": settings.bitcoin_wallet_address,
        "ethereum_wallet_address": settings.ethereum_wallet_address
    }

@app.get("/api/admin/wallet-addresses")
def get_wallet_addresses(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get current wallet addresses"""
    settings = get_or_create_admin_settings(db)
    return {
        "bitcoin_wallet_address": settings.bitcoin_wallet_address,
        "ethereum_wallet_address": settings.ethereum_wallet_address
    }

@app.get("/api/deposits/info/{crypto_type}")
def get_deposit_info(crypto_type: CryptoType, db: Session = Depends(get_db)):
    """Get deposit information including QR code and wallet address"""
    settings = get_or_create_admin_settings(db)
    
    # Get wallet address & QR from admin settings
    if crypto_type == "bitcoin":
        wallet_address = settings.bitcoin_wallet_address
        qr_code_url = settings.bitcoin_deposit_qr
        usd_rate = settings.bitcoin_rate_usd
    else:  # ethereum
        wallet_address = settings.ethereum_wallet_address
        qr_code_url = settings.ethereum_deposit_qr
        usd_rate = settings.ethereum_rate_usd
    
    if not wallet_address:
        raise HTTPException(status_code=404, detail=f"No wallet address configured for {crypto_type}")
    
    return {
        "crypto_type": crypto_type,
        "qr_code_url": qr_code_url,
        "wallet_address": wallet_address,
        "usd_rate": usd_rate
    }


def get_crypto_usd_rate(db: Session, crypto_type: str) -> Decimal:
    """Get current USD rate for crypto from admin settings"""
    settings = get_or_create_admin_settings(db)

    if crypto_type == "bitcoin":
        return Decimal(settings.bitcoin_rate_usd or "50000.00")
    else:
        return Decimal(settings.ethereum_rate_usd or "3000.00")


def convert_crypto_to_usd(crypto_amount: Decimal, crypto_type: str, db: Session) -> Decimal:
    """Convert crypto amount to USD"""
    rate = get_crypto_usd_rate(db, crypto_type)
    return crypto_amount * rate


def convert_usd_to_crypto(usd_amount: Decimal, crypto_type: str, db: Session) -> Decimal:
    """Convert USD amount to crypto"""
    rate = get_crypto_usd_rate(db, crypto_type)
    return usd_amount / rate

@app.get("/api/deposits/rates")
def get_crypto_rates(db: Session = Depends(get_db)):
    """Get current crypto to USD conversion rates"""
    settings = db.query(AdminSettings).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return {
        "bitcoin_usd_rate": settings.bitcoin_rate_usd,
        "ethereum_usd_rate": settings.ethereum_rate_usd
    }


@app.post("/api/deposits/convert")
def convert_amount(
    request: DepositConvertRequest,
    db: Session = Depends(get_db)
):
    """Convert between crypto and USD amounts"""

    if request.amount and request.usd_amount:
        raise HTTPException(status_code=400, detail="Provide either crypto amount or USD amount, not both")
    
    if not request.amount and not request.usd_amount:
        raise HTTPException(status_code=400, detail="Provide either crypto amount or USD amount")
    
    if request.amount:
        # Convert crypto to USD
        usd_equivalent = convert_crypto_to_usd(request.amount, request.crypto_type, db)
        return {
            "crypto_amount": request.amount,
            "usd_amount": usd_equivalent,
            "crypto_type": request.crypto_type
        }
    else:
        # Convert USD to crypto
        crypto_equivalent = convert_usd_to_crypto(request.usd_amount, request.crypto_type, db)
        return {
            "crypto_amount": crypto_equivalent,
            "usd_amount": request.usd_amount,
            "crypto_type": request.crypto_type
        }


@app.post("/api/deposits/create")
def create_deposit(
    deposit_data: DepositCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new crypto deposit with USD conversion"""
    
    if current_user.is_flagged:
        raise HTTPException(status_code=403, detail="Account flagged - deposits not allowed")

    # Normalize crypto_type
    crypto_type = deposit_data.crypto_type.lower()

    # Determine amounts (prioritize crypto amount if both are provided)
    if deposit_data.amount:
        crypto_amount = deposit_data.amount
        usd_amount = convert_crypto_to_usd(crypto_amount, crypto_type, db)
    elif deposit_data.usd_amount:
        usd_amount = deposit_data.usd_amount
        crypto_amount = convert_usd_to_crypto(usd_amount, crypto_type, db)
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either crypto amount or USD amount"
        )

    # Get deposit info from AdminSettings
    settings = db.query(AdminSettings).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Admin settings not found")

    if crypto_type == "bitcoin":
        wallet_address = settings.bitcoin_wallet_address
        qr_code_url = settings.bitcoin_deposit_qr
    elif crypto_type == "ethereum":
        wallet_address = settings.ethereum_wallet_address
        qr_code_url = settings.ethereum_deposit_qr
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported crypto type: {crypto_type}")

    if not wallet_address:
        raise HTTPException(status_code=404, detail=f"No wallet address configured for {crypto_type}")

    # Save deposit record
    deposit = CryptoDeposit(
        user_id=current_user.id,
        crypto_type=crypto_type,
        amount=crypto_amount,
        usd_amount=usd_amount,
        transaction_hash=deposit_data.transaction_hash or None,
        status=DepositStatus.PENDING
    )

    db.add(deposit)
    db.commit()
    db.refresh(deposit)

    # Log activity
    log_activity(
        db, current_user.id, "DEPOSIT_CREATED",
        f"Created {crypto_type} deposit of {crypto_amount} (${usd_amount} USD)",
        request.client.host
    )

    # Format amounts for response
    def fmt_crypto(val: Decimal) -> str:
        return str(val.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN))

    def fmt_usd(val: Decimal) -> str:
        return str(val.quantize(Decimal("0.01"), rounding=ROUND_DOWN))

    return {
        "message": "Deposit created successfully",
        "deposit_id": deposit.id,
        "crypto_amount": fmt_crypto(crypto_amount),
        "usd_amount": fmt_usd(usd_amount),
        "qr_code_url": qr_code_url,
        "wallet_address": wallet_address,
        "crypto_type": crypto_type
    }

@app.post("/api/deposits/{deposit_id}/upload-evidence")
async def upload_deposit_evidence(
    deposit_id: int,
    evidence_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload deposit evidence (screenshot/proof)"""
    
    # Fetch the deposit
    deposit = db.query(CryptoDeposit).filter(
        CryptoDeposit.id == deposit_id,
        CryptoDeposit.user_id == current_user.id
    ).first()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    if deposit.status != DepositStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only upload evidence for pending deposits")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "application/pdf"]
    if evidence_file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only images (JPEG, PNG, GIF) and PDF files are allowed")
    
    # Upload file to cloud storage using EmailService instance
    file_extension = evidence_file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    email_service = EmailService()
    cloud_url = await email_service.upload_to_cloud(evidence_file, unique_filename)
    
    # Update deposit with cloud URL
    deposit.evidence_url = cloud_url
    db.commit()
    
    # Send email to admin
    admin_email = ADMIN_EMAIL or "admin@example.com"
    email_body = f"""
        <p><strong>User:</strong> {current_user.name} ({current_user.email})</p>
        <p><strong>Crypto Type:</strong> {deposit.crypto_type.title()}</p>
        <p><strong>Amount:</strong> {deposit.amount}</p>
        <p><strong>USD Amount:</strong> {deposit.usd_amount}</p>
        <p><strong>Deposit ID:</strong> {deposit.id}</p>
        <p><strong>Transaction Hash:</strong> {deposit.transaction_hash or "Not provided"}</p>
    """
    
    email_service.send_email(
        to_email=admin_email,
        subject=f"New Deposit Evidence - {deposit.crypto_type.title()} Deposit #{deposit.id}",
        body=email_body,
        is_html=True,
        attachment_url=cloud_url
    )
    
    # Log activity
    log_activity(
        db, current_user.id, "DEPOSIT_EVIDENCE_UPLOADED",
        f"Uploaded evidence for {deposit.crypto_type} deposit #{deposit.id}",
        "system"
    )
    
    return {
        "message": "Evidence uploaded successfully",
        "evidence_url": deposit.evidence_url
    }


@app.post("/api/deposits/{deposit_id}/submit")
def submit_deposit(
    deposit_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit deposit for admin review (with or without evidence)"""
    
    # Fetch the deposit
    deposit = db.query(CryptoDeposit).filter(
        CryptoDeposit.id == deposit_id,
        CryptoDeposit.user_id == current_user.id
    ).first()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    if deposit.status != DepositStatus.PENDING:
        raise HTTPException(status_code=400, detail="Deposit already submitted")
    
    # Update deposit status to submitted
    deposit.status = DepositStatus.SUBMITTED
    db.commit()
    
    # Send email to admin if evidence not uploaded
    if not deposit.evidence_url:
        admin_email = ADMIN_EMAIL or "admin@example.com"
        email_body = f"""
            <p><strong>User:</strong> {current_user.name} ({current_user.email})</p>
            <p><strong>Crypto Type:</strong> {deposit.crypto_type.title()}</p>
            <p><strong>Amount:</strong> {deposit.amount}</p>
            <p><strong>USD Amount:</strong> {deposit.usd_amount}</p>
            <p><strong>Deposit ID:</strong> {deposit.id}</p>
            <p><strong>Transaction Hash:</strong> {deposit.transaction_hash or "Not provided"}</p>
        """
        email_service.send_email(
            to_email=admin_email,
            subject=f"New Deposit Submission - {deposit.crypto_type.title()} Deposit #{deposit.id}",
            body=email_body,
            is_html=True
        )
    
    # Get IP, location, device info for user notification
    ip_address = request.client.host if hasattr(request, "client") else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    location = get_location_from_ip(ip_address)
    device_info = get_readable_device(user_agent)
    
    # Send deposit initiated alert to user
    try:
        template_vars = {
            "current_user": current_user,  # ✅ Include current_user for template
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "ip_address": ip_address,
            "location": location,
            "device_info": device_info,
            "crypto_type": deposit.crypto_type.title(),
            "amount": deposit.amount,
            "usd_amount": deposit.usd_amount,
            "status": "Waiting for admin verification",
            "deposit_id": deposit.id
        }
        email_service.send_template_email(
            to_email=current_user.email,
            subject="💰 Deposit Initiated",
            template_name="deposit_initiated.html",
            template_vars=template_vars
        )
    except Exception as e:
        logger.error(f"Failed to send deposit alert to user: {e}")
    
    # Log activity
    log_activity(
        db, current_user.id, "DEPOSIT_SUBMITTED",
        f"Submitted {deposit.crypto_type} deposit #{deposit.id} for admin review",
        ip_address
    )
    
    return {"message": "Deposit submitted for admin review, waiting for admin verification"}
    

@app.get("/api/user/deposits")
def get_user_deposits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch all deposits for the currently logged-in user.
    Returns deposit details including crypto type, amounts, status, evidence, and creation date.
    """
    deposits = db.query(CryptoDeposit).filter(
        CryptoDeposit.user_id == current_user.id
    ).order_by(CryptoDeposit.created_at.desc()).all()

    result = []
    for deposit in deposits:
        result.append({
            "id": deposit.id,
            "crypto_type": deposit.crypto_type,
            "amount": deposit.amount,
            "usd_amount": deposit.usd_amount,
            "status": deposit.status,
            "transaction_hash": deposit.transaction_hash,
            "evidence_url": deposit.evidence_url,
            "created_at": deposit.created_at.isoformat()
        })

    return result

# =============================================================================
# ADMIN DEPOSIT MANAGEMENT ENDPOINTS
# =============================================================================

@app.get("/api/admin/deposits/pending")
def get_pending_deposits(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all deposits that are pending or submitted for admin confirmation"""
    
    deposits = (
        db.query(CryptoDeposit)
        .options(joinedload(CryptoDeposit.user))  # eager load user
        .filter(CryptoDeposit.status.in_([DepositStatus.PENDING, DepositStatus.SUBMITTED]))
        .order_by(CryptoDeposit.created_at.desc())
        .all()
    )
    
    return [
        {
            "id": d.id,
            "user_email": d.user.email if d.user else None,
            "user_name": d.user.name if d.user else None,
            "crypto_type": d.crypto_type,
            "amount": d.amount,
            "usd_amount": d.usd_amount,
            "transaction_hash": str(d.transaction_hash) if d.transaction_hash else "",
            "status": d.status.value if hasattr(d.status, "value") else d.status,
            "created_at": d.created_at
        }
        for d in deposits
    ]
    


@app.put("/api/admin/deposits/{deposit_id}/confirm")
async def confirm_deposit(
    deposit_id: int,
    request: Request,
    action: str = Query(..., regex="^(confirm|reject)$"),  # strictly confirm or reject
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Confirm or reject a deposit and start mining if confirmed"""
    
    deposit = db.query(CryptoDeposit).filter(CryptoDeposit.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    user = db.query(User).filter(User.id == deposit.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if action == "confirm":
        deposit.status = DepositStatus.CONFIRMED
        deposit.confirmed_by = admin_user.id
        deposit.confirmed_at = datetime.utcnow()
        
        # Add crypto to user balance
        if deposit.crypto_type.lower() == "bitcoin":
            user.bitcoin_balance += deposit.amount
        else:
            user.ethereum_balance += deposit.amount
        
        # ✅ Get mining rate (personal -> global -> default)
        if user.personal_mining_rate:
            mining_rate = user.personal_mining_rate
        else:
            settings = get_admin_settings(db)
            mining_rate = settings.global_mining_rate if settings else 70  # fallback default

        # Create mining session
        mining_session = MiningSession(
            user_id=user.id,
            deposit_id=deposit.id,
            crypto_type=deposit.crypto_type,
            deposited_amount=deposit.amount,
            mining_rate=mining_rate,
            created_at=datetime.utcnow(),
            is_active=True
        )
        db.add(mining_session)

        # Log transaction
        log_transaction(
            db=db,
            user_id=user.id,
            transaction_type="deposit",
            crypto_type=deposit.crypto_type,
            amount=deposit.amount,
            description=f"Deposit confirmed by admin - {deposit.crypto_type} mining started at {mining_rate}%",
            reference_id=str(deposit.id)
        )
        
        # Trigger referral rewards if applicable
        process_referral_rewards(
            db=db,
            new_user=user,
            deposit_amount=deposit.amount,
            deposit_type=deposit.crypto_type
        )
        
        # Log admin action
        log_admin_action(
            db=db,
            admin_id=admin_user.id,
            action="confirm_deposit",
            target_type="deposit",
            target_id=str(deposit.id),
            details=f"Confirmed {deposit.crypto_type} deposit of {deposit.amount} for user {user.email}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )

    elif action == "reject":
        deposit.status = DepositStatus.REJECTED
        deposit.confirmed_by = admin_user.id
        deposit.confirmed_at = datetime.utcnow()
        
        # Log admin action
        log_admin_action(
            db=db,
            admin_id=admin_user.id,
            action="reject_deposit",
            target_type="deposit",
            target_id=str(deposit.id),
            details=f"Rejected {deposit.crypto_type} deposit of {deposit.amount} for user {user.email}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )

    # Commit changes
    db.commit()

    # Map status to match email template
    status_text = "Approved" if deposit.status == DepositStatus.CONFIRMED else "Rejected"

    # Send email
    try:
        template_vars = {
            "deposit_id": deposit.id,
            "crypto_type": deposit.crypto_type,
            "amount": deposit.amount,
            "usd_amount": deposit.usd_amount,
            "status": status_text
        }
        email_service.send_template_email(
            to_email=user.email,
            subject=f"Your {deposit.crypto_type.title()} Deposit Status",
            template_name="deposit_status_alert.html",
            template_vars=template_vars
        )
    except Exception as e:
        logger.error(f"Failed to send deposit status email to user: {e}")

    return {"message": f"Deposit {action}ed successfully"}


@app.post("/api/mining/live-progress")
def mining_live_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ⛔ Stop immediately if mining is paused for this user
    if getattr(current_user, "mining_paused", False):
        return {
            "message": "Mining is paused for this user",
            "total_mined": 0,
            "sessions": []
        }

    now = datetime.now(timezone.utc)
    total_mined = Decimal(0)
    sessions_data = []

    # Fetch active mining sessions
    active_sessions = db.query(MiningSession).filter(
        MiningSession.user_id == current_user.id,
        MiningSession.is_active == True
    ).all()

    for session in active_sessions:
        deposited_amount = Decimal(session.deposited_amount)

        # Convert stored percent to fraction for calculations
        mining_rate_percent = Decimal(session.mining_rate)  # e.g., 90 for 90%
        mining_rate_fraction = mining_rate_percent / Decimal(100)  # 0.9

        total_per_day = deposited_amount * mining_rate_fraction
        seconds_in_day = Decimal(24 * 3600)

        # Ensure last_mined is not None
        last_mined = session.last_mined or session.created_at
        elapsed_seconds = Decimal((now - last_mined).total_seconds())
        mined_amount = total_per_day / seconds_in_day * elapsed_seconds

        # Update session mined amount safely
        session.mined_amount = (session.mined_amount or Decimal(0)) + mined_amount
        session.last_mined = now

        # Normalize crypto_type
        crypto_type = session.crypto_type.lower().strip()

        # Update user balance based on crypto type
        if crypto_type in ["bitcoin", "btc"]:
            current_user.bitcoin_balance = (current_user.bitcoin_balance or Decimal(0)) + mined_amount
            balance = float(current_user.bitcoin_balance)
        elif crypto_type in ["ethereum", "eth"]:
            current_user.ethereum_balance = (current_user.ethereum_balance or Decimal(0)) + mined_amount
            balance = float(current_user.ethereum_balance)
        else:
            raise ValueError(f"Unsupported crypto type: {session.crypto_type}")

        total_mined += mined_amount

        sessions_data.append({
            "session_id": session.id,
            "crypto_type": session.crypto_type,
            "deposited_amount": float(session.deposited_amount),
            "mining_rate_percent": float(mining_rate_percent),  # show human-readable percent
            "current_mined": float(mined_amount),
            "balance": balance
        })

    db.commit()  # Persist balances and last_mined

    return {
        "message": "Mining synced",
        "total_mined": float(total_mined),
        "sessions": sessions_data
    }


@app.put("/api/admin/mining/{session_id}/pause")
def pause_mining_session(
    session_id: int,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Pause a mining session"""
    session = db.query(MiningSession).filter(MiningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Mining session not found")
    
    session.is_active = False
    session.paused_at = datetime.utcnow()
    
    log_admin_action(
        db=db,
        admin_id=admin_user.id,
        action="pause_mining",
        target_type="mining_session",
        target_id=str(session.id),
        description=f"Paused mining session for user {session.user.email}",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")
    )
    
    db.commit()
    
    return {"message": "Mining session paused successfully"}

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

@app.on_event("startup")
@repeat_every(seconds=30)  # Process email queue every 30 seconds
def process_email_queue():
    """Background task to process pending emails."""
    db = SessionLocal()
    try:
        # Fetch up to 10 pending emails
        pending_emails = db.query(EmailNotification).filter(
            EmailNotification.status == "pending"
        ).limit(10).all()
        
        for email in pending_emails:
            try:
                success = send_email_now(
                    to_email=email.recipient_email,
                    subject=email.subject,
                    html_content=email.html_content
                )

                if success:
                    email.status = "sent"
                    email.sent_at = datetime.utcnow()
                else:
                    email.attempts += 1
                    if email.attempts < 3:
                        email.status = "pending"
                        email.scheduled_for = datetime.utcnow() + timedelta(minutes=5)
                    else:
                        email.status = "failed"

            except Exception as e:
                email.attempts += 1
                email.status = "failed"
                print(f"❌ Failed to send email ID {email.id}: {e}")
        
        db.commit()
    
    except Exception as e:
        print(f"❌ Error processing email queue: {e}")
        db.rollback()
    
    finally:
        db.close()

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

@app.on_event("startup")
def setup_database_and_admin():
    """Initialize database tables and ensure a single admin user exists."""
    # ✅ Create all tables
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Environment variables
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        admin_pin = os.getenv("ADMIN_PIN")

        if not all([admin_email, admin_password, admin_pin]):
            print("⚠️ Missing ADMIN credentials in environment, skipping admin creation.")
            return

        # 🔹 Fetch all admin users
        all_admins = db.query(User).filter(User.is_admin == True).all()

        if all_admins:
            # Update the first admin with environment credentials
            admin_user = all_admins[0]
            admin_user.email = admin_email
            admin_user.password_hash = pwd_context.hash(admin_password)
            admin_user.pin_hash = pwd_context.hash(admin_pin)
            admin_user.email_verified = True
            admin_user.user_id = admin_user.user_id or generate_user_id()
            admin_user.referral_code = admin_user.referral_code or generate_referral_code()
            db.add(admin_user)

            # Delete any extra admins
            for extra_admin in all_admins[1:]:
                db.delete(extra_admin)

            db.commit()
            print(f"✅ Admin user updated: {admin_email}")
            if len(all_admins) > 1:
                print(f"⚠️ Deleted {len(all_admins)-1} extra admin(s)")

        else:
            # No admin exists, create one
            admin_user = User(
                name="Admin",
                email=admin_email,
                password_hash=pwd_context.hash(admin_password),
                pin_hash=pwd_context.hash(admin_pin),
                is_admin=True,
                email_verified=True,
                user_id=generate_user_id(),
                referral_code=generate_referral_code()
            )
            db.add(admin_user)
            db.commit()
            print(f"✅ Admin user created: {admin_email}")

        # 🔹 Check and create default admin settings
        existing_settings = db.query(AdminSettings).first()
        if not existing_settings:
            default_settings = AdminSettings(
                bitcoin_rate_usd=Decimal("50000.0"),
                ethereum_rate_usd=Decimal("3000.0"),
                global_mining_rate=Decimal("0.7"),
                referral_reward_enabled=True,
                referral_reward_type="bitcoin",
                referral_reward_amount=Decimal("0.001"),
                referrer_reward_amount=Decimal("0.001")
            )
            db.add(default_settings)
            db.commit()
            print("✅ Default admin settings created")
        else:
            print("ℹ️ Admin settings already exist")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating/updating admin user/settings: {e}")
    finally:
        db.close()

@app.get("/api/analytics/dashboard", response_model=UserAnalyticsResponse)
async def get_user_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics dashboard for user"""
    admin_settings = get_admin_settings(db)

    # ---------------------
    # Portfolio Overview
    # ---------------------
    usd_values = calculate_usd_values(current_user, admin_settings) or {}

    total_balance_usd = usd_values.get("total_balance_usd", 0)
    bitcoin_balance_usd = usd_values.get("bitcoin_value_usd", 0)
    ethereum_balance_usd = usd_values.get("ethereum_value_usd", 0)

    portfolio_overview = {
        "total_value_usd": total_balance_usd,
        "bitcoin_balance": current_user.bitcoin_balance or 0,
        "ethereum_balance": current_user.ethereum_balance or 0,
        "bitcoin_value_usd": bitcoin_balance_usd,
        "ethereum_value_usd": ethereum_balance_usd,
        "asset_allocation": {
            "bitcoin_percentage": (bitcoin_balance_usd / total_balance_usd * 100) if total_balance_usd else 0,
            "ethereum_percentage": (ethereum_balance_usd / total_balance_usd * 100) if total_balance_usd else 0
        }
    }

    # ---------------------
    # Mining Performance
    # ---------------------
    active_sessions = db.query(MiningSession).filter(
        MiningSession.user_id == current_user.id,
        MiningSession.is_active == True
    ).all()

    total_mining_power = sum(Decimal(s.deposited_amount or 0) for s in active_sessions)
    avg_mining_rate = (sum(Decimal(s.mining_rate or 0) for s in active_sessions) / len(active_sessions)) if active_sessions else Decimal(0)

    daily_estimated_earnings_usd = Decimal(0)
    for s in active_sessions:
        deposited_amount = Decimal(s.deposited_amount or 0)
        mining_rate_percent = Decimal(s.mining_rate or 0)
        crypto_type = (s.crypto_type or "").lower().strip()

        daily_mined_crypto = deposited_amount * (mining_rate_percent / Decimal(100))

        if crypto_type in ["bitcoin", "btc"]:
            daily_estimated_earnings_usd += daily_mined_crypto * Decimal(admin_settings.bitcoin_rate_usd or 0)
        elif crypto_type in ["ethereum", "eth"]:
            daily_estimated_earnings_usd += daily_mined_crypto * Decimal(admin_settings.ethereum_rate_usd or 0)

    mining_performance = {
        "active_sessions": len(active_sessions),
        "total_mining_power": float(total_mining_power),
        "average_mining_rate": float(avg_mining_rate),
        "daily_estimated_earnings": float(daily_estimated_earnings_usd)
    }

    # ---------------------
    # Earnings History (last 30 days)
    # ---------------------
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    earnings_transactions = db.query(TransactionHistory).filter(
        TransactionHistory.user_id == current_user.id,
        TransactionHistory.transaction_type.in_(["mining_reward", "referral_reward"]),
        TransactionHistory.created_at >= thirty_days_ago
    ).all()

    mining_earnings = sum(Decimal(t.amount or 0) for t in earnings_transactions if t.transaction_type == "mining_reward")
    referral_earnings = sum(Decimal(t.amount or 0) for t in earnings_transactions if t.transaction_type == "referral_reward")

    earnings_history = {
        "total_earnings": float(mining_earnings + referral_earnings),
        "mining_earnings": float(mining_earnings),
        "referral_earnings": float(referral_earnings),
        "daily_breakdown": []
    }

    for i in range(30):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_total = db.query(func.sum(TransactionHistory.amount)).filter(
            TransactionHistory.user_id == current_user.id,
            TransactionHistory.transaction_type.in_(["mining_reward", "referral_reward"]),
            TransactionHistory.created_at >= day_start,
            TransactionHistory.created_at < day_end
        ).scalar() or 0

        earnings_history["daily_breakdown"].append({
            "date": day_start.strftime("%Y-%m-%d"),
            "earnings": float(day_total)
        })

    # ---------------------
    # Transaction Analytics
    # ---------------------
    all_transactions = db.query(TransactionHistory).filter(TransactionHistory.user_id == current_user.id).all()

    transaction_analytics = {
        "total_transactions": len(all_transactions),
        "transaction_types": {},
        "volume_by_crypto": {"bitcoin": 0, "ethereum": 0}
    }

    for tx in all_transactions:
        tx_type = tx.transaction_type or "unknown"
        transaction_analytics["transaction_types"][tx_type] = transaction_analytics["transaction_types"].get(tx_type, 0) + 1

        crypto_type = (tx.crypto_type or "").lower()
        if crypto_type in ["bitcoin", "ethereum"]:
            transaction_analytics["volume_by_crypto"][crypto_type] += float(tx.amount or 0)

    # ---------------------
    # Referral Performance (Corrected)
    # ---------------------
    # All referred users (for reference)
    referrals = db.query(User).filter(User.referred_by_code == current_user.referral_code).all()

    # Only count referral rewards that were actually paid
    paid_rewards = db.query(ReferralReward).filter(
        ReferralReward.referrer_id == current_user.id,
        ReferralReward.status == "paid"
    ).all()

    referral_performance = {
        "total_referrals": len(referrals),
        "total_rewards": float(sum(Decimal(r.reward_amount or 0) for r in paid_rewards)),
        "active_referrals": len(paid_rewards),  # users with paid reward
        "referral_code": current_user.referral_code or ""
    }

    # ---------------------
    # Growth Metrics
    # ---------------------
    first_tx = db.query(TransactionHistory).filter(TransactionHistory.user_id == current_user.id).order_by(TransactionHistory.created_at.asc()).first()
    first_date = first_tx.created_at if first_tx else current_user.created_at
    if first_date.tzinfo is None:
        first_date = first_date.replace(tzinfo=timezone.utc)

    days_active = max((now - first_date).days, 1)

    growth_metrics = {
        "days_active": days_active,
        "average_daily_earnings": float((mining_earnings + referral_earnings) / days_active),
        "growth_rate": 0,
        "milestones": {
            "first_deposit": bool(db.query(CryptoDeposit).filter(CryptoDeposit.user_id == current_user.id).first()),
            "first_referral": len(referrals) > 0,
            "mining_active": len(active_sessions) > 0
        }
    }

    return UserAnalyticsResponse(
        portfolio_overview=portfolio_overview,
        mining_performance=mining_performance,
        earnings_history=earnings_history,
        transaction_analytics=transaction_analytics,
        referral_performance=referral_performance,
        growth_metrics=growth_metrics
    )


@app.get("/api/analytics/mining-performance", response_model=MiningPerformanceData)
async def get_mining_performance(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed mining performance analytics"""
    now = datetime.now(timezone.utc)

    # Daily earnings
    daily_earnings = []
    for i in range(days):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_mining_earnings = db.query(func.sum(TransactionHistory.amount)).filter(
            TransactionHistory.user_id == current_user.id,
            TransactionHistory.transaction_type == "mining_reward",
            TransactionHistory.created_at >= day_start,
            TransactionHistory.created_at < day_end
        ).scalar() or Decimal(0)

        day_mining_earnings = Decimal(day_mining_earnings)

        daily_earnings.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "bitcoin_earned": float(day_mining_earnings),
            "ethereum_earned": 0,  # Could separate by crypto type
            "total_earned": float(day_mining_earnings)
        })

    # Weekly summary
    week_start = now - timedelta(days=7)
    weekly_earnings = Decimal(
        db.query(func.sum(TransactionHistory.amount)).filter(
            TransactionHistory.user_id == current_user.id,
            TransactionHistory.transaction_type == "mining_reward",
            TransactionHistory.created_at >= week_start
        ).scalar() or 0
    )

    # Monthly trends
    month_start = now - timedelta(days=30)
    monthly_earnings = Decimal(
        db.query(func.sum(TransactionHistory.amount)).filter(
            TransactionHistory.user_id == current_user.id,
            TransactionHistory.transaction_type == "mining_reward",
            TransactionHistory.created_at >= month_start
        ).scalar() or 0
    )

    # Efficiency metrics
    active_sessions = db.query(MiningSession).filter(
        MiningSession.user_id == current_user.id,
        MiningSession.is_active == True
    ).all()

    total_deposited = sum(Decimal(session.deposited_amount) for session in active_sessions)
    total_mined = sum(Decimal(session.mined_amount) for session in active_sessions)
    efficiency = float((total_mined / total_deposited * Decimal(100)) if total_deposited > 0 else Decimal(0))

    return MiningPerformanceData(
        daily_earnings=daily_earnings,
        weekly_summary={
            "total_earned": float(weekly_earnings),
            "average_daily": float(weekly_earnings / Decimal(7)),
            "best_day": max(daily_earnings[-7:], key=lambda x: x["total_earned"])["date"] if daily_earnings else None
        },
        monthly_trends={
            "total_earned": float(monthly_earnings),
            "trend": "up",  # Placeholder; could calculate actual trend
            "growth_rate": 0
        },
        efficiency_metrics={
            "mining_efficiency": efficiency,
            "active_sessions": len(active_sessions),
            "total_mining_power": float(total_deposited)
        }
    )



# ---------------------
# Portfolio Analytics
# ---------------------
@app.get("/api/analytics/portfolio", response_model=PortfolioAnalytics)
async def get_portfolio_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio analytics and performance"""
    admin_settings = get_admin_settings(db)
    usd_values = calculate_usd_values(current_user, admin_settings)
    
    # ---------------------
    # Current Value
    # ---------------------
    current_value = {
        "total_usd": float(Decimal(usd_values["total_balance_usd"])),
        "bitcoin_amount": float(Decimal(current_user.bitcoin_balance)),
        "ethereum_amount": float(Decimal(current_user.ethereum_balance)),
        "bitcoin_usd": float(Decimal(usd_values["bitcoin_balance_usd"])),
        "ethereum_usd": float(Decimal(usd_values["ethereum_balance_usd"]))
    }
    
    # ---------------------
    # Historical Performance (last 30 days)
    # ---------------------
    historical_performance = []
    for i in range(30):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        historical_performance.append({
            "date": day.strftime("%Y-%m-%d"),
            "total_value": float(Decimal(usd_values["total_balance_usd"])),
            "bitcoin_value": float(Decimal(usd_values["bitcoin_balance_usd"])),
            "ethereum_value": float(Decimal(usd_values["ethereum_balance_usd"]))
        })
    
    # ---------------------
    # Asset Allocation
    # ---------------------
    total_value = Decimal(usd_values["total_balance_usd"])
    asset_allocation = {
        "bitcoin": {
            "percentage": float(Decimal(usd_values["bitcoin_balance_usd"]) / total_value * Decimal(100)) if total_value > 0 else 0,
            "value": float(Decimal(usd_values["bitcoin_balance_usd"]))
        },
        "ethereum": {
            "percentage": float(Decimal(usd_values["ethereum_balance_usd"]) / total_value * Decimal(100)) if total_value > 0 else 0,
            "value": float(Decimal(usd_values["ethereum_balance_usd"]))
        }
    }
    
    # ---------------------
    # Growth Rate Placeholder
    # ---------------------
    growth_rate = {
        "daily": 0,  # Would calculate based on historical data
        "weekly": 0,
        "monthly": 0,
        "all_time": 0
    }
    
    return PortfolioAnalytics(
        current_value=current_value,
        historical_performance=historical_performance,
        asset_allocation=asset_allocation,
        growth_rate=growth_rate
    )

# ---------------------
# Transaction Logging
# ---------------------
def log_transaction(
    db: Session,
    user_id: int,
    transaction_type: str,
    crypto_type: Optional[str],
    amount: Decimal,
    description: str,
    reference_id: Optional[str] = None
):
    """Log transaction for history tracking"""
    amount = Decimal(amount)  # Ensure Decimal
    transaction = TransactionHistory(
        user_id=user_id,
        transaction_type=transaction_type,
        crypto_type=crypto_type,
        amount=amount,
        description=description,
        reference_id=reference_id
    )
    db.add(transaction)
    db.commit()

@app.get("/api/admin/audit-logs", response_model=List[AdminAuditLogResponse])
async def get_admin_audit_logs(
    limit: int = 100,
    offset: int = 0,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    admin_email: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin audit logs with filtering"""
    query = db.query(AdminAuditLog).options(joinedload(AdminAuditLog.admin))
    
    if action:
        query = query.filter(AdminAuditLog.action == action)
    
    if target_type:
        query = query.filter(AdminAuditLog.target_type == target_type)
    
    if admin_email:
        query = query.join(User).filter(User.email.ilike(f"%{admin_email}%"))
    
    if start_date:
        query = query.filter(AdminAuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AdminAuditLog.created_at <= end_date)
    
    logs = query.order_by(AdminAuditLog.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return [
        AdminAuditLogResponse(
            id=log.id,
            admin_id=log.admin_id,
            admin_name=log.admin.name,
            admin_email=log.admin.email,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at
        )
        for log in logs
    ]

@app.get("/api/admin/audit-summary")
async def get_audit_summary(
    days: int = 30,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit log summary and statistics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total actions by type
    action_counts = db.query(
        AdminAuditLog.action,
        func.count(AdminAuditLog.id).label('count')
    ).filter(
        AdminAuditLog.created_at >= start_date
    ).group_by(AdminAuditLog.action).all()
    
    # Actions by admin
    admin_counts = db.query(
        User.email,
        func.count(AdminAuditLog.id).label('count')
    ).join(AdminAuditLog).filter(
        AdminAuditLog.created_at >= start_date
    ).group_by(User.email).all()
    
    # Recent critical actions
    critical_actions = db.query(AdminAuditLog).options(joinedload(AdminAuditLog.admin)).filter(
        AdminAuditLog.action.in_(['user_suspension', 'user_flag', 'deposit_rejection', 'withdrawal_rejection']),
        AdminAuditLog.created_at >= start_date
    ).order_by(AdminAuditLog.created_at.desc()).limit(10).all()
    
    return {
        "period_days": days,
        "total_actions": sum(count for _, count in action_counts),
        "actions_by_type": {action: count for action, count in action_counts},
        "actions_by_admin": {email: count for email, count in admin_counts},
        "recent_critical_actions": [
            {
                "id": log.id,
                "admin_email": log.admin.email,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "created_at": log.created_at
            }
            for log in critical_actions
        ]
    }

@app.get("/api/user/transaction-history", response_model=List[TransactionHistoryResponse])
async def get_user_transaction_history(
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    crypto_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction history with filtering"""
    query = db.query(TransactionHistory).filter(TransactionHistory.user_id == current_user.id)
    
    if transaction_type:
        query = query.filter(TransactionHistory.transaction_type == transaction_type)
    
    if crypto_type:
        query = query.filter(TransactionHistory.crypto_type == crypto_type)
    
    if start_date:
        query = query.filter(TransactionHistory.created_at >= start_date)
    
    if end_date:
        query = query.filter(TransactionHistory.created_at <= end_date)
    
    transactions = query.order_by(TransactionHistory.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return [TransactionHistoryResponse.from_orm(t) for t in transactions]

@app.get("/api/user/transaction-summary")
async def get_user_transaction_summary(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction summary statistics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total transactions by type
    transaction_counts = db.query(
        TransactionHistory.transaction_type,
        func.count(TransactionHistory.id).label('count'),
        func.sum(TransactionHistory.amount).label('total_amount')
    ).filter(
        TransactionHistory.user_id == current_user.id,
        TransactionHistory.created_at >= start_date
    ).group_by(TransactionHistory.transaction_type).all()
    
    # Daily transaction volume
    daily_volume = []
    for i in range(days):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_total = db.query(func.sum(TransactionHistory.amount)).filter(
            TransactionHistory.user_id == current_user.id,
            TransactionHistory.created_at >= day_start,
            TransactionHistory.created_at < day_end
        ).scalar() or 0
        
        daily_volume.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "volume": float(day_total)
        })
    
    return {
        "period_days": days,
        "transaction_summary": {
            t_type: {"count": count, "total_amount": float(total_amount)}
            for t_type, count, total_amount in transaction_counts
        },
        "daily_volume": daily_volume,
        "total_transactions": sum(count for _, count, _ in transaction_counts)
    }
    
@app.get("/api/admin/qr-codes")
def get_all_qr_codes(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all QR codes for admin management"""

    settings = get_or_create_admin_settings(db)

    return [
        {
            "crypto_type": "bitcoin",
            "qr_code_url": settings.bitcoin_deposit_qr,
        },
        {
            "crypto_type": "ethereum",
            "qr_code_url": settings.ethereum_deposit_qr,
        }
    ]


@app.get("/", response_model=dict)
@app.head("/")
def root():
    return {"message": "Server is running"}

@app.delete("/api/admin/qr-codes/{crypto_type}")
def delete_qr_code(
    crypto_type: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a QR code URL for a specific crypto (bitcoin/ethereum)"""

    crypto_type = crypto_type.lower()
    if crypto_type not in ["bitcoin", "ethereum"]:
        raise HTTPException(status_code=400, detail="Invalid crypto type. Must be 'bitcoin' or 'ethereum'")

    settings = get_or_create_admin_settings(db)

    # Clear the field in DB
    if crypto_type == "bitcoin":
        settings.bitcoin_deposit_qr = None
    else:
        settings.ethereum_deposit_qr = None

    db.commit()
    db.refresh(settings)

    # Log admin action
    log_admin_action(
        db=db,
        admin_id=admin_user.id,
        action=f"delete_qr_code_{crypto_type}",
        target_type="admin_settings",
        target_id=crypto_type,
        details=f"Deleted {crypto_type} QR code URL"
    )

    return {"message": f"{crypto_type.capitalize()} QR code deleted successfully"}

# Mount static files for serving uploaded images
@app.post("/api/admin/upload-qr-code")
async def upload_qr_code(
    crypto_type: str = Form(...),
    qr_code_url: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None):
    # ✅ Ensure admin access
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # ✅ Validate crypto type
    crypto_type = crypto_type.lower()
    if crypto_type not in ["bitcoin", "ethereum"]:
        raise HTTPException(status_code=400, detail="Invalid crypto type. Must be 'bitcoin' or 'ethereum'")
    
    # ✅ Validate URL format
    if not qr_code_url or not qr_code_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http:// or https://")
    
    # ✅ Update AdminSettings
    settings = get_or_create_admin_settings(db)
    if crypto_type == "bitcoin":
        settings.bitcoin_deposit_qr = qr_code_url
    else:
        settings.ethereum_deposit_qr = qr_code_url
    
    db.commit()
    db.refresh(settings)
    
    # ✅ Log admin action
    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="upload_qr_code",
        target_type="admin_settings",
        target_id=crypto_type,
        details=f"Updated {crypto_type} QR code URL",
    )
    
    return {
        "success": True,
        "message": f"QR code URL updated successfully for {crypto_type}",
        "data": {
            "crypto_type": crypto_type,
            "qr_code_url": qr_code_url
        }
    }


@app.get("/api/user/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns full user details including BTC/ETH balances and their USD equivalents.
    """
    # ---------------------
    # Calculate USD equivalents
    # ---------------------
    admin_settings = get_admin_settings(db)
    usd_values = calculate_usd_values(current_user, admin_settings) or {}

    bitcoin_balance_usd = usd_values.get("bitcoin_balance_usd", 0)
    ethereum_balance_usd = usd_values.get("ethereum_balance_usd", 0)
    total_balance_usd = usd_values.get("total_balance_usd", 0)

    # ---------------------
    # Count referred users
    # ---------------------
    referred_count = db.query(User).filter(User.referred_by_code == current_user.referral_code).count()

    return UserResponse(
        id=current_user.id,
        user_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email or "",  # ✅ must include email
        status=current_user.status,
        is_admin=current_user.is_admin,
        is_agent=current_user.is_agent,
        is_flagged=current_user.is_flagged,
        usd_balance=total_balance_usd,
        bitcoin_balance=current_user.bitcoin_balance,
        ethereum_balance=current_user.ethereum_balance,
        bitcoin_balance_usd=bitcoin_balance_usd,
        ethereum_balance_usd=ethereum_balance_usd,
        total_balance_usd=total_balance_usd,
        bitcoin_wallet=current_user.bitcoin_wallet,
        ethereum_wallet=current_user.ethereum_wallet,
        personal_mining_rate=current_user.personal_mining_rate,
        referral_code=current_user.referral_code,
        email_verified=current_user.email_verified,
        birthday_day=current_user.birthday_day,
        birthday_month=current_user.birthday_month,
        birthday_year=current_user.birthday_year,
        gender=current_user.gender,
        user_country_code=current_user.user_country_code,
        zip_code=current_user.zip_code,
        created_at=current_user.created_at,
        referred_users_count=referred_count
    )



@app.get("/api/user/withdrawals", response_model=List[WithdrawalResponse])
def get_user_withdrawals(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all withdrawals for the logged-in user.
    """
    # Fetch withdrawals
    withdrawals = (
        db.query(Withdrawal)
        .filter(Withdrawal.user_id == current_user.id)
        .order_by(Withdrawal.created_at.desc())
        .all()
    )

    # Get admin crypto rates
    admin_settings = db.query(AdminSettings).first()
    if not admin_settings:
        raise HTTPException(status_code=500, detail="Admin settings not configured")

    response = []
    for w in withdrawals:
        # Clean crypto_type string for consistency
        crypto_type_clean = str(w.crypto_type).lower()

        if crypto_type_clean in ["bitcoin", "btc", "cryptotype.bitcoin"]:
            crypto_display = "Bitcoin"
            rate = Decimal(admin_settings.bitcoin_rate_usd)
            crypto_symbol = "BTC"
        elif crypto_type_clean in ["ethereum", "eth", "cryptotype.ethereum"]:
            crypto_display = "Ethereum"
            rate = Decimal(admin_settings.ethereum_rate_usd)
            crypto_symbol = "ETH"
        else:
            # fallback for any unexpected types
            crypto_display = crypto_type_clean.capitalize()
            rate = Decimal(admin_settings.bitcoin_rate_usd)
            crypto_symbol = crypto_display[:3].upper()

        # Calculate USD dynamically
        usd_amount = float(Decimal(w.amount) * rate)

        response.append(
            WithdrawalResponse(
                id=w.id,
                crypto_type=crypto_display,       # friendly name
                amount=float(w.amount),
                usd_amount=usd_amount,
                wallet_address=w.wallet_address,
                status=w.status,
                transaction_hash=w.transaction_hash,
                created_at=w.created_at.isoformat(),  # ISO string
            )
        )

    return response


@app.post("/api/withdrawals/create", response_model=WithdrawalResponse)
def create_withdrawal(
    withdrawal: WithdrawalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new withdrawal request for the logged-in user.
    """

    # 🔒 Check if withdrawals are suspended for this user
    if getattr(current_user, "withdrawal_suspended", False):
        raise HTTPException(
            status_code=403,
            detail="Withdrawals are currently suspended for your account. Please contact support."
        )

    # Fetch admin settings for crypto rates
    admin_settings = db.query(AdminSettings).first()
    if not admin_settings:
        raise HTTPException(status_code=500, detail="Admin settings not configured")

    # Determine user balance and rate
    if withdrawal.crypto_type.value.lower() == "bitcoin":
        balance = current_user.bitcoin_balance
        rate = Decimal(admin_settings.bitcoin_rate_usd)
        crypto_display = "Bitcoin"
    else:
        balance = current_user.ethereum_balance
        rate = Decimal(admin_settings.ethereum_rate_usd)
        crypto_display = "Ethereum"

    # Check sufficient balance
    if withdrawal.amount > balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Deduct balance and update USD equivalent
    new_balance = balance - withdrawal.amount
    usd_balance = new_balance * rate

    if withdrawal.crypto_type.value.lower() == "bitcoin":
        current_user.bitcoin_balance = new_balance
        current_user.bitcoin_balance_usd = float(usd_balance)
    else:
        current_user.ethereum_balance = new_balance
        current_user.ethereum_balance_usd = float(usd_balance)

    db.add(current_user)

    # Generate unique transaction hash
    tx_hash = str(uuid.uuid4())

    # Create withdrawal record
    new_withdrawal = Withdrawal(
        user_id=current_user.id,
        crypto_type=crypto_display,
        amount=float(withdrawal.amount),
        wallet_address=withdrawal.wallet_address,
        status="pending",
        transaction_hash=tx_hash,
        created_at=datetime.utcnow(),
    )

    db.add(new_withdrawal)
    db.commit()
    db.refresh(new_withdrawal)

    # Notify user via email
    try:
        template_vars = {
            "current_user": current_user,  # pass full user object
            "transaction_id": new_withdrawal.transaction_hash,
            "crypto_type": new_withdrawal.crypto_type,
            "amount": new_withdrawal.amount,
            "usd_amount": float(Decimal(new_withdrawal.amount) * rate),
            "wallet_address": new_withdrawal.wallet_address,
            "status": new_withdrawal.status  # keep as-is, template can capitalize
        }
        email_service.send_template_email(
            to_email=current_user.email,
            subject=f"Withdrawal Request Submitted - {new_withdrawal.crypto_type}",
            template_name="withdrawal_alert.html",
            template_vars=template_vars
        )
    except Exception as e:
        logger.error(f"Failed to send withdrawal email to user: {e}")

    # Return frontend-safe response
    return WithdrawalResponse(
        id=new_withdrawal.id,
        crypto_type=new_withdrawal.crypto_type,
        amount=float(new_withdrawal.amount),
        usd_amount=float(Decimal(new_withdrawal.amount) * rate),
        wallet_address=new_withdrawal.wallet_address,
        status=new_withdrawal.status,
        transaction_hash=new_withdrawal.transaction_hash,
        created_at=new_withdrawal.created_at.isoformat(),
    )

@app.post("/api/transfers/create", response_model=CryptoTransferResponse)
def create_transfer(
    transfer_data: CryptoTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a crypto transfer between users and notify both sender and recipient.
    """

    # Validate recipient
    if transfer_data.to_email:
        recipient = db.query(User).filter(User.email == transfer_data.to_email).first()
    else:
        recipient = db.query(User).filter(User.user_id == transfer_data.to_user_id).first()

    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    if recipient.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

    # Fetch admin settings
    settings = db.query(AdminSettings).first()
    if not settings:
        raise HTTPException(status_code=500, detail="Admin settings not configured")

    # Determine crypto type and rate
    crypto_type_clean = transfer_data.crypto_type.value.lower()
    if crypto_type_clean == "bitcoin":
        rate = Decimal(settings.bitcoin_rate_usd)
        if transfer_data.amount > current_user.bitcoin_balance:
            raise HTTPException(status_code=400, detail="Insufficient Bitcoin balance")
        current_user.bitcoin_balance -= transfer_data.amount
        recipient.bitcoin_balance += transfer_data.amount
        current_user.bitcoin_balance_usd = float(current_user.bitcoin_balance * rate)
        recipient.bitcoin_balance_usd = float(recipient.bitcoin_balance * rate)
        crypto_display = "Bitcoin"
    else:
        rate = Decimal(settings.ethereum_rate_usd)
        if transfer_data.amount > current_user.ethereum_balance:
            raise HTTPException(status_code=400, detail="Insufficient Ethereum balance")
        current_user.ethereum_balance -= transfer_data.amount
        recipient.ethereum_balance += transfer_data.amount
        current_user.ethereum_balance_usd = float(current_user.ethereum_balance * rate)
        recipient.ethereum_balance_usd = float(recipient.ethereum_balance * rate)
        crypto_display = "Ethereum"

    # Generate transaction hash
    tx_hash = str(uuid.uuid4())
    usd_amount = float(Decimal(transfer_data.amount) * rate)

    # Create transfer record
    new_transfer = CryptoTransfer(
        from_user_id=current_user.id,
        to_user_id=recipient.id,
        crypto_type=crypto_display,
        amount=float(transfer_data.amount),
        usd_amount=usd_amount,
        transaction_hash=tx_hash,
        created_at=datetime.utcnow()
    )
    db.add(new_transfer)
    db.add(current_user)
    db.add(recipient)
    db.commit()
    db.refresh(new_transfer)

    # Notify sender
    try:
        email_service.send_template_email(
            to_email=current_user.email,
            subject=f"Crypto Transfer Sent - {crypto_display}",
            template_name="transfer_alert.html",
            template_vars={
                "transaction_id": tx_hash,
                "crypto_type": crypto_display,
                "amount": float(transfer_data.amount),
                "usd_amount": usd_amount,
                "to_user_name": recipient.name,
                "to_user_email": recipient.email,
                "status": "Sent"
            }
        )
    except Exception as e:
        logger.error(f"Failed to send transfer email to sender: {e}")

    # Notify recipient
    try:
        email_service.send_template_email(
            to_email=recipient.email,
            subject=f"Crypto Transfer Received - {crypto_display}",
            template_name="transfer_alert.html",
            template_vars={
                "transaction_id": tx_hash,
                "crypto_type": crypto_display,
                "amount": float(transfer_data.amount),
                "usd_amount": usd_amount,
                "from_user_name": current_user.name,
                "from_user_email": current_user.email,
                "status": "Received"
            }
        )
    except Exception as e:
        logger.error(f"Failed to send transfer email to recipient: {e}")

    # Return response
    return CryptoTransferResponse(
        id=new_transfer.id,
        crypto_type=new_transfer.crypto_type,
        amount=float(new_transfer.amount),
        usd_amount=float(new_transfer.usd_amount),
        transaction_hash=new_transfer.transaction_hash,
        created_at=new_transfer.created_at.isoformat(),
        from_user=BasicUserInfo(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name
        ),
        to_user=BasicUserInfo(
            id=recipient.id,
            email=recipient.email,
            name=recipient.name
        ),
    )


@app.get("/api/user/transfers", response_model=List[CryptoTransferResponse])
def get_user_transfers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all crypto transfers involving the logged-in user and mark
    each as sent or received based on the current user.
    """

    transfers = (
        db.query(CryptoTransfer)
        .filter(
            (CryptoTransfer.from_user_id == current_user.id) |
            (CryptoTransfer.to_user_id == current_user.id)
        )
        .order_by(CryptoTransfer.created_at.desc())
        .all()
    )

    results = []
    for t in transfers:
        # Determine direction
        if t.from_user_id == current_user.id:
            direction = "sent"
        else:
            direction = "received"

        results.append(
            CryptoTransferResponse(
                id=t.id,
                crypto_type=t.crypto_type,
                amount=float(t.amount),
                usd_amount=float(t.usd_amount),
                transaction_hash=t.transaction_hash,
                created_at=t.created_at.isoformat(),
                from_user=BasicUserInfo(
                    id=t.from_user.id,
                    email=t.from_user.email,
                    name=t.from_user.name
                ),
                to_user=BasicUserInfo(
                    id=t.to_user.id,
                    email=t.to_user.email,
                    name=t.to_user.name
                ),
                direction=direction  # new field indicating sent/received
            )
        )

    return results
    

@app.get("/api/admin/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    users = db.query(User).all()

    # Extract IP + User-Agent before logging
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="get_all_users",
        target_type="User",
        details="Fetched all users",
        ip_address=ip_address,
        user_agent=user_agent
    )

    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "bitcoin_balance": u.bitcoin_balance,
            "ethereum_balance": u.ethereum_balance,
            "is_active": u.status == "active",
            "is_suspended": u.is_suspended,
            "mining_paused": u.mining_paused,
            "withdrawal_suspended": u.withdrawal_suspended,
            "created_at": u.created_at
        }
        for u in users
    ]


# 2. Search users
@app.get("/api/admin/users/search")
def search_users(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    users = db.query(User).filter(
        or_(
            User.email.ilike(f"%{q}%"),
            User.name.ilike(f"%{q}%"),
            User.user_id.ilike(f"%{q}%")
        )
    ).all()

    log_admin_action(
        db,
        admin_id=current_user.id,
        action="search_users",
        target_type="user",
        details=f"Searched for users with query: {q}",
        request=request
    )

    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "bitcoin_balance": u.bitcoin_balance,
            "ethereum_balance": u.ethereum_balance,
            "is_active": u.status == "active",
            "is_suspended": u.is_suspended,
            "mining_paused": u.mining_paused,
            "withdrawal_suspended": u.withdrawal_suspended,
            "created_at": u.created_at
        }
        for u in users
    ]


# 3. Get user profile
@app.get("/api/admin/users/{user_id}/profile")
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # aggregate info
    total_deposits = db.query(CryptoDeposit).filter(CryptoDeposit.user_id == user.id, CryptoDeposit.status == "confirmed").count()
    total_withdrawals = db.query(Withdrawal).filter(Withdrawal.user_id == user.id, Withdrawal.status == "confirmed").count()
    mining_sessions_count = db.query(MiningSession).filter(MiningSession.user_id == user.id).count()
    referral_count = db.query(User).filter(User.referred_by_code == user.referral_code).count()

    log_admin_action(
        db,
        admin_id=current_user.id,
        action="get_user_profile",
        target_type="user",
        target_id=str(user.id),
        details=f"Fetched profile for {user.email}",
        request=request
    )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "bitcoin_balance": user.bitcoin_balance,
        "ethereum_balance": user.ethereum_balance,
        "status": user.status,
        "is_suspended": user.is_suspended,
        "mining_paused": user.mining_paused,
        "withdrawal_suspended": user.withdrawal_suspended,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "personal_mining_rate": user.personal_mining_rate,
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "mining_sessions_count": mining_sessions_count,
        "referral_count": referral_count
    }


# 4. Suspend user
@app.put("/api/admin/users/{user_id}/suspend")
def suspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_suspended = True
    db.commit()

    log_admin_action(
        db,
        admin_id=current_user.id,
        action="suspend_user",
        target_type="user",
        target_id=str(user.id),
        details=f"Suspended user {user.email}",
        request=request
    )

    return {"message": f"User {user.email} suspended successfully"}


# 5. Unsuspend user
@app.put("/api/admin/users/{user_id}/unsuspend")
def unsuspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_suspended = False
    db.commit()

    log_admin_action(
        db,
        admin_id=current_user.id,
        action="unsuspend_user",
        target_type="user",
        target_id=str(user.id),
        details=f"Unsuspended user {user.email}",
        request=request
    )

    return {"message": f"User {user.email} unsuspended successfully"}


# 6. Pause mining
@app.put("/api/admin/users/{user_id}/pause-mining")
def pause_mining(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.mining_paused = True
    db.commit()

    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="pause_mining",
        target_type="user",
        target_id=str(user.id),
        details=f"Mining paused for {user.email}",
        request=request
    )

    return {"message": f"Mining paused for {user.email}"}


# 7. Resume mining
@app.put("/api/admin/users/{user_id}/resume-mining")
def resume_mining(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.mining_paused = False
    db.commit()

    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="resume_mining",
        target_type="user",
        target_id=str(user.id),
        details=f"Mining resumed for {user.email}",
        request=request
    )

    return {"message": f"Mining resumed for {user.email}"}


# 8. Suspend withdrawals
@app.put("/api/admin/users/{user_id}/suspend-withdrawals")
def suspend_withdrawals(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.withdrawal_suspended = True
    db.commit()

    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="suspend_withdrawals",
        target_type="user",
        target_id=str(user.id),
        details=f"Withdrawals suspended for {user.email}",
        request=request
    )

    return {"message": f"Withdrawals suspended for {user.email}"}


# 9. Enable withdrawals
@app.put("/api/admin/users/{user_id}/enable-withdrawals")
def enable_withdrawals(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.withdrawal_suspended = False
    db.commit()

    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="enable_withdrawals",
        target_type="user",
        target_id=str(user.id),
        details=f"Withdrawals enabled for {user.email}",
        request=request
    )

    return {"message": f"Withdrawals enabled for {user.email}"}


# 10. Reset password (admin action)
@app.put("/api/admin/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a temporary random password
    import secrets, string
    temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    user.password_hash = hash_password(temp_password)
    db.commit()

    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="reset_password",
        target_type="user",
        target_id=str(user.id),
        details=f"Password reset for {user.email}",
        request=request
    )

    return {"message": f"Password reset successfully for {user.email}", "temporary_password": temp_password}


# 11. Set personal mining rate
@app.put("/api/admin/users/{user_id}/set-mining-rate")
def set_personal_mining_rate(
    user_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    rate = body.get("mining_rate")

    # Convert string to float (so "90" works)
    try:
        rate = float(rate)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Mining rate must be a number")

    # Validate as percentage 0–100
    if not (0 <= rate <= 100):
        raise HTTPException(status_code=400, detail="Invalid mining rate. Must be between 0 and 100")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Store as percentage directly
    user.personal_mining_rate = rate
    db.commit()

    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="set_mining_rate",
        target_type="user",
        target_id=str(user.id),
        details=f"Set personal mining rate to {rate} for {user.email}",
        request=request
    )

    return {"message": f"Mining rate set for {user.email}", "rate": rate}

# 12. Clear personal mining rate (use global)
@app.put("/api/admin/users/{user_id}/clear-mining-rate")
def clear_personal_mining_rate(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.personal_mining_rate = None
    db.commit()

    log_admin_action(
        db=db,
        admin_id=current_user.id,
        action="clear_mining_rate",
        target_type="user",
        target_id=str(user.id),
        details=f"Cleared personal mining rate for {user.email}",
        request=request
    )

    return {"message": f"Personal mining rate cleared for {user.email}"}


# 13. View transaction/admin logs
@app.get("/api/admin/logs/transactions")
def get_admin_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    logs = db.query(AdminActionLog).order_by(AdminActionLog.created_at.desc()).all()

    return [
        {
            "id": log.id,
            "admin_id": log.admin_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        }
        for log in logs
    ]


@app.get("/api/admin/dashboard/stats")
def admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Total users
    total_users = db.query(User).count()

    # Total confirmed deposits
    total_deposits = db.query(CryptoDeposit) \
        .filter(CryptoDeposit.status == "confirmed") \
        .with_entities(func.coalesce(func.sum(CryptoDeposit.amount), 0)).scalar()

    # Total crypto distributed via internal transfers
    total_crypto_distributed = db.query(CryptoTransfer) \
        .with_entities(func.coalesce(func.sum(CryptoTransfer.amount), 0)).scalar()

    # Pending withdrawals
    pending_withdrawals = db.query(Withdrawal) \
        .filter(Withdrawal.status == "pending") \
        .with_entities(func.coalesce(func.sum(Withdrawal.amount), 0)).scalar()

    # Active mining sessions
    active_mining_sessions = db.query(MiningSession) \
        .filter(MiningSession.is_active == True).count()

    return {
        "total_users": total_users,
        "total_deposits": float(total_deposits or 0),
        "total_crypto_distributed": float(total_crypto_distributed or 0),
        "pending_withdrawals": float(pending_withdrawals or 0),
        "active_mining_sessions": active_mining_sessions,
    }

@app.get("/api/admin/settings")
def get_admin_settings_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    settings = db.query(AdminSettings).first()
    if not settings:
        settings = AdminSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "bitcoin_rate_usd": float(settings.bitcoin_rate_usd),
        "ethereum_rate_usd": float(settings.ethereum_rate_usd),
        "global_mining_rate": settings.global_mining_rate,
        "bitcoin_wallet_address": settings.bitcoin_wallet_address or "",
        "ethereum_wallet_address": settings.ethereum_wallet_address or "",
        "referral_reward_enabled": settings.referral_reward_enabled,
        "referral_reward_type": settings.referral_reward_type,
        "referrer_reward_percent": settings.referrer_reward_percent,  # percentage-based
    }

@app.put("/api/admin/settings")
def update_admin_settings(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Fetch existing settings or create default
    settings = db.query(AdminSettings).first()
    if not settings:
        settings = AdminSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    # Fields allowed to update
    for field in [
        "bitcoin_rate_usd",
        "ethereum_rate_usd",
        "global_mining_rate",
        "bitcoin_wallet_address",
        "ethereum_wallet_address",
        "referral_reward_enabled",
        "referral_reward_type",
        "referrer_reward_percent",
    ]:
        if field in data:
            value = data[field]

            # special handling for global_mining_rate
            if field == "global_mining_rate":
                try:
                    value = float(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid mining rate")

                # ✅ Store directly as percentage (0–100)
                if not (0 <= value <= 100):
                    raise HTTPException(status_code=400, detail="Mining rate must be between 0 and 100%")

            setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return {"message": "Settings updated successfully"}

@app.on_event("startup")
@repeat_every(seconds=3600)  # every hour
def update_crypto_rates():
    db: Session = next(get_db())
    try:
        btc_response = httpx.get(BTC_API_URL, timeout=10)
        eth_response = httpx.get(ETH_API_URL, timeout=10)

        btc_data = btc_response.json()
        eth_data = eth_response.json()

        print("BTC raw response:", btc_data)
        print("ETH raw response:", eth_data)

        btc_usd = float(btc_data["quotes"]["USD"]["price"])
        eth_usd = float(eth_data["quotes"]["USD"]["price"])

        settings = db.query(AdminSettings).first()
        if not settings:
            settings = AdminSettings()
            db.add(settings)

        settings.bitcoin_rate_usd = btc_usd
        settings.ethereum_rate_usd = eth_usd
        db.commit()
        print(f"Updated BTC={btc_usd}, ETH={eth_usd}")
    except Exception as e:
        print("Failed to update crypto rates:", e)
    finally:
        db.close()


@app.get("/api/admin/withdrawals/pending")
def get_pending_withdrawals(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all pending withdrawals for admin confirmation"""
    withdrawals = (
        db.query(Withdrawal)
        .options(joinedload(Withdrawal.user))  # eager load user
        .filter(Withdrawal.status == WithdrawalStatus.PENDING)
        .order_by(Withdrawal.created_at.desc())
        .all()
    )

    return [
        {
            "id": w.id,
            "user_email": w.user.email if w.user else None,
            "crypto_type": w.crypto_type,
            "amount": w.amount,
            "wallet_address": w.wallet_address,
            "transaction_hash": str(w.transaction_hash) if w.transaction_hash is not None else "",
            "created_at": w.created_at
        }
        for w in withdrawals
    ]


@app.put("/api/admin/withdrawals/{withdrawal_id}/confirm")
async def confirm_withdrawal(
    withdrawal_id: int,
    action: str = Query(..., regex="^(confirm|reject)$"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Confirm or reject a withdrawal and notify the user via email with full details.
    """

    # Fetch the withdrawal
    withdrawal = db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id).first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")

    if withdrawal.status != WithdrawalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Withdrawal already processed")

    # Fetch the user
    user = db.query(User).filter(User.id == withdrawal.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch admin settings for crypto rates
    admin_settings = db.query(AdminSettings).first()
    if not admin_settings:
        raise HTTPException(status_code=500, detail="Admin settings not configured")

    usd_amount = float(
        withdrawal.amount * Decimal(
            admin_settings.bitcoin_rate_usd if withdrawal.crypto_type.lower() == "bitcoin" else admin_settings.ethereum_rate_usd
        )
    )

    # Determine action and update withdrawal
    if action == "confirm":
        withdrawal.status = WithdrawalStatus.APPROVED
        email_status = "Approved"
        log_action_type = "confirm_withdrawal"
        log_details = f"Approved withdrawal of {withdrawal.amount} {withdrawal.crypto_type} for user {user.email}"
    else:  # reject
        withdrawal.status = WithdrawalStatus.REJECTED
        email_status = "Rejected"
        log_action_type = "reject_withdrawal"
        log_details = f"Rejected withdrawal of {withdrawal.amount} {withdrawal.crypto_type} for user {user.email}"

        # Refund user balance on rejection
        if withdrawal.crypto_type.lower() == "bitcoin":
            user.bitcoin_balance += withdrawal.amount
        else:
            user.ethereum_balance += withdrawal.amount
        db.add(user)

    withdrawal.processed_at = datetime.utcnow()
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)

    # Send email notification
    try:
        email_service.send_template_email(
            to_email=user.email,
            subject=f"Withdrawal {email_status} - {withdrawal.crypto_type}",
            template_name="withdrawal_status_alert.html",
            template_vars={
                "transaction_id": withdrawal.transaction_hash,
                "crypto_type": withdrawal.crypto_type,
                "amount": withdrawal.amount,
                "usd_amount": usd_amount,
                "wallet_address": withdrawal.wallet_address,
                "status": email_status,
                "user": user
            }
        )
    except Exception as e:
        logger.error(f"Failed to send withdrawal {email_status.lower()} email to user: {e}")

    # Log admin action
    log_admin_action(
        db=db,
        admin_id=admin_user.id,
        action=log_action_type,
        target_type="withdrawal",
        target_id=str(withdrawal.id),
        details=log_details,
        ip_address="System",
        user_agent="System"
    )

    return {
        "message": f"Withdrawal {email_status.lower()} successfully",
        "withdrawal_id": withdrawal.id,
        "status": withdrawal.status.value if hasattr(withdrawal.status, "value") else withdrawal.status
    }
    


@app.get("/health")
@app.head("/health")
def health_check():
    return {"status": "ok", "message": "Backend is awake and running"}
