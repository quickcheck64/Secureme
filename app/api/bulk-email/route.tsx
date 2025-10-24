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
    const emailList: string[] = Array.isArray(emails)
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

    // ✅ Multi SMTP accounts setup
    const smtpAccounts = [
      { user: process.env.SMTP_USER1, pass: process.env.SMTP_PASS1 },
      { user: process.env.SMTP_USER2, pass: process.env.SMTP_PASS2 },
      { user: process.env.SMTP_USER3, pass: process.env.SMTP_PASS3 },
    ].filter((acc) => acc.user && acc.pass);

    if (smtpAccounts.length === 0) {
      return new Response(
        JSON.stringify({ success: false, error: "No SMTP accounts configured" }),
        { status: 500 }
      );
    }

    // ✅ Render email template
    const subject = "New Investment Opportunity";
    const html = render(<MarketingTemplate />);

    let sentCount = 0;
    let failedCount = 0;
    let currentAccountIndex = 0;

    // Function to create transporter
    const createTransporter = (account: { user: string; pass: string }) =>
      nodemailer.createTransport({
        service: "gmail",
        auth: { user: account.user, pass: account.pass },
      });

    // Send in batches of 2 emails per 60 seconds
    while (emailList.length > 0) {
      const batch = emailList.splice(0, 2); // Take 2 emails
      const account = smtpAccounts[currentAccountIndex];
      const transporter = createTransporter(account);

      for (const email of batch) {
        try {
          await transporter.sendMail({
            from: `"Smart S9Trading" <${account.user}>`,
            to: email,
            subject,
            html,
          });
          console.log(`✅ Sent to ${email} via ${account.user}`);
          sentCount++;
        } catch (err: any) {
          console.error(`❌ Failed to send to ${email} via ${account.user}:`, err.message);

          // Switch to next account if available
          if (currentAccountIndex < smtpAccounts.length - 1) {
            currentAccountIndex++;
            console.log(`Switching to next SMTP account: ${smtpAccounts[currentAccountIndex].user}`);
            emailList.unshift(email); // Retry failed email with next account
            break; // exit batch loop to reset transporter
          } else {
            console.error(`All SMTP accounts failed for ${email}. Skipping.`);
            failedCount++;
          }
        }
      }

      // Wait 60 seconds before sending next batch
      if (emailList.length > 0) {
        console.log("⏳ Waiting 60 seconds before sending next batch...");
        await new Promise((res) => setTimeout(res, 60000));
      }
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
