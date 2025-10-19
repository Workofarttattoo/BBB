# Better Business Builder - Licensing System Guide

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**

---

## Overview

Better Business Builder implements a **dual-model licensing system** that generates revenue while providing users with clear options:

### Option 1: Revenue Share Agreement (50%)
- No upfront cost
- User pays 50% of gross revenue generated using BBB
- Perpetual agreement while using the software
- Monthly payment reporting required
- Audit rights for compliance verification

### Option 2: Purchased License
- One-time payment based on scale (pricing on request)
- Perpetual commercial rights
- No revenue sharing obligations
- Support included for 12 months
- Scalable pricing for users, businesses, and support levels

### Option 3: Trial Period
- 14 days of full access to all 26 quantum features
- No payment required to evaluate
- After trial expires, user must choose Option 1 or 2
- License status enforced automatically at API level

---

## How It Works

### 1. User Registration Flow

```
New User
  ↓
[Sign Up → Select Trial]
  ↓
Access all 26 quantum features for 14 days
  ↓
Before day 14 expires:
  - Accept 50% revenue share, OR
  - Purchase full license
  ↓
License status updated in database
  ↓
Full access continues indefinitely
```

### 2. Revenue Share Process

**Monthly Cycle:**

1. **User's Business Generates Revenue** (using BBB)
   - Product sales
   - Service fees
   - Subscription revenue
   - Consulting fees
   - Advertising revenue
   - Affiliate commissions
   - Other income

2. **User Submits Revenue Report** (by 15th of next month)
   - POST `/api/licensing/submit-revenue-report`
   - Reports detailed breakdown by revenue type
   - System calculates 50% owed

3. **Payment Due** (by 15th of following month)
   - Example: January revenue → Due by Feb 15th → Paid by March 15th
   - Wire transfer, ACH, or agreed payment method
   - Late payments: 5% monthly interest (60% APR)

4. **Financial Verification**
   - Quarterly certified financial statements (50k+ revenue)
   - Annual audit (100k+ revenue)
   - Licensor audit rights: once annually with 30 days notice
   - Underpayment >5%: auditor cost borne by licensee
   - Underpayment >10%: additional penalties apply

### 3. Purchased License Process

**One-time Setup:**

1. Contact: josh@corporationoflight.com
2. Quote provided based on:
   - License tier (Starter/Professional/Enterprise)
   - Number of users
   - Number of businesses
   - Support level (Basic/Premium/Enterprise)
3. One-time payment
4. License key issued
5. Perpetual access (no revenue sharing)

**Pricing Example:**
- Professional tier: $9,999 base
- +$199 per user (e.g., 5 users = +$995)
- +$299 per business (e.g., 2 businesses = +$598)
- Premium support: +$1,999
- **Total: ~$12,591 for 5-user, 2-business setup with premium support**

---

## API Endpoints

All endpoints require JWT authentication token.

### License Status & Information

**GET `/api/licensing/status`**
Returns current license status and financial summary.

Response:
```json
{
  "license_status": "revenue_share",
  "license_type": "professional",
  "trial_expires_at": "2025-01-31T00:00:00Z",
  "days_remaining": 14,
  "has_active_agreement": true,
  "agreement_type": "revenue_share",
  "total_revenue_reported": 50000.00,
  "total_revenue_share_owed": 25000.00,
  "total_revenue_share_paid": 20000.00,
  "outstanding_balance": 5000.00,
  "overdue_reports": 0
}
```

### Accept Revenue Share Agreement

**POST `/api/licensing/accept-revenue-share`**

Request:
```json
{
  "company_name": "Acme Corp",
  "legal_entity_type": "LLC",
  "address": "123 Main St, New York, NY 10001",
  "phone": "212-555-0100",
  "confirmation": "I AGREE to 50% revenue share terms"
}
```

Response:
```json
{
  "success": true,
  "message": "Revenue share agreement accepted successfully...",
  "agreement_id": 42,
  "license_status": "revenue_share",
  "accepted_at": "2025-01-17T14:30:00Z"
}
```

**Important:** Confirmation text must be EXACTLY: `"I AGREE to 50% revenue share terms"`

### Submit Monthly Revenue Report

**POST `/api/licensing/submit-revenue-report`**

Request:
```json
{
  "report_month": "2025-01",
  "product_sales": 10000.00,
  "service_fees": 5000.00,
  "subscription_revenue": 15000.00,
  "consulting_fees": 3000.00,
  "advertising_revenue": 1000.00,
  "affiliate_commissions": 500.00,
  "other_revenue": 2000.00,
  "notes": "Q1 strong performance"
}
```

Response:
```json
{
  "success": true,
  "report_id": 156,
  "gross_revenue": 36500.00,
  "revenue_share_owed": 18250.00,
  "payment_due_date": "2025-02-15T00:00:00Z",
  "message": "Revenue report submitted. Payment of $18,250.00 due by 2025-02-15"
}
```

**Revenue Definition:** "Gross revenue" = ALL income received that was generated using, with, or through BBB. This includes the 7 categories plus ANY other business income where BBB was used.

### View Revenue Reports

**GET `/api/licensing/revenue-reports`**

Response:
```json
{
  "reports": [
    {
      "id": 156,
      "month": "2025-01",
      "gross_revenue": 36500.00,
      "revenue_share_owed": 18250.00,
      "payment_due_date": "2025-02-15T00:00:00Z",
      "payment_received_date": null,
      "status": "pending",
      "breakdown": {
        "product_sales": 10000.00,
        "service_fees": 5000.00,
        "subscription_revenue": 15000.00,
        "consulting_fees": 3000.00,
        "advertising_revenue": 1000.00,
        "affiliate_commissions": 500.00,
        "other_revenue": 2000.00
      }
    }
  ]
}
```

### Purchase Full License

**POST `/api/licensing/purchase-license`**

Request:
```json
{
  "license_type": "professional",
  "max_users": 5,
  "max_businesses": 2,
  "support_level": "premium",
  "company_name": "Acme Corp",
  "billing_email": "billing@acmecorp.com"
}
```

Response:
```json
{
  "success": true,
  "message": "License quote generated. Contact josh@corporationoflight.com to complete purchase.",
  "amount": 12591.00,
  "payment_url": null
}
```

**Note:** Currently returns quote for manual processing. In production, would integrate with Stripe/PayPal.

### Terminate Agreement

**POST `/api/licensing/terminate-agreement`**

Request:
```json
{
  "reason": "Switching to competitor"
}
```

Response:
```json
{
  "success": true,
  "message": "Agreement terminated successfully. All use of BBB Software must cease immediately.",
  "outstanding_payments": 2,
  "outstanding_amount": 8750.00,
  "note": "Outstanding payments remain due even after termination."
}
```

**Important:** Terminating agreement immediately revokes license. User must:
- Stop using BBB Software immediately
- Delete all copies and instances
- Pay all outstanding revenue share amounts
- License status reverts to trial (if available) or unlicensed

### Get Agreement Document

**GET `/api/licensing/agreement-document`**

Response:
```json
{
  "agreement_id": 42,
  "type": "revenue_share",
  "accepted_at": "2025-01-17T14:30:00Z",
  "status": "active",
  "ip_address": "203.0.113.45",
  "company_name": "Acme Corp",
  "legal_entity_type": "LLC",
  "address": "123 Main St, New York, NY 10001",
  "phone": "212-555-0100",
  "terms": "See REVENUE_SHARE_AGREEMENT.md for full terms"
}
```

---

## Implementation Details

### Database Tables

**license_agreements**
- Tracks all executed agreements (digital signatures)
- Records: company info, IP address, acceptance timestamp
- Status: active, terminated, suspended

**revenue_reports**
- Monthly revenue reports from revenue share users
- Tracks gross revenue, share owed, payment status
- Breakdown by revenue category for audit purposes

**purchased_licenses**
- Records for purchased license users
- Includes: license key, purchase amount, support expiration
- Used for key validation and support entitlement

### Authentication Flow

All license endpoints require:
1. JWT authentication token (Bearer token in Authorization header)
2. Valid user in database
3. Active user account (is_active = true)

### License Enforcement

The `require_license_access()` dependency in auth.py enforces licensing at API level:

```python
@require_license_access
def get_protected_resource(current_user: User):
    # Only runs if user has:
    # - Revenue share agreement (active), OR
    # - Purchased license (active), OR
    # - Valid trial period
```

Any endpoint decorated with `@require_license_access`:
- Blocks users with no license/agreement
- Blocks expired trial users
- Allows trial, revenue share, and licensed users

### Quantum Feature Access

All 26 quantum features require both:
1. License check (`require_license_access`)
2. Quantum access check (`require_quantum_access`)

Users with revenue share agreements or purchased licenses get full quantum feature access.

---

## Terms Summary

### Revenue Share (50%)
- **Cost:** 50% of gross revenue (paid monthly)
- **Duration:** Perpetual (continues while using software)
- **Payment:** Monthly by 15th of following month
- **Late Fee:** 5% per month (60% APR)
- **Reporting:** Monthly/quarterly/annual depending on scale
- **Audit:** Annual audit rights for licensor
- **Termination:** 30 days notice, outstanding payments still due

### Purchased License
- **Cost:** One-time fee ($2,999 - $29,999+ depending on scale)
- **Duration:** Perpetual (forever, doesn't expire)
- **Support:** Included 12 months (renewable)
- **Updates:** Includes all updates during support period
- **Renewal:** Optional support renewal annually
- **Termination:** Can terminate, no refunds
- **Usage:** Single legal entity, specific deployment scope

### Trial Period
- **Cost:** Free
- **Duration:** 14 days
- **Features:** All 26 quantum features included
- **Enforcement:** Automatic after 14 days
- **Action Required:** Must accept revenue share or purchase license
- **Access After:** Revoked until option selected

---

## Revenue Definitions

For revenue share calculations, "Revenue" includes ALL of:

1. **Product Sales** - Direct product revenue
2. **Service Fees** - Consulting, implementation, professional services
3. **Subscription Revenue** - Recurring monthly/annual charges
4. **Consulting Fees** - Expert services delivered
5. **Advertising Revenue** - Ad placements, sponsorships
6. **Affiliate Commissions** - Referral and partnership income
7. **Other Revenue** - Any other income where BBB was used

**Critical:** Revenue is calculated on **GROSS** amounts (before expenses), not net profit.

Example: If you have $100,000 in gross product sales and $50,000 in costs, you owe 50% of $100,000 = $50,000 (not 50% of the $50,000 profit).

---

## Contact & Support

For licensing inquiries:
- **Email:** josh@corporationoflight.com
- **Revenue Share:** Agreement execution and reporting questions
- **License Purchase:** Quote requests and custom terms
- **Payment Issues:** Payment verification and late payment resolution
- **Legal:** Contract disputes and enforcement

---

## Compliance & Legal

All agreements are:
- Legally binding electronic contracts
- Governed by US law
- Subject to binding arbitration
- Fully enforceable in court
- Non-transferable per legal entity

Users warrant they have:
- Authority to enter agreements
- Will comply with all laws
- Will provide accurate financial reports
- Will maintain audit records

Licensor retains all IP, patents, copyrights, and trade secrets in BBB software.

---

Last Updated: January 2025