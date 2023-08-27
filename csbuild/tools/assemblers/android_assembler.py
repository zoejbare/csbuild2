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
.. module:: android_assembler
	:synopsis: Android assember tool

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import os

from .assembler_base import AssemblerBase
from ..common.android_tool_base import AndroidToolBase
from ... import log
from ..._utils import response_file, shared_globals

class AndroidAssembler(AndroidToolBase, AssemblerBase):
	"""
	Android assembler implementation
	"""
	supportedArchitectures = AndroidToolBase.supportedArchitectures
	inputFiles={".s", ".S"}
	outputFiles = {".o"}

	def __init__(self, projectSettings):
		AndroidToolBase.__init__(self, projectSettings)
		AssemblerBase.__init__(self, projectSettings)

	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		"""
		Run project setup, if any, before building the project, but after all dependencies have been resolved.

		:param project: project being set up
		:type project: csbuild._build.project.Project
		"""
		AndroidToolBase.SetupForProject(self, project)
		AssemblerBase.SetupForProject(self, project)

	def _getOutputFiles(self, project, inputFile):
		intDirPath = project.GetIntermediateDirectory(inputFile)
		filename = os.path.splitext(os.path.basename(inputFile.filename))[0] + ".o"
		return tuple({ os.path.join(intDirPath, filename) })

	def _getCommand(self, project, inputFile):
		cmd = self._getInputFileArgs(inputFile) \
			+ self._getDefaultArgs(project) \
			+ self._getCustomArgs() \
			+ self._getOutputFileArgs(project, inputFile) \
			+ self._getPreprocessorArgs() \
			+ self._getIncludeDirectoryArgs() \
			+ self._getArchitectureArgs()

		if self._androidInfo.isBuggyClang:
			return [self._androidInfo.clangExePath] + cmd

		inputFileBasename = os.path.basename(inputFile.filename)
		responseFile = response_file.ResponseFile(project, "{}-{}".format(inputFile.uniqueDirectoryId, inputFileBasename), cmd)

		if shared_globals.showCommands:
			log.Command("ResponseFile: {}\n\t{}".format(responseFile.filePath, responseFile.AsString()))

		return [self._androidInfo.clangExePath, "@{}".format(responseFile.filePath)]

	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getDefaultArgs(self, project):
		args = [
			"-funwind-tables",
			"-fstack-protector",
			"-fno-omit-frame-pointer",
			"-fno-strict-aliasing",
			"-fno-short-enums",
			"-Wno-unused-command-line-argument",
			"-Wa,--noexecstack",
		]
		if project.projectType == csbuild.ProjectType.SharedLibrary:
			args.append("-fPIC")
		return args

	def _getCustomArgs(self):
		return self._asmFlags

	def _getInputFileArgs(self, inputFile):
		return ["-c", "{}".format(inputFile.filename)]

	def _getOutputFileArgs(self, project, inputFile):
		outputFiles = self._getOutputFiles(project, inputFile)
		return ["-o", "{}".format(outputFiles[0])]

	def _getPreprocessorArgs(self):
		args = self._getDefaultAndroidDefines()
		args.extend(["-D{}".format(d) for d in self._defines])
		args.extend(["-U{}".format(u) for u in self._undefines])
		return args

	def _getIncludeDirectoryArgs(self):
		args = ["-I{}".format(d) for d in self._includeDirectories]
		args.extend(["-I{}".format(d) for d in self._androidInfo.sysIncPaths])
		return args

	def _getArchitectureArgs(self):
		return ["-target", self._androidInfo.targetTripleName]
