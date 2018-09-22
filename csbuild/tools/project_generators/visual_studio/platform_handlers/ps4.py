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
.. module:: ps4
	:synopsis: Built-in Visual Studio platform handler for outputing PS4 project files.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

from . import VsBasePlatformHandler


class VsPs4PlatformHandler(VsBasePlatformHandler):
	"""
	Visual Studio platform handler as a base class, containing project writing functionality for the PS4 platform.
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
		return "ORBIS"

	@staticmethod
	def GetApplicationExtension():
		"""
		Get the extension that represents executables for the current platform.

		:return: Application extension.
		:rtype: str
		"""
		return ".elf"

	def WriteGlobalFooter(self, parentXmlNode, project):
		"""
		Write any final data nodes needed by the project.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject
		"""
		# Extension settings
		importGroupXmlNode = self._addXmlNode(parentXmlNode, "ImportGroup")
		importGroupXmlNode.set("Label", "ExtensionSettings")

		self._addXmlNode(importGroupXmlNode, "Import").set("Project", r"$(VCTargetsPath)\BuildCustomizations\OrbisWavePsslc.props")
		self._addXmlNode(importGroupXmlNode, "Import").set("Project", r"$(VCTargetsPath)\BuildCustomizations\SCU.props")

		# Extension targets
		importGroupXmlNode = self._addXmlNode(parentXmlNode, "ImportGroup")
		importGroupXmlNode.set("Label", "ExtensionTargets")

		self._addXmlNode(importGroupXmlNode, "Import").set("Project", r"$(VCTargetsPath)\BuildCustomizations\OrbisWavePsslc.targets")
		self._addXmlNode(importGroupXmlNode, "Import").set("Project", r"$(VCTargetsPath)\BuildCustomizations\SCU.targets")

	def WriteGlobalImportTargets(self, parentXmlNode, project):
		"""
		Write global import target needed for the project.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()

		importGroupXmlNode = self._addXmlNode(parentXmlNode, "ImportGroup")
		importGroupXmlNode.set("Condition", "'$(Platform)'=='{}'".format(vsPlatformName))

		importXmlNode = self._addXmlNode(importGroupXmlNode, "Import")
		importXmlNode.set("Condition", r"'$(ConfigurationType)' == 'Makefile' and Exists('$(VCTargetsPath)\Platforms\$(Platform)\SCE.Makefile.$(Platform).targets')")
		importXmlNode.set("Project", r"$(VCTargetsPath)\Platforms\$(Platform)\SCE.Makefile.$(Platform).targets")

	def WriteProjectConfiguration(self, parentXmlNode, project, vsConfig):
		"""
		Write the project configuration nodes for this platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format( vsConfig, vsPlatformName )

		projectConfigXmlNode = self._addXmlNode(parentXmlNode, "ProjectConfiguration")
		projectConfigXmlNode.set("Include", vsBuildTarget)

		configXmlNode = self._addXmlNode(projectConfigXmlNode, "Configuration")
		configXmlNode.text = vsConfig

		platformXmlNode = self._addXmlNode(projectConfigXmlNode, "Platform")
		platformXmlNode.text = vsPlatformName

	def WriteConfigPropertyGroup(self, parentXmlNode, project, vsConfig):
		"""
		Write the property group nodes for the project's configuration and platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format(vsConfig, vsPlatformName)

		propertyGroupXmlNode = self._addXmlNode(parentXmlNode, "PropertyGroup")
		propertyGroupXmlNode.set("Label", "Configuration")
		propertyGroupXmlNode.set("Condition", "'$(Configuration)|$(Platform)'=='{}'".format(vsBuildTarget))

		configTypeXmlNode = self._addXmlNode(propertyGroupXmlNode, "ConfigurationType")
		configTypeXmlNode.text = "Makefile"

	def WriteImportProperties(self, parentXmlNode, project, vsConfig):
		"""
		Write any special import properties for this platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""
		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format(vsConfig, vsPlatformName)

		importGroupXmlNode = self._addXmlNode(parentXmlNode, "ImportGroup")
		importGroupXmlNode.set("Label", "PropertySheets")
		importGroupXmlNode.set("Condition", "'$(Configuration)|$(Platform)'=='{}'".format(vsBuildTarget))

		importXmlNode = self._addXmlNode( importGroupXmlNode, "Import")
		importXmlNode.set("Label", "LocalAppDataPlatform")
		importXmlNode.set("Project", r"$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props")
		importXmlNode.set("Condition", r"exists('$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props')")

	def WriteUserDebugPropertyGroup(self, parentXmlNode, project, vsConfig):
		"""
		Write the property group nodes specifying the user debug settings.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project data.
		:type project: csbuild.tools.project_generators.visual_studio.internal.VsProject

		:param vsConfig: Visual Studio configuration being written.
		:type vsConfig: str
		"""

		vsPlatformName = self.GetVisualStudioPlatformName()
		vsBuildTarget = "{}|{}".format(vsConfig, vsPlatformName)

		propertyGroupXmlNode = self._addXmlNode(parentXmlNode, "PropertyGroup")
		propertyGroupXmlNode.set("Condition", "'$(Configuration)|$(Platform)'=='{}'".format(vsBuildTarget))

		workingDirXmlNode = self._addXmlNode(propertyGroupXmlNode, "LocalDebuggerWorkingDirectory" )
		workingDirXmlNode.text = "$(OutDir)"

		debuggerFlavorXmlNode = self._addXmlNode(propertyGroupXmlNode, "DebuggerFlavor" )
		debuggerFlavorXmlNode.text = "ORBISDebugger"
