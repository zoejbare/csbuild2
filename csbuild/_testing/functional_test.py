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
.. module:: functional_test
	:synopsis: A base class for functional tests, which will execute makefiles

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import os
import subprocess
import sys
import threading

from .testcase import TestCase
from .. import log
from .._utils import PlatformString

class FunctionalTest(TestCase):
	"""
	Base class for running functional tests that invoke an actual makefile.
	"""
	def setUp(self):
		self._prevdir = os.getcwd()
		module = __import__(self.__class__.__module__)
		path = os.path.dirname(module.__file__)
		if PlatformString("CSBUILD_NO_AUTO_RUN") in os.environ:
			self._oldenviron = os.environ[PlatformString("CSBUILD_NO_AUTO_RUN")]
			del os.environ[PlatformString("CSBUILD_NO_AUTO_RUN")]
		else:
			self._oldenviron = None

		os.chdir(path)

	def tearDown(self):
		try:
			self.RunMake("--clean")
		finally:
			os.chdir(self._prevdir)
			if self._oldenviron is not None:
				os.environ[PlatformString("CSBUILD_NO_AUTO_RUN")] = self._oldenviron

	def RunMake(self, *args):
		"""
		Run the test's local makefile with the given args. The makefile must be in the same directory and named make.py
		:param args: Arguments to pass
		:type args: str
		:return: Tuple of returncode, stdout and stderr output from the process
		:rtype: tuple[int, str, str]
		"""
		cmd = [sys.executable, "make.py"]
		cmd.extend(args)
		log.Test("Executing {} (cwd: {})", cmd, os.getcwd())
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		running = True
		output = []
		errors = []
		def _streamOutput(pipe, outlist, sysbuffer):
			while running:
				try:
					line = PlatformString(pipe.readline())
				except IOError:
					continue
				if not line:
					break
				sysbuffer.write("            {}".format(line))
				outlist.append(line)

		outputThread = threading.Thread(target=_streamOutput, args=(proc.stdout, output, sys.stdout))
		errorThread = threading.Thread(target=_streamOutput, args=(proc.stderr, errors, sys.stderr))

		outputThread.start()
		errorThread.start()

		proc.wait()
		running = False

		outputThread.join()
		errorThread.join()

		return proc.returncode, "".join(output), "".join(errors)

	# pylint: disable=invalid-name
	def assertMakeSucceeds(self, *args):
		"""
		Assert that running a makefile succeeds
		:param args: Arguments to pass
		:type args: str
		:return: Tuple of returncode, stdout and stderr output from the process
		:rtype: tuple[int, str, str]
		"""
		returncode, output, errors = self.RunMake(*args)
		self.assertEqual(returncode, 0)
		return returncode, output, errors

	def assertMakeRaises(self, error, *args):
		"""
		Assert that running a makefile fails with the given error
		:param args: Arguments to pass
		:type args: str
		:param error: Error or exception to search for in the logs
		:type error: Exception or str
		:return: Tuple of returncode, stdout and stderr output from the process
		:rtype: tuple[int, str, str]
		"""
		returncode, output, errors = self.RunMake(*args)
		self.assertNotEqual(returncode, 0)
		if issubclass(error, Exception):
			error = error.__name__
		self.assertIn(error, errors)
		return returncode, output, errors

	def assertFileExists(self, filename):
		"""
		Assert that an expected file exists
		:param filename: file to check
		:type filename: str
		"""

		self.assertTrue(os.path.exists(filename))

	# pylint: disable=invalid-name
	def assertFileContents(self, filename, contents):
		"""
		Assert that an expected file exists and its contents are as expected
		:param filename: file to check
		:type filename: str
		:param contents: Contents to check against
		:type contents: str
		"""
		self.assertFileExists(filename)
		with open(filename, "r") as f:
			self.assertEqual(contents, f.read())
