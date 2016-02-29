# Copyright (C) 2013 Jaedyn K. Draper
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
.. module:: run_unit_tests
	:synopsis: Import this file and call RunTests() to run csbuild's unit tests.
		Ensure cwd is one directory above the csbuild package. Do not execute directly, it will fail.
"""

from __future__ import unicode_literals, division, print_function

import sys
import unittest

from csbuild._utils import shared_globals, terminfo
from csbuild._testing import testcase


def RunTests():
	"""
	Run all unit tests.
	Must be executed with current working directory being a directory that contains the csbuild package.
	"""
	shared_globals.colorSupported = terminfo.TermInfo.SupportsColor()
	tests = unittest.defaultTestLoader.discover("csbuild", "*.py", ".")
	testRunner = testcase.TestRunner(stream=sys.stdout, verbosity=0)
	testRunner.run(tests)
