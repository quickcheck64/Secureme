import * as React from "react";

interface MarketingTemplateProps {
  title: string;
  message: string;
  ctaLink?: string;
  ctaText?: string;
}

export default function MarketingTemplate({
  title,
  message,
  ctaLink,
  ctaText,
}: MarketingTemplateProps) {
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
          <h2 style={{ fontSize: "22px", marginBottom: "15px", color: "#111" }}>
            {title}
          </h2>
          <p
            style={{
              fontSize: "16px",
              lineHeight: "1.6",
              color: "#444",
              marginBottom: "25px",
            }}
            dangerouslySetInnerHTML={{ __html: message }}
          ></p>

          {ctaLink && ctaText && (
            <div style={{ textAlign: "center", marginBottom: "30px" }}>
              <a
                href={ctaLink}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  backgroundColor: "#0057e7",
                  color: "#ffffff",
                  padding: "12px 24px",
                  borderRadius: "6px",
                  textDecoration: "none",
                  fontWeight: "bold",
                  display: "inline-block",
                }}
              >
                {ctaText}
              </a>
            </div>
          )}

          <p
            style={{
              fontSize: "13px",
              color: "#888",
              marginTop: "30px",
              textAlign: "center",
            }}
          >
            This email was sent to you by Smart S9 Trading.  
            If you no longer wish to receive updates, please ignore this message.
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
