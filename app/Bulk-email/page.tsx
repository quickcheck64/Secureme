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
          template: "marketing", // handled by backend
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
            <label className="block font-medium mb-1">Email List</label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              rows={8}
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
              result.success
                ? "border-green-400 bg-green-50"
                : "border-red-400 bg-red-50"
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
