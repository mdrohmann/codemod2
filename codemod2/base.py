#!/usr/bin/env python

# Copyright (c) 2024 Martin Drohmann
# Copyright (c) 2007-2008 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See accompanying file LICENSE.
#
# @author Martin Drohmann
# @author Justin Rosenstein

from __future__ import print_function

import argparse
import os
import regex as re
import sys
import textwrap
from math import ceil
from difflib import Differ

from codemod2.patch import Patch
from codemod2.position import Position
from codemod2.query import Query
import codemod2.helpers as helpers
import codemod2.terminal_helper as terminal

if sys.version_info[0] >= 3:
    unicode = str


def run_interactive(query, editor=None, just_count=False, default_no=False):
    """
    Asks the user about each patch suggested by the result of the query.

    @param query        An instance of the Query class.
    @param editor       Name of editor to use for manual intervention, e.g.
                        'vim'
                        or 'emacs'.  If omitted/None, defaults to $EDITOR
                        environment variable.
    @param just_count   If true: don't run normally.  Just print out number of
                        places in the codebase where the query matches.
    """

    # Load start from bookmark, if appropriate.
    bookmark = _load_bookmark()
    if bookmark:
        print(f"Resume where you left off, at {bookmark} (y/n)? ", end=" ")
        sys.stdout.flush()
        if _prompt(default="y") == "y":
            query.start_position = bookmark

    # Okay, enough of this foolishness of computing start and end.
    # Let's ask the user about some one line diffs!
    print("Searching for first instance...")
    suggestions = query.generate_patches()

    if just_count:
        for count, _ in enumerate(suggestions):
            terminal.terminal_move_to_beginning_of_line()
            print(count, end=" ")
            sys.stdout.flush()  # since print statement ends in comma
        print()
        return

    for patch in suggestions:
        _save_bookmark(patch.start_position)
        _ask_about_patch(query, patch, editor, default_no, query.yes_to_all)
        print("Searching...")
    _delete_bookmark()
    if query.yes_to_all:
        terminal.terminal_clear()
        print(
            "You MUST indicate in your code review:"
            " \"codemod2 with 'Yes to all'\"."
            "Make sure you and other people review the changes.\n\n"
            "With great power, comes great responsibility."
        )


def line_transformation_suggestor(line_transformation, line_filter=None):
    """
    Returns a suggestor (a function that takes a list of lines and yields
    patches) where suggestions are the result of line-by-line transformations.

    @param line_transformation  Function that, given a line, returns another
                                line
                                with which to replace the given one.  If the
                                output line is different from the input line,
                                the
                                user will be prompted about whether to make the
                                change.  If the output is None, this means "I
                                don't have a suggestion, but the user should
                                still be asked if they want to edit the line."
    @param line_filter          Given a line, returns True or False.  If False,
                                a line is ignored (as if line_transformation
                                returned the line itself for that line).
    """

    def suggestor(lines):
        # Iterates through the lines, applying the line transformation
        # function to each one. Yields Patch objects for lines that
        # should be changed. Skips lines where line_filter returns False.
        for line_number, line in enumerate(lines):
            if line_filter and not line_filter(line):
                continue
            candidate = line_transformation(line)
            if candidate is None:
                yield Patch(line_number)
            else:
                yield Patch(line_number, file_lines=lines, new_lines=[candidate])

    return suggestor


def regex_suggestor(
    regex: re.Pattern, substitution=None, ignore_case=False, line_filter=None
):
    """
    regex_suggestor takes a regex pattern and optional substitution, and returns a suggestor 
    function that can be used with line_transformation_suggestor.

    The returned suggestor will yield patches for lines that match the provided regex. If a
    substitution is provided, the patch will contain the substituted line. Otherwise, the 
    patch will just flag the match without suggesting changes.

    A line_filter can also be provided to filter which lines to apply the regex to.
    """

    if isinstance(regex, str):
        if ignore_case is False:
            regex = re.compile(regex)
        else:
            regex = re.compile(regex, re.IGNORECASE)

    if substitution is None:

        def line_transformation(line):
            return None if regex.match(line) else line
    else:

        def line_transformation(line):
            return regex.subf(substitution, line)

    return line_transformation_suggestor(line_transformation, line_filter)


def multiline_regex_suggestor(regex, substitution=None, ignore_case=False):
    r"""
    Return a suggestor function which, given a list of lines, generates patches
    to substitute matches of the given regex with (if provided) the given
    substitution.

    @param regex         Either a regex object or a string describing a regex.
    @param substitution  Either None (meaning that we should flag the matches
                         without suggesting an alternative), or a string (using
                         \1 notation to back-reference match groups) or a
                         function (that takes a match object as input).

    >>> s = multiline_regex_suggestor(r'args=(?<dict>\{(?:[^{}]+|(?P>dict))*+\})', r'args=Args({dict})')
    >>> patches = list(s([
    ...     '  some_arg=2,\n',
    ...     '  args={"abc": 1, "def": {"ghi": 1}, "jkl": 1},\n',
    ...     '  another_arg="another_arg"',
    ... ]))
    >>> len(patches)
    1
    >>> p = patches[0]
    >>> (p.start_line_number, p.end_line_number)
    (1, 2)
    >>> p.new_lines
    ['  args=Args({"abc": 1, "def": {"ghi": 1}, "jkl": 1}),\n']

    Example 2:  remove in middle of line
    >>> s2 = multiline_regex_suggestor(r'middle', r'')
    >>> patches2 = list(s2([
    ...     '  before\n',
    ...     '  start middle end\n',
    ...     '  after\n',
    ... ]))
    >>> len(patches2)
    1
    >>> p2 = patches2[0]
    >>> (p2.start_line_number, p2.end_line_number)
    (1, 2)
    >>> p2.new_lines
    ['  start  end\n']

    Example 2:  remove newline
    >>> s3 = multiline_regex_suggestor(r'end\R', r'')
    >>> patches3 = list(s3([
    ...     '  before\n',
    ...     '  start middle end\n',
    ...     '  after\n',
    ... ]))
    >>> len(patches3)
    1
    >>> p3 = patches3[0]
    >>> (p3.start_line_number, p3.end_line_number)
    (1, 3)
    >>> p3.new_lines
    ['  start middle   after\n']
    """
    if isinstance(regex, str):
        if ignore_case is False:
            regex = re.compile(regex, re.DOTALL | re.MULTILINE)
        else:
            regex = re.compile(
                regex,
                re.DOTALL | re.MULTILINE | re.IGNORECASE,
            )

    if isinstance(substitution, str):

        def substitution_func(match: re.Match):
            lines = match.expandf(substitution)
            lines = lines.splitlines(keepends=True)
            return lines
    else:
        substitution_func = substitution

    def suggestor(lines):
        pos = 0
        while True:
            match = regex.search("".join(lines), pos)
            if not match:
                break
            assert isinstance(match, re.Match)
            start_row, start_col = _index_to_row_col(lines, match.start())
            end_row, end_col = _index_to_row_col(lines, match.end())

            if substitution_func is None:
                new_lines = None
            else:
                new_lines = substitution_func(match)
                if len(new_lines) > 0:
                    new_lines[0] = lines[start_row][0:start_col] + new_lines[0]
                    new_lines[-1] = new_lines[-1] + lines[end_row][end_col:]
                else:
                    new_line = lines[start_row][0:start_col] + lines[end_row][end_col:]
                    if len(new_line) > 0:
                        new_lines = [new_line]

            yield Patch(
                start_line_number=start_row,
                end_line_number=end_row + 1,
                file_lines=lines,
                new_lines=new_lines,
            )
            # Advance past the end of the last match: No recursive matches
            pos = match.end()

    return suggestor


def _index_to_row_col(lines, index):
    r"""
    >>> lines = ['hello\n', 'world\n']
    >>> _index_to_row_col(lines, 0)
    (0, 0)
    >>> _index_to_row_col(lines, 6)
    (1, 0)
    >>> _index_to_row_col(lines, 7)
    (1, 1)
    """
    if index < 0:
        raise IndexError("negative index")
    current_index = 0
    for line_number, line in enumerate(lines):
        line_length = len(line)
        if current_index + line_length > index:
            return line_number, index - current_index
        current_index += line_length
    raise IndexError(f"index {index} out of range")


def print_patch(patch, lines_to_print, file_lines):
    """
    Prints a unified diff of the changes in the given Patch to the terminal,
    with line numbers and surrounding context.
    """
    end_line_number = patch.end_line_number
    if patch.new_lines is None:
        diff = [
            f"* {line}"
            for line in file_lines[patch.start_line_number : end_line_number]
        ]
    else:
        differ = Differ()
        if (
            len(patch.new_lines) == 0
            or len(patch.new_lines[-1]) == 0
            or patch.new_lines[-1][-1] != "\n"
        ) and len(file_lines) > end_line_number + 1:
            new_lines = patch.new_lines[:-1] + [
                patch.new_lines[-1] + file_lines[end_line_number]
            ]
            end_line_number += 1
        else:
            new_lines = patch.new_lines
        diff = list(
            differ.compare(
                file_lines[patch.start_line_number : end_line_number],
                new_lines,
            )
        )

    def _color(char):
        match char:
            case "-":
                return "RED"
            case "+":
                return "GREEN"
            case "?":
                return "GREY"
            case "*":
                return "YELLOW"
            case _:
                return "BLACK"

    num_lines = len(diff)
    size_of_context = max(0, lines_to_print - num_lines)
    size_of_up_context = int(ceil(size_of_context / 2))
    size_of_down_context = int(ceil(size_of_context / 2))
    start_context_line_number = max(patch.start_line_number - size_of_up_context, 0)
    end_context_line_number = min(
        end_line_number + size_of_down_context, len(file_lines)
    )
    print(
        "  "
        + "  ".join(file_lines[start_context_line_number : patch.start_line_number])
    )
    for line in diff:
        color = _color(line[0])
        terminal.terminal_print(line, color=color)
    print("  " + "  ".join(file_lines[end_line_number:end_context_line_number]))


def _ask_about_patch(query, patch, editor, default_no, yes_to_all):
    default_action = "n" if default_no else "y"
    terminal.terminal_clear()
    terminal.terminal_print(f"{patch.render_range()}\n", color="WHITE")
    print()

    with open(patch.path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    size = list(terminal.terminal_get_size())
    print_patch(patch, size[0] - 20, lines)

    print()

    if patch.new_lines is not None:
        if not yes_to_all:
            if default_no:
                print(
                    "Accept change (y = yes, n = no [default], e = edit, "
                    + "A = yes to all, E = yes+edit, q = quit)? "
                )
            else:
                print(
                    "Accept change (y = yes [default], n = no, e = edit, "
                    + "A = yes to all, E = yes+edit, q = quit)? "
                )
            p = _prompt("yneEAq", default=default_action)
        else:
            p = "y"
    else:
        print("(e = edit [default], n = skip line, q = quit)? ", end=" ")
        p = _prompt("enq", default="e")

    if p in "A":
        query.yes_to_all = True
        p = "y"
    if p in "yE":
        lines = patch.apply_to(lines)
        _save(patch.path, lines)
    if p in "eE":
        run_editor(patch.start_position, editor)
    if p in "q":
        sys.exit(0)


def _prompt(letters="yn", default=None):
    """
    Wait for the user to type a character (and hit Enter).  If the user enters
    one of the characters in `letters`, return that character.  If the user
    hits Enter without entering a character, and `default` is specified,
    returns `default`.  Otherwise, asks the user to enter a character again.
    """
    while True:
        try:
            input_text = sys.stdin.readline().strip()
        except KeyboardInterrupt:
            sys.exit(0)
        if input_text and input_text in letters:
            return input_text
        if default is not None and input_text == "":
            return default
        print("Come again?")


def _save(path, lines):
    with open(path, "w", encoding="utf-8") as file_w:
        file_w.writelines(lines)


def run_editor(position, editor=None):
    editor = editor or os.environ.get("EDITOR") or "vim"
    os.system(f"{editor} +{position.line_number+1} {position.path}")


#
# Bookmarking functions.  codemod2 saves a file called .codemod2.bookmark to
# keep track of where you were the last time you exited in the middle of
# an interactive session.
#


def _save_bookmark(position):
    with open(".codemod2.bookmark", "w", encoding="utf-8") as file_w:
        file_w.write(str(position))


def _load_bookmark():
    try:
        with open(".codemod2.bookmark", "r", encoding="utf-8") as bookmark_file:
            contents = bookmark_file.readline().strip()
            return Position(contents)
    except IOError:
        return None


def _delete_bookmark():
    try:
        os.remove(".codemod2.bookmark")
    except OSError:
        pass  # file didn't exist


#
# Code to make this run as an executable from the command line.
#


def _parse_command_line():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            r"""
            codemod2.py is a tool/library to assist you with large-scale
            codebase refactors
            that can be partially automated but still require
            human oversight and
            occasional intervention.

            Example: Let's say you're deprecating your use
            of the <font> tag.  From the
            command line, you might make progress by running:

              codemod2.py -m -d /home/modrohmann/www --extensions py,html \
                         '<font *color="?(.*?)"?>(.*?)</font>' \
                         '<span style="color: \1;">\2</span>'

            For each match of the regex, you'll be shown a colored diff,
            and asked if you
            want to accept the change (the replacement of
                                       the <font> tag with a <span>
            tag), reject it, or edit the line in question
            in your $EDITOR of choice.
            """
        ),
        epilog=textwrap.dedent(
            r"""
            You can also use codemod2 for transformations that are much
            more sophisticated
            than regular expression substitution.  Rather than using
            the command line, you
            write Python code that looks like:

              import codemod2
              query = codemod2.Query(...)
              run_interactive(query)

            See the documentation for the Query class for details.

            @author Justin Rosenstein
            """
        ),
    )

    parser.add_argument(
        "-m",
        action="store_true",
        help="Have regex work over multiple lines "
        "(e.g. have dot match newlines). "
        "By default, codemod2 applies the regex one "
        "line at a time.",
    )
    parser.add_argument(
        "-d",
        action="store",
        type=str,
        default=".",
        help="The path whose descendent files "
        "are to be explored. "
        "Defaults to current dir.",
    )
    parser.add_argument(
        "-i", action="store_true", help="Perform case-insensitive search."
    )

    parser.add_argument(
        "--start",
        action="store",
        type=str,
        help="A path:line_number-formatted position somewhere"
        " in the hierarchy from which to being exploring,"
        'or a percentage (e.g. "--start 25%%") of '
        "the way through to start."
        "Useful if you're divvying up the "
        "substitution task across multiple people.",
    )
    parser.add_argument(
        "--end",
        action="store",
        type=str,
        help="A path:line_number-formatted position "
        "somewhere in the hierarchy just *before* "
        "which we should stop exploring, "
        "or a percentage of the way through, "
        "just before which to end.",
    )

    parser.add_argument(
        "--extensions",
        action="store",
        default="*",
        type=str,
        help="A comma-delimited list of file extensions "
        "to process. Also supports Unix pattern "
        "matching.",
    )
    parser.add_argument(
        "--include-extensionless",
        action="store_true",
        help="If set, this will check files without "
        "an extension, along with any matching file "
        "extensions passed in --extensions",
    )
    parser.add_argument(
        "--exclude-paths",
        action="store",
        type=str,
        help="A comma-delimited list of paths to exclude.",
    )

    parser.add_argument(
        "--accept-all",
        action="store_true",
        help="Automatically accept all " "changes (use with caution).",
    )

    parser.add_argument(
        "--default-no",
        action="store_true",
        help="If set, this will make the default " "option to not accept the change.",
    )

    parser.add_argument(
        "--editor",
        action="store",
        type=str,
        help='Specify an editor, e.g. "vim" or emacs". '
        "If omitted, defaults to $EDITOR environment "
        "variable.",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Don't run normally.  Instead, just print "
        "out number of times places in the codebase "
        "where the 'query' matches.",
    )
    parser.add_argument(
        "match",
        nargs="?",
        action="store",
        type=str,
        help="Regular expression to match.",
    )
    parser.add_argument(
        "subst",
        nargs="?",
        action="store",
        type=str,
        help="Substitution to replace with.",
    )

    arguments = parser.parse_args()
    if not arguments.match:
        parser.exit(0, parser.format_usage())

    query_options = {}
    query_options["yes_to_all"] = arguments.accept_all

    query_options["suggestor"] = (
        multiline_regex_suggestor if arguments.m else regex_suggestor
    )(arguments.match, arguments.subst, arguments.i)

    query_options["start"] = arguments.start
    query_options["end"] = arguments.end
    query_options["root_directory"] = arguments.d
    query_options["inc_extensionless"] = arguments.include_extensionless

    if arguments.exclude_paths is not None:
        exclude_paths = arguments.exclude_paths.split(",")
    else:
        exclude_paths = None
    query_options["path_filter"] = helpers.path_filter(
        arguments.extensions.split(","), exclude_paths
    )

    options = {}
    options["query"] = Query(**query_options)
    if arguments.editor is not None:
        options["editor"] = arguments.editor
    options["just_count"] = arguments.count
    options["default_no"] = arguments.default_no

    return options


def main():
    options = _parse_command_line()
    run_interactive(**options)


if __name__ == "__main__":
    main()
