from dataclasses import dataclass, field
from .submission import Submission

@dataclass
class ComparisonResult:
    submission: Submission
    result: None
