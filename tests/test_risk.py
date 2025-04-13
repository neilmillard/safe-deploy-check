# test_risk.py
from datetime import datetime
from src.risk import assess_risk


class File:
    def __init__(self, filename):
        self.filename = filename


def test_low_risk():
    certainty_score = assess_risk(
        changed_files=[File("main.py"), File("README.md")],
        reviewers=["alice"],
        check_work_hours=False,
    )
    assert certainty_score.score == 100
    assert certainty_score.reasons[0] == "All good. No major risks detected."


def test_file_count_risk():
    certainty_score = assess_risk(
        changed_files=[File(f"file{i}.py") for i in range(25)], reviewers=["bob"]
    )
    assert certainty_score.score < 100
    assert any("files changed" in r for r in certainty_score.reasons)


def test_secret_file_risk():
    changed_files = [File("config/.env"), File("main.py")]
    certainty_score = assess_risk(changed_files=changed_files, reviewers=["bob"])
    assert certainty_score.score < 100
    assert any("Suspicious file" in r for r in certainty_score.reasons)
    assert "config/.env" in certainty_score.files


def test_time_risk():
    fake_friday = datetime(2024, 1, 5, 17, 30)  # Friday 5:30PM
    certainty_score = assess_risk(
        changed_files=[File("main.py")], reviewers=["carol"], current_time=fake_friday
    )
    assert certainty_score.score < 100
    assert any("Friday" in r for r in certainty_score.reasons)


def test_no_reviewer_risk():
    certainty_score = assess_risk(changed_files=[File("main.py")], reviewers=[])
    assert certainty_score.score < 100
    assert any("No reviewer" in r for r in certainty_score.reasons)
