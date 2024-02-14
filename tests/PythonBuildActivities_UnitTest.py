# ----------------------------------------------------------------------
# |
# |  PythonBuildActivities_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-02-14 11:35:07
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Unit tests for PythonBuildActivities.py"""

import re
import sys
import textwrap

from typing import Callable, cast
from unittest.mock import patch

from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent
from dbrownell_DevTools.PythonBuildActivities import *
import pytest


# ----------------------------------------------------------------------
_repo_root = Path(__file__).parent.parent


# ----------------------------------------------------------------------
class TestBlack:
    expected_output = textwrap.dedent(
        """\
        Heading...
          Running black...DONE! (0, <scrubbed duration>)
        DONE! (0, <scrubbed duration>)
        """,
    )

    # ----------------------------------------------------------------------
    def test_NoFormatNotVerbose(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Black(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
            ),
        )

        assert len(args) == 2
        assert args[0] == 'black --check "{}"'.format(_repo_root)
        assert not kwargs

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_FormatNotVerbose(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Black(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
                format_sources=True,
            ),
        )

        assert len(args) == 2
        assert args[0] == 'black "{}"'.format(_repo_root)
        assert not kwargs

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_Verbose(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0, verbose=True)

        args, kwargs = _PatchStream(
            lambda: Black(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
            ),
        )

        assert len(args) == 2
        assert args[0] == 'black --check --verbose "{}"'.format(_repo_root)
        assert not kwargs

        assert (
            cast(str, next(dm_and_content))
            == textwrap.dedent(
                """\
            Heading...
              Running black...
                VERBOSE: Command Line: black --check --verbose "{}"

              DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """,
            ).format(_repo_root)
        )


# ----------------------------------------------------------------------
class TestPylint:
    expected_output = textwrap.dedent(
        """\
        Heading...
          Running pylint...DONE! (0, <scrubbed duration>)
        DONE! (0, <scrubbed duration>)
        """,
    )

    # ----------------------------------------------------------------------
    def test_NoMinScoreNotVerbose(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Pylint(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
            ),
        )

        assert len(args) == 2
        assert args[0] == 'pylint --fail-under=9.5 "{}"'.format(_repo_root)
        assert not kwargs

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_CustomMinScoreNotVerbose(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Pylint(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
                min_score=10,
            ),
        )

        assert len(args) == 2
        assert args[0] == 'pylint --fail-under=10 "{}"'.format(_repo_root)
        assert not kwargs

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_Verbose(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0, verbose=True)

        args, kwargs = _PatchStream(
            lambda: Pylint(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
            ),
        )

        assert len(args) == 2
        assert args[0] == 'pylint --fail-under=9.5 --verbose "{}"'.format(_repo_root)
        assert not kwargs

        assert (
            cast(str, next(dm_and_content))
            == textwrap.dedent(
                """\
            Heading...
              Running pylint...
                VERBOSE: Command Line: pylint --fail-under=9.5 --verbose "{}"

              DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """,
            ).format(_repo_root)
        )


# ----------------------------------------------------------------------
class TestPytest:
    expected_output = textwrap.dedent(
        """\
        Heading...
          Running pytest...DONE! (0, <scrubbed duration>)
        DONE! (0, <scrubbed duration>)
        """,
    )

    # ----------------------------------------------------------------------
    def test_Standard(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Pytest(
                cast(DoneManager, next(dm_and_content)), _repo_root, "dbrownell_DevTools"
            ),
        )

        assert len(args) == 2
        assert args[0] == "pytest --benchmark-skip  --capture=no --verbose -vv  ."
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_CodeCoverage(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Pytest(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
                "dbrownell_DevTools",
                code_coverage=True,
            ),
        )

        assert len(args) == 2
        assert (
            args[0]
            == "pytest --benchmark-skip --cov=dbrownell_DevTools  --capture=no --verbose -vv  ."
        )
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_MinCoverage(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Pytest(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
                "dbrownell_DevTools",
                min_coverage=90,
            ),
        )

        assert len(args) == 2
        assert (
            args[0]
            == "pytest --benchmark-skip --cov=dbrownell_DevTools --cov-fail-under=90  --capture=no --verbose -vv  ."
        )
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_Benchmarks(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Pytest(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
                "dbrownell_DevTools",
                run_benchmarks=True,
            ),
        )

        assert len(args) == 2
        assert args[0] == "pytest  --capture=no --verbose -vv  ."
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_AdditionalArgs(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Pytest(
                cast(DoneManager, next(dm_and_content)),
                _repo_root,
                "dbrownell_DevTools",
                pytest_args="more args here",
            ),
        )

        assert len(args) == 2
        assert args[0] == "pytest --benchmark-skip  --capture=no --verbose -vv more args here ."
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == self.expected_output


# ----------------------------------------------------------------------
class TestPackage:
    expected_output = textwrap.dedent(
        """\
        Heading...
          Packaging...DONE! (0, <scrubbed duration>)
        DONE! (0, <scrubbed duration>)
        """,
    )

    # ----------------------------------------------------------------------
    def test_NoAdditionalArgs(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Package(cast(DoneManager, next(dm_and_content)), _repo_root)
        )

        assert len(args) == 2
        assert args[0] == "python -m build "
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == self.expected_output

    # ----------------------------------------------------------------------
    def test_AdditionalArgs(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        args, kwargs = _PatchStream(
            lambda: Package(cast(DoneManager, next(dm_and_content)), _repo_root, "additional args")
        )

        assert len(args) == 2
        assert args[0] == "python -m build additional args"
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == self.expected_output


# ----------------------------------------------------------------------
class TestPublish:
    # ----------------------------------------------------------------------
    def test_Standard(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        with patch.object(Path, "is_dir", return_value=True):
            args, kwargs = _PatchStream(
                lambda: Publish(cast(DoneManager, next(dm_and_content)), _repo_root, "<token>"),
            )

        assert len(args) == 2
        assert (
            args[0]
            == 'twine upload --repository-url https://test.PyPi.org/legacy/ --username __token__ --password <token> --non-interactive --disable-progress-bar  "dist/*.whl"'
        )
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == textwrap.dedent(
            """\
            Heading...
              Publishing to 'https://test.PyPi.org/legacy/'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """,
        )

    # ----------------------------------------------------------------------
    def test_Production(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        with patch.object(Path, "is_dir", return_value=True):
            args, kwargs = _PatchStream(
                lambda: Publish(
                    cast(DoneManager, next(dm_and_content)),
                    _repo_root,
                    "<token>",
                    production=True,
                ),
            )

        assert len(args) == 2
        assert (
            args[0]
            == 'twine upload --repository-url https://upload.PyPi.org/legacy/ --username __token__ --password <token> --non-interactive --disable-progress-bar  "dist/*.whl"'
        )
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == textwrap.dedent(
            """\
            Heading...
              Publishing to 'https://upload.PyPi.org/legacy/'...DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """,
        )

    # ----------------------------------------------------------------------
    def test_Verbose(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0, verbose=True)

        with patch.object(Path, "is_dir", return_value=True):
            args, kwargs = _PatchStream(
                lambda: Publish(cast(DoneManager, next(dm_and_content)), _repo_root, "<token>"),
            )

        assert len(args) == 2
        assert (
            args[0]
            == 'twine upload --repository-url https://test.PyPi.org/legacy/ --username __token__ --password <token> --non-interactive --disable-progress-bar --verbose "dist/*.whl"'
        )
        assert len(kwargs) == 1
        assert kwargs["cwd"] == _repo_root

        assert cast(str, next(dm_and_content)) == textwrap.dedent(
            """\
            Heading...
              Publishing to 'https://test.PyPi.org/legacy/'...
                VERBOSE: Command Line: twine upload --repository-url https://test.PyPi.org/legacy/ --username __token__ --password <token> --non-interactive --disable-progress-bar --verbose "dist/*.whl"

              DONE! (0, <scrubbed duration>)
            DONE! (0, <scrubbed duration>)
            """,
        )

    # ----------------------------------------------------------------------
    def test_NoDistDir(self):
        invalid_dir = Path("does_not_exist")

        with pytest.raises(
            DoneManagerException,
            match=re.escape(
                "The distribution directory '{}' does not exist. Please make sure that the package has been built before invoking this functionality.".format(
                    invalid_dir / "dist"
                )
            ),
        ):
            dm_and_content = GenerateDoneManagerAndContent(expected_result=-1)

            Publish(
                cast(DoneManager, next(dm_and_content)),
                invalid_dir,
                "<token>",
            )


# ----------------------------------------------------------------------
class TestBuildBinary:
    # ----------------------------------------------------------------------
    @pytest.mark.skipif(
        sys.version_info.major == 3 and sys.version_info.minor == 12,
        reason="cx_Freeze is not yet supported with Python 3.12",
    )
    def test_BuildBinary(self, tmp_path):
        python_filename = tmp_path / "HelloWorld.py"

        with python_filename.open("w") as f:
            f.write("print('Hello, World!')")

        build_filename = tmp_path / "build_binary.py"

        with build_filename.open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    from cx_Freeze import setup, Executable

                    setup(
                        name="HelloWorld",
                        version="0.1.0",
                        description="Test binary",
                        executables=[
                            Executable(
                                "{}",
                                base="console",
                                target_name="HelloWorld",
                            ),
                        ],
                        options={{
                            "build_exe": {{
                                "excludes": [
                                    "tcl",
                                    "tkinter",
                                ],
                                "no_compress": False,
                                "optimize": 0,
                            }},
                        }},
                    )
                    """,
                ).format(python_filename.as_posix()),
            )

        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        BuildBinary(
            cast(DoneManager, next(dm_and_content)),
            build_filename,
            output_dir,
        )

        content = cast(str, next(dm_and_content))

    # ----------------------------------------------------------------------
    def test_EarlyExit(self):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=-1)

        _PatchStream(
            lambda: BuildBinary(
                cast(DoneManager, next(dm_and_content)),
                Path("does_not_exist"),
                Path("does_not_exist"),
            ),
            return_value=-1,
        )

        assert cast(str, next(dm_and_content)) == textwrap.dedent(
            """\
            Heading...
              Building binary...
                Building executable...DONE! (-1, <scrubbed duration>)
              DONE! (-1, <scrubbed duration>)
            DONE! (-1, <scrubbed duration>)
            """,
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _PatchStream(
    func: Callable[[], None],
    return_value: int = 0,
) -> tuple[list[str], dict[str, str]]:
    with patch(
        "dbrownell_DevTools.PythonBuildActivities.SubprocessEx.Stream",
        return_value=return_value,
    ) as mock:
        func()

        return mock.call_args.args, mock.call_args.kwargs
