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
.. package:: visual_studio
	:synopsis: Visual Studio project generators

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import os
import abc

from csbuild import log

from . import internal

from ...common.tool_traits import HasDefines, HasIncludeDirectories

from ....toolchain import SolutionGenerator
from ...._utils.decorators import MetaClass


@MetaClass(abc.ABCMeta)
class VsBasePlatformHandler(object):
	def __init__(self):
		pass

	def GetToolchainArchitecturePair(self):
		"""
		Get a tuple describing the toolchain and architecture the current platform handler applies to.

		:return: Tuple of toolchain and architecture.
		:rtype: tuple[str, str]
		"""
		pass

	def GetVisualStudioPlatformName(self):
		"""
		Get the name that is recognizeable by Visual Studio for the current platform.

		:return: Visual Studio platform name.
		:rtype: str
		"""
		pass

	def WriteGlobalHeader(self, parentXmlNode, generator):
		"""
		Write any top-level information about this platform at the start of the project file.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param generator: Visual Studio project generator to use when writing out data.
		:type generator: VsProjectGenerator
		"""
		pass

	def WriteGlobalFooter(self, parentXmlNode, generator):
		"""
		Write any final data nodes needed by the project.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param generator: Visual Studio project generator to use when writing out data.
		:type generator: VsProjectGenerator
		"""
		pass

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

	def WriteExtraPropertyGroupBuildNodes(self, parentXmlNode, generator):
		"""
		Write extra property group nodes related to platform build properties.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param generator: Visual Studio project generator to use when writing out data.
		:type generator: VsProjectGenerator
		"""
		pass

	def WriteGlobalImportTargets(self, parentXmlNode, generator):
		"""
		Write global import target needed for the project.

		:param parentXmlNode: Parent project XML node.
		:type parentXmlNode: xml.etree.ElementTree.SubElement

		:param generator: Visual Studio project generator to use when writing out data.
		:type generator: VsProjectGenerator
		"""
		pass


def AddPlatformHandlers(*args):
	"""
	Added custom platform handlers to the Visual Studio generator.

	:param args: Custom Visual Studio platform handlers.
	:type args: list[VsBasePlatformHandler]
	"""
	pass


class VsProjectGenerator(HasDefines, HasIncludeDirectories):
	"""
	Visual Studio project generator

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	inputGroups = internal.ALL_FILE_EXTENSIONS
	outputFiles = { ".proj" }

	def __init__(self, projectSettings):
		HasDefines.__init__(self, projectSettings)
		HasIncludeDirectories.__init__(self, projectSettings)

		self._projectData = None
		self._sourceFiles = []
		self._groupSegments = []

	def SetupForProject(self, project):
		# No setup necessary.
		pass

	def RunGroup(self, inputProject, inputFiles):
		self._projectData = inputProject
		self._sourceFiles = [x.filename for x in inputFiles]
		# TODO: One project groups are implemented, parse it for the current project and store the results in self._groupSegments.

		return "{}.proj".format(inputProject.outputName)

	@property
	def sourceFiles(self):
		return self._sourceFiles

	@property
	def groupSegments(self):
		return self._groupSegments

	@property
	def includeDirectories(self):
		return self._includeDirectories

	@property
	def defines(self):
		return self._defines

	@property
	def projectData(self):
		return self._projectData


class VsSolutionGenerator2010(SolutionGenerator):
	"""Visual Studio 2010 solution generator"""

	@staticmethod
	def GenerateSolution(outputDir, solutionName, projects): # pylint: disable=missing-raises-doc
		"""
		Generates the actual solution file from the projects generated by each tool.
		The actual project objects are passed to the solution generator, allowing the generator to gather information
		about the projects themselves, as well as outputs returned from the project generator tools
		(via project.inputFiles[".ext"], which is a list of csbuild._build.input_file.InputFile objects) and
		data on the tools (via calling methods and properties on the tool through project.toolchain.Tool(ToolType).Method()
		or project.toolchain.Tool(ToolType).property)

		:param outputDir: Top-level directory all solution files should be placed into
		:type outputDir: str
		:param solutionName: Desired base name of the solution
		:type solutionName: str
		:param projects: Set of all built projects
		:type projects: list[csbuild._build.project.Project]
		"""
		projects = _getProjectData(projects)

		internal.WriteProjectFiles(outputDir, solutionName, projects, internal.Version.Vs2010)


class VsSolutionGenerator2012(SolutionGenerator):
	"""Visual Studio 2012 solution generator"""

	@staticmethod
	def GenerateSolution(outputDir, solutionName, projects): # pylint: disable=missing-raises-doc
		"""
		Generates the actual solution file from the projects generated by each tool.
		The actual project objects are passed to the solution generator, allowing the generator to gather information
		about the projects themselves, as well as outputs returned from the project generator tools
		(via project.inputFiles[".ext"], which is a list of csbuild._build.input_file.InputFile objects) and
		data on the tools (via calling methods and properties on the tool through project.toolchain.Tool(ToolType).Method()
		or project.toolchain.Tool(ToolType).property)

		:param outputDir: Top-level directory all solution files should be placed into
		:type outputDir: str
		:param solutionName: Desired base name of the solution
		:type solutionName: str
		:param projects: Set of all built projects
		:type projects: list[csbuild._build.project.Project]
		"""
		projects = _getProjectData(projects)

		internal.WriteProjectFiles(outputDir, solutionName, projects, internal.Version.Vs2012)


class VsSolutionGenerator2013(SolutionGenerator):
	"""Visual Studio 2013 solution generator"""

	@staticmethod
	def GenerateSolution(outputDir, solutionName, projects): # pylint: disable=missing-raises-doc
		"""
		Generates the actual solution file from the projects generated by each tool.
		The actual project objects are passed to the solution generator, allowing the generator to gather information
		about the projects themselves, as well as outputs returned from the project generator tools
		(via project.inputFiles[".ext"], which is a list of csbuild._build.input_file.InputFile objects) and
		data on the tools (via calling methods and properties on the tool through project.toolchain.Tool(ToolType).Method()
		or project.toolchain.Tool(ToolType).property)

		:param outputDir: Top-level directory all solution files should be placed into
		:type outputDir: str
		:param solutionName: Desired base name of the solution
		:type solutionName: str
		:param projects: Set of all built projects
		:type projects: list[csbuild._build.project.Project]
		"""
		projects = _getProjectData(projects)

		internal.WriteProjectFiles(outputDir, solutionName, projects, internal.Version.Vs2013)


class VsSolutionGenerator2015(SolutionGenerator):
	"""Visual Studio 2015 solution generator"""

	@staticmethod
	def GenerateSolution(outputDir, solutionName, projects): # pylint: disable=missing-raises-doc
		"""
		Generates the actual solution file from the projects generated by each tool.
		The actual project objects are passed to the solution generator, allowing the generator to gather information
		about the projects themselves, as well as outputs returned from the project generator tools
		(via project.inputFiles[".ext"], which is a list of csbuild._build.input_file.InputFile objects) and
		data on the tools (via calling methods and properties on the tool through project.toolchain.Tool(ToolType).Method()
		or project.toolchain.Tool(ToolType).property)

		:param outputDir: Top-level directory all solution files should be placed into
		:type outputDir: str
		:param solutionName: Desired base name of the solution
		:type solutionName: str
		:param projects: Set of all built projects
		:type projects: list[csbuild._build.project.Project]
		"""
		projects = _getProjectData(projects)

		internal.WriteProjectFiles(outputDir, solutionName, projects, internal.Version.Vs2015)


class VsSolutionGenerator2017(SolutionGenerator):
	"""Visual Studio 2017 solution generator"""

	@staticmethod
	def GenerateSolution(outputDir, solutionName, projects): # pylint: disable=missing-raises-doc
		"""
		Generates the actual solution file from the projects generated by each tool.
		The actual project objects are passed to the solution generator, allowing the generator to gather information
		about the projects themselves, as well as outputs returned from the project generator tools
		(via project.inputFiles[".ext"], which is a list of csbuild._build.input_file.InputFile objects) and
		data on the tools (via calling methods and properties on the tool through project.toolchain.Tool(ToolType).Method()
		or project.toolchain.Tool(ToolType).property)

		:param outputDir: Top-level directory all solution files should be placed into
		:type outputDir: str
		:param solutionName: Desired base name of the solution
		:type solutionName: str
		:param projects: Set of all built projects
		:type projects: list[csbuild._build.project.Project]
		"""
		projects = _getProjectData(projects)

		internal.WriteProjectFiles(outputDir, solutionName, projects, internal.Version.Vs2017)


def _getProjectData(projects):
	"""
	Helper function to convert a list of projects to a list of their project generators.

	:param projects: Set of all built projects
	:type projects: list[csbuild._build.project.Project]

	:return: List of project generators
	:rtype: list[csbuild.tools.project_generator.visual_studio.VsProjectGenerator]
	"""
	return [x.toolchain.Tool(VsProjectGenerator) for x in projects]
