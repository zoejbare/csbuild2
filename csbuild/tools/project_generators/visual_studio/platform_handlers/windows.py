# Copyright (C) 2018 Jaedyn K. Draper
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
.. module:: windows
	:synopsis: Built-in Visual Studio platform handlers for outputing Windows-compatible project files.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

from . import VsBasePlatformHandler


class VsBaseWindowsPlatformHandler(VsBasePlatformHandler):
	"""
	Visual Studio platform handler as a base class, containing project writing functionality for all Windows platforms.
	"""
	def __init__(self, buildTarget, vsInstallInfo):
		VsBasePlatformHandler.__init__(self, buildTarget, vsInstallInfo)

	def WriteConfigPropertyGroup(self, parentXmlNode, project, vsConfig):
		"""
		Write the property group nodes for the project's configuration and platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format(vsConfig, vsPlatformName)

		propertyGroupXmlNode = self._addXmlNode(parentXmlNode, "PropertyGroup")
		propertyGroupXmlNode.set("Label", "Configuration")
		propertyGroupXmlNode.set("Condition", "'$(Configuration)|$(Platform)'=='{}'".format(vsBuildTarget))

		# While required for all native Visual Studio projects, makefiles projects won't really suffer any
		# ill effects from not having this, but Visual Studio will sometimes annoyingly list each project
		# as being built for another version of Visual Studio.  Adding the correct toolset for the running
		# version of Visual Studio will make that annoyance go away.
		platformToolsetXmlNode = self._addXmlNode(propertyGroupXmlNode, "PlatformToolset")
		platformToolsetXmlNode.text = self.vsInstallInfo.toolsetVersion

		configTypeNode = self._addXmlNode(propertyGroupXmlNode, "ConfigurationType")
		configTypeNode.text = "Makefile"

	def WriteUserDebugPropertyGroup(self, parentXmlNode, project, vsConfig):
		"""
		Write the property group nodes specifying the user debug settings.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format(vsConfig, vsPlatformName)

		propertyGroupXmlNode = self._addXmlNode(parentXmlNode, "PropertyGroup")
		propertyGroupXmlNode.set("Condition", "'$(Configuration)|$(Platform)'=='{}'".format(vsBuildTarget))

		workingDirXmlNode = self._addXmlNode(propertyGroupXmlNode, "LocalDebuggerWorkingDirectory")
		workingDirXmlNode.text = "$(OutDir)"

		debuggerTypeXmlNode = self._addXmlNode(propertyGroupXmlNode, "LocalDebuggerDebuggerType")
		debuggerTypeXmlNode.text = "NativeOnly"

		debuggerFlavorXmlNode = self._addXmlNode(propertyGroupXmlNode, "DebuggerFlavor")
		debuggerFlavorXmlNode.text = "WindowsLocalDebugger"


class VsWindowsX86PlatformHandler(VsBaseWindowsPlatformHandler):
	"""
	Visual Studio x86 platform handler implementation.
	"""
	def __init__(self, buildTarget, vsInstallInfo):
		VsBaseWindowsPlatformHandler.__init__(self, buildTarget, vsInstallInfo)

	@staticmethod
	def GetVisualStudioPlatformName():
		"""
		Get the name that is recognizeable by Visual Studio for the current platform.

		:return: Visual Studio platform name.
		:rtype: str
		"""
		return "Win32"


class VsWindowsX64PlatformHandler(VsBaseWindowsPlatformHandler):
	"""
	Visual Studio x64 platform handler implementation.
	"""
	def __init__(self, buildTarget, vsInstallInfo):
		VsBaseWindowsPlatformHandler.__init__(self, buildTarget, vsInstallInfo)

	@staticmethod
	def GetVisualStudioPlatformName():
		"""
		Get the name that is recognizeable by Visual Studio for the current platform.

		:return: Visual Studio platform name.
		:rtype: str
		"""
		return "x64"
