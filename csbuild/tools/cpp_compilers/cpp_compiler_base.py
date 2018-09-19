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
.. module:: cpp_compiler_base
	:synopsis: Basic class for C++ compilers

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import os
import csbuild

from abc import ABCMeta, abstractmethod

from ..common.tool_traits import \
	HasDebugLevel, \
	HasDebugRuntime, \
	HasDefines, \
	HasIncludeDirectories, \
	HasOptimizationLevel, \
	HasStaticRuntime

from ... import commands, log
from ..._utils.decorators import MetaClass

def _ignore(_):
	pass

@MetaClass(ABCMeta)
class CppCompilerBase(HasDebugLevel, HasDebugRuntime, HasDefines, HasIncludeDirectories, HasOptimizationLevel, HasStaticRuntime):
	"""
	Base class for C++ compilers

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	inputFiles={".cpp", ".c", ".cc", ".cxx"}
	dependencies={".gch", ".pch"}

	################################################################################
	### Initialization
	################################################################################

	def __init__(self, projectSettings):
		self._globalFlags = projectSettings.get("globalFlags", [])
		self._cFlags = projectSettings.get("cFlags", [])
		self._cxxFlags = projectSettings.get("cxxFlags", [])

		HasDebugLevel.__init__(self, projectSettings)
		HasDebugRuntime.__init__(self, projectSettings)
		HasDefines.__init__(self, projectSettings)
		HasIncludeDirectories.__init__(self, projectSettings)
		HasOptimizationLevel.__init__(self, projectSettings)
		HasStaticRuntime.__init__(self, projectSettings)


	################################################################################
	### Static makefile methods
	################################################################################

	@staticmethod
	def AddCompilerFlags(*flags):
		"""
		Add compiler flags that are applid to both C and C++ files.

		:param flags: List of flags
		:type flags: str
		"""
		csbuild.currentPlan.ExtendList("globalFlags", flags)

	@staticmethod
	def AddCompilerCxxFlags(*flags):
		"""
		Add compiler cxx flags.

		:param flags: List of cxx flags
		:type flags: str
		"""
		csbuild.currentPlan.ExtendList("cxxFlags", flags)


	################################################################################
	### Methods that may be implemented by subclasses as needed
	################################################################################

	def _getEnv(self, project):
		_ignore(project)
		return None


	################################################################################
	### Abstract methods that need to be implemented by subclasses
	################################################################################

	@abstractmethod
	def _getOutputFiles(self, project, inputFile):
		return ("", )

	@abstractmethod
	def _getCommand(self, project, inputFile, isCpp):
		return []


	################################################################################
	### Base class methods containing logic shared by all subclasses
	################################################################################

	def SetupForProject(self, project):
		HasIncludeDirectories.SetupForProject(self, project)

		if project.projectType == csbuild.ProjectType.SharedLibrary:
			self._defines.add("CSB_SHARED_LIBRARY=1")
		elif project.projectType == csbuild.ProjectType.StaticLibrary:
			self._defines.add("CSB_STATIC_LIBRARY=1")
		else:
			self._defines.add("CSB_APPLICATION=1")

		self._defines.add("CSB_TARGET_{}=1".format(project.targetName.upper()))

	def Run(self, inputProject, inputFile):
		"""
		Execute a single build step. Note that this method is run massively in parallel with other build steps.
		It is NOT thread-safe in ANY way. If you need to change shared state within this method, you MUST use a
		mutex.

		:param inputProject: project being built
		:type inputProject: csbuild._build.project.Project
		:param inputFile: File to build
		:type inputFile: input_file.InputFile
		:return: tuple of files created by the tool - all files must have an extension in the outputFiles list
		:rtype: tuple[str]
		"""
		log.Build(
			"Compiling {} ({}-{}-{})...",
			os.path.basename(inputFile.filename),
			inputProject.toolchainName,
			inputProject.architectureName,
			inputProject.targetName
		)

		_, extension = os.path.splitext(inputFile.filename)
		returncode, _, _ = commands.Run(self._getCommand(inputProject, inputFile, extension in {".cpp", ".cc", ".cxx"}), env=self._getEnv(inputProject))
		if returncode != 0:
			raise csbuild.BuildFailureException(inputProject, inputFile)
		return self._getOutputFiles(inputProject, inputFile)
