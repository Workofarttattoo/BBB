# Railway PostgreSQL Setup for BBB

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**

---

## Quick Start

### 1. Create Railway Account
- Go to: https://railway.app
- Sign up with GitHub (easiest)

### 2. Add PostgreSQL Database
```bash
# In Railway dashboard:
1. Click "New"
2. Select "Database"
3. Select "PostgreSQL"
4. Wait for provisioning (1-2 minutes)
```

### 3. Get Connection String
```
In Railway:
1. Click your PostgreSQL service
2. Go to "Connect" tab
3. Copy CONNECTION_STRING_URL
```

It will look like:
```
postgresql://postgres:PASSWORD@containers-us-west-XX.railway.app:XXXX/railway
```

### 4. Add to Vercel

```
Vercel Dashboard:
1. Go to: https://vercel.com/dashboard
2. Select your BBB project
3. Settings → Environment Variables
4. Add:
   Name: DATABASE_URL
   Value: [paste Railway connection string]
5. Save
```

### 5. Deploy

```bash
cd /Users/noone/Blank_Business_Builder
./deploy_to_vercel.sh
```

---

## Environment Variables for Vercel

Add these to Vercel Settings → Environment Variables:

| Name | Value | Source |
|------|-------|--------|
| `DATABASE_URL` | Railway connection string | Railway dashboard |
| `JWT_SECRET_KEY` | Generate with: `openssl rand -hex 32` | Generate locally |
| `STRIPE_SECRET_KEY` | sk_test_... | Stripe dashboard |
| `OPENAI_API_KEY` | sk-... | OpenAI dashboard |
| `SECRET_KEY` | Generate with: `openssl rand -hex 32` | Generate locally |

---

## Generate Secure Keys

```bash
# Generate JWT_SECRET_KEY
openssl rand -hex 32

# Generate SECRET_KEY
openssl rand -hex 32
```

Copy the output to Vercel environment variables.

---

## Deploy Command

Once DATABASE_URL is set in Vercel:

```bash
cd /Users/noone/Blank_Business_Builder
./deploy_to_vercel.sh
```

Or manually:

```bash
vercel --prod --env-file .env.production
```

---

## Verify Deployment

After deployment:

1. Go to: https://bbb.aios.is/docs
2. Should see FastAPI Swagger UI
3. All 30+ endpoints listed
4. License endpoints visible

---

## Common Issues

**Issue: 502 Bad Gateway**
- Database URL incorrect
- Check Railway connection string in Vercel
- Ensure DATABASE_URL variable is set

**Issue: Database connection timeout**
- Railway database not ready yet
- Wait 2-3 minutes
- Try redeploying

**Issue: Endpoint returns 500**
- Check Vercel logs: https://vercel.com/dashboard → Project → Deployments
- Look at recent build logs

---

## Free Tier Limits

Railway Free Tier includes:
- ✅ 1 PostgreSQL database
- ✅ $5 credit/month
- ✅ Enough for 1000+ users on small queries
- ✅ Auto-pauses after 7 days idle

---

## Next: Deploy to Vercel

Once DATABASE_URL is in Vercel environment:

```bash
./deploy_to_vercel.sh
```

Site will be live at: **https://bbb.aios.is** 🚀
