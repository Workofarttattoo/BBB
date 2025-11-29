"""
Lightweight onboarding assistant that guides new business setup.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

from .business_data import BusinessIdea, default_ideas
from .jiminy import JiminyCricket, create_jiminy, check_license_file
from .quantum_optimizer import QuantumOptimizer, OptimizationResult

IRS_EIN_URL = (
    "https://www.irs.gov/businesses/small-businesses-self-employed/"
    "apply-for-an-employer-identification-number-ein-online"
)

PromptFn = Callable[[str], str]


@dataclass
class FounderProfile:
    name: str
    location_state: str
    preferred_industry: str
    weekly_hours: int
    startup_budget: float
    risk_posture: str


class OnboardingAssistant:
    """Guides a user through onboarding and recommends business ideas."""

    def __init__(
        self,
        prompt_fn: Optional[PromptFn] = None,
        optimizer: Optional[QuantumOptimizer] = None,
        jiminy: Optional[JiminyCricket] = None,
        ideas: Optional[Iterable[BusinessIdea]] = None,
    ) -> None:
        self.prompt_fn = prompt_fn or (lambda q: input(q + " "))
        self.optimizer = optimizer or QuantumOptimizer()
        reminders = [
            "Verify regulatory requirements for your industry before accepting payments.",
            "Use the official IRS EIN portal when applying for federal identifiers.",
            "Document manual checks after running the quantum forecast.",
        ]
        self.jiminy = jiminy or create_jiminy(
            reminders=reminders,
            checks=[check_license_file()],
        )
        self.ideas = list(ideas or default_ideas())

    def _ask(self, question: str, validator: Callable[[str], bool], cast: Callable[[str], object]) -> object:
        while True:
            response = self.prompt_fn(question)
            response = response.strip()
            if validator(response):
                return cast(response)
            print("Let's try that again—please provide a valid response.")

    def collect_profile(self) -> FounderProfile:
        with self.jiminy.conscience("founder_onboarding"):
            name = str(
                self._ask(
                    "What is your name?",
                    validator=lambda x: len(x) >= 2,
                    cast=lambda x: x,
                )
            )
            location_state = str(
                self._ask(
                    "Which U.S. state will you operate from?",
                    validator=lambda x: len(x) >= 2,
                    cast=lambda x: x.upper(),
                )
            )
            preferred_industry = str(
                self._ask(
                    "Which industry do you want to explore? (Finance, Ecommerce, Healthcare, etc.)",
                    validator=lambda x: len(x) >= 3,
                    cast=lambda x: x.title(),
                )
            )
            weekly_hours = int(
                self._ask(
                    "How many hours per week can you commit?",
                    validator=lambda x: x.isdigit() and 1 <= int(x) <= 80,
                    cast=int,
                )
            )
            startup_budget = float(
                self._ask(
                    "What is your startup budget in USD?",
                    validator=lambda x: x.replace(".", "", 1).isdigit(),
                    cast=float,
                )
            )
            risk_posture = str(
                self._ask(
                    "Risk posture? (conservative / balanced / bold)",
                    validator=lambda x: x.lower() in {"conservative", "balanced", "bold"},
                    cast=lambda x: x.lower(),
                )
            )
        self.jiminy.affirm("Founder profile captured successfully.")
        return FounderProfile(
            name=name,
            location_state=location_state,
            preferred_industry=preferred_industry,
            weekly_hours=weekly_hours,
            startup_budget=startup_budget,
            risk_posture=risk_posture,
        )

    def shortlist(self, profile: FounderProfile) -> List[BusinessIdea]:
        candidates: List[BusinessIdea] = []
        for idea in self.ideas:
            if idea.startup_cost > profile.startup_budget * 1.2:
                continue
            if idea.time_commitment_hours_per_week > profile.weekly_hours * 1.2:
                continue
            if profile.preferred_industry.lower() not in idea.industry.lower():
                # keep adjacent industries but skip if no overlap and not finance generalist
                if profile.preferred_industry.lower() != "generalist":
                    continue
            candidates.append(idea)
        if not candidates:
            self.jiminy.affirm(
                "No direct matches found; expanding search to all ideas for exploratory review."
            )
            candidates = self.ideas
        return candidates

    def recommend(self, profile: FounderProfile, top_n: int = 3) -> List[OptimizationResult]:
        ideas = self.shortlist(profile)
        results = self.optimizer.evaluate(ideas)
        filtered = [r for r in results if r.meets_floor]
        if not filtered:
            filtered = results
        return filtered[:top_n]

    def onboarding_steps(self, profile: FounderProfile, selections: List[OptimizationResult]) -> List[str]:
        best = selections[0] if selections else None
        steps = [
            f"Hello {profile.name}, based in {profile.location_state}. Let's formalize your idea.",
            "1. Confirm your business structure (LLC, sole proprietorship, etc.) with a local advisor.",
            (
                "2. Apply for your Employer Identification Number (EIN) via the official IRS portal: "
                f"{IRS_EIN_URL}"
            ),
            "3. Register for state and local permits as required by your jurisdiction.",
            "4. Set up a dedicated business bank account and bookkeeping workflow.",
            "5. Draft a 90-day execution plan with weekly checkpoints.",
        ]
        if best:
            steps.insert(
                1,
                (
                    f"Recommended concept: {best.idea.name} ({best.idea.industry}) — expected monthly profit "
                    f"${best.monthly_average:,.2f} with success probability {best.success_probability:.2%}."
                ),
            )
            if not best.meets_floor:
                steps.append(
                    "⚠️ Forecast lands below the $4,500/month floor. Consider increasing budget or available hours."
                )
            if not best.meets_target:
                steps.append(
                    "⚠️ Quarterly target of $20,000 is not yet met. Iterate on pricing, marketing, or alternative concepts."
                )
        return steps

    def run(self) -> Dict[str, object]:
        profile = self.collect_profile()
        selections = self.recommend(profile)
        plan = self.onboarding_steps(profile, selections)
        return {
            "profile": profile,
            "recommendations": selections,
            "plan": plan,
            "irs_ein_url": IRS_EIN_URL,
        }
