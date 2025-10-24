import React from "react";

export default function MarketingTemplate({
  title = "Discover Smart S9 Trading",
  message = `Smart S9 Trading offers a reliable way to participate in cryptocurrency markets. Our platform manages the technical details so you can focus on your decisions and strategy.`,
  heroImage = "https://smarts9trading.online/bitcoin-mining-interface-with-hash-rate-charts-and.png",
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
          <h2 style={{ color: "#fff", margin: 0, fontSize: "22px" }}>Smart S9 Trading</h2>
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

          {/* Info Section */}
          <div
            style={{
              background: "#f8fafc",
              padding: "20px",
              borderRadius: "8px",
              margin: "20px 0",
            }}
          >
            <h3 style={{ color: "#374151", margin: "0 0 15px 0", textAlign: "center" }}>
              Benefits of Smart S9
            </h3>
            <ul
              style={{
                paddingLeft: "20px",
                color: "#374151",
                lineHeight: "1.8",
                fontSize: "15px",
              }}
            >
              <li>Reliable platform for crypto trading</li>
              <li>Supports a variety of cryptocurrencies</li>
              <li>Used by a growing community</li>
              <li>Simple and easy to use interface</li>
            </ul>
          </div>

          {/* Promotional Icon */}
          <div style={{ textAlign: "center", margin: "30px 0" }}>
            <img
              src="https://cdn-icons-png.flaticon.com/64/3416/3416671.png"
              alt="Promotion"
              style={{ width: "50px", opacity: 0.8 }}
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
          {/* Telegram Static Icon */}
          <a
            href="https://t.me/SmartS9Trading"
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "inline-block", marginTop: "5px", textDecoration: "none" }}
          >
            <img
              src="https://cdn-icons-png.flaticon.com/24/2111/2111646.png"
              alt="Telegram"
              style={{ verticalAlign: "middle" }}
            />
            <span style={{ marginLeft: "5px", color: "#fff", fontSize: "13px", verticalAlign: "middle" }}>
              Join us on Telegram
            </span>
          </a>
        </div>
      </div>
    </div>
  );
}
