import * as React from "react";

export default function MarketingTemplate() {
  return (
    <div
      style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        backgroundColor: "#f4f4f7",
        padding: "40px 0",
        color: "#333",
      }}
    >
      <div
        style={{
          backgroundColor: "#ffffff",
          maxWidth: "600px",
          margin: "0 auto",
          borderRadius: "10px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.1)",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            backgroundColor: "#0057e7",
            color: "#ffffff",
            padding: "25px 20px",
            textAlign: "center",
            fontSize: "20px",
            fontWeight: "bold",
          }}
        >
          Smart S9 Trading
        </div>

        {/* Body */}
        <div style={{ padding: "30px 25px" }}>
          <h2
            style={{
              fontSize: "22px",
              marginBottom: "15px",
              color: "#111",
              textAlign: "center",
            }}
          >
            Earn Daily Profits with Smart S9
          </h2>

          <p
            style={{
              fontSize: "16px",
              lineHeight: "1.6",
              color: "#444",
              marginBottom: "25px",
            }}
          >
            At <strong>Smart S9 Trading</strong>, our fully automated trading
            system analyzes the crypto market in real-time, executes profitable
            trades, and sends instant payouts directly to your wallet — no
            manual trading experience required.
          </p>

          <p
            style={{
              fontSize: "16px",
              lineHeight: "1.6",
              color: "#444",
              marginBottom: "25px",
            }}
          >
            Join thousands of active users earning consistent profits daily.
            With Smart S9, you can grow your portfolio automatically with
            minimal risk and full transparency.
          </p>

          {/* CTA Button */}
          <div style={{ textAlign: "center", margin: "30px 0" }}>
            <a
              href="https://smarts9.com/dashboard"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                backgroundColor: "#0057e7",
                color: "#ffffff",
                padding: "14px 28px",
                borderRadius: "6px",
                textDecoration: "none",
                fontWeight: "bold",
                display: "inline-block",
              }}
            >
              Start Trading Now
            </a>
          </div>

          <p
            style={{
              fontSize: "15px",
              color: "#444",
              marginTop: "25px",
            }}
          >
            <strong>Why choose Smart S9?</strong>
          </p>

          <ul
            style={{
              paddingLeft: "20px",
              color: "#444",
              lineHeight: "1.6",
              fontSize: "15px",
            }}
          >
            <li>Up to 70% daily profit potential</li>
            <li>Instant automated payouts</li>
            <li>Trusted by over 10,000 active users</li>
            <li>Zero trading knowledge required</li>
          </ul>

          {/* Note */}
          <p
            style={{
              fontSize: "13px",
              color: "#888",
              marginTop: "30px",
              textAlign: "center",
            }}
          >
            You are receiving this email because you interacted with Smart S9
            Trading. If you no longer wish to receive updates, you can ignore
            this message.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          textAlign: "center",
          fontSize: "12px",
          color: "#999",
          marginTop: "20px",
        }}
      >
        © {new Date().getFullYear()} Smart S9 Trading. All rights reserved.
      </div>
    </div>
  );
}
