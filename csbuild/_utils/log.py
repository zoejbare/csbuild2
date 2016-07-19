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
.. module:: log
	:synopsis: Thread-safe logging system

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import sys
import threading
import re

if sys.version_info[0] >= 3:
	import queue
else:
	import Queue as queue

from . import terminfo, shared_globals, BytesType, StrType

_logQueue = queue.Queue()
_stopEvent = object()
_callbackQueue = None

def _writeLog(color, level, msg):
	if shared_globals.colorSupported:
		terminfo.TermInfo.SetColor(color)
		sys.stdout.write("{}: ".format(level))
		sys.stdout.flush()
		terminfo.TermInfo.ResetColor()

		split = re.split(R"(<&\w*>)(.*?)(</&>|$)", msg)
		for piece in split:
			match = re.match(R"<&(\w*)>", piece)
			if match:
				color = getattr(terminfo.TermColor, match.group(1))
				terminfo.TermInfo.SetColor(color)
			elif piece == "</&>":
				terminfo.TermInfo.ResetColor()
			else:
				sys.stdout.write(piece)
				sys.stdout.flush()

		sys.stdout.write("\n")
		sys.stdout.flush()
		terminfo.TermInfo.ResetColor()
	else:
		sys.stdout.write("{}: ".format(level))

		split = re.split(R"(<&\w*>)(.*?)(</&>|$)", msg)
		for piece in split:
			match = re.match(R"<&(\w*)>", piece)
			if match or piece == "</&>":
				continue
			else:
				sys.stdout.write(piece)

		sys.stdout.write("\n")
		sys.stdout.flush()
	if shared_globals.logFile:
		shared_globals.logFile.write("{0}: {1}\n".format(level, msg))

def Pump():
	"""
	Print logs that have been inserted into the queue from another thread.
	Logs inserted on the main thread are printed immediately -
	in single-threaded contexts this function is irrelevant
	"""
	try:
		# Pump all logs till we get an Empty exception, then return
		while True:
			event = _logQueue.get(block=False)
			_writeLog(*event)
	except queue.Empty:
		return

def SetCallbackQueue(callbackQueue):
	"""
	Set the callback queue for threaded logging - a Pump call will be added to the queue each time a log call is made.
	This will ensure that logs are printed as quickly as possible after being inserted into the queue.

	:param callbackQueue: A queue for executing Pump calls
	:type callbackQueue: queue.Queue
	:return:
	"""
	global _callbackQueue
	_callbackQueue = callbackQueue

_mainThread = threading.currentThread()

def _logMsg(color, level, msg, quietThreshold):
	"""Print a message to stdout"""
	if shared_globals.quiet < quietThreshold:
		if isinstance(msg, BytesType):
			msg = msg.decode("UTF-8")
		if threading.currentThread() == _mainThread:
			_writeLog(color, level, msg)
		else:
			assert _callbackQueue is not None, "Threaded logging requires a callback queue (shared with ThreadPool)"
			_logQueue.put((color, level, msg), block=False)
			_callbackQueue.put(Pump)


def _formatMsg(msg, *args, **kwargs):
	if not isinstance(msg, BytesType) and not isinstance(msg, StrType):
		return repr(msg)
	elif args or kwargs:
		return msg.format(*args, **kwargs)
	return msg


def Error(msg, *args, **kwargs):
	"""
	Log an error message

	:param msg: Text to log
	:type msg: BytesType, StrType
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.RED, "ERROR", msg, 3)
	shared_globals.errors.append(msg)


def Warn(msg, *args, **kwargs):
	"""
	Log a warning

	:param msg: Text to log
	:type msg: BytesType, StrType
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.YELLOW, "WARN", msg, 3)
	shared_globals.warnings.append(msg)


def WarnNoPush(msg, *args, **kwargs):
	"""
	Log a warning, don't push it to the list of warnings to be echoed at the end of compilation.

	:param msg: Text to log
	:type msg: str
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.YELLOW, "WARN", msg, 3)


def Info(msg, *args, **kwargs):
	"""
	Log general info. This info only appears with -v specified.

	:param msg: Text to log
	:type msg: str
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.CYAN, "INFO", msg, 1)


def Build(msg, *args, **kwargs):
	"""
	Log info related to building

	:param msg: Text to log
	:type msg: str
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.MAGENTA, "BUILD", msg, 2)


def Test(msg, *args, **kwargs):
	"""
	Log info related to testing - typically used by the unit test framework, but could be used
	by makefiles that run tests as part of a build

	:param msg: Text to log
	:type msg: str
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.MAGENTA, "TEST", msg, 2)


def Linker(msg, *args, **kwargs):
	"""
	Log info related to linking

	:param msg: Text to log
	:type msg: str
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.GREEN, "LINKER", msg, 2)


def Thread(msg, *args, **kwargs):
	"""
	Log info related to threads, particularly stalls caused by waiting on another thread to finish

	:param msg: Text to log
	:type msg: str
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.BLUE, "THREAD", msg, 2)


def Install(msg, *args, **kwargs):
	"""
	Log info related to the installer

	:param msg: Text to log
	:type msg: str
	:param args: Args to str.format
	:type args: any
	:param kwargs: args to str.format
	:type kwargs: any
	"""
	msg = _formatMsg(msg, *args, **kwargs)
	_logMsg(terminfo.TermColor.WHITE, "INSTALL", msg, 2)
