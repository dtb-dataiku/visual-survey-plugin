from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Sequence, Dict, Any


# CONSTANTS
DELIMITER = "|"


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
            valid = ", ".join(m.value for m in cls)
            raise ValueError(f"Unknown question type '{raw}'. Expected one of: {valid}") from e
            
    @classmethod
    def list_types(cls) -> List[str]:
        """Return a list of supported question types."""
        return [m.value for m in cls]
            
@dataclass
class SurveyQuestion:
    """
    A survey question
    
    Attributes
    ----------
    id: str
        Unique identifer to be used as column name when saving responses.
    label: str
        Human-readable question text to display to the user.
    question_type: QuestionType
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
    question_type: QuestionType
    options: List[str] = field(default_factory=list)
    default: Optional[str] = None
    required: bool = False
        
    def validate(self) -> None:
        """"""
        if self.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.MULTI_CHOICE, QuestionType.RANK):
            if not self.options:
                raise ValueError(f"Question '{self.id}' is {self.question_type} but has no options specified.")
            if self.default and self.default not in self.options:
                raise ValueError(f"Default '{self.default}' not present in options for question '{self.id}'.")


# HELPER FUNCTIONS
def _split_options(raw: str, delimiter: str = DELIMITER) -> List[str]:
    """Split the pipe‑delimited options column into a clean list."""
    return [opt.strip() for opt in raw.split(delimiter) if opt.strip()]

def _to_bool(val: Any) -> bool:
    """Coerce various truthy / falsy representations into a proper boolean."""
    
    # Handle booleans
    if isinstance(val, bool):
        return val
    
    # Handle None values
    if val is None:
        return False
    
    # Handle numeric equivalents (0/1)
    if isinstance(val, (int, float)):
        return bool(val)
    
    # Handle strings like 'y', 'yes', 'n', or 'no'
    val_str = str(val).strip().lower()
    truthy = {"y", "yes", "t", "true", "1"}
    falsey = {"n", "no", "f", "false", "0"}
    
    if val_str in truthy:
        return True
    if val_str in falsey:
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
            question_type=QuestionType.from_raw(r["question_type"]),
            options=_split_options(r.get("options", "")),
            default=default,
            required=_to_bool(r.get("required", False))
        )
        q.validate()
        questions.append(q)
    
    return questions