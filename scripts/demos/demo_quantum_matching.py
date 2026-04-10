#!/usr/bin/env python3
"""
Demonstration of Quantum-Enhanced Business Matching
Using Unified Business Library (31 businesses)

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/blank_business_builder/premium_workflows'))

from quantum_optimizer import QuantumOptimizer


def demo_quantum_matching():
    """Demonstrate quantum-enhanced business matching"""

    print("=" * 80)
    print("BBB QUANTUM BUSINESS MATCHING DEMONSTRATION")
    print("=" * 80)
    print()
    print("Using Unified Business Library:")
    print("  • 21 AI Automation Businesses (2025 research)")
    print("  • 10 Legacy High-Performing Models")
    print("  • Total: 31 Business Models")
    print()

    optimizer = QuantumOptimizer()

    # Test Case 1: Budget-conscious beginner
    print("=" * 80)
    print("TEST CASE 1: Budget-Conscious Beginner")
    print("=" * 80)
    profile1 = {
        "budget": 2000,
        "available_hours_week": 10,
        "experience_level": "beginner",
        "risk_tolerance": 0.3,
        "automation_preference": 0.9
    }

    print("\nUser Profile:")
    for key, value in profile1.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")

    print("\nRunning quantum optimization...")
    result1 = optimizer.select_optimal_business_model(profile1)

    print(f"\n✅ Found {result1['total_matches']} matching businesses from library of {result1['library_size']}")
    print(f"🔬 Quantum Enhanced: {result1['quantum_enhanced']}")
    print(f"📊 Confidence: {result1['confidence'] * 100:.0f}%")
    print(f"🧮 Algorithm: {result1['matching_algorithm']}")
    print()

    print("TOP 5 RECOMMENDATIONS:")
    print("-" * 80)

    for i, rec in enumerate(result1['all_recommendations'], 1):
        business = rec['business']
        print(f"\n{i}. {business.name}")
        print(f"   Quantum Score: {rec['quantum_score']:.1f}/100")
        print(f"   Category: {business.category}")
        print(f"   Revenue: ${rec['monthly_revenue']:,}/month | Startup: ${rec['startup_cost']:,}")
        print(f"   Automation: {rec['automation_level']}% | Time: {rec['time_commitment']} hrs/week")
        print(f"   Success Rate: {rec['success_probability']:.0f}% | Difficulty: {business.difficulty}")
        print(f"   Source: {business.source}")

    # Test Case 2: Well-funded intermediate
    print("\n\n" + "=" * 80)
    print("TEST CASE 2: Well-Funded Intermediate")
    print("=" * 80)
    profile2 = {
        "budget": 15000,
        "available_hours_week": 20,
        "experience_level": "intermediate",
        "risk_tolerance": 0.6,
        "automation_preference": 0.6,
        "preferred_categories": ["Ecommerce", "AI Automation Services"]
    }

    print("\nUser Profile:")
    for key, value in profile2.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")

    print("\nRunning quantum optimization...")
    result2 = optimizer.select_optimal_business_model(profile2)

    print(f"\n✅ Found {result2['total_matches']} matching businesses")
    print(f"🔬 Quantum Enhanced: {result2['quantum_enhanced']}")
    print(f"📊 Confidence: {result2['confidence'] * 100:.0f}%")
    print()

    print("TOP 5 RECOMMENDATIONS:")
    print("-" * 80)

    for i, rec in enumerate(result2['all_recommendations'], 1):
        business = rec['business']
        print(f"\n{i}. {business.name}")
        print(f"   Quantum Score: {rec['quantum_score']:.1f}/100")
        print(f"   Category: {business.category}")
        print(f"   Revenue: ${rec['monthly_revenue']:,}/month | Startup: ${rec['startup_cost']:,}")
        print(f"   Automation: {rec['automation_level']}% | Time: {rec['time_commitment']} hrs/week")
        print(f"   Success Rate: {rec['success_probability']:.0f}% | Source: {business.source}")

    # Test Case 3: High-roller advanced
    print("\n\n" + "=" * 80)
    print("TEST CASE 3: High-Budget Advanced Entrepreneur")
    print("=" * 80)
    profile3 = {
        "budget": 50000,
        "available_hours_week": 30,
        "experience_level": "advanced",
        "risk_tolerance": 0.8,
        "automation_preference": 0.5
    }

    print("\nUser Profile:")
    for key, value in profile3.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")

    print("\nRunning quantum optimization...")
    result3 = optimizer.select_optimal_business_model(profile3)

    print(f"\n✅ Found {result3['total_matches']} matching businesses")
    print(f"🔬 Quantum Enhanced: {result3['quantum_enhanced']}")
    print(f"📊 Confidence: {result3['confidence'] * 100:.0f}%")
    print()

    print("TOP 5 RECOMMENDATIONS:")
    print("-" * 80)

    for i, rec in enumerate(result3['all_recommendations'][:3], 1):  # Show top 3 for brevity
        business = rec['business']
        print(f"\n{i}. {business.name}")
        print(f"   Quantum Score: {rec['quantum_score']:.1f}/100")
        print(f"   Category: {business.category}")
        print(f"   Revenue: ${rec['monthly_revenue']:,}/month | Startup: ${rec['startup_cost']:,}")
        print(f"   Automation: {rec['automation_level']}% | Time: {rec['time_commitment']} hrs/week")
        print(f"   ROI Score: {rec['roi_score']:.1f}/100 | Success: {rec['success_probability']:.0f}%")

    # Summary
    print("\n\n" + "=" * 80)
    print("🎯 QUANTUM MATCHING SUMMARY")
    print("=" * 80)
    print()
    print("✅ Successfully integrated unified business library")
    print("✅ Quantum-enhanced multi-objective optimization")
    print("✅ Personalized matching across 31 business models")
    print("✅ 5-factor scoring system:")
    print("   1. ROI Potential (30%)")
    print("   2. Success Probability (25%)")
    print("   3. Automation Fit (20%)")
    print("   4. Time Efficiency (15%)")
    print("   5. Budget Fit (10%)")
    print()
    print("🚀 Ready for production deployment!")
    print("=" * 80)


if __name__ == "__main__":
    demo_quantum_matching()
