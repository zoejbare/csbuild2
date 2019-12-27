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
.. module:: mac_os_clang_linker
	:synopsis: Clang linker tool for the macOS platform.

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import os

from .clang_linker import ClangLinker

from ..common import FindLibraries
from ..common.apple_tool_base import MacOsToolBase

class MacOsClangLinker(MacOsToolBase, ClangLinker):
	"""
	Clang compiler implementation
	"""
	supportedPlatforms = { "Darwin" }
	outputFiles = { "", ".a", ".dylib" }
	crossProjectDependencies = { ".a", ".dylib" }

	def __init__(self, projectSettings):
		MacOsToolBase.__init__(self, projectSettings)
		ClangLinker.__init__(self, projectSettings)


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		MacOsToolBase.SetupForProject(self, project)
		ClangLinker.SetupForProject(self, project)

	def _findLibraries(self, project, libs):
		sysLibDirs = [
			"/usr/local/lib",
			"/usr/lib",
		]
		allLibraryDirectories = [x for x in self._libraryDirectories] + sysLibDirs

		return FindLibraries([x for x in libs], allLibraryDirectories, [".dylib", ".so", ".a"])

	def _getDefaultArgs(self, project):
		baseArgs = ClangLinker._getDefaultArgs(self, project)

		# Get the special library build flag.
		libraryBuildArg = {
			csbuild.ProjectType.SharedLibrary: "-dynamiclib",
		}.get(project.projectType, "")

		return baseArgs + [
			libraryBuildArg
		]

	def _getRpathArgs(self):
		# TODO: We should make the default rpath configurable between @executable_path, @loader_path, and @rpath.
		args = [
			"-Xlinker", "-rpath",
			"-Xlinker", "@executable_path",
		]
		for lib in self._actualLibraryLocations.values():
			args.extend([
				"-Xlinker", "-rpath",
				"-Xlinker", os.path.dirname(lib),
			])
		return args

	def _getLibraryArgs(self):
		libArgs = [lib for lib in self._actualLibraryLocations.values()]
		frameworkDirArgs = ["-F{}".format(path) for path in self._frameworkDirectories]
		frameworkArgs = []
		for framework in self._frameworks:
			frameworkArgs.extend(["-framework", framework])

		return frameworkDirArgs + frameworkArgs + libArgs

	def _getStartGroupArgs(self):
		return []

	def _getEndGroupArgs(self):
		return []

	def _useResponseFileWithArchiver(self):
		return False
