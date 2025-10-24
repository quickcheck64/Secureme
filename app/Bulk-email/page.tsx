"use client";

import React, { useState } from "react";

export default function BulkEmailPage() {
  const [emails, setEmails] = useState("");
  const [subject, setSubject] = useState("");
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [ctaLink, setCtaLink] = useState("");
  const [ctaText, setCtaText] = useState("");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setEmails(text);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setResult(null);

    try {
      const response = await fetch("/api/bulk-email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.NEXT_PUBLIC_API_AUTH_TOKEN}`, // optional, if you set it client-side
        },
        body: JSON.stringify({
          subject,
          template: "marketing",
          data: { title, message, ctaLink, ctaText },
          emails,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error("Bulk email failed:", err);
      setResult({ success: false, error: "Failed to send emails." });
    }

    setSending(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 flex justify-center">
      <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-md">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          📧 Bulk Email Sender (Gmail)
        </h1>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block font-medium mb-1">Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full border rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              placeholder="Enter email subject"
              required
            />
          </div>

          <div>
            <label className="block font-medium mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full border rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              placeholder="Enter main heading"
              required
            />
          </div>

          <div>
            <label className="block font-medium mb-1">Message</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={5}
              className="w-full border rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              placeholder="Type your marketing message"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium mb-1">CTA Link</label>
              <input
                type="url"
                value={ctaLink}
                onChange={(e) => setCtaLink(e.target.value)}
                className="w-full border rounded-lg p-2.5"
                placeholder="https://example.com"
              />
            </div>

            <div>
              <label className="block font-medium mb-1">CTA Text</label>
              <input
                type="text"
                value={ctaText}
                onChange={(e) => setCtaText(e.target.value)}
                className="w-full border rounded-lg p-2.5"
                placeholder="Learn More"
              />
            </div>
          </div>

          <div>
            <label className="block font-medium mb-1">Email List</label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              rows={6}
              className="w-full border rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              placeholder="Paste email addresses here (comma, space, or newline separated)"
              required
            />
            <div className="text-sm text-gray-500 mt-2">or upload file:</div>
            <input
              type="file"
              accept=".txt,.csv,.pdf"
              onChange={handleFileUpload}
              className="mt-1 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={sending}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400"
          >
            {sending ? "Sending..." : "Send Emails"}
          </button>
        </form>

        {result && (
          <div
            className={`mt-6 p-4 rounded-lg border ${
              result.success ? "border-green-400 bg-green-50" : "border-red-400 bg-red-50"
            }`}
          >
            {result.success ? (
              <p className="text-green-700 font-medium">
                ✅ Sent: {result.sent} | ❌ Failed: {result.failed}
              </p>
            ) : (
              <p className="text-red-700 font-medium">❌ {result.error}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
      }
