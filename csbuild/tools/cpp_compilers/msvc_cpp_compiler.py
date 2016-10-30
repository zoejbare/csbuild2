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
.. module:: msvc_cpp_compiler
	:synopsis: msvc compiler tool for C++

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import os

from .cpp_compiler_base import CppCompilerBase
from ..common.msvc_tool_base import MsvcToolBase
from ..common.tool_traits import HasDebugLevel, HasOptimizationLevel

DebugLevel = HasDebugLevel.DebugLevel
OptimizationLevel = HasOptimizationLevel.OptimizationLevel

class MsvcCppCompiler(MsvcToolBase, CppCompilerBase):
	"""
	MSVC compiler tool implementation.
	"""
	supportedPlatforms = {"Windows"}
	supportedArchitectures = {"x86", "x64"}
	outputFiles = {".obj"}


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def __init__(self, projectSettings):
		MsvcToolBase.__init__(self, projectSettings)
		CppCompilerBase.__init__(self, projectSettings)

	def _getEnv(self, project):
		return self._vcvarsall.env

	def _getOutputFiles(self, project, inputFile):
		outputPath = os.path.join(project.GetIntermediateDirectory(inputFile), os.path.splitext(os.path.basename(inputFile.filename))[0])
		outputFiles = ["{}.obj".format(outputPath)]

		if self._debugLevel in [DebugLevel.ExternalSymbols, DebugLevel.ExternalSymbolsPlus]:
			outputFiles.append("{}.pdb".format(outputPath))
			if self._debugLevel == DebugLevel.ExternalSymbolsPlus:
				outputFiles.append("{}.idb".format(outputPath))

		return tuple(outputFiles)

	def _getCommand(self, project, inputFile, isCpp):
		compilerPath = os.path.join(self._vcvarsall.binPath, "cl.exe")
		cmd = [compilerPath]  \
			+ self._getDefaultArgs() \
			+ self._getPreprocessorArgs() \
			+ [
				self._getDebugArg(),
				self._getOptimizationArg(),
				self._getRuntimeLinkageArg(),
				self._getRuntimeErrorChecksArg(),
			] \
			+ self._getOutputFileArgs(project, inputFile) \
			+ [inputFile.filename]
		return [arg for arg in cmd if arg]

	def SetupForProject(self, project):
		MsvcToolBase.SetupForProject(self, project)
		CppCompilerBase.SetupForProject(self, project)


	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getDefaultArgs(self):
		return ["/nologo", "/c", "/Oi", "/GS"]

	def _getDebugArg(self):
		arg = {
			DebugLevel.EmbeddedSymbols: "/Z7",
			DebugLevel.ExternalSymbols: "/Zi",
			DebugLevel.ExternalSymbolsPlus: "/ZI",
		}
		return arg.get(self._debugLevel, "")

	def _getOptimizationArg(self):
		arg = {
			OptimizationLevel.Size: "/O1",
			OptimizationLevel.Speed: "/O2",
			OptimizationLevel.Max: "/Ox",
		}
		return arg.get(self._optLevel, "/Od")

	def _getRuntimeLinkageArg(self):
		return "/{}{}".format(
			"MT" if self._staticRuntime else "MD",
			"d" if self._debugRuntime else ""
		)

	def _getPreprocessorArgs(self):
		return ["/D{}".format(d) for d in self._defines] + ["/U{}".format(u) for u in self._undefines]

	def _getRuntimeErrorChecksArg(self):
		return "/RTC1" if self._optLevel == OptimizationLevel.Disabled else ""

	def _getOutputFileArgs(self, project, inputFile):
		outputPath = os.path.join(project.GetIntermediateDirectory(inputFile), os.path.splitext(os.path.basename(inputFile.filename))[0])
		args = ["/Fo{}".format("{}.obj".format(outputPath))]

		if self._debugLevel in [DebugLevel.ExternalSymbols, DebugLevel.ExternalSymbolsPlus]:
			args.append("/Fd{}".format("{}.pdb".format(outputPath)))

		return args
