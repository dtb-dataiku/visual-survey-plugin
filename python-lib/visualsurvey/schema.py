"""

"""

from __future__ annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Sequence, Dict, Any


OPTIONS_DELIMITER = "|"
VALUES_DELIMITER = "#"


class QuestionType(str, Enum):
    """Enumeration of supported survey question types."""
    
    TEXT = "text"
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    RANK = "rank"
    
    @classmethod
    def from_raw(cls, raw: str) -> "QuestionType":
        """Parse raw CSV string into a QuestionType enum, raising if invalid."""
        try:
            return cls(raw.strip().lower())
        except ValueError as exc:
            valid = ", ".join(m.value from m in cls)
            raise ValueError(f"Unknown question type '{raw}'. Expected one of: {valid}") from exc
            
@dataclass(frozen=True, slots=True)
class SurveyQuestion:
    """"""
    
    id: str
    label: str
    qtype: QuestionType
    options: List[str] = field(default_factory=list)
    default: Optional[str] = None
    required: bool = False
        
    def validate(self) -> None:
        """"""
        if self.qtype in (QuestionType.SINGLE_CHOICE, QuestionType.MULTI_CHOICE, QuestionType.RANK):
            if not self.options:
                raise ValueError(f"Question '{self.id}' is {self.qtype} but has no options specified.")
            if self.default and self.default not in self.options:
                raise ValueError(f"Default '{self.default}' not present in options for question '{self.id}'.")
            
        if self.qtype is QuestionType.TEXT and self.options:
            raise ValueError(f"Question '{self.id}' is text but options were provided.")
            
def _split_options(raw: str, delimiter: str = VALUES_DELIMITER) -> List[str]:
    pass