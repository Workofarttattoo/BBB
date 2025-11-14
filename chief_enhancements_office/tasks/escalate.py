"""
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Escalation task with intelligent priority scoring and external research triggers.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import EnhancementTask

if TYPE_CHECKING:
    from ..meta_agent import EnhancementContext


class EscalationCriteria:
    """Evaluates when issues should be escalated."""

    @staticmethod
    def should_escalate(issue: dict[str, Any], telemetry: dict[str, Any]) -> dict[str, Any]:
        """Determine if issue warrants escalation."""
        reasons = []
        severity_score = 0

        # Check severity
        severity = issue.get('severity', 'medium')
        if severity == 'critical':
            reasons.append('Critical severity level')
            severity_score += 100
        elif severity == 'high':
            reasons.append('High severity level')
            severity_score += 75

        # Check category
        category = issue.get('category', 'unknown')
        if category == 'security':
            reasons.append('Security vulnerability detected')
            severity_score += 50
        elif category == 'performance':
            reasons.append('Performance degradation detected')
            severity_score += 25

        # Check if automated resolution failed
        if issue.get('requires_human_review', False):
            reasons.append('Automated resolution not available')
            severity_score += 20

        # Check complexity indicators
        if issue.get('priority_score', 0) > 100:
            reasons.append('High complexity score')
            severity_score += 15

        # Check if recurring issue
        kb_patterns = telemetry.get('helpdesk_analysis', {}).get('kb_patterns', {})
        if kb_patterns.get('total_patterns', 0) > 0:
            for pattern in kb_patterns.get('patterns', []):
                if pattern.get('occurrences', 0) > 3:
                    reasons.append('Recurring issue pattern detected')
                    severity_score += 30
                    break

        # Escalate if score exceeds threshold
        should_escalate = severity_score >= 75

        return {
            'should_escalate': should_escalate,
            'severity_score': severity_score,
            'reasons': reasons,
            'escalation_level': EscalationCriteria._determine_level(severity_score)
        }

    @staticmethod
    def _determine_level(score: int) -> str:
        """Determine escalation level based on score."""
        if score >= 150:
            return 'immediate'  # Page on-call
        elif score >= 100:
            return 'urgent'  # Next business day
        elif score >= 75:
            return 'standard'  # This week
        else:
            return 'low'  # Backlog


class ResearchQueryGenerator:
    """Generates targeted research queries for external knowledge search."""

    @staticmethod
    def generate_queries(issue: dict[str, Any], context: dict[str, Any]) -> list[str]:
        """Generate search queries for issue research."""
        queries = []

        description = issue.get('description', '')
        category = issue.get('category', 'unknown')

        # Base query from description
        key_terms = ResearchQueryGenerator._extract_key_terms(description)
        if key_terms:
            queries.append(' '.join(key_terms[:5]))

        # Category-specific queries
        if category == 'security':
            queries.extend([
                f"{' '.join(key_terms[:3])} security vulnerability CVE",
                f"{' '.join(key_terms[:3])} exploit mitigation",
                f"{' '.join(key_terms[:3])} security best practices"
            ])
        elif category == 'performance':
            queries.extend([
                f"{' '.join(key_terms[:3])} performance optimization",
                f"{' '.join(key_terms[:3])} profiling techniques",
                f"{' '.join(key_terms[:3])} benchmark results"
            ])
        elif category == 'bug':
            queries.extend([
                f"{' '.join(key_terms[:3])} error solution",
                f"{' '.join(key_terms[:3])} debugging guide",
                f"{' '.join(key_terms[:3])} troubleshooting steps"
            ])

        # Technology-specific queries
        tech_stack = context.get('technologies', [])
        for tech in tech_stack[:3]:
            queries.append(f"{tech} {' '.join(key_terms[:3])}")

        # Add version-specific queries if applicable
        if 'version' in description.lower():
            queries.append(f"{' '.join(key_terms[:3])} version compatibility")

        return queries[:10]  # Limit to top 10 queries

    @staticmethod
    def _extract_key_terms(text: str) -> list[str]:
        """Extract key technical terms from text."""
        import re

        # Remove common words
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'
        }

        words = re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())
        key_terms = [w for w in words if w not in stopwords and len(w) > 2]

        # Prioritize technical terms (CamelCase, snake_case, etc.)
        technical_terms = [
            w for w in key_terms
            if '_' in w or '-' in w or any(c.isupper() for c in text if text.index(c.lower()) == text.lower().index(w))
        ]

        return technical_terms + [t for t in key_terms if t not in technical_terms]


class ExpertRecommendationEngine:
    """Recommends subject matter experts for escalated issues."""

    EXPERT_DOMAINS = {
        'security': [
            'security engineer',
            'penetration tester',
            'security architect',
            'incident responder'
        ],
        'performance': [
            'performance engineer',
            'systems architect',
            'database administrator',
            'DevOps engineer'
        ],
        'bug': [
            'senior developer',
            'tech lead',
            'QA engineer',
            'release manager'
        ],
        'compatibility': [
            'platform engineer',
            'integration specialist',
            'compatibility tester'
        ],
        'design': [
            'solutions architect',
            'principal engineer',
            'technical architect'
        ]
    }

    @staticmethod
    def recommend_experts(issue: dict[str, Any]) -> list[str]:
        """Recommend experts based on issue category."""
        category = issue.get('category', 'unknown')
        severity = issue.get('severity', 'medium')

        experts = ExpertRecommendationEngine.EXPERT_DOMAINS.get(category, ['senior developer'])

        # For critical issues, always include architect
        if severity == 'critical' and 'solutions architect' not in experts:
            experts.append('solutions architect')

        return experts


class EscalationTask(EnhancementTask):
    """Intelligent escalation with priority scoring and research automation."""

    name = "escalation"

    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir

    def execute(self, ctx: "EnhancementContext", *, options: dict[str, Any]) -> None:
        ctx.log("Evaluating escalation criteria")

        # Get issues from telemetry
        issues = ctx.telemetry.get('issues', [])
        helpdesk_analysis = ctx.telemetry.get('helpdesk_analysis', {})

        if not issues:
            ctx.log("No issues requiring escalation")
            return

        # Evaluate each issue for escalation
        escalations = []
        research_queries = []

        for issue in issues:
            # Determine if escalation needed
            evaluation = EscalationCriteria.should_escalate(issue, ctx.telemetry)

            if evaluation['should_escalate']:
                # Generate research queries
                tech_context = {
                    'technologies': self._extract_technologies(ctx)
                }
                queries = ResearchQueryGenerator.generate_queries(issue, tech_context)

                # Recommend experts
                experts = ExpertRecommendationEngine.recommend_experts(issue)

                escalation = {
                    'issue': issue,
                    'evaluation': evaluation,
                    'research_queries': queries,
                    'recommended_experts': experts,
                    'escalation_timestamp': datetime.utcnow().isoformat()
                }

                escalations.append(escalation)
                research_queries.extend(queries)

                ctx.log(
                    f"Escalating issue ({evaluation['escalation_level']}): "
                    f"{issue.get('description', 'Unknown')[:50]}..."
                )

        if not escalations:
            ctx.log("No issues met escalation criteria")
            return

        # Store escalation data
        ctx.telemetry['escalations'] = {
            'total_escalated': len(escalations),
            'by_level': {
                'immediate': len([e for e in escalations if e['evaluation']['escalation_level'] == 'immediate']),
                'urgent': len([e for e in escalations if e['evaluation']['escalation_level'] == 'urgent']),
                'standard': len([e for e in escalations if e['evaluation']['escalation_level'] == 'standard']),
                'low': len([e for e in escalations if e['evaluation']['escalation_level'] == 'low']),
            },
            'escalations': escalations
        }

        # Generate escalation report
        report = self._generate_escalation_report(ctx.product, escalations)
        report_path = self.knowledge_dir / f"{ctx.product.replace(' ', '_').lower()}_escalations.md"
        report_path.write_text(report, encoding='utf-8')
        ctx.improvements.append(str(report_path))

        # Generate research queries file
        research_log = self.knowledge_dir / f"{ctx.product.replace(' ', '_').lower()}_research.log"
        research_log.write_text('\n'.join(set(research_queries)), encoding='utf-8')
        ctx.improvements.append(str(research_log))

        # Generate machine-readable escalation data
        data_path = self.knowledge_dir / f"{ctx.product.replace(' ', '_').lower()}_escalations.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(escalations, f, indent=2)
        ctx.improvements.append(str(data_path))

        ctx.log(f"Escalated {len(escalations)} issues")
        ctx.log(f"Generated {len(set(research_queries))} research queries")
        ctx.log(f"Reports saved to {self.knowledge_dir}")

    def _extract_technologies(self, ctx: "EnhancementContext") -> list[str]:
        """Extract technology stack from telemetry."""
        technologies = []

        # From dependencies
        python_deps = ctx.telemetry.get('python_dependencies', {}).get('dependencies', [])
        technologies.extend([dep['name'] for dep in python_deps[:10]])

        npm_deps = ctx.telemetry.get('npm_dependencies', {}).get('dependencies', [])
        technologies.extend([dep['name'] for dep in npm_deps[:10]])

        # Common frameworks detection
        if any('django' in t.lower() for t in technologies):
            technologies.append('Django')
        if any('flask' in t.lower() for t in technologies):
            technologies.append('Flask')
        if any('react' in t.lower() for t in technologies):
            technologies.append('React')
        if any('vue' in t.lower() for t in technologies):
            technologies.append('Vue')

        return list(set(technologies))

    def _generate_escalation_report(
        self,
        product: str,
        escalations: list[dict[str, Any]]
    ) -> str:
        """Generate comprehensive escalation report."""
        report = f"# Escalation Report: {product}\n\n"
        report += f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"

        # Summary
        report += "## Summary\n\n"
        report += f"- **Total Escalations**: {len(escalations)}\n"

        level_counts = {}
        for esc in escalations:
            level = esc['evaluation']['escalation_level']
            level_counts[level] = level_counts.get(level, 0) + 1

        for level, count in sorted(level_counts.items(), key=lambda x: ['immediate', 'urgent', 'standard', 'low'].index(x[0])):
            report += f"- **{level.title()}**: {count}\n"

        report += "\n"

        # Immediate escalations
        immediate = [e for e in escalations if e['evaluation']['escalation_level'] == 'immediate']
        if immediate:
            report += "## Immediate Escalations (Page On-Call)\n\n"
            for esc in immediate:
                issue = esc['issue']
                eval_data = esc['evaluation']

                report += f"### {issue.get('description', 'Unknown Issue')[:80]}...\n\n"
                report += f"- **Severity Score**: {eval_data['severity_score']}\n"
                report += f"- **Category**: {issue.get('category', 'unknown')}\n"
                report += f"- **Severity**: {issue.get('severity', 'medium')}\n"
                report += f"- **Escalation Reasons**:\n"
                for reason in eval_data['reasons']:
                    report += f"  - {reason}\n"
                report += f"- **Recommended Experts**: {', '.join(esc['recommended_experts'])}\n"
                report += f"- **Research Queries**:\n"
                for query in esc['research_queries'][:5]:
                    report += f"  - `{query}`\n"
                report += "\n"

        # Urgent escalations
        urgent = [e for e in escalations if e['evaluation']['escalation_level'] == 'urgent']
        if urgent:
            report += "## Urgent Escalations (Next Business Day)\n\n"
            for esc in urgent:
                issue = esc['issue']
                report += f"- **{issue.get('description', 'Unknown')[:80]}...**\n"
                report += f"  - Severity Score: {esc['evaluation']['severity_score']}\n"
                report += f"  - Experts: {', '.join(esc['recommended_experts'])}\n"
                report += "\n"

        # Standard escalations
        standard = [e for e in escalations if e['evaluation']['escalation_level'] == 'standard']
        if standard:
            report += "## Standard Escalations (This Week)\n\n"
            for esc in standard:
                issue = esc['issue']
                report += f"- {issue.get('description', 'Unknown')[:80]}... "
                report += f"(Score: {esc['evaluation']['severity_score']})\n"

        report += "\n"

        # Research plan
        report += "## Research Plan\n\n"
        all_queries = []
        for esc in escalations:
            all_queries.extend(esc['research_queries'])

        unique_queries = list(set(all_queries))[:20]
        report += "### Recommended Research Queries\n\n"
        for idx, query in enumerate(unique_queries, 1):
            report += f"{idx}. `{query}`\n"

        report += "\n"

        # Expert assignments
        report += "## Recommended Expert Assignments\n\n"
        expert_issues = {}
        for esc in escalations:
            for expert in esc['recommended_experts']:
                if expert not in expert_issues:
                    expert_issues[expert] = []
                expert_issues[expert].append(esc['issue'].get('description', 'Unknown')[:50])

        for expert, issues_list in sorted(expert_issues.items()):
            report += f"### {expert.title()}\n\n"
            for issue_desc in issues_list[:5]:
                report += f"- {issue_desc}...\n"
            report += "\n"

        # Action items
        report += "## Action Items\n\n"

        if immediate:
            report += "### Immediate (NOW)\n\n"
            for esc in immediate:
                report += f"- [ ] Page on-call for: {esc['issue'].get('description', 'Unknown')[:60]}...\n"
            report += "\n"

        if urgent:
            report += "### Next Business Day\n\n"
            for esc in urgent:
                report += f"- [ ] Assign to {esc['recommended_experts'][0]}: {esc['issue'].get('description', 'Unknown')[:60]}...\n"
            report += "\n"

        if standard:
            report += "### This Week\n\n"
            for esc in standard:
                report += f"- [ ] Schedule review: {esc['issue'].get('description', 'Unknown')[:60]}...\n"

        report += "\n---\n\n"
        report += "*Generated by Chief Enhancements Office Escalation Engine*\n"

        return report
