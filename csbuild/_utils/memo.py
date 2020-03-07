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
.. module:: memo
	:synopsis: Thread-safe memoization utilities
"""

from __future__ import unicode_literals, division, print_function

import threading
from .._testing import testcase

unset = object()

class NotReady(Exception):
	"""
	Simple exception representing a failed result from TryGet()
	"""
	pass

class MemoObject(object):
	"""
	An object within the memo, with facilities for thread-safe writes and blocking reads.
	These are write-once structures. Once written they cannot be changed. This allows optimizations on reads
	once the write has persisted.
	"""
	def __init__(self):
		self._lock = threading.Lock()
		self._lock.acquire()
		self.value = unset

	def Commit(self, value):
		"""
		Commit a value to the memo object, which frees up any blocking reads.

		:param value: The value to write
		:type value: any
		"""
		self.value = value
		self._lock.release()

	def Get(self):
		"""
		Get a value from the memo object. If the value has not yet been written, this will block until
		the write is complete.

		:return: The written value
		:rtype: any
		"""
		# Cannot rely on GIL for this since this, by design, must block.

		#pylint: disable=not-context-manager
		with self._lock:
			return self.value

	def TryGet(self):
		"""
		Try to obtain a value. If the value's been written, this will return it immediately without blocking.
		Otherwise this will raise a NotReady exception.

		:return: The value
		:rtype: any
		:raises NotReady: if the value has not yet been written
		"""
		# Relying on the GIL to make this work.
		# This should be safe since it's only one operation.
		ret = self.value
		if ret is unset:
			raise NotReady
		return ret

	def Unlocked(self):
		"""
		Check whether the value has been written yet.

		:return: True if the value's been committed, False otherwise
		:rtype: bool
		"""
		# Relying on the GIL to make this work.
		# This should be safe since it's only one operation.
		return self.value is not unset

class MemoObjectWrapper(object):
	"""
	A simple wrapper around a MemoObject. Since MemoObjects are write-once, this class avoids locking on Get() once
	a successful write has been performed.

	:param obj: The MemoObject to wrap
	:type obj: MemoObject
	"""
	def __init__(self, obj):
		self._object = obj
		if obj.Unlocked():
			# If the value's already been set, we can avoid ever going through any locks.
			# Replace Get and TryGet with _getUnlocked
			self._value = obj.value
			# pylint: disable=invalid-name
			self.Get = self._getUnlocked
			self.TryGet = self._getUnlocked

	def _getUnlocked(self):
		return self._value

	# pylint: disable=method-hidden
	def Get(self):
		"""
		Get a value from the memo object. If the value has not yet been written, this will block until
		the write is complete.

		:return: The written value
		:rtype: any
		"""
		self._value = self._object.Get()
		# Once we have a value, we can avoid going through the lock again.
		# Replace Get and TryGet with _getUnlocked
		self.Get = self._getUnlocked
		self.TryGet = self._getUnlocked
		return self._value

	def TryGet(self):
		"""
		Try to obtain a value. If the value's been written, this will return it immediately without blocking.
		Otherwise this will raise a NotReady exception.

		:return: The value
		:rtype: any
		:raises NotReady: if the value has not yet been written
		"""
		self._value = self._object.TryGet()
		# Once we have a value, we can avoid going through the lock again.
		# Replace Get and TryGet with _getUnlocked
		self.Get = self._getUnlocked
		self.TryGet = self._getUnlocked
		return self._value


class Memo(object):
	"""
	A thread-safe memoization dictionary. This dictionary is write-once, read-many.
	Which is to say, once a value has been written, it cannot be overwritten.
	The intended use of this is to avoid repeating work, and to coordinate between multiple threads
	to ensure only one thread will do the work for any given task. The result is then stored here,
	and future tasks that need this value can read it from here without redoing the work.
	"""
	def __init__(self):
		self.lock = threading.Lock()
		self.vals = {}

	def __getitem__(self, item):
		# Relying on the GIL to keep this from being corrupted.
		# This should be safe since it's only one operation.
		return MemoObjectWrapper(self.vals[item])

	def __contains__(self, item):
		# Relying on the GIL to keep this from being corrupted.
		# This should be safe since it's only one operation.
		return item in self.vals

	def GetForWrite(self, key):
		"""
		Attempt to obtain write responsibility for a given key. This returns a 2-tuple where the first value
		indicates whether or not write responsibility was obtained, and the second is the memo object for this value.
		If write responsibility was not obtained, the second value should be used to read, not to commit new data.
		Otherwise work whould be performed and the result committed into the second value.

		:param key: The key to memoize
		:type key: any
		:return: 2-tuple of (writeResponsibilityGranted, memo object)
		:rtype: tuple[bool, MemoObject]
		"""
		#pylint: disable=not-context-manager
		with self.lock:
			try:
				return False, self.vals[key]
			except KeyError:
				ret = MemoObject()
				self.vals[key] = ret
		return True, ret


### Unit Tests ###

class TestMemo(testcase.TestCase):
	"""Test the memo"""

	# pylint: disable=invalid-name
	def testMemo(self):
		"""Simple test of the memo"""
		from .. import log
		import time
		memo = Memo()
		def _writeThread():
			for i in range(1,1000):
				readyForWrite, value = memo.GetForWrite("key{}".format(i))
				self.assertTrue(readyForWrite)
				value.Commit(i)

		def _readThread():
			lastVal = 0
			while True:
				try:
					val = memo["key{}".format(lastVal + 1)].Get()
				except KeyError:
					# Try again while write thread works on this
					time.sleep(0)
					continue
				self.assertEqual(val, lastVal+1)
				if val == 999:
					return
				lastVal = val

		writeThread = threading.Thread(target=_writeThread)
		readThreads = [threading.Thread(target=_readThread) for _ in range(10)]

		log.Test("Starting threads")
		for thread in readThreads:
			thread.start()
		writeThread.start()

		lastVal = 0
		while True:
			try:
				val = memo["key{}".format(lastVal + 1)].Get()
			except KeyError:
				# Try again while write thread works on this
				time.sleep(0)
				continue
			self.assertEqual(val, lastVal+1)
			if val % 100 == 0 and val != lastVal:
				log.Test("Finished {} iterations...", val)
			if val == 999:
				break
			lastVal = val

		log.Test("Joining threads")
		writeThread.join()
		for thread in readThreads:
			thread.join()

		self.assertEqual(memo["key999"].TryGet(), 999)
