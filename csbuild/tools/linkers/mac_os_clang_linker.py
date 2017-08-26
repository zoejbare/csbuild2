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

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild

from .clang_linker import ClangLinker

from ..common.apple_tool_base import MacOsToolBase

class MacOsClangLinker(MacOsToolBase, ClangLinker):
	"""
	Clang compiler implementation
	"""

	outputFiles = {"", ".a", ".dylib"}
	crossProjectDependencies = {".a", ".dylib"}

	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def __init__(self, projectSettings):
		MacOsToolBase.__init__(self, projectSettings)
		ClangLinker.__init__(self, projectSettings)

	def SetupForProject(self, project):
		MacOsToolBase.SetupForProject(self, project)
		ClangLinker.SetupForProject(self, project)

	def _getDefaultArgs(self, project):
		baseArgs = ClangLinker._getDefaultArgs(self, project)

		# Get the special library build flag.
		libraryBuildArg = {
			csbuild.ProjectType.SharedLibrary: "-dynamiclib",
		}.get(project.projectType, "")

		return baseArgs + [
			libraryBuildArg
		]

	def _getLibraryArgs(self):
		return [lib for lib in self._actualLibraryLocations.values()]

	def _getStartGroupArgs(self):
		return []

	def _getEndGroupArgs(self):
		return []
