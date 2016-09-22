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
	:synopsis: Basic test of C++ tools

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

from csbuild._testing.functional_test import FunctionalTest
from csbuild.tools.linkers.linker_base import LibraryError
from csbuild._utils import PlatformBytes
import os
import subprocess
import platform

def Touch(fname):
	"""
	Touch a file to update its modification time
	:param fname: Filename
	:type fname: str
	"""
	with open(fname, 'a'):
		os.utime(fname, None)

#TODO: Once we have a windows-compatible compiler tool, this needs to run on all platforms.
if platform.system() == "Linux":
	class BasicCppTest(FunctionalTest):
		"""Basic c++ test"""

		# pylint: disable=invalid-name
		def setUp(self): # pylint: disable=arguments-differ
			if platform.system() == "Windows":
				self.outputFile = "hello_world/out/hello_world.exe"
			else:
				self.outputFile = "hello_world/out/hello_world"
			FunctionalTest.setUp(self, cleanArgs=["--project=hello_world"])

		def testCompileSucceeds(self):
			"""Basic tool test"""
			self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands")

			self.assertTrue(os.path.exists(self.outputFile))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("Hello, World!"))

		def testLibraryFail(self):
			"""Test that invalid libraries cause a failure"""
			self.cleanArgs = ["--project=fail_libraries"]
			self.assertMakeRaises(LibraryError, "-v", "--project=fail_libraries", "--show-commands")

		def testRecompileDoesntCompileOrLinkAnything(self):
			"""Test that recompiling without any changes doesn't do anything"""
			_, out, _ = self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands")
			self.assertIn("Compiling hello.cpp", out)
			self.assertIn("Compiling main.cpp", out)
			self.assertIn("Linking hello_world", out)

			_, out, _ = self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands")
			self.assertNotIn("Compiling hello.cpp", out)
			self.assertNotIn("Compiling main.cpp", out)
			self.assertNotIn("Linking hello_world", out)

			self.assertTrue(os.path.exists(self.outputFile))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("Hello, World!"))

		def testRecompileAfterTouchRebuildsOnlyOneFile(self):
			"""Test that recompiling after touching one file builds only that file"""
			_, out, _ = self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands")
			self.assertIn("Compiling hello.cpp", out)
			self.assertIn("Compiling main.cpp", out)
			self.assertIn("Linking hello_world", out)

			Touch("hello_world/hello.cpp")

			_, out, _ = self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands")
			self.assertIn("Compiling hello.cpp", out)
			self.assertNotIn("Compiling main.cpp", out)
			self.assertIn("Linking hello_world", out)

			self.assertTrue(os.path.exists(self.outputFile))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("Hello, World!"))

			Touch("hello_world/main.cpp")

			_, out, _ = self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands")
			self.assertNotIn("Compiling hello.cpp", out)
			self.assertIn("Compiling main.cpp", out)
			self.assertIn("Linking hello_world", out)

			self.assertTrue(os.path.exists(self.outputFile))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("Hello, World!"))

		def testRecompileAfterTouchingHeaderRebuildsBothFiles(self):
			"""Test that recompiling after touching a header causes all cpp files that include it to recompile"""
			_, out, _ = self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands")
			self.assertIn("Compiling hello.cpp", out)
			self.assertIn("Compiling main.cpp", out)
			self.assertIn("Linking hello_world", out)

			Touch("hello_world/header.hpp")

			_, out, _ = self.assertMakeSucceeds("-v", "--project=hello_world", "--show-commands")
			self.assertIn("Compiling hello.cpp", out)
			self.assertIn("Compiling main.cpp", out)
			self.assertIn("Linking hello_world", out)

			self.assertTrue(os.path.exists(self.outputFile))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("Hello, World!"))
