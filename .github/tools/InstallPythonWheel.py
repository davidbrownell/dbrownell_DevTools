# ----------------------------------------------------------------------
# |
# |  InstallPythonWheel.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-02-01 10:42:44
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Searches for a .whl file to install and then installs it."""

# Note that this file will not be run from an activated environment, so only basic python packages
# should be used.

import os
import subprocess
import sys

from pathlib import Path


if len(sys.argv) != 2:
    raise Exception("Usage: {} <search_directory>".format(sys.argv[0]))

search_directory = Path(sys.argv[1])
if not search_directory.is_dir():
    raise Exception("'{}' is not a valid directory.".format(search_directory))

# Find the first .whl file in the directory
wheel_files: list[Path] = []

for root, _, filenames in os.walk(search_directory):
    if not filenames:
        continue

    root_path = Path(root)

    for filename in filenames:
        if filename.endswith(".whl"):
            wheel_files.append(root_path / filename)

if not wheel_files:
    raise Exception("No .whl files were found in '{}'.".format(search_directory))

if len(wheel_files) > 1:
    raise Exception(
        "Multiple .whl files were found in '{}':\n{}".format(
            search_directory,
            "\n".join("    - {}".format(wheel_file) for wheel_file in wheel_files),
        )
    )

# Install the .whl file
sys.stdout.write("Installing '{}'...\n".format(wheel_files[0]))

result = subprocess.run(
    'pip install "{}"'.format(wheel_files[0]),
    check=True,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)

sys.stdout.write(result.stdout.decode("utf-8"))
sys.exit(result.returncode)
