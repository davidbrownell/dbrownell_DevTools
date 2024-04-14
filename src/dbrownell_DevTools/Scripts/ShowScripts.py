# ----------------------------------------------------------------------
# |
# |  ShowScripts.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-04-13 23:24:19
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Show all python scripts available by the activated repository."""

import os

from pathlib import Path
from typing import Annotated

import typer

from dbrownell_Common.InflectEx import inflect  # type: ignore[import-untyped]
from dbrownell_Common import PathEx  # type: ignore[import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags  # type: ignore[import-untyped]
from rich import print as rich_print
from rich.columns import Columns
from typer.core import TyperGroup


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # pylint: disable=missing-class-docstring
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs):  # pylint: disable=unused-argument
        return self.commands.keys()


# ----------------------------------------------------------------------
app = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
@app.command("EntryPoint", help=__doc__, no_args_is_help=False)
def EntryPoint(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        binary_files: list[str] = []

        with dm.Nested(
            "Searching for binary files...",
            lambda: "{} found".format(inflect.no("binary file", len(binary_files))),
        ):
            env_var = os.getenv("PYTHON_BOOTSTRAPPER_GENERATED_DIR")
            assert env_var is not None

            generated_dir = Path(env_var)

            if os.name == "nt":
                scripts_dir = PathEx.EnsureDir(generated_dir / "Scripts")

                for child in scripts_dir.iterdir():
                    if child.is_file() and child.suffix == ".exe":
                        binary_files.append(child.stem)

            else:
                scripts_dir = PathEx.EnsureDir(generated_dir / "bin")

                for child in scripts_dir.iterdir():
                    if child.is_file() and child.stat().st_mode & os.X_OK:
                        binary_files.append(child.name)

        dm.WriteLine("\n\n")

        rich_print(
            Columns(
                binary_files,
                equal=True,
                expand=True,
                column_first=True,
            ),
        )

        dm.WriteLine("\n\n")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
