# codemod2

[![PyPI](https://img.shields.io/pypi/v/codemod2.svg)](https://pypi.python.org/pypi/codemod2)
[![downloads](https://img.shields.io/pypi/dw/codemod2.svg)](https://pypi.python.org/pypi/codemod2)


## Overview

codemod2 is a tool/library to assist you with large-scale codebase refactors that can be partially automated but still require human oversight and occasional intervention.  This is a FORK of the retired codemod cli tools developed by Justin Rosenstein at Facebook.

Example: Let's say you're deprecating your use of the `<font>` tag.  From the command line, you might make progress by running:

    codemod2 -m -d /home/mdrohmann/www --extensions py,html \
        '<font *color="?(.*?)"?>(.*?)</font>' \
        '<span style="color: {1};">\2</span>'

For each match of the regex, you'll be shown a colored diff, and asked if you want to accept the change (the replacement of the `<font>` tag with a `<span>` tag), reject it, or edit the line in question in your `$EDITOR` of choice.

### Motivation for the fork

Most programming languages have some kind of balanced parantheses or brackets.
PCRE2 regular expressions can help for such a use case.  In my specific case, I
wanted to wrap Python dictionaries in a specific type constructor in some
contexts.

The following codemod2 regular expression accomplishes this:

    codemod2 -m 'context=(?<expr>\{(?:[^}{]+|(?P>expr))*+\})' 'context=DictConstructor({1})'


Note, that the substitution string is a Python format string now, because
codemod uses the [regex](https://pypi.org/project/regex/) package instead of
the standard lib `re` package.

The diff output is also improved and now uses the routines from the `difflib`
library to display changes.

### Alternatives

There are more sophisticated solutions to modifying your code base that are based on parsing an abstract or concrete syntax tree representation of your code.  Examples in the Python space are [rope](https://github.com/python-rope/rope) and [libCST](https://github.com/Instagram/LibCST).  In Golang, there are tools like [eg] (https://github.com/golang/tools/blob/master/refactor/eg/eg.go) and [rf](https://pkg.go.dev/rsc.io/rf).

All of the above may work more reliably for the use-cases they provide solutions for.  But in my own experience, I often got disappointed after going through the process of

* finding the tool that works for the use-case
* understanding its usage, and
* applying it to my use-case.

Consider that refactors usually are simple tasks, and when assessing the
efficacy of a tool and you are working on a small to medium sized code-base, you
have to weigh the above investment against the option to just slog through it
for half an hour with a cup of coffee, applying all the changes with your
favorite editor manually until the linter and test checks are happy again.  This
tool is simple, but generic and regular expressions are widely known, such that
many members of your team can use and understand them.

So, compared to most alternatives, this is where codemod2 shines:

* Easy on-boarding if you knw regular expressions: no need to learn new syntax
* Capabilities and limitations of codemod2 are easy to understand

## Install

In a virtual environment or as admin user

`pip install codemod2`

or with pipx

`pipx install codemod2`

## Usage

The last two arguments are a regular expression to match and a substitution string, respectively.  Or you can omit the substitution string, and just be prompted on each match for whether you want to edit in your editor.

Options (all optional) include:

    -m
      Have regex work over multiple lines (e.g. have dot match newlines).  By
      default, codemod2 applies the regex one line at a time.
    -d
      The path whose ancestor files are to be explored.  Defaults to current dir.
    -i
      Make your search case-insensitive
    --start
      A path:line_number-formatted position somewhere in the hierarchy from which
      to being exploring, or a percentage (e.g. "--start 25%") of the way through
      to start.  Useful if you're divvying up the substitution task across
      multiple people.
    --end
      A path:line_number-formatted position somewhere in the hierarchy just
      *before* which we should stop exploring, or a percentage of the way
      through, just before which to end.
    --extensions
      A comma-delimited list of file extensions to process. Also supports Unix
      pattern matching.
    --include-extensionless
      If set, this will check files without an extension, along with any
      matching file extensions passed in --extensions
    --accept-all
      Automatically accept all changes (use with caution)
    --default-no
      Set default behavior to reject the change.
    --editor
      Specify an editor, e.g. "vim" or "emacs".  If omitted, defaults to $EDITOR
      environment variable.
    --count
      Don't run normally.  Instead, just print out number of times places in the
      codebase where the 'query' matches.
    --test
      Don't run normally.  Instead, just run the unit tests embedded in the
      codemod2 library.

You can also use codemod for transformations that are much more sophisticated
than regular expression substitution.  Rather than using the command line, you
write Python code that looks like:

    from codemod2 import run_interactive, Query
    run_interactive(Query(...))

See the documentation for the Query class for details if you want to try it.


## Dependencies

* python2
* regex

## Credits

Copyright (c) 2024 Martin Drohmann.

Copyright (c) 2007-2008 Facebook.

Created by Justin Rosenstein.

Licensed under the Apache License, Version 2.0.

