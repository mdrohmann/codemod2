class LibraryError(Exception):
    errorcode: int
    def __init__(self, errorcode: int, context_msg: str = '') -> None: ...

class CompileError(LibraryError):
    def __init__(self, errorcode: int, context_msg: str = '') -> None: ...

class MatchError(LibraryError):
    def __init__(self, errorcode: int, context_msg: str = '') -> None: ...
