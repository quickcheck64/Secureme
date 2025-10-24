import nodemailer from "nodemailer";
import { render } from "@react-email/render";
import MarketingTemplate from "../../../components/email-templates/MarketingTemplate";

const AUTH_TOKEN = process.env.API_AUTH_TOKEN;

export async function POST(request: Request) {
  try {
    // ✅ Authorization
    const authHeader = request.headers.get("Authorization");
    if (!authHeader || authHeader !== `Bearer ${AUTH_TOKEN}`) {
      return new Response(JSON.stringify({ success: false, error: "Unauthorized" }), { status: 401 });
    }

    // ✅ Extract request data
    const { subject, template, data, emails } = await request.json();

    if (!subject || !template || !emails) {
      return new Response(
        JSON.stringify({ success: false, error: "Missing subject, template, or emails" }),
        { status: 400 }
      );
    }

    // 🧹 Clean email list
    let emailList: string[] = [];
    if (typeof emails === "string") {
      emailList = emails
        .split(/[\n,; ]+/)
        .map((e) => e.trim())
        .filter((e) => e.includes("@"));
    } else if (Array.isArray(emails)) {
      emailList = emails.filter((e) => e.includes("@"));
    }

    if (emailList.length === 0) {
      return new Response(JSON.stringify({ success: false, error: "No valid email addresses provided" }), {
        status: 400,
      });
    }

    // ✅ Gmail SMTP
    const smtpUser = process.env.SMTP_USER;
    const smtpPass = process.env.SMTP_PASS;

    if (!smtpUser || !smtpPass) {
      return new Response(JSON.stringify({ success: false, error: "Gmail SMTP not configured" }), { status: 500 });
    }

    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: {
        user: smtpUser,
        pass: smtpPass,
      },
    });

    // ✅ Choose and render template
    let html = "";
    if (template === "marketing") {
      const { title, message, ctaLink, ctaText } = data;
      html = render(<MarketingTemplate title={title} message={message} ctaLink={ctaLink} ctaText={ctaText} />);
    } else {
      return new Response(JSON.stringify({ success: false, error: "Unknown template name" }), { status: 400 });
    }

    // ✅ Send emails sequentially
    let sentCount = 0;
    let failedCount = 0;

    for (const email of emailList) {
      try {
        await transporter.sendMail({
          from: `"Smart S9 Trading" <${smtpUser}>`,
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

      // small delay between sends (1.5s)
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
