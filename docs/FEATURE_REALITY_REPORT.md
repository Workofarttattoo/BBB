# BBB Feature Reality Report

This document validates the flagship promises in the README and surfaces where the code is already wired versus areas that still rely on external or missing pieces.

## Proven, Connected Components

- **Quantum-inspired ranking** – `QuantumOptimizer` turns business ideas into measurable three-month profit projections, probabilities, and target checks without any external services. It is fully implemented in pure Python and already used by onboarding. 【F:src/blank_business_builder/quantum_optimizer.py†L8-L69】
- **Onboarding with guardrails** – `OnboardingAssistant` runs the CLI interview, invokes `QuantumOptimizer`, and wraps the session with the Jiminy conscience helper (license check, regulatory reminders). The steps it prints are derived directly from the optimizer’s outputs. 【F:src/blank_business_builder/onboarding.py†L11-L121】【F:src/blank_business_builder/onboarding.py†L123-L177】
- **Autonomous loop with real service hooks** – The Level 6 orchestrator provisions role-specific agents that call concrete service clients (ScrapingBee + ECH0 for research, SendGrid/Twitter via ECH0 for outreach, Stripe or ECH0 for payments). The main loop assigns tasks, executes them concurrently, and updates metrics for the dashboard payload. 【F:src/blank_business_builder/autonomous_business.py†L72-L324】【F:src/blank_business_builder/autonomous_business.py†L342-L474】

## External Dependencies You Must Supply

These capabilities are coded but depend on credentials or an extra local service:

- **ECH0 local brain** – Required for the fast paths in research, email, social, and payments; the repo expects `ech0_local_brain` to be importable at runtime and does not vend that package. 【F:src/blank_business_builder/ech0_service.py†L1-L44】
- **Third-party APIs** – ScrapingBee (market research), SendGrid (email), Stripe (checkout), and Twitter via Tweepy (social posting) are used as fallbacks when ECH0 is unavailable. Without real API keys these flows will raise at runtime. 【F:src/blank_business_builder/features/market_research.py†L1-L34】【F:src/blank_business_builder/features/email_service.py†L1-L29】【F:src/blank_business_builder/features/payment_processor.py†L1-L28】【F:src/blank_business_builder/features/social_media.py†L1-L23】

## Areas That Were Vapor Until Wired Up

- **Research tasks returning real data** – Researcher agents were previously returning coroutine objects because competitor scraping and Google search were invoked without awaiting the async calls. The calls are now awaited so task results contain actual payloads when the services succeed. 【F:src/blank_business_builder/autonomous_business.py†L205-L214】
- **Service readiness** – Because dependencies are empty in `pyproject.toml`, you must install FastAPI, SQLAlchemy, SendGrid, ScrapingBee, Tweepy, and Stripe before running the API or agent workflows. (No change required here—this is a visibility warning.) 【F:pyproject.toml†L1-L15】

## Next Connection Targets

- Bundle a lightweight ECH0 shim or add feature flags so that research/email/social/payment fallbacks degrade gracefully when the local brain is absent.
- Provide sample `.env` template documenting required API keys for ScrapingBee, SendGrid, Stripe, and Twitter so the autonomous loop can run without manual code edits.
- Add integration tests that mock the external clients to validate the autonomous loop without hitting the network.
