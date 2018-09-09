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
	def __init__(self, buildTarget):
		VsBasePlatformHandler.__init__(self, buildTarget)

	def WriteGlobalHeader(self, parentXmlNode, project, config):
		"""
		Write any top-level information about this platform at the start of the project file.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: internal.VsProject

		:param config: Visual Studio configuration being written out.
		:type config: str
		"""
		pass

	def WriteGlobalFooter(self, parentXmlNode, project, config):
		"""
		Write any final data nodes needed by the project.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: internal.VsProject

		:param config: Visual Studio configuration being written out.
		:type config: str
		"""
		pass

	def WriteProjectConfiguration(self, parentXmlNode, project, config):
		"""
		Write the project configuration nodes for this platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: internal.VsProject

		:param config: Visual Studio configuration being written out.
		:type config: str
		"""
		pass

	def WriteConfigPropertyGroup(self, parentXmlNode, project, config):
		"""
		Write the property group nodes for the project's configuration and platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: internal.VsProject

		:param config: Visual Studio configuration being written out.
		:type config: str
		"""
		pass

	def WriteImportProperties(self, parentXmlNode, project, config):
		"""
		Write any special import properties for this platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: internal.VsProject

		:param config: Visual Studio configuration being written out.
		:type config: str
		"""
		pass

	def WriteUserDebugPropertyGroup(self, parentXmlNode, project, config):
		"""
		Write the property group nodes specifying the user debug settings.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: internal.VsProject

		:param config: Visual Studio configuration being written out.
		:type config: str
		"""
		pass

	def WriteExtraPropertyGroupBuildNodes(self, parentXmlNode, project, config):
		"""
		Write extra property group nodes related to platform build properties.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: internal.VsProject

		:param config: Visual Studio configuration being written out.
		:type config: str
		"""
		pass

	def WriteGlobalImportTargets(self, parentXmlNode, project, config):
		"""
		Write global import target needed for the project.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param project: Visual Studio project project data.
		:type project: internal.VsProject

		:param config: Visual Studio configuration being written out.
		:type config: str
		"""
		pass


class VsWindowsX86PlatformHandler(VsBaseWindowsPlatformHandler):
	"""
	Visual Studio x86 platform handler implementation.
	"""
	def __init__(self, buildTarget):
		VsBaseWindowsPlatformHandler.__init__(self, buildTarget)

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
	def __init__(self, buildTarget):
		VsBaseWindowsPlatformHandler.__init__(self, buildTarget)

	@staticmethod
	def GetVisualStudioPlatformName():
		"""
		Get the name that is recognizeable by Visual Studio for the current platform.

		:return: Visual Studio platform name.
		:rtype: str
		"""
		return "x64"
