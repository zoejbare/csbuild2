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
import os

from abc import ABCMeta

from ..._utils.decorators import MetaClass
from ...toolchain import Tool


@MetaClass(ABCMeta)
class AndroidToolBase(Tool):
	"""
	Parent class for all tools targetting Apple platforms.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)

		self._ndkHomePath = projectSettings.get("androidNdkHomePath", "")
		self._sdkHomePath = projectSettings.get("androidSdkHomePath", "")
		self._antHomePath = projectSettings.get("androidAntHomePath", "")
		self._javaHomePath = projectSettings.get("androidJavaHomePath", "")
		self._androidManifestFilePath = projectSettings.get("androidManifestFilePath", "")

		assert self._ndkHomePath, "Android NDK home path not provided"
		assert os.access(self._ndkHomePath, os.F_OK), "Android NDK home path does not exist: {}".format(self._ndkHomePath)

		assert self._sdkHomePath, "Android SDK home path not provided"
		assert os.access(self._sdkHomePath, os.F_OK), "Android SDK home path does not exist: {}".format(self._sdkHomePath)

		assert self._antHomePath, "Android Ant home path not provided"
		assert os.access(self._antHomePath, os.F_OK), "Android Ant home path does not exist: {}".format(self._antHomePath)

		assert self._javaHomePath, "Android Java home path not provided"
		assert os.access(self._javaHomePath, os.F_OK), "Android Java home path does not exist: {}".format(self._javaHomePath)

		assert self._androidManifestFilePath, "Android manifest file path not provided"
		assert os.access(self._androidManifestFilePath, os.F_OK), "Android manifest file path does not exist: {}".format(self._androidManifestFilePath)


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def SetupForProject(self, project):
		Tool.SetupForProject(self, project)


	################################################################################
	### Static makefile methods
	################################################################################

	@staticmethod
	def SetAndroidNdkHomePath(path):
		"""
		Sets the path to the Android NDK home.

		:param path: Android NDK home path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidNdkHomePath", os.path.abspath(path))

	@staticmethod
	def SetAndroidSdkHomePath(path):
		"""
		Sets the path to the Android SDK home.

		:param path: Android SDK home path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidSdkHomePath", os.path.abspath(path))

	@staticmethod
	def SetAndroidAntHomePath(path):
		"""
		Sets the path to the Android Ant home.

		:param path: Android Ant home path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidAntHomePath", os.path.abspath(path))

	@staticmethod
	def SetAndroidJavaHomePath(path):
		"""
		Sets the path to the Android Java home.

		:param path: Android Java home path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidJavaHomePath", os.path.abspath(path))

	@staticmethod
	def SetAndroidManifestFilePath(path):
		"""
		Sets the path to the Android manifest file.

		:param path: Android manifest file path.
		:type path: str
		"""
		csbuild.currentPlan.SetValue("androidManifestFilePath", os.path.abspath(path))
