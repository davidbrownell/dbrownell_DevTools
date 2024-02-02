# ----------------------------------------------------------------------
# |
# |  CreatePythonBinaryArchive.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-02-01 18:18:28
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Searches for a python binary output directory and then creates an archive from it."""

import os
import re

from pathlib import Path
from typing import Annotated

import typer

from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags  # type: ignore [import-untyped]
from dbrownell_Common import SubprocessEx  # type: ignore [import-untyped]
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
@app.command("CreateArchive", no_args_is_help=False)
def CreateArchive(
    output_dir: Annotated[
        Path,
        typer.Argument(file_okay=False, resolve_path=True, help="Output directory."),
    ],
) -> None:
    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=True, debug=False),
    ) as dm:
        this_dir = Path(__file__).parent

        all_directories: list[Path] = []

        with dm.Nested("Collecting binary directories...") as collect_dm:
            regex = re.compile(r"^exe\..+?-\d+\.\d+$")

            for root, directories, _ in os.walk(this_dir / "build"):
                if not directories:
                    continue

                root_path = Path(root)

                for directory in directories:
                    match = regex.match(directory)
                    if match:
                        all_directories.append(root_path / directory)

            if not all_directories:
                collect_dm.WriteError("No directories were found.\n")
                return

            if len(all_directories) > 1:
                collect_dm.WriteError(
                    "{} directories were found, but only 1 was expected.\n".format(
                        len(all_directories)
                    )
                )
                return

        with dm.Nested("Creating archive...") as archive_dm:
            source_dir = all_directories[0]

            if os.name == "nt":
                command_line = r'PowerShell -Command "Compress-Archive -Path {}\* -DestinationPath {}.zip"'.format(
                    source_dir, output_dir / source_dir.parts[-1]
                )
            else:
                command_line = 'tar --create "--file={}.tar.gz" --gzip --verbose *'.format(
                    output_dir / source_dir.parts[-1]
                )

            archive_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

            output_dir.mkdir(parents=True, exist_ok=True)

            with archive_dm.YieldStream() as stream:
                archive_dm.result = SubprocessEx.Stream(
                    command_line,
                    stream,
                    cwd=source_dir,
                )

                if archive_dm.result != 0:
                    return


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
