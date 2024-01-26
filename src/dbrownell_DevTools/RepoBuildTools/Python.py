# ----------------------------------------------------------------------
# |
# |  Python.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-01-19 14:04:48
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Implement tasks used when working with Python repositories."""

import re

from pathlib import Path
from typing import Annotated, Callable, Optional

from dbrownell_Common import PathEx
from dbrownell_Common.Streams.DoneManager import (
    DoneManager,
    DoneManagerException,
    Flags as DoneManagerFlags,
)
from dbrownell_Common import SubprocessEx

import typer


# ----------------------------------------------------------------------
# |
# |  Private Types
# |
# ----------------------------------------------------------------------
_verbose_typer_option = typer.Option("--verbose", help="Write verbose information to the terminal.")
_debug_typer_option = typer.Option("--debug", help="Write debug information to the terminal.")


# ----------------------------------------------------------------------
# |
# |  Public Functions
# |
# ----------------------------------------------------------------------
def BlackFuncFactory(
    source_root: Path,
    app: typer.Typer,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("Black", no_args_is_help=False)
    def Black(
        format: Annotated[  # pylint: disable=redefined-builtin
            bool,
            typer.Option(
                "--format",
                help="Format the files; the default behavior checks if any files need to be formatted.",
            ),
        ] = False,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Runs black on the python code."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            with dm.Nested("Running black...") as black_dm:
                command_line = "black {}{}{}".format(
                    "" if format else "--check ",
                    "--verbose " if verbose else "",
                    "" if source_root is None else '"{}"'.format(source_root),
                )

                black_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

                with black_dm.YieldStream() as stream:
                    black_dm.result = SubprocessEx.Stream(command_line, stream)
                    if black_dm.result != 0:
                        return

    # ----------------------------------------------------------------------

    return Black


# ----------------------------------------------------------------------
def PylintFuncFactory(
    source_root: Path,
    app: typer.Typer,
    default_min_score: float = 9.5,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("Pylint", no_args_is_help=False)
    def Pylint(
        min_score: Annotated[
            float,
            typer.Option(
                "--min-score",
                min=0.0,
                max=10.0,
                help="Fail if the total score is less than this value.",
            ),
        ] = default_min_score,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Runs pylint on the python code."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            with dm.Nested("Running pylint...") as pylint_dm:
                command_line = 'pylint {}{} "{}"'.format(
                    "--fail-under={} ".format(min_score),
                    "--verbose " if verbose else "",
                    source_root,
                )

                pylint_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

                with pylint_dm.YieldStream() as stream:
                    pylint_dm.result = SubprocessEx.Stream(command_line, stream)
                    if pylint_dm.result != 0:
                        return

    # ----------------------------------------------------------------------

    return Pylint


# ----------------------------------------------------------------------
def PytestFuncFactory(
    test_root: Path,
    cov_name: str,
    app: typer.Typer,
    default_min_coverage: float = 95.0,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("Pytest", no_args_is_help=False)
    def Pytest(
        code_coverage: Annotated[
            bool,
            typer.Option("--code-coverage", help="Run tests with code coverage information."),
        ] = False,
        min_coverage: Annotated[
            Optional[float],
            typer.Option(
                "--min-coverage",
                min=0.0,
                max=100.0,
                help="Fail if the code coverage percentage is less than this value.",
            ),
        ] = None,
        benchmark: Annotated[
            bool,
            typer.Option("--benchmark", help="Run benchmark tests in addition to other tests."),
        ] = False,
        pytest_args: Annotated[
            Optional[str],
            typer.Option("--pytest-args", help="Additional arguments passed to pytest."),
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Runs pytest on the python tests."""

        if code_coverage:
            min_coverage = min_coverage or default_min_coverage

        del code_coverage

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            with dm.Nested("Running pytest...") as pytest_dm:
                command_line = "pytest {}{} --capture=no --verbose -vv {} .".format(
                    "--benchmark-skip " if not benchmark else "",
                    (
                        ""
                        if min_coverage is None
                        else "--cov={} --cov-fail-under={} ".format(cov_name, min_coverage)
                    ),
                    pytest_args or "",
                )

                pytest_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

                with pytest_dm.YieldStream() as stream:
                    pytest_dm.result = SubprocessEx.Stream(
                        command_line,
                        stream,
                        cwd=test_root,
                    )
                    if pytest_dm.result != 0:
                        return

    # ----------------------------------------------------------------------

    return Pytest


# ----------------------------------------------------------------------
def UpdateVersionFuncFactory(
    source_root: Path,
    init_filename: Path,
    app: typer.Typer,
) -> Callable:
    assert source_root.is_dir(), source_root
    assert init_filename.is_file(), init_filename
    assert PathEx.IsDescendant(init_filename, source_root), (init_filename, source_root)

    # ----------------------------------------------------------------------
    @app.command("UpdateVersion", no_args_is_help=False)
    def UpdateVersion(
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Updates the version of the python package."""

        pass

    # ----------------------------------------------------------------------

    return UpdateVersion


# ----------------------------------------------------------------------
def PackageFuncFactory(
    source_root: Path,
    app: typer.Typer,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("Package", no_args_is_help=False)
    def Package(
        additional_args: Annotated[
            Optional[list[str]],
            typer.Option("--arg", help="Additional arguments passed to the build command."),
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Builds the python package."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            with dm.Nested("Packaging...") as package_dm:
                command_line = "python -m build {}".format(
                    ""
                    if not additional_args
                    else " ".join('"{}"'.format(arg) for arg in additional_args)
                )

                package_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

                with package_dm.YieldStream() as stream:
                    package_dm.result = SubprocessEx.Stream(
                        command_line,
                        stream,
                        cwd=source_root,
                    )
                    if package_dm.result != 0:
                        return

    # ----------------------------------------------------------------------

    return Package


# ----------------------------------------------------------------------
def PublishFuncFactory(
    source_root: Path,
    app: typer.Typer,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("Publish", no_args_is_help=False)
    def Publish(
        pypi_api_token: Annotated[
            str,
            typer.Argument(
                help="API token (generated on PyPi.org or test.PyPi.org); the token should be scoped to this project only."
            ),
        ],
        production: Annotated[
            bool,
            typer.Option("--production", help="Push to the PyPi.org rather than test.PyPi.org."),
        ] = False,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Publishes the python package."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            dist_dir = source_root / "dist"

            if not dist_dir.is_dir():
                raise DoneManagerException(
                    "The distribution directory '{}' does not exist. Please run this script with the 'Package' argument to create it.".format(
                        dist_dir,
                    ),
                )

            if production:
                repository_url = "https://upload.PyPi.org/legacy/"
            else:
                repository_url = "https://test.PyPi.org/legacy/"

            with dm.Nested("Publishing to '{}'...".format(repository_url)) as publish_dm:
                command_line = 'twine upload --repository-url {} --username __token__ --password {} --non-interactive --disable-progress-bar {} "dist/*.whl"'.format(
                    repository_url,
                    pypi_api_token,
                    "--verbose" if publish_dm.is_verbose else "",
                )

                publish_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

                with publish_dm.YieldStream() as stream:
                    publish_dm.result = SubprocessEx.Stream(
                        command_line,
                        stream,
                        cwd=source_root,
                    )
                    if publish_dm.result != 0:
                        return

    # ----------------------------------------------------------------------

    return Publish
