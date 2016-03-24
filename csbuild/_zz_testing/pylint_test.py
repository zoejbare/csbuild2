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
.. module:: pylint_test
	:synopsis: Run pylint as part of the unit test framework
"""

from __future__ import unicode_literals, division, print_function

import multiprocessing
import os
import subprocess
import sys
import traceback
import threading

if sys.version_info[0] >= 3:
	import queue
else:
	import Queue as queue

from . import testcase
from .._utils import thread_pool, log, PlatformString


class TestPylint(testcase.TestCase):
	"""Test to run pylint"""
	# pylint: disable=invalid-name
	def testPyLint(self):
		"""Run pylint on the code and ensure it passes all pylint checks"""

		callbackQueue = queue.Queue()
		log.SetCallbackQueue(callbackQueue)
		pool = thread_pool.ThreadPool(multiprocessing.cpu_count(), callbackQueue, stopOnException=False)

		env = dict(os.environ)
		env[PlatformString('PYTHONPATH')] = os.pathsep.join(sys.path)

		fd = subprocess.Popen([sys.executable, "csbuild/_zz_testing/run_pylint.py", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
		out, err = fd.communicate()
		if err:
			log.Error(err)
		if out:
			log.Info(out)

		failedLints = set()
		lock = threading.Lock()

		def _runPylint(module):
			log.Info("Linting module {}", module)
			fd = subprocess.Popen([sys.executable, "csbuild/_zz_testing/run_pylint.py", module], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
			out, err = fd.communicate()
			if err:
				log.Error(err)
			if out:
				log.Error(out)
			if fd.returncode != 0:
				with lock:
					failedLints.add(module)
			self.assertEqual(0, fd.returncode)

		class _sharedLocals(object):
			count = 0
			done = 0

		def _checkDone():
			_sharedLocals.done += 1
			log.Info("-- Completed {} out of {} lintings", _sharedLocals.done, _sharedLocals.count)
			if _sharedLocals.count == _sharedLocals.done:
				pool.Stop()

		for root, _, files in os.walk("csbuild"):
			for filename in files:
				if filename.endswith(".py"):
					if filename.endswith("_py3.py") and sys.version_info[0] != 3:
						continue

					if filename.endswith("_py2.py") and sys.version_info[0] != 2:
						continue

					_sharedLocals.count += 1
					pool.AddTask((_runPylint, os.path.join(root, filename)), _checkDone)

		pool.Start()
		errors = False

		while True:
			cb = callbackQueue.get(block=True)
			if cb is thread_pool.ThreadPool.exitEvent:
				break
			try:
				cb()
			except Exception:
				log.Error(traceback.format_exc())
				errors = True

		log.SetCallbackQueue(None)

		if failedLints:
			log.Error("The following modules failed to lint:")
			for module in failedLints:
				log.Error("\t{}", module)
			self.fail("{} files failed to lint.".format(len(failedLints)))

		if errors:
			self.fail("Exceptions were thrown during the test")
