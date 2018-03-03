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
.. module:: gcc_cpp_compiler
	:synopsis: gcc compiler tool for C++

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import os
import csbuild

from .cpp_compiler_base import CppCompilerBase
from ..common.tool_traits import HasDebugLevel, HasOptimizationLevel

DebugLevel = HasDebugLevel.DebugLevel
OptimizationLevel = HasOptimizationLevel.OptimizationLevel

class GccCppCompiler(CppCompilerBase):
	"""
	GCC compiler implementation
	"""
	supportedArchitectures = {"x86", "x64"}
	outputFiles = {".o"}


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def _getOutputFiles(self, project, inputFile):
		filename = os.path.splitext(os.path.basename(inputFile.filename))[0] + ".o"
		return os.path.join(project.GetIntermediateDirectory(inputFile), filename)

	def _getCommand(self, project, inputFile, isCpp):
		cmdExe = self._getComplierName(isCpp)
		extraFlags = self._cxxFlags if isCpp else self._cFlags
		cmd = [cmdExe] \
			+ self._getInputFileArgs(inputFile) \
			+ self._getDefaultArgs(project) \
			+ self._getOutputFileArgs(project, inputFile) \
			+ self._getPreprocessorArgs() \
			+ self._getIncludeDirectoryArgs() \
			+ self._getDebugArgs() \
			+ self._getOptimizationArgs() \
			+ self._getArchitectureArgs(project) \
			+ extraFlags
		return [arg for arg in cmd if arg]


	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getComplierName(self, isCpp):
		return "g++" if isCpp else "gcc"

	def _getDefaultArgs(self, project):
		args = ["--pass-exit-codes"]
		if project.projectType == csbuild.ProjectType.SharedLibrary:
			args.append("-fPIC")
		return args

	def _getInputFileArgs(self, inputFile):
		return ["-c", inputFile.filename]

	def _getOutputFileArgs(self, project, inputFile):
		return ["-o", self._getOutputFiles(project, inputFile)]

	def _getPreprocessorArgs(self):
		return ["-D{}".format(d) for d in self._defines] + ["-U{}".format(u) for u in self._undefines]

	def _getIncludeDirectoryArgs(self):
		return ["-I" + d for d in self._includeDirectories]

	def _getDebugArgs(self):
		if self._debugLevel != DebugLevel.Disabled:
			return ["-g"]
		return []

	def _getOptimizationArgs(self):
		arg = {
			OptimizationLevel.Size: "s",
			OptimizationLevel.Speed: "fast",
			OptimizationLevel.Max: "3",
		}
		return ["-O{}".format(arg.get(self._optLevel, "0"))]

	def _getArchitectureArgs(self, project):
		arg = "-m64" if project.architectureName == "x64" else "-m32"
		return [arg]
