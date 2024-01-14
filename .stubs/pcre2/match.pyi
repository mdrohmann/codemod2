from enum import IntEnum as IntEnum
from .pattern import Pattern

class Match:
    def __init__(self, *args, **kwargs) -> None: ...
    @property
    def options(self) -> int: ...
    @property
    def subject(self): ...
    @property
    def pattern(self) -> Pattern: ...
    def start(self, group: int | str = 0) -> int: ...
    def end(self, group: int | str = 0) -> int: ...
    def substring(self, group: int | str = 0) -> str: ...
    def __getitem__(self, group: int | str): ...
    def expand(self, replacement: str, offset: int = 0, options: int = 0, low_memory: bool = False): ...
    def groups(self): ...
