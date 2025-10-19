# Better Business Builder (BBB)

**Turn-Key Autonomous Business Platform** - Onboard once, collect passive income forever.

Better Business Builder deploys **Level 6 Autonomous AI Agents** that run your business completely hands-off. You onboard, the AI handles EVERYTHING, you get paid.

## 🤖 Fully Autonomous Operation

BBB agents handle:

- ✅ **Research & Market Analysis** - Identify opportunities, track competitors, analyze trends
- ✅ **Content Creation & Marketing** - SEO blogs, social media, email campaigns, Google Ads
- ✅ **Lead Generation** - Find prospects, qualify leads, nurture relationships
- ✅ **Sales & Closing** - Cold outreach, discovery calls, proposals, deal closing
- ✅ **Fulfillment** - Deliver products/services with quality assurance
- ✅ **Customer Support** - 24/7 email/chat support, issue resolution, retention
- ✅ **Financial Management** - Invoicing, payment processing, revenue tracking, reporting

## 💰 Passive Income Model

1. **Onboard** (15 minutes): Answer a few questions about your preferences
2. **Deploy Agents** (Instant): Level 6 AI agents activate and start working
3. **Monitor** (Optional): Check your dashboard to see revenue growth
4. **Get Paid** (Automatic): Agents generate revenue, you collect checks

Target: **$20,000+ per quarter** in passive income.

## Quick Start

> Requires Python 3.9 or later.

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### Option 1: Launch Beautiful GUI

```bash
bbb --gui
```

Opens interactive web interface with:
- Onboarding wizard
- Business idea explorer (32+ businesses across 11 industries)
- Quantum optimization results
- Financial projections
- Business plan export (Markdown/JSON)

### Option 2: Deploy Autonomous Business (Level 6 Agents)

```bash
bbb --autonomous --business "AI Chatbot Integration Service" --duration 24
```

Deploys Level 6 autonomous agents that:
- Run your business 24/7 completely hands-off
- Handle research, marketing, sales, fulfillment, support, finance
- Generate revenue while you sleep
- Report metrics to your dashboard

### Option 3: CLI Interview

```bash
bbb
```

Interactive command-line onboarding that produces:
1. Personalized business recommendations targeting $20K/quarter
2. Action steps including IRS EIN enrollment
3. Financial projections and optimization scores

### Programmatic Usage

```python
from blank_business_builder import OnboardingAssistant
from blank_business_builder.autonomous_business import launch_autonomous_business
import asyncio

# Traditional onboarding
assistant = OnboardingAssistant()
outcome = assistant.run()
print(outcome["plan"][0])

# Launch autonomous business
async def main():
    metrics = await launch_autonomous_business(
        business_concept="AI Chatbot Integration Service",
        founder_name="Your Name",
        duration_hours=24.0
    )
    print(f"Revenue generated: ${metrics['metrics']['revenue']['total']}")

asyncio.run(main())
```

## How the Quantum Forecast Works

The `QuantumOptimizer` converts projected quarterly profits into probability amplitudes (squared amplitudes sum to one). Concepts with stronger profit signals receive higher measurement probabilities. The optimizer:

1. Projects three-month profit, modelling ramp-up months before full revenue.
2. Filters out ideas that fail the $4,500/month floor when alternatives exist.
3. Flags whether the $20,000 quarterly target is met so you can iterate if the bar is not hit.

This is intentionally lightweight—no external quantum SDK is required—yet the amplitude model keeps the selection logic explainable.

## Jiminy Cricket Oversight

The assistant instantiates a mini Jiminy Cricket guardian each run. It:

- Verifies that a LICENSE file exists (if absent, you are reminded to add one).
- Emits reminders about regulatory compliance and manual verification steps.
- Wraps the intake session inside a conscience context so you receive completion cues.

Add your own checks by passing a custom `JiminyCricket` instance into `OnboardingAssistant`.

## Extending Business Ideas

Additional business templates can be appended to `src/blank_business_builder/business_data.py`. For each idea specify:

- `startup_cost`
- `expected_monthly_revenue`
- `expected_monthly_expenses`
- `time_commitment_hours_per_week`
- `ramp_up_months`

The optimizer instantly reevaluates the new portfolio during the next run.

## Roadmap

- Optional HTTP integration to validate government portal uptime with retries.
- Export onboarding plans to Markdown or Notion for follow-up tracking.
- Integrate additional compliance checkpoints per state.

Operate ethically, confirm each regulatory step manually, and use the IRS portal above for official EIN issuance.
