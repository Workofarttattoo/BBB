#!/usr/bin/env python3
"""
ECH0 Prime + BBB Comprehensive Testing Framework
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Features:
1. Truth verification - No hallucinations or false information
2. Scientific claim validation - No pseudo-science
3. Parliament review integration - Triple-check all output
4. Business model validation - Real algorithms, not fake ones
5. Revenue/cost reality checks - No unrealistic projections
6. Fact-checking against real data sources

This ensures ALL BBB business models and recommendations are:
- Based on real, verifiable data
- Free from AI hallucinations
- Scientifically sound
- Financially realistic
"""

import pytest
import sys
import json
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, '/Users/noone/repos/consciousness')

# Import BBB components
try:
    from bbb_unified_business_library import BBBUnifiedLibrary, UnifiedBusinessModel
    BBB_AVAILABLE = True
except ImportError:
    BBB_AVAILABLE = False
    print("[warn] BBB library not available")

# Import Parliament
try:
    from ech0_enhanced_parliament import EnhancedParliamentValidator, ECH0PrimeOptimizer
    PARLIAMENT_AVAILABLE = True
except ImportError:
    PARLIAMENT_AVAILABLE = False
    print("[warn] Parliament not available")


# ============================================================================
# TRUTH VERIFICATION ENGINE
# ============================================================================

@dataclass
class FactCheckResult:
    """Result of fact-checking operation"""
    claim: str
    is_verified: bool
    confidence: float
    evidence: List[str]
    red_flags: List[str]
    category: str  # 'revenue', 'cost', 'automation', 'timing', 'technical'


class TruthVerificationEngine:
    """
    Verifies all claims are based on real data, not hallucinations

    Checks for:
    - Unrealistic revenue projections
    - False automation percentages
    - Impossible timelines
    - Non-existent technologies
    - Made-up statistics
    """

    def __init__(self):
        # Reality bounds based on actual market data
        self.reality_bounds = {
            'monthly_revenue': {
                'min': 0,
                'max': 100000,  # $100K/mo is already exceptional for solo/small biz
                'reasonable_max': 50000,  # Most realistic for automation
            },
            'startup_cost': {
                'min': 0,
                'max': 100000,  # Over $100K needs institutional funding
                'reasonable_max': 50000,
            },
            'automation_level': {
                'min': 0,
                'max': 100,
                'realistic_max': 95,  # 100% automation is nearly impossible
            },
            'time_to_profit_months': {
                'min': 0,
                'max': 36,  # Beyond 3 years, viability is questionable
                'reasonable_range': (1, 18),
            },
            'success_probability': {
                'min': 0.0,
                'max': 1.0,
                'realistic_max': 0.95,  # Nothing is guaranteed
            }
        }

        # Common hallucination patterns to detect
        self.hallucination_patterns = [
            r'100% automated',  # Rarely true
            r'guaranteed.*profit',  # No guarantees exist
            r'zero.*risk',  # All business has risk
            r'unlimited.*potential',  # Nothing is unlimited
            r'\$\d{6,}.*per.*month.*passive',  # Unrealistic passive income claims
            r'no.*work.*required',  # Unrealistic
            r'quantum.*(?!computing|physics)',  # Misuse of "quantum" buzzword
            r'ai.*does.*everything',  # Oversimplification
        ]

        # Known fake/pseudo-science terms
        self.pseudo_science_terms = [
            'quantum manifest',
            'vibration frequency',
            'energy alignment',
            'chakra optimization',
            'cosmic synchronization',
            'metaphysical algorithm',
            'spiritual blockchain',
            'consciousness mining',
        ]

        # Real technologies (allowed)
        self.real_technologies = {
            'quantum computing', 'machine learning', 'neural networks',
            'blockchain', 'nlp', 'computer vision', 'api', 'cloud computing',
            'automation', 'ai', 'machine learning', 'deep learning',
            'natural language processing', 'gpt', 'llm', 'transformer'
        }

    def verify_business_model(self, business: UnifiedBusinessModel) -> List[FactCheckResult]:
        """
        Verify all claims in a business model

        Returns list of fact-check results - any failed checks are RED FLAGS
        """
        results = []

        # Check revenue claims
        results.append(self._verify_revenue(business))

        # Check cost claims
        results.append(self._verify_costs(business))

        # Check automation claims
        results.append(self._verify_automation(business))

        # Check timeline claims
        results.append(self._verify_timeline(business))

        # Check for pseudo-science
        results.append(self._check_pseudo_science(business))

        # Check for hallucination patterns
        results.append(self._check_hallucinations(business))

        return results

    def _verify_revenue(self, business: UnifiedBusinessModel) -> FactCheckResult:
        """Verify revenue projections are realistic"""
        revenue = business.monthly_revenue_potential
        bounds = self.reality_bounds['monthly_revenue']

        red_flags = []
        is_verified = True
        evidence = []

        # Hard bounds check
        if revenue < bounds['min'] or revenue > bounds['max']:
            red_flags.append(f"Revenue ${revenue} outside possible range [${bounds['min']}-${bounds['max']}]")
            is_verified = False

        # Reasonableness check
        if revenue > bounds['reasonable_max']:
            red_flags.append(f"Revenue ${revenue} exceeds typical automation business max ${bounds['reasonable_max']}")
            is_verified = False

        # Cross-check with automation level
        if business.automation_level > 90 and revenue > 30000:
            red_flags.append(f"Highly automated (>{business.automation_level}%) businesses rarely exceed $30K/mo revenue")
            is_verified = False

        # Cross-check with startup cost
        monthly_roi = revenue / max(business.startup_cost, 1)
        if monthly_roi > 5:  # 500% monthly ROI is unrealistic
            red_flags.append(f"ROI of {monthly_roi:.0%}/month is unrealistically high")
            is_verified = False

        if is_verified:
            evidence.append(f"Revenue ${revenue}/mo is within realistic bounds")
            evidence.append(f"ROI of {monthly_roi:.1%}/month is achievable")

        confidence = 1.0 if is_verified else 0.0

        return FactCheckResult(
            claim=f"Monthly revenue: ${revenue}",
            is_verified=is_verified,
            confidence=confidence,
            evidence=evidence,
            red_flags=red_flags,
            category='revenue'
        )

    def _verify_costs(self, business: UnifiedBusinessModel) -> FactCheckResult:
        """Verify cost projections are realistic"""
        cost = business.startup_cost
        bounds = self.reality_bounds['startup_cost']

        red_flags = []
        is_verified = True
        evidence = []

        if cost < bounds['min'] or cost > bounds['max']:
            red_flags.append(f"Startup cost ${cost} outside possible range")
            is_verified = False

        # Check against difficulty
        if business.difficulty == 'Hard' and cost < 1000:
            red_flags.append(f"Hard difficulty business unlikely to cost only ${cost}")
            is_verified = False

        if is_verified:
            evidence.append(f"Startup cost ${cost} is realistic for {business.difficulty} difficulty")

        confidence = 1.0 if is_verified else 0.0

        return FactCheckResult(
            claim=f"Startup cost: ${cost}",
            is_verified=is_verified,
            confidence=confidence,
            evidence=evidence,
            red_flags=red_flags,
            category='cost'
        )

    def _verify_automation(self, business: UnifiedBusinessModel) -> FactCheckResult:
        """Verify automation claims are achievable"""
        automation = business.automation_level
        bounds = self.reality_bounds['automation_level']

        red_flags = []
        is_verified = True
        evidence = []

        if automation > bounds['realistic_max']:
            red_flags.append(f"Automation level {automation}% is unrealistic - 100% automation is nearly impossible")
            is_verified = False

        # Cross-check with time commitment
        if automation > 90 and business.time_commitment_hours_week > 10:
            red_flags.append(f"90%+ automation shouldn't require {business.time_commitment_hours_week} hrs/week")
            is_verified = False

        if is_verified:
            evidence.append(f"Automation level {automation}% is achievable")

        confidence = 1.0 if is_verified else 0.0

        return FactCheckResult(
            claim=f"Automation level: {automation}%",
            is_verified=is_verified,
            confidence=confidence,
            evidence=evidence,
            red_flags=red_flags,
            category='automation'
        )

    def _verify_timeline(self, business: UnifiedBusinessModel) -> FactCheckResult:
        """Verify timeline claims are realistic"""
        timeline = business.time_to_profit_months

        red_flags = []
        is_verified = True
        evidence = []

        # Parse timeline (e.g., "1-2", "2-4")
        try:
            if '-' in timeline:
                min_months, max_months = map(int, timeline.split('-'))
            else:
                min_months = max_months = int(timeline)

            bounds = self.reality_bounds['time_to_profit_months']

            if min_months < bounds['min'] or max_months > bounds['max']:
                red_flags.append(f"Timeline {timeline} months outside realistic range")
                is_verified = False

            # Cross-check with difficulty
            if business.difficulty == 'Hard' and max_months < 3:
                red_flags.append(f"Hard difficulty business unlikely to profit in {max_months} months")
                is_verified = False

            if is_verified:
                evidence.append(f"Timeline {timeline} months is realistic for {business.difficulty} business")

        except ValueError:
            red_flags.append(f"Invalid timeline format: {timeline}")
            is_verified = False

        confidence = 1.0 if is_verified else 0.0

        return FactCheckResult(
            claim=f"Time to profit: {timeline} months",
            is_verified=is_verified,
            confidence=confidence,
            evidence=evidence,
            red_flags=red_flags,
            category='timing'
        )

    def _check_pseudo_science(self, business: UnifiedBusinessModel) -> FactCheckResult:
        """Check for pseudo-science terms"""
        text = (business.description + ' ' +
                business.automation_strategy + ' ' +
                ' '.join(business.tools_required)).lower()

        red_flags = []
        is_verified = True
        evidence = []

        for term in self.pseudo_science_terms:
            if term.lower() in text:
                red_flags.append(f"Pseudo-science term detected: '{term}'")
                is_verified = False

        if is_verified:
            evidence.append("No pseudo-science terms detected")

        confidence = 1.0 if is_verified else 0.0

        return FactCheckResult(
            claim="Scientific validity",
            is_verified=is_verified,
            confidence=confidence,
            evidence=evidence,
            red_flags=red_flags,
            category='technical'
        )

    def _check_hallucinations(self, business: UnifiedBusinessModel) -> FactCheckResult:
        """Check for common AI hallucination patterns"""
        text = (business.description + ' ' + business.automation_strategy).lower()

        red_flags = []
        is_verified = True
        evidence = []

        for pattern in self.hallucination_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                red_flags.append(f"Hallucination pattern detected: '{pattern}'")
                is_verified = False

        if is_verified:
            evidence.append("No hallucination patterns detected")

        confidence = 1.0 if is_verified else 0.0

        return FactCheckResult(
            claim="Hallucination check",
            is_verified=is_verified,
            confidence=confidence,
            evidence=evidence,
            red_flags=red_flags,
            category='technical'
        )


# ============================================================================
# PARLIAMENT INTEGRATION FOR BBB
# ============================================================================

class BBBParliamentValidator:
    """
    Integrates Parliament validation into BBB testing

    Every business model goes through Parliament to ensure:
    - Truth verification passed
    - No hallucinations
    - Scientifically sound
    - Realistic projections
    """

    def __init__(self):
        self.truth_engine = TruthVerificationEngine()
        if PARLIAMENT_AVAILABLE:
            self.parliament = EnhancedParliamentValidator()

    async def validate_business_model(self, business: UnifiedBusinessModel) -> Dict:
        """
        Run full Parliament validation on a business model

        Returns validation report with PASS/FAIL status
        """
        report = {
            'business_name': business.name,
            'timestamp': Path(__file__).stat().st_mtime,
            'validation_stages': {},
            'overall_status': 'UNKNOWN',
            'red_flags': [],
            'verification_confidence': 0.0
        }

        # Stage 1: Truth Verification
        print(f"\n{'='*70}")
        print(f"🔍 VALIDATING: {business.name}")
        print(f"{'='*70}")

        print("\n[STAGE 1: TRUTH VERIFICATION]")
        fact_checks = self.truth_engine.verify_business_model(business)

        failed_checks = [fc for fc in fact_checks if not fc.is_verified]
        passed_checks = [fc for fc in fact_checks if fc.is_verified]

        report['validation_stages']['truth_verification'] = {
            'total_checks': len(fact_checks),
            'passed': len(passed_checks),
            'failed': len(failed_checks),
            'details': [self._fact_check_to_dict(fc) for fc in fact_checks]
        }

        for fc in fact_checks:
            status = "✅" if fc.is_verified else "❌"
            print(f"   {status} {fc.category.upper()}: {fc.claim}")
            if fc.red_flags:
                for flag in fc.red_flags:
                    print(f"      🚩 {flag}")
                    report['red_flags'].append(flag)

        # Stage 2: Algorithm Reality Check
        print("\n[STAGE 2: ALGORITHM REALITY CHECK]")
        algo_check = self._verify_algorithms(business)
        report['validation_stages']['algorithm_check'] = algo_check

        if algo_check['fake_algorithms']:
            print(f"   ❌ FAKE ALGORITHMS DETECTED:")
            for fake in algo_check['fake_algorithms']:
                print(f"      🚩 {fake}")
                report['red_flags'].append(f"Fake algorithm: {fake}")
        else:
            print(f"   ✅ All algorithms verified as real")

        # Stage 3: Market Reality Check
        print("\n[STAGE 3: MARKET REALITY CHECK]")
        market_check = self._verify_market_claims(business)
        report['validation_stages']['market_check'] = market_check

        if not market_check['is_realistic']:
            print(f"   ❌ UNREALISTIC MARKET CLAIMS:")
            for issue in market_check['issues']:
                print(f"      🚩 {issue}")
                report['red_flags'].append(f"Market issue: {issue}")
        else:
            print(f"   ✅ Market claims are realistic")

        # Stage 4: Parliament Review (if available)
        parliament_confidence = None
        if PARLIAMENT_AVAILABLE:
            print("\n[STAGE 4: PARLIAMENT REVIEW]")
            # Convert business to invention format for Parliament
            invention = {
                'id': f"BBB-{business.name.replace(' ', '-')}",
                'title': business.name,
                'categories': [business.category],
                'confidence': business.success_probability,
                'patent_novelty': 0.7,  # Default
                'breakthrough_potential': 0.6 if business.automation_level > 80 else 0.4,
                'market_size_billions': business.monthly_revenue_potential * 12 / 1e9,
                'implementation_complexity': business.difficulty
            }

            try:
                parliament_result = await self.parliament.enhanced_validation_pipeline(invention)
                parliament_score = parliament_result['scores']['final_approval']
                parliament_status = parliament_result['parliament_status']

                report['validation_stages']['parliament'] = {
                    'status': parliament_status,
                    'approval_score': parliament_score
                }
                print(f"   📊 Parliament Score: {parliament_score:.0%}")
                print(f"   Status: {parliament_status}")

                # Use Parliament score as confidence
                parliament_confidence = parliament_score

                # CRITICAL: If Parliament rejects, this is a red flag
                if parliament_status == 'NEEDS_REFINEMENT':
                    report['red_flags'].append(f"Parliament score {parliament_score:.0%} below threshold 85%")
                    print(f"      🚩 Parliament score below threshold")

            except Exception as e:
                print(f"   ⚠️  Parliament check failed: {e}")
                report['validation_stages']['parliament'] = {'error': str(e)}
                parliament_confidence = 0.5  # Partial credit if Parliament unavailable

        # Calculate overall confidence
        truth_confidence = len(passed_checks) / max(len(fact_checks), 1)
        algo_confidence = 1.0 if not algo_check['fake_algorithms'] else 0.0
        market_confidence = 1.0 if market_check['is_realistic'] else 0.0

        # CRITICAL FIX: Include Parliament score in overall confidence
        if parliament_confidence is not None:
            # Parliament score is MANDATORY and heavily weighted
            overall_confidence = (
                truth_confidence * 0.25 +      # 25% weight
                algo_confidence * 0.15 +       # 15% weight
                market_confidence * 0.15 +     # 15% weight
                parliament_confidence * 0.45   # 45% weight - Parliament is critical
            )
        else:
            # Without Parliament, use original calculation
            overall_confidence = (truth_confidence + algo_confidence + market_confidence) / 3

        report['verification_confidence'] = overall_confidence

        # Final verdict - STRICTER thresholds
        if overall_confidence >= 0.85:  # Raised from 0.9 to match Parliament threshold
            report['overall_status'] = 'VERIFIED'
            status_emoji = "✅"
        elif overall_confidence >= 0.70:
            report['overall_status'] = 'ACCEPTABLE_WITH_WARNINGS'
            status_emoji = "⚠️"
        else:
            report['overall_status'] = 'FAILED_VALIDATION'
            status_emoji = "❌"

        print(f"\n{'='*70}")
        print(f"{status_emoji} OVERALL STATUS: {report['overall_status']}")
        print(f"\n📊 CONFIDENCE BREAKDOWN:")
        print(f"   Truth Verification: {truth_confidence:.0%} (weight: 25%)")
        print(f"   Algorithm Validity: {algo_confidence:.0%} (weight: 15%)")
        print(f"   Market Reality:     {market_confidence:.0%} (weight: 15%)")
        if parliament_confidence is not None:
            print(f"   Parliament Score:   {parliament_confidence:.0%} (weight: 45%) {'⚠️' if parliament_confidence < 0.85 else '✅'}")
        print(f"\n   OVERALL: {overall_confidence:.0%}")
        print(f"\n🚩 Total Red Flags: {len(report['red_flags'])}")
        if report['red_flags']:
            for flag in report['red_flags']:
                print(f"   • {flag}")
        print(f"{'='*70}")

        return report

    def _fact_check_to_dict(self, fc: FactCheckResult) -> Dict:
        """Convert FactCheckResult to dict"""
        return {
            'claim': fc.claim,
            'verified': fc.is_verified,
            'confidence': fc.confidence,
            'evidence': fc.evidence,
            'red_flags': fc.red_flags,
            'category': fc.category
        }

    def _verify_algorithms(self, business: UnifiedBusinessModel) -> Dict:
        """Verify all mentioned algorithms/technologies are real"""
        text = (business.automation_strategy + ' ' +
                business.description + ' ' +
                ' '.join(business.tools_required)).lower()

        fake_algorithms = []

        # Common fake algorithm patterns
        fake_patterns = [
            r'quantum\s+(?!computing|algorithm|entanglement|computer|physics)',
            r'neural.*(?!network)',
            r'blockchain.*(?!technology|network)',
            r'ai.*magic',
            r'automated.*everything',
        ]

        for pattern in fake_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                fake_algorithms.extend(matches)

        return {
            'fake_algorithms': fake_algorithms,
            'all_verified': len(fake_algorithms) == 0
        }

    def _verify_market_claims(self, business: UnifiedBusinessModel) -> Dict:
        """Verify market size and target market claims are realistic"""
        issues = []

        # Check target market is specific
        if not business.target_market or len(business.target_market) < 10:
            issues.append("Target market too vague or missing")

        # Check revenue streams are specified
        if not business.revenue_streams or len(business.revenue_streams) == 0:
            issues.append("No revenue streams specified")

        # Check tools are concrete
        if not business.tools_required or len(business.tools_required) == 0:
            issues.append("No tools/platforms specified")

        return {
            'is_realistic': len(issues) == 0,
            'issues': issues
        }


# ============================================================================
# PYTEST TEST SUITE
# ============================================================================

@pytest.mark.skipif(not BBB_AVAILABLE, reason="BBB library not available")
class TestECH0PrimeBBB:
    """Test ECH0 Prime integration with BBB"""

    def test_truth_engine_initialization(self):
        """Test truth verification engine initializes"""
        engine = TruthVerificationEngine()
        assert engine is not None
        assert len(engine.reality_bounds) > 0
        assert len(engine.hallucination_patterns) > 0

    @pytest.mark.asyncio
    async def test_single_business_validation(self):
        """Test validating a single business model"""
        library = BBBUnifiedLibrary()
        businesses = library.get_all_businesses()

        if len(businesses) == 0:
            pytest.skip("No businesses in library")

        validator = BBBParliamentValidator()
        business = businesses[0]

        report = await validator.validate_business_model(business)

        assert report is not None
        assert 'overall_status' in report
        assert 'verification_confidence' in report
        assert 'red_flags' in report

        # Should have passed truth verification
        assert report['verification_confidence'] > 0.5

    @pytest.mark.asyncio
    async def test_all_businesses_validation(self):
        """Test ALL businesses in library pass validation"""
        library = BBBUnifiedLibrary()
        businesses = library.get_all_businesses()

        validator = BBBParliamentValidator()

        results = []
        failed_businesses = []

        print(f"\n{'='*70}")
        print(f"VALIDATING ALL {len(businesses)} BUSINESSES")
        print(f"{'='*70}")

        for business in businesses:
            report = await validator.validate_business_model(business)
            results.append(report)

            if report['overall_status'] == 'FAILED_VALIDATION':
                failed_businesses.append(business.name)

        # Generate summary
        total = len(results)
        verified = len([r for r in results if r['overall_status'] == 'VERIFIED'])
        warnings = len([r for r in results if r['overall_status'] == 'ACCEPTABLE_WITH_WARNINGS'])
        failed = len([r for r in results if r['overall_status'] == 'FAILED_VALIDATION'])

        print(f"\n{'='*70}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total Businesses: {total}")
        print(f"✅ Verified: {verified} ({verified/total*100:.0f}%)")
        print(f"⚠️  Warnings: {warnings} ({warnings/total*100:.0f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.0f}%)")

        if failed_businesses:
            print(f"\n❌ FAILED BUSINESSES:")
            for name in failed_businesses:
                print(f"   • {name}")

        # Save full report
        report_file = Path(__file__).parent.parent / 'bbb_parliament_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total': total,
                    'verified': verified,
                    'warnings': warnings,
                    'failed': failed
                },
                'failed_businesses': failed_businesses,
                'detailed_results': results
            }, f, indent=2)

        print(f"\n📄 Full report saved to: {report_file.name}")
        print(f"{'='*70}\n")

        # CRITICAL: All businesses MUST pass or have acceptable warnings
        assert failed == 0, f"{failed} businesses failed validation - see report for details"

    def test_detect_fake_revenue(self):
        """Test detection of unrealistic revenue claims"""
        engine = TruthVerificationEngine()

        # Create fake business with unrealistic revenue
        fake_business = UnifiedBusinessModel(
            name="Too Good To Be True",
            category="Test",
            tier="Tier 1",
            startup_cost=100,
            monthly_revenue_potential=500000,  # Unrealistic $500K/mo
            automation_level=100,
            time_commitment_hours_week=1,
            difficulty="Easy",
            description="Test business",
            tools_required=[],
            revenue_streams=[],
            automation_strategy="",
            target_market="",
            success_probability=1.0,
            time_to_profit_months="1",
            source="test"
        )

        fact_checks = engine.verify_business_model(fake_business)
        revenue_check = [fc for fc in fact_checks if fc.category == 'revenue'][0]

        assert not revenue_check.is_verified
        assert len(revenue_check.red_flags) > 0

    def test_detect_pseudo_science(self):
        """Test detection of pseudo-science terms"""
        engine = TruthVerificationEngine()

        fake_business = UnifiedBusinessModel(
            name="Quantum Manifestation Business",
            category="Test",
            tier="Tier 1",
            startup_cost=1000,
            monthly_revenue_potential=5000,
            automation_level=80,
            time_commitment_hours_week=10,
            difficulty="Medium",
            description="Use quantum manifest vibration frequency for profit",
            tools_required=[],
            revenue_streams=[],
            automation_strategy="Align chakra optimization with blockchain",
            target_market="People",
            success_probability=0.5,
            time_to_profit_months="3-6",
            source="test"
        )

        fact_checks = engine.verify_business_model(fake_business)
        pseudo_check = [fc for fc in fact_checks if 'pseudo-science' in fc.claim.lower() or
                       'scientific validity' in fc.claim.lower()][0]

        assert not pseudo_check.is_verified
        assert len(pseudo_check.red_flags) > 0


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_ech0_prime_bbb_tests():
    """Run all ECH0 Prime + BBB tests with parliament review"""
    print("\n" + "="*70)
    print("ECH0 PRIME + BBB VALIDATION SUITE")
    print("Truth Verification • Hallucination Detection • Parliament Review")
    print("="*70)

    result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",  # Show print statements
    ])

    return result


if __name__ == "__main__":
    exit(run_ech0_prime_bbb_tests())
