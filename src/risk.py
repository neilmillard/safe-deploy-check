from datetime import datetime, UTC

from github.File import File

from src.certainty_score import CertaintyScore


def assess_risk(
    changed_files: list[File],
    reviewers,
    check_work_hours=True,
    max_files=20,
    secret_globs=None,
    current_time=None,
    min_certainty=70,
) -> CertaintyScore:
    """
    Assess the risk of a code change based on various factors.

    This function calculates a risk score for a proposed code change by considering factors like the
    number of changed files, presence of potentially sensitive files, deployment timing, and
    reviewer availability. It then determines a certainty score and provides a list of reasons
    contributing to the risk level.

    Parameters:
    changed_files: list[File]
        A list of File objects representing the files that were changed in the proposed code
        change.
    reviewers
        A list of reviewers assigned to the code change.
    check_work_hours: bool, optional
        A flag indicating whether work hours should be checked for the deployment timing. Default is
        True.
    max_files: int, optional
        The maximum number of files allowed to be changed to avoid increasing the risk score.
        Default is 20.
    secret_globs: list[str] or None, optional
        A list of file patterns that are considered sensitive. Files matching these patterns
        increase the risk score. Default is ['.env', '.pem', 'secrets.py'].
    current_time
        The current datetime used for timing considerations. If not provided, the current time in
        UTC is used.
    min_certainty: int, optional
        The minimum certainty percentage required to consider the changes low risk. Default is 70.

    Returns:
    CertaintyScore
        An object containing the certainty score, reasons contributing to the risk score, list of
        filenames considered sensitive, and a conclusion ("success" or "failure").

    Raises:
    ValueError
    """
    risk = 0
    reasons = []
    filenames = []
    secret_globs = secret_globs or [".env", ".pem", "secrets.py"]
    current_time = current_time or datetime.now(UTC)

    # File count check
    if len(changed_files) > max_files:
        risk += 2
        reasons.append(f"{len(changed_files)} files changed (max is {max_files})")

    # Secret file detection
    for f in changed_files:
        for pattern in secret_globs:
            if f.filename.endswith(pattern):
                risk += 3
                filenames.append(f.filename)
    if len(filenames) > 0:
        reasons.append("Suspicious file(s)")

    # Deployment time
    if check_work_hours:
        if current_time.weekday() == 4 and current_time.hour >= 16:  # Friday 4PM+
            risk += 2
            reasons.append("Deploying late on Friday")

    # Reviewer check
    if not reviewers:
        risk += 1
        reasons.append("No reviewer assigned")

    certainty = max(0, 10 - risk) * 10
    conclusion = "success" if certainty >= min_certainty else "failure"
    if len(reasons) < 1:
        reasons = ["All good. No major risks detected."]

    return CertaintyScore(certainty, reasons, filenames, conclusion)
