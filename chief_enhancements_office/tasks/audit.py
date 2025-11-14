"""
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Software audit task with comprehensive code analysis capabilities.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import EnhancementTask

if TYPE_CHECKING:
    from ..meta_agent import EnhancementContext


class CodeMetricsAnalyzer:
    """Analyzes code complexity and quality metrics."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def analyze_python_file(self, filepath: Path) -> dict[str, Any]:
        """Analyze a single Python file for metrics."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(filepath))

            metrics = {
                'lines_of_code': len(source.splitlines()),
                'blank_lines': sum(1 for line in source.splitlines() if not line.strip()),
                'comment_lines': sum(1 for line in source.splitlines() if line.strip().startswith('#')),
                'functions': 0,
                'classes': 0,
                'complexity': 0,
                'max_function_complexity': 0,
                'imports': 0,
                'docstrings': 0,
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['functions'] += 1
                    complexity = self._calculate_complexity(node)
                    metrics['complexity'] += complexity
                    metrics['max_function_complexity'] = max(
                        metrics['max_function_complexity'], complexity
                    )
                    if ast.get_docstring(node):
                        metrics['docstrings'] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics['classes'] += 1
                    if ast.get_docstring(node):
                        metrics['docstrings'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics['imports'] += 1

            return metrics

        except Exception as e:
            return {'error': str(e)}

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity

    def analyze_javascript_file(self, filepath: Path) -> dict[str, Any]:
        """Analyze a JavaScript/TypeScript file for basic metrics."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()

            metrics = {
                'lines_of_code': len(source.splitlines()),
                'blank_lines': sum(1 for line in source.splitlines() if not line.strip()),
                'comment_lines': sum(
                    1 for line in source.splitlines()
                    if line.strip().startswith('//') or line.strip().startswith('/*')
                ),
                'functions': len(re.findall(r'\bfunction\b|\b=>\b', source)),
                'classes': len(re.findall(r'\bclass\b', source)),
                'imports': len(re.findall(r'\bimport\b|\brequire\b', source)),
            }

            return metrics

        except Exception as e:
            return {'error': str(e)}

    def analyze_project(self) -> dict[str, Any]:
        """Analyze entire project for code metrics."""
        results = {
            'python': {'files': [], 'totals': defaultdict(int)},
            'javascript': {'files': [], 'totals': defaultdict(int)},
            'rust': {'files': [], 'totals': defaultdict(int)},
        }

        # Python files
        for py_file in self.project_root.rglob('*.py'):
            if '.venv' in str(py_file) or 'venv' in str(py_file):
                continue
            metrics = self.analyze_python_file(py_file)
            if 'error' not in metrics:
                results['python']['files'].append({
                    'path': str(py_file.relative_to(self.project_root)),
                    'metrics': metrics
                })
                for key, value in metrics.items():
                    results['python']['totals'][key] += value

        # JavaScript/TypeScript files
        for js_file in self.project_root.rglob('*.js'):
            if 'node_modules' in str(js_file):
                continue
            metrics = self.analyze_javascript_file(js_file)
            if 'error' not in metrics:
                results['javascript']['files'].append({
                    'path': str(js_file.relative_to(self.project_root)),
                    'metrics': metrics
                })
                for key, value in metrics.items():
                    results['javascript']['totals'][key] += value

        for ts_file in self.project_root.rglob('*.ts'):
            if 'node_modules' in str(ts_file):
                continue
            metrics = self.analyze_javascript_file(ts_file)
            if 'error' not in metrics:
                results['javascript']['files'].append({
                    'path': str(ts_file.relative_to(self.project_root)),
                    'metrics': metrics
                })
                for key, value in metrics.items():
                    results['javascript']['totals'][key] += value

        # Rust files (basic line counting)
        for rs_file in self.project_root.rglob('*.rs'):
            if 'target' in str(rs_file):
                continue
            try:
                with open(rs_file, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                results['rust']['files'].append({
                    'path': str(rs_file.relative_to(self.project_root)),
                    'metrics': {'lines_of_code': len(lines)}
                })
                results['rust']['totals']['lines_of_code'] += len(lines)
            except Exception:
                pass

        return dict(results)


class SecurityScanner:
    """Scans code for security vulnerabilities."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan_python_security(self) -> dict[str, Any]:
        """Scan Python code for security issues."""
        issues = []

        # Check for common security anti-patterns
        for py_file in self.project_root.rglob('*.py'):
            if '.venv' in str(py_file) or 'venv' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                relative_path = str(py_file.relative_to(self.project_root))

                # Check for dangerous functions
                if 'eval(' in content:
                    issues.append({
                        'severity': 'high',
                        'file': relative_path,
                        'issue': 'Use of eval() detected - potential code injection',
                        'line': self._find_line_number(content, 'eval(')
                    })

                if 'exec(' in content:
                    issues.append({
                        'severity': 'high',
                        'file': relative_path,
                        'issue': 'Use of exec() detected - potential code injection',
                        'line': self._find_line_number(content, 'exec(')
                    })

                if 'pickle.loads' in content and 'untrusted' in content.lower():
                    issues.append({
                        'severity': 'high',
                        'file': relative_path,
                        'issue': 'Unsafe pickle.loads() usage - potential code execution',
                        'line': self._find_line_number(content, 'pickle.loads')
                    })

                if 'shell=True' in content:
                    issues.append({
                        'severity': 'medium',
                        'file': relative_path,
                        'issue': 'subprocess with shell=True - potential command injection',
                        'line': self._find_line_number(content, 'shell=True')
                    })

                if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
                    issues.append({
                        'severity': 'critical',
                        'file': relative_path,
                        'issue': 'Hard-coded password detected',
                        'line': self._find_line_number(content, 'password')
                    })

                if re.search(r'api[_-]?key\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
                    issues.append({
                        'severity': 'critical',
                        'file': relative_path,
                        'issue': 'Hard-coded API key detected',
                        'line': self._find_line_number(content, 'api')
                    })

            except Exception:
                pass

        return {
            'total_issues': len(issues),
            'by_severity': {
                'critical': len([i for i in issues if i['severity'] == 'critical']),
                'high': len([i for i in issues if i['severity'] == 'high']),
                'medium': len([i for i in issues if i['severity'] == 'medium']),
                'low': len([i for i in issues if i['severity'] == 'low']),
            },
            'issues': issues
        }

    def _find_line_number(self, content: str, pattern: str) -> int:
        """Find line number of pattern in content."""
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 0


class DependencyAuditor:
    """Audits project dependencies for issues."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def audit_python_dependencies(self) -> dict[str, Any]:
        """Audit Python dependencies from requirements.txt or pyproject.toml."""
        results = {
            'dependencies': [],
            'vulnerabilities': [],
            'outdated': [],
        }

        req_file = self.project_root / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package name and version
                        match = re.match(r'^([a-zA-Z0-9_-]+)([><=!~]+.*)?$', line)
                        if match:
                            pkg_name = match.group(1)
                            version_spec = match.group(2) or ''
                            results['dependencies'].append({
                                'name': pkg_name,
                                'version': version_spec,
                                'file': 'requirements.txt'
                            })

        # Check for common vulnerable packages
        vulnerable_packages = {
            'django': '< 3.2',
            'flask': '< 2.0',
            'requests': '< 2.26',
            'urllib3': '< 1.26.5',
        }

        for dep in results['dependencies']:
            pkg = dep['name'].lower()
            if pkg in vulnerable_packages:
                results['vulnerabilities'].append({
                    'package': dep['name'],
                    'current': dep['version'],
                    'recommendation': f'Update to {vulnerable_packages[pkg]}',
                    'severity': 'high'
                })

        return results

    def audit_npm_dependencies(self) -> dict[str, Any]:
        """Audit npm dependencies from package.json."""
        results = {
            'dependencies': [],
            'dev_dependencies': [],
            'vulnerabilities': [],
        }

        pkg_file = self.project_root / 'package.json'
        if pkg_file.exists():
            try:
                with open(pkg_file, 'r', encoding='utf-8') as f:
                    pkg_data = json.load(f)

                for name, version in pkg_data.get('dependencies', {}).items():
                    results['dependencies'].append({
                        'name': name,
                        'version': version,
                        'type': 'production'
                    })

                for name, version in pkg_data.get('devDependencies', {}).items():
                    results['dev_dependencies'].append({
                        'name': name,
                        'version': version,
                        'type': 'development'
                    })

            except Exception as e:
                results['error'] = str(e)

        return results

    def audit_cargo_dependencies(self) -> dict[str, Any]:
        """Audit Rust dependencies from Cargo.toml."""
        results = {
            'dependencies': [],
        }

        cargo_file = self.project_root / 'Cargo.toml'
        if cargo_file.exists():
            try:
                with open(cargo_file, 'r', encoding='utf-8') as f:
                    in_deps = False
                    for line in f:
                        if line.strip() == '[dependencies]':
                            in_deps = True
                            continue
                        elif line.strip().startswith('['):
                            in_deps = False
                            continue

                        if in_deps and '=' in line:
                            parts = line.split('=')
                            name = parts[0].strip()
                            version = parts[1].strip().strip('"')
                            results['dependencies'].append({
                                'name': name,
                                'version': version,
                            })

            except Exception as e:
                results['error'] = str(e)

        return results


class GitAnalyzer:
    """Analyzes Git repository metrics."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def analyze_repository(self) -> dict[str, Any]:
        """Analyze Git repository for metrics."""
        if not (self.project_root / '.git').exists():
            return {'error': 'Not a git repository'}

        results = {}

        try:
            # Get commit count
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            results['total_commits'] = int(result.stdout.strip())

            # Get contributor count
            result = subprocess.run(
                ['git', 'shortlog', '-s', '-n', '--all'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            results['contributors'] = len(result.stdout.strip().splitlines())

            # Get branch count
            result = subprocess.run(
                ['git', 'branch', '-a'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            results['branches'] = len(result.stdout.strip().splitlines())

            # Get recent activity
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            results['recent_commits'] = result.stdout.strip().splitlines()

        except subprocess.CalledProcessError as e:
            results['error'] = f'Git command failed: {e}'
        except Exception as e:
            results['error'] = str(e)

        return results


class SoftwareAuditTask(EnhancementTask):
    """Comprehensive software audit with real analysis capabilities."""

    name = "software-audit"

    def execute(self, ctx: "EnhancementContext", *, options: dict[str, Any]) -> None:
        ctx.log("Starting comprehensive software audit")

        project_root = Path(options.get('project_root', '.'))
        if not project_root.exists():
            ctx.log(f"Project root {project_root} does not exist")
            ctx.telemetry['audit_error'] = f'Project root not found: {project_root}'
            return

        # Code metrics analysis
        ctx.log("Analyzing code metrics")
        metrics_analyzer = CodeMetricsAnalyzer(project_root)
        code_metrics = metrics_analyzer.analyze_project()
        ctx.telemetry['code_metrics'] = code_metrics

        # Security scanning
        ctx.log("Scanning for security vulnerabilities")
        security_scanner = SecurityScanner(project_root)
        security_results = security_scanner.scan_python_security()
        ctx.telemetry['security_scan'] = security_results

        if security_results['total_issues'] > 0:
            ctx.log(f"Found {security_results['total_issues']} security issues")
            for issue in security_results['issues']:
                ctx.telemetry.setdefault("issues", []).append({
                    'type': 'security',
                    'severity': issue['severity'],
                    'file': issue['file'],
                    'issue': issue['issue'],
                    'line': issue.get('line', 0)
                })

        # Dependency audit
        ctx.log("Auditing project dependencies")
        dep_auditor = DependencyAuditor(project_root)

        python_deps = dep_auditor.audit_python_dependencies()
        ctx.telemetry['python_dependencies'] = python_deps

        npm_deps = dep_auditor.audit_npm_dependencies()
        ctx.telemetry['npm_dependencies'] = npm_deps

        cargo_deps = dep_auditor.audit_cargo_dependencies()
        ctx.telemetry['cargo_dependencies'] = cargo_deps

        if python_deps.get('vulnerabilities'):
            ctx.log(f"Found {len(python_deps['vulnerabilities'])} vulnerable Python packages")
            for vuln in python_deps['vulnerabilities']:
                ctx.telemetry.setdefault("issues", []).append({
                    'type': 'dependency_vulnerability',
                    'severity': vuln['severity'],
                    'package': vuln['package'],
                    'recommendation': vuln['recommendation']
                })

        # Git repository analysis
        ctx.log("Analyzing Git repository")
        git_analyzer = GitAnalyzer(project_root)
        git_metrics = git_analyzer.analyze_repository()
        ctx.telemetry['git_metrics'] = git_metrics

        # Summary statistics
        total_issues = len(ctx.telemetry.get('issues', []))
        ctx.log(f"Audit complete: {total_issues} issues found")
        ctx.telemetry['audit_summary'] = {
            'total_issues': total_issues,
            'security_issues': security_results['total_issues'],
            'dependency_vulnerabilities': len(python_deps.get('vulnerabilities', [])),
            'python_files': len(code_metrics['python']['files']),
            'javascript_files': len(code_metrics['javascript']['files']),
            'rust_files': len(code_metrics['rust']['files']),
        }
