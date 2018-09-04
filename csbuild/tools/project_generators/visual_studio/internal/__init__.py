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
.. package:: internal
	:synopsis: Internal functionality for the Visual Studio solution generator.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import os
import sys
import uuid

from csbuild import log

from ....assemblers.gcc_assembler import GccAssembler
from ....assemblers.msvc_assembler import MsvcAssembler

from ....cpp_compilers.cpp_compiler_base import CppCompilerBase

from ....java_compilers.java_compiler_base import JavaCompilerBase


class Version(object):
	"""
	Enum values representing Visual Studio versions.
	"""
	Vs2010 = "2010"
	Vs2012 = "2012"
	Vs2013 = "2013"
	Vs2015 = "2015"
	Vs2017 = "2017"


# Dictionary of MSVC version numbers to tuples of items needed for the file format.
#   Tuple[0] = Friendly version name for logging output.
#   Tuple[1] = File format version (e.g., "Microsoft Visual Studio Solution File, Format Version XX").
#   Tuple[2] = Version of Visual Studio the solution belongs to (e.g., "# Visual Studio XX").
FILE_FORMAT_VERSION_INFO = {
	Version.Vs2010: ("2010", "11.00", "2010"),
	Version.Vs2012: ("2012", "12.00", "2012"),
	Version.Vs2013: ("2013", "12.00", "2013"),
	Version.Vs2015: ("2015", "12.00", "14"),
	Version.Vs2017: ("2017", "12.00", "15"),
}

CPP_SOURCE_FILE_EXTENSIONS = CppCompilerBase.inputFiles
CPP_HEADER_FILE_EXTENSIONS = { ".h", ".hh", ".hpp", ".hxx" }

ASM_FILE_EXTENSIONS = GccAssembler.inputFiles | MsvcAssembler.inputFiles

MISC_FILE_EXTENSIONS = { ".inl", ".inc", ".def" } \
	| JavaCompilerBase.inputGroups

ALL_FILE_EXTENSIONS = CPP_SOURCE_FILE_EXTENSIONS \
	| CPP_HEADER_FILE_EXTENSIONS \
	| ASM_FILE_EXTENSIONS \
	| MISC_FILE_EXTENSIONS

# Global set of generated UUIDs for Visual Studio projects.  The list is needed to make sure there are no
# duplicates when generating new IDs.
UUID_TRACKER = set()


def _generateUuid(name):
	"""
	Generate a new UUID.

	:param name: Name to use for hashing the new ID.
	:type name: str

	:return: New UUID
	:rtype: :class:`UUID`
	"""
	global UUID_TRACKER

	nameIndex = 0
	nameToHash = name if name else ""

	# Keep generating new UUIDs until we've found one that isn't already in use. This is only useful in cases
	# where we have a pool of objects and each one needs to be guaranteed to have a UUID that doesn't collide
	# with any other object in the same pool.  Though, because of the way UUIDs work, having a collision should
	# be extremely rare anyway.
	while True:
		newUuid = uuid.uuid5( uuid.NAMESPACE_OID, nameToHash )
		if not newUuid in UUID_TRACKER:
			UUID_TRACKER.add( newUuid )
			return newUuid

		# Name collision!  The easy solution here is to slightly modify the name in a predictable way.
		nameToHash = "{}{}".format( name, nameIndex )
		nameIndex += 1


def _fixConfigName( configName ):
	# Visual Studio can be exceptionally picky about configuration names.  For instance, if your build script
	# has the "debug" target, you may run into problems with Visual Studio showing that alongside it's own
	# "Debug" configuration, which it may have decided to silently add alongside your own.  The solution is to
	# just put the configurations in a format it expects (first letter upper case). That way, it will see "Debug"
	# already there and won't try to silently 'fix' that up for you.
	return configName.capitalize()


def _getItemRootFolderName(filePath):
	fileExt = os.path.splitext(filePath)[1]
	if fileExt in CPP_SOURCE_FILE_EXTENSIONS:
		return "C/C++ source files"
	elif fileExt in CPP_HEADER_FILE_EXTENSIONS:
		return "C/C++ header files"
	elif fileExt in ASM_FILE_EXTENSIONS:
		return "Assembly files"
	elif not fileExt:
		return "Unknown files"

	fileTypeName = fileExt[1:].capitalize()
	return "{} files".format(fileTypeName)


def _getSourceFileProjectStructure(projWorkingPath, projExtraPaths, filePath, separateFileExtensions):
	projStructure = []

	# The first item should be the file name directory if separating by file extension.
	if separateFileExtensions:
		folderName = _getItemRootFolderName(filePath)

		projStructure.append(folderName)

	relativePath = None
	tempPath = os.path.relpath(filePath, projWorkingPath)

	if tempPath != filePath:
		# The input file path is under the project's working directory.
		relativePath = tempPath

	else:
		# The input file path is outside the project's working directory.
		projStructure.append("[External]")

		# Search each extra source directory in the project to see if the input file path is under one of them.
		for extraPath in projExtraPaths:
			tempPath = os.path.relpath(filePath, extraPath)

			if tempPath != filePath:
				# Found the extra source directory that contains the input file path.
				relativePath = tempPath
				rootPath = filePath[:-(len(relativePath) + 1)]
				baseFolderName = os.path.basename(rootPath)

				# For better organization, add the input file to a special directory that hopefully identifies it.
				projStructure.append(baseFolderName)
				break

	if not relativePath:
		# The input file was not found under any source directory, so it'll just be added by itself.
		projStructure.append(os.path.basename(filePath))

	else:
		# Take the relative path and split it into segments to form the remaining directories for the project structure.
		relativePath = relativePath.replace("\\", "/")
		pathSegments = relativePath.split("/")

		projStructure.extend(pathSegments)

	return projStructure


class VsProjectType(object):
	"""
	Enum describing project types.
	"""
	Root = "root"
	Standard = "standard"
	BuildAll = "build_all"
	Regen = "regen"
	Filter = "filter"


class VsProjectItemType(object):
	"""
	Enum describing project item types.
	"""
	File = "file"
	Folder = "folder"


class VsProjectItem(object):
	"""
	Container for items owned by Visual Studio projects.
	"""
	def __init__(self, name, path, itemType):
		self.name = name
		self.path = path
		self.itemType = itemType
		self.supportedPlatforms = set()
		self.children = {}


class VsProject(object):
	"""
	Container for project-level data in Visual Studio.
	"""
	def __init__(self, name, projType):
		self.name = name
		self.projType = projType
		self.guid = _generateUuid(name)
		self.children = {}
		self.items = {}
		self.supportedPlatforms = set()
		self.platformIncludePaths = {}
		self.platformDefines = {}

	def MergeProjectData(self, platformId, generator):
		if self.projType == VsProjectType.Standard:
			projectData = generator.projectData

			# Make sure the current platform is registered for this project.
			if platformId not in self.supportedPlatforms:
				self.supportedPlatforms.add(platformId)
				self.platformIncludePaths.update({ platformId: [] })
				self.platformDefines.update({ platformId: [] })

			self.platformIncludePaths[platformId].extend([x for x in generator.includeDirectories])
			self.platformDefines[platformId].extend([x for x in generator.defines])

			# Added items for each source file in the project.
			for filePath in generator.sourceFiles:
				projStructure = _getSourceFileProjectStructure(projectData.workingDirectory, projectData.sourceDirs, filePath, True)
				parentMap = self.items

				# Get the file item, then remove it from the project structure.
				fileItem = VsProjectItem(projStructure[-1], filePath, VsProjectItemType.File)
				projStructure = projStructure[:-1]

				# Build the hierarchy of folder items under the project.
				for segment in projStructure:
					if segment not in parentMap:
						parentMap.update({ segment: VsProjectItem(segment, None, VsProjectItemType.Folder) })

					parentMap = parentMap[segment].children

				if fileItem.name not in parentMap:
					# The current file item is new, so map it under the parent item.
					parentMap.update({ fileItem.name: fileItem })

				else:
					# The current file item already exists, so get the original object for its mapping.
					fileItem = parentMap[fileItem.name]

				# Update the set of supported platforms for the current file item.
				fileItem.supportedPlatforms.add(platformId)


def _buildProjectHierarchy(generators):
	rootProject = VsProject(None, VsProjectType.Root)

	for gen in generators:
		platformId = (gen.projectData.toolchainName, gen.projectData.architectureName, _fixConfigName(gen.projectData.targetName))
		parent = rootProject

		# Find the appropriate parent project if this project is part of a group.
		for segment in gen.groupSegments:
			# If the current segment in the group is not represented in the current parent's child project list yet,
			# create it and insert it.
			if segment not in parent.children:
				parent.children.update({ segment: VsProject(segment, VsProjectType.Filter) })

			parent = parent.children[segment]

		projName = gen.projectData.name

		if projName not in parent.children:
			# The current project does not exist yet, so create it and map it as a child to the parent project.
			proj = VsProject(projName, VsProjectType.Standard)
			parent.children.update({ projName: proj })

		else:
			# Get the existing project entry from the parent.
			proj = parent.children[projName]

		# Merge the generator's platform data into the project.
		proj.MergeProjectData(platformId, gen)


	return rootProject


def WriteProjectFiles(outputRootPath, solutionName, generators, vsVersion):
	"""
	Write out the Visual Studio project files.

	:param outputRootPath: Root path for all output files.
	:type outputRootPath: str

	:param solutionName: Name of the output solution file.
	:type solutionName: str

	:param generators: List of project generators.
	:type generators: list[csbuild.tools.project_generators.visual_studio.VsProjectGenerator]

	:param vsVersion: Version of Visual Studio to create projects for.
	:type vsVersion: str
	"""
	rootProject = _buildProjectHierarchy(generators)
