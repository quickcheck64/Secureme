import { render } from "@react-email/render"
import nodemailer from "nodemailer"
import RegistrationEmail from "../../../components/email-templates/RegistrationEmail"
import ContactEmail from "../../../components/email-templates/ContactEmail"

// ✅ List of allowed frontend origins
const ALLOWED_ORIGINS = [
  "https://chainminer.netlify.app",
  "https://your-other-frontend.com"
]

export async function POST(request: Request) {
  // Handle preflight (OPTIONS) requests for CORS
  if (request.method === "OPTIONS") {
    const origin = request.headers.get("Origin") || ""
    const headers: Record<string, string> = {
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    }

    if (ALLOWED_ORIGINS.includes(origin)) {
      headers["Access-Control-Allow-Origin"] = origin
    }

    return new Response(null, { headers })
  }

  const origin = request.headers.get("Origin") || ""
  const corsHeaders: Record<string, string> = {}
  if (ALLOWED_ORIGINS.includes(origin)) {
    corsHeaders["Access-Control-Allow-Origin"] = origin
  }

  try {
    const { type, data } = await request.json()

    const step =
      type === "signup" ? "registration" :
      type === "contact" ? "contact" :
      null

    if (!step) {
      return new Response(JSON.stringify({ success: false, error: "Invalid email type" }), { status: 400, headers: corsHeaders })
    }

    const smtpUser = process.env.SMTP_USER
    const smtpPass = process.env.SMTP_PASS
    const receiverEmail = process.env.RECEIVER_EMAIL

    if (!smtpUser || !smtpPass || !receiverEmail) {
      return new Response(JSON.stringify({ success: false, error: "Email service not configured" }), { status: 500, headers: corsHeaders })
    }

    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: { user: smtpUser, pass: smtpPass },
    })

    const timestamp = new Date().toISOString()
    let subject = ""
    let emailHtml = ""

    if (step === "registration") {
      const { name, email, phone } = data
      subject = `New Signup - ${name} (${email}) [${timestamp}]`
      emailHtml = render(<RegistrationEmail name={name} email={email} phone={phone} />)
    } else if (step === "contact") {
      const { name, email, subject: contactSubject, category, message } = data
      subject = `New Contact Message - ${contactSubject || category} (${name}) [${timestamp}]`
      emailHtml = render(<ContactEmail name={name} email={email} category={category} message={message} />)
    }

    const info = await transporter.sendMail({
      from: `"Smart S9Trading" <${smtpUser}>`,
      to: receiverEmail,
      subject,
      html: emailHtml,
      text: step === "registration"
        ? `New signup from ${data.name} (${data.email}), phone: ${data.phone}`
        : `Contact message from ${data.name} (${data.email}): ${data.message}`,
    })

    console.log("[v0] Email sent successfully:", info.messageId)
    return new Response(JSON.stringify({ success: true }), { status: 200, headers: corsHeaders })
  } catch (error: any) {
    console.error("[v0] Email API error:", error)
    return new Response(JSON.stringify({
      success: false,
      error: "Failed to send email",
      details: error?.message || "Unknown error"
    }), { status: 500, headers: corsHeaders })
  }
}
