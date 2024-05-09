# ----------------------------------------------------------------------
# |
# |  VSCodeTests.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-04-13 18:22:19
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Updates VSCode's launch.json file to invoke python tests."""

import os

# This script is invoked in 2 different ways:
#
#   1) As an entry point for a command line application
#   2) From cog when updating a launch.json file
#
# When the script is initially invoked, the environment variable `_VSCODE_TESTS_COGGING__`
# will not be defined. The script will then define this variable and set it to the name
# of the file being cogged.

IS_COGGING_ENVVAR_NAME = "_VSCODE_TESTS_COGGING__"

if os.getenv(IS_COGGING_ENVVAR_NAME, None) is None:
    # If here, this file was invoked as a command line application.

    import io
    import textwrap

    from pathlib import Path
    from typing import Annotated

    import typer

    from cogapp import Cog  # type: ignore[import-untyped]
    from dbrownell_Common.ContextlibEx import ExitStack  # type: ignore[import-untyped]
    from dbrownell_Common.Streams.DoneManager import (  # type: ignore[import-untyped]
        DoneManager,
        Flags as DoneManagerFlags,
    )
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
        working_dir: Annotated[
            Path,
            typer.Argument(
                exists=True,
                file_okay=False,
                resolve_path=True,
                help="The directory to search for test files.",
            ),
        ] = Path.cwd(),
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
            # Create launch.json if it doesn't exist
            launch_json_filename = working_dir / ".vscode" / "launch.json"

            if not launch_json_filename.is_file():
                with dm.Nested("Creating 'launch.json'..."):
                    launch_json_filename.parent.mkdir(parents=True, exist_ok=True)

                    with launch_json_filename.open("w") as f:
                        f.write(
                            textwrap.dedent(
                                """\
                                {
                                    // Use IntelliSense to learn about possible attributes.
                                    // Hover to view descriptions of existing attributes.
                                    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
                                    "version": "0.2.0",
                                    "configurations": [
                                        // [[[cog import VSCodeTests]]]
                                        // [[[end]]]
                                    ]
                                }
                                """,
                            ),
                        )

            with dm.Nested(f"Updating '{launch_json_filename}'...") as cog_dm:
                # Launch cog
                os.environ[IS_COGGING_ENVVAR_NAME] = str(working_dir)
                with ExitStack(lambda: os.environ.pop(IS_COGGING_ENVVAR_NAME)):
                    sink = io.StringIO()

                    cogger = Cog()

                    cogger.setOutput(
                        stdout=sink,
                        stderr=sink,
                    )

                    result = cogger.main(
                        [
                            "custom_cog",  # Fake script name
                            "-e",  # Warn if a file has no cog code in it
                            "-r",  # Replace
                            "--verbosity=0",
                            "-I",
                            str(Path(__file__).parent),
                            str(launch_json_filename),
                        ],
                    )

                    output = sink.getvalue()

                    if result == 0:
                        lines = output.rstrip().split("\n")

                        if lines[-1].startswith("Warning:"):
                            result = 1

                        if result != 0:
                            if "no cog code found in" in output:
                                cog_dm.WriteError(
                                    textwrap.dedent(
                                        f"""\
                                        Cog content was not found in '{launch_json_filename}'.

                                        Ensure that these statements appear in the file:

                                            {{
                                                ...
                                                "configurations": [
                                                    // [[[cog import VSCodeTests]]]
                                                    // [[[end]]]
                                                ]
                                                ...
                                            }}

                                        """,
                                    ),
                                )
                            else:
                                cog_dm.WriteError(output)

                            return

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    if __name__ == "__main__":
        app()

else:
    # If here, this script was invoked by cog.

    import re
    import textwrap

    from pathlib import Path

    import cog
    from dbrownell_Common import PathEx  # type: ignore[import-untyped]

    # ----------------------------------------------------------------------
    def CogEntryPoint():
        working_dir_str = os.getenv(IS_COGGING_ENVVAR_NAME)
        assert working_dir_str is not None

        working_dir = Path(working_dir_str)

        # Discover tests
        test_name_regex = re.compile(r"^.+_.+Test.py")

        test_filenames: list[Path] = []

        for root, _, filenames in os.walk(working_dir):
            root_path = Path(root)

            for filename in filenames:
                if not test_name_regex.match(filename):
                    continue

                test_filenames.append(root_path / filename)

        for test_filename in test_filenames:
            cog.outl(
                textwrap.dedent(
                    """\
                    {{
                        // {filename}
                        "name": "{name}",

                        "presentation": {{
                            "hidden": false,
                            "group": "{group}",
                        }},

                        "type": "debugpy",
                        "request": "launch",
                        "justMyCode": false,
                        "console": "integratedTerminal",

                        "module": "pytest",
                        "cwd": "{dirname}",

                        "args": [
                            "-o",
                            "python_files=*Test.py",
                            "-vv",
                            "{basename}",

                            "--capture=no",  // Do not capture stderr/stdout

                            // To run a test method within a class, use the following expression
                            // with the `-k` argument that follows:
                            //
                            //      <class_name> and <test_name> [and not <other_test_name>]
                            //

                            // "-k", "test_name or expression",

                            // Insert custom program args here
                        ],
                    }},
                    """,
                )
                .rstrip()
                .format(
                    filename=test_filename.as_posix(),
                    dirname=test_filename.parent.as_posix(),
                    basename=test_filename.name,
                    name=test_filename.stem,
                    group=PathEx.CreateRelativePath(working_dir, test_filename.parent).as_posix(),
                ),
            )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    CogEntryPoint()
