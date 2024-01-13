codemod
=======

[![PyPI](https://img.shields.io/pypi/v/codemod2.svg)](https://pypi.python.org/pypi/codemod2)
[![downloads](https://img.shields.io/pypi/dw/codemod2.svg)](https://pypi.python.org/pypi/codemod2)


Overview
--------

codemod2 is a tool/library to assist you with large-scale codebase refactors that can be partially automated but still require human oversight and occasional intervention.

Example: Let's say you're deprecating your use of the `<font>` tag.  From the command line, you might make progress by running:

    codemod2 -m -d /home/mdrohmann/www --extensions php,html \
        '<font *color="?(.*?)"?>(.*?)</font>' \
        '<span style="color: \1;">\2</span>'

For each match of the regex, you'll be shown a colored diff, and asked if you want to accept the change (the replacement of the `<font>` tag with a `<span>` tag), reject it, or edit the line in question in your `$EDITOR` of choice.

Install
-------
In a virtual environment or as admin user

`pip install codemod2`

or with pipx

`pipx install codemod2`

Usage
-----

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

You can also use codemod for transformations that are much more sophisticated than regular expression substitution.  Rather than using the command line, you write Python code that looks like:

    import codemod2
    codemod2.Query(...).run_interactive()

Note:  I didn't test yet, that the Query object still works.

See the documentation for the Query class for details if you want to try it.

Motivation for the fork
-----------------------

Most programming languages have some kind of balanced parantheses or brackets.
PCRE2 regular expressions can help for such a use case.  In my specific case, I
wanted to wrap Python dictionaries in a specific type constructor in some
contexts.

The following codemod2 regular expression accomplishes this:

    codemod2 -m 'context=(?<expr>\{(?:[^}{]+|(?P>expr))*+\})' 'context=DictConstructor($1)'

Dependencies
------------

* python2
* pcre2

Credits
-------

Copyright (c) 2024 Martin Drohmann.

Copyright (c) 2007-2008 Facebook.

Created by Justin Rosenstein.

Licensed under the Apache License, Version 2.0.

