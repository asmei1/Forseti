from typing import List
from dataclasses import dataclass, field

@dataclass
class CodeUnit:
    ast: List['Token'] = field(default_factory=list) 
    # tokenized_program: 'TokenizedProgram' = None
    

