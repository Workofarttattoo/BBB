#!/bin/bash
# Deploy Better Business Builder to bbb.aios.is via Vercel
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

set -e

echo "🚀 Deploying Better Business Builder to bbb.aios.is"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from Blank_Business_Builder directory"
    exit 1
fi

# Install Vercel CLI if not installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Login to Vercel
echo "🔐 Logging into Vercel..."
vercel login

# Deploy to production
echo "🚀 Deploying to production..."
vercel --prod

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "Next steps:"
echo "1. Wait for deployment to complete"
echo "2. Add custom domain in Vercel dashboard:"
echo "   - Domain: bbb.aios.is"
echo "3. Add DNS records at Namecheap (see instructions below)"
echo ""
echo "📝 DNS Configuration for Namecheap:"
echo "===================================="
echo "1. Go to Namecheap → Domains → aios.is → Advanced DNS"
echo "2. Add CNAME Record:"
echo "   Type: CNAME Record"
echo "   Host: bbb"
echo "   Value: cname.vercel-dns.com"
echo "   TTL: Automatic"
echo ""
echo "3. Save changes and wait 5-10 minutes for DNS propagation"
echo ""
echo "🎉 Your site will be live at: https://bbb.aios.is"
