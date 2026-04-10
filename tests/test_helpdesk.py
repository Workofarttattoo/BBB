import sys
from pathlib import Path

# Ensure we can import chief_enhancements_office
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from chief_enhancements_office.tasks.helpdesk import IssuePrioritizer

def test_base_severity_scores():
    prioritizer = IssuePrioritizer()

    issues = [
        {'severity': 'critical'},
        {'severity': 'high'},
        {'severity': 'medium'},
        {'severity': 'low'}
    ]

    # expected scores:
    # critical: 100 + 1 (default user) = 101
    # high: 75 + 1 = 76
    # medium: 50 + 1 = 51
    # low: 25 + 1 = 26

    results = prioritizer.prioritize(issues)

    # Output is sorted descending
    assert results[0]['severity'] == 'critical'
    assert results[0]['priority_score'] == 101
    assert results[1]['severity'] == 'high'
    assert results[1]['priority_score'] == 76
    assert results[2]['severity'] == 'medium'
    assert results[2]['priority_score'] == 51
    assert results[3]['severity'] == 'low'
    assert results[3]['priority_score'] == 26

def test_category_boosts():
    prioritizer = IssuePrioritizer()

    issues = [
        {'severity': 'medium', 'category': 'security'},      # 50 + 50 + 1 = 101
        {'severity': 'medium', 'category': 'performance'},   # 50 + 25 + 1 = 76
        {'severity': 'medium', 'category': 'other'}          # 50 + 0 + 1 = 51
    ]

    results = prioritizer.prioritize(issues)

    assert results[0]['category'] == 'security'
    assert results[0]['priority_score'] == 101
    assert results[1]['category'] == 'performance'
    assert results[1]['priority_score'] == 76
    assert results[2]['category'] == 'other'
    assert results[2]['priority_score'] == 51

def test_affected_users_boost():
    prioritizer = IssuePrioritizer()

    issues = [
        {'severity': 'low', 'affected_users': 10},  # 25 + 0 + 10 = 35
        {'severity': 'low', 'affected_users': 50},  # 25 + 0 + 50 = 75
        {'severity': 'low', 'affected_users': 100}  # 25 + 0 + 50 = 75 (capped at 50)
    ]

    results = prioritizer.prioritize(issues)

    scores = [issue['priority_score'] for issue in results]
    assert sorted(scores, reverse=True) == [75, 75, 35]

    for r in results:
        if r['affected_users'] == 10:
            assert r['priority_score'] == 35
        elif r['affected_users'] in (50, 100):
            assert r['priority_score'] == 75

def test_default_values():
    prioritizer = IssuePrioritizer()

    issues = [{}]  # Empty issue

    # default severity: medium (50)
    # default category: unknown (0)
    # default affected_users: 1
    # total expected = 51

    results = prioritizer.prioritize(issues)

    assert len(results) == 1
    assert results[0]['priority_score'] == 51

def test_priority_sorting():
    prioritizer = IssuePrioritizer()

    issues = [
        {'id': 1, 'severity': 'low', 'affected_users': 1},     # 25 + 1 = 26
        {'id': 2, 'severity': 'critical', 'affected_users': 1},# 100 + 1 = 101
        {'id': 3, 'severity': 'medium', 'category': 'security'}# 50 + 50 + 1 = 101
    ]

    results = prioritizer.prioritize(issues)

    assert results[0]['id'] in (2, 3)
    assert results[1]['id'] in (2, 3)
    assert results[2]['id'] == 1

    assert results[0]['priority_score'] == 101
    assert results[1]['priority_score'] == 101
    assert results[2]['priority_score'] == 26
