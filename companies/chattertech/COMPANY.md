# ChatterTech.ai Company Identity

## Core Identity
**Name**: ChatterTech.ai  
**Tagline**: AI Receptionists That Never Sleep  
**Mission**: Provide 24/7 automated phone answering for small businesses using ElevenLabs Agent Platform.  
**Founder**: Joshua Hendricks Cole (inventor@aios.is)  
**Phone**: +1 415 594 0143  

## Value Proposition
"We answer your calls 24/7, book appointments directly into your calendar, and handle FAQs instantly—so you never miss a job while you sleep or work on-site."

## Target Customer (Ideal Customer Profile)
1. **Home Services (Primary)**: HVAC, Plumbing, Roofing, Electricians (5–20 employees). Pain: Missed calls = lost $500+ jobs.
2. **Medical/Dental (Secondary)**: Private practices, clinics. Pain: After-hours overflow.
3. **Real Estate (Tertiary)**: Property managers, independent agents. Pain: High call volume, repetitive questions.

## Service Packages (Fixed Pricing)
| Package | Price | Features | Target |
|---------|-------|----------|--------|
| **After-Hours Answering** | $99/mo | 6pm–8am coverage, voicemail transcription, emergency flagging | Medical/Dental |
| **24/7 Virtual Receptionist** | $199/mo | Full-day coverage, appointment booking, FAQ handling, SMS follow-up | **Home Services (Flagship)** |
| **Multi-Line Call Center** | $399/mo | Up to 5 concurrent lines, custom IVR, CRM integration, priority support | Property Management |

## Brand Voice
- **Professional yet Warm**: Sound like a helpful human receptionist, not a robot.
- **Efficient**: Get to the point, respect caller time.
- **Trustworthy**: Accurate information, reliable handoffs.

## Operational Rules (Viktor Mode)
1. **Assume Forward**: If a lead's industry is unclear, default to Home Services script.
2. **No Custom Dev**: We sell fixed packages only. No "build me a custom bot" work.
3. **Approval Gates**: All outbound emails and cold calls require CEO approval in GUI.
4. **Email**: Use IMAP (inventor@aios.is) for inbound; draft outbound for approval.
5. **Voice**: All voice agents run on ElevenLabs Agent Platform.

## Tech Stack
- **Voice**: ElevenLabs Agent Platform (STT, LLM, TTS, Telephony)
- **Email**: IMAP (mail.privatemail.com:993)
- **Memory**: Firebase Realtime Database (Knowledge Vault)
- **Orchestration**: BBB Viktor Agents (Celery + Redis)
- **GUI**: FastAPI + Vue.js Dashboard
