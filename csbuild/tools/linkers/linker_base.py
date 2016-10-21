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
.. module:: linker_base
	:synopsis: A base class for binary linkers, as used by c++, d, assembly, etc

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import os

import csbuild
from abc import ABCMeta, abstractmethod

from ..common.tool_traits import HasDebugLevel, HasDebugRuntime, HasStaticRuntime

from ... import commands, log
from ..._utils.decorators import MetaClass

def _ignore(_):
	pass

class LibraryError(Exception):
	"""
	Represents an error indicating a missing library in a project.
	"""
	def __init__(self, proj):
		self.proj = proj
		Exception.__init__(self)

	def __str__(self):
		return "One or more libraries for project {} could not be found or were invalid.".format(self.proj)

	__repr__ = __str__

@MetaClass(ABCMeta)
class LinkerBase(HasDebugLevel, HasDebugRuntime, HasStaticRuntime):
	"""
	Base class for a linker

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	################################################################################
	### Initialization
	################################################################################

	def __init__(self, projectSettings):
		self._libraries = projectSettings.get("libraries", [])
		self._libraryDirectories = projectSettings.get("libraryDirectories", [])
		self._actualLibraryLocations = {
			library : library
			for library in self._libraries
		}

		HasDebugLevel.__init__(self, projectSettings)
		HasDebugRuntime.__init__(self, projectSettings)
		HasStaticRuntime.__init__(self, projectSettings)

	def SetupForProject(self, project):
		"""
		Project setup - in this case, verify libraries before running the build.

		:param project: Project to set up for
		:type project: project.Project
		:raises LibraryError: If a library is not found
		"""
		log.Linker("Verifying libraries for {}...", project)
		if self._libraries:
			self._actualLibraryLocations = self._findLibraries(self._libraries)

			if self._actualLibraryLocations is None:
				raise LibraryError(project)

		self._actualLibraryLocations.update(
			{
				dependProject.outputName : os.path.join(
					dependProject.outputDir,
					dependProject.outputName + self._getOutputExtension(dependProject.projectType)
				)
				for dependProject in project.dependencies if project.projectType != csbuild.ProjectType.Application
			}
		)


	################################################################################
	### Static makefile methods
	################################################################################

	@staticmethod
	def AddLibraries(*libs):
		"""
		Add libraries to be linked against. These can be provided as either 'foo' or 'libfoo.a'/'libfoo.lib' as is appropriate for the platform.

		:param libs: List of libraries
		:type libs: str
		"""
		csbuild.currentPlan.UnionSet("libraries", libs)

	@staticmethod
	def AddLibraryDirectories(*dirs):
		"""
		Add directories to look for libraries in

		:param dirs: Directories to scan
		:type dirs: str
		"""
		csbuild.currentPlan.UnionSet("libraryDirectories", [os.path.abspath(directory) for directory in dirs])


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
	def _getOutputFiles(self, project):
		"""
		Get the set of output files that will be created from linking a project

		:param project: project being linked
		:type project: project.Project
		:return: tuple of files that will be produced from linking
		:rtype: tuple[str]
		"""
		return ""

	@abstractmethod
	def _getCommand(self, project, inputFiles):
		"""
		Get the command to link the provided set of files for the provided project

		:param project: Project to link
		:type project: project.Project
		:param inputFiles: files being linked
		:type inputFiles: input_file.InputFile
		:return: Command to execute, broken into a list, as would be provided to subrpocess functions
		:rtype: list
		"""
		return []

	@abstractmethod
	def _findLibraries(self, libs):
		"""
		Search for the provided set of libraries, verify they exist, and map them to their actual file locations

		:param libs: libraries to search for
		:type libs: str
		:return: map of input string to actual absolute path to the library
		:rtype: dict[str, str]
		"""
		return {}

	@abstractmethod
	def _getOutputExtension(self, projectType):
		"""
		Get the output extension for a given project type

		:param projectType: the project type
		:type projectType: csbuild.ProjectType
		:return: the extension, including the dot
		:rtype: str
		"""
		return ""


	################################################################################
	### Base class methods containing logic shared by all subclasses
	################################################################################

	def RunGroup(self, project, inputFiles):
		"""
		Execute a group build step. Note that this method is run massively in parallel with other build steps.
		It is NOT thread-safe in ANY way. If you need to change shared state within this method, you MUST use a
		mutex.

		:param project:
		:type project: csbuild._build.project.Project
		:param inputFiles: List of files to build
		:type inputFiles: list[input_file.InputFile]
		:return: tuple of files created by the tool - all files must have an extension in the outputFiles list
		:rtype: tuple[str]
		"""
		log.Linker("Linking {}{}...", project.outputName, self._getOutputExtension(project.projectType))
		returncode, _, _ = commands.Run(self._getCommand(project, inputFiles), env=self._getEnv(project))
		if returncode != 0:
			raise csbuild.BuildFailureException(project, inputFiles)
		return self._getOutputFiles(project)
