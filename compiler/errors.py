from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class SemanticError:
    msg: str
    pos: Optional[Tuple[int, int]] = None

    def __str__(self):
        if self.pos:
            return f"{self.msg} (at line {self.pos[0]}, col {self.pos[1]})"
        return self.msg


class Diagnostics:
    def __init__(self):
        self.errors: List[SemanticError] = []

    def add(self, msg: str, pos: Optional[Tuple[int, int]] = None):
        self.errors.append(SemanticError(msg, pos))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def report(self):
        for e in self.errors:
            print("Error:", str(e))
