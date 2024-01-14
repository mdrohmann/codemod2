from _typeshed import Incomplete
from enum import IntEnum

__libpcre2_version__: Incomplete

class MetaOption(IntEnum):
    @classmethod
    def verify(cls, options): ...
    @classmethod
    def decompose(cls, options): ...

class CompileOption(MetaOption):
    ALLOW_EMPTY_CLASS: int
    ALT_BSUX: int
    ALT_CIRCUMFLEX: int
    ALT_VERBNAMES: int
    ANCHORED: int
    CASELESS: int
    DOLLAR_ENDONLY: int
    DOTALL: int
    DUPNAMES: int
    ENDANCHORED: int
    EXTENDED: int
    EXTENDED_MORE: int
    FIRSTLINE: int
    LITERAL: int
    MATCH_UNSET_BACKREF: int
    MULTILINE: int
    UCP: int
    UNGREEDY: int
    UTF: int

class MatchOption(MetaOption):
    NOTBOL: int
    NOTEOL: int
    NOTEMPTY: int
    NOTEMPTY_ATSTART: int

class SubstituteOption(MetaOption):
    NOTBOL: int
    NOTEOL: int
    NOTEMPTY: int
    NOTEMPTY_ATSTART: int
    GLOBAL: int
    EXTENDED: int
    UNSET_EMPTY: int
    UNKNOWN_UNSET: int
    LITERAL: int
    REPLACEMENT_ONLY: int
ExpandOption: int

class BsrChar(IntEnum):
    UNICODE: int
    ANYCRLF: int

class NewlineChar(IntEnum):
    CR: int
    LF: int
    CRLF: int
    ANY: int
    ANYCRLF: int
    NUL: int

A: Incomplete
I: Incomplete  # noqa
G: Incomplete
M: Incomplete
NE: Incomplete
NS: Incomplete
U: Incomplete
S: Incomplete
X: Incomplete
