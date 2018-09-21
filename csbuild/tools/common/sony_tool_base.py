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
.. module:: sony_tool_base
	:synopsis: Base tools for all Sony tool implementations.

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import os

from abc import ABCMeta

from csbuild import log

from ..._utils import PlatformString
from ..._utils.decorators import MetaClass

from ...toolchain import Tool

@MetaClass(ABCMeta)
class SonyBaseTool(Tool):
	"""
	Parent class for all Sony tools.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)

	@staticmethod
	def _commonFindLibraries(libDirs, libs):
		notFound = set()
		found = {}

		def _searchForLib(libName, libDir, libExt):
			# Add the extension if it's not already there.
			filename = "{}{}".format(libName, libExt) if not libName.endswith(libExt) else libName

			# Try searching for the library name as it is.
			log.Info("Looking for library {} in directory {}...".format(filename, libDir))
			fullPath = os.path.join(libDir, filename)

			# Check if the file exists at the current path.
			if os.access(fullPath, os.F_OK):
				return fullPath

			# If the library couldn't be found, simulate posix by adding the "lib" prefix.
			filename = "lib{}".format(filename)

			log.Info("Looking for library {} in directory {}...".format(filename, libDir))
			fullPath = os.path.join(libDir, filename)

			# Check if the modified filename exists at the current path.
			if os.access(fullPath, os.F_OK):
				return fullPath

			return None

		for libraryName in libs:
			if os.access(libraryName, os.F_OK):
				abspath = os.path.abspath(libraryName)
				log.Info("... found {}".format(abspath))
				found[libraryName] = abspath
			else:
				for libraryDir in libDirs:
					# Search for the library as a ".prx" dynamic library file.
					fullPath = _searchForLib(libraryName, libraryDir, ".prx")
					if fullPath:
						log.Info("... found {}".format(fullPath))
						found[libraryName] = fullPath

					else:
						# As a fallback, search for the library as a ".a" static archive file.
						fullPath = _searchForLib(libraryName, libraryDir, ".a")
						if fullPath:
							log.Info("... found {}".format(fullPath))
							found[libraryName] = fullPath


				if libraryName not in found:
					# Failed to find the library in any of the provided directories.
					log.Error("Failed to find library \"{}\".".format(libraryName))
					notFound.add(libraryName)

		return None if notFound else found


@MetaClass(ABCMeta)
class Ps4BaseTool(SonyBaseTool):
	"""
	Parent class for all PS4 tools.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		SonyBaseTool.__init__(self, projectSettings)

		self._ps4SdkPath = projectSettings.get("ps4SdkPath", None)


	####################################################################################################################
	### Static makefile methods
	####################################################################################################################

	@staticmethod
	def SetPs4SdkPath(sdkPath):
		"""
		Set the path to the PS4 SDK.

		:param sdkPath: Path to the PS4 SDK.
		:type sdkPath: str
		"""
		csbuild.currentPlan.SetValue("ps4SdkPath", os.path.abspath(sdkPath))


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		# If the SDK path wasn't set, attempt to find it from the environment.
		if not self._ps4SdkPath:
			self._ps4SdkPath = os.getenv("SCE_ORBIS_SDK_DIR", None)

		assert self._ps4SdkPath, "No PS4 SDK path has been set"
		assert os.access(self._ps4SdkPath, os.F_OK), "PS4 SDK path does not exist: {}".format(self._ps4SdkPath)


@MetaClass(ABCMeta)
class PsVitaBaseTool(SonyBaseTool):
	"""
	Parent class for all PSVita tools.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		SonyBaseTool.__init__(self, projectSettings)

		self._psVitaSdkPath = projectSettings.get("psVitaSdkPath", None)


	####################################################################################################################
	### Static makefile methods
	####################################################################################################################

	@staticmethod
	def SetPsVitaSdkPath(sdkPath):
		"""
		Set the path to the PSVita SDK.

		:param sdkPath: Path to the PSVita SDK.
		:type sdkPath: str
		"""
		csbuild.currentPlan.SetValue("psVitaSdkPath", os.path.abspath(sdkPath))


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		# If the SDK path wasn't set, attempt to find it from the environment.
		if not self._psVitaSdkPath:
			self._psVitaSdkPath = os.getenv("SCE_PSP2_SDK_DIR", None)

		assert self._psVitaSdkPath, "No PSVita SDK path has been set"
		assert os.access(self._psVitaSdkPath, os.F_OK), "PS4 PSVita path does not exist: {}".format(self._psVitaSdkPath)
