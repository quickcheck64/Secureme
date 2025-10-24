import nodemailer from "nodemailer";
import { render } from "@react-email/render";
import MarketingTemplate from "../../../components/email-templates/MarketingTemplate";

export async function POST(request: Request) {
  try {
    // ✅ Extract request data
    const { emails } = await request.json();
    if (!emails) {
      return new Response(JSON.stringify({ success: false, error: "Missing emails" }), {
        status: 400,
      });
    }

    // 🧹 Clean email list
    const emailList = Array.isArray(emails)
      ? emails.filter((e) => e.includes("@"))
      : emails
          .split(/[\n,; ]+/)
          .map((e) => e.trim())
          .filter((e) => e.includes("@"));

    if (emailList.length === 0) {
      return new Response(
        JSON.stringify({ success: false, error: "No valid email addresses provided" }),
        { status: 400 }
      );
    }

    // ✅ Gmail SMTP setup
    const smtpUser = process.env.SMTP_USER;
    const smtpPass = process.env.SMTP_PASS;
    if (!smtpUser || !smtpPass) {
      return new Response(
        JSON.stringify({ success: false, error: "Gmail SMTP not configured" }),
        { status: 500 }
      );
    }

    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: { user: smtpUser, pass: smtpPass },
    });

    // ✅ Render the fixed email template (handles message + CTA)
    const subject = "Smart S9Trading – New Investment Opportunity";
    const html = render(<MarketingTemplate />);

    // ✅ Send emails sequentially
    let sentCount = 0;
    let failedCount = 0;

    for (const email of emailList) {
      try {
        await transporter.sendMail({
          from: `"Smart S9Trading" <${smtpUser}>`,
          to: email,
          subject,
          html,
        });
        console.log(`✅ Sent to ${email}`);
        sentCount++;
      } catch (err: any) {
        console.error(`❌ Failed to send to ${email}:`, err.message);
        failedCount++;
      }

      // ⏳ delay between sends (avoid Gmail spam filter)
      await new Promise((res) => setTimeout(res, 1500));
    }

    return new Response(
      JSON.stringify({ success: true, sent: sentCount, failed: failedCount }),
      { status: 200 }
    );
  } catch (error: any) {
    console.error("Bulk Gmail error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: "Failed to send bulk email",
        details: error.message,
      }),
      { status: 500 }
    );
  }
}
