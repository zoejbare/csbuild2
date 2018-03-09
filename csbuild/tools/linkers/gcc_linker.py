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
.. module:: gcc_linker
	:synopsis: gcc linker tool for C++, d, asm, etc

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import os
import re

import csbuild

from .linker_base import LinkerBase
from ... import commands, log
from ..._utils import ordered_set

class GccLinker(LinkerBase):
	"""
	GCC linker tool for c++, d, asm, etc
	"""
	supportedArchitectures = {"x86", "x64"}

	inputGroups = {".o"}
	outputFiles = {"", ".a", ".so"}
	crossProjectDependencies = {".a", ".so"}

	_failRegex = re.compile(R"ld: cannot find -l(.*)")


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def _getOutputFiles(self, project):
		return tuple({os.path.join(project.outputDir, project.outputName + self._getOutputExtension(project.projectType))})

	def _getCommand(self, project, inputFiles):
		if project.projectType == csbuild.ProjectType.StaticLibrary:
			cmd = [self._getArchiverName(), "rcs"] \
				+ self._linkerFlags \
				+ self._getOutputFileArgs(project) \
				+ self._getInputFileArgs(inputFiles)
		else:
			cmd = [self._getBinaryLinkerName(), "-L/"] \
				+ self._getDefaultArgs(project) \
				+ self._getOutputFileArgs(project) \
				+ self._getInputFileArgs(inputFiles) \
				+ self._getStartGroupArgs() \
				+ self._getLibraryArgs() \
				+ self._getEndGroupArgs() \
				+ self._getArchitectureArgs(project) \
				+ self._linkerFlags
		return [arg for arg in cmd if arg]

	def _findLibraries(self, libs):
		ret = {}

		shortLibs = ordered_set.OrderedSet(libs)
		longLibs = []

		for lib in libs:
			if os.access(lib, os.F_OK):
				abspath = os.path.abspath(lib)
				ret[lib] = abspath
				shortLibs.remove(lib)

		if shortLibs:
			# In most cases this should be finished in exactly two attempts.
			# However, in some rare cases, ld will get to a successful lib after hitting a failure and just give up.
			# -lpthread is one such case, and in that case we have to do this more than twice.
			# However, the vast majority of cases should require only two calls (and only one if everything is -lfoo format)
			# and the vast majority of the cases that require a third pass will not require a fourth... but, everything
			# is possible! Still better than doing a pass per file like we used to.
			while True:
				cmd = [self._getLdName(), "-M", "-o", "/dev/null"] + \
					  ["-l"+lib for lib in shortLibs] + \
					  ["-l:"+lib for lib in longLibs] + \
					  ["-L"+path for path in self._getLibrarySearchDirectories()]
				returncode, out, err = commands.Run(cmd, None, None)
				if returncode != 0:
					lines = err.splitlines()
					moved = False
					for line in lines:
						match = GccLinker._failRegex.match(line)
						if match:
							lib = match.group(1)
							if lib not in shortLibs:
								for errorLine in lines:
									log.Error(errorLine)
								return None
							shortLibs.remove(lib)
							longLibs.append(lib)
							moved = True

					if not moved:
						for line in lines:
							log.Error(line)
						return None

					continue
				break

			matches = []
			loading = False
			inGroup = False
			for line in out.splitlines():
				if line.startswith("LOAD"):
					if inGroup:
						continue
					loading = True
					matches.append(line[5:])
				elif line == "START GROUP":
					inGroup = True
				elif line == "END GROUP":
					inGroup = False
				elif loading:
					break

			assert len(matches) == len(shortLibs) + len(longLibs)
			assert len(matches) + len(ret) == len(libs)
			for i, lib in enumerate(shortLibs):
				ret[lib] = matches[i]
			for i, lib in enumerate(longLibs):
				ret[lib] = matches[i+len(shortLibs)]
			for lib in libs:
				log.Info("Found library '{}' at {}", lib, ret[lib])

		return ret

	def _getOutputExtension(self, projectType):
		outputExt = {
			csbuild.ProjectType.SharedLibrary: ".so",
			csbuild.ProjectType.StaticLibrary: ".a",
		}.get(projectType, "")

		return outputExt


	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getLdName(self):
		return "ld"

	def _getBinaryLinkerName(self):
		return "gcc"

	def _getArchiverName(self):
		return "ar"

	def _getDefaultArgs(self, project):
		args = []
		if project.projectType == csbuild.ProjectType.SharedLibrary:
			args += ["-shared", "-fPIC"]
		return args

	def _getOutputFileArgs(self, project):
		if project.projectType == csbuild.ProjectType.StaticLibrary:
			return [self._getOutputFiles(project)[0]]
		return ["-o", self._getOutputFiles(project)[0]]

	def _getInputFileArgs(self, inputFiles):
		return [f.filename for f in inputFiles]

	def _getLibraryArgs(self):
		return ["-l:{}".format(lib) for lib in self._actualLibraryLocations.values()]

	def _getStartGroupArgs(self):
		return ["-Wl,--no-as-needed", "-Wl,--start-group"]

	def _getEndGroupArgs(self):
		return ["-Wl,--end-group"]

	def _getArchitectureArgs(self, project):
		arg = "-m64" if project.architectureName == "x64" else "-m32"
		return [arg]

	def _getLibrarySearchDirectories(self):
		return self._libraryDirectories
