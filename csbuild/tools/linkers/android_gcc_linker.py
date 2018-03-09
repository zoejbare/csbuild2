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
.. module:: android_gcc_linker
	:synopsis: Android gcc linker tool.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import os

from ..common.android_tool_base import AndroidToolBase, AndroidStlLibType

from .gcc_linker import GccLinker

class AndroidGccLinker(GccLinker, AndroidToolBase):
	"""
	Android gcc linker implementation
	"""
	supportedArchitectures = AndroidToolBase.supportedArchitectures

	outputFiles = {".a", ".so"}


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		"""
		Run project setup, if any, before building the project, but after all dependencies have been resolved.

		:param project: project being set up
		:type project: csbuild._build.project.Project
		"""
		GccLinker.SetupForProject(self, project)
		AndroidToolBase.SetupForProject(self, project)

	def _getOutputExtension(self, projectType):
		# Android doesn't have a native application type.  Applications are linked as shared libraries.
		outputExt = {
			csbuild.ProjectType.SharedLibrary: ".so",
			csbuild.ProjectType.StaticLibrary: ".a",
		}.get(projectType, ".so")

		return outputExt

	def _getLdName(self):
		return self._androidInfo.ldPath

	def _getBinaryLinkerName(self):
		return self._androidInfo.gccPath

	def _getArchiverName(self):
		return self._androidInfo.arPath

	def _getDefaultArgs(self, project):
		return [] if project.projectType == csbuild.ProjectType.StaticLibrary else ["-shared", "-fPIC"]

	def _getLibraryArgs(self):
		stlLibInfo = {
			AndroidStlLibType.Gnu: (self._androidInfo.libStdCppLibPath, "libgnustl"),
			AndroidStlLibType.LibCpp: (self._androidInfo.libCppLibPath, "libc++"),
			AndroidStlLibType.StlPort: (self._androidInfo.stlPortLibPath, "libstlport"),
		}.get(self._androidStlLibType, None)

		args = ["-lc", "-lm", "-lgcc", "-llog", "-landroid"]

		if stlLibInfo:
			stlLibPath = stlLibInfo[0]
			stlLibName = stlLibInfo[1]
			ext = "_static.a" if self._staticRuntime else "_shared.so"
			fullPath = os.path.join(stlLibPath, "{}{}".format(stlLibName, ext))
			args.append("-l:{}".format(fullPath))

		return args + GccLinker._getLibraryArgs(self)

	def _getArchitectureArgs(self, project):
		return self._getBuildArchArgs(project.architectureName)

	def _getSystemArgs(self, project):
		return [
			"--sysroot",
			self._androidInfo.sysRootPath,
			"-Wl,--rpath-link={}".format(self._androidInfo.systemLibPath)
		]

	def _getLibrarySearchDirectories(self):
		return [self._androidInfo.systemLibPath] + self._libraryDirectories
