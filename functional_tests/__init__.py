# Copyright (C) 2016 Jaedyn K. Draper
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
.. package:: functional_tests
	:synopsis: Set of functional tests for csbuild, just contains directories with tests in it
		This file only exists to perform test loading.

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function
import os
import imp
from unittest import TestSuite, defaultTestLoader

def load_tests(_loader, _tests, _pattern): #pylint: disable=invalid-name
	"""Load tests"""
	suite = TestSuite()

	for testdir in os.listdir("functional_tests"):
		if os.path.isdir(os.path.join("functional_tests", testdir)):
			modulepath = os.path.join("functional_tests", testdir, "tests.py")
			if os.access(modulepath, os.F_OK):
				suite.addTest(defaultTestLoader.loadTestsFromModule(imp.load_source("functional_tests.{}.tests".format(testdir), modulepath)))

	return suite