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
.. module:: msvc_assembler
	:synopsis: msvc assembler tool

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import os

from .assembler_base import AssemblerBase
from ..common.msvc_tool_base import MsvcToolBase

class MsvcAssembler(MsvcToolBase, AssemblerBase):
	"""
	MSVC assembler implementation.
	"""
	supportedPlatforms = {"Windows"}
	supportedArchitectures = {"x86", "x64"}
	inputFiles={".asm"}
	outputFiles = {".obj"}


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def __init__(self, projectSettings):
		MsvcToolBase.__init__(self, projectSettings)
		AssemblerBase.__init__(self, projectSettings)

	def _getEnv(self, project):
		return self.vcvarsall.env

	def _getOutputFiles(self, project, inputFile):
		outputPath = os.path.join(project.GetIntermediateDirectory(inputFile), os.path.splitext(os.path.basename(inputFile.filename))[0])

		return tuple({ "{}.obj".format(outputPath) })

	def _getCommand(self, project, inputFile):
		assemblerPath = self._getExecutablePath(project)
		cmd = [assemblerPath]  \
			+ self._getDefaultArgs() \
			+ self._getPreprocessorArgs() \
			+ self._getIncludeDirectoryArgs() \
			+ self._asmFlags \
			+ self._getOutputFileArgs(project, inputFile) \
			+ [inputFile.filename]
		return [arg for arg in cmd if arg]

	def SetupForProject(self, project):
		MsvcToolBase.SetupForProject(self, project)
		AssemblerBase.SetupForProject(self, project)


	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getExecutablePath(self, project):
		return os.path.join(self.vcvarsall.binPath, "ml64.exe" if project.architectureName == "x64" else "ml.exe")

	def _getDefaultArgs(self):
		args = ["/nologo", "/c"]
		return args

	def _getPreprocessorArgs(self):
		defineArgs = ["/D{}".format(d) for d in self._defines]
		return defineArgs

	def _getIncludeDirectoryArgs(self):
		args = ["/I{}".format(directory) for directory in self._includeDirectories]
		return args

	def _getOutputFileArgs(self, project, inputFile):
		outputFiles = self._getOutputFiles(project, inputFile)
		return ["/Fo", outputFiles[0]]
