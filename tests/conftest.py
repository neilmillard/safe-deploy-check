import os
from unittest.mock import patch, Mock

import pytest

from src.certainty_score import CertaintyScore
from src.github_gateway import GitHubGateway


@pytest.fixture
def mock_github():
    with patch("src.github_gateway.Github") as mock_github:
        yield mock_github


@pytest.fixture
def github_gateway():
    with patch.dict(os.environ, {"INPUT_GITHUB_TOKEN": "fake_token"}):
        return GitHubGateway()


@pytest.fixture
def mock_repo():
    repo = Mock()
    repo.get_commit = Mock()
    repo.get_pull = Mock()
    repo.create_check_run = Mock()
    repo.get_check_run = Mock()
    return repo


@pytest.fixture
def test_score():
    return CertaintyScore(
        82, ["No reviewers", "Suspicious file(s)"], ["config/.env"], "success"
    )
