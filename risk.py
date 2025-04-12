from datetime import datetime, UTC

def assess_risk(changed_files, reviewers, check_work_hours=True, max_files=20, secret_globs=None, current_time=None):
    risk = 0
    reasons = []
    secret_globs = secret_globs or ['.env', '.pem', 'secrets.py']
    current_time = current_time or datetime.now(UTC)

    # File count check
    if len(changed_files) > max_files:
        risk += 2
        reasons.append(f"{len(changed_files)} files changed (max is {max_files})")

    # Secret file detection
    for filename in changed_files:
        for pattern in secret_globs:
            if filename.endswith(pattern):
                risk += 3
                reasons.append(f"Suspicious file: {filename}")

    # Deployment time
    if check_work_hours:
        if current_time.weekday() == 4 and current_time.hour >= 16:  # Friday 4PM+
            risk += 2
            reasons.append("Deploying late on Friday")

    # Reviewer check
    if not reviewers:
        risk += 1
        reasons.append("No reviewer assigned")

    certainty = max(0, 10 - risk)
    return certainty, reasons
