import os

import pytest
from unittest.mock import Mock, patch

from github import GithubException

from src.github_gateway import GitHubGateway, get_github_gateway


class TestGitHubGateway:

    def test_init_with_token(self):
        gateway = GitHubGateway("explicit_token")
        assert gateway.github_token == "explicit_token"

    def test_init_with_env_var(self):
        with patch.dict(os.environ, {"INPUT_GITHUB_TOKEN": "env_token"}):
            gateway = GitHubGateway()
            assert gateway.github_token == "env_token"

    def test_init_no_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GitHub token is required"):
                GitHubGateway()

    def test_get_repo(self, github_gateway, mock_github):
        mock_repo = Mock()
        mock_get_repo = Mock(return_value=mock_repo)
        github_gateway.client.get_repo = mock_get_repo

        result = github_gateway.get_repo("owner/repo")

        github_gateway.client.get_repo.assert_called_once_with("owner/repo")
        assert result == mock_repo

    def test_get_repo_invalid_name(self, github_gateway):
        with pytest.raises(ValueError, match="Invalid repository name"):
            github_gateway.get_repo("")

        with pytest.raises(ValueError, match="Invalid repository name"):
            github_gateway.get_repo("invalid-repo-format")

    def test_get_check_run_summary_found(self, github_gateway, mock_repo, test_score):
        # Setup
        github_gateway.get_repo = Mock(return_value=mock_repo)
        mock_commit = Mock()
        mock_repo.get_commit.return_value = mock_commit

        mock_check_run = Mock()
        mock_check_run.name = "Certainty Score"
        mock_check_run.output.summary = test_score.to_json()

        mock_commit.get_check_runs.return_value = [
            Mock(name="Other Check"),
            mock_check_run,
        ]

        # Execute
        result = github_gateway.get_check_run_certainty_score("owner/repo", "sha123")

        # Assert
        github_gateway.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_commit.assert_called_once_with("sha123")
        mock_commit.get_check_runs.assert_called_once()
        assert result == test_score

    def test_get_check_run_summary_not_found(self, github_gateway, mock_repo):
        # Setup
        github_gateway.get_repo = Mock(return_value=mock_repo)
        mock_commit = Mock()
        mock_repo.get_commit.return_value = mock_commit

        mock_commit.get_check_runs.return_value = [
            Mock(name="Other Check"),
        ]

        # Execute
        result = github_gateway.get_check_run_certainty_score("owner/repo", "sha123")

        # Assert
        assert None is result

    def test_get_check_run_summary_exception(self, github_gateway, mock_repo):
        # Setup
        github_gateway.get_repo = Mock(return_value=mock_repo)
        mock_repo.get_commit.side_effect = GithubException(404, "Not found")

        # Execute
        result = github_gateway.get_check_run_certainty_score("owner/repo", "sha123")

        # Assert
        assert None is result

    def test_get_check_run_invalid_summary_exception(self, github_gateway, mock_repo):
        # Setup
        github_gateway.get_repo = Mock(return_value=mock_repo)
        mock_commit = Mock()
        mock_repo.get_commit.return_value = mock_commit

        mock_check_run = Mock()
        mock_check_run.name = "Certainty Score"
        mock_check_run.output.summary = "Not structured Json"

        mock_commit.get_check_runs.return_value = [
            Mock(name="Other Check"),
            mock_check_run,
        ]

        # Execute
        result = github_gateway.get_check_run_certainty_score("owner/repo", "sha123")

        # Assert
        assert None is result

    def test_get_pr_from_ref_valid(self, github_gateway, mock_repo):
        # Setup
        github_gateway.get_repo = Mock(return_value=mock_repo)
        mock_pr = Mock()
        mock_repo.get_pull.return_value = mock_pr

        result = github_gateway.get_pr_from_ref("owner/repo", "refs/pull/123/merge")

        # Assert
        github_gateway.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_pull.assert_called_once_with(123)
        assert result == mock_pr

    def test_get_pr_from_ref_invalid_ref(self, github_gateway):
        with pytest.raises(ValueError, match="is not a pull request"):
            github_gateway.get_pr_from_ref("owner/repo", "refs/heads/main")

    def test_create_check_run(self, github_gateway, mock_repo):
        github_gateway.get_repo = Mock(return_value=mock_repo)
        mock_check_run = Mock()
        mock_check_run.id = 12345
        mock_repo.create_check_run.return_value = mock_check_run

        # Execute
        with patch("src.github_gateway.datetime") as mock_datetime:
            mock_datetime.now.return_value = "fake_now"
            result = github_gateway.create_check_run("owner/repo", "sha123")

        # Assert
        github_gateway.get_repo.assert_called_once_with("owner/repo")
        mock_repo.create_check_run.assert_called_once()
        assert mock_repo.create_check_run.call_args[1]["head_sha"] == "sha123"
        assert mock_repo.create_check_run.call_args[1]["name"] == "Certainty Score"
        assert result == 12345

    def test_create_check_run_invalid_sha(self, github_gateway):
        with pytest.raises(ValueError, match="Commit SHA is required"):
            github_gateway.create_check_run("owner/repo", "")

    def test_update_check_run(self, github_gateway, mock_repo, test_score):
        # Setup
        github_gateway.get_repo = Mock(return_value=mock_repo)
        mock_check_run = Mock()
        mock_repo.get_check_run.return_value = mock_check_run

        # Execute
        with patch("src.github_gateway.datetime") as mock_datetime:
            mock_datetime.now.return_value = "fake_now"
            github_gateway.update_check_run_with_score("owner/repo", 12345, test_score)

        # Assert
        github_gateway.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_check_run.assert_called_once_with(12345)
        mock_check_run.edit.assert_called_once()
        assert mock_check_run.edit.call_args[1]["status"] == "completed"
        assert mock_check_run.edit.call_args[1]["conclusion"] == "success"
        assert (
            mock_check_run.edit.call_args[1]["output"]["summary"]
            == test_score.to_json()
        )

    def test_update_check_run_invalid_id(self, github_gateway, test_score):
        with pytest.raises(ValueError, match="Check run ID is required"):
            github_gateway.update_check_run_with_score(
                "owner/repo", None, test_score, "text"
            )


def test_get_github_gateway():
    with patch.dict(os.environ, {"INPUT_GITHUB_TOKEN": "test_token"}):
        with patch("src.github_gateway.GitHubGateway") as mock_gateway_class:
            _ = get_github_gateway()
            mock_gateway_class.assert_called_once_with("test_token")
