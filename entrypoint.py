import os
import sys
from github import Github
from datetime import datetime

token = os.environ['INPUT_GITHUB_TOKEN']
repo_name = os.environ['GITHUB_REPOSITORY']
pr_number = os.environ.get('PR_NUMBER') or os.environ.get('GITHUB_REF_NAME', '').split('/')[-1]

g = Github(token)
repo = g.get_repo(repo_name)

# Get the pull request (assumes PR trigger)
try:
    pr = repo.get_pull(int(pr_number))
except:
    print("Could not determine PR number.")
    sys.exit(1)

risk = 0
reasons = []

# Check file count
files = list(pr.get_files())
if len(files) > 20:
    risk += 2
    reasons.append("Too many files changed")

# Check for secrets
for f in files:
    if f.filename.endswith(('.env', '.pem', 'secrets.py')):
        risk += 3
        reasons.append(f"Suspicious file: {f.filename}")

# Check day/time
now = datetime.utcnow()
if now.weekday() == 4 and now.hour >= 15:
    risk += 2
    reasons.append("Deploying on Friday evening")

# Check reviewers
if not pr.requested_reviewers:
    risk += 1
    reasons.append("No reviewer assigned")

# Final output
print("Safe Deploy Check Completed.")
print(f"Risk Score: {risk}/10")
print("Reasons:")
for reason in reasons:
    print("-", reason)

# Fail if risk too high
if risk >= 5:
    print("Deployment Risk Too High! Aborting.")
    sys.exit(1)
