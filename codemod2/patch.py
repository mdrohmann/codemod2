from codemod2.position import Position


class Patch(object):
    r"""
    Represents a range of a file and (optionally) a list of lines with which to
    replace that range.

    Example 0: Replace two complete lines with three lines
    >>> l0 = ['a\n', 'b\n', 'c\n', 'd\n', 'e\n', 'f\n']
    >>> p0 = Patch(2, 4, l0, ['X\n', 'Y\n', 'Z\n'], 'x.php')
    >>> print(p0.render_range())
    x.php:2-4
    >>> p0.new_end_line_number
    5
    >>> p0.apply_to(l0)
    ['a\n', 'b\n', 'X\n', 'Y\n', 'Z\n', 'e\n', 'f\n']

    Example 1: Remove two complete lines
    >>> l = ["a\n", "b\n", "  c\n", "d\n", "e\n", "f\n"]
    >>> p1 = Patch(1,3, l, [], 'filename')
    >>> p1.new_end_line_number
    1
    >>> p1.apply_to(l)
    ['a\n', 'd\n', 'e\n', 'f\n']

    Example 2: Replace last two lines with something else
    >>> p2 = Patch(4,6, l, ['something else\n'], 'filename')
    >>> p2.new_end_line_number
    5
    >>> p2.apply_to(l)
    ['a\n', 'b\n', '  c\n', 'd\n', 'something else\n']

    Example 3: Replace the characters `c\n` in third row with `something else` merging with next line
    >>> p3 = Patch(2,3, l, '  something else', 'filename')
    >>> p3.new_end_line_number
    2
    >>> p3.apply_to(l)
    ['a\n', 'b\n', '  something elsed\n', 'e\n', 'f\n']
    """

    def __init__(
        self,
        start_line_number: int,
        end_line_number: int | None = None,
        file_lines: list[str] | None = None,
        new_lines: list[str] | str | None = None,
        path: str | None = None,
    ):
        """
        Constructs a Patch object.

        @param end_line_number  The line number just *after* the end of
                                the range.
                                Defaults to
                                start_line_number + 1, i.e. a one-line
                                diff.
        @param lines            The set of lines which are to be replaced
        @param new_lines        The set of lines with which to
                                replace the range
                                specified, or a newline-delimited string.
                                Omitting this means that
                                this "patch" doesn't actually
                                suggest a change.
        @param path             Path is optional only so that
                                suggestors that have
                                been passed a list of lines
                                don't have to set the
                                path explicitly.
                                (It'll get set by the suggestor's caller.)
        """
        self.path = path
        self.start_line_number = start_line_number
        self.end_line_number = (
            start_line_number + 1 if end_line_number is None else end_line_number
        )
        self.new_lines = (
            new_lines.splitlines(True) if isinstance(new_lines, str) else new_lines
        )

        self.new_end_line_number = None
        if self.new_lines is not None:
            assert file_lines is not None
            self.new_end_line_number = self._patch_end_line_number()

    def apply_to(self, lines: list[str]) -> list[str]:
        assert self.new_lines is not None
        end_line_number = self.end_line_number
        last_new_line = self.new_lines[-1:]
        if len(last_new_line) == 1 and (
            len(last_new_line[0]) == 0 or last_new_line[0][-1] != "\n"
        ):
            last_new_line = [
                "".join(
                    last_new_line
                    + lines[self.end_line_number : self.end_line_number + 1]
                )
            ]
            end_line_number += 1
        return (
            lines[: self.start_line_number]
            + self.new_lines[:-1]
            + last_new_line
            + lines[end_line_number:]
        )

    def _patch_end_line_number(self) -> int:
        r"""
        computes the end line number of the patch

        if new lines don't end in a new line we ensure that it next time, we re-try to match at this line again
        """
        assert self.new_lines is not None
        return (
            self.start_line_number
            + len(self.new_lines)
            - (
                1
                if len(self.new_lines) > 0
                and len(self.new_lines[-1]) > 0
                and self.new_lines[-1][-1] != "\n"
                else 0
            )
        )

    def render_range(self) -> str:
        """
        returns a string <path>:<range>
        """
        path = self.path or "<unknown>"
        if self.start_line_number == self.end_line_number - 1:
            return f"{path}:{self.start_line_number}"
        else:
            return f"{path}:{self.start_line_number}-{self.end_line_number}"

    @property
    def start_position(self) -> Position:
        assert self.path is not None
        return Position(self.path, self.start_line_number)
