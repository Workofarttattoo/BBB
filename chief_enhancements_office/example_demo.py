#!/usr/bin/env python3
"""
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Demonstration of Chief Enhancements Office meta-agent capabilities.
"""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.chief_enhancements_office.meta_agent import ChiefEnhancementsMetaAgent


def run_demo():
    """Run comprehensive demonstration of Chief Enhancements Office."""
    print("=" * 80)
    print("Chief Enhancements Office Meta-Agent - Demonstration")
    print("=" * 80)
    print()

    # Initialize meta-agent
    knowledge_dir = Path("reports/enhancements_demo")
    agent = ChiefEnhancementsMetaAgent(knowledge_dir=knowledge_dir)

    print(f"Knowledge directory: {knowledge_dir}")
    print(f"Pipeline tasks: {[task.name for task in agent.pipeline]}")
    print()

    # Example 1: Audit a Python project
    print("Example 1: Auditing Python Project")
    print("-" * 80)

    project_root = Path(__file__).parent.parent.parent.parent / "aios"
    if project_root.exists():
        print(f"Analyzing project: {project_root}")
        ctx = agent.run(
            product="Ai|oS",
            project_root=str(project_root),
            knowledge_dir=str(knowledge_dir)
        )

        print()
        print("Results:")
        print(f"  - Logs: {len(ctx.logs)} entries")
        print(f"  - Issues found: {len(ctx.telemetry.get('issues', []))}")
        print(f"  - Tickets created: {len(ctx.tickets)}")
        print(f"  - Improvements suggested: {len(ctx.improvements)}")
        print()

        # Display audit summary
        audit_summary = ctx.telemetry.get('audit_summary', {})
        if audit_summary:
            print("Audit Summary:")
            for key, value in audit_summary.items():
                print(f"  - {key}: {value}")
            print()

        # Display optimization summary
        perf_analysis = ctx.telemetry.get('performance_analysis', {})
        if perf_analysis:
            print("Performance Analysis:")
            print(f"  - Performance issues: {perf_analysis.get('total_issues', 0)}")
            print(f"  - Optimization opportunities: {perf_analysis.get('total_opportunities', 0)}")
            print()

        # Display helpdesk summary
        helpdesk = ctx.telemetry.get('helpdesk_analysis', {})
        if helpdesk:
            print("Helpdesk Analysis:")
            print(f"  - Total tickets: {helpdesk.get('total_tickets', 0)}")
            print(f"  - Auto-resolved: {helpdesk.get('auto_resolved', 0)}")
            print(f"  - Escalated: {helpdesk.get('escalated', 0)}")
            print()

        # Display escalation summary
        escalations = ctx.telemetry.get('escalations', {})
        if escalations:
            print("Escalations:")
            print(f"  - Total escalated: {escalations.get('total_escalated', 0)}")
            by_level = escalations.get('by_level', {})
            for level, count in by_level.items():
                if count > 0:
                    print(f"  - {level.title()}: {count}")
            print()

        # Display generated reports
        print("Generated Reports:")
        for improvement in ctx.improvements:
            print(f"  - {improvement}")
        print()

        # Sample some logs
        print("Sample Logs:")
        for log in ctx.logs[:5]:
            print(f"  {log}")
        if len(ctx.logs) > 5:
            print(f"  ... and {len(ctx.logs) - 5} more")
        print()

    else:
        print(f"Project root not found: {project_root}")
        print("Skipping Example 1")
        print()

    # Example 2: Custom project analysis
    print()
    print("Example 2: Custom Project Analysis")
    print("-" * 80)

    custom_project = Path.cwd()
    print(f"Analyzing current directory: {custom_project}")

    ctx2 = agent.run(
        product="Custom Project",
        project_root=str(custom_project),
        knowledge_dir=str(knowledge_dir)
    )

    print()
    print("Analysis complete!")
    print(f"Check {knowledge_dir} for detailed reports")
    print()

    # Example 3: Demonstrate individual components
    print()
    print("Example 3: Component Demonstrations")
    print("-" * 80)

    # Code metrics analyzer
    print("Code Metrics Analysis:")
    from modules.chief_enhancements_office.tasks.audit import CodeMetricsAnalyzer

    if project_root.exists():
        analyzer = CodeMetricsAnalyzer(project_root)
        metrics = analyzer.analyze_project()

        print(f"  Python files analyzed: {len(metrics['python']['files'])}")
        if metrics['python']['totals']:
            print(f"  Total Python LOC: {metrics['python']['totals'].get('lines_of_code', 0)}")
            print(f"  Total functions: {metrics['python']['totals'].get('functions', 0)}")
            print(f"  Total classes: {metrics['python']['totals'].get('classes', 0)}")
        print()

    # Security scanner
    print("Security Scanning:")
    from modules.chief_enhancements_office.tasks.audit import SecurityScanner

    if project_root.exists():
        scanner = SecurityScanner(project_root)
        security_results = scanner.scan_python_security()

        print(f"  Total security issues: {security_results['total_issues']}")
        by_severity = security_results['by_severity']
        for severity, count in by_severity.items():
            if count > 0:
                print(f"    - {severity.title()}: {count}")
        print()

    # Issue classifier
    print("Issue Classification:")
    from modules.chief_enhancements_office.tasks.helpdesk import IssueClassifier

    classifier = IssueClassifier()
    test_issues = [
        "Hard-coded password detected in authentication module",
        "Performance degradation in database queries",
        "Missing documentation for API endpoints",
        "TypeError when calling user.get_profile()",
    ]

    for issue in test_issues:
        classification = classifier.classify(issue)
        print(f"  Issue: {issue[:60]}...")
        print(f"    Category: {classification['category']}")
        print(f"    Severity: {classification['severity']}")
        print(f"    Confidence: {classification['confidence']:.2f}")
        print()

    # Automated troubleshooter
    print("Automated Troubleshooting:")
    from modules.chief_enhancements_office.tasks.helpdesk import AutomatedTroubleshooter

    troubleshooter = AutomatedTroubleshooter()
    test_errors = [
        "ImportError: No module named 'django'",
        "MemoryError: Unable to allocate array",
        "PermissionError: [Errno 13] Permission denied: '/etc/config'",
    ]

    for error in test_errors:
        result = troubleshooter.troubleshoot(error)
        print(f"  Error: {error}")
        if result.get('automated_solution'):
            sol = result['automated_solution']
            print(f"    Solution: {sol['solution']}")
            if sol['commands']:
                print(f"    Commands: {', '.join(sol['commands'])}")
        else:
            print("    Requires human review")
        print()

    print("=" * 80)
    print("Demonstration Complete!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
