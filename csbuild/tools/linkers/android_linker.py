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
.. module:: android_linker
	:synopsis: Android linker tool.

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import os

import csbuild

from .linker_base import LinkerBase
from ..common import FindLibraries
from ..common.android_tool_base import AndroidToolBase
from ... import log
from ..._utils import response_file, shared_globals

class AndroidLinker(AndroidToolBase, LinkerBase):
	"""
	Android linker implementation
	"""
	supportedArchitectures = AndroidToolBase.supportedArchitectures

	inputGroups = {".o"}
	outputFiles = {".a", ".so"}

	def __init__(self, projectSettings):
		AndroidToolBase.__init__(self, projectSettings)
		LinkerBase.__init__(self, projectSettings)

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
		LinkerBase.SetupForProject(self, project)

	def _getOutputFiles(self, project):
		return tuple({ os.path.join(project.outputDir, project.outputName + self._getOutputExtension(project.projectType)) })

	def _getCommand(self, project, inputFiles):
		if project.projectType == csbuild.ProjectType.StaticLibrary:
			cmdExe = self._androidInfo.arExePath
			cmd = ["rcs"] \
				+ self._getOutputFileArgs(project) \
				+ self._getInputFileArgs(inputFiles)
		else:
			cmdExe = self._androidInfo.clangExePath
			cmd = self._getDefaultArgs(project) \
				+ self._getCustomArgs() \
				+ self._getArchitectureArgs() \
				+ self._getSystemArgs() \
				+ self._getOutputFileArgs(project) \
				+ self._getInputFileArgs(inputFiles) \
				+ self._getLibraryPathArgs() \
				+ self._getStartGroupArgs() \
				+ self._getLibraryArgs() \
				+ self._getEndGroupArgs()

		if self._androidInfo.isBuggyClang:
			return [cmdExe] + cmd

		responseFile = response_file.ResponseFile(project, "linker-{}".format(project.outputName), cmd)

		if shared_globals.showCommands:
			log.Command("ResponseFile: {}\n\t{}".format(responseFile.filePath, responseFile.AsString()))

		return [cmdExe, "@{}".format(responseFile.filePath)]

	def _getEnv(self, project):
		binPath = self._androidInfo.gccBinPath
		if not binPath:
			return None

		envCopy = dict(os.environ)
		envCopy["PATH"] = "{};{}".format(binPath, envCopy["PATH"])
		return envCopy

	def _findLibraries(self, project, libs):
		libDirPaths = list(self._libraryDirectories)
		libDirPaths.extend(self._androidInfo.sysLibPaths)

		return FindLibraries(libs, libDirPaths, [".so", ".a"])

	def _getOutputExtension(self, projectType):
		# Android doesn't have a native application type; applications are linked as shared libraries.
		outputExt = {
			csbuild.ProjectType.StaticLibrary: ".a",
		}.get(projectType, ".so")

		return outputExt

	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getDefaultArgs(self, project):
		args = [
			"-Wno-unused-command-line-argument",
			"-Wl,--no-undefined",
			"-Wl,--no-allow-shlib-undefined",
			"-Wl,--unresolved-symbols=report-all",
			"-Wl,-z,noexecstack",
			"-Wl,-z,relro",
			"-Wl,-z,now",
		]
		if project.projectType != csbuild.ProjectType.StaticLibrary:
			args.extend(["-shared", "-fPIC"])
		return args

	def _getCustomArgs(self):
		return self._linkerFlags

	def _getOutputFileArgs(self, project):
		outFile = self._getOutputFiles(project)[0]
		if project.projectType == csbuild.ProjectType.StaticLibrary:
			return [outFile]
		return ["-o", outFile]

	def _getInputFileArgs(self, inputFiles):
		return [f.filename for f in inputFiles]

	def _getLibraryPathArgs(self):
		libDirPaths = { "-L{}".format(os.path.dirname(d)) for d in self._actualLibraryLocations.values() }
		args = list(libDirPaths)
		args.extend(["-L{}".format(d) for d in self._androidInfo.sysLibPaths])
		return args

	def _getLibraryArgs(self):
		args = ["-lc", "-lm", "-llog", "-landroid"]

		libSuffix = "static" if self._staticRuntime else "shared"
		args.append("-l{}".format("c++_{}".format(libSuffix)))

		# Add only the basename for each library.
		for lib in self._actualLibraryLocations.values():
			args.append("-l:{}".format(os.path.basename(lib)))

		return args

	def _getArchitectureArgs(self):
		return ["-target", self._androidInfo.targetTripleName]

	def _getSystemArgs(self):
		return [
			"--prefix", self._androidInfo.prefixPath,
		]

	def _getStartGroupArgs(self):
		return ["-Wl,--no-as-needed", "-Wl,--start-group"]

	def _getEndGroupArgs(self):
		return ["-Wl,--end-group"]
