# -*- coding: utf-8 -*-

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
.. module:: perf_timer
	:synopsis: Thread-safe performance timer to collect high-level performance statistics

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import time
import threading
import re
from collections import deque

from . import log
from ._utils import FormatTime, shared_globals

class PerfTimer(object):
	"""
	Performance timer to collect performance stats on csbuild to aid in diagnosing slow builds.
	Used as a context manager around a block of code, will store cumulative execution time for that block.

	:param blockName: The name of the block to store execution for.
	:type blockName: str
	"""
	perfQueue = deque()
	perfStack = threading.local()

	def __init__(self, blockName):
		if shared_globals.runPerfReport:
			self.blockName = blockName
			self.incstart = 0
			self.excstart = 0
			self.exclusive = 0
			self.inclusive = 0
			self.scopeName = blockName

	def __enter__(self):
		if shared_globals.runPerfReport:
			now = time.time()
			try:
				prev = PerfTimer.perfStack.stack[-1]
				prev.exclusive += now - prev.excstart
				self.scopeName = prev.scopeName + "::" + self.blockName

				PerfTimer.perfStack.stack.append(self)
			except:
				PerfTimer.perfStack.stack = [self]

			self.incstart = now
			self.excstart = now

	def __exit__(self, excType, excVal, excTb):
		if shared_globals.runPerfReport:
			now = time.time()
			try:
				prev = PerfTimer.perfStack.stack[-2]
				prev.excstart = now
			except:
				pass

			self.exclusive += now - self.excstart
			self.inclusive = now - self.incstart

			PerfTimer.perfQueue.append((self.scopeName, self.inclusive, self.exclusive, threading.current_thread().ident))
			PerfTimer.perfStack.stack.pop()

	@staticmethod
	def PrintPerfReport():
		"""
		Print out all the collected data from PerfTimers in a heirarchical tree
		"""
		fullreport = {}
		threadreports = {}
		while True:
			try:
				pair = PerfTimer.perfQueue.popleft()
				fullreport.setdefault(pair[0], [0,0,0,[],[]])
				fullreport[pair[0]][0] += pair[1]
				fullreport[pair[0]][1] += pair[2]
				fullreport[pair[0]][2] += 1

				threadreport = threadreports.setdefault(pair[3], {})
				threadreport.setdefault(pair[0], [0,0,0])
				threadreport[pair[0]][0] += pair[1]
				threadreport[pair[0]][1] += pair[2]
				threadreport[pair[0]][2] += 1
			except IndexError:
				break

		if not fullreport:
			return

		log.Custom(log.Color.WHITE, "PERF", "Perf reports:")

		def _recurse(report, sortedKeys, prefix, replacementText, printed, itemfmt):
			prev = (None, None)

			for key in sortedKeys:
				if key in printed:
					continue

				if key.startswith(prefix):
					printkey = key.replace(prefix, replacementText, 1)
					if printkey.find("::") != -1:
						continue
					if prev != (None, None):
						log.Custom(
							log.Color.WHITE,
							"PERF",
							itemfmt,
							prev[0],
							FormatTime(report[prev[1]][0]),
							FormatTime(report[prev[1]][1]),
							report[prev[1]][2],
							FormatTime(report[prev[1]][0]/report[prev[1]][2]),
							FormatTime(report[prev[1]][1]/report[prev[1]][2]),
						)
						printed.add(prev[1])
						_recurse(report, sortedKeys, prev[1] + "::", (" │  " * int(len(replacementText)/3)) + " ├─ ", printed, itemfmt)
					prev = (printkey, key)

			if prev != (None, None):
				printkey = prev[0].replace("├", "└")
				log.Custom(
					log.Color.WHITE,
					"PERF",
					itemfmt,
					printkey,
					FormatTime(report[prev[1]][0]),
					FormatTime(report[prev[1]][1]),
					report[prev[1]][2],
					FormatTime(report[prev[1]][0]/report[prev[1]][2]),
					FormatTime(report[prev[1]][1]/report[prev[1]][2]),
				)
				printed.add(prev[1])
				_recurse(report, sortedKeys, prev[1] + "::", ("    " * int(len(replacementText)/3)) + " ├─ ", printed, itemfmt)

		def _alteredKey(key):
			return re.sub("([^:]*::)", "    ", key)

		def _printReport(report, threadId):
			if not report:
				return

			maxlen = len(str(threadId))
			totalcount = 0
			for key in report:
				maxlen = max(len(_alteredKey(key)), maxlen)
				totalcount += report[key][2]

			log.Custom(log.Color.WHITE, "PERF", "")
			linefmt = "+={{:=<{}}}=+============+============+=======+============+============+".format(maxlen)
			line = linefmt.format('')
			log.Custom(log.Color.WHITE, "PERF", line)
			headerfmt = "| {{:<{}}} | INCLUSIVE  | EXCLUSIVE  | CALLS |  INC_MEAN  |  EXC_MEAN  |".format(maxlen)
			log.Custom(log.Color.WHITE, "PERF", headerfmt, threadId)
			log.Custom(log.Color.WHITE, "PERF", line)
			itemfmt = "| {{:{}}} | {{:>10}} | {{:>10}} | {{:>5}} | {{:>10}} | {{:>10}} |".format(maxlen)
			printed = set()
			sortedKeys = sorted(report, reverse=True, key=lambda x: report[x][0])
			total = 0
			for key in sortedKeys:
				if key in printed:
					continue
				if key.find("::") != -1:
					continue
				log.Custom(
					log.Color.WHITE,
					"PERF",
					itemfmt,
					key,
					FormatTime(report[key][0]),
					FormatTime(report[key][1]),
					report[key][2],
					FormatTime(report[key][0]/report[key][2]),
					FormatTime(report[key][1]/report[key][2]),
				)
				total += report[key][0]
				_recurse(report, sortedKeys, key + "::", " ├─ ", printed, itemfmt)

			log.Custom(log.Color.WHITE, "PERF", line)
			log.Custom(
				log.Color.WHITE,
				"PERF",
				itemfmt,
				"TOTAL",
				FormatTime(total),
				FormatTime(total),
				totalcount,
				FormatTime(total/totalcount),
				FormatTime(total/totalcount)
			)
			log.Custom(log.Color.WHITE, "PERF", line)


		for threadId, report in threadreports.items():
			if threadId == threading.current_thread().ident:
				continue
			else:
				_printReport(report, "Worker Thread {}".format(threadId))

		_printReport(threadreports[threading.current_thread().ident], "Main Thread")
		_printReport(fullreport, "CUMULATIVE")
