"""Echo Prime optimization and lightweight Parliament validation."""

from .ech0_prime_validation import ECH0PrimeOptimizer


class EnhancedParliamentValidator:
    """Compatibility validator for Echo Prime BBB checks."""

    async def enhanced_validation_pipeline(self, invention):
        optimized = await ECH0PrimeOptimizer().optimize_invention(invention)
        score = optimized.get("prime_score", 0.0)
        return {
            "optimized_invention": optimized,
            "scores": {"final_approval": score},
            "parliament_status": "APPROVED" if score >= 0.85 else "NEEDS_REFINEMENT",
        }


__all__ = ["ECH0PrimeOptimizer", "EnhancedParliamentValidator"]
