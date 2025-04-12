# test_risk.py
import pytest
from datetime import datetime
from risk import assess_risk

def test_low_risk():
    score, reasons = assess_risk(
        changed_files=['main.py', 'README.md'],
        reviewers=['alice'],
        check_work_hours=False
    )
    assert score == 10
    assert not reasons

def test_file_count_risk():
    score, reasons = assess_risk(
        changed_files=[f'file{i}.py' for i in range(25)],
        reviewers=['bob']
    )
    assert score < 10
    assert any("files changed" in r for r in reasons)

def test_secret_file_risk():
    score, reasons = assess_risk(
        changed_files=['config/.env', 'main.py'],
        reviewers=['bob']
    )
    assert score < 10
    assert any("Suspicious file" in r for r in reasons)

def test_time_risk():
    fake_friday = datetime(2024, 1, 5, 17, 30)  # Friday 5:30PM
    score, reasons = assess_risk(
        changed_files=['main.py'],
        reviewers=['carol'],
        current_time=fake_friday
    )
    assert score < 10
    assert any("Friday" in r for r in reasons)

def test_no_reviewer_risk():
    score, reasons = assess_risk(
        changed_files=['main.py'],
        reviewers=[]
    )
    assert score < 10
    assert any("No reviewer" in r for r in reasons)
