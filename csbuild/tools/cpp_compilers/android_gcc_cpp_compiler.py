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
.. module:: android_base_cpp_compiler
	:synopsis: Android GCC compiler tool for C++.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import os

from ..common.android_tool_base import AndroidToolBase, AndroidStlLibType

from .gcc_cpp_compiler import GccCppCompiler


class AndroidGccCppCompiler(GccCppCompiler, AndroidToolBase):
	"""
	Android GCC c++ compiler implementation
	"""
	supportedArchitectures = AndroidToolBase.supportedArchitectures

	def __init__(self, projectSettings):
		GccCppCompiler.__init__(self, projectSettings)
		AndroidToolBase.__init__(self, projectSettings)


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		"""
		Run project setup, if any, before building the project, but after all dependencies have been resolved.

		:param project: project being set up
		:type project: csbuild._build.project.Project
		"""
		GccCppCompiler.SetupForProject(self, project)
		AndroidToolBase.SetupForProject(self, project)

	def _getComplierName(self, isCpp):
		return self._androidInfo.gppPath if isCpp else self._androidInfo.gccPath

	def _getArchitectureArgs(self, project):
		# The architecture is implied from the executable being run.
		return []

	def _getSystemArgs(self, project, isCpp):
		stlIncPaths = {
			AndroidStlLibType.Gnu: self._androidInfo.libStdCppIncludePaths,
			AndroidStlLibType.LibCpp: self._androidInfo.libCppIncludePaths,
			AndroidStlLibType.StlPort: self._androidInfo.stlPortIncludePaths,
		}.get(self._androidStlLibType, None)
		assert stlIncPaths, "Invalid Android STL library type: {}".format(self._androidStlLibType)

		args = []

		# Add the sysroot include paths.
		for path in self._androidInfo.systemIncludePaths:
			args.extend([
				"-isystem",
				path,
			])

		if isCpp:
			# Add each include path for the selected version of STL.
			for path in stlIncPaths:
				args.extend([
					"-isystem",
					path,
				])

		return args
