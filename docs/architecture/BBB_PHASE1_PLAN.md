BBB Phase 1 Kickoff — Database · Auth · Payments
===============================================

Scope (4 Weeks)
---------------
- Harden the data model for licensing, revenue share, and tier limits.
- Enforce license-aware auth guards and quantum feature gating.
- Restructure paid plans (Starter, Pro, Enterprise) and surface upgrade paths.
- Define repository encryption boundaries with git-crypt while keeping demo flow accessible.

Database Upgrades
-----------------
- `users` table now tracks:
  - `subscription_tier` (`free`, `starter`, `pro`, `enterprise`)
  - `license_status` (`trial`, `revenue_share`, `licensed`, `suspended`)
  - `license_agreed_at`, `license_terms_version`, `trial_expires_at`
  - `revenue_share_percentage`
  - `stripe_customer_id`, `is_active`
- `businesses` table gains canonical fields (`business_name`, `industry`, `description`, `website_url`, `created_at`).
- New relational tables:
  - `business_plans` for AI-generated plan storage.
  - `marketing_campaigns` for auto-created campaigns and performance blobs.
- `subscriptions` table normalized around plan lookup keys (`starter`, `pro`, `enterprise`) and cancellation state.

Auth & License Enforcement
--------------------------
- `RoleBasedAccessControl` refreshed with tier caps (3/6/12 businesses) and feature flags (`core`, `quantum`, `enterprise`).
- New dependencies:
  - `require_license_access` blocks core actions until the user either (a) accepts 50% revenue share or (b) activates a license.
  - `require_quantum_access` restricts `/api/quantum/*` to Pro+ tiers.
- Trial window defaults to 7 days on registration; cancellations drop accounts back to `trial` with a 3-day grace period.
- License endpoints:
  - `POST /api/license/accept-revenue-share` → locks revenue share percentage (defaults 50%).
  - `POST /api/license/activate` → upgrades tier post-checkout.
  - `GET /api/license/status` → surfaces current gate state to the UI.

Payments & Pricing
------------------
- Stripe plan catalog consolidated in `StripeService.PLANS`:

  | Plan       | Monthly | Business Cap | Highlights                              |
  |------------|---------|--------------|-----------------------------------------|
  | Starter    | $299    | 3            | Core automations, demo unlock            |
  | Pro        | $799    | 6            | Quantum workflows, premium automations   |
  | Enterprise | $1,499  | 12           | Unlimited ops, white-label dashboards    |

- Checkout endpoint now accepts plan keys (`starter`, `pro`, `enterprise`) and seeds metadata for provisioning.
- Webhook handlers align subscription lookups with new tiers and gracefully downgrade on cancellation.

git-crypt Lockdown Strategy
---------------------------
1. **Initialize** (one-time, repo root):
   ```bash
   git-crypt init
   git-crypt add-gpg-user <YOUR-GPG-ID>
   ```
2. **Scope encryption** via `.gitattributes`:
   ```
   src/blank_business_builder/premium_workflows/** filter=git-crypt diff=git-crypt
   src/blank_business_builder/quantum_*/**        filter=git-crypt diff=git-crypt
   src/blank_business_builder/level6_agent.py     filter=git-crypt diff=git-crypt
   src/blank_business_builder/all_features_implementation.py filter=git-crypt diff=git-crypt
   logs/**                                        filter=git-crypt diff=git-crypt
   ```
   Leave lightweight demo scaffolding (`main.py`, `api/`, `public/`) unencrypted so the app boots and showcases basic flows.
3. **Operational cadence**:
   - Run `git-crypt lock` before pushing public demos.
   - Distribute the git-crypt key only after revenue-share acceptance or paid license execution.
   - Capture encrypted blob fingerprints in release notes to audit who accessed proprietary modules.

Deliverables & Next Actions
---------------------------
1. **Week 1:** finalize DB migrations + seed scripts, enable git-crypt attributes, document unlock workflow.
2. **Week 2:** wire UI screens for license prompts, revenue share acknowledgement, and Stripe checkout.
3. **Week 3:** expand audit logging (license state transitions, quantum feature usage).
4. **Week 4:** smoke validation: trial lockouts, Pro quantum access, enterprise campaign ceilings.

Future Enhancements
-------------------
- Integrate automated reminders before trial expiry/grace revocation.
- Add SLA dashboards for enterprise accounts (counts against the 12-business cap).
- Capture revenue share payouts in a dedicated ledger for finance reconciliation.
- Layer feature toggles so marketing site can run in pure demo mode without decrypting git-crypt content.
