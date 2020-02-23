# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path
import pytest
import subprocess
import sys
import unittest

from tsfpga import TSFPGA_DOC
from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file, delete


THIS_DIR = Path(__file__).parent


def run_pylint(files):
    config = THIS_DIR / "pylintrc"
    command = [sys.executable, "-m", "pylint", f"--rcfile={config}"] + files

    subprocess.check_call(command)


def test_pylint():
    # Exclude doc folder, since conf.py used by sphinx does not conform
    files = list(find_git_files(file_endings_include="py", exclude_directories=[TSFPGA_DOC]))
    run_pylint(files)


def run_pycodestyle(files):
    config = THIS_DIR / "pycodestylerc"
    command = [sys.executable, "-m", "pycodestyle", f"--config={config}"] + files

    subprocess.check_call(command)


def test_pycodestyle():
    files = list(find_git_files(file_endings_include="py"))
    run_pycodestyle(files)


class TestPythonLintFunctions(unittest.TestCase):

    file = THIS_DIR / "dummy_python_file.py"
    ugly_code = """
aa  =
def bb:
cc  = 3
"""

    def setUp(self):
        delete(self.file)
        create_file(self.file, self.ugly_code)

    def test_pylint_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_pylint([self.file])

    def test_pycodestyle_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_pycodestyle([self.file])
