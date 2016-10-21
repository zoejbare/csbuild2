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
.. module:: msvc_linker
	:synopsis: msvc linker tool for C++, d, asm, etc

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import os
import csbuild

from .linker_base import LinkerBase
from ..common.msvc_tool_base import MsvcToolBase
from ..common.tool_traits import HasDebugLevel
from ... import log

DebugLevel = HasDebugLevel.DebugLevel

class MsvcLinker(MsvcToolBase, LinkerBase):
	"""
	MSVC linker tool implementation for c++ and asm.
	"""
	supportedPlatforms = {"Windows"}
	supportedArchitectures = {"x86", "x64", "arm"}
	inputGroups = {".obj"}
	outputFiles = {".exe", ".lib", ".dll"}
	crossProjectDependencies = {".lib"}


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def __init__(self, projectSettings):
		MsvcToolBase.__init__(self, projectSettings)
		LinkerBase.__init__(self, projectSettings)

	def _getEnv(self, project):
		return self._vcvarsall.env

	def _getOutputFiles(self, project):
		outputPath = os.path.join(project.outputDir, project.outputName)
		outputFiles = {
			csbuild.ProjectType.StaticLibrary: ["{}.lib".format(outputPath)],
			csbuild.ProjectType.SharedLibrary: ["{}.lib".format(outputPath), "{}.dll".format(outputPath)],
			csbuild.ProjectType.Application: ["{}.exe".format(outputPath)],
		}[project.projectType]

		# Output files when not building a static library.
		if project.projectType != csbuild.ProjectType.StaticLibrary:
			outputFiles.append("{}.ilk".format(outputPath))

			# Add the PDB file if debugging is enabled.
			if self._debugLevel != DebugLevel.Disabled:
				outputFiles.append("{}.pdb".format(outputPath))


		return tuple(outputFiles)

	def _getCommand(self, project, inputFiles):
		if project.projectType == csbuild.ProjectType.StaticLibrary:
			linkerPath = os.path.join(self._vcvarsall.binPath, "lib.exe")
		else:
			linkerPath = os.path.join(self._vcvarsall.binPath, "link.exe")
		cmd = [
		      linkerPath,
		      self._getMachineArg(project),
		      self._getOutputFileArg(project)
	      ] \
			+ self._getDefaultArgs(project) \
			+ self._getImportLibraryAndPdbFileArgs(project) \
			+ self._getLibraryArgs(project) \
			+ [f.filename for f in inputFiles]
		return [arg for arg in cmd if arg]

	def _findLibraries(self, libs):
		notFound = set()
		found = {}
		allLibraryDirectories = sorted(self._libraryDirectories + self._vcvarsall.libPaths)

		for libraryName in libs:
			for libraryDir in allLibraryDirectories:
				# Add the ".lib" extension if it's not already there.
				filename = "{}.lib".format(libraryName) if not libraryName.endswith(".lib") else libraryName

				# Try searching for the library name as it is.
				log.Info("Looking for library {} in directory {}...".format(filename, libraryDir))
				fullPath = os.path.join(libraryDir, filename)

				# Check if the file exists at the current path.
				if os.access(fullPath, os.F_OK):
					log.Info("... found {}".format(fullPath))
					found[libraryName] = fullPath
					break

				# If the library couldn't be found, simulate posix by adding the "lib" prefix.
				filename = "lib{}".format(filename)

				log.Info("Looking for library {} in directory {}...".format(filename, libraryDir))
				fullPath = os.path.join(libraryDir, filename)

				# Check if the modified filename exists at the current path.
				if os.access(fullPath, os.F_OK):
					log.Info("... found {}".format(fullPath))
					found[libraryName] = fullPath
					break

			if libraryName not in found:
				# Failed to find the library in any of the provided directories.
				log.Error('Failed to find library "{}".'.format(libraryName))
				notFound.add(libraryName)

		return None if notFound else found


	def _getOutputExtension(self, projectType):
		# These are extensions of the files that can be output from the linker or librarian.
		# The library extensions should represent the file types that can actually linked against.
		ext = {
			csbuild.ProjectType.SharedLibrary: ".lib",
			csbuild.ProjectType.StaticLibrary: ".lib",
		}
		return ext.get(projectType, ".exe")

	def SetupForProject(self, project):
		MsvcToolBase.SetupForProject(self, project)
		LinkerBase.SetupForProject(self, project)


	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getDefaultArgs(self, project):
		args = [
			"/ERRORREPORT:NONE",
			"/NOLOGO",
		]
		# Arguments for any project that is not a static library.
		if project.projectType != csbuild.ProjectType.StaticLibrary:
			args.extend([
				"/NXCOMPAT",
				"/DYNAMICBASE",
			])
			if self._debugLevel != DebugLevel.Disabled:
				args.append("/DEBUG")
			if project.projectType == csbuild.ProjectType.SharedLibrary:
				args.append("/DLL")
		return args

	def _getMachineArg(self, project):
		return "/MACHINE:{}".format(project.architectureName.upper())

	def _getImportLibraryAndPdbFileArgs(self, project):
		if project.projectType == csbuild.ProjectType.StaticLibrary:
			# Static libraries do not have these arguments.
			return []
		else:
			outputPath = os.path.join(project.outputDir, project.outputName)
			args = []
			if project.projectType == csbuild.ProjectType.SharedLibrary:
				args.append("/IMPLIB:{}.lib".format(outputPath))
			if self._debugLevel != DebugLevel.Disabled:
				args.append("/PDB:{}.pdb".format(outputPath))
			return args

	def _getLibraryArgs(self, project):
		# Static libraries don't require the default libraries to be linked, so only add them when building an application or shared library.
		args = [] if project.projectType == csbuild.ProjectType.StaticLibrary else [
			"kernel32.lib",
			"user32.lib",
			"gdi32.lib",
			"winspool.lib",
			"comdlg32.lib",
			"advapi32.lib",
			"shell32.lib",
			"ole32.lib",
			"oleaut32.lib",
			"uuid.lib",
			"odbc32.lib",
			"odbccp32.lib",
		]
		args.extend([lib for lib in self._actualLibraryLocations.values()])
		return args

	def _getOutputFileArg(self, project):
		ext = {
			csbuild.ProjectType.SharedLibrary: ".dll",
			csbuild.ProjectType.StaticLibrary: ".lib",
		}
		return "/OUT:{}{}".format(os.path.join(project.outputDir, project.outputName), ext.get(project.projectType, ".exe"))
