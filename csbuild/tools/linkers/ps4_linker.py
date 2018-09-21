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
.. module:: ps4_linker
	:synopsis: Implementation of the PS4 linker tool.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import os

from .gcc_linker import GccLinker

from ..common.sony_tool_base import Ps4BaseTool, SonyBaseTool

def _ignore(_):
	pass

class Ps4Linker(Ps4BaseTool, GccLinker):
	"""
	PS4 linker tool implementation
	"""
	supportedPlatforms = { "Windows" }
	supportedArchitectures = { "x64" }

	outputFiles = { ".elf", ".a", ".prx" }
	crossProjectDependencies = { ".a", ".prx" }

	def __init__(self, projectSettings):
		Ps4BaseTool.__init__(self, projectSettings)
		GccLinker.__init__(self, projectSettings)

	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def _findLibraries(self, project, libs):
		targetLibPath = os.path.join(self._ps4SdkPath, "target", "lib")
		allLibraryDirectories = [x for x in self._libraryDirectories] + [targetLibPath]

		return SonyBaseTool._commonFindLibraries(allLibraryDirectories, libs)

	def _getOutputExtension(self, projectType):
		outputExt = {
			csbuild.ProjectType.SharedLibrary: ".prx",
			csbuild.ProjectType.StaticLibrary: ".a",
		}.get(projectType, ".elf")

		return outputExt

	def _getBinaryLinkerName(self):
		return os.path.join(self._ps4SdkPath, "host_tools", "bin", "orbis-clang++.exe")

	def _getArchiverName(self):
		return os.path.join(self._ps4SdkPath, "host_tools", "bin", "orbis-ar.exe")

	def _getDefaultArgs(self, project):
		args = [
			"-fPIC",
			"-Wl,-oformat=prx",
			"-Wl,-prx-stub-output-dir={}".format(project.outputDir)
		] if project.projectType == csbuild.ProjectType.SharedLibrary \
			else []
		return args

	def _getLibraryPathArgs(self, project):
		_ignore(project)
		return []

	def _getLibraryArgs(self):
		return ["{}".format(lib) for lib in self._actualLibraryLocations.values()]

	def _getStartGroupArgs(self):
		return ["-Wl,--start-group"]

	def SetupForProject(self, project):
		Ps4BaseTool.SetupForProject(self, project)
		GccLinker.SetupForProject(self, project)
