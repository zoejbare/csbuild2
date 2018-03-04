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
.. module:: tests
	:synopsis: Basic test of Java tools

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

from csbuild._testing.functional_test import FunctionalTest
from csbuild.tools.linkers.linker_base import LibraryError
from csbuild._utils import PlatformBytes

import os
import platform
import subprocess
import time

def Touch(fname):
	"""
	Touch a file to update its modification time
	:param fname: Filename
	:type fname: str
	"""
	writeBit = 0x80
	oldPermissions = os.stat(fname).st_mode
	isReadOnly = not oldPermissions & writeBit
	if isReadOnly:
		os.chmod(fname, oldPermissions | writeBit)
	try:
		with open(fname, 'a'):
			# Mac has terrible filesystem time resolution, so we have to force a sleep
			# in order for changes to be picked up.
			if platform.system() == "Darwin":
				time.sleep(1)
			os.utime(fname, None)
	finally:
		if isReadOnly:
			os.chmod(fname, oldPermissions)

class BasicJavaTest(FunctionalTest):
	"""Basic c++ test"""

	# pylint: disable=invalid-name
	def setUp(self): # pylint: disable=arguments-differ
		self.outputFile = "out/hello_world.jar"
		outDir = "out"
		FunctionalTest.setUp(self, outDir=outDir, cleanArgs=["--project=hello_world", "--at"])

	def testCompileSucceeds(self):
		"""Test that the project succesfully compiles"""
		self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands", "--toolchain=oracle-java")

		self.assertTrue(os.access(self.outputFile, os.F_OK))
		#out = subprocess.check_output([self.outputFile])

		#self.assertEqual(out, PlatformBytes("Hello, World! Goodbye, World!"))