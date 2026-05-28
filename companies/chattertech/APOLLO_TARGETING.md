# ChatterTech.ai - Apollo Targeting Strategy

## Business Model Clarification
**We do NOT build custom tools on-the-fly.** That model failed on Fiverr because:
- Custom work doesn't scale
- Clients don't know what to ask for
- No repeatable sales process

**Instead, we sell 3 fixed "AI Receptionist" packages:**

### Package 1: After-Hours Answering ($99/mo)
- Answers calls when business is closed
- Takes messages, books appointments
- Forwards emergencies only
- **Target**: Medical clinics, dental offices, law firms

### Package 2: 24/7 Virtual Receptionist ($199/mo)
- Answers all calls, never misses a lead
- Qualifies prospects, books appointments
- Handles FAQs (hours, pricing, location)
- **Target**: HVAC, plumbing, roofing, real estate agents

### Package 3: Multi-Line Call Center ($399/mo)
- Handles multiple simultaneous calls
- Routes to correct department
- CRM integration, call recording
- **Target**: Home builders, property management, multi-location clinics

---

## Apollo.io Search Filters

### Primary Target: Medical/Dental Practices
```json
{
  "industries": ["Medical Practice", "Dental Office", "Veterinary Clinic"],
  "titles": ["Owner", "Practice Manager", "Office Manager", "Clinic Director"],
  "employees": "2-10",
  "location": "United States",
  "keywords": ["private practice", "family owned"]
}
```
**Why**: They miss 30% of calls after hours. One missed patient = $200+ lost.

### Secondary Target: Home Services
```json
{
  "industries": ["Construction", "HVAC", "Plumbing", "Roofing", "Electrical"],
  "titles": ["Owner", "Operations Manager", "General Manager"],
  "employees": "2-20",
  "location": "United States",
  "keywords": ["emergency service", "24/7"]
}
```
**Why**: Emergency calls = high value. Missed call = competitor gets the job.

### Tertiary Target: Real Estate
```json
{
  "industries": ["Real Estate", "Property Management"],
  "titles": ["Broker Owner", "Acquisitions Manager", "Property Manager"],
  "employees": "2-15",
  "location": "United States",
  "keywords": ["rentals", "investments"]
}
```
**Why**: High commission deals. Need instant response to leads.

---

## Cold Email Script (Apollo → Email Sequence)

**Subject**: Missed 3 calls yesterday?

Hi [First Name],

I noticed [Company Name] doesn't have 24/7 call coverage. 

Last week, a local [industry] office missed 12 after-hours calls. Each one went to a competitor.

ChatterTech.ai provides an AI receptionist that:
- Answers every call, 24/7
- Books appointments directly into your calendar
- Costs less than a part-time employee ($99/mo vs $2,000/mo)

Want to hear a demo call? Just reply "demo" and I'll send you a recording.

Best,
Joshua Cole
Founder, ChatterTech.ai

P.S. We're offering a free 7-day trial this week for [industry] businesses in [City].

---

## Cold Call Script (Phone → Discovery Hour)

**Opener**: 
"Hi [Name], Joshua from ChatterTech.ai. We help [industry] businesses stop missing calls after hours. Quick question - who answers your phones when you're closed or busy with clients?"

**If they say "nobody" or "voicemail"**:
"That's exactly what we fix. Our AI receptionist answers every call, books appointments, and forwards emergencies. Costs $99/month - less than one missed job pays for it. Want to hear a 2-minute demo?"

**Close**:
"Let's do this - I'll set up a free 7-day trial. If you don't recover at least one missed call in week one, no charge. Fair?"

---

## Daily Outreach Goals

| Activity | Target | Tool |
|----------|--------|------|
| Apollo searches | 50 leads/day | Apollo API |
| Cold emails sent | 20/day | SendGrid (gated) |
| Cold calls made | 10/day | Twilio + AI agent |
| Demos booked | 2/day | Calendar link |
| Trials started | 1/day | Stripe checkout |

---

## Success Metrics

- **Response Rate**: >5% on cold email
- **Demo Booking Rate**: >10% of replies
- **Trial-to-Paid**: >30% conversion
- **Churn**: <5% monthly

**Revenue Math**: 
- 100 trials/month → 30 customers → $3,000 MRR (at $99 avg)
- Goal: 100 customers = $10,000 MRR in 4 months

---

## Integration Notes

1. **Apollo API**: Use `POST /people/search` with filters above
2. **Approval Gate**: Bulk export (>50 leads) requires CEO approval
3. **CRM Sync**: Approved leads → HubSpot/Pipedrive via webhook
4. **Email Sending**: Max 20/day per domain to avoid spam flags
5. **Call Tracking**: Log all outbound calls in BBB task queue
