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
    <div className="min-h-screen flex items-center justify-center bg-background dark:bg-[#0B0C10] transition-colors duration-300 px-4 py-10">
      <div className="w-full max-w-md bg-card dark:bg-[#1F2833] border border-border dark:border-[#45A29E]/20 rounded-2xl shadow-lg p-8">
        {/* Header */}
        <div className="flex items-center justify-center mb-6">
          <div className="w-10 h-10 rounded-full bg-[#45A29E] flex items-center justify-center mr-3">
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
          <h1 className="text-2xl font-bold text-foreground dark:text-white">Bulk Email Sender</h1>
        </div>

        <p className="text-sm text-muted-foreground dark:text-gray-400 mb-8 text-center">
          Upload or paste email addresses below to send marketing messages instantly.
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-foreground dark:text-gray-200 mb-2">
              Email List
            </label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              rows={8}
              className="w-full rounded-lg border border-border dark:border-[#45A29E]/30 bg-white dark:bg-[#0B0C10] 
                         text-gray-900 dark:text-gray-100 p-3 text-sm focus:ring-2 focus:ring-[#45A29E] outline-none"
              placeholder="Paste email addresses here (comma, space, or newline separated)"
              required
            />
            <div className="text-xs text-muted-foreground dark:text-gray-500 mt-2">
              Or upload from file:
            </div>
            <input
              type="file"
              accept=".txt,.csv"
              onChange={handleFileUpload}
              className="mt-1 text-sm text-muted-foreground dark:text-gray-400"
            />
          </div>

          <button
            type="submit"
            disabled={sending}
            className="w-full py-3 rounded-lg font-medium bg-[#45A29E] hover:bg-[#66FCF1] hover:text-gray-900 
                       text-white dark:text-gray-900 transition-all shadow-md disabled:bg-gray-500"
          >
            {sending ? "Sending..." : "Send Emails"}
          </button>
        </form>

        {/* Result message */}
        {result && (
          <div
            className={`mt-6 p-4 rounded-lg border ${
              result.success
                ? "border-green-500 bg-green-50 dark:bg-green-900/20"
                : "border-red-500 bg-red-50 dark:bg-red-900/20"
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
