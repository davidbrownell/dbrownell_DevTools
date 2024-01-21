"""Sample test file"""

# pylint: disable=invalid-name

from . import MyModule


# ----------------------------------------------------------------------
def test_Standard():  # pylint: disable=invalid-name
    assert MyModule.Add(1, 2) == 3
