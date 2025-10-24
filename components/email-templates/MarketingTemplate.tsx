import React from "react";

export default function MarketingTemplate({
  title = "Earn Daily Profits with Smart S9",
  message = `At Smart S9 Trading, our fully automated trading system analyzes the crypto market in real-time, executes profitable trades, and sends instant payouts directly to your wallet — no manual trading experience required.`,
  ctaLoginText = "Login Now",
  ctaSignupText = "Sign Up",
  loginLink = "https://smarts9trading.online/login",
  signupLink = "https://smarts9trading.online/signup",
  heroImage = "https://smarts9trading.online/public/bitcoin-mining-interface-with-hash-rate-charts-and.png",
  accessDetails = { time: "", ip: "", location: "", device: "" },
}) {
  return (
    <div
      style={{
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        backgroundColor: "#f5f7fa",
        color: "#333",
        padding: "40px 0",
        width: "100%",
      }}
    >
      <div
        style={{
          maxWidth: "600px",
          margin: "0 auto",
          backgroundColor: "#fff",
          borderRadius: "8px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.05)",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            background: "linear-gradient(135deg,#22c55e 0%,#15803d 100%)",
            padding: "25px 20px",
            textAlign: "center",
            color: "#fff",
          }}
        >
          <img
            src="https://smarts9trading.online/public/logo.png"
            alt="Smart S9 Trading"
            style={{ height: "50px", marginBottom: "10px" }}
          />
          <h2 style={{ color: "#fff", margin: 0 }}>Smart S9 Trading</h2>
        </div>

        {/* Hero Image */}
        <div style={{ textAlign: "center", margin: "20px 0" }}>
          <img
            src={heroImage}
            alt="Crypto Trading Dashboard"
            style={{ width: "100%", maxWidth: "560px", borderRadius: "8px" }}
          />
        </div>

        {/* Body */}
        <div style={{ padding: "30px" }}>
          <h1
            style={{
              fontSize: "24px",
              color: "#111827",
              marginBottom: "20px",
              textAlign: "center",
            }}
          >
            {title}
          </h1>

          <p
            style={{
              fontSize: "16px",
              lineHeight: "1.6",
              color: "#374151",
              marginBottom: "25px",
              textAlign: "center",
            }}
          >
            {message}
          </p>

          {/* CTA Buttons */}
          <div style={{ textAlign: "center", margin: "30px 0" }}>
            <a
              href={loginLink}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                backgroundColor: "#22c55e",
                color: "#fff",
                padding: "14px 28px",
                borderRadius: "6px",
                textDecoration: "none",
                fontWeight: "bold",
                marginRight: "10px",
                display: "inline-block",
              }}
            >
              {ctaLoginText} →
            </a>
            <a
              href={signupLink}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                backgroundColor: "#15803d",
                color: "#fff",
                padding: "14px 28px",
                borderRadius: "6px",
                textDecoration: "none",
                fontWeight: "bold",
                display: "inline-block",
              }}
            >
              {ctaSignupText} →
            </a>
          </div>

          {/* Optional Access Details */}
          {accessDetails.time && (
            <div
              style={{
                background: "#ecfdf5",
                border: "2px solid #16a34a",
                padding: "20px",
                borderRadius: "12px",
                margin: "25px 0",
                textAlign: "center",
              }}
            >
              <h3 style={{ color: "#15803d", margin: "0 0 10px 0" }}>Access Details</h3>
              <div style={{ fontSize: "16px", margin: "8px 0", color: "#065f46" }}>
                <strong>Time:</strong> {accessDetails.time}
              </div>
              <div style={{ fontSize: "16px", margin: "8px 0", color: "#065f46" }}>
                <strong>IP Address:</strong> {accessDetails.ip}
              </div>
              <div style={{ fontSize: "16px", margin: "8px 0", color: "#065f46" }}>
                <strong>Location:</strong> {accessDetails.location}
              </div>
              <div style={{ fontSize: "16px", margin: "8px 0", color: "#065f46" }}>
                <strong>Device:</strong> {accessDetails.device}
              </div>
            </div>
          )}

          {/* Info Section */}
          <div
            style={{
              background: "#f8fafc",
              padding: "20px",
              borderRadius: "8px",
              margin: "20px 0",
            }}
          >
            <h3 style={{ color: "#374151", margin: "0 0 15px 0" }}>Why choose Smart S9?</h3>
            <ul style={{ paddingLeft: "20px", color: "#374151", lineHeight: "1.6", fontSize: "15px" }}>
              <li>💰 Up to 70% daily profit potential</li>
              <li>⚡ Instant automated payouts</li>
              <li>👥 Trusted by over 10,000 active users</li>
              <li>📝 Zero trading knowledge required</li>
            </ul>
          </div>

          {/* Security Notice */}
          <div
            style={{
              background: "#fef3c7",
              border: "1px solid #fbbf24",
              padding: "15px",
              borderRadius: "8px",
              margin: "20px 0",
              fontSize: "14px",
              color: "#92400e",
            }}
          >
            <strong>⚠ Security Notice:</strong> Never share your login details. If this wasn’t you, please contact support immediately.
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          textAlign: "center",
          fontSize: "12px",
          color: "#fff",
          marginTop: "20px",
          background: "linear-gradient(135deg,#22c55e 0%,#15803d 100%)",
          padding: "25px 20px",
        }}
      >
        &copy; {new Date().getFullYear()} Smart S9 Trading. All rights reserved.
        <div style={{ marginTop: "10px" }}>
          {/* Social Icons */}
          <a href="https://twitter.com/smarts9" style={{ margin: "0 5px" }}>
            <img
              src="https://cdn-icons-png.flaticon.com/24/733/733579.png"
              alt="Twitter"
            />
          </a>
          <a href="https://facebook.com/smarts9" style={{ margin: "0 5px" }}>
            <img
              src="https://cdn-icons-png.flaticon.com/24/733/733547.png"
              alt="Facebook"
            />
          </a>
          <a href="https://instagram.com/smarts9" style={{ margin: "0 5px" }}>
            <img
              src="https://cdn-icons-png.flaticon.com/24/733/733558.png"
              alt="Instagram"
            />
          </a>
        </div>
      </div>
    </div>
  );
}
