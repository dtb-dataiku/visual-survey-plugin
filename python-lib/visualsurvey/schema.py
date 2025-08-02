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
        except ValueError as e:
            valid = ", ".join(m.value from m in cls)
            raise ValueError(f"Unknown question type '{raw}'. Expected one of: {valid}") from e
            
@dataclass(frozen=True, slots=True)
class SurveyQuestion:
    """
    A survey question
    
    Attributes
    ----------
    id: str
        Unique identifer to be used as column name when saving responses.
    label: str
        Human-readable question text to display to the user.
    qtype: QuestionType
        Interaction widget type.
    options: List[str], optional
        Allowed choices for choice-based questions. Ignored for text questions.
    default: str, optional
        Pre-select option or default text shown in the input.
    required: bool
        Whether the question must be answered before form submission.
    """
    
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
            
def _split_options(raw: str, delimiter: str = OPTIONS_DELIMITER) -> List[str]:
    pass

def parse_questions() -> List[SurveyQuestion]:
    """
    
    """
    
    return questions
