import os
import sys
from github import Github
from datetime import datetime

token = os.environ['INPUT_GITHUB_TOKEN']
repo_name = os.environ['GITHUB_REPOSITORY']
sha = os.environ['GITHUB_SHA']

g = Github(token)
repo = g.get_repo(repo_name)

check = repo.create_check_run(
    name="Safe Deploy Check",
    head_sha=sha,
    status="in_progress"
)

# Get the pull request (assumes PR trigger)
try:
    pr_number = os.environ.get('PR_NUMBER') or os.environ.get('GITHUB_REF_NAME', '').split('/')[-1]
    pr = repo.get_pull(int(pr_number))
except:
    print("Could not determine PR number.")
    sys.exit(1)

risk = 0
reasons = []

try:
    
    files = list(pr.get_files())
    if len(files) > 20:
        risk += 2
        reasons.append("Too many files changed")

    for f in files:
        if f.filename.endswith(('.env', '.pem', 'secrets.py')):
            risk += 3
            reasons.append(f"Suspicious file: {f.filename}")

    now = datetime.utcnow()
    if now.weekday() == 4 and now.hour >= 15:
        risk += 2
        reasons.append("Deploying on Friday evening")

    if not pr.requested_reviewers:
        risk += 1
        reasons.append("No reviewer assigned")

   certainty = max(0, 10 - risk)

    conclusion = "success" if certainty >= 7 else "neutral" if certainty >= 4 else "failure"

    output = {
        "title": f"Certainty Score: {certainty}/10",
        "summary": "\n".join(reasons) if reasons else "✅ All checks passed. Low risk.",
        "text": "Deployment safety check based on file changes, reviewers, timing, and secret scanning."
    }

    check.edit(status="completed", conclusion=conclusion, output=output)
    if conclusion == "failure":
        sys.exit(1)

except Exception as e:
    check.edit(status="completed", conclusion="failure", output={
        "title": "Safe Deploy Check Failed",
        "summary": str(e),
        "text": "There was an error running the deploy risk assessment."
    })
    sys.exit(1)
