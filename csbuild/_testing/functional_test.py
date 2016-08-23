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
import shutil
import platform

from .testcase import TestCase
from .. import log
from .._utils import PlatformString
from .._utils.string_abc import String

import ctypes
from ctypes import wintypes

if platform.system() == "Windows":
	# pylint: disable=import-error
	# Create ctypes wrapper for Win32 functions we need, with correct argument/return types
	_CreateMutex = ctypes.windll.kernel32.CreateMutexA
	_CreateMutex.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCSTR]
	_CreateMutex.restype = wintypes.HANDLE

	_WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
	_WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
	_WaitForSingleObject.restype = wintypes.DWORD

	_ReleaseMutex = ctypes.windll.kernel32.ReleaseMutex
	_ReleaseMutex.argtypes = [wintypes.HANDLE]
	_ReleaseMutex.restype = wintypes.BOOL

	_CloseHandle = ctypes.windll.kernel32.CloseHandle
	_CloseHandle.argtypes = [wintypes.HANDLE]
	_CloseHandle.restype = wintypes.BOOL

	class _namedMutex(object):
		# pylint: disable=invalid-name
		"""Represents a named synchronization primitive - a named mutex in windows, a file lock in linux"""
		def __init__(self, name):
			# Backslashes not ok. Forward slashes are fine.
			self.name = name.replace("\\", "/")
			if sys.version_info[0] >= 3:
				self.name = self.name.encode("UTF-8")
			ret = _CreateMutex(None, False, self.name)
			if not ret:
				raise ctypes.WinError()
			self.handle = ret

		def acquire(self):
			"""Acquire the lock"""
			timeout = 0xFFFFFFFF
			ret = _WaitForSingleObject(self.handle, timeout)
			if ret not in (0, 0x80, 0x102):
				# Waiting failed
				raise ctypes.WinError()

		def release(self):
			"""Release the lock"""
			ret = _ReleaseMutex(self.handle)
			if not ret:
				raise ctypes.WinError()

		def close(self):
			"""Close the lock"""
			ret = _CloseHandle(self.handle)
			if not ret:
				raise ctypes.WinError()

		def __enter__(self):
			self.acquire()

		def __exit__(self, excType, excVal, tb):
			self.release()
			return False
else:
	import fcntl # pylint: disable=import-error
	class _namedMutex(object):
		# pylint: disable=invalid-name
		"""Represents a named synchronization primitive - a named mutex in windows, a file lock in linux"""
		def __init__(self, name):
			self.name = name
			self.handle = open(name, 'w')

		def acquire(self):
			"""Acquire the lock"""
			fcntl.flock(self.handle, fcntl.LOCK_EX)

		def release(self):
			"""Release the lock"""
			fcntl.flock(self.handle, fcntl.LOCK_UN)

		def close(self):
			"""Close the lock"""
			self.handle.close()
			os.remove(self.name)

		def __enter__(self):
			self.acquire()

		def __exit__(self, excType, excVal, tb):
			self.release()
			return False

class FunctionalTest(TestCase):
	"""
	Base class for running functional tests that invoke an actual makefile.
	"""
	def setUp(self):
		self._prevdir = os.getcwd()
		module = __import__(self.__class__.__module__)
		path = os.path.dirname(module.__file__)

		self.mtx = _namedMutex(os.path.join("csbuild", path, "lock"))
		self.mtx.acquire()

		if PlatformString("CSBUILD_NO_AUTO_RUN") in os.environ:
			self._oldenviron = os.environ[PlatformString("CSBUILD_NO_AUTO_RUN")]
			del os.environ[PlatformString("CSBUILD_NO_AUTO_RUN")]
		else:
			self._oldenviron = None

		os.chdir(path)

		# Make sure we start in a good state
		if os.path.exists("out"):
			shutil.rmtree("out")
		if os.path.exists("intermediate"):
			shutil.rmtree("intermediate")

	def tearDown(self):
		try:
			self.RunMake("--clean")
			self.assertFalse(os.path.exists("out"))
			self.assertFalse(os.path.exists("intermediate"))
		finally:
			os.chdir(self._prevdir)
			if self._oldenviron is not None:
				os.environ[PlatformString("CSBUILD_NO_AUTO_RUN")] = self._oldenviron
			self.mtx.release()
			self.mtx.close()

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
		Assert that running a makefile fails with the given exception
		:param args: Arguments to pass
		:type args: str
		:param error: Error or exception to search for in the logs
		:type error: Exception or str
		:return: Tuple of returncode, stdout and stderr output from the process
		:rtype: tuple[int, str, str]
		"""
		returncode, output, errors = self.RunMake(*args)
		self.assertNotEqual(returncode, 0)
		if not isinstance(error, String):
			error = error.__name__
		self.assertIn(error, errors)
		return returncode, output, errors

	def assertMakeFails(self, error, *args):
		"""
		Assert that running a makefile fails with the given csbuild error
		:param args: Arguments to pass
		:type args: str
		:param error: Error string to search for in the logs
		:type error: str
		:return: Tuple of returncode, stdout and stderr output from the process
		:rtype: tuple[int, str, str]
		"""
		returncode, output, errors = self.RunMake(*args)
		self.assertNotEqual(returncode, 0)
		self.assertIn(error, output)
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
