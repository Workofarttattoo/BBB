import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from chief_enhancements_office.tasks.audit import SecurityScanner, SoftwareAuditTask

class MockContext:
    def __init__(self):
        self.telemetry = {}
        self.logs = []

    def log(self, message: str) -> None:
        self.logs.append(message)

def test_security_scanner_scan_python_security(tmp_path):
    # Create mock python files with known insecure functions
    insecure_file = tmp_path / "insecure.py"
    insecure_file.write_text(
        "import os\n"
        "eval('print(\"hello\")')\n"
        "exec('print(\"hello\")')\n"
        "import pickle\n"
        "pickle.loads(untrusted_data)\n"
        "import subprocess\n"
        "subprocess.run('ls -l', shell=True)\n"
        "password = 'super_secret_password'\n"
        "api_key = '12345-abcde'\n"
    )

    safe_file = tmp_path / "safe.py"
    safe_file.write_text(
        "print('This is a safe file')\n"
        "x = 5 + 5\n"
    )

    scanner = SecurityScanner(tmp_path)
    results = scanner.scan_python_security()

    assert results['total_issues'] == 6
    assert results['by_severity']['critical'] == 2
    assert results['by_severity']['high'] == 3
    assert results['by_severity']['medium'] == 1
    assert results['by_severity']['low'] == 0

    # Check if specific issues are found
    issues = results['issues']

    eval_issue = next(i for i in issues if 'eval(' in i['issue'])
    assert eval_issue['severity'] == 'high'
    assert eval_issue['file'] == 'insecure.py'
    assert eval_issue['line'] == 2

    exec_issue = next(i for i in issues if 'exec(' in i['issue'])
    assert exec_issue['severity'] == 'high'
    assert exec_issue['file'] == 'insecure.py'
    assert exec_issue['line'] == 3

    pickle_issue = next(i for i in issues if 'pickle.loads' in i['issue'])
    assert pickle_issue['severity'] == 'high'
    assert pickle_issue['file'] == 'insecure.py'
    assert pickle_issue['line'] == 5

    shell_issue = next(i for i in issues if 'shell=True' in i['issue'])
    assert shell_issue['severity'] == 'medium'
    assert shell_issue['file'] == 'insecure.py'
    assert shell_issue['line'] == 7

    password_issue = next(i for i in issues if 'password' in i['issue'].lower())
    assert password_issue['severity'] == 'critical'
    assert password_issue['file'] == 'insecure.py'
    assert password_issue['line'] == 8

    api_key_issue = next(i for i in issues if 'api key' in i['issue'].lower())
    assert api_key_issue['severity'] == 'critical'
    assert api_key_issue['file'] == 'insecure.py'
    assert api_key_issue['line'] == 9

def test_software_audit_task(tmp_path):
    # Set up a mock project root with an insecure file to trigger security scan telemetry
    insecure_file = tmp_path / "insecure.py"
    insecure_file.write_text("eval('print(\"hello\")')\n")

    task = SoftwareAuditTask()
    ctx = MockContext()

    task.execute(ctx, options={'project_root': str(tmp_path)})

    assert 'security_scan' in ctx.telemetry
    assert ctx.telemetry['security_scan']['total_issues'] == 1
    assert len(ctx.telemetry['issues']) == 1
    assert ctx.telemetry['issues'][0]['type'] == 'security'
    assert ctx.telemetry['issues'][0]['issue'] == 'Use of eval() detected - potential code injection'
