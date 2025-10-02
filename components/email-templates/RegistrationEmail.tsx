// components/email-templates/RegistrationEmail.tsx
interface RegistrationEmailProps {
  name: string
  email: string
  phone: string
}

export default function RegistrationEmail({ name, email, phone }: RegistrationEmailProps) {
  return (
    <div style={{ fontFamily: "Arial, sans-serif", maxWidth: "600px", margin: "0 auto" }}>
      <h2 style={{ color: "#059669" }}>New User Signup</h2>
      <p>A new user has registered with the following details:</p>
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
        <p><strong>Phone:</strong> {phone}</p>
      </div>
      <p style={{ color: "#6b7280" }}>This is an automated notification from your registration system.</p>
    </div>
  )
}
