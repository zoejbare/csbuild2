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


@MetaClass(ABCMeta)
class AndroidStlLibType(object):
	Gnu = 0
	LibCpp = 1
	StlPort = 2

	MinValue = Gnu
	MaxValue = StlPort

class AndroidInfo(object):
	"""
	Collection of paths for a specific version of Android and architecture.

	:param gccPath: Full path to the gcc executable.
	:type gccPath: str

	:param gppPath: Full path to the g++ executable.
	:type gppPath: str

	:param asPath: Full path to the as executable.
	:type asPath: str

	:param ldPath: Full path to the ld executable.
	:type ldPath: str

	:param arPath: Full path to the ar executable.
	:type arPath: str

	:param clangPath: Full path to the clang executable.
	:type clangPath: str

	:param clangppPath: Full path to the clang++ executable.
	:type clangppPath: str

	:param zipAlignPath: Full path to the zipAlign executable.
	:type zipAlignPath: str

	:param systemLibPath: Full path to the Android system libraries.
	:type systemLibPath: str

	:param systemIncludePaths: List of full paths to the Android system headers.
	:type systemIncludePaths: list[str]

	:param nativeAppGluPath: Full path to the Android native glue source and header files.
	:type nativeAppGluPath: str

	:param libStdCppLibPath: Full path to the libstdc++ libraries.
	:type libStdCppLibPath: str

	:param libStdCppIncludePaths: List of full paths to the libstdc++ headers.
	:type libStdCppIncludePaths: list[str]

	:param libCppLibPath: Full path to the libc++ libraries.
	:type libCppLibPath: str

	:param libCppIncludePaths: List of full paths to the libc++ headers.
	:type libCppIncludePaths: list[str]

	:param stlPortLibPath: Full path to the stlport libraries.
	:type stlPortLibPath: str

	:param stlPortIncludePaths: List of full paths to the stlport headers.
	:type stlPortIncludePaths: list[str]
	"""
	Instances = {}

	def __init__(
			self,
			gccPath,
			gppPath,
			asPath,
			ldPath,
			arPath,
			clangPath,
			clangppPath,
			zipAlignPath,
			systemLibPath,
			systemIncludePaths,
			nativeAppGluPath,
			libStdCppLibPath,
			libStdCppIncludePaths,
			libCppLibPath,
			libCppIncludePaths,
			stlPortLibPath,
			stlPortIncludePaths,
	):
		self.gccPath = gccPath
		self.gppPath = gppPath
		self.asPath = asPath
		self.ldPath = ldPath
		self.arPath = arPath
		self.clangPath = clangPath
		self.clangppPath = clangppPath
		self.zipAlignPath = zipAlignPath
		self.systemLibPath = systemLibPath
		self.systemIncludePaths = systemIncludePaths
		self.nativeAppGluPath = nativeAppGluPath
		self.libStdCppLibPath = libStdCppLibPath
		self.libStdCppIncludePaths = libStdCppIncludePaths
		self.libCppLibPath = libCppLibPath
		self.libCppIncludePaths = libCppIncludePaths
		self.stlPortLibPath = stlPortLibPath
		self.stlPortIncludePaths = stlPortIncludePaths


@MetaClass(ABCMeta)
class AndroidToolBase(Tool):
	"""
	Parent class for all tools targetting Android platforms.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView

	:ivar: _androidInfo: Collection of information about the selected Android toolchain and system.
	:type _androidInfo: :class:`AndroidInfo`
	"""
	supportedArchitectures = { "x86", "x64", "arm", "arm64", "mips", "mips64" }

	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)

		self._androidNdkRootPath = projectSettings.get("androidNdkRootPath", "")
		self._androidSdkRootPath = projectSettings.get("androidSdkRootPath", "")
		self._androidManifestFilePath = projectSettings.get("androidManifestFilePath", "")
		self._androidTargetSdkVersion = projectSettings.get("androidTargetSdkVersion", None)
		self._androidStlLibType = projectSettings.get("androidStlLibType", AndroidStlLibType.Gnu)
		self._androidUseDefaultNativeAppGlue = projectSettings.get("androidUseDefaultNativeAppGlue", False)

		# If no NDK root path is specified, try to get it from the environment.
		if not self._androidNdkRootPath and "ANDROID_NDK_ROOT" in os.environ:
			self._androidNdkRootPath = os.environ["ANDROID_NDK_ROOT"]

		# If no SDK root path is specified, try to get it from the environment.
		if not self._androidSdkRootPath and "ANDROID_HOME" in os.environ:
			self._androidSdkRootPath = os.environ["ANDROID_HOME"]

		assert self._androidNdkRootPath, "No Android NDK root path provided"
		assert self._androidSdkRootPath, "No Android SDK root path provided"
		assert self._androidManifestFilePath, "No Android manifest file path provided"
		assert self._androidTargetSdkVersion, "No Android target SDK version provided"
		assert AndroidStlLibType.MinValue <= self._androidStlLibType <= AndroidStlLibType.MaxValue, "Invalid value for Android STL lib type: {}".format(self._androidStlLibType)

		assert os.access(self._androidNdkRootPath, os.F_OK), "Android NDK root path does not exist: {}".format(self._androidNdkRootPath)
		assert os.access(self._androidSdkRootPath, os.F_OK), "Android SDK root path does not exist: {}".format(self._androidSdkRootPath)
		assert os.access(self._androidManifestFilePath, os.F_OK), "Android manifest file path does not exist: {}".format(self._androidManifestFilePath)

		self._androidInfo = None


	####################################################################################################################
	### Private methods
	####################################################################################################################

	def _getInfo(self, arch):
		key = (self._androidNdkRootPath, self._androidSdkRootPath, arch)

		if key not in AndroidInfo.Instances:
			def _getToolchainPrefix():
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

			def _getStlArchName():
				stlArchName = {
					"x86": "x86",
					"x64": "x86_64",
					"arm": "armeabi-v7a",
					"arm64": "arm64-v8a",
					"mips": "mips",
					"mips64": "mips64",
				}.get(arch, "")
				assert stlArchName, "Android architecture not supported: {}".format(arch)

				return stlArchName

			def _getIncludeArchName():
				# Search for a toolchain by architecture.
				includeArchName = {
					"x86": "i686-linux-android",
					"x64": "x86_64-linux-android",
					"arm": "arm-linux-androideabi",
					"arm64": "arm-linux-androideabi",
					"mips": "mipsel-linux-android",
					"mips64": "mips64el-linux-android",
				}.get(arch, "")
				assert includeArchName, "Android architecture not supported: {}".format(arch)

				return includeArchName

			platformName = platform.system().lower()
			exeExtension = ".exe" if platform.system() == "Windows" else ""
			toolchainPrefix = _getToolchainPrefix()
			rootToolchainPath = os.path.join(self._androidNdkRootPath, "toolchains")
			archToolchainPath = glob.glob(os.path.join(rootToolchainPath, "{}-*".format(toolchainPrefix)))
			llvmToolchainPath = glob.glob(os.path.join(rootToolchainPath, "llvm", "prebuilt", "{}-*".format(platformName)))
			stlArchName = _getStlArchName()
			stlRootPath = os.path.join(self._androidNdkRootPath, "sources", "cxx-stl")
			sysRootPath = os.path.join(self._androidNdkRootPath, "platforms", "android-{}".format(self._androidTargetSdkVersion), self._getPlatformArchName(arch))
			sysRootLibPath = os.path.join(sysRootPath, "usr", "lib")
			sysRootBaseIncludePath = os.path.join(self._androidNdkRootPath, "sysroot", "usr", "include")
			sysRootArchIncludePath = os.path.join(sysRootBaseIncludePath, _getIncludeArchName())
			nativeAppGluePath = os.path.join(self._androidNdkRootPath, "sources", "android", "native_app_glue")

			assert archToolchainPath, "No Android toolchain installed for architecture: {}".format(arch)
			assert llvmToolchainPath, "No Android LLVM toolchain installed for platform: {}".format(platformName)
			assert os.access(sysRootPath, os.F_OK), "No Android sysroot found at path: {}".format(sysRootPath)

			archToolchainPath = archToolchainPath[0]

			gccVersionStartIndex = archToolchainPath.rfind("-")
			assert gccVersionStartIndex > 0, "Android GCC version not parsable from path: {}".format(archToolchainPath)

			# Save the gcc version since we'll need it for getting the libstdc++ paths.
			gccVersion = archToolchainPath[gccVersionStartIndex + 1:]

			archToolchainPath = glob.glob(os.path.join(archToolchainPath, "prebuilt", "{}-*".format(platformName)))
			assert archToolchainPath, "No Android \"{}\" toolchain installed for platform: {}".format(toolchainPrefix, platformName)

			archToolchainPath = os.path.join(archToolchainPath[0], "bin")
			llvmToolchainPath = os.path.join(llvmToolchainPath[0], "bin")

			# Get the compiler and linker paths.
			gccPath = glob.glob(os.path.join(archToolchainPath, "*-android-gcc{}".format(exeExtension)))
			gppPath = glob.glob(os.path.join(archToolchainPath, "*-android-g++{}".format(exeExtension)))
			asPath = glob.glob(os.path.join(archToolchainPath, "*-android-as{}".format(exeExtension)))
			ldPath = glob.glob(os.path.join(archToolchainPath, "*-android-ld{}".format(exeExtension)))
			arPath = glob.glob(os.path.join(archToolchainPath, "*-android-ar{}".format(exeExtension)))
			clangPath = os.path.join(llvmToolchainPath, "clang{}".format(exeExtension))
			clangppPath = os.path.join(llvmToolchainPath, "clang++{}".format(exeExtension))

			assert gccPath, "No Android gcc executable found for architecture: {}".format(arch)
			assert gppPath, "No Android g++ executable found for architecture: {}".format(arch)
			assert asPath, "No Android as executable found for architecture: {}".format(arch)
			assert ldPath, "No Android ld executable found for architecture: {}".format(arch)
			assert arPath, "No Android ar executable found for architecture: {}".format(arch)
			assert os.access(clangPath, os.F_OK), "No Android clang executable found for architecture: {}".format(arch)
			assert os.access(clangppPath, os.F_OK), "No Android clang++ executable found for architecture: {}".format(arch)

			gccPath = gccPath[0]
			gppPath = gppPath[0]
			asPath = asPath[0]
			ldPath = ldPath[0]
			arPath = arPath[0]

			buildToolsPath = glob.glob(os.path.join(self._androidSdkRootPath, "build-tools", "*"))
			assert buildToolsPath, "No Android build tools are installed"

			# For now, it doesn't seem like we need a specific version, so just pick the first one.
			buildToolsPath = buildToolsPath[0]

			# Get the miscellaneous build tool paths.
			zipAlignPath = os.path.join(buildToolsPath, "zipalign{}".format(exeExtension))

			assert os.access(zipAlignPath, os.F_OK), "ZipAlign not found in Android build tools path: {}".format(buildToolsPath)

			# Get the root paths to each STL flavor.
			libStdCppRootPath = os.path.join(stlRootPath, "gnu-libstdc++", gccVersion)
			libCppRootPath = os.path.join(stlRootPath, "llvm-libc++")
			stlPortRootPath = os.path.join(stlRootPath, "stlport")

			assert os.access(libStdCppRootPath, os.F_OK), "Android libstdc++ not found at path: {}".format(libStdCppRootPath)
			assert os.access(libCppRootPath, os.F_OK), "Android libc++ not found at path: {}".format(libCppRootPath)
			assert os.access(stlPortRootPath, os.F_OK), "Android stlport not found at path: {}".format(stlPortRootPath)

			libStdCppLibPath = os.path.join(libStdCppRootPath, "libs", stlArchName)
			libCppLibPath = os.path.join(libCppRootPath, "libs", stlArchName)
			stlPortLibPath = os.path.join(stlPortRootPath, "libs", stlArchName)

			libStdCppIncludePaths = [
				os.path.join(libStdCppRootPath, "include"),
				os.path.join(libStdCppLibPath, "include"),
			]
			libCppIncludePaths = [
				os.path.join(libCppRootPath, "include"),
			]
			stlPortIncludePaths = [
				os.path.join(stlPortRootPath, "stlport"),
			]

			AndroidInfo.Instances[key] = \
				AndroidInfo(
					gccPath,
					gppPath,
					asPath,
					ldPath,
					arPath,
					clangPath,
					clangppPath,
					zipAlignPath,
					sysRootLibPath,
					[
						sysRootBaseIncludePath,
						sysRootArchIncludePath,
					],
					nativeAppGluePath,
					libStdCppLibPath,
					libStdCppIncludePaths,
					libCppLibPath,
					libCppIncludePaths,
					stlPortLibPath,
					stlPortIncludePaths,
				)

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

	@staticmethod
	def SetAndroidStlLib(lib):
		"""
		Sets the Android STL lib type.

		:param lib: Android STL lib type.
		:type lib: int
		"""
		csbuild.currentPlan.SetValue("androidStlLibType", lib)

	@staticmethod
	def UseDefaultAndroidNativeAppGlue(useDefaultAppGlue):
		"""
		Sets a boolean to use the default Android native app glue.

		:param useDefaultAppGlue: Use default Android native app glue?
		:type useDefaultAppGlue: bool
		"""
		csbuild.currentPlan.SetValue("androidUseDefaultNativeAppGlue", useDefaultAppGlue)
