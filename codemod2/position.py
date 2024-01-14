from typing import Type, Union


class Position(object):
    """
    >>> p1, p2 = Position('./hi.php', 20), Position('./hi.php:20')
    >>> p1.path == p2.path and p1.line_number == p2.line_number
    True
    >>> p1
    Position('./hi.php', 20)
    >>> print(p1)
    ./hi.php:20
    >>> Position(p1)
    Position('./hi.php', 20)
    >>> Position(None, None)
    Position(None, None)
    """

    def __init__(self, *path_and_line_number: Union[str, int, "Position"]):
        """
        You can use the two parameter version, and pass a
        path and line number, or
        you can use the one parameter version, and
        pass a $path:$line_number string,
        or another instance of Position to copy.
        """
        if len(path_and_line_number) == 2:
            path, line_number = path_and_line_number
            assert path is None or isinstance(path, str)
            assert line_number is None or isinstance(line_number, int)
            self.path: str | None = path
            self.line_number: int | None = line_number
        elif len(path_and_line_number) == 1:
            arg = path_and_line_number[0]
            assert isinstance(arg, str | Position)
            if isinstance(arg, Position):
                self.path, self.line_number = arg.path, arg.line_number
            else:
                try:
                    self.path, line_number_s = arg.split(":")
                    self.line_number = int(line_number_s)
                except ValueError as exc:
                    raise ValueError(
                        f"inappropriately formatted Position string: {path_and_line_number[0]}"
                    ) from exc
        else:
            raise TypeError("Position takes 1 or 2 arguments")

    def __repr__(self) -> str:
        return f"Position({repr(self.path)}, {self.line_number})"

    def __str__(self) -> str:
        return f"{self.path}:{self.line_number}"
