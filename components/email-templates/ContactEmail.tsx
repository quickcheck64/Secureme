// components/email-templates/ContactEmail.tsx
interface ContactEmailProps {
  name: string
  email: string
  category: string
  message: string
}

export default function ContactEmail({ name, email, category, message }: ContactEmailProps) {
  return (
    <div style={{ fontFamily: "Arial, sans-serif", maxWidth: "600px", margin: "0 auto" }}>
      <h2 style={{ color: "#059669" }}>New Contact Message</h2>
      <p>A user has submitted a message through the contact form:</p>
      <div
        style={{
          background: "#f3f4f6",
          padding: "20px",
          borderRadius: "8px",
          margin: "20px 0",
        }}
      >
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Category:</strong> {category}</p>
        <p><strong>Message:</strong> {message}</p>
      </div>
      <p style={{ color: "#6b7280" }}>This is an automated notification from your contact system.</p>
    </div>
  )
}
