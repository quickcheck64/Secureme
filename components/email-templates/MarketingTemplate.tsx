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
    <html>
      <body
        style={{
          fontFamily: "Arial, sans-serif",
          backgroundColor: "#f9f9f9",
          padding: "20px",
          color: "#333",
        }}
      >
        <table
          width="100%"
          style={{
            maxWidth: "600px",
            margin: "0 auto",
            backgroundColor: "#ffffff",
            borderRadius: "10px",
            overflow: "hidden",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
        >
          <tr>
            <td
              style={{
                backgroundColor: "#0D6EFD",
                color: "#ffffff",
                textAlign: "center",
                padding: "20px 10px",
              }}
            >
              <h1 style={{ margin: 0, fontSize: "24px" }}>Smart S9 Trading</h1>
            </td>
          </tr>

          <tr>
            <td style={{ padding: "30px 25px" }}>
              <h2 style={{ color: "#222", marginTop: 0 }}>{title}</h2>
              <p style={{ lineHeight: "1.6", fontSize: "15px" }}>{message}</p>

              {ctaLink && (
                <div style={{ textAlign: "center", marginTop: "25px" }}>
                  <a
                    href={ctaLink}
                    style={{
                      backgroundColor: "#0D6EFD",
                      color: "#fff",
                      textDecoration: "none",
                      padding: "12px 24px",
                      borderRadius: "6px",
                      fontWeight: "bold",
                      display: "inline-block",
                    }}
                  >
                    {ctaText || "Learn More"}
                  </a>
                </div>
              )}
            </td>
          </tr>

          <tr>
            <td
              style={{
                backgroundColor: "#f1f1f1",
                textAlign: "center",
                padding: "15px",
                fontSize: "13px",
                color: "#777",
              }}
            >
              © {new Date().getFullYear()} Smart S9 Trading. All rights reserved.<br />
              <a
                href="#"
                style={{ color: "#0D6EFD", textDecoration: "none" }}
              >
                Unsubscribe
              </a>
            </td>
          </tr>
        </table>
      </body>
    </html>
  );
}
