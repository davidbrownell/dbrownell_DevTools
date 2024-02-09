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
import shutil

from pathlib import Path
from typing import Annotated

import typer

from dbrownell_Common.InflectEx import inflect  # type: ignore [import-untyped]
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
                    fullpath = root_path / directory

                    match = regex.match(directory)
                    if match:
                        all_directories.append(fullpath)
                    else:
                        children = list(fullpath.iterdir())

                        # Are we looking at the scenario where we have multiple binaries? If so,
                        # rename the exe directory so that it includes the name of the binary.
                        if (
                            len(children) == 1
                            and children[0].is_dir()
                            and regex.match(children[0].name)
                        ):
                            renamed_directory = root_path / "{}-{}".format(
                                directory, children[0].name
                            )

                            shutil.move(children[0], renamed_directory)
                            all_directories.append(renamed_directory)

            if not all_directories:
                collect_dm.WriteError("No directories were found.\n")
                return

        with dm.Nested(
            "Creating {}...".format(inflect.no("archive", len(all_directories)))
        ) as archive_dm:
            if os.name == "nt":
                command_line_template = r'PowerShell -Command "Compress-Archive -Path {src}\* -DestinationPath {dst}.zip"'
            else:
                command_line_template = 'tar --create "--file={dst}.tar.gz" --gzip --verbose *'

            output_dir.mkdir(parents=True, exist_ok=True)

            for index, source_dir in enumerate(all_directories):
                with archive_dm.Nested(
                    "Processing '{}' ({} of {})...".format(
                        source_dir.name,
                        index + 1,
                        len(all_directories),
                    )
                ) as this_dm:
                    command_line = command_line_template.format(
                        src=source_dir,
                        dst=output_dir / source_dir.parts[-1],
                    )

                    this_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

                    with this_dm.YieldStream() as stream:
                        this_dm.result = SubprocessEx.Stream(
                            command_line,
                            stream,
                            cwd=source_dir,
                        )

                        if this_dm.result != 0:
                            return


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
