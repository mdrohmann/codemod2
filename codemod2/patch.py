from codemod2.position import Position


class Patch(object):
    """
    Represents a range of a file and (optionally) a list of lines with which to
    replace that range.

    >>> l = ['a', 'b', 'c', 'd', 'e', 'f']
    >>> p = Patch(2, 4, l, ['a', 'b', 'X', 'Y', 'Z', 'e', 'f'], 'x.php')
    >>> print(p.render_range())
    x.php:2-4
    >>> p.new_end_line_number
    5
    """

    def __init__(
        self,
        start_line_number: int,
        end_line_number: int | None=None,
        file_lines: list[str] | None=None,
        new_lines: list[str] | str | None=None,
        path: str | None=None,
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
        self.end_line_number = start_line_number + 1 if end_line_number is None else end_line_number
        self.new_lines = new_lines.splitlines(True) if isinstance(new_lines, str) else new_lines

        self.new_end_line_number = None
        if self.new_lines is not None:
            assert file_lines is not None
            self.new_end_line_number = self._patch_end_line_number(file_lines)

    def _patch_end_line_number(self, file_lines: list[str]) -> int:
        r"""
        computes the end line number of the patch
        
        Example 1: Remove two complete lines
        >>> l = ["a\n", "b\n", "  c\n", "d\n", "e\n", "f\n"]
        >>> nl = ["a\n", "  d\n", "e\n", "f\n"]
        >>> p = Patch(1,3, l, nl, 'filename')
        >>> p._patch_end_line_number(l)
        1
        >>> nl[1] == "  d\n"
        True

        Example 2: Replace last two lines with something else
        >>> nl2 = ["a\n", "b\n", "  c\n", "d\n", "something else\n"]
        >>> p2 = Patch(4,6, l, nl2, 'filename')
        >>> p2._patch_end_line_number(l)
        5
        >>> len(nl2) == 5
        True

        Example 3: Replace the characters `c\n` in third row with `something else` merging with next line
        >>> nl3 = ["a\n", "b\n", "  something elsed\n", "e\n", "f\n"]
        >>> p3 = Patch(2,3, l, nl3, 'filename')
        >>> p3._patch_end_line_number(l)
        2
        """
        # find matching line in patch
        j: int = len(file_lines) - 1
        assert self.new_lines is not None
        for i in reversed(range(self.start_line_number, len(self.new_lines))):
            if i < 0:
                raise RuntimeError(
                    "This should not happen: Cannot find end of patch"
                )
            if j <= self.end_line_number:
                # multi-line patches may have removed the new-line
                if self.new_lines[i] == file_lines[j]:
                    return i
                elif self.new_lines[i].endswith(file_lines[j]):
                    return i
                else:
                    return i+1
            assert self.new_lines[i] == file_lines[j], "This should not happen: Cannot find end of patch"
            j -= 1

        return len(self.new_lines)

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
