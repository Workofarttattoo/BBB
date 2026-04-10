import pytest
import sys
from pathlib import Path

# Add root directory to path to import chief_enhancements_office
sys.path.insert(0, str(Path(__file__).parent.parent))

from chief_enhancements_office.tasks.helpdesk import IssueClassifier

def test_classify_security():
    """Test classification of a security issue."""
    classifier = IssueClassifier()
    issue_text = "There is a major vulnerability in the auth system."
    result = classifier.classify(issue_text)

    assert result['category'] == 'security'
    assert result['severity'] == 'critical'
    assert result['confidence'] > 0.0

def test_classify_bug():
    """Test classification of a bug issue."""
    classifier = IssueClassifier()
    issue_text = "The application keeps throwing an exception and crashes."
    result = classifier.classify(issue_text)

    assert result['category'] == 'bug'
    assert result['severity'] == 'high'
    assert result['confidence'] > 0.0

def test_classify_unknown():
    """Test classification of an issue with no matching keywords."""
    classifier = IssueClassifier()
    issue_text = "This is just some random text about nothing in particular."
    result = classifier.classify(issue_text)

    assert result['category'] == 'unknown'
    assert result['severity'] == 'medium'
    assert result['confidence'] == 0.0

def test_classify_highest_confidence():
    """Test that the category with the highest confidence is selected."""
    classifier = IssueClassifier()
    # The string has "bug" 3 times, but "slow" only 1 time.
    # Therefore the confidence for "bug" will be higher than "performance".
    issue_text = "It is slow, but it is a bug bug bug."
    result = classifier.classify(issue_text)

    assert result['category'] == 'bug'
    assert result['severity'] == 'high'
