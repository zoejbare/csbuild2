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
.. module:: android
	:synopsis: Built-in Visual Studio platform handler for outputing Android project files.

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild

from . import VsBasePlatformHandler

def _ignore(_):
	pass

class VsNsightTegraPlatformHandler(VsBasePlatformHandler):
	"""
	Visual Studio platform handler as a base class, containing project writing functionality for the Nsight Tegra (Android) platform.
	"""
	def __init__(self, buildTarget, vsInstallInfo):
		VsBasePlatformHandler.__init__(self, buildTarget, vsInstallInfo)

	@staticmethod
	def GetVisualStudioPlatformName():
		"""
		Get the name that is recognizeable by Visual Studio for the current platform.

		:return: Visual Studio platform name.
		:rtype: str
		"""
		return "Tegra-Android"

	@staticmethod
	def GetOutputExtensionIfDebuggable(projectOutputType):
		"""
		Get the file extension of the input project output type for the current platform.
		Only applies to debuggable projects.  Any other project types should return `None`.

		:param projectOutputType: Final output type of a project.
		:type projectOutputType: any

		:return: Application extension.
		:rtype: str
		"""
		return {
			csbuild.ProjectType.Application: ".apk",
		}.get(projectOutputType, None)

	@staticmethod
	def GetIntellisenseAdditionalOptions(project, buildSpec):
		"""
		Get any additional NMake options to configure intellisense.

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param buildSpec: Build spec being written to use with the project data.
		:type buildSpec: tuple[str, str, str]

		:return: Additional NMake options.
		:rtype: str or None
		"""
		ccStandard = project.platformCcLanguageStandard[buildSpec]
		cxxStandard = project.platformCxxLanguageStandard[buildSpec]
		args = [
			"/std:{}".format(ccStandard) if ccStandard else None,
			"/std:{}".format(cxxStandard) if cxxStandard else None,
			"/Zc:__STDC__",
			"/Zc:__cplusplus",
		]
		return " ".join([x for x in args if x])

	def WriteGlobalHeader(self, parentXmlNode, project):
		"""
		Write any top-level information about this platform at the start of the project file.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject
		"""
		propertyGroupXmlNode = self._addXmlNode(parentXmlNode, "PropertyGroup")
		propertyGroupXmlNode.set("Label", "NsightTegraProject")

		tegraRevisionNumberXmlNode = self._addXmlNode(propertyGroupXmlNode, "NsightTegraProjectRevisionNumber")
		tegraRevisionNumberXmlNode.text = "11"

		upgradeWithoutPromptXmlNode = self._addXmlNode(propertyGroupXmlNode, "NsightTegraUpgradeOnceWithoutPrompt")
		upgradeWithoutPromptXmlNode.text = "true"

	def WriteProjectConfiguration(self, parentXmlNode, project, buildSpec, vsConfig):
		"""
		Write the project configuration nodes for this platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param buildSpec: Build spec being written to use with the project data.
		:type buildSpec: tuple[str, str, str]

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format(vsConfig, vsPlatformName)

		projectConfigXmlNode = self._addXmlNode(parentXmlNode, "ProjectConfiguration")
		projectConfigXmlNode.set("Include", vsBuildTarget)

		configXmlNode = self._addXmlNode(projectConfigXmlNode, "Configuration")
		configXmlNode.text = vsConfig

		platformXmlNode = self._addXmlNode(projectConfigXmlNode, "Platform")
		platformXmlNode.text = vsPlatformName

	def WriteConfigPropertyGroup(self, parentXmlNode, project, buildSpec, vsConfig):
		"""
		Write the property group nodes for the project's configuration and platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param buildSpec: Build spec being written to use with the project data.
		:type buildSpec: tuple[str, str, str]

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format(vsConfig, vsPlatformName)

		propertyGroupXmlNode = self._addXmlNode(parentXmlNode, "PropertyGroup")
		propertyGroupXmlNode.set("Label", "Configuration")
		propertyGroupXmlNode.set("Condition", "'$(Configuration)|$(Platform)'=='{}'".format(vsBuildTarget))

		configTypeXmlNode = self._addXmlNode(propertyGroupXmlNode, "ConfigurationType")
		configTypeXmlNode.text = "ExternalBuildSystem"

	def WriteUserDebugPropertyGroup(self, parentXmlNode, project, buildSpec, vsConfig):
		"""
		Write the property group nodes specifying the user debug settings.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param buildSpec: Build spec being written to use with the project data.
		:type buildSpec: tuple[str, str, str]

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format(vsConfig, vsPlatformName)

		propertyGroupXmlNode = self._addXmlNode(parentXmlNode, "PropertyGroup")
		propertyGroupXmlNode.set("Condition", "'$(Configuration)|$(Platform)'=='{}'".format(vsBuildTarget))

		workingDirXmlNode = self._addXmlNode(propertyGroupXmlNode, "BuildXmlPath")
		workingDirXmlNode.text = "$(OutDir)"
