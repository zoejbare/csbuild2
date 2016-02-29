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
.. module:: thread_pool
	:synopsis: Thread pool and task manager class for performing parallel operations
			with callbacks on the main thread when they are complete

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import threading
import sys
import functools
if sys.version_info[0] >= 3:
	import queue
	from collections.abc import Callable
	from ._reraise_py3 import Reraise
else:
	import Queue as queue
	from collections import Callable
	# pylint: disable=import-error
	from ._reraise_py2 import Reraise

from . import testcase, log
from .decorators import TypeChecked

class ThreadPool(object):
	"""
	Thread Pool and Task Management class
	Allows tasks to be inserted into a queue in a thread-safe way from any thread
	The first available thread will then handle that task

	:param numThreads: Number of threads in the pool - must be positive
	:type numThreads: int
	:param callbackQueue: Queue to be used to pass completion callbacks back to the main thread
	:type callbackQueue: queue.Queue
	:param stopOnException: Stop processing tasks once any thread has received an exception.
	:type stopOnException: bool
	"""
	exitEvent = object()

	@TypeChecked(numThreads=int, callbackQueue=queue.Queue, stopOnException=bool)
	def __init__(self, numThreads, callbackQueue, stopOnException=True):

		assert numThreads > 0

		self.queue = queue.Queue()
		self.threads = [threading.Thread(target=self._threadRunner) for _ in range(numThreads)]
		self.callbackQueue = callbackQueue
		self.stopOnException = stopOnException
		self.excInfo = None
		"""@type: queue.Queue"""

	def Start(self):
		"""
		Start all threads in the pool and begin executing tasks
		"""
		_ = [t.start() for t in self.threads]

	@TypeChecked(task=(Callable, tuple, type(None)), callback=(Callable, tuple, type(None)))
	def AddTask(self, task, callback):
		"""
		Add a task into the queue to be executed on the first available thread.
		This is safe to call from any thread, including threads currently executing tasks.

		:param task: Task to be executed on another thread - either a callable or a tuple of callable + args
		:type task: (Callable, *args)
		:param callback: Callback to be placed into the callback queue when this task is complete - either a callable or a tuple of callable + args
		:type callback: (Callable, *args)
		"""

		if isinstance(task, tuple):
			task = functools.partial(task[0], *(task[1:]))

		if isinstance(callback, tuple):
			callback = functools.partial(callback[0], *(callback[1:]))

		self.queue.put((task, callback), block=False)

	def Stop(self):
		"""
		Stop and join all threads. All tasks currently in the queue will finish execution before it stops.
		"""

		for _ in range(len(self.threads)):
			self.queue.put(ThreadPool.exitEvent, block=False)
		_ = [t.join() for t in self.threads]
		self.callbackQueue.put(ThreadPool.exitEvent)

	def _rethrowException(self, excInfo):
		Reraise(excInfo[1], excInfo[2])

	def _threadRunner(self):
		while True:
			task = self.queue.get(block=True)
			if task is ThreadPool.exitEvent:
				return
			if self.stopOnException and self.excInfo is not None:
				return

			try:
				if task[0]:
					task[0]()
			except:
				self.excInfo = sys.exc_info()

				self.callbackQueue.put(functools.partial(self._rethrowException, sys.exc_info()))

				if self.stopOnException:
					self.callbackQueue.put(self.Stop)
					return

			if task[1]:
				self.callbackQueue.put(task[1], block=False)


class TestThreadPool(testcase.TestCase):
	"""Test the thread pool"""

	# pylint: disable=invalid-name
	def testThreadPool(self):
		"""Test that the thread pool works in the general case"""
		import time
		import random

		callbackQueue = queue.Queue()
		log.SetCallbackQueue(callbackQueue)
		pool = ThreadPool(4, callbackQueue)
		pool.Start()

		class _sharedLocals(object):
			count = 0
			iter = 0
			callbackCount = 0

		expectedCount = 0
		lock = threading.Lock()

		def _callback():
			_sharedLocals.callbackCount += 1
			if _sharedLocals.callbackCount % 100 == 0:
				log.Info("{} callbacks completed.", _sharedLocals.callbackCount)
			if _sharedLocals.callbackCount == 400:
				pool.Stop()

		def _incrementCount2(i):
			time.sleep(random.uniform(0.001, 0.0125))
			with lock:
				_sharedLocals.count += i
				_sharedLocals.iter += 1
				if _sharedLocals.iter % 25 == 0:
					log.Info("{} iterations completed.", _sharedLocals.iter)

		def _incrementCount(i):
			time.sleep(random.uniform(0.001, 0.0125))
			with lock:
				_sharedLocals.count += i
				_sharedLocals.iter += 1
				if _sharedLocals.iter % 25 == 0:
					log.Info("{} iterations completed.", _sharedLocals.iter)
			pool.AddTask((_incrementCount2, i+1), _callback)

		for i in range(200):
			pool.AddTask((_incrementCount, i), _callback)
			expectedCount += i
			expectedCount += i + 1

		while True:
			cb = callbackQueue.get(block=True)
			if cb is ThreadPool.exitEvent:
				break
			cb()

		self.assertEqual(_sharedLocals.count, expectedCount)
		log.SetCallbackQueue(None)

	def testExceptionRethrown(self):
		"""Test that when an exception is thrown on a thread, all threads stop and that exception's rethrown on the main thread"""

		callbackQueue = queue.Queue()
		log.SetCallbackQueue(callbackQueue)
		pool = ThreadPool(4, callbackQueue)

		def _throwException():
			raise RuntimeError("Exception!")

		pool.AddTask(_throwException, None)
		pool.Start()

		caughtException = False
		while True:
			cb = callbackQueue.get(block=True)

			if cb is ThreadPool.exitEvent:
				break

			try:
				cb()
			except RuntimeError:
				caughtException = True
				import traceback
				exc = traceback.format_exc()
				self.assertIn("_threadRunner", exc)
				self.assertIn("_throwException", exc)
			else:
				self.assertTrue(caughtException, "Exception was not thrown")
