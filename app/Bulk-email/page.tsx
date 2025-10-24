"use client";

import React, { useState } from "react";

export default function BulkEmailPage() {
  const [emails, setEmails] = useState("");
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
        },
        body: JSON.stringify({
          template: "marketing", // backend handles content
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
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-lg bg-card border border-border rounded-2xl shadow-md p-8">
        <div className="flex items-center justify-center gap-2 mb-6">
          <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 8l9 6 9-6-9-6-9 6z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 8v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Bulk Email Sender</h1>
        </div>

        <p className="text-sm text-muted-foreground mb-6 text-center">
          Send bulk marketing emails directly via Gmail integration.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Email List
            </label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              rows={8}
              className="w-full border border-border bg-background rounded-lg p-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-600"
              placeholder="Paste email addresses here (comma, space, or newline separated)"
              required
            />
            <div className="text-xs text-muted-foreground mt-2">
              Or upload from file:
            </div>
            <input
              type="file"
              accept=".txt,.csv"
              onChange={handleFileUpload}
              className="mt-1 text-sm text-muted-foreground"
            />
          </div>

          <button
            type="submit"
            disabled={sending}
            className="w-full py-3 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 transition-all"
          >
            {sending ? "Sending..." : "Send Emails"}
          </button>
        </form>

        {result && (
          <div
            className={`mt-6 p-4 rounded-lg border ${
              result.success
                ? "border-green-400 bg-green-50 dark:bg-green-900/20"
                : "border-red-400 bg-red-50 dark:bg-red-900/20"
            }`}
          >
            {result.success ? (
              <p className="text-green-700 dark:text-green-400 font-medium text-sm text-center">
                ✅ Sent: {result.sent} | ❌ Failed: {result.failed}
              </p>
            ) : (
              <p className="text-red-700 dark:text-red-400 font-medium text-sm text-center">
                ❌ {result.error}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
