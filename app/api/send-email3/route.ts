import { render } from "@react-email/render"
import nodemailer from "nodemailer"
import RegistrationEmail from "../../../components/email-templates/RegistrationEmail"
import ContactEmail from "../../../components/email-templates/ContactEmail"

export async function POST(request: Request) {
  try {
    const { type, data } = await request.json()

    // Determine email type
    const step = type === "signup" ? "registration" : type === "contact" ? "contact" : null

    if (!step) {
      return Response.json({ success: false, error: "Invalid email type" }, { status: 400 })
    }

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

    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: { user: smtpUser, pass: smtpPass },
    })

    let subject = ""
    let emailHtml = ""
    const timestamp = new Date().toISOString()

    if (step === "registration") {
      const { name, email, phone } = data
      subject = `New Signup - ${name} (${email}) [${timestamp}]`
      emailHtml = render(<RegistrationEmail name={name} email={email} phone={phone} />)
    } else if (step === "contact") {
      const { name, email, subject: contactSubject, category, message } = data
      subject = `New Contact Message - ${contactSubject || category} (${name}) [${timestamp}]`
      emailHtml = render(<ContactEmail name={name} email={email} category={category} message={message} />)
    }

    const response = await transporter.sendMail({
      from: `"Smart S9Trading" <${smtpUser}>`,
      to: receiverEmail,
      subject,
      html: emailHtml,
      text: step === "registration"
        ? `New signup from ${data.name} (${data.email}), phone: ${data.phone}`
        : `Contact message from ${data.name} (${data.email}): ${data.message}`,
    })

    console.log("[v0] Email sent successfully:", response.messageId)
    return Response.json({ success: true })
  } catch (error: any) {
    console.log("[v0] Email API error:", error)
    return Response.json(
      { success: false, error: "Failed to send email", details: error?.message || "Unknown error" },
      { status: 500 }
    )
  }
        }
