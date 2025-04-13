import pytest
import json
from src.certainty_score import CertaintyScore, Conclusion


class TestConclusion:

    def test_valid_conclusions(self):
        assert Conclusion.SUCCESS.value == "success"
        assert Conclusion.NEUTRAL.value == "neutral"
        assert Conclusion.FAILURE.value == "failure"
        assert Conclusion.CANCELLED.value == "cancelled"
        assert Conclusion.SKIPPED.value == "skipped"
        assert Conclusion.TIMED_OUT.value == "timed_out"
        assert Conclusion.ACTION_REQUIRED.value == "action_required"

    def test_is_valid(self):
        assert Conclusion.is_valid("success") is True
        assert Conclusion.is_valid("neutral") is True
        assert Conclusion.is_valid("invalid_value") is False


class TestCertaintyScore:

    def test_initialization(self, test_score):
        score = test_score
        assert score.score == 82
        assert score.reasons == ["No reviewers", "Suspicious file(s)"]
        assert score.files == ["config/.env"]
        assert score.conclusion == "success"

    def test_initialization_defaults(self):
        score = CertaintyScore(75)
        assert score.score == 75
        assert score.reasons == []
        assert score.files == []
        assert score.conclusion == "neutral"

    def test_validation_score_type(self):
        with pytest.raises(ValueError, match="Score must be an integer"):
            CertaintyScore("not an int")

    def test_validation_score_range(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            CertaintyScore(-1)

        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            CertaintyScore(101)

    def test_validation_reasons_type(self):
        with pytest.raises(ValueError, match="Reasons must be a list"):
            CertaintyScore(80, "not a list")

    def test_validation_files_type(self):
        with pytest.raises(ValueError, match="Files must be a list"):
            CertaintyScore(80, [], "not a list")

    def test_validation_conclusion_type(self):
        with pytest.raises(ValueError, match="Conclusion must be a string"):
            CertaintyScore(80, [], [], 123)

    def test_validation_conclusion_value(self):
        with pytest.raises(ValueError, match="Invalid conclusion"):
            CertaintyScore(80, [], [], "invalid_conclusion")

    def test_to_dict(self):
        score = CertaintyScore(
            82, ["No reviewers", "Changed env file"], ["config/.env"]
        )
        expected = {
            "conclusion": "neutral",
            "score": 82,
            "reasons": ["No reviewers", "Changed env file"],
            "files": ["config/.env"],
        }
        assert score.to_dict() == expected

    def test_to_json(self):
        score = CertaintyScore(
            82, ["No reviewers", "Changed env file"], ["config/.env"]
        )
        expected = {
            "conclusion": "neutral",
            "score": 82,
            "reasons": ["No reviewers", "Changed env file"],
            "files": ["config/.env"],
        }
        json_str = score.to_json()
        assert json.loads(json_str) == expected

    def test_from_dict(self):
        data = {
            "score": 82,
            "reasons": ["No reviewers", "Changed env file"],
            "files": ["config/.env"],
        }
        score = CertaintyScore.from_dict(data)
        assert score.score == 82
        assert score.reasons == ["No reviewers", "Changed env file"]
        assert score.files == ["config/.env"]

    def test_from_dict_missing_fields(self):
        data = {"score": 82}
        score = CertaintyScore.from_dict(data)
        assert score.score == 82
        assert score.reasons == []
        assert score.files == []

    def test_from_json(self):
        json_str = '{"score": 82, "reasons": ["No reviewers", "Changed env file"], "files": ["config/.env"]}'
        score = CertaintyScore.from_json(json_str)
        assert score.score == 82
        assert score.reasons == ["No reviewers", "Changed env file"]
        assert score.files == ["config/.env"]

    def test_from_json_invalid(self):
        with pytest.raises(ValueError, match="Invalid JSON string"):
            CertaintyScore.from_json("not valid json")

    def test_get_summary(self):
        score = CertaintyScore(
            82, ["No reviewers", "Changed env file"], ["config/.env"]
        )
        summary = score.get_summary()
        assert "Certainty Score: 82/100" in summary
        assert "Concerns: No reviewers, Changed env file" in summary
        assert "Files: config/.env" in summary

    def test_get_summary_empty_lists(self):
        score = CertaintyScore(82)
        summary = score.get_summary()
        assert "Certainty Score: 82/100" in summary
        assert "Concerns: No specific concerns" in summary
        assert "Files: No specific files" in summary
