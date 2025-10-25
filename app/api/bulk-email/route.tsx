import nodemailer from "nodemailer";
import { render } from "@react-email/render";
import MarketingTemplate from "../../../components/email-templates/MarketingTemplate";

export async function POST(request) {
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

    // 🧩 Split batch (max 30 emails per send)
    const batchList = emailList.slice(0, 30);

    // ✅ Load multiple Gmail accounts (SMTP_USER_1 ... SMTP_USER_10)
    const senders = [];
    for (let i = 1; i <= 10; i++) {
      const user = process.env[`SMTP_USER_${i}`];
      const pass = process.env[`SMTP_PASS_${i}`];
      if (user && pass) senders.push({ user, pass });
    }

    // fallback (in case you only have 1 Gmail)
    if (senders.length === 0 && process.env.SMTP_USER && process.env.SMTP_PASS) {
      senders.push({ user: process.env.SMTP_USER, pass: process.env.SMTP_PASS });
    }

    if (senders.length === 0) {
      return new Response(
        JSON.stringify({ success: false, error: "No Gmail accounts configured" }),
        { status: 500 }
      );
    }

    const subject = "New Investment Opportunity";
    const html = render(<MarketingTemplate />);

    let sent = [];
    let failed = [];

    // 🚀 Assign 3 emails per sender
    for (let i = 0; i < batchList.length; i++) {
      const senderIndex = Math.floor(i / 3) % senders.length;
      const { user, pass } = senders[senderIndex];

      const transporter = nodemailer.createTransport({
        service: "gmail",
        auth: { user, pass },
      });

      const email = batchList[i];

      try {
        await transporter.sendMail({
          from: `"Smart S9Trading" <${user}>`,
          to: email,
          subject,
          html,
        });
        console.log(`✅ Sent to ${email} (via ${user})`);
        sent.push(email);
      } catch (err) {
        console.error(`❌ Failed to send to ${email} (${user}):`, err.message);
        failed.push(email);
      }

      // ⏳ Delay to avoid Gmail spam trigger
      await new Promise((res) => setTimeout(res, 2000));
    }

    // ✅ Return result to frontend
    return new Response(
      JSON.stringify({
        success: true,
        sent,
        failed,
        remainingCount: emailList.length - batchList.length,
      }),
      { status: 200 }
    );
  } catch (error) {
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
