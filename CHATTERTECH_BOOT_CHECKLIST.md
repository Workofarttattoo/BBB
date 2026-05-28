# ChatterTech.ai - Pre-Boot Checklist ✅

## ✅ COMPLETED

### Company Pack (`/workspace/companies/chattertech/`)
- [x] `COMPANY.md` - Mission, vision, values, target customer, brand voice
- [x] `pricing.json` - 3 packages ($99/$199/$399), add-ons, trial, guarantee
- [x] `services.json` - Core services, technical capabilities, success stories
- [x] `policy.json` - Approval gates, compliance rules, escalation matrix
- [x] `skills/outbound_sales.md` - Full sales scripts, objection handling, Apollo targeting
- [x] `APOLLO_TARGETING.md` - Target industries, titles, cold email/call scripts

### Configuration
- [x] `.env` file created with your email credentials (inventor@aios.is)
- [x] Apollo targeting configured for Medical/Home Services/Real Estate
- [x] Approval gates set (20 emails/day, 50 leads/search, all charges require approval)

### Business Model Clarity
**We sell 3 fixed AI Receptionist packages:**
1. **After-Hours Answering** ($99/mo) - Medical/dental offices
2. **24/7 Virtual Receptionist** ($199/mo) - HVAC, plumbing, roofers (MOST POPULAR)
3. **Multi-Line Call Center** ($399/mo) - Property management, home builders

**NOT custom work on-the-fly** - that failed on Fiverr. Fixed products = scalable.

---

## ⚠️ REQUIRED BEFORE BOOT

### 1. API Keys (Get These Now)
```bash
# Edit .env and fill in:
ELEVENLABS_API_KEY=get_from_elevenlabs.io
DEEPGRAM_API_KEY=get_from_deepgram.com  
TWILIO_ACCOUNT_SID=get_from_twilio.com
TWILIO_AUTH_TOKEN=get_from_twilio.com
TWILIO_PHONE_NUMBER=buy_from_twilio (~$1/mo + usage)

# Optional but recommended:
APOLLO_API_KEY=get_from_apollo.io (for lead search)
STRIPE_SECRET_KEY=get_from_stripe.com (for billing)
SENDGRID_API_KEY=get_from_sendgrid.net (for email)
```

### 2. Redis Server (For Celery)
```bash
# Mac (with Homebrew):
brew install redis
redis-server

# Or Docker:
docker run -d -p 6379:6379 redis:latest

# Test: redis-cli ping → should return PONG
```

### 3. Ollama Models
```bash
# Pull required models:
ollama pull qwen3.5:4b   # Worker/Judge
ollama pull qwen3.5:9b   # Middle Manager

# Test: curl http://localhost:11434/api/tags
```

### 4. Firebase Credentials (Optional - for Knowledge Vault sync)
```bash
# If using Firebase:
# 1. Create project at console.firebase.google.com
# 2. Download service account JSON
# 3. Save as ./config/firebase_credentials.json
# 4. Set FIREBASE_DATABASE_URL in .env
```

---

## 🚀 BOOT COMMANDS

```bash
cd /workspace

# 1. Start Redis (if not running)
redis-server

# 2. Start Celery worker + beat (in separate terminals or background)
celery -A blank_business_builder.tasks worker -l info &
celery -A blank_business_builder.tasks beat -l info &

# 3. Start GUI server
PYTHONPATH=src uvicorn blank_business_builder.gui_server:app --host 0.0.0.0 --port 8000

# 4. Open browser
# http://localhost:8000
```

---

## 📊 FIRST AUTONOMOUS TASKS

Once booted, agents will:

1. **Search Apollo** for 50 leads (Medical/Dental practices, 2-10 employees)
   - Requires: APOLLO_API_KEY
   - Approval gate: CEO must approve bulk search result

2. **Draft cold emails** for top 20 leads
   - Uses: skills/outbound_sales.md scripts
   - Approval gate: CEO must approve before sending

3. **Make outbound calls** to top 10 leads
   - Uses: Twilio + ElevenLabs voice
   - Script: "Hi [Name], Joshua from ChatterTech.ai..."
   - Goal: Book 2-3 demos

4. **Sync Knowledge Vault** to Firebase (if configured)
   - Uploads: COMPANY.md, pricing.json, services.json, skills/

---

## 🎯 SUCCESS METRICS (First Week)

| Metric | Target |
|--------|--------|
| Apollo leads found | 200+ |
| Cold emails sent | 100 (20/day x 5 days) |
| Cold calls made | 50 (10/day) |
| Demos booked | 6-10 |
| Trials started | 3-5 |
| Paid customers | 1-2 |

**Revenue Math**: 2 customers x $199/mo = **$398 MRR in Week 1**

---

## 🔧 TROUBLESHOOTING

### Ollama not responding?
```bash
ollama serve  # In one terminal
curl http://localhost:11434/api/tags  # Test in another
```

### Redis connection failed?
```bash
redis-cli ping  # Should return PONG
# If not: redis-server
```

### Celery not processing tasks?
```bash
# Check worker logs:
celery -A blank_business_builder.tasks worker -l debug

# Purge stale tasks:
celery -A blank_business_builder.tasks purge
```

### GUI won't start?
```bash
# Check port 8000 is free:
lsof -i :8000
# Kill if needed: kill -9 <PID>

# Restart:
PYTHONPATH=src uvicorn blank_business_builder.gui_server:app --host 0.0.0.0 --port 8000
```

---

## 📞 NEXT STEPS AFTER BOOT

1. **Verify email**: Check inventor@aios.is for any setup confirmations
2. **Get API keys**: ElevenLabs, Deepgram, Twilio (15 min setup each)
3. **Test one call**: Manual outbound call to test Twilio + voice pipeline
4. **Approve first batch**: CEO approves first 20 leads from Apollo search
5. **Monitor dashboard**: Watch task progress in GUI Agent Command Center

**Questions?** Ping the CEO chat in GUI or check logs/judge.jsonl for decision trails.

---

*ChatterTech.ai - AI Receptionists That Never Sleep*
*Built by Joshua Cole | inventor@aios.is*
