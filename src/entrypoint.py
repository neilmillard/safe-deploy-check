import logging
import os
import sys

from src.certainty_score import CertaintyScore
from src.github_gateway import GitHubGateway
from src.risk import assess_risk


def main():
    error = False
    logger = logging.getLogger(__name__)

    repo = os.getenv("GITHUB_REPOSITORY")
    sha = os.getenv("GITHUB_SHA")

    max_files = int(os.getenv("INPUT_MAX_FILE_COUNT", "20"))
    secret_globs = os.getenv("INPUT_SECRET_FILE_GLOBS", ".env,.pem").split(",")
    min_certainty = int(os.getenv("INPUT_MIN_CERTAINTY", "70"))
    block_on_failure = os.getenv("INPUT_BLOCK_ON_FAILURE", "true").lower() == "true"
    check_work_hours = os.getenv("INPUT_CHECK_WORK_HOURS", "true").lower() == "true"

    # Get the pull request (assumes PR trigger)
    ref = os.environ.get("GITHUB_REF")
    if not ref:
        message = "GITHUB_REF environment variable is missing or empty."
        print(message)
        raise ValueError(message)

    gg = GitHubGateway()

    pr = gg.get_pr_from_ref(repo, ref)

    check_id = None
    certainty_score = None
    try:
        changed_files = list(pr.get_files())
        reviewers = pr.requested_reviewers

        # Create Check Run
        check_id = gg.create_check_run(repo, sha)

        # Evaluate Risk
        certainty_score = assess_risk(
            changed_files=changed_files,
            reviewers=reviewers,
            check_work_hours=check_work_hours,
            max_files=max_files,
            secret_globs=secret_globs,
            min_certainty=min_certainty,
        )

        gg.update_check_run_with_score(repo, check_id, certainty_score)

        # Verify check data
        gg.get_check_run_certainty_score(repo, sha)

    except Exception as e:
        logger.error(f"There was an error running the deploy risk assessment. {e}")
        if not certainty_score:
            certainty_score = CertaintyScore(0, ["Unknown error"], [], "failure")
        if check_id:
            gg.update_check_run_with_score(
                repo,
                check_id,
                certainty_score,
                "There was an error running the deploy risk assessment.",
            )
        error = True

    if certainty_score.conclusion == "failure" and block_on_failure:
        error = True

    if error:
        sys.exit(1)


if __name__ == "__main__":
    main()
