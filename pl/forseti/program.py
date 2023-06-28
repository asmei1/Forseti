from typing import List
from dataclasses import dataclass


@dataclass
class Program:
    filenames: List[str]
    raw_codes: List[str]
    author: str = ""
