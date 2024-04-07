# ----------------------------------------------------------------------
# |
# |  PythonBuildActivities.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-02-14 09:25:17
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Functionality often invoked as part of a python project's build process"""

import os
import re
import shutil
import sys

from pathlib import Path
from typing import Optional

from dbrownell_Common.ContextlibEx import ExitStack  # type: ignore[import-untyped]
from dbrownell_Common.InflectEx import inflect  # type: ignore[import-untyped]
from dbrownell_Common import PathEx  # type: ignore[import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager, DoneManagerException  # type: ignore[import-untyped]
from dbrownell_Common import SubprocessEx  # type: ignore[import-untyped]

if sys.version_info >= (3, 11):
    from tomllib import load as toml_load
else:
    from tomli import load as toml_load


# ----------------------------------------------------------------------
def Black(
    dm: DoneManager,
    source_root: Path,
    *,
    format_sources: bool = False,
    args: Optional[str] = None,
) -> None:
    """Runs black on the python code"""

    with dm.Nested("Running black...") as black_dm:
        command_line = 'black {}{}{}"{}"'.format(
            "" if format_sources else "--check ",
            "--verbose " if black_dm.is_verbose else "",
            f"{args} " if args else "",
            source_root,
        )

        black_dm.WriteVerbose(f"Command Line: {command_line}\n\n")

        with black_dm.YieldStream() as stream:
            black_dm.result = SubprocessEx.Stream(command_line, stream)


# ----------------------------------------------------------------------
def Pylint(
    dm: DoneManager,
    source_root: Path,
    min_score: float = 9.5,
    *,
    args: Optional[str] = None,
) -> None:
    """Runs pylint on the python code"""

    with dm.Nested("Running pylint...") as pylint_dm:
        command_line = 'pylint --fail-under={} {}{}"{}"'.format(
            min_score,
            "--verbose " if pylint_dm.is_verbose else "",
            f"{args} " if args else "",
            source_root,
        )

        pylint_dm.WriteVerbose(f"Command Line: {command_line}\n\n")

        with pylint_dm.YieldStream() as stream:
            pylint_dm.result = SubprocessEx.Stream(command_line, stream)


# ----------------------------------------------------------------------
def Pytest(
    dm: DoneManager,
    test_root: Path,
    python_package_name: str,
    min_coverage: Optional[float] = None,
    *,
    args: Optional[str] = None,
    code_coverage: bool = False,
    run_benchmarks: bool = False,
) -> None:
    """Runs pytest on the python code"""

    if min_coverage is not None:
        code_coverage = True

    with dm.Nested("Running pytest...") as pytest_dm:
        command_line = "pytest {}{}{} --capture=no --verbose -vv {} .".format(
            "--benchmark-skip " if not run_benchmarks else "",
            f"--cov={python_package_name} " if code_coverage else "",
            f"--cov-fail-under={min_coverage} " if min_coverage is not None else "",
            args or "",
        )

        pytest_dm.WriteVerbose(f"Command Line: {command_line}\n\n")

        with pytest_dm.YieldStream() as stream:
            pytest_dm.result = SubprocessEx.Stream(
                command_line,
                stream,
                cwd=test_root,
            )


# ----------------------------------------------------------------------
def Package(
    dm: DoneManager,
    source_root: Path,
    args: Optional[str] = None,
) -> None:
    """Builds a python package"""

    delete_dynamic_readme_file_func = lambda: None

    # Dynamically extract content from README.md if:
    #
    #      1) `readme` in `pyproject.toml` starts with "dynamic_"
    #      2) `README.md` contains the tags
    #           <!-- BEGIN: Exclude Package -->
    #           <!-- END: Exclude Package -->
    #          surrounding content that should not be included in the
    #          package's README content
    #
    with dm.Nested("Preparing README.md..."):
        with PathEx.EnsureFile(source_root / "pyproject.toml").open("rb") as f:
            toml_content = toml_load(f)

        readme_filename = toml_content.get("project", {}).get("readme", None)
        if readme_filename.startswith("dynamic_"):
            original_filename = PathEx.EnsureFile(source_root / "README.md")
            dynamic_filename = source_root / readme_filename

            # Get the existing content
            with original_filename.open() as f:
                readme_content = f.read()

            # Update the content
            begin_regex = re.compile(r"<!--\s*BEGIN:\s*Exclude Package\s*-->")
            end_regex = re.compile(r"<!--\s*END:\s*Exclude Package\s*-->")

            new_content: list[str] = []
            last_index = 0

            while True:
                begin_match = begin_regex.search(readme_content, last_index)
                if begin_match is None:
                    break

                new_content.append(readme_content[last_index : begin_match.start()])

                end_match = end_regex.search(readme_content, begin_match.end())
                if end_match is None:
                    raise DoneManagerException("Missing end tag for exclude package")

                last_index = end_match.end()

            new_content.append(readme_content[last_index:])

            readme_content = "".join(new_content)

            # Write the updated content to the dynamic file
            with dynamic_filename.open("w") as f:
                f.write(readme_content)

            # Delete the file when done
            delete_dynamic_readme_file_func = dynamic_filename.unlink

    with ExitStack(delete_dynamic_readme_file_func):
        with dm.Nested("Packaging...") as package_dm:
            command_line = "python -m build {}".format(args or "")

            package_dm.WriteVerbose(f"Command Line: {command_line}\n\n")

            with package_dm.YieldStream() as stream:
                package_dm.result = SubprocessEx.Stream(
                    command_line,
                    stream,
                    cwd=source_root,
                )


# ----------------------------------------------------------------------
def Publish(
    dm: DoneManager,
    source_root: Path,
    pypi_api_token: str,
    *,
    production: bool = False,
    args: Optional[str] = None,
) -> None:
    """Publishes a python package"""

    dist_dir = source_root / "dist"

    if not dist_dir.is_dir():
        raise DoneManagerException(
            "The distribution directory '{}' does not exist. Please make sure that the package has been built before invoking this functionality.".format(
                dist_dir
            )
        )

    if production:
        repository_url = "https://upload.PyPi.org/legacy/"
    else:
        repository_url = "https://test.PyPi.org/legacy/"

    with dm.Nested("Publishing to '{}'...".format(repository_url)) as publish_dm:
        command_line = 'twine upload --repository-url {} --username __token__ --password {} --non-interactive --disable-progress-bar {} {}"dist/*.whl"'.format(
            repository_url,
            pypi_api_token,
            "--verbose" if publish_dm.is_verbose else "",
            f"{args} " if args else "",
        )

        publish_dm.WriteVerbose(f"Command Line: {command_line}\n\n")

        with publish_dm.YieldStream() as stream:
            publish_dm.result = SubprocessEx.Stream(
                command_line,
                stream,
                cwd=source_root,
            )


# ----------------------------------------------------------------------
def BuildBinary(
    dm: DoneManager,
    build_filename: Path,
    output_dir: Path,
) -> None:
    """Builds a python binary"""

    with dm.Nested("Building binary...") as build_dm:
        with build_dm.Nested("Building executable...") as build_exe_dm:
            command_line = f"python {build_filename.name} build_exe"

            build_exe_dm.WriteVerbose(f"Command Line: {command_line}\n\n")

            with build_exe_dm.YieldStream() as stream:
                build_exe_dm.result = SubprocessEx.Stream(
                    command_line,
                    stream,
                    cwd=build_filename.parent,
                )

            if build_exe_dm.result != 0:
                return

        build_dir = PathEx.EnsureDir(build_filename.parent / "build")

        # Remove empty directories
        empty_directories_removed = 0

        with build_dm.Nested(
            "Removing empty directories...",
            lambda: "{} removed".format(inflect.no("directory", empty_directories_removed)),
        ) as prune_dm:
            directories: list[Path] = []

            for root, _, _ in os.walk(build_dir):
                directories.append(Path(root))

            for directory in reversed(directories):
                if not any(item for item in directory.iterdir()):
                    with prune_dm.VerboseNested(f"Removing '{directory}'..."):
                        shutil.rmtree(directory)
                        empty_directories_removed += 1

        if output_dir.is_dir():
            with dm.Nested("Removing previous build directory..."):
                shutil.rmtree(output_dir)

        with dm.Nested("Moving files..."):
            output_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                build_dir,
                output_dir,
                copy_function=shutil.move,
            )

            shutil.rmtree(build_dir)
