"""
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Helpdesk task with intelligent issue tracking and automated troubleshooting.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import EnhancementTask

if TYPE_CHECKING:
    from ..meta_agent import EnhancementContext


class IssueClassifier:
    """Classifies issues by category and severity."""

    CATEGORIES = {
        'security': {
            'keywords': ['vulnerability', 'security', 'exploit', 'injection', 'xss', 'csrf', 'auth'],
            'severity': 'critical'
        },
        'performance': {
            'keywords': ['slow', 'timeout', 'lag', 'memory', 'cpu', 'performance', 'bottleneck'],
            'severity': 'high'
        },
        'bug': {
            'keywords': ['error', 'exception', 'crash', 'fail', 'broken', 'bug', 'wrong'],
            'severity': 'high'
        },
        'compatibility': {
            'keywords': ['incompatible', 'version', 'deprecated', 'breaking change', 'upgrade'],
            'severity': 'medium'
        },
        'usability': {
            'keywords': ['confusing', 'unclear', 'hard to use', 'ux', 'ui', 'interface'],
            'severity': 'medium'
        },
        'documentation': {
            'keywords': ['documentation', 'docs', 'readme', 'guide', 'tutorial', 'example'],
            'severity': 'low'
        },
        'feature_request': {
            'keywords': ['feature', 'enhancement', 'improvement', 'would be nice', 'please add'],
            'severity': 'low'
        }
    }

    def classify(self, issue_text: str) -> dict[str, Any]:
        """Classify an issue by analyzing its text."""
        issue_lower = issue_text.lower()

        # Find matching categories
        matches = []
        for category, info in self.CATEGORIES.items():
            for keyword in info['keywords']:
                if keyword in issue_lower:
                    matches.append({
                        'category': category,
                        'severity': info['severity'],
                        'confidence': issue_lower.count(keyword) / len(issue_lower.split())
                    })
                    break

        if not matches:
            return {
                'category': 'unknown',
                'severity': 'medium',
                'confidence': 0.0
            }

        # Return highest confidence match
        return max(matches, key=lambda m: m['confidence'])


class IssuePrioritizer:
    """Assigns priority scores to issues."""

    SEVERITY_WEIGHTS = {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25
    }

    def prioritize(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Calculate priority scores for issues."""
        for issue in issues:
            severity = issue.get('severity', 'medium')
            category = issue.get('category', 'unknown')

            # Base score from severity
            score = self.SEVERITY_WEIGHTS.get(severity, 50)

            # Boost security and performance issues
            if category == 'security':
                score += 50
            elif category == 'performance':
                score += 25

            # Boost based on affected users (if available)
            affected_users = issue.get('affected_users', 1)
            score += min(affected_users, 50)

            issue['priority_score'] = score

        # Sort by priority score
        return sorted(issues, key=lambda i: i['priority_score'], reverse=True)


class AutomatedTroubleshooter:
    """Provides automated troubleshooting suggestions."""

    SOLUTIONS = {
        'import_error': {
            'pattern': r'(ImportError|ModuleNotFoundError): No module named',
            'solution': 'Install missing dependency with pip install <package>',
            'commands': ['pip install <package>']
        },
        'permission_error': {
            'pattern': r'PermissionError|Permission denied',
            'solution': 'Check file permissions or run with appropriate privileges',
            'commands': ['chmod +x <file>', 'sudo <command>']
        },
        'syntax_error': {
            'pattern': r'SyntaxError',
            'solution': 'Fix syntax error in code at specified line',
            'commands': []
        },
        'connection_error': {
            'pattern': r'(ConnectionError|Connection refused|Timeout)',
            'solution': 'Check network connectivity and service availability',
            'commands': ['ping <host>', 'telnet <host> <port>', 'curl <url>']
        },
        'file_not_found': {
            'pattern': r'FileNotFoundError|No such file or directory',
            'solution': 'Verify file path exists or create required file/directory',
            'commands': ['ls -la <path>', 'mkdir -p <directory>']
        },
        'memory_error': {
            'pattern': r'MemoryError|Out of memory',
            'solution': 'Increase available memory or optimize memory usage',
            'commands': ['free -h', 'top', 'ps aux --sort=-rss']
        },
        'type_error': {
            'pattern': r'TypeError',
            'solution': 'Fix type mismatch in code - check argument types',
            'commands': []
        },
        'attribute_error': {
            'pattern': r'AttributeError',
            'solution': 'Object does not have requested attribute - check API docs',
            'commands': []
        },
        'key_error': {
            'pattern': r'KeyError',
            'solution': 'Dictionary key not found - use .get() or check key exists',
            'commands': []
        },
        'value_error': {
            'pattern': r'ValueError',
            'solution': 'Invalid value provided to function - check input validation',
            'commands': []
        }
    }

    def troubleshoot(self, issue_text: str) -> dict[str, Any]:
        """Provide automated troubleshooting suggestions."""
        suggestions = []

        for error_type, info in self.SOLUTIONS.items():
            if re.search(info['pattern'], issue_text, re.IGNORECASE):
                suggestions.append({
                    'error_type': error_type,
                    'solution': info['solution'],
                    'commands': info['commands']
                })

        if not suggestions:
            return {
                'automated_solution': None,
                'requires_human_review': True
            }

        return {
            'automated_solution': suggestions[0],
            'alternative_solutions': suggestions[1:] if len(suggestions) > 1 else [],
            'requires_human_review': False
        }


class KnowledgeBaseBuilder:
    """Builds knowledge base from recurring issues."""

    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
        self.kb_file = knowledge_dir / 'helpdesk_knowledge_base.json'

    def extract_patterns(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common patterns from issues."""
        # Group similar issues
        issue_groups = defaultdict(list)

        for issue in issues:
            # Create fingerprint based on category and key terms
            fingerprint = self._create_fingerprint(issue.get('description', ''))
            issue_groups[fingerprint].append(issue)

        # Identify recurring patterns
        patterns = []
        for fingerprint, group in issue_groups.items():
            if len(group) >= 2:  # Recurring if appears 2+ times
                patterns.append({
                    'pattern_id': fingerprint,
                    'occurrences': len(group),
                    'category': group[0].get('category', 'unknown'),
                    'sample_description': group[0].get('description', ''),
                    'automated_solution': group[0].get('automated_solution')
                })

        return {
            'total_patterns': len(patterns),
            'patterns': sorted(patterns, key=lambda p: p['occurrences'], reverse=True)
        }

    def _create_fingerprint(self, text: str) -> str:
        """Create fingerprint for issue clustering."""
        # Extract key terms (ignore common words)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = [w.lower() for w in re.findall(r'\w+', text) if w.lower() not in stopwords]

        # Sort and create hash
        key_terms = sorted(set(words))[:10]  # Top 10 unique terms
        fingerprint = hashlib.md5(' '.join(key_terms).encode()).hexdigest()[:12]
        return fingerprint


class TicketRouter:
    """Routes tickets to appropriate handlers."""

    def route(self, issue: dict[str, Any]) -> str:
        """Determine routing destination for issue."""
        category = issue.get('category', 'unknown')
        severity = issue.get('severity', 'medium')
        automated_solution = issue.get('automated_solution')

        if automated_solution and automated_solution.get('automated_solution'):
            return 'auto_resolved'
        elif category == 'security' or severity == 'critical':
            return 'escalate_immediate'
        elif severity == 'high':
            return 'escalate_priority'
        elif category in ['documentation', 'feature_request']:
            return 'backlog'
        else:
            return 'triage_queue'


class HelpdeskTask(EnhancementTask):
    """Intelligent helpdesk with automated issue tracking and troubleshooting."""

    name = "helpdesk"

    def execute(self, ctx: "EnhancementContext", *, options: dict[str, Any]) -> None:
        ctx.log("Starting helpdesk operations")

        # Extract issues from telemetry
        raw_issues = ctx.telemetry.get('issues', [])

        if not raw_issues:
            ctx.log("No issues found in telemetry")
            ctx.tickets.append("No active issues - system operating normally")
            return

        ctx.log(f"Processing {len(raw_issues)} issues")

        # Initialize components
        classifier = IssueClassifier()
        prioritizer = IssuePrioritizer()
        troubleshooter = AutomatedTroubleshooter()
        kb_builder = KnowledgeBaseBuilder(Path(options.get('knowledge_dir', 'reports/enhancements')))
        router = TicketRouter()

        # Process each issue
        processed_issues = []
        for idx, issue in enumerate(raw_issues, 1):
            # Classify issue
            description = issue.get('issue', '') or issue.get('description', '')
            classification = classifier.classify(description)

            # Get troubleshooting suggestions
            troubleshooting = troubleshooter.troubleshoot(description)

            # Build ticket
            ticket = {
                'ticket_id': f"TICKET-{idx:04d}",
                'description': description,
                'category': classification['category'],
                'severity': classification['severity'],
                'confidence': classification['confidence'],
                'automated_solution': troubleshooting.get('automated_solution'),
                'requires_human_review': troubleshooting.get('requires_human_review', True),
                'affected_users': issue.get('affected_users', 1),
                'source': issue
            }

            # Route ticket
            routing = router.route(ticket)
            ticket['routing'] = routing

            processed_issues.append(ticket)

            # Log ticket creation
            if routing == 'auto_resolved':
                solution = ticket['automated_solution']
                ctx.tickets.append(
                    f"{ticket['ticket_id']} - AUTO-RESOLVED: {description[:60]}... "
                    f"Solution: {solution['solution']}"
                )
                ctx.log(f"Auto-resolved {ticket['ticket_id']}")
            elif routing == 'escalate_immediate':
                ctx.tickets.append(
                    f"{ticket['ticket_id']} - ESCALATED (CRITICAL): {description[:60]}..."
                )
                ctx.log(f"Escalated {ticket['ticket_id']} - critical priority")
            else:
                ctx.tickets.append(
                    f"{ticket['ticket_id']} - {routing.upper()}: {description[:60]}..."
                )

        # Prioritize remaining issues
        processed_issues = prioritizer.prioritize(processed_issues)

        # Build knowledge base
        kb_patterns = kb_builder.extract_patterns(processed_issues)

        # Store results in telemetry
        ctx.telemetry['helpdesk_analysis'] = {
            'total_tickets': len(processed_issues),
            'auto_resolved': len([t for t in processed_issues if t['routing'] == 'auto_resolved']),
            'escalated': len([t for t in processed_issues if 'escalate' in t['routing']]),
            'by_category': {},
            'by_severity': {},
            'kb_patterns': kb_patterns
        }

        # Count by category and severity
        for ticket in processed_issues:
            category = ticket['category']
            severity = ticket['severity']
            ctx.telemetry['helpdesk_analysis']['by_category'][category] = \
                ctx.telemetry['helpdesk_analysis']['by_category'].get(category, 0) + 1
            ctx.telemetry['helpdesk_analysis']['by_severity'][severity] = \
                ctx.telemetry['helpdesk_analysis']['by_severity'].get(severity, 0) + 1

        # Generate helpdesk report
        report = self._generate_helpdesk_report(processed_issues, kb_patterns)
        report_path = Path(options.get('knowledge_dir', 'reports/enhancements')) / \
                     f"{ctx.product.replace(' ', '_').lower()}_helpdesk_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding='utf-8')
        ctx.improvements.append(str(report_path))

        ctx.log(f"Helpdesk report saved to {report_path}")
        ctx.log(
            f"Summary: {len(processed_issues)} tickets, "
            f"{ctx.telemetry['helpdesk_analysis']['auto_resolved']} auto-resolved, "
            f"{ctx.telemetry['helpdesk_analysis']['escalated']} escalated"
        )

    def _generate_helpdesk_report(
        self,
        tickets: list[dict[str, Any]],
        kb_patterns: dict[str, Any]
    ) -> str:
        """Generate comprehensive helpdesk report."""
        report = "# Helpdesk Analysis Report\n\n"

        # Summary
        report += "## Summary\n\n"
        report += f"- **Total Tickets**: {len(tickets)}\n"
        report += f"- **Auto-Resolved**: {len([t for t in tickets if t['routing'] == 'auto_resolved'])}\n"
        report += f"- **Escalated**: {len([t for t in tickets if 'escalate' in t['routing']])}\n"
        report += f"- **Recurring Patterns**: {kb_patterns['total_patterns']}\n\n"

        # Critical issues
        critical_tickets = [t for t in tickets if t['severity'] == 'critical']
        if critical_tickets:
            report += "## Critical Issues (Immediate Action Required)\n\n"
            for ticket in critical_tickets:
                report += f"### {ticket['ticket_id']}: {ticket['description'][:80]}...\n\n"
                report += f"- **Category**: {ticket['category']}\n"
                report += f"- **Routing**: {ticket['routing']}\n"
                if ticket['automated_solution']:
                    sol = ticket['automated_solution']
                    report += f"- **Suggested Solution**: {sol['solution']}\n"
                    if sol.get('commands'):
                        report += f"- **Commands**: `{', '.join(sol['commands'])}`\n"
                report += "\n"

        # High priority issues
        high_tickets = [t for t in tickets if t['severity'] == 'high'][:10]
        if high_tickets:
            report += "## High Priority Issues\n\n"
            for ticket in high_tickets:
                report += f"- **{ticket['ticket_id']}** ({ticket['category']}): {ticket['description'][:80]}...\n"
                if ticket['automated_solution']:
                    report += f"  - Solution: {ticket['automated_solution']['solution']}\n"

        report += "\n"

        # Recurring patterns
        if kb_patterns['patterns']:
            report += "## Recurring Patterns (Knowledge Base)\n\n"
            for pattern in kb_patterns['patterns'][:5]:
                report += f"### Pattern: {pattern['category'].title()}\n\n"
                report += f"- **Occurrences**: {pattern['occurrences']}\n"
                report += f"- **Sample**: {pattern['sample_description'][:100]}...\n"
                if pattern.get('automated_solution'):
                    report += f"- **Standard Solution**: {pattern['automated_solution']['solution']}\n"
                report += "\n"

        # Category breakdown
        report += "## Issues by Category\n\n"
        category_counts = {}
        for ticket in tickets:
            category = ticket['category']
            category_counts[category] = category_counts.get(category, 0) + 1

        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{category.title()}**: {count}\n"

        report += "\n"

        # Action items
        report += "## Action Items\n\n"
        report += "### Immediate (Next 24 Hours)\n\n"
        for ticket in tickets[:5]:
            if 'escalate' in ticket['routing']:
                report += f"- [ ] Resolve {ticket['ticket_id']}: {ticket['description'][:60]}...\n"

        report += "\n### This Week\n\n"
        medium_tickets = [t for t in tickets if t['severity'] == 'medium'][:5]
        for ticket in medium_tickets:
            report += f"- [ ] Address {ticket['ticket_id']}: {ticket['description'][:60]}...\n"

        report += "\n### Backlog\n\n"
        low_tickets = [t for t in tickets if t['severity'] == 'low'][:5]
        for ticket in low_tickets:
            report += f"- [ ] Review {ticket['ticket_id']}: {ticket['description'][:60]}...\n"

        report += "\n---\n\n"
        report += "*Generated by Chief Enhancements Office Helpdesk*\n"

        return report
