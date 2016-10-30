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
.. module:: event
	:synopsis: Native lock-free event system for supported platforms

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import platform
import ctypes
import os
import threading
import time

from .._testing import testcase

class _event(object):
	def __init__(self, ident, event, deleter):
		self.ident = ident
		self.event = event
		self.deleter = deleter

	def Close(self):
		"""Close the event"""
		self.deleter(self.event)

if platform.system() == "Windows":
	CreateEventA = ctypes.windll.kernel32.CreateEventA
	GetLastError = ctypes.windll.kernel32.GetLastError
	SetEvent = ctypes.windll.kernel32.SetEvent
	WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
	def _createEvent():
		return _event(0, CreateEventA(None, False, False, None), ctypes.windll.kernel32.CloseHandle)

	def _setEvent(event):
		SetEvent(event.event)

	def _waitForEvent(event):
		WaitForSingleObject(event.event, -1)

elif platform.system() == "Linux":
	libc = ctypes.cdll.LoadLibrary("libc.so.6")
	def _createEvent():
		return _event(0, libc.eventfd(0, 0), os.close)

	def _setEvent(event):
		os.write(event.event, ctypes.c_ulonglong(1))

	def _waitForEvent(event):
		os.read(event.event, 8)

else:
	import select
	from select import kevent, kqueue
	_highId = 0
	_idLock = threading.Lock()
	KQ_FILT_USER = -10 #select, for some reason, doesn't expose these...
	KQ_NOTE_TRIGGER = 0x01000000
	KQ_NOTE_FFNOP = 0x0

	def _createEvent():
		global _highId
		with _idLock:
			_highId += 1
			ident = _highId
		queue = kqueue()
		events = [
			kevent(
				ident=ident,
				filter=KQ_FILT_USER,
				flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR, # pylint: disable=no-member
				fflags=KQ_NOTE_FFNOP
			)
		]
		queue.control(events, 0)
		return _event(ident, queue, lambda x: x.close())

	def _setEvent(event):
		events = [
			kevent(
				ident=event.ident,
				filter=KQ_FILT_USER,
				flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR, # pylint: disable=no-member
				fflags=KQ_NOTE_TRIGGER
			)
		]
		event.event.control(events, 0)

	def _waitForEvent(event):
		event.event.control(None, 1)

class Event(object):
	"""
	An event object that can be used for thread synchronization without the use of locks
	Note that only one thread may wait on an event at a time.
	This does not require a guardian bool as does a condition variable
	"""
	def __init__(self):
		self._event = _createEvent()

	def Notify(self):
		"""
		Wake up the thread that is waiting on this event
		"""
		# TODO: I do not know why this occasionally fails on Windows with an Invalid Handle error
		# For some reason, it will randomly fail, and then a second call will succeed.
		# For now I'm just going to retry on a failure, maybe some day I'll figure out the cause...
		try:
			_setEvent(self._event)
		except OSError:
			_setEvent(self._event)

	def Wait(self):
		"""
		Sleep until an event is ready.
		If Notify() is called before Wait(), Wait() will return immediately.
		"""
		_waitForEvent(self._event)

	def __del__(self):
		self._event.Close()

class TestEvent(testcase.TestCase):
	"""Test events"""
	# pylint: disable=invalid-name
	def testSimpleEventWorks(self):
		"""Simple event test"""
		event = Event()

		def _thread():
			event.Wait()

		t = threading.Thread(target=_thread)
		t.start()
		time.sleep(0.5)
		event.Notify()
		t.join()

	def testEventDoesntReturnUntilNotified(self):
		"""Test that events don't return until they're notified"""
		event = Event()

		def _thread():
			start = time.time()
			event.Wait()
			end = time.time()
			self.assertGreater(end-start, 0.45)

		t = threading.Thread(target=_thread)
		t.start()

		time.sleep(0.5)
		event.Notify()
		t.join()

	def testEventTriggersWhenNotifyBeforeWait(self):
		"""Test that notification before wait causes wait to return immediately"""
		event = Event()

		def _thread():
			time.sleep(0.5)
			event.Wait()

		t = threading.Thread(target=_thread)
		t.start()

		event.Notify()
		t.join()
