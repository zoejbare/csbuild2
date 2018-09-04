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
.. modele:: windows
	:synopsis: Built-in Visual Studio platform handlers for outputing Windows-compatible project files.

.. moduleauthor:: Brandon Bare
"""

from .. import VsBasePlatformHandler


class VsBaseWindowsPlatformHandler(VsBasePlatformHandler):
	"""
	Visual Studio platform handler as a base class, containing project writing functionality for all Windows platforms.
	"""
	def __init__(self):
		VsBasePlatformHandler.__init__(self)

	def WriteProjectConfiguration(self, parentXmlNode, generator):
		"""
		Write the project configuration nodes for this platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param generator: Visual Studio project generator to use when writing out data.
		:type generator: VsProjectGenerator
		"""
		pass

	def WriteConfigPropertyGroup(self, parentXmlNode, generator):
		"""
		Write the property group nodes for the project's configuration and platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param generator: Visual Studio project generator to use when writing out data.
		:type generator: VsProjectGenerator
		"""
		pass

	def WriteImportProperties(self, parentXmlNode, generator):
		"""
		Write any special import properties for this platform.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param generator: Visual Studio project generator to use when writing out data.
		:type generator: VsProjectGenerator
		"""
		pass

	def WriteUserDebugPropertyGroup(self, parentXmlNode, generator):
		"""
		Write the property group nodes specifying the user debug settings.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param generator: Visual Studio project generator to use when writing out data.
		:type generator: VsProjectGenerator
		"""
		pass
