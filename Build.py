# ----------------------------------------------------------------------
# |
# |  Build.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-12-23 12:50:20
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Build tasks for this python module."""

import sys

from pathlib import Path

import typer

from dbrownell_DevTools.RepoBuildTools import Python as RepoBuildTools
from typer.core import TyperGroup


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # pylint: disable=missing-class-docstring
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs):  # pylint: disable=unused-argument
        return self.commands.keys()


# ----------------------------------------------------------------------
this_dir = Path(__file__).parent
assert this_dir.is_dir(), this_dir

src_dir = this_dir / "src" / "dbrownell_DevTools"
assert src_dir.is_dir(), src_dir

tests_dir = this_dir / "tests"
assert tests_dir.is_dir(), tests_dir

app = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
Black = RepoBuildTools.BlackFuncFactory(this_dir, app)
Pylint = RepoBuildTools.PylintFuncFactory(src_dir, app)
Pytest = RepoBuildTools.PytestFuncFactory(
    tests_dir, "dbrownell_DevTools", app, default_min_coverage=50.0
)
UpdateVersion = RepoBuildTools.UpdateVersionFuncFactory(src_dir, app)
Package = RepoBuildTools.PackageFuncFactory(this_dir, app)
Publish = RepoBuildTools.PublishFuncFactory(this_dir, app)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(app())
