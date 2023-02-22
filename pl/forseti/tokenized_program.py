from dataclasses import dataclass, field
from typing import List


@dataclass
class TokenizedProgram:
    code_units: List['CodeUnit'] = field(default_factory=list) 
    raw_codes: List[str] = field(default_factory=list) 
    filenames: List[str] = field(default_factory=list) 
    author: str = ""
