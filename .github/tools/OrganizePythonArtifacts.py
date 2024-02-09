# ----------------------------------------------------------------------
# |
# |  OrganizePythonArtifacts.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-01-27 19:54:52
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Organizes artifacts into a format suitable for publishing."""

import os
import re
import shutil
import textwrap

from pathlib import Path
from typing import Annotated, Optional

import typer

from dbrownell_Common.InflectEx import inflect  # type: ignore [import-untyped]
from dbrownell_Common import PathEx  # type: ignore [import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager  # type: ignore [import-untyped]
from typer.core import TyperGroup  # type: ignore [import-untyped]


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
@app.command("Organize")
def Organize(
    stage_dir: Annotated[
        Path,
        typer.Argument(
            file_okay=False,
            exists=True,
            resolve_path=True,
            help="Artifacts directory.",
        ),
    ],
    dest_dir: Annotated[
        Path,
        typer.Argument(
            file_okay=False,
            resolve_path=True,
            help="Destination directory.",
        ),
    ],
) -> None:
    with DoneManager.CreateCommandLine() as dm:
        all_filenames: list[Path] = []

        with dm.Nested(
            "Collecting build artifacts...",
            lambda: "{} found".format(inflect.no("file", len(all_filenames))),
        ):
            for root, _, walk_filenames in os.walk(stage_dir):
                if not walk_filenames:
                    continue

                root_path = Path(root)

                for walk_filename in walk_filenames:
                    all_filenames.append(root_path / walk_filename)

        # Organize the files
        wheel_version: Optional[str] = None
        all_files: dict[str, list[Path]] = {}

        with dm.Nested("Organizing files...") as organize_dm:
            python_version_regex = re.compile(r"^.+-(?P<version>.+?)-py.+$")

            for filename in all_filenames:
                all_files.setdefault(filename.name, []).append(filename)

                if filename.suffix == ".whl":
                    match = python_version_regex.match(filename.name)
                    if match is None:
                        organize_dm.WriteError(
                            "The wheel filename '{}' is not in the expected format.\n".format(
                                filename.name
                            )
                        )
                        continue

                    this_version = match.group("version")

                    if wheel_version is None:
                        wheel_version = this_version
                    elif this_version != wheel_version:
                        organize_dm.WriteError(
                            "The wheel version '{}' in '{}' does not match '{}'.\n".format(
                                this_version,
                                filename.name,
                                wheel_version,
                            )
                        )

            for filenames in all_files.values():
                filenames.sort(key=lambda f: f.stat().st_size)

        with dm.Nested("Copying files...") as copy_dm:
            dest_dir.mkdir(parents=True, exist_ok=True)

            for filenames in all_files.values():
                filename = filenames[0]

                with copy_dm.Nested("Copying '{}'...".format(filename.name)) as this_copy_dm:
                    shutil.copyfile(filename, dest_dir / filename.name)

                    if len(filenames) > 1:
                        this_copy_dm.WriteInfo(
                            textwrap.dedent(
                                """\
                                Multiple files were found for '{}' (the first file will be copied):
                                {}
                                """,
                            ).format(
                                filename.name,
                                "\n".join(
                                    "    {}) [{}] {}".format(index + 1, PathEx.GetSizeDisplay(f), f)
                                    for index, f in enumerate(filenames)
                                ),
                            ),
                        )

        with dm.Nested("Creating Version file...") as version_dm:
            version_filename = dest_dir / "__version__"

            if version_filename.is_file():
                version_dm.WriteError("The file '{}' already exists.\n".format(version_filename))
            else:
                with version_filename.open("w") as f:
                    f.write(str(wheel_version))


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
