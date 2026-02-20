// Created: 2026-02-19
/**
 * Kerne Protocol - Email Inbound Webhook Handler
 * 
 * Receives webhooks from Resend for incoming emails to @kerne.ai
 * Fetches full email content and forwards to appropriate Gmail addresses.
 * 
 * Routing:
 * - devon@kerne.ai → liamlakevold@gmail.com
 * - team@kerne.ai → liamlakevold@gmail.com (default catch-all)
 */

import { NextRequest, NextResponse } from "next/server";

// Email forwarding routing table
// Maps kerne.ai addresses to personal Gmail addresses
// Each team member's kerne.ai email routes to their own Gmail
const EMAIL_ROUTES: Record<string, string> = {
  // Scofield (Devon) - liamlakevold@gmail.com
  "devon@kerne.ai": "liamlakevold@gmail.com",
  "scofield@kerne.ai": "liamlakevold@gmail.com",
  
  // Mahone - routes to Mahone's Gmail
  "mahone@kerne.ai": "nowmahone@gmail.com",
  
  // Bagwell - routes to Bagwell's Gmail
  "bagwell@kerne.ai": "tb12344444444@gmail.com",
  
  // Shared addresses - route to team inbox or primary contact
  "team@kerne.ai": "liamlakevold@gmail.com",
  "contact@kerne.ai": "liamlakevold@gmail.com",
  "info@kerne.ai": "liamlakevold@gmail.com",
  "support@kerne.ai": "liamlakevold@gmail.com",
};

// Default forward destination (catch-all for unmatched @kerne.ai addresses)
// Routes to primary team contact
const DEFAULT_FORWARD = "liamlakevold@gmail.com";

interface ResendWebhookEvent {
  type: string;
  created_at: string;
  data: {
    email_id: string;
    created_at: string;
    from: string;
    to: string[];
    bcc: string[];
    cc: string[];
    message_id: string;
    subject: string;
    attachments: Array<{
      id: string;
      filename: string;
      content_type: string;
      content_disposition: string;
      content_id: string;
    }>;
  };
}

interface EmailContent {
  id: string;
  from: string;
  to: string[];
  subject: string;
  html?: string;
  text?: string;
  attachments: Array<{
    id: string;
    filename: string;
    content_type: string;
    content: string;
  }>;
}

async function getEmailContent(emailId: string): Promise<EmailContent | null> {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.error("RESEND_API_KEY not configured");
    return null;
  }

  try {
    const response = await fetch(`https://api.resend.com/emails/${emailId}`, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    });

    if (!response.ok) {
      console.error(`Failed to fetch email ${emailId}: ${response.status}`);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching email content:", error);
    return null;
  }
}

async function forwardEmail(
  to: string,
  originalFrom: string,
  originalTo: string,
  subject: string,
  html: string | undefined,
  text: string | undefined
): Promise<boolean> {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.error("RESEND_API_KEY not configured");
    return false;
  }

  try {
    const forwardSubject = `[Kerne Forward] ${subject}`;
    const forwardHtml = `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #f5f5f5; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
          <p style="margin: 0; font-size: 14px; color: #666;">
            <strong>Forwarded email from Kerne Protocol</strong><br>
            From: ${originalFrom}<br>
            To: ${originalTo}<br>
            Subject: ${subject}
          </p>
        </div>
        <div style="border-top: 1px solid #eee; padding-top: 16px;">
          ${html || `<pre style="white-space: pre-wrap;">${text || "No content"}</pre>`}
        </div>
      </div>
    `;

    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "Kerne Forward <forward@kerne.ai>",
        to: [to],
        subject: forwardSubject,
        html: forwardHtml,
        reply_to: originalFrom,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Failed to forward email: ${response.status} ${errorText}`);
      return false;
    }

    const result = await response.json();
    console.log(`Email forwarded successfully to ${to}, ID: ${result.id}`);
    return true;
  } catch (error) {
    console.error("Error forwarding email:", error);
    return false;
  }
}

export async function POST(request: NextRequest) {
  console.log("[Email Inbound] Received webhook request");

  try {
    const event: ResendWebhookEvent = await request.json();

    // Verify this is an email.received event
    if (event.type !== "email.received") {
      console.log(`[Email Inbound] Ignoring event type: ${event.type}`);
      return NextResponse.json({ status: "ignored", reason: "wrong event type" });
    }

    const { email_id, from, to, subject } = event.data;
    console.log(`[Email Inbound] Processing email ${email_id}`);
    console.log(`  From: ${from}`);
    console.log(`  To: ${to.join(", ")}`);
    console.log(`  Subject: ${subject}`);

    // Get full email content from Resend API
    const emailContent = await getEmailContent(email_id);
    if (!emailContent) {
      console.error(`[Email Inbound] Failed to fetch email content for ${email_id}`);
      return NextResponse.json({ status: "error", reason: "failed to fetch content" }, { status: 500 });
    }

    // Determine forwarding destination based on recipient
    const recipientEmail = to[0].toLowerCase();
    const forwardTo = EMAIL_ROUTES[recipientEmail] || DEFAULT_FORWARD;

    console.log(`[Email Inbound] Forwarding to: ${forwardTo}`);

    // Forward the email
    const success = await forwardEmail(
      forwardTo,
      from,
      recipientEmail,
      subject,
      emailContent.html,
      emailContent.text
    );

    if (success) {
      return NextResponse.json({
        status: "success",
        email_id,
        forwarded_to: forwardTo,
      });
    } else {
      return NextResponse.json({ status: "error", reason: "forward failed" }, { status: 500 });
    }
  } catch (error) {
    console.error("[Email Inbound] Error processing webhook:", error);
    return NextResponse.json(
      { status: "error", reason: "internal error" },
      { status: 500 }
    );
  }
}

// Health check endpoint
export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "Kerne Email Inbound Handler",
    routes: Object.keys(EMAIL_ROUTES),
  });
}