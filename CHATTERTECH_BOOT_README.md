# 🚀 ChatterTech.ai - Boot Instructions

## ✅ What's Complete

### Core Infrastructure
- [x] **Company Pack**: `companies/chattertech-ai/` with COMPANY.md, policy.json, skills/, services.json, pricing.json
- [x] **Email Integration**: IMAP listener for inventor@aios.is (mail.privatemail.com:993)
- [x] **Phone Number**: +1 415 594 0143 (Twilio-ready)
- [x] **Apollo Targets**: 3 ICP profiles (Home Services $199/mo, Medical $99/mo, Real Estate $399/mo)
- [x] **Knowledge Vault**: Synced with Firebase, semantic search enabled
- [x] **Voice Agent Engine**: Twilio + Deepgram + ElevenLabs integration ready
- [x] **Redis/Celery**: Configuration prepared for task queue

### Viktor-Style Autonomy
- [x] Assume-forward execution policy
- [x] Auto-judge loop with revise cycles (max 3)
- [x] Approval gates for outbound email/payments
- [x] Middle manager heartbeat (30min audit)
- [x] Paperclip issue sync (GUI paste mode ready)

### GUI Dashboard
- [x] React component structure (chattertech_components.tsx)
- [x] Premium dark theme with animations
- [x] Live call stats, agent status, recent calls table
- [x] Quick actions panel

---

## ⚠️ CRITICAL: Before First Boot

### 1. Get API Keys (Required)
Create `.env` file with these keys:

```bash
# LLM
OLLAMA_BASE_URL=http://127.0.0.1:11434
ROLE_WORKER_MODEL=qwen3.5:4b
ROLE_JUDGE_MODEL=qwen3.5:4b
MIDDLE_MANAGER_MODEL=qwen3.5:9b

# Voice Stack
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+14155940143
DEEPGRAM_API_KEY=your_deepgram_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Email (already configured)
EMAIL_USER=inventor@aios.is
EMAIL_PASSWORD=F00lpr00f596!
EMAIL_IMAP_SERVER=mail.privatemail.com
EMAIL_IMAP_PORT=993

# Redis (optional but recommended)
REDIS_URL=redis://localhost:6379/0

# Firebase (optional for knowledge sync)
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-creds.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com

# Paperclip (optional)
PAPERCLIP_API_URL=http://127.0.0.1:3100
PAPERCLIP_API_TOKEN=your_token

# Apollo (for outbound leads)
APOLLO_API_KEY=your_apollo_key
```

### 2. Pull Ollama Models
```bash
ollama pull qwen3.5:4b    # Worker/Judge model (~2.5GB)
ollama pull qwen3.5:9b    # Middle manager model (~5GB)
```

### 3. Start Redis (Optional but Recommended)
```bash
# macOS
brew install redis
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:latest
```

### 4. Test Email Connection
```bash
cd /workspace
PYTHONPATH=src python chattertech_email_config.py
# Should show: ✓ Connected to inventor@aios.is
```

---

## 🎯 Target Customers (Apollo Search Profiles)

### Primary: Home Services ($199/mo)
**Who**: HVAC, Plumbing, Electrical, Roofing companies (2-20 employees)  
**Titles**: Owner, Founder, Operations Manager  
**Pain**: Missing after-hours calls = lost revenue  
**Search Query**: `"HVAC OR plumbing" AND "owner" AND employees:1-50`

### Secondary: Medical/Dental ($99/mo)
**Who**: Dental offices, Medical practices, Veterinary clinics  
**Titles**: Practice Manager, Office Manager, Doctor  
**Pain**: Patients can't reach office after hours  
**Search Query**: `"Dental OR medical practice" AND "practice manager" AND employees:1-20`

### Tertiary: Real Estate ($399/mo)
**Who**: Property management, Real estate brokerages  
**Titles**: Broker, Property Manager, Leasing Manager  
**Pain**: Missing lead calls during busy periods  
**Search Query**: `"Property management" AND employees:5-100`

---

## 📦 Service Packages (Fixed, Not Custom)

| Package | Price | Target | Features |
|---------|-------|--------|----------|
| **After-Hours Answering** | $99/mo | Medical/Dental | 24/7 coverage, HIPAA-compliant, Emergency routing |
| **24/7 Virtual Receptionist** | $199/mo | Home Services | Live transfer, Appointment booking, After-hours support |
| **Multi-Line Call Center** | $399/mo | Real Estate | Unlimited calls, Property inquiries, Showing scheduling |

**Offer**: Free 7-day trial + setup included

---

## 🔧 Boot Commands

### Option A: Full Stack (Recommended)
```bash
cd /workspace

# 1. Start Redis (if using)
redis-server &

# 2. Start Celery worker
celery -A blank_business_builder.tasks worker -l info &

# 3. Start Celery beat (scheduler)
celery -A blank_business_builder.tasks beat -l info &

# 4. Start GUI server
PYTHONPATH=src uvicorn blank_business_builder.gui_server:app --host 0.0.0.0 --port 8000
```

### Option B: GUI Only (Quick Test)
```bash
cd /workspace
PYTHONPATH=src uvicorn blank_business_builder.gui_server:app --host 0.0.0.0 --port 8000
```

**Open**: http://localhost:8000

---

## 🎮 First Actions in GUI

1. **Agent Command Center** → Verify Viktor mode is enabled
2. **Enterprise Ops** → 
   - Click "Knowledge Vault" to browse company info
   - Test "Firebase Sync" if credentials added
3. **Approvals Panel** → Check for any pending approvals
4. **Chat** → Try commands:
   - "viktor status"
   - "knowledge search pricing"
   - "show active tasks"

---

## 📈 Path to First $398 MRR

**Goal**: 2 customers × $199/mo (Home Services package)

### Week 1: Setup
- [ ] Get all API keys
- [ ] Test voice agent locally
- [ ] Build simple landing page (Carrd.co or Framer)
- [ ] Set up Stripe for billing

### Week 2: Outbound Blitz
- [ ] Export 200 HVAC/plumbing leads from Apollo
- [ ] Send 50 emails/day for 4 days
- [ ] Follow up with phone calls to openers
- [ ] Offer 7-day free trial

### Week 3: Close First Customers
- [ ] Run trials for interested prospects
- [ ] Show call recordings + transcripts
- [ ] Convert 2 trials to paid ($398 MRR)

### Week 4: Automate
- [ ] Wire email leads → autonomous task queue
- [ ] Set up approval gates for outbound
- [ ] Enable middle manager heartbeat
- [ ] Let Viktor run prospecting autonomously

---

## 🆘 Troubleshooting

### Ollama Connection Failed
```bash
# Check if Ollama is running
curl http://127.0.0.1:11434/api/tags

# If not running, start it
ollama serve
```

### Redis Not Available
System will fallback to inline execution. Heartbeats won't run on schedule but manual tasks will work.

### Email Connection Failed
- Verify password: `F00lpr00f596!` (note: capital F, exclamation mark)
- Check firewall allows port 993
- Try manual IMAP test: `telnet mail.privatemail.com 993`

### GUI Won't Load
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process if needed
kill -9 <PID>

# Restart server
PYTHONPATH=src uvicorn blank_business_builder.gui_server:app --host 0.0.0.0 --port 8000
```

---

## 📞 Support

**Phone**: +1 415 594 0143 (ChatterTech router agent)  
**Email**: inventor@aios.is  
**Domain**: chattertech.ai (configured)

---

**Next Step**: Get API keys → Run boot commands → Open GUI → Start prospecting! 🚀
