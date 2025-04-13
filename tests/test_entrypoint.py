import os
import pytest
from unittest.mock import patch, MagicMock

from src.entrypoint import main
from src.certainty_score import CertaintyScore


@pytest.fixture
def setup_env_vars():
    """Set up the required environment variables."""
    os.environ["GITHUB_REPOSITORY"] = "test_repo"
    os.environ["GITHUB_SHA"] = "test_sha"
    os.environ["INPUT_MAX_FILE_COUNT"] = "5"
    os.environ["INPUT_SECRET_FILE_GLOBS"] = ".env,.pem"
    os.environ["INPUT_MIN_CERTAINTY"] = "80"
    os.environ["INPUT_BLOCK_ON_FAILURE"] = "true"
    os.environ["INPUT_CHECK_WORK_HOURS"] = "false"
    os.environ["GITHUB_REF"] = "refs/pull/123/merge"


@patch("src.entrypoint.GitHubGateway")
@patch("src.entrypoint.assess_risk")
def test_main_success(mock_assess_risk, mock_github_gateway, setup_env_vars):
    """Test main function with successful execution."""
    mock_pr = MagicMock()
    mock_pr.get_files.return_value = ["file1.py", "file2.py"]
    mock_pr.requested_reviewers = ["reviewer1", "reviewer2"]

    mock_gg_instance = MagicMock()
    mock_gg_instance.get_pr_from_ref.return_value = mock_pr
    mock_gg_instance.create_check_run.return_value = "check_id"
    mock_gg_instance.get_check_run_certainty_score.return_value = None

    mock_github_gateway.return_value = mock_gg_instance

    mock_certainty_score = CertaintyScore(
        score=85,
        reasons=["Reason 1", "Reason 2"],
        files=["file1.py"],
        conclusion="success",
    )
    mock_assess_risk.return_value = mock_certainty_score

    # Run the main function
    main()

    # Assertions
    mock_gg_instance.get_pr_from_ref.assert_called_once_with(
        "test_repo", "refs/pull/123/merge"
    )
    assert mock_pr.get_files.called
    assert mock_gg_instance.create_check_run.called
    mock_assess_risk.assert_called_once_with(
        changed_files=["file1.py", "file2.py"],
        reviewers=["reviewer1", "reviewer2"],
        check_work_hours=False,
        max_files=5,
        secret_globs=[".env", ".pem"],
        min_certainty=80,
    )
    mock_gg_instance.update_check_run_with_score.assert_called_once_with(
        "test_repo", "check_id", mock_certainty_score
    )


@patch("src.entrypoint.GitHubGateway")
@patch("src.entrypoint.assess_risk")
def test_main_failure(mock_assess_risk, mock_github_gateway, setup_env_vars):
    """Test main function with a failure conclusion."""
    mock_pr = MagicMock()
    mock_pr.get_files.return_value = ["file1.py", "file2.py"]
    mock_pr.requested_reviewers = ["reviewer1"]

    mock_gg_instance = MagicMock()
    mock_gg_instance.get_pr_from_ref.return_value = mock_pr
    mock_gg_instance.create_check_run.return_value = "check_id"

    mock_github_gateway.return_value = mock_gg_instance

    mock_certainty_score = CertaintyScore(
        score=50,
        reasons=["High-risk change"],
        files=["file1.py"],
        conclusion="failure",
    )
    mock_assess_risk.return_value = mock_certainty_score

    # Mock sys.exit to avoid stopping the test
    with patch("sys.exit") as mock_exit:
        main()

        # Assertions
        mock_exit.assert_called_once_with(1)
        mock_gg_instance.update_check_run_with_score.assert_called_once_with(
            "test_repo", "check_id", mock_certainty_score
        )


@patch("src.entrypoint.GitHubGateway")
def test_main_missing_env_var(mock_github_gateway):
    """Test main function when a required environment variable is missing."""
    os.environ.clear()  # Clear all environment variables

    # Mock sys.exit to avoid stopping the test
    with patch("sys.exit") as mock_exit:
        with pytest.raises(ValueError) as excinfo:
            main()

        # Assertions
        assert "GITHUB_REF environment variable is missing or empty." in str(
            excinfo.value
        )
        mock_exit.assert_not_called()


@patch("src.entrypoint.GitHubGateway")
def test_main_exception_handling(mock_github_gateway, setup_env_vars, caplog):
    """Test main function when an exception occurs."""
    mock_pr = MagicMock()
    mock_pr.get_files.side_effect = Exception("API error")

    mock_gg_instance = MagicMock()
    mock_gg_instance.get_pr_from_ref.return_value = mock_pr
    mock_github_gateway.return_value = mock_gg_instance

    # Mock sys.exit to avoid stopping the test
    with patch("sys.exit") as mock_exit:
        main()

        assert "API error" in caplog.text

        mock_exit.assert_called_once_with(1)
        mock_gg_instance.update_check_run_with_score.assert_not_called()


@patch("src.entrypoint.GitHubGateway")
@patch("src.entrypoint.assess_risk")
def test_main_exception_after_create_check(
    mock_assess_risk, mock_github_gateway, setup_env_vars, caplog
):
    """Test main function when an exception occurs."""
    mock_pr = MagicMock()
    mock_pr.get_files.return_value = ["file1.py", "file2.py"]
    mock_pr.requested_reviewers = ["reviewer1"]

    mock_gg_instance = MagicMock()
    mock_gg_instance.get_pr_from_ref.return_value = mock_pr
    mock_gg_instance.create_check_run.return_value = "check_id"

    mock_github_gateway.return_value = mock_gg_instance

    mock_assess_risk.side_effect = ValueError("Conclusion must be a string")

    # Mock sys.exit to avoid stopping the test
    with patch("sys.exit") as mock_exit:
        main()

        assert "Conclusion must be a string" in caplog.text

        mock_exit.assert_called_once_with(1)
        mock_gg_instance.update_check_run_with_score.assert_called()
