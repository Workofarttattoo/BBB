#!/bin/bash
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
#
# ECH0 Prime + BBB Validation Runner
# Runs full test suite with parliament review

set -e

echo "================================================================================"
echo "🏛️  ECH0 PRIME + BBB VALIDATION SUITE"
echo "================================================================================"
echo ""
echo "Running comprehensive validation with:"
echo "  ✅ Truth Verification Engine"
echo "  ✅ Hallucination Detection"
echo "  ✅ Pseudo-Science Checks"
echo "  ✅ Parliament Review"
echo "  ✅ Market Reality Validation"
echo ""
echo "================================================================================"
echo ""

# Run tests with pytest
echo "🧪 Running test suite..."
echo ""

python3 -m pytest tests/test_ech0_prime_bbb.py -v --tb=short -s

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo "✅ ALL TESTS PASSED"
    echo "================================================================================"
    echo ""
    echo "All BBB business models have been validated:"
    echo "  • No hallucinations detected"
    echo "  • No pseudo-science found"
    echo "  • All revenue/cost projections realistic"
    echo "  • All algorithms verified as real"
    echo "  • Parliament approval granted"
    echo ""
    echo "📄 Detailed report: bbb_parliament_validation_report.json"
    echo ""
    echo "================================================================================"
else
    echo ""
    echo "================================================================================"
    echo "❌ VALIDATION FAILED"
    echo "================================================================================"
    echo ""
    echo "Some business models failed validation. Review the output above for:"
    echo "  🚩 Red flags (unrealistic claims)"
    echo "  🚩 Hallucination patterns"
    echo "  🚩 Pseudo-science terms"
    echo "  🚩 Fake algorithms"
    echo ""
    echo "Fix these issues before proceeding."
    echo ""
    echo "================================================================================"
    exit 1
fi
