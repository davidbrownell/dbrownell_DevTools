# ----------------------------------------------------------------------
# |
# |  MatchTests.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-04-13 12:23:56
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Matches tests with source files."""

import os
import re

from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Annotated, Optional, Protocol

import typer

from dbrownell_Common.InflectEx import inflect  # type: ignore[import-untyped]
from dbrownell_Common import PathEx  # type: ignore[import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags  # type: ignore[import-untyped]
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
@app.command("MatchTests", help=__doc__, no_args_is_help=False)
def MatchTests(
    working_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            resolve_path=True,
            help="The directory to search for source and test files.",
        ),
    ] = Path.cwd(),
    include_globs: Annotated[
        list[str],
        typer.Option("--include", help="Glob pattern for source files to include."),
    ] = [],
    exclude_globs: Annotated[
        list[str],
        typer.Option("--exclude", help="Glob pattern for source files to exclude."),
    ] = [],
    source_dir_name: Annotated[
        str,
        typer.Option("--src-dir-name", help="The name of the source directory."),
    ] = "src",
    test_dir_name: Annotated[
        str,
        typer.Option("--test-dir-name", help="The name of the test directory."),
    ] = "tests",
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
        # Get the source dir
        source_dir = working_dir / source_dir_name
        if not source_dir.is_dir():
            dm.WriteError(f"The source directory '{source_dir}' does not exist.\n")
            return

        # Look for the code dir under this dir
        subdirs: list[Path] = [
            child
            for child in source_dir.iterdir()
            if child.is_dir() and not child.name.endswith(".egg-info")
        ]

        if len(subdirs) == 1:
            source_dir = subdirs[0]

        # Get the source files
        source_files: dict[PurePath, Path] = {}

        with dm.Nested(
            f"Collecting source files in '{source_dir}'...",
            lambda: "{} found".format(inflect.no("file", len(source_files))),
        ):
            for source_file in _CollectFiles(
                source_dir,
                include_globs,
                exclude_globs,
            ):
                source_files[PathEx.CreateRelativePath(source_dir, source_file)] = source_file

        for func in _TEST_DISCOVERY_FUNCTIONS:
            test_file_infos = func(dm, working_dir, source_dir, test_dir_name)
            if test_file_infos is None:
                continue

            # Organize the tests
            test_files: dict[PurePath, _TestInfo] = {}

            for tfi in test_file_infos:
                test_files[tfi.source_filename] = tfi

            # Match the source and tests
            matched: dict[PurePath, Optional[PurePath]] = {}

            with dm.Nested("Matching tests..."):
                for relative_path in source_files.keys():
                    matching_test = test_files.pop(relative_path, None)

                    if matching_test is None:
                        matched[relative_path] = None
                    else:
                        matched[relative_path] = matching_test.relative_filename

            # Display the results
            dm.WriteLine("")

            if dm.is_verbose:
                matched_count = 0

                with dm.Nested(
                    "Matched tests...",
                    lambda: "{} matched".format(inflect.no("test", matched_count)),
                    suffix="\n",
                ) as matching_dm:
                    for source_file, test_file in matched.items():
                        if test_file is not None:
                            matching_dm.WriteLine(f"{source_file} ->\n{test_file}\n\n")
                            matched_count += 1

            # Missing
            missing_tests: list[PurePath] = []

            for source_file, test_file in matched.items():
                if test_file is None:
                    missing_tests.append(source_file)

            if missing_tests:
                with dm.Nested(
                    "{} missing tests...".format(inflect.no("source file", len(missing_tests))),
                    suffix="\n",
                ) as missing_dm:
                    for source_file in missing_tests:
                        missing_dm.WriteError(f"{source_file}\n")

            # Orphaned
            if test_files:
                with dm.Nested(
                    "{}...".format(inflect.no("orphaned test", len(test_files))),
                    suffix="\n",
                ) as orphaned_dm:
                    for tfi in test_files.values():
                        orphaned_dm.WriteError(f"{tfi.test_filename}\n")

            return

        # If here, we couldn't discover the tests
        dm.WriteError("Unable to discover tests.\n")


# ----------------------------------------------------------------------
# |
# |  Private Types
# |
# ----------------------------------------------------------------------
@dataclass
class _TestInfo:
    test_filename: Path
    relative_filename: PurePath
    source_filename: PurePath


# ----------------------------------------------------------------------
class _TestDiscoveryFunction(Protocol):
    def __call__(
        self,
        dm: DoneManager,
        working_dir: Path,
        source_dir: Path,
        test_dir_name: str,
    ) -> Optional[list[_TestInfo]]: ...


# ----------------------------------------------------------------------
# |
# |  Private Functions
# |
# ----------------------------------------------------------------------
def _TestDirDiscovery(
    dm: DoneManager,
    working_dir: Path,
    source_dir: Path,  # pylint: disable=unused-argument
    test_dir_name: str,
) -> Optional[list[_TestInfo]]:
    tests_dir = working_dir / test_dir_name
    if not tests_dir.is_dir():
        return None

    results: list[_TestInfo] = []

    with dm.Nested(
        f"Collecting test files in '{tests_dir}'...",
        lambda: "{} found".format(inflect.no("file", len(results))),
    ):
        test_filename_regex = re.compile(r"^(?P<name>.+)_(?P<testtype>.+)Test\.py$")

        for filename in _CollectFiles(tests_dir):
            relative_path = PathEx.CreateRelativePath(tests_dir, filename)

            match = test_filename_regex.match(relative_path.name)
            if match:
                source_path = relative_path.parent / f"{match.group('name')}.py"
            else:
                source_path = relative_path

            results.append(_TestInfo(filename, relative_path, source_path))

    return results


# ----------------------------------------------------------------------
def _CollectFiles(
    path: Path,
    include_globs: Optional[list[str]] = None,
    exclude_globs: Optional[list[str]] = None,
) -> list[Path]:
    results: list[Path] = []

    for root, _, filenames in os.walk(path):
        if not filenames:
            continue

        root_path = Path(root)

        for filename in filenames:
            fullpath = root_path / filename

            if fullpath.suffix != ".py":
                continue

            if fullpath.name == "__init__.py":
                continue

            if (exclude_globs and any(fullpath.match(glob) for glob in exclude_globs)) or (
                (include_globs and not any(fullpath.match(glob) for glob in include_globs))
            ):
                continue

            results.append(fullpath)

    return results


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
_TEST_DISCOVERY_FUNCTIONS: list[_TestDiscoveryFunction] = [
    _TestDirDiscovery,
]


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
