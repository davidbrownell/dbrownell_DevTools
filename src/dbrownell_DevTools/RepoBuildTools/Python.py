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
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Implement tasks used when working with Python repositories."""

import re

from enum import Enum
from pathlib import Path
from typing import Annotated, Callable, Optional

from dbrownell_Common import PathEx  # type: ignore [import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags  # type: ignore [import-untyped]
from semantic_version import Version as SemVer  # type: ignore [import-untyped]
import typer

from dbrownell_DevTools import BuildActivities
from dbrownell_DevTools import PythonBuildActivities


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
    repo_root: Path,  # given /src/<package_name>, repo_root is /
    app: typer.Typer,
    additional_args: Optional[str] = None,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("black", no_args_is_help=False)
    def Black(
        format: Annotated[  # pylint: disable=redefined-builtin
            bool,
            typer.Option(
                "--format",
                help="Format the files; the default behavior checks if any files need to be formatted.",
            ),
        ] = False,
        black_args: Annotated[
            Optional[str],
            typer.Option(
                "--args",
                help="Additional arguments passed to black.",
            ),
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Runs black on the python code."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            args = []

            if additional_args:
                args.append(additional_args)
            if black_args:
                args.append(black_args)

            optional_args = " ".join(args) if args else None

            PythonBuildActivities.Black(
                dm,
                repo_root,
                format_sources=format,
                args=optional_args,
            )

    # ----------------------------------------------------------------------

    return Black


# ----------------------------------------------------------------------
def PylintFuncFactory(
    package_root: Path,  # given /src/<package_name>, package_root is /src/<package_name>
    app: typer.Typer,
    default_min_score: float = 9.5,
    additional_args: Optional[str] = None,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("pylint", no_args_is_help=False)
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
        pylint_args: Annotated[
            Optional[str],
            typer.Option(
                "--args",
                help="Additional arguments passed to pylint.",
            ),
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Runs pylint on the python code."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            args = []

            if additional_args:
                args.append(additional_args)
            if pylint_args:
                args.append(pylint_args)

            optional_args = " ".join(args) if args else None

            PythonBuildActivities.Pylint(
                dm,
                package_root,
                min_score,
                args=optional_args,
            )

    # ----------------------------------------------------------------------

    return Pylint


# ----------------------------------------------------------------------
def PytestFuncFactory(
    test_root: Path,  # given /src/<package_name> and /tests, test_root is /tests
    cov_name: str,
    app: typer.Typer,
    default_min_coverage: float = 95.0,
    additional_args: Optional[str] = None,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("pytest", no_args_is_help=False)
    def Pytest(
        code_coverage: Annotated[
            bool,
            typer.Option("--code-coverage", help="Run tests with code coverage information."),
        ] = False,
        benchmark: Annotated[
            bool,
            typer.Option("--benchmark", help="Run benchmark tests in addition to other tests."),
        ] = False,
        pytest_args: Annotated[
            Optional[str],
            typer.Option("--args", help="Additional arguments passed to pytest."),
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Runs pytest on the python tests."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            args = []

            if additional_args:
                args.append(additional_args)
            if pytest_args:
                args.append(pytest_args)

            optional_args = " ".join(args) if args else None

            PythonBuildActivities.Pytest(
                dm,
                test_root,
                cov_name,
                default_min_coverage if code_coverage else None,
                args=optional_args,
                code_coverage=code_coverage,
                run_benchmarks=benchmark,
            )

    # ----------------------------------------------------------------------

    return Pytest


# ----------------------------------------------------------------------
def UpdateVersionFuncFactory(
    source_root: Path,  # given /src/<package_name>, source_root is /src
    init_filename: Path,
    app: typer.Typer,
) -> Callable:
    assert source_root.is_dir(), source_root
    assert init_filename.is_file(), init_filename
    assert PathEx.IsDescendant(init_filename, source_root), (init_filename, source_root)

    # ----------------------------------------------------------------------
    @app.command("update_version", no_args_is_help=False)
    def UpdateVersion(
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Updates the version of the python package."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            # ----------------------------------------------------------------------
            def UpdateContent(
                content: str,
                semantic_version: SemVer,
            ) -> str:
                return re.sub(
                    r"^__version__\s*=\s*.*$",
                    '__version__ = "{}"'.format(semantic_version),
                    content,
                    count=1,
                    flags=re.MULTILINE,
                )

            # ----------------------------------------------------------------------

            BuildActivities.UpdateVersion(
                dm,
                source_root,
                init_filename,
                UpdateContent,
            )

    # ----------------------------------------------------------------------

    return UpdateVersion


# ----------------------------------------------------------------------
def PackageFuncFactory(
    repo_root: Path,  # given /src/<package_name>, repo_root is /
    app: typer.Typer,
    additional_args: Optional[str] = None,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("package", no_args_is_help=False)
    def Package(
        package_args: Annotated[
            Optional[str],
            typer.Option("--args", help="Additional arguments passed to build."),
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Builds the python package."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            args = []

            if additional_args:
                args.append(additional_args)
            if package_args:
                args.append(package_args)

            optional_args = " ".join(args) if args else None

            PythonBuildActivities.Package(
                dm,
                repo_root,
                args=optional_args,
            )

    # ----------------------------------------------------------------------

    return Package


# ----------------------------------------------------------------------
def PublishFuncFactory(
    repo_root: Path,  # given /src/<package_name>, repo_root is /
    app: typer.Typer,
    additional_args: Optional[str] = None,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("publish", no_args_is_help=False)
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
        publish_args: Annotated[
            Optional[str],
            typer.Option("--args", help="Additional arguments based to the publish command."),
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Publishes the python package."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            args = []

            if additional_args:
                args.append(additional_args)
            if publish_args:
                args.append(publish_args)

            optional_args = " ".join(args) if args else None

            PythonBuildActivities.Publish(
                dm,
                repo_root,
                pypi_api_token,
                production=production,
                args=optional_args,
            )

    # ----------------------------------------------------------------------

    return Publish


# ----------------------------------------------------------------------
def BuildBinaryFuncFactory(
    repo_root: Path,  # given /src/<package_name>, repo_root is /
    build_filename: Path,
    app: typer.Typer,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("build_binary", no_args_is_help=False)
    def BuildBinary(
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Builds a python executable using cx_Freeze."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            PythonBuildActivities.BuildBinary(
                dm,
                build_filename,
                repo_root / "build",
            )

    # ----------------------------------------------------------------------

    return BuildBinary


# ----------------------------------------------------------------------
def BuildBinariesFuncFactory(
    repo_root: Path,  # given /src/<package_name>, repo_root is /
    build_filenames: dict[str, Path],
    app: typer.Typer,
) -> Callable:
    # Create an enumeration of the build names
    enum_type = Enum("BuildNames", {item: item for item in build_filenames})  # type: ignore

    # ----------------------------------------------------------------------
    @app.command("build_binaries", no_args_is_help=False)
    def BuildBinaries(
        binary_names: Annotated[
            Optional[list[enum_type]], typer.Argument(help="The name of the binary to build.")  # type: ignore
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Builds a python executable using cx_Freeze."""

        binary_names = binary_names or list(enum_type)  # type: ignore

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            for index, build_enum in enumerate(binary_names):
                build_name = build_enum.name
                build_filename = build_filenames[build_name]

                with dm.Nested(
                    "Building '{}' ({} of {})...".format(build_name, index + 1, len(binary_names)),
                    suffix="\n",
                ) as this_dm:
                    PythonBuildActivities.BuildBinary(
                        this_dm,
                        build_filename,
                        repo_root / "build" / build_name,
                    )

    # ----------------------------------------------------------------------

    return BuildBinaries


# ----------------------------------------------------------------------
def CreateDockerImageFuncFactory(
    repo_root: Path,  # Given /src/<package_name>, repo_root is /
    app: typer.Typer,
    docker_license: Optional[str] = None,  # https://spdx.org/licenses/
    default_description: Optional[str] = None,
    default_bootstrap_args: str = "--package",
    create_base_image_func: Optional[BuildActivities.CreateBaseImageFunc] = None,
) -> Callable:
    # ----------------------------------------------------------------------
    @app.command("create_docker_image", no_args_is_help=False)
    def CreateDockerImage(
        name_suffix: Annotated[
            Optional[str],
            typer.Option(
                "--name-suffix",
                help="Suffix applies to the docker image tag.",
            ),
        ] = None,
        description: Annotated[
            Optional[str],
            typer.Option(
                "--description",
                help="Description embedded within the docker image.",
            ),
        ] = None,
        bootstrap_args: Annotated[
            Optional[str],
            typer.Option(
                "--bootstrap-args",
                help="Additional arguments passed to the bootstrap command.",
            ),
        ] = None,
        verbose: Annotated[bool, _verbose_typer_option] = False,
        debug: Annotated[bool, _debug_typer_option] = False,
    ) -> None:
        """Creates a docker image for the repository."""

        with DoneManager.CreateCommandLine(
            flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
        ) as dm:
            # Create the image
            final_bootstrap_args = default_bootstrap_args

            if bootstrap_args:
                final_bootstrap_args += f" {bootstrap_args}"

            docker_image_id = BuildActivities.CreateDockerImage(
                dm,
                repo_root,
                create_base_image_func,
                final_bootstrap_args,
                name_suffix,
                docker_license,
                description or default_description,
            )

            if dm.result != 0:
                return

            assert docker_image_id is not None

    # ----------------------------------------------------------------------

    return CreateDockerImage
