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
from csbuild._utils import PlatformBytes

import os
import platform
import re
import subprocess

#TODO: Remove this platform restriction once other toolchains can be supported.
if platform.system() == "Windows":
	class CppFeaturesTest(FunctionalTest):
		"""Basic c++ test"""

		ExplicitDefineIsPresent = "Explicit define is present"
		ImplicitDefineIsPresent = "Implicit define is present"
		NoExplicitDefine = "No explicit define"
		NoImplicitDefine = "No implicit define"

		# pylint: disable=invalid-name
		def setUp(self): # pylint: disable=arguments-differ
			if platform.system() == "Windows":
				self.outputFile = "out/hello_world.exe"
			else:
				self.outputFile = "out/hello_world"
			FunctionalTest.setUp(self)

		def testDisableSymbolsDisableOptDynamicReleaseRuntime(self):
			"""Test that the correct compiler options are being set."""
			self.cleanArgs = ["--target=nosymbols_noopt_dynamic_release"]
			_, out, _ = self.assertMakeSucceeds("--show-commands", "--target=nosymbols_noopt_dynamic_release")

			self.assertIs(re.compile(R"^COMMAND: .* (/Z7 |/Zi |/ZI )", re.M).search(out), None)
			self.assertIsNot(re.compile(R"^COMMAND: .* (/Od )", re.M).search(out), None)
			self.assertIsNot(re.compile(R"^COMMAND: .* (/MD )", re.M).search(out), None)

			self.assertTrue(os.access(self.outputFile, os.F_OK))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("{} - {}".format(CppFeaturesTest.NoExplicitDefine, CppFeaturesTest.ImplicitDefineIsPresent)))

		def testEmbeddedSymbolsSizeOptStaticReleaseRuntime(self):
			"""Test that the correct compiler options are being set."""
			self.cleanArgs = ["--target=embeddedsymbols_sizeopt_static_release"]
			_, out, _ = self.assertMakeSucceeds("--show-commands", "--target=embeddedsymbols_sizeopt_static_release")

			self.assertIsNot(re.compile(R"^COMMAND: .* (/Z7 )", re.M).search(out), None)
			self.assertIsNot(re.compile(R"^COMMAND: .* (/O1 )", re.M).search(out), None)
			self.assertIsNot(re.compile(R"^COMMAND: .* (/MT )", re.M).search(out), None)

			self.assertTrue(os.access(self.outputFile, os.F_OK))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("{} - {}".format(CppFeaturesTest.ExplicitDefineIsPresent, CppFeaturesTest.ImplicitDefineIsPresent)))

		def testExternalSymbolsSpeeOptDynamicDebugRuntime(self):
			"""Test that the correct compiler options are being set."""
			self.cleanArgs = ["--target=externalsymbols_speedopt_dynamic_debug"]
			_, out, _ = self.assertMakeSucceeds("--show-commands", "--target=externalsymbols_speedopt_dynamic_debug")

			self.assertIsNot(re.compile(R"^COMMAND: .* (/Zi )", re.M).search(out), None)
			self.assertIsNot(re.compile(R"^COMMAND: .* (/O2 )", re.M).search(out), None)
			self.assertIsNot(re.compile(R"^COMMAND: .* (/MDd )", re.M).search(out), None)

			self.assertTrue(os.access(self.outputFile, os.F_OK))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("{} - {}".format(CppFeaturesTest.NoExplicitDefine, CppFeaturesTest.NoImplicitDefine)))

		def testExternalPlusSymbolsMaxOptStaticDebugRuntime(self):
			"""Test that the correct compiler options are being set."""
			self.cleanArgs = ["--target=externalplussymbols_maxopt_static_debug"]
			_, out, _ = self.assertMakeSucceeds("--show-commands", "--target=externalplussymbols_maxopt_static_debug")

			self.assertIsNot(re.compile(R"^COMMAND: .* (/ZI )", re.M).search(out), None)
			self.assertIsNot(re.compile(R"^COMMAND: .* (/Ox )", re.M).search(out), None)
			self.assertIsNot(re.compile(R"^COMMAND: .* (/MTd )", re.M).search(out), None)

			self.assertTrue(os.access(self.outputFile, os.F_OK))
			out = subprocess.check_output([self.outputFile])

			self.assertEqual(out, PlatformBytes("{} - {}".format(CppFeaturesTest.ExplicitDefineIsPresent, CppFeaturesTest.NoImplicitDefine)))
