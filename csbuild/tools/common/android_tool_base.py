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

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import glob
import os
import platform

from abc import ABCMeta

from ... import log
from ..._utils.decorators import MetaClass
from ...toolchain import Tool

def _getNdkVersion(ndkPath):
	packagePropsFilePath = os.path.join(ndkPath, "source.properties")
	if not os.access(packagePropsFilePath, os.F_OK):
		# The 'source.properties' file was not found, no version information can be extracted.
		return 0, 0, 0

	with open(packagePropsFilePath, "r") as f:
		fileLines = f.readlines()

	commentTokens = { "#", ";", "//" }

	# Check each line for the package revision which contains the version info.
	for line in fileLines:
		if line:
			lineEndIndex = len(line)

			# Comments are typically not found in this file, but we check for them
			# anyway in case someone decides to add them at some point.
			for token in commentTokens:
				if token in line:
					startIndex = line.index(token)

					# Use the earliest comment token found in the line.
					if startIndex < lineEndIndex:
						lineEndIndex = startIndex

			# Strip out any comments found in the line.
			line = line[0:lineEndIndex]

			lineElements = line.split("=", 2)
			lineKey = lineElements[0].strip() if len(lineElements) > 0 else None
			lineValue = lineElements[1].strip() if len(lineElements) > 1 else None

			if lineKey == "Pkg.Revision" and lineValue:
				versions = lineValue.split(".")
				majorVersion = int(versions[0]) if len(versions) > 0 else 0
				minorVersion = int(versions[1]) if len(versions) > 1 else 0
				revision = int(versions[2]) if len(versions) > 2 else 0

				return majorVersion, minorVersion, revision

	# No package revision found.
	return 0, 0, 0

class AndroidInfo(object):
	"""
	Collection of paths for a specific version of Android and architecture.

	:param androidArch: Android target architecture.
	:type androidArch: str

	:param targetSdkVersion: SDK version to target.
	:type targetSdkVersion: int

	:param sdkRootPath: Default Android SDK root path.
	:type sdkRootPath: str

	:param ndkRootPath: Default Android NDK root path.
	:type ndkRootPath: str
	"""
	Instances = {}

	def __init__(self, androidArch, targetSdkVersion, sdkRootPath, ndkRootPath):
		self.sdkVersion = targetSdkVersion
		self.ndkVersion = (0, 0, 0)
		self.sdkRootPath = ""
		self.ndkRootPath = ""
		self.sysIncPaths = []
		self.sysLibPaths = []
		self.prefixPath = ""
		self.buildToolsPath = ""
		self.gccBinPath = ""
		self.clangExePath = ""
		self.clangCppExePath = ""
		self.arExePath = ""
		self.targetTripleName = ""
		self.buildArchName = ""
		self.isBuggyClang = False

		# The Android NDK currently only ships with x64 host support for all platforms.
		toolchainHostPlatformName = "{}-x86_64".format(platform.system().lower())
		exeFileExtension = ".exe" if platform.system() == "Windows" else ""

		# Search for a toolchain by architecture.
		self.targetTripleName, self.buildArchName, archTripleName, gccToolchainName, libcppArchName, sysArchName, platformLibDirName = {
			"x86":    ("i686-none-linux-android",      "i686",    "i686-linux-android",     "x86-4.9",                    "x86",         "arch-x86",    "lib"),
			"x64":    ("x86_64-none-linux-android",    "x86_64",  "x86_64-linux-android",   "x86_64-4.9",                 "x86_64",      "arch-x86_64", "lib64"),
			"arm":    ("armv7-none-linux-androideabi", "armv7-a", "arm-linux-androideabi",  "arm-linux-androideabi-4.9",  "armeabi-v7a", "arch-arm",    "lib"),
			"arm64":  ("aarch64-none-linux-android",   "armv8-a", "aarch64-linux-android",  "aarch64-linux-android-4.9",  "arm64-v8a",   "arch-arm64",  "lib"),
			"mips":   ("mipsel-none-linux-android",    "mips32",  "mipsel-linux-android",   "mipsel-linux-android-4.9",   "mips",        "arch-mips",   "lib"),
			"mips64": ("mips64el-none-linux-android",  "mips64",  "mips64el-linux-android", "mips64el-linux-android-4.9", "mips64",      "arch-mips64", "lib64"),
		}.get(androidArch, (None, None, None, None, None, None, None))
		assert self.targetTripleName is not None, "Architecture not supported for Android: {}".format(androidArch)

		# Verify the target SDK version has been set.
		assert self.sdkVersion, "No Android target SDK version provided"
		assert isinstance(self.sdkVersion, int), "Android target SDK version is not an integer: \"{}\"".format(self.sdkVersion)

		# If no SDK root path is specified, try to get it from the environment.
		possiblePaths = [
			sdkRootPath,
			os.environ.get("ANDROID_HOME", None),
			os.environ.get("ANDROID_SDK_ROOT", None),
		]

		if platform.system() == "Darwin":
			# Special case for default install location of the SDK on macOS.
			possiblePaths.append(os.path.join(os.environ["HOME"], "Library", "Android", "sdk"))

		# Last ditch effort, try the user's home directory as the install location of the SDK.
		possiblePaths.append(os.path.join(os.path.expanduser("~"), "Android", "sdk"))

		# Loop over all the possible paths and go with the first one that exists.
		for candidateSdkPath in possiblePaths:
			if not candidateSdkPath:
				continue

			log.Info("Checking possible Android SDK path: {}".format(candidateSdkPath))
			if os.access(candidateSdkPath, os.F_OK):
				matchingBuildToolsPaths = glob.glob(os.path.join(candidateSdkPath, "build-tools", "{}.*".format(self.sdkVersion)))
				if not matchingBuildToolsPaths:
					log.Warn("Found Android SDK path, but it does not support target version {}: {}".format(self.sdkVersion, candidateSdkPath))
					continue

				log.Info("Using Android SDK: {}".format(candidateSdkPath))

				self.sdkRootPath = candidateSdkPath

				# Select the last matching path in the list since it should be the latest.
				self.buildToolsPath = matchingBuildToolsPaths[-1]
				break

		# Verify the SDK path was set and exists.
		assert self.sdkRootPath, "No valid Android SDK found for target version: {}".format(self.sdkVersion)
		assert os.access(self.sdkRootPath, os.F_OK), "Android SDK root path does not exist: {}".format(self.sdkRootPath)

		# If no NDK root path is specified, try to get it from the environment.
		possibleNdkPaths = [
			ndkRootPath,
			os.environ.get("ANDROID_NDK", None),
			os.environ.get("ANDROID_NDK_ROOT", None),
		]

		# Check for an NDK embedded within the SDK directory.
		possibleNdkPaths.extend(reversed(glob.glob(os.path.join(self.sdkRootPath, "ndk", "*"))))
		possibleNdkPaths.extend(reversed(glob.glob(os.path.join(self.sdkRootPath, "ndk-bundle", "*"))))

		# Loop over all the possible paths and go with the first one that exists and meets our requirements.
		for candidateNdkPath in possibleNdkPaths:
			if not candidateNdkPath:
				continue

			log.Info("Checking possible Android NDK path: {}".format(candidateNdkPath))
			if os.access(candidateNdkPath, os.F_OK):
				ndkVersionMajor, ndkVersionMinor, ndkRevision = _getNdkVersion(candidateNdkPath)

				# Skip very old NDKs since we don't have a reliable way of extracting their version information.
				if ndkVersionMajor == 0:
					log.Warn("Found Android NDK, but unable to detect NDK version: {}".format(candidateNdkPath))
					continue

				# Skip any NDK version we've already checked and all that are older than what we currently have.
				if ndkRevision <= self.ndkVersion[2]:
					continue

				# When either MIPS architecture is selected, skip NDKs that no longer support it.
				if ndkVersionMajor >= 17 and androidArch in { "mips", "mips64" }:
					log.Warn("Found Android NDK, but it does not support any MIPS architectures: {}".format(candidateNdkPath))
					continue

				gccToolchainRootPath = os.path.join(candidateNdkPath, "toolchains", gccToolchainName, "prebuilt", toolchainHostPlatformName)
				gccToolchainBinPath = os.path.join(gccToolchainRootPath, archTripleName, "bin")
				gccToolchainLibPath = glob.glob(os.path.join(gccToolchainRootPath, "lib", "gcc", archTripleName, "4.9*"))

				if gccToolchainLibPath:
					gccToolchainLibPath = gccToolchainLibPath[-1]

				llvmToolchainRootPath = os.path.join(candidateNdkPath, "toolchains", "llvm", "prebuilt", toolchainHostPlatformName)
				llvmToolchainBinPath = os.path.join(llvmToolchainRootPath, "bin")
				llvmToolchainSysRootPath = os.path.join(llvmToolchainRootPath, "sysroot")

				platformRootPath = os.path.join(candidateNdkPath, "platforms")
				platformVersionPath = os.path.join(platformRootPath, "android-{}".format(self.sdkVersion), sysArchName)
				platformIncPath = os.path.join(platformVersionPath, "usr", "include")
				platformLibPath = os.path.join(platformVersionPath, "usr", platformLibDirName)

				toolchainSysLibRootPath = os.path.join(llvmToolchainSysRootPath, "usr", "lib", archTripleName)
				toolchainPlatformSysLibPath = os.path.join(toolchainSysLibRootPath, "{}".format(self.sdkVersion))

				toolchainSysLibPaths = [toolchainPlatformSysLibPath, toolchainSysLibRootPath]

				# The real sysroot path will be determined by the location of the precompiled crt objects.
				def evaluateSysLibPaths(libPaths):
					crtbeginFileName = "crtbegin_so.o"

					for path in libPaths:
						filePath = os.path.join(path, crtbeginFileName)

						if os.access(filePath, os.F_OK):
							return libPaths, path

					return None, None

				# Check the platform sysroot for the real library path.
				realSysLibPaths, prefixPath = evaluateSysLibPaths([platformLibPath])

				# If the real library path couldn't be found, check the toolchain sysroot.
				if not realSysLibPaths:
					realSysLibPaths, prefixPath = evaluateSysLibPaths(toolchainSysLibPaths)

				if not realSysLibPaths:
					log.Warn("Found Android NDK, but failed to find the location of its sysroot libraries: {}".format(candidateNdkPath))
					continue

				baseSysRootPath = os.path.join(candidateNdkPath, "sysroot")
				baseSysIncPath = os.path.join(baseSysRootPath, "usr", "include")
				baseSysIncArchPath = os.path.join(baseSysIncPath, archTripleName)

				toolchainSysIncPath = os.path.join(llvmToolchainSysRootPath, "usr", "include")
				toolchainSysIncArchPath = os.path.join(toolchainSysIncPath, archTripleName)

				sourcesRootPath = os.path.join(candidateNdkPath, "sources")
				sourcesCxxStlRootPath = os.path.join(sourcesRootPath, "cxx-stl", "llvm-libc++")

				sysIncPaths = [
					baseSysIncPath,
					baseSysIncArchPath,
					platformIncPath,
					toolchainSysIncPath,
					toolchainSysIncArchPath,
					os.path.join(sourcesCxxStlRootPath, "include"),
					os.path.join(sourcesCxxStlRootPath, "libcxx", "include"),
				]
				sysLibPaths = realSysLibPaths
				sysLibPaths.extend([
					gccToolchainLibPath,
					os.path.join(sourcesCxxStlRootPath, "libs", libcppArchName),
				])

				# Resolve all the system include and library paths to figure out which actually exist.
				sysIncPaths = [path for path in sysIncPaths if path and os.access(path, os.F_OK)]
				sysLibPaths = [path for path in sysLibPaths if path and os.access(path, os.F_OK)]

				if not sysIncPaths:
					log.Warn("Found Android NDK, but could not find any valid sysroot include paths: {}".format(candidateNdkPath))
					continue

				if not sysLibPaths:
					log.Warn("Found Android NDK, but could not find any valid sysroot library paths: {}".format(candidateNdkPath))
					continue

				gccArExePath = os.path.join(gccToolchainBinPath, "ar{}".format(exeFileExtension))
				llvmArExePath = os.path.join(llvmToolchainBinPath, "llvm-ar{}".format(exeFileExtension))
				clangExePath = os.path.join(llvmToolchainBinPath, "clang{}".format(exeFileExtension))
				clangCppExePath = os.path.join(llvmToolchainBinPath, "clang++{}".format(exeFileExtension))
				arExePath = llvmArExePath if os.access(llvmArExePath, os.F_OK) else gccArExePath

				if not os.access(clangExePath, os.F_OK):
					log.Warn("Found Android NDK, but clang executable is missing: {}".format(candidateNdkPath))
					continue

				if not os.access(clangCppExePath, os.F_OK):
					log.Warn("Found Android NDK, but clang++ executable is missing: {}".format(candidateNdkPath))
					continue

				if not os.access(arExePath, os.F_OK):
					log.Warn("Found Android NDK, but archiver executable is missing: {}".format(candidateNdkPath))
					continue

				log.Info("Using Android NDK: {}".format(candidateNdkPath))

				self.ndkVersion = (ndkVersionMajor, ndkVersionMinor, ndkRevision)
				self.ndkRootPath = candidateNdkPath
				self.sysIncPaths = sysIncPaths
				self.sysLibPaths = sysLibPaths
				self.prefixPath = prefixPath
				self.gccBinPath = gccToolchainBinPath
				self.clangExePath = clangExePath
				self.clangCppExePath = clangCppExePath
				self.arExePath = arExePath

				# Clang in NDK 11 has a bug in its handling of response files, meaning we can't use them with it.
				self.isBuggyClang = (ndkVersionMajor == 11)
				break

		# Verify the NDK path was set and exists.
		assert self.ndkRootPath, "No valid Android NDK found for target version: {}".format(self.sdkVersion)
		assert os.access(self.ndkRootPath, os.F_OK), "Android NDK root path does not exist: {}".format(self.ndkRootPath)


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

		self._androidSdkRootPath = projectSettings.get("androidSdkRootPath", "")
		self._androidNdkRootPath = projectSettings.get("androidNdkRootPath", "")
		self._androidTargetSdkVersion = projectSettings.get("androidTargetSdkVersion", 0)
		self._androidManifestFilePath = projectSettings.get("androidManifestFilePath", "")

		self._androidInfo = None

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
			arch = project.architectureName

			if arch not in AndroidInfo.Instances:
				AndroidInfo.Instances[arch] = AndroidInfo(
					arch,
					self._androidTargetSdkVersion,
					self._androidSdkRootPath,
					self._androidNdkRootPath
				)

			self._androidInfo = AndroidInfo.Instances[arch]

	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getDefaultAndroidDefines(self):
		return [
			"-D__ANDROID_API__={}".format(self._androidTargetSdkVersion),
			"-DANDROID_NDK",
			"-DANDROID",
			"-D__ANDROID__",
		]

	################################################################################
	### Static makefile methods
	################################################################################

	@staticmethod
	def SetAndroidSdkRootPath(path):
		"""
		Sets the path to the Android SDK root.

		:param path: Android SDK root path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidSdkRootPath", os.path.abspath(path) if path else None)

	@staticmethod
	def SetAndroidNdkRootPath(path):
		"""
		Sets the path to the Android NDK home.

		:param path: Android NDK home path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidNdkRootPath", os.path.abspath(path) if path else None)

	@staticmethod
	def SetAndroidTargetSdkVersion(version):
		"""
		Sets the Android target SDK version.

		:param version: Android target SDK version.
		:type version: int
		"""
		csbuild.currentPlan.SetValue("androidTargetSdkVersion", version)

	@staticmethod
	def SetAndroidManifestFilePath(path):
		"""
		Sets the path to the Android manifest file.

		:param path: Android manifest file path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidManifestFilePath", os.path.abspath(path))
