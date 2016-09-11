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
.. module:: rwlock
	:synopsis: Native reader/writer lock implementations for supported platforms using ctypes

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import ctypes
import platform
import contextlib

class _rwlock(object):
	def __init__(self, lock, plock, deleter):
		self.lock = lock
		self.plock = plock
		self._deleter = deleter

	def Close(self):
		"""
		Close the lock
		"""
		if self._deleter is not None:
			self._deleter(self.plock)

if platform.system() == "Windows":
	from ctypes import wintypes
	class _srwLock(ctypes.Structure):
		_fields_ = [("Ptr", wintypes.LPVOID)] # pylint: disable=invalid-name

	def _createRWLock():
		lock = _srwLock()
		plock = ctypes.pointer(lock)
		ctypes.windll.kernel32.InitializeSRWLock(plock)
		return _rwlock(lock, plock, None)

	def _acquireRead(lock):
		ctypes.windll.kernel32.AcquireSRWLockShared(lock.plock)

	def _acquireWrite(lock):
		ctypes.windll.kernel32.AcquireSRWLockExclusive(lock.plock)

	def _tryAcquireRead(lock):
		return ctypes.windll.kernel32.TryAcquireSRWLockShared(lock.plock) == -1681989375 # Why this number? NO CLUE.

	def _tryAcquireWrite(lock):
		return ctypes.windll.kernel32.TryAcquireSRWLockExclusive(lock.plock) == -1681989375 # Why this number? NO CLUE.

	def _releaseRead(lock):
		ctypes.windll.kernel32.ReleaseSRWLockShared(lock.plock)

	def _releaseWrite(lock):
		ctypes.windll.kernel32.ReleaseSRWLockExclusive(lock.plock)
else:
	import os

	if platform.system() == "Darwin":
		_librt = ctypes.CDLL('libpthread.dylib', use_errno=True)

		if platform.architecture()[0] == '64bit':
			_pthread_rwlock_t_size = ctypes.c_byte * 200
		elif platform.architecture()[0] == '32bit':
			_pthread_rwlock_t_size = ctypes.c_byte * 128
	else:
		_librt = ctypes.CDLL('librt.so', use_errno=True)

		if platform.architecture()[0] == '64bit':
			_pthread_rwlock_t_size = ctypes.c_byte * 56
		elif platform.architecture()[0] == '32bit':
			_pthread_rwlock_t_size = ctypes.c_byte * 32
		else:
			_pthread_rwlock_t_size = ctypes.c_byte * 44

	class _pthread_rwlock_t(ctypes.Structure): # pylint: disable=invalid-name
		_fields_ = [("Ptr", _pthread_rwlock_t_size)] # pylint: disable=invalid-name

	_pthread_rwlock_t_p = ctypes.POINTER(_pthread_rwlock_t)

	_api = [
		('pthread_rwlock_destroy', [_pthread_rwlock_t_p]),
		('pthread_rwlock_init', [_pthread_rwlock_t_p, ctypes.c_void_p]),
		('pthread_rwlock_unlock', [_pthread_rwlock_t_p]),
		('pthread_rwlock_wrlock', [_pthread_rwlock_t_p]),
		('pthread_rwlock_rdlock', [_pthread_rwlock_t_p]),
		('pthread_rwlock_trywrlock', [_pthread_rwlock_t_p]),
		('pthread_rwlock_tryrdlock', [_pthread_rwlock_t_p]),
	]

	def _checkForErrors(result, func, _):
		if result != 0:
			error = os.strerror(result)
			raise OSError(result, '{} failed: {}'.format(func.__name__, error))

	def _defineArgtypes(library, name, args):
		func = getattr(library, name)
		func.argtypes = args
		func.errcheck = _checkForErrors

	# At the global level we add argument types and error checking to the
	# functions:
	for function, argtypes in _api:
		_defineArgtypes(_librt, function, argtypes)

	def _createRWLock():
		lock = _pthread_rwlock_t()
		plock = ctypes.pointer(lock)

		# Initialize the rwlock
		_librt.pthread_rwlock_init(plock, None)
		return _rwlock(lock, plock, _librt.pthread_rwlock_destroy)

	def _acquireRead(lock):
		_librt.pthread_rwlock_rdlock(lock.plock)

	def _acquireWrite(lock):
		_librt.pthread_rwlock_wrlock(lock.plock)

	def _tryAcquireRead(lock):
		try:
			_librt.pthread_rwlock_tryrdlock(lock.plock)
		except OSError:
			return False
		else:
			return True

	def _tryAcquireWrite(lock):
		try:
			_librt.pthread_rwlock_trywrlock(lock.plock)
		except OSError:
			return False
		else:
			return True

	def _releaseRead(lock):
		_librt.pthread_rwlock_unlock(lock.plock)

	def _releaseWrite(lock):
		_librt.pthread_rwlock_unlock(lock.plock)

class RWLock(object):
	"""
	Multi-reader, single-writer lock.
	"""
	def __init__(self):
		self._lock = _createRWLock()

	def AcquireRead(self):
		"""
		Acquire the lock for reading. Multiple reads may be done simultaneously as long as no writes are occurring.
		"""
		_acquireRead(self._lock)

	def AcquireWrite(self):
		"""
		Acquire the lock for writing. Only one write my occur at a time, and will block until all active reads are done.
		"""
		_acquireWrite(self._lock)

	def TryAcquireRead(self):
		"""
		Try to acquire a read lock
		:return: True if acquired, false otherwise
		:rtype: bool
		"""
		return _tryAcquireRead(self._lock)

	def TryAcquireWrite(self):
		"""
		Try to acquire a write lock
		:return: True if acquired, false otherwise
		:rtype: bool
		"""
		return _tryAcquireWrite(self._lock)

	def ReleaseRead(self):
		"""
		Release a read lock
		"""
		_releaseRead(self._lock)

	def ReleaseWrite(self):
		"""
		Release a write lock
		"""
		_releaseWrite(self._lock)

	def __del__(self):
		self._lock.Close()

@contextlib.contextmanager
def Reader(lock):
	"""
	Context manager for acquiring and releasing a read lock
	:param lock: lock to acquire
	:type lock: RWLock
	"""
	lock.AcquireRead()
	yield
	lock.ReleaseRead()

@contextlib.contextmanager
def Writer(lock):
	"""
	Context manager for acquiring and releasing a write lock
	:param lock: lock to acquire
	:type lock: RWLock
	"""
	lock.AcquireWrite()
	yield
	lock.ReleaseWrite()
