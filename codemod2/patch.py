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
    >>> l = ['a', 'b', 'c', 'd', 'e', 'f']
    >>> p.apply_to(l)
    >>> l
    ['a', 'b', 'X', 'Y', 'Z', 'e', 'f']
    """

    def __init__(
        self,
        start_line_number,
        end_line_number=None,
        file_lines=None,
        new_lines=None,
        path=None,
    ):  # noqa
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
        self.end_line_number = end_line_number
        self.new_lines = new_lines

        if self.end_line_number is None:
            self.end_line_number = self.start_line_number + 1
        if isinstance(self.new_lines, str):
            self.new_lines = self.new_lines.splitlines(True)
        self.new_end_line_number = None
        if self.new_lines is not None:
            assert file_lines is not None
            self.new_end_line_number = self._patch_end_line_number(file_lines)

    def apply_to(self, lines):
        if self.new_lines is None:
            raise ValueError("Can't apply patch without suggested new lines.")
        lines[self.start_line_number : self.end_line_number] = self.new_lines[
            self.start_line_number : self.new_end_line_number
        ]

    def _patch_end_line_number(self, file_lines) -> int:
        r"""
        computes the end line number of the patch
        
        >>> l = ["a\n", "b\n", "  c\n", "d\n", "e\n", "f\n"]
        >>> nl = ["a\n", "  d\n", "e\n", "f\n"]
        >>> p = Patch(1,2, l, nl, 'filename')
        >>> p._patch_end_line_number(l)
        1
        >>> nl[1] == "  d\n"
        True
        """
        # find matching line in patch
        for i in reversed(range(self.start_line_number, len(self.new_lines))):
            for j, line in enumerate(reversed(file_lines[self.end_line_number :])):
                if i - j < 0:
                    raise RuntimeError(
                        "This should not happen: Cannot find end of patch"
                    )
                if line != self.new_lines[i - j]:
                    return i - j

        return len(self.new_lines)

    def render_range(self):
        path = self.path or "<unknown>"
        if self.start_line_number == self.end_line_number - 1:
            return f"{path}:{self.start_line_number}"
        else:
            return f"{path}:{self.start_line_number}-{self.end_line_number}"

    @property
    def start_position(self):
        return Position(self.path, self.start_line_number)
