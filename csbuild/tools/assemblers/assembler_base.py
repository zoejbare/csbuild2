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
.. module:: assembler_base
	:synopsis: Base class for assemblers

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import os
import csbuild

from abc import ABCMeta, abstractmethod

from ... import commands, log
from ...toolchain import Tool
from ..._utils import ordered_set
from ..._utils.decorators import MetaClass

def _ignore(_):
	pass

@MetaClass(ABCMeta)
class AssemblerBase(Tool):
	"""
	Base class for assemblers

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	dependencies={}

	################################################################################
	### Initialization
	################################################################################

	def __init__(self, projectSettings):
		super(Tool, self).__init__()
		self._includeDirectories = projectSettings.get("includeDirectories", ordered_set.OrderedSet())
		self._defines = projectSettings.get("defines", ordered_set.OrderedSet())
		self._asmFlags = projectSettings.get("asmFlags", [])


	################################################################################
	### Static makefile methods
	################################################################################

	@staticmethod
	def AddIncludeDirectories(*dirs):
		"""
		Add directories to search for headers in

		:param dirs: list of directories
		:type dirs: str
		"""
		csbuild.currentPlan.UnionSet("includeDirectories", [os.path.abspath(directory) for directory in dirs])

	@staticmethod
	def AddDefines(*defines):
		"""
		Add preprocessor defines to the current project.

		:param defines: List of defines.
		:type defines: str
		"""
		csbuild.currentPlan.UnionSet("defines", defines)

	@staticmethod
	def AddAssemblerFlags(*flags):
		"""
		Add assembler flags.

		:param flags: List of asm flags
		:type flags: str
		"""
		csbuild.currentPlan.ExtendList("asmFlags", flags)


	################################################################################
	### Public API
	################################################################################

	def GetIncludeDirectories(self):
		"""
		Get the list of include directories

		:return: include dirs
		:rtype: ordered_set.OrderedSet[str]
		"""
		return self._includeDirectories


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
		return ""

	@abstractmethod
	def _getCommand(self, project, inputFile):
		return []


	################################################################################
	### Base class methods containing logic shared by all subclasses
	################################################################################

	def SetupForProject(self, project):
		if project.projectType == csbuild.ProjectType.SharedLibrary:
			self._defines.add("CSB_SHARED_LIBRARY=1")
		elif project.projectType == csbuild.ProjectType.StaticLibrary:
			self._defines.add("CSB_STATIC_LIBRARY=1")
		else:
			self._defines.add("CSB_APPLICATION=1")
		self._defines.add("CSB_TARGET_{}=1".format(project.targetName.upper()))

	def Run(self, project, inputFile):
		"""
		Execute a single build step. Note that this method is run massively in parallel with other build steps.
		It is NOT thread-safe in ANY way. If you need to change shared state within this method, you MUST use a
		mutex.

		:param project: project being built
		:type project: csbuild._build.project.Project
		:param inputFile: File to build
		:type inputFile: input_file.InputFile
		:return: tuple of files created by the tool - all files must have an extension in the outputFiles list
		:rtype: tuple[str]
		"""
		log.Build("Assembling {}...", os.path.basename(inputFile.filename))

		_, extension = os.path.splitext(inputFile.filename)
		returncode, _, _ = commands.Run(self._getCommand(project, inputFile), env=self._getEnv(project))
		if returncode != 0:
			raise csbuild.BuildFailureException(project, inputFile)
		return self._getOutputFiles(project, inputFile)
