import logging
import os
from datetime import datetime, UTC
from typing import Optional

from github import Github, PullRequest, Repository

from src.certainty_score import CertaintyScore

logger = logging.getLogger(__name__)


class GitHubGateway:
    """A gateway class for interacting with the GitHub API."""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the GitHub gateway.

        Args:
            github_token: GitHub API token. If None, it will be retrieved from environment variables.
        """
        self.github_token = github_token or os.getenv("INPUT_GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is required but not provided")
        self.client = Github(self.github_token)

    def get_repo(self, repo_name: str) -> Repository.Repository:
        """
        Get a GitHub repository.

        Args:
            repo_name: The repository name in the format 'owner/repo'

        Returns:
            Repository object

        Raises:
            ValueError: If repo_name is invalid
        """
        if not repo_name or "/" not in repo_name:
            raise ValueError(f"Invalid repository name: {repo_name}")

        return self.client.get_repo(repo_name)

    def get_check_run_certainty_score(
        self, repo_name: str, commit_sha: str
    ) -> Optional[CertaintyScore]:
        """
        Get the certainty score from a check run for a commit.

        Args:
            repo_name: The repository name in the format 'owner/repo'
            commit_sha: The SHA of the commit

        Returns:
            A CertaintyScore object if found, None otherwise
        """
        try:
            repo = self.get_repo(repo_name)
            commit = repo.get_commit(commit_sha)
            check_runs = commit.get_check_runs()

            for check in check_runs:
                if check.name == "Certainty Score":
                    try:
                        return CertaintyScore.from_json(check.output.summary)
                    except ValueError:
                        logger.warning(
                            "Failed to parse Certainty Score from check summary"
                        )
                        return None

            return None
        except Exception as e:
            logger.error(f"Failed to get check run summary: {e}")
            return None

    def get_pr_from_ref(self, repo_name, ref) -> PullRequest.PullRequest:
        """
        Get the PR object from the current ref (if the event is a PR).

        Args:
            repo_name: The repository name in the format 'owner/repo'
            ref: The ref of the PR

        Returns:
            PullRequest object

        Raises:
            ValueError: If the current ref is not a pull request
        """
        if ref.startswith("refs/pull/"):
            pr_number = ref.split("/")[2]  # Extract the PR number
        else:
            raise ValueError(f"Ref {ref} is not a pull request.")

        # Fetch the PR from GitHub
        repo = self.get_repo(repo_name)
        return repo.get_pull(int(pr_number))

    def create_check_run(self, repo_name: str, sha: str) -> int:
        """
        Create a new check run and return its ID.

        Args:
            repo_name: The repository name in the format 'owner/repo'
            sha: The commit SHA

        Returns:
            The ID of the created check run

        Raises:
            ValueError: If repo_name or sha is invalid
        """
        if not sha:
            raise ValueError("Commit SHA is required")

        repo = self.get_repo(repo_name)
        check_run = repo.create_check_run(
            name="Certainty Score",
            head_sha=sha,
            status="in_progress",
            started_at=datetime.now(UTC),
        )
        return check_run.id

    def update_check_run_with_score(
        self,
        repo_name: str,
        check_id: int,
        certainty_score: CertaintyScore,
        details_text: Optional[str] = None,
    ) -> None:
        """
        Update the status of an existing check run.

        Args:
            repo_name: The repository name in the format 'owner/repo'
            check_id: The ID of the check run to update
            certainty_score: The CertaintyScore object
            details_text: Optional Additional details to include in the check run

        Raises:
            ValueError: If any required parameter is invalid
        """
        if not check_id:
            raise ValueError("Check run ID is required")

        conclusion = certainty_score.conclusion

        summary = certainty_score.to_json()

        if details_text is None:
            details_text = certainty_score.get_summary()

        repo = self.get_repo(repo_name)
        check_run = repo.get_check_run(check_id)

        check_run.edit(
            status="completed",
            conclusion=conclusion,
            completed_at=datetime.now(UTC),
            output={
                "title": f"Certainty Score: {certainty_score.score}",
                "summary": summary,
                "text": details_text,
            },
        )
        logger.info(
            f"Check run updated with score {certainty_score.score} (conclusion: {conclusion})"
        )


def get_github_gateway() -> GitHubGateway:
    """Factory function to create a GitHub gateway instance."""
    return GitHubGateway(os.getenv("INPUT_GITHUB_TOKEN"))
