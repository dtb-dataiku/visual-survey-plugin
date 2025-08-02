"""

"""

from __future__ annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Sequence, Dict, Any


OPTIONS_DELIMITER = "|"
VALUES_DELIMITER = '#'


# CLASS DEFINITIONS
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
    values: List[], optional
        Derived from options.
    default: str, optional
        Pre-select option or default text shown in the input.
    required: bool
        Whether the question must be answered before form submission.
    """
    
    id: str
    label: str
    qtype: QuestionType
    options: List[str] = field(default_factory=list)
    values: List[] = field(default_factory=list)
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


# HELPER FUNCTIONS
def _split_options(raw: str, delimiter: str = OPTIONS_DELIMITER) -> List[str]:
    """Split the pipe‑delimited options column into a clean list."""
    return [option.strip() for option in raw.split(delimiter) if option.strip()]

def _to_bool(value: Any) -> bool:
    """Coerce various truthy / falsy representations into a proper boolean."""
    
    # Handle booleans
    if isinstance(value, bool):
        return value
    
    # Handle None values
    if val is None:
        return False
    
    # Handle numeric equivalents (0/1)
    if isinstance(value, (int, float)):
        return bool(value)
    
    # Handle strings like 'y', 'yes', 'n', or 'no'
    value_str = str(value).strip().lower()
    truthy = {"y", "yes", "t", "true", "1"}
    falsey = {"n", "no", "f", "false", "0"}
    
    if value_str in truthy:
        return True
    if value_str in falsey:
        return False
    
    # Return false as a fallback
    return False


# FUNCTIONS
def parse_questions(rows: Sequence[Dict[str, Any]]) -> List[SurveyQuestion]:
    """
    Convert a list of CSV/Dict rows into typed SurveyQuestion instances.
    
    Attributes
    ----------
    rows: Sequence[Dict[str, Any]]
        Typically what you'd get from ``dataset.iter_rows()`` in Dataiku.
        
    Returns
    -------
    List[SurveyQuestion]
    """
    
    questions: List[SurveyQuestion] = []
        
    for r in rows:
        raw_default = r.get("default", None)
        default: Optional[str] = None if raw_default in ("", None) else str(raw_default)
        
        q = SurveyQuestion(
            id=r["id"],
            label=r["label"],
            qtype=QuestionType.from_raw(r.["qtype"]),
            options=_split_options(r.get("options", "")),
            default=default,
            required=_to_bool(r.get("required", False))
        )
        q.validate()
        questions.append(q)
    
    return questions
