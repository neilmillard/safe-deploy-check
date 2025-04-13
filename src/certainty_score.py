from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any
import json


class Conclusion(str, Enum):
    """Valid conclusion states for a certainty score check."""

    SUCCESS = "success"
    NEUTRAL = "neutral"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a string value is a valid conclusion."""
        return value in [item.value for item in cls]


@dataclass
class CertaintyScore:
    """Represents the certainty score and related information for a code change."""

    score: int
    reasons: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    conclusion: str = Conclusion.NEUTRAL.value

    def __post_init__(self):
        """Validate the data after initialization."""
        if not isinstance(self.score, int):
            raise ValueError("Score must be an integer")
        if self.score < 0 or self.score > 100:
            raise ValueError("Score must be between 0 and 100")

        if not isinstance(self.reasons, list):
            raise ValueError("Reasons must be a list")

        if not isinstance(self.files, list):
            raise ValueError("Files must be a list")

        if not isinstance(self.conclusion, str):
            raise ValueError("Conclusion must be a string")

        if not Conclusion.is_valid(self.conclusion):
            raise ValueError(
                f"Invalid conclusion: {self.conclusion}. Must be one of: {', '.join([c.value for c in Conclusion])}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the CertaintyScore to a dictionary."""
        return {
            "score": self.score,
            "reasons": self.reasons,
            "files": self.files,
            "conclusion": self.conclusion,
        }

    def to_json(self) -> str:
        """Convert the CertaintyScore to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CertaintyScore":
        """Create a CertaintyScore instance from a dictionary."""
        return cls(
            score=data.get("score", 0),
            reasons=data.get("reasons", []),
            files=data.get("files", []),
            conclusion=data.get("conclusion", Conclusion.NEUTRAL.value),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CertaintyScore":
        """Create a CertaintyScore instance from a JSON string."""
        try:
            return cls.from_dict(json.loads(json_str))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")

    def get_summary(self) -> str:
        """Generate a human-readable summary."""
        reasons_text = (
            ", ".join(self.reasons) if self.reasons else "No specific concerns"
        )
        files_text = ", ".join(self.files) if self.files else "No specific files"

        conclusion_text = self.conclusion.upper()

        return f"Certainty Score: {self.score}/100 ({conclusion_text})\nConcerns: {reasons_text}\nFiles: {files_text}"
