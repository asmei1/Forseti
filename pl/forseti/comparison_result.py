from dataclasses import dataclass, field
from .comparison_pair import ComparisonPair


@dataclass
class ComparisonResult:
    pair: ComparisonPair
    result: None
    matches_a: None
    matches_b: None
