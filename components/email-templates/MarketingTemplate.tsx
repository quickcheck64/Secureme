import React from "react";

export default function MarketingTemplate({
  title = "Explore Smart S9 Trading",
  message = `Smart S9 Trading is a reliable platform for participating in cryptocurrency markets. The platform provides the tools you need to explore crypto trading effectively.`,
  heroImage = "https://smarts9trading.online/bitcoin-mining-interface-with-hash-rate-charts-and.png",
  websiteLink = "https://smarts9trading.online",
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
            padding: "20px",
            textAlign: "center",
            color: "#fff",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "22px" }}>Smart S9 Trading</h2>
        </div>

        {/* Hero Image */}
        <div style={{ textAlign: "center", margin: "20px 0" }}>
          <img
            src={heroImage}
            alt="Crypto Trading Dashboard"
            style={{ width: "90%", maxWidth: "500px", borderRadius: "8px", display: "block", margin: "0 auto" }}
          />
        </div>

        {/* Body */}
        <div style={{ padding: "30px" }}>
          <h1
            style={{
              fontSize: "22px",
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

          {/* Promotional Paragraph */}
          <div
            style={{
              background: "#ecfdf5",
              border: "1px solid #16a34a",
              padding: "20px",
              borderRadius: "8px",
              marginBottom: "25px",
              textAlign: "center",
              color: "#065f46",
              fontSize: "15px",
            }}
          >
            Earn up to <strong>70% daily profits</strong> as a trader, with guaranteed earnings on the platform.  
            Invite active traders and get <strong>10% lifetime commission</strong> on every trade they make.
          </div>

          {/* CTA Button */}
          <div style={{ textAlign: "center", marginBottom: "25px" }}>
            <a
              href={websiteLink}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                backgroundColor: "#22c55e",
                color: "#fff",
                padding: "14px 28px",
                borderRadius: "6px",
                textDecoration: "none",
                fontWeight: "bold",
                fontSize: "16px",
                display: "inline-block",
              }}
            >
              Start Trading Now
            </a>
          </div>

          {/* Benefits Section */}
          <div
            style={{
              background: "#f8fafc",
              padding: "20px",
              borderRadius: "8px",
              marginBottom: "25px",
            }}
          >
            <h3 style={{ color: "#374151", textAlign: "center", marginBottom: "15px" }}>
              Platform Highlights
            </h3>
            <ul
              style={{
                paddingLeft: "20px",
                color: "#374151",
                lineHeight: "1.8",
                fontSize: "15px",
              }}
            >
              <li>Professional interface for trading cryptocurrencies</li>
              <li>Supports multiple digital currencies</li>
              <li>Growing community of users</li>
              <li>Easy-to-use navigation and features</li>
            </ul>
          </div>

          {/* Subtle Promotional Icon */}
          <div style={{ textAlign: "center", marginTop: "20px" }}>
            <img
              src="https://cdn-icons-png.flaticon.com/64/3416/3416671.png"
              alt="Promotion"
              style={{ width: "50px", opacity: 0.7 }}
            />
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
          {/* Telegram */}
          <a
            href="https://t.me/SmartS9Trading"
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "inline-block", marginTop: "5px", textDecoration: "none", color: "#fff" }}
          >
            <img
              src="https://cdn-icons-png.flaticon.com/24/2111/2111646.png"
              alt="Telegram"
              style={{ verticalAlign: "middle", marginRight: "5px" }}
            />
            Join us on Telegram
          </a>
        </div>
      </div>
    </div>
  );
}
