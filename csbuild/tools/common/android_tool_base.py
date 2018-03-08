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
.. module:: android_tool_base
	:synopsis: Abstract base class for Android tools.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import glob
import os
import platform

from abc import ABCMeta

from ..._utils.decorators import MetaClass
from ...toolchain import Tool


class AndroidInfo(object):
	"""
	Collection of paths for a specific version of Android and architecture.

	:param gccPath: Full path to the gcc executable.
	:type gccPath: str

	:param gppPath: Full path to the g++ executable.
	:type gppPath: str

	:param ldPath: Full path to the ld executable.
	:type ldPath: str

	:param clangPath: Full path to the clang executable.
	:type clangPath: str

	:param clangppPath: Full path to the clang++ executable.
	:type clangppPath: str

	:param zipAlignPath: Full path to the zipAlign executable.
	:type zipAlignPath: str

	:param sysRootPath: Full path the Android sysroot.
	:type sysRootPath: str
	"""
	Instances = {}

	def __init__(self, gccPath, gppPath, ldPath, clangPath, clangppPath, zipAlignPath, sysRootPath):
		self.gccPath = gccPath
		self.gppPath = gppPath
		self.ldPath = ldPath
		self.clangPath = clangPath
		self.clangppPath = clangppPath
		self.zipAlignPath = zipAlignPath
		self.sysRootPath = sysRootPath


@MetaClass(ABCMeta)
class AndroidToolBase(Tool):
	"""
	Parent class for all tools targetting Android platforms.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	supportedArchitectures = { "x86", "x64", "arm", "arm64", "mips", "mips64" }

	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)

		self._androidNdkRootPath = projectSettings.get("androidNdkRootPath", "")
		self._androidSdkRootPath = projectSettings.get("androidSdkRootPath", "")
		self._androidManifestFilePath = projectSettings.get("androidManifestFilePath", "")
		self._androidTargetSdkVersion = projectSettings.get("androidTargetSdkVersion", None)

		# If no NDK root path is specified, try to get it from the environment.
		if not self._androidNdkRootPath and "ANDROID_NDK_ROOT" in os.environ:
			self._androidNdkRootPath = os.environ["ANDROID_NDK_ROOT"]

		# If no SDK root path is specified, try to get it from the environment.
		if not self._androidSdkRootPath and "ANDROID_HOME" in os.environ:
			self._androidSdkRootPath = os.environ["ANDROID_HOME"]

		assert os.access(self._androidNdkRootPath, os.F_OK), "Android NDK root path does not exist: {}".format(self._androidNdkRootPath)
		assert os.access(self._androidSdkRootPath, os.F_OK), "Android SDK root path does not exist: {}".format(self._androidSdkRootPath)

		assert self._androidManifestFilePath, "Android manifest file path not provided"
		assert os.access(self._androidManifestFilePath, os.F_OK), "Android manifest file path does not exist: {}".format(self._androidManifestFilePath)

		assert self._androidTargetSdkVersion, "Android target SDK version not provided"

		self._androidInfo = None


	####################################################################################################################
	### Private methods
	####################################################################################################################

	def _getInfo(self, arch):
		key = (self._androidNdkRootPath, self._androidSdkRootPath, arch)

		if key not in AndroidInfo.Instances:
			def _getToolchainPrefix(arch):
				# Search for a toolchain by architecture.
				toolchainArchPrefix = {
					"x86": "x86",
					"x64": "x86_64",
					"arm": "arm",
					"arm64": "aarch64",
					"mips": "mipsel",
					"mips64": "mips64el",
				}.get(arch, "")
				assert toolchainArchPrefix, "Android architecture not supported: {}".format(arch)

				return toolchainArchPrefix

			platformName = platform.system().lower()
			exeExtension = ".exe" if platform.system() == "Windows" else ""
			toolchainPrefix = _getToolchainPrefix(arch)
			rootToolchainPath = os.path.join(self._androidNdkRootPath, "toolchains")
			archToolchainPath = glob.glob(os.path.join(rootToolchainPath, "{}-*".format(toolchainPrefix)))
			llvmToolchainPath = glob.glob(os.path.join(rootToolchainPath, "llvm", "prebuilt", "{}-*".format(platformName)))
			sysRootPath = os.path.join(self._androidNdkRootPath, "platforms", "android-{}".format(self._androidTargetSdkVersion), self._getPlatformArchName(arch))

			assert archToolchainPath, "No Android toolchain installed for architecture: {}".format(arch)
			assert llvmToolchainPath, "No Android LLVM toolchain installed for platform: {}".format(platformName)
			assert os.access(sysRootPath, os.F_OK), "No Android sysroot found at path: {}".format(sysRootPath)

			archToolchainPath = glob.glob(os.path.join(archToolchainPath[0], "prebuilt", "{}-*".format(platformName)))
			llvmToolchainPath = llvmToolchainPath[0]

			assert archToolchainPath, "No Android \"{}\" toolchain installed for platform: {}".format(toolchainPrefix, platformName)

			archToolchainPath = os.path.join(archToolchainPath, "bin")
			llvmToolchainPath = os.path.join(llvmToolchainPath, "bin")

			# Get the compiler and linker paths.
			gccPath = glob.glob(os.path.join(archToolchainPath, "*-gcc{}".format(exeExtension)))
			gppPath = glob.glob(os.path.join(archToolchainPath, "*-g++{}".format(exeExtension)))
			ldPath = glob.glob(os.path.join(archToolchainPath, "*-ld{}".format(exeExtension)))
			clangPath = os.path.join(llvmToolchainPath, "clang{}".format(exeExtension))
			clangppPath = os.path.join(llvmToolchainPath, "clang++{}".format(exeExtension))

			assert gccPath, "No Android gcc executable found for architecture: {}".format(arch)
			assert gppPath, "No Android g++ executable found for architecture: {}".format(arch)
			assert ldPath, "No Android ld executable found for architecture: {}".format(arch)
			assert os.access(clangPath, os.F_OK), "No Android clang executable found for architecture: {}".format(arch)
			assert os.access(clangppPath, os.F_OK), "No Android clang++ executable found for architecture: {}".format(arch)

			buildToolsPath = glob.glob(os.path.join(self._androidSdkRootPath, "build-tools", "*"))
			assert buildToolsPath, "No Android build tools are installed"

			# For now, it doesn't seem like we need a specific version, so just pick the first one.
			buildToolsPath = buildToolsPath[0]

			# Get the miscellaneous build tool paths.
			zipAlignPath = os.path.join(buildToolsPath, "zipAlign{}".format(exeExtension))

			assert os.access(zipAlignPath, os.F_OK), "ZipAlign not found in Android build tools path: {}".format(buildToolsPath)

			AndroidInfo.Instances[key] = AndroidInfo(gccPath, gppPath, ldPath, clangPath, clangppPath, zipAlignPath, sysRootPath)

		return AndroidInfo.Instances[key]

	def _getPlatformArchName(self, arch):
		platformArchName = {
			"x86": "arch-x86",
			"x64": "arch-x86_64",
			"arm": "arch-arm",
			"arm64": "arch-arm64",
			"mips": "arch-mips",
			"mips64": "arch-mips64",
		}.get(arch, "")

		assert platformArchName, "Architecture not supported: {}".format(arch)

		return platformArchName


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		"""
		Run project setup, if any, before building the project, but after all dependencies have been resolved.

		:param project: project being set up
		:type project: csbuild._build.project.Project
		"""
		Tool.SetupForProject(self, project)

		if not self._androidInfo:
			self._androidInfo = self._getInfo(project.architectureName)


	################################################################################
	### Static makefile methods
	################################################################################

	@staticmethod
	def SetAndroidNdkRootPath(path):
		"""
		Sets the path to the Android NDK home.

		:param path: Android NDK home path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidNdkRootPath", os.path.abspath(path))

	@staticmethod
	def SetAndroidSdkRootPath(path):
		"""
		Sets the path to the Android SDK root.

		:param path: Android SDK root path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidSdkRootPath", os.path.abspath(path))

	@staticmethod
	def SetAndroidManifestFilePath(path):
		"""
		Sets the path to the Android manifest file.

		:param path: Android manifest file path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidManifestFilePath", os.path.abspath(path))

	@staticmethod
	def SetAndroidTargetSdkVersion(version):
		"""
		Sets the Android target SDK version.

		:param version: Android target SDK version.
		:type version: int
		"""
		csbuild.currentPlan.SetValue("androidTargetSdkVersion", version)

@MetaClass(ABCMeta)
class AndroidBaseCompiler(AndroidToolBase):
	"""
	Parent class for all Android compiler tools.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		AndroidToolBase.__init__(self, projectSettings)
