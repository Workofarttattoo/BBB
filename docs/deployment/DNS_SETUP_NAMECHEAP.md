# DNS Setup for bbb.aios.is on Namecheap

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**

---

## Overview

You're setting up `bbb.aios.is` to point to GitHub Pages for hosting the Better Business Builder website.

**Domain:** aios.is (already purchased on Namecheap)
**Subdomain:** bbb.aios.is
**Hosting:** GitHub Pages (workofarttattoo/BBB repository)
**SSL:** Automatic (GitHub provides free HTTPS)

---

## Step 1: Verify GitHub Pages Setup

First, ensure the BBB repository has GitHub Pages enabled:

1. Go to: https://github.com/workofarttattoo/BBB
2. Click **Settings** (gear icon)
3. Scroll down to **Pages** section
4. Verify:
   - **Source:** Deploy from a branch
   - **Branch:** main → /docs folder
   - **Custom domain:** bbb.aios.is (should auto-populate from CNAME file)

**Status:** You should see a green checkmark "Your site is live at https://bbb.aios.is"

---

## Step 2: Configure DNS at Namecheap

### 2.1 Log into Namecheap

1. Go to: https://www.namecheap.com
2. Sign in to your account
3. Go to **Account** → **Domain List**
4. Find **aios.is** and click **Manage**

### 2.2 Access Advanced DNS Settings

1. Click the **Advanced DNS** tab
2. Scroll down to **Host Records** section

### 2.3 Add/Update DNS Records

You need to create DNS records pointing to GitHub Pages. You have TWO options:

#### **OPTION A: Using CNAME (Recommended for subdomain)**

Add a new CNAME record:

| Type  | Host       | Value                          | TTL    |
|-------|------------|--------------------------------|--------|
| CNAME | bbb        | workofarttattoo.github.io      | 30 min |

**Steps:**
1. Find existing CNAME records
2. Click **Add Record**
3. Select **Type:** CNAME
4. **Host:** bbb
5. **Value:** workofarttattoo.github.io
6. **TTL:** 30 min (or 300 for 5 minutes)
7. Click **Save Changes**

#### **OPTION B: Using A Records (Alternative)**

If CNAME doesn't work, use GitHub's IP addresses:

| Type | Host | Value             | TTL    |
|------|------|-------------------|--------|
| A    | bbb  | 185.199.108.153   | 30 min |
| A    | bbb  | 185.199.109.153   | 30 min |
| A    | bbb  | 185.199.110.153   | 30 min |
| A    | bbb  | 185.199.111.153   | 30 min |

**Steps:**
1. Click **Add Record** four times (one for each IP)
2. Select **Type:** A
3. **Host:** bbb
4. **Value:** [each IP address above]
5. **TTL:** 30 min
6. Click **Save Changes** after each

### 2.4 Verify DNS Records

After adding records, you should see something like:

```
Host: bbb              Type: CNAME     Value: workofarttattoo.github.io
```

---

## Step 3: Wait for DNS Propagation

DNS changes can take 5 minutes to 48 hours to propagate worldwide. Usually faster:

1. **5 minutes:** Most local resolution
2. **30 minutes:** Most regions
3. **2-4 hours:** All regions
4. **24 hours:** All caches cleared

**Check DNS propagation:**
- https://www.whatsmydns.net → Enter bbb.aios.is
- Shows which regions have updated
- When all regions show same IP, you're good

---

## Step 4: Verify HTTPS Setup

Once DNS propagates:

1. Visit: https://bbb.aios.is
2. Should see the BBB landing page
3. Check SSL certificate:
   - Click padlock icon in browser address bar
   - Should show GitHub's SSL certificate
   - No warnings or errors

**If certificate error:**
- Check that CNAME file exists in repository
- Verify DNS records at Namecheap
- Wait for DNS propagation
- GitHub can take 10 minutes to issue certificate after DNS is set

---

## Step 5: Verify GitHub Pages Configuration

In the GitHub repository settings, you should see:

```
Your site is published at https://bbb.aios.is
```

Green checkmark indicates successful deployment.

---

## Complete DNS Setup Examples

### Example 1: Using CNAME (Recommended)

```
Host Records:
- Type: CNAME, Host: bbb, Value: workofarttattoo.github.io, TTL: 30 min
```

### Example 2: Using A Records

```
Host Records:
- Type: A, Host: bbb, Value: 185.199.108.153, TTL: 30 min
- Type: A, Host: bbb, Value: 185.199.109.153, TTL: 30 min
- Type: A, Host: bbb, Value: 185.199.110.153, TTL: 30 min
- Type: A, Host: bbb, Value: 185.199.111.153, TTL: 30 min
```

---

## Troubleshooting

### Issue: "404 Not Found" or "There isn't a GitHub Pages site here"

**Solution:**
1. Verify CNAME file exists in repo root: `/CNAME`
2. Content must be exactly: `bbb.aios.is`
3. Check GitHub Pages settings - "Custom domain" should show bbb.aios.is
4. Wait 10 minutes for GitHub to issue SSL certificate

### Issue: DNS not updating

**Solutions:**
1. Check you're editing the correct domain (aios.is)
2. Verify you're in **Advanced DNS** section
3. Wait for TTL to expire (usually 30 min)
4. Use: https://www.whatsmydns.net to check propagation
5. Try flushing your local DNS cache:
   - **Mac:** `sudo dscacheutil -flushcache`
   - **Windows:** `ipconfig /flushdns`
   - **Linux:** `sudo systemd-resolve --flush-caches`

### Issue: "Certification not yet issued"

**Solutions:**
1. GitHub issues certificate AFTER DNS is confirmed working
2. Wait 10-15 minutes after DNS propagates
3. Keep trying to access https://bbb.aios.is
4. Certificate auto-renews every 90 days

### Issue: Subdomain works but parent domain doesn't

This is **normal and expected**:
- `bbb.aios.is` → GitHub Pages ✅
- `aios.is` → Namecheap/your main domain ✅

They can point to different places.

### Issue: CNAME conflicts with other records

**Solution:** Use A records instead of CNAME. Only one CNAME per subdomain.

---

## Rollback DNS (If Needed)

To revert bbb.aios.is back to original:

1. Go to Namecheap **Advanced DNS**
2. Delete the CNAME or A records you added
3. DNS will revert in 30 min to 24 hours

---

## Next Steps After DNS is Live

1. **Update Documentation**
   - Site now live at https://bbb.aios.is
   - Update all links and marketing materials

2. **Test Functionality**
   - Test all 26 quantum features
   - Verify licensing system works
   - Test revenue share reporting

3. **Monitor Performance**
   - GitHub Pages automatically caches
   - SSL certificate auto-renews

4. **Update Social Media**
   - Point to https://bbb.aios.is
   - Announce platform launch

---

## DNS Record Reference

For future reference, your DNS records should look like:

```
aios.is - Main Domain
├── bbb.aios.is → workofarttattoo.github.io (GitHub Pages)
├── mail.aios.is → [Your email provider]
└── [other subdomains]
```

---

## Important Notes

- **CNAME vs A Records:** CNAME is preferred for subdomains, A records are fallback
- **TTL:** 30 min (1800 sec) recommended for quick updates during setup
- **SSL:** Automatically issued and renewed by GitHub (free)
- **Downtime:** Minimal - DNS propagation usually within 5 minutes
- **Email:** Email for aios.is continues working (different MX records)

---

## Support

If you encounter issues:

1. **GitHub Pages Docs:** https://docs.github.com/en/pages
2. **Namecheap Support:** https://www.namecheap.com/support/
3. **DNS Checker:** https://www.whatsmydns.net

---

Last Updated: January 2025

**Status: Ready for deployment to bbb.aios.is** ✅
