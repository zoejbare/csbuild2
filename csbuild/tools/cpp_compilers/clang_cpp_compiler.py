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
.. module:: clang_cpp_compiler
	:synopsis: Clang compiler tool for C++.

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild

from .gcc_cpp_compiler import GccCppCompiler
from ..._utils import PlatformString

import subprocess

class ClangCppCompiler(GccCppCompiler):
	"""
	Clang compiler implementation
	"""

	def __init__(self, projectSettings):
		GccCppCompiler.__init__(self, projectSettings)

		targetTriplet = PlatformString(subprocess.check_output(["clang", "-dumpmachine"]))
		targetSegments = targetTriplet.strip().split("-", 1)

		self._nativeTargetPrefix = targetSegments[0] if targetSegments else None
		self._nativeTargetSuffix = targetSegments[1] if targetSegments and len(targetSegments) > 1 else None


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def _getComplierName(self, project, isCpp):
		return "clang++" if isCpp else "clang"

	def _getDefaultArgs(self, project):
		args = ["-fPIC"] if project.projectType == csbuild.ProjectType.SharedLibrary else []
		return args

	def _getArchitectureArgs(self, project):
		args = GccCppCompiler._getArchitectureArgs(self, project)
		target = self._getArchTarget(project)

		if target:
			if args is None:
				args = []

			args.extend([
				"-target", target,
			])

		return args


	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getArchTarget(self, project):
		if not self._nativeTargetPrefix or not self._nativeTargetSuffix:
			return None

		# When necessary fill in the architecture name with something clang expects.
		targetPrefix = {
			"x86": "i386",
			"x64": "x86_64",
			"arm": self._nativeTargetPrefix \
				if self._nativeTargetPrefix.startswith("armv") \
				else "armv6",
			"arm64": self._nativeTargetPrefix \
				if self._nativeTargetPrefix.startswith("aarch64") \
				else "aarch64",
		}.get(project.architectureName, None)
		if not targetPrefix:
			return None

		return "{}-{}".format(targetPrefix, self._nativeTargetSuffix)
