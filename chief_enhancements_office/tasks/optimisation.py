"""
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Optimisation task with performance profiling and actionable recommendations.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import EnhancementTask

if TYPE_CHECKING:
    from ..meta_agent import EnhancementContext


class PerformanceAnalyzer:
    """Analyzes code for performance issues and optimization opportunities."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def analyze_python_performance(self) -> dict[str, Any]:
        """Analyze Python code for performance anti-patterns."""
        issues = []
        opportunities = []

        for py_file in self.project_root.rglob('*.py'):
            if '.venv' in str(py_file) or 'venv' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()

                tree = ast.parse(source, filename=str(py_file))
                relative_path = str(py_file.relative_to(self.project_root))

                # Check for common performance issues
                for node in ast.walk(tree):
                    # Detect nested loops (O(n^2) or worse)
                    if isinstance(node, (ast.For, ast.While)):
                        nested_loops = sum(
                            1 for child in ast.walk(node)
                            if isinstance(child, (ast.For, ast.While))
                        )
                        if nested_loops > 2:
                            issues.append({
                                'severity': 'medium',
                                'file': relative_path,
                                'issue': f'Deeply nested loops detected ({nested_loops} levels)',
                                'recommendation': 'Consider algorithmic optimization or vectorization',
                                'line': node.lineno
                            })

                    # Detect list comprehension that could be generator
                    if isinstance(node, ast.ListComp):
                        parent = self._find_parent(tree, node)
                        if parent and isinstance(parent, (ast.For, ast.Call)):
                            opportunities.append({
                                'file': relative_path,
                                'opportunity': 'List comprehension could be generator expression',
                                'benefit': 'Reduced memory usage',
                                'line': node.lineno
                            })

                    # Detect repeated string concatenation
                    if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
                        if isinstance(node.target, ast.Name):
                            opportunities.append({
                                'file': relative_path,
                                'opportunity': 'String concatenation in loop detected',
                                'recommendation': 'Use join() or list accumulation',
                                'benefit': 'O(n) instead of O(n^2)',
                                'line': node.lineno
                            })

                    # Detect inefficient dict/list operations
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute):
                            if node.func.attr == 'keys' and isinstance(node.func.value, ast.Name):
                                # Iterating over .keys() unnecessarily
                                opportunities.append({
                                    'file': relative_path,
                                    'opportunity': 'Unnecessary .keys() call',
                                    'recommendation': 'Iterate directly over dict',
                                    'benefit': 'Cleaner code, slight performance gain',
                                    'line': node.lineno
                                })

            except Exception:
                pass

        return {
            'performance_issues': issues,
            'optimization_opportunities': opportunities,
            'total_issues': len(issues),
            'total_opportunities': len(opportunities)
        }

    def _find_parent(self, tree: ast.AST, target: ast.AST) -> ast.AST | None:
        """Find parent node of target in AST."""
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child == target:
                    return node
        return None


class CodeQualityAnalyzer:
    """Analyzes code quality and suggests improvements."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def analyze_code_quality(self) -> dict[str, Any]:
        """Analyze code for quality issues."""
        suggestions = []

        for py_file in self.project_root.rglob('*.py'):
            if '.venv' in str(py_file) or 'venv' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()

                tree = ast.parse(source, filename=str(py_file))
                relative_path = str(py_file.relative_to(self.project_root))

                # Check for long functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                        if func_lines > 50:
                            suggestions.append({
                                'category': 'maintainability',
                                'file': relative_path,
                                'function': node.name,
                                'issue': f'Function is {func_lines} lines long',
                                'recommendation': 'Consider breaking into smaller functions',
                                'priority': 'medium'
                            })

                        # Check for too many parameters
                        param_count = len(node.args.args) + len(node.args.kwonlyargs)
                        if param_count > 5:
                            suggestions.append({
                                'category': 'maintainability',
                                'file': relative_path,
                                'function': node.name,
                                'issue': f'Function has {param_count} parameters',
                                'recommendation': 'Consider using dataclass or config object',
                                'priority': 'low'
                            })

                        # Check for missing docstring
                        if not ast.get_docstring(node) and not node.name.startswith('_'):
                            suggestions.append({
                                'category': 'documentation',
                                'file': relative_path,
                                'function': node.name,
                                'issue': 'Missing docstring',
                                'recommendation': 'Add docstring describing purpose and parameters',
                                'priority': 'low'
                            })

                    # Check for large classes
                    if isinstance(node, ast.ClassDef):
                        methods = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                        if len(methods) > 20:
                            suggestions.append({
                                'category': 'design',
                                'file': relative_path,
                                'class': node.name,
                                'issue': f'Class has {len(methods)} methods',
                                'recommendation': 'Consider splitting into multiple classes',
                                'priority': 'high'
                            })

            except Exception:
                pass

        return {
            'suggestions': suggestions,
            'by_category': {
                'maintainability': len([s for s in suggestions if s['category'] == 'maintainability']),
                'documentation': len([s for s in suggestions if s['category'] == 'documentation']),
                'design': len([s for s in suggestions if s['category'] == 'design']),
            },
            'by_priority': {
                'high': len([s for s in suggestions if s['priority'] == 'high']),
                'medium': len([s for s in suggestions if s['priority'] == 'medium']),
                'low': len([s for s in suggestions if s['priority'] == 'low']),
            },
            'total_suggestions': len(suggestions)
        }


class ResourceOptimizer:
    """Identifies resource usage optimization opportunities."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def analyze_resource_usage(self) -> dict[str, Any]:
        """Analyze resource usage patterns."""
        optimizations = []

        # Check for large dependencies
        req_file = self.project_root / 'requirements.txt'
        if req_file.exists():
            heavy_packages = {
                'tensorflow': 'Consider tensorflow-cpu if GPU not needed',
                'torch': 'Consider CPU-only version if GPU not required',
                'pandas': 'Consider polars for better performance',
                'opencv-python': 'Use opencv-python-headless if GUI not needed',
            }

            with open(req_file, 'r', encoding='utf-8') as f:
                for line in f:
                    pkg = line.strip().split('>=')[0].split('==')[0].split('[')[0].lower()
                    if pkg in heavy_packages:
                        optimizations.append({
                            'type': 'dependency',
                            'package': pkg,
                            'recommendation': heavy_packages[pkg],
                            'benefit': 'Reduced installation size and memory footprint'
                        })

        # Check package.json for optimization opportunities
        pkg_file = self.project_root / 'package.json'
        if pkg_file.exists():
            try:
                with open(pkg_file, 'r', encoding='utf-8') as f:
                    pkg_data = json.load(f)

                # Check for development dependencies in production
                dev_deps = pkg_data.get('devDependencies', {})
                if dev_deps:
                    optimizations.append({
                        'type': 'build',
                        'recommendation': 'Ensure devDependencies not included in production build',
                        'benefit': 'Smaller bundle size'
                    })

                # Check for bundling configuration
                if 'webpack' not in pkg_data.get('dependencies', {}) and \
                   'webpack' not in dev_deps and \
                   len(pkg_data.get('dependencies', {})) > 5:
                    optimizations.append({
                        'type': 'build',
                        'recommendation': 'Consider adding bundler (webpack/rollup/vite)',
                        'benefit': 'Optimized bundle size and load times'
                    })

            except Exception:
                pass

        # Check for Docker optimization opportunities
        dockerfile = self.project_root / 'Dockerfile'
        if dockerfile.exists():
            with open(dockerfile, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'alpine' not in content.lower():
                optimizations.append({
                    'type': 'container',
                    'recommendation': 'Consider using Alpine-based images',
                    'benefit': 'Significantly smaller image size'
                })

            if 'multi-stage' not in content.lower() and 'FROM' in content:
                optimizations.append({
                    'type': 'container',
                    'recommendation': 'Use multi-stage builds',
                    'benefit': 'Smaller final image, better layer caching'
                })

        return {
            'optimizations': optimizations,
            'total_opportunities': len(optimizations)
        }


class OptimisationTask(EnhancementTask):
    """Comprehensive optimization analysis with actionable recommendations."""

    name = "optimisation"

    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir

    def execute(self, ctx: "EnhancementContext", *, options: dict[str, Any]) -> None:
        ctx.log("Starting optimization analysis")

        project_root = Path(options.get('project_root', '.'))
        if not project_root.exists():
            ctx.log(f"Project root {project_root} does not exist")
            return

        # Performance analysis
        ctx.log("Analyzing performance patterns")
        perf_analyzer = PerformanceAnalyzer(project_root)
        perf_results = perf_analyzer.analyze_python_performance()
        ctx.telemetry['performance_analysis'] = perf_results

        if perf_results['total_issues'] > 0:
            ctx.log(f"Found {perf_results['total_issues']} performance issues")

        if perf_results['total_opportunities'] > 0:
            ctx.log(f"Identified {perf_results['total_opportunities']} optimization opportunities")

        # Code quality analysis
        ctx.log("Analyzing code quality")
        quality_analyzer = CodeQualityAnalyzer(project_root)
        quality_results = quality_analyzer.analyze_code_quality()
        ctx.telemetry['code_quality'] = quality_results

        if quality_results['total_suggestions'] > 0:
            ctx.log(f"Generated {quality_results['total_suggestions']} code quality suggestions")

        # Resource optimization
        ctx.log("Analyzing resource usage")
        resource_optimizer = ResourceOptimizer(project_root)
        resource_results = resource_optimizer.analyze_resource_usage()
        ctx.telemetry['resource_optimization'] = resource_results

        if resource_results['total_opportunities'] > 0:
            ctx.log(f"Found {resource_results['total_opportunities']} resource optimization opportunities")

        # Generate optimization report
        report = self._generate_optimization_report(
            ctx.product,
            perf_results,
            quality_results,
            resource_results
        )

        report_path = self.knowledge_dir / f"{ctx.product.replace(' ', '_').lower()}_optimization_report.md"
        report_path.write_text(report, encoding='utf-8')
        ctx.improvements.append(str(report_path))

        ctx.log(f"Optimization report saved to {report_path}")

    def _generate_optimization_report(
        self,
        product: str,
        perf_results: dict[str, Any],
        quality_results: dict[str, Any],
        resource_results: dict[str, Any]
    ) -> str:
        """Generate comprehensive optimization report."""
        report = f"# Optimization Report: {product}\n\n"
        report += "## Executive Summary\n\n"

        total_items = (
            perf_results['total_issues'] +
            perf_results['total_opportunities'] +
            quality_results['total_suggestions'] +
            resource_results['total_opportunities']
        )

        report += f"Total optimization items identified: **{total_items}**\n\n"

        # Performance section
        report += "## Performance Optimization\n\n"
        report += f"- **Issues Found**: {perf_results['total_issues']}\n"
        report += f"- **Opportunities**: {perf_results['total_opportunities']}\n\n"

        if perf_results['performance_issues']:
            report += "### High-Priority Performance Issues\n\n"
            for issue in perf_results['performance_issues'][:10]:
                report += f"- **{issue['file']}:{issue.get('line', '?')}**\n"
                report += f"  - Issue: {issue['issue']}\n"
                report += f"  - Recommendation: {issue['recommendation']}\n\n"

        if perf_results['optimization_opportunities']:
            report += "### Quick Wins\n\n"
            for opp in perf_results['optimization_opportunities'][:10]:
                report += f"- **{opp['file']}:{opp.get('line', '?')}**\n"
                report += f"  - {opp['opportunity']}\n"
                report += f"  - Benefit: {opp.get('benefit', 'Performance improvement')}\n\n"

        # Code quality section
        report += "## Code Quality Improvements\n\n"
        report += f"- **Total Suggestions**: {quality_results['total_suggestions']}\n"
        report += f"- **High Priority**: {quality_results['by_priority']['high']}\n"
        report += f"- **Medium Priority**: {quality_results['by_priority']['medium']}\n"
        report += f"- **Low Priority**: {quality_results['by_priority']['low']}\n\n"

        high_priority = [s for s in quality_results['suggestions'] if s['priority'] == 'high']
        if high_priority:
            report += "### High-Priority Quality Issues\n\n"
            for sug in high_priority[:10]:
                report += f"- **{sug['file']}**\n"
                report += f"  - Issue: {sug['issue']}\n"
                report += f"  - Recommendation: {sug['recommendation']}\n\n"

        # Resource optimization section
        report += "## Resource Optimization\n\n"
        report += f"- **Opportunities**: {resource_results['total_opportunities']}\n\n"

        if resource_results['optimizations']:
            report += "### Recommended Optimizations\n\n"
            for opt in resource_results['optimizations']:
                report += f"- **{opt['type'].title()}**: {opt.get('package', opt['recommendation'])}\n"
                report += f"  - {opt.get('recommendation', '')}\n"
                report += f"  - Benefit: {opt.get('benefit', 'Improved efficiency')}\n\n"

        # Implementation checklist
        report += "## Implementation Checklist\n\n"
        report += "### Immediate Actions (Quick Wins)\n\n"

        quick_wins = []
        for opp in perf_results['optimization_opportunities'][:5]:
            quick_wins.append(f"- [ ] {opp['opportunity']} in {opp['file']}")

        for opt in resource_results['optimizations'][:3]:
            quick_wins.append(f"- [ ] {opt['recommendation']}")

        report += '\n'.join(quick_wins) + '\n\n'

        report += "### Medium-Term Improvements\n\n"
        medium_term = []
        for issue in perf_results['performance_issues'][:5]:
            medium_term.append(f"- [ ] {issue['recommendation']} in {issue['file']}")

        for sug in [s for s in quality_results['suggestions'] if s['priority'] == 'high'][:5]:
            medium_term.append(f"- [ ] {sug['recommendation']} in {sug['file']}")

        report += '\n'.join(medium_term) + '\n\n'

        report += "### Long-Term Refactoring\n\n"
        long_term = [
            "- [ ] Comprehensive performance profiling with real workload",
            "- [ ] Automated code quality checks in CI/CD pipeline",
            "- [ ] Regular dependency audits and updates",
            "- [ ] Establish performance budgets and monitoring"
        ]
        report += '\n'.join(long_term) + '\n\n'

        report += "---\n\n"
        report += "*Generated by Chief Enhancements Office Meta-Agent*\n"

        return report
