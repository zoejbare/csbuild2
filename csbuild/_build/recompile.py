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
.. module:: recompile
	:synopsis: Utility functions for checking recompilability of a file or files
"""

from __future__ import unicode_literals, division, print_function

from . import project, input_file
from .._utils import memo, ordered_set
from ..toolchain import CompileChecker
from .._utils.decorators import TypeChecked
from .. import perf_timer, log

class Completed(object):
	"""
	Represents a value that has already been determined.
	Thin wrapper where Get and TryGet both return the value, and Unlocked returns true always

	:param value: The value to wrap
	:type value: any
	"""
	def __init__(self, value):
		self._value = value

	def Get(self):
		"""
		Get the value

		:return: the value
		:rtype: any
		"""
		return self._value

	def TryGet(self):
		"""
		Try to get the value

		:return: the value
		:rtype: any
		"""
		return self._value

	def Unlocked(self):
		"""
		Check if the object is unlocked

		:return: True always
		:rtype: bool
		"""
		return True

class Deferred(object):
	"""
	Represents a deferred calculation that's waiting on results from one or more dependency

	:param checker: The compile checker to use for checking values
	:type checker: CompileChecker
	:param itemToWrite: The item to commit the final calculated value to
	:type itemToWrite: memo.MemoObject
	:param values: The values that must be resulved before committing a result
	:type values: list
	"""
	def __init__(self, checker, itemToWrite, values):
		self._item = itemToWrite
		self._values = values
		self._checker = checker

	def Get(self):
		"""
		Get the value. Commits to the stored MemoObject after retrieving all values.

		:return: the value
		:rtype: any
		"""
		value = self._checker.CondenseRecompileChecks([value.Get() for value in self._values])
		self._item.Commit(value)
		return value

	def TryGet(self):
		"""
		Try to get the value. If successful, commits to the stored MemoObject after retrieving all values.

		:return: the value
		:rtype: any
		:raises memo.NotReady: If the attempt fails
		"""
		datas = []
		throw = False
		for data in self._values:
			try:
				datas.append(data.TryGet())
			except memo.NotReady:
				throw = True

		if throw:
			raise memo.NotReady()

		value = self._checker.CondenseRecompileChecks(datas)
		self._item.Commit(value)
		return value

	def Unlocked(self):
		"""
		Check if the object can be read from

		:return: true if all of its wrapped items are unlocked
		:rtype: bool
		"""
		return len([item for item in self._values if not item.Unlocked()]) == 0

def CheckCompilabilityForFile(buildProject, checker, inputFile, valueMemo, allDeps):
	"""
	Check compatibility for a single file

	:param buildProject: Project being filtered
	:type buildProject: project.Project
	:param checker: Checker
	:type checker: CompileChecker
	:param inputFile: Input file to check
	:type inputFile: input_file.InputFile
	:param valueMemo: memo to collect memoized values from
	:type valueMemo: memo.Memo
	:param allDeps: All processed dependencies for a given set of checked files used to avoid redundant processing when there are recursive includes.
	:type allDeps: set[str]
	:return: A value with a blocking Get() and not-blocking TryGet()
	:rtype: any
	"""
	# First, check if someone's already processed (or is processing) this input.
	# If so, return their result (which may eventually block on the eventual read
	# if they're still working on it, but the point is we shouldn't work on it)
	if inputFile in valueMemo:
		return valueMemo[inputFile]

	# If no one has fully processed it, try to get write permission for it.
	# This is likely to succeed, but there is a chance another thread has beaten us
	# to it after we did our read check. If this is the case, we'll go ahead and
	# return their in-progress MemoObject, which will block on read if they aren't
	# finished yet when the read happens.
	readyForWrite, item = valueMemo.GetForWrite(inputFile)
	if not readyForWrite:
		return item

	with perf_timer.PerfTimer("Non-memoized compilability check"):
		# At this point we've successfully obtained the write lock on this object.
		# We should be the only ones working on it and our write lock should block
		# readers, but there should not be any other writers.
		# Time to calculate the value.

		# First get the time of the current input file.
		values = [Completed(checker.GetRecompileValue(buildProject, inputFile))]

		# Now walk the dependencies
		deps = [input_file.InputFile(dep) for dep in checker.GetDependencies(buildProject, inputFile) if dep not in allDeps]
		if not deps:
			return values[0]

		# Update the complete dependency list with all the new dependencies found for the current input file.
		allDeps.update([dep.filename for dep in deps])

		for dep in deps:
			# For each dependency, recurse and add the result (completed or not) to our values.
			nestedItem = CheckCompilabilityForFile(buildProject, checker, dep, valueMemo, allDeps)
			values.append(nestedItem)

		ret = Deferred(checker, item, values)
		# Go ahead and resolve everything we can by doing a TryGet(). If this resolves EVERYTHING,
		# we'll just convert from Deferred to Completed. If not, we'll return a Deferred that will
		# be tried again at each level up the chain until it works!
		try:
			with perf_timer.PerfTimer("Cross-thread Partial Resolution"):
				return Completed(ret.TryGet())
		except memo.NotReady:
			return ret

@TypeChecked(buildProject=project.Project, checker=CompileChecker, inputFiles=ordered_set.OrderedSet)
def ShouldRecompile(buildProject, checker, inputFiles):
	"""
	Determine whether or not a file or list of files should be recompiled.

	:param buildProject: Project being filtered
	:type buildProject: project.Project
	:param checker: Compile checker to check with
	:type checker: CompileChecker
	:param inputFiles: files to check
	:type inputFiles: ordered_set.OrderedSet[input_file.InputFile]
	:return: True if the list of inputs should be reprocessed, false otherwise
	:rtype: bool
	"""
	with perf_timer.PerfTimer("Filter for recompile"):
		log.Info("Checking if we should compile {}", inputFiles)
		baseline = checker.GetRecompileBaseline(buildProject, inputFiles)
		if baseline is None:
			return True
		values = [CheckCompilabilityForFile(buildProject, checker, f, checker.memo, set()) for f in inputFiles]

		with perf_timer.PerfTimer("Cross-thread Final Resolution"):
			return checker.ShouldRecompile(checker.CondenseRecompileChecks([value.Get() for value in values]), baseline)
