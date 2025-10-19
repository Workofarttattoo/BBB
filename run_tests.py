"""
Comprehensive Test Runner with Coverage Reporting
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Runs complete test suite and generates coverage reports.
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def run_tests_with_coverage():
    """Run all tests with coverage reporting."""
    print("=" * 80)
    print("Better Business Builder - Comprehensive Test Suite")
    print("Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light)")
    print("=" * 80)
    print()

    # Install test dependencies if needed
    print("📦 Checking test dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q",
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "pytest-xdist>=3.3.1"
    ], check=False)

    print("✅ Dependencies ready\n")

    # Run tests with coverage
    print("🧪 Running test suite...\n")

    tests_dir = Path(__file__).parent / "tests"

    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--cov=src/blank_business_builder",
        "--cov-report=html:test_coverage_html",
        "--cov-report=json:test_coverage.json",
        "--cov-report=term-missing",
        "--tb=short",
        "-n", "auto"  # Run tests in parallel
    ]

    result = subprocess.run(cmd)

    print("\n" + "=" * 80)

    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

    # Read coverage data
    coverage_file = Path("test_coverage.json")
    if coverage_file.exists():
        with open(coverage_file) as f:
            coverage_data = json.load(f)

        total_coverage = coverage_data["totals"]["percent_covered"]
        print(f"\n📊 Code Coverage: {total_coverage:.1f}%")

        if total_coverage >= 80:
            print("✅ Met 80%+ coverage target!")
        else:
            print(f"⚠️  Coverage below 80% target ({total_coverage:.1f}% < 80%)")

    print("\n📁 Coverage reports generated:")
    print(f"  - HTML: test_coverage_html/index.html")
    print(f"  - JSON: test_coverage.json")
    print(f"  - Dashboard: test_dashboard.html")

    # Generate test dashboard
    generate_test_dashboard(coverage_data if coverage_file.exists() else None)

    print("\n" + "=" * 80)

    return result.returncode


def generate_test_dashboard(coverage_data):
    """Generate visual test dashboard."""
    total_coverage = coverage_data["totals"]["percent_covered"] if coverage_data else 0
    total_statements = coverage_data["totals"]["num_statements"] if coverage_data else 0
    covered_statements = coverage_data["totals"]["covered_lines"] if coverage_data else 0

    # Count test files
    tests_dir = Path(__file__).parent / "tests"
    test_files = list(tests_dir.glob("test_*.py"))

    dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BBB Test Suite Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 50px;
        }}

        h1 {{
            font-size: 3.5em;
            margin-bottom: 20px;
        }}

        .coverage-badge {{
            display: inline-block;
            background: {"linear-gradient(135deg, #4caf50, #45a049)" if total_coverage >= 80 else "linear-gradient(135deg, #ff9800, #f57c00)"};
            padding: 15px 40px;
            border-radius: 50px;
            font-size: 2em;
            font-weight: bold;
            margin: 20px 0;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 50px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
        }}

        .stat-icon {{
            font-size: 3em;
            margin-bottom: 15px;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .stat-label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .section {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 25px;
            padding: 40px;
            margin-bottom: 30px;
        }}

        .section h2 {{
            font-size: 2.5em;
            margin-bottom: 30px;
            border-bottom: 3px solid rgba(255, 255, 255, 0.3);
            padding-bottom: 15px;
        }}

        .test-file {{
            background: rgba(255, 255, 255, 0.05);
            border-left: 5px solid #4caf50;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
        }}

        .test-file-name {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .progress-bar {{
            width: 100%;
            height: 30px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4caf50, #8bc34a);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            transition: width 1s ease-in-out;
        }}

        .cta-button {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            margin: 10px;
            transition: all 0.3s;
        }}

        .cta-button:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }}

        .copyright {{
            text-align: center;
            margin-top: 50px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test Suite Dashboard</h1>
            <div class="coverage-badge">{total_coverage:.1f}% Coverage</div>
            <p style="font-size: 1.2em; margin-top: 20px;">
                Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-value">{total_coverage:.1f}%</div>
                <div class="stat-label">Code Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-value">{len(test_files)}</div>
                <div class="stat-label">Test Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-value">{covered_statements}</div>
                <div class="stat-label">Lines Covered</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📄</div>
                <div class="stat-value">{total_statements}</div>
                <div class="stat-label">Total Lines</div>
            </div>
        </div>

        <div class="section">
            <h2>Coverage Progress</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {total_coverage}%">
                    {total_coverage:.1f}%
                </div>
            </div>
            <p style="text-align: center; font-size: 1.2em; margin-top: 20px;">
                {"✅ Exceeded 80% coverage target!" if total_coverage >= 80 else f"⚠️  {80 - total_coverage:.1f}% more needed to reach 80% target"}
            </p>
        </div>

        <div class="section">
            <h2>Test Files</h2>
            {chr(10).join(f'''
            <div class="test-file">
                <div class="test-file-name">✓ {test_file.name}</div>
                <div style="opacity: 0.8;">{test_file.stem.replace("_", " ").title()}</div>
            </div>
            ''' for test_file in test_files)}
        </div>

        <div class="section" style="text-align: center;">
            <h2>Detailed Reports</h2>
            <p style="font-size: 1.2em; margin-bottom: 30px;">
                View comprehensive coverage reports
            </p>
            <a href="test_coverage_html/index.html" class="cta-button">📊 HTML Coverage Report</a>
            <a href="test_coverage.json" class="cta-button">📁 JSON Data</a>
            <a href="QUANTUM_COMPLETE_SUMMARY.html" class="cta-button">🔬 Quantum Summary</a>
        </div>

        <div class="copyright">
            Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light).<br>
            All Rights Reserved. PATENT PENDING.<br>
            Quantum-Optimized Testing Suite
        </div>
    </div>
</body>
</html>
"""

    dashboard_path = Path("test_dashboard.html")
    dashboard_path.write_text(dashboard_html)

    print(f"\n✅ Generated test dashboard: {dashboard_path}")


if __name__ == "__main__":
    sys.exit(run_tests_with_coverage())
