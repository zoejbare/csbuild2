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
.. module:: clang_tool_base
	:synopsis: Abstract base class for clang tools.

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import subprocess

from abc import ABCMeta

from ..._utils.decorators import MetaClass
from ...toolchain import Tool
from ... import commands


def _ignore(_):
	pass

def _noLogOnRun(shared, msg):
	_ignore(shared)
	_ignore(msg)


class ClangHostToolInfo(object):
	"""
	Class for maintaining data output by clang needed by the build process.
	"""
	Instance = None

	def __init__(self):
		try:
			# Verify the 'xcrun' program exists.
			subprocess.call(["clang"], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		except:
			raise IOError("Program 'clang' could not be found; please make sure you have it installed on your system")

		_, targetTriplet, _ = commands.Run(["clang", "-dumpmachine"], stdout = _noLogOnRun, stderr = _noLogOnRun)
		targetSegments = targetTriplet.strip().split("-", 1)

		self._nativeTargetPrefix = targetSegments[0] if targetSegments else None
		self._nativeTargetSuffix = targetSegments[1] if targetSegments and len(targetSegments) > 1 else None

	@property
	def nativeTargetPrefix(self):
		"""
		Return the native target triple prefix
		"""
		return self._nativeTargetPrefix

	@property
	def nativeTargetSuffix(self):
		"""
		Return the native target triple suffix
		"""
		return self._nativeTargetSuffix


@MetaClass(ABCMeta)
class ClangToolBase(Tool):
	"""
	Parent class for all tools targeting clang builds.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)

		self._clangToolInfo = None


	####################################################################################################################
	### Base methods
	####################################################################################################################

	def _getArchitectureTargetTripleArgs(self, project):
		args = []
		target = self._getArchTarget(project)

		if target:
			args.extend([
				"-target", target,
			])

		return args

	def _getArchTarget(self, project):
		targetPrefix = self._clangToolInfo.nativeTargetPrefix
		targetSuffix = self._clangToolInfo.nativeTargetSuffix

		if not targetPrefix or not targetSuffix:
			return None

		# When necessary fill in the architecture name with something clang expects.
		targetPrefix = {
			"x86": "i386",
			"x64": "x86_64",
			"arm": targetPrefix \
				if targetPrefix.startswith("armv") \
				else "armv6",
			"arm64": targetPrefix \
				if targetPrefix.startswith("aarch64") \
				else "aarch64",
		}.get(project.architectureName, None)
		if not targetPrefix:
			return None

		return "{}-{}".format(targetPrefix, targetSuffix)

	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		Tool.SetupForProject(self, project)

		# Create the clang tool info if the singleton doesn't already exist.
		if not ClangHostToolInfo.Instance:
			ClangHostToolInfo.Instance = ClangHostToolInfo()

		self._clangToolInfo = ClangHostToolInfo.Instance
