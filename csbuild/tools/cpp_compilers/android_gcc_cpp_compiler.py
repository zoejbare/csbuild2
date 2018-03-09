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
.. module:: android_base_cpp_compiler
	:synopsis: Android GCC compiler tool for C++.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import os

from ..common.android_tool_base import AndroidToolBase, AndroidStlLibType

from .gcc_cpp_compiler import GccCppCompiler

from ..._build.input_file import  InputFile

# BEGIN TEMP
# Commandline args from a test in the Tegra VS plugin that compiles correctly:
# -fpic -funwind-tables -fstack-protector -march=armv8-a -fno-exceptions -fno-rtti -O0 -g3 -gdwarf-4 -ggdb3 -D__ANDROID_API__=26 -DANDROID_NDK -DANDROID -D__ANDROID__ -fno-omit-frame-pointer -fno-strict-aliasing -funswitch-loops -finline-limit=100 -I"C:/NVPACK/android-ndk-r15c/sources/cxx-stl/llvm-libc++/include" -I"C:/NVPACK/android-ndk-r15c/sources/android/support/include" -I"C:/NVPACK/android-ndk-r15c/sysroot/usr/include" -I"C:/NVPACK/android-ndk-r15c/sysroot/usr/include/aarch64-linux-android" -I"C:/NVPACK/android-ndk-r15c/sources/cxx-stl/llvm-libc++/include" -I"C:/NVPACK/android-ndk-r15c/sources/android/support/include" -I"C:/NVPACK/android-ndk-r15c/toolchains/aarch64-linux-android-4.9/prebuilt/windows-x86_64/lib/gcc/aarch64-linux-android/4.9.x/include" -Wa,--noexecstack -fno-short-enums -std=gnu++11 -x c++ -I"C:/NVPACK/android-ndk-r15c/sysroot/usr/include" -I"C:/NVPACK/android-ndk-r15c/sysroot/usr/include/aarch64-linux-android" -o Tegra-Android/Debug/Android1.o  -c -MD jni/Android1.cpp C:/USERS/BRANDON/DESKTOP/ANDROID1/JNI/ANDROID1.CPP
# END TEMP

class AndroidGccCppCompiler(GccCppCompiler, AndroidToolBase):
	"""
	Android GCC c++ compiler implementation
	"""
	supportedArchitectures = AndroidToolBase.supportedArchitectures

	def __init__(self, projectSettings):
		GccCppCompiler.__init__(self, projectSettings)
		AndroidToolBase.__init__(self, projectSettings)


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		"""
		Run project setup, if any, before building the project, but after all dependencies have been resolved.

		:param project: project being set up
		:type project: csbuild._build.project.Project
		"""
		GccCppCompiler.SetupForProject(self, project)
		AndroidToolBase.SetupForProject(self, project)

		if project.projectType == csbuild.ProjectType.Application and self._androidUseDefaultNativeAppGlue:
			nativeAppGlueSourcePath = os.path.join(self._androidInfo.nativeAppGluPath, "android_native_app_glue.c")
			assert os.access(nativeAppGlueSourcePath, os.F_OK), "Android native app glue source file not found at path: {}".format(nativeAppGlueSourcePath)

			project.inputFiles[".c"].add(InputFile(nativeAppGlueSourcePath))

	def _getComplierName(self, isCpp):
		return self._androidInfo.gppPath if isCpp else self._androidInfo.gccPath

	def _getPreprocessorArgs(self):
		args = [
			"-D__ANDROID_API__={}".format(self._androidTargetSdkVersion),
			"-DANDROID_NDK",
			"-DANDROID",
			"-D__ANDROID__",
		]
		return args + GccCppCompiler._getPreprocessorArgs(self)

	def _getArchitectureArgs(self, project):
		# The architecture is implied from the executable being run.
		return []

	def _getSystemArgs(self, project, isCpp):
		stlIncPaths = {
			AndroidStlLibType.Gnu: self._androidInfo.libStdCppIncludePaths,
			AndroidStlLibType.LibCpp: self._androidInfo.libCppIncludePaths,
			AndroidStlLibType.StlPort: self._androidInfo.stlPortIncludePaths,
		}.get(self._androidStlLibType, None)
		assert stlIncPaths, "Invalid Android STL library type: {}".format(self._androidStlLibType)

		args = []

		# Add the sysroot include paths.
		for path in self._androidInfo.systemIncludePaths:
			args.extend([
				"-isystem",
				path,
			])

		if isCpp:
			# Add each include path for the selected version of STL.
			for path in stlIncPaths:
				args.extend([
					"-isystem",
					path,
				])

		if self._androidUseDefaultNativeAppGlue:
			args.extend([
				"-isystem",
				self._androidInfo.nativeAppGluPath,
			])

		return args
