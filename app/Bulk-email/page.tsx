"use client"

import React, { useState } from "react"

export default function BulkEmailPage() {
  const [emails, setEmails] = useState("")
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const text = await file.text()
    setEmails(text)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSending(true)
    setResult(null)

    try {
      const response = await fetch("/api/bulk-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template: "marketing",
          emails,
        }),
      })

      const data = await response.json()
      setResult(data)
    } catch (err) {
      console.error("Bulk email failed:", err)
      setResult({ success: false, error: "Failed to send emails." })
    }

    setSending(false)
  }

  return (
    <div className="deposit-container">
      <div className="deposit-card">
        {/* Header */}
        <div className="deposit-header">
          <div className="deposit-icon">
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l9 6 9-6-9-6-9 6z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 8v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8" />
            </svg>
          </div>
          <h1 className="deposit-title">Bulk Email Sender</h1>
        </div>

        <p className="text-sm text-muted-foreground mb-8 text-center">
          Upload or paste email addresses below to send marketing messages instantly.
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Email List
            </label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              rows={8}
              className="deposit-input"
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
            className="deposit-button"
          >
            {sending ? "Sending..." : "Send Emails"}
          </button>
        </form>

        {/* Result */}
        {result && (
          <div
            className={`mt-6 p-4 rounded-lg border ${
              result.success ? "border-green-500 bg-green-50 dark:bg-green-900/20" : "border-red-500 bg-red-50 dark:bg-red-900/20"
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
  )
}
