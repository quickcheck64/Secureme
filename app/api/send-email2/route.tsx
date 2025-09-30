import nodemailer from "nodemailer"

// Only authorized backend requests can send emails
const AUTH_TOKEN = process.env.API_AUTH_TOKEN // set this in env

export async function POST(request: Request) {
  try {
    const authHeader = request.headers.get("Authorization")
    if (!authHeader || authHeader !== `Bearer ${AUTH_TOKEN}`) {
      return Response.json({ success: false, error: "Unauthorized" }, { status: 401 })
    }

    const { to, subject, html, text } = await request.json()

    if (!to || !subject || !html) {
      return Response.json(
        { success: false, error: "Missing required fields: to, subject, html" },
        { status: 400 }
      )
    }

    const smtpUser = process.env.SMTP_USER
    const smtpPass = process.env.SMTP_PASS

    if (!smtpUser || !smtpPass) {
      console.log("[v1] Missing SMTP credentials")
      return Response.json({ success: false, error: "Email service not configured" }, { status: 500 })
    }

    // Setup SMTP transporter
    const transporter = nodemailer.createTransport({
      service: "gmail", // or use any SMTP service
      auth: {
        user: smtpUser,
        pass: smtpPass,
      },
    })

    const response = await transporter.sendMail({
      from: `"Smart S9miner" <${smtpUser}>`,
      to,
      subject,
      html,
      text: text || "", // fallback if no plain text provided
    })

    console.log("[v1] Email sent successfully:", response.messageId)

    return Response.json({ success: true, messageId: response.messageId })
  } catch (error: any) {
    console.log("[v1] Email API error:", error)
    return Response.json(
      { success: false, error: "Failed to send email", details: error?.message || "Unknown error" },
      { status: 500 }
    )
  }
}
