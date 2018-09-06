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

import codecs
import contextlib
import hashlib
import os
import sys
import tempfile
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


class VsFileInfo(object):
	"""
	Visual Studio version data helper class.

	:ivar friendlyName: Friendly version name for logging.
	:type friendlyName: str

	:ivar fileVersion: File format version (e.g., "Microsoft Visual Studio Solution File, Format Version XX.XX" where "XX.XX" is the member value).
	:type fileVersion: str

	:ivar versionId: Version of Visual Studio the solution belongs to (e.g., "# Visual Studio XX" where "XX" is the member value).
	:type versionId: str
	"""
	def __init__(self, friendlyName, fileVersion, versionId):
		self.friendlyName = friendlyName
		self.fileVersion = fileVersion
		self.versionId = versionId


FILE_FORMAT_VERSION_INFO = {
	Version.Vs2010: VsFileInfo("2010", "11.00", "2010"),
	Version.Vs2012: VsFileInfo("2012", "12.00", "2012"),
	Version.Vs2013: VsFileInfo("2013", "12.00", "2013"),
	Version.Vs2015: VsFileInfo("2015", "12.00", "14"),
	Version.Vs2017: VsFileInfo("2017", "12.00", "15"),
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

# Keep track of the registered platform handlers.
PLATFORM_HANDLERS = {}


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
			return "{{{}}}".format(str(newUuid)).upper()

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


def RegisterPlatformHandler(handler):
	"""
	Register a platform handler.

	:param handler: Platform handler to be registered.
	:type handler: class
	"""
	global PLATFORM_HANDLERS

	key = handler.GetToolchainArchitecturePair()

	if key in PLATFORM_HANDLERS:
		log.Warn("Overwriting Visual Studio platform handler registered for {}".format(key))

	PLATFORM_HANDLERS.update({ key: handler() })


class VsProjectType(object):
	"""
	Enum describing project types.
	"""
	Root = "root"
	Standard = "standard"
	Filter = "filter"


class VsProjectSubType(object):
	"""
	Enum describing project sub-types.
	"""
	Normal = "normal"
	BuildAll = "build_all"
	Regen = "regen"


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
	def __init__(self, name, relFilePath, projType):
		self.name = name
		self.relFilePath = relFilePath
		self.projType = projType
		self.subType = VsProjectSubType.Normal
		self.guid = _generateUuid(name)
		self.children = {}
		self.items = {}
		self.supportedTargets = set()
		self.platformIncludePaths = {}
		self.platformDefines = {}

		self.slnTypeGuid = {
			VsProjectType.Standard: "{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}",
			VsProjectType.Filter: "{2150E333-8FDC-42A3-9474-1A3956D46DE8}",
		}.get(self.projType, "{UNKNOWN}")

	def MergeProjectData(self, target, generator):
		"""
		Merge data for a given target and generator into the project.

		:param target: Target matching the input generator.
		:type target: tuple[str, str, str]

		:param generator: Generator containing the data that needs to be merged into the project.
		:type generator: csbuild.tools.project_generators.visual_studio.VsProjectGenerator
		"""
		if self.projType == VsProjectType.Standard:

			# Register support for the input target.
			if target not in self.supportedTargets:
				self.supportedTargets.add(target)
				self.platformIncludePaths.update({ target: [] })
				self.platformDefines.update({ target: [] })

			# Merge the data from the generator.
			if generator:
				self.platformIncludePaths[target].extend([x for x in generator.includeDirectories])
				self.platformDefines[target].extend([x for x in generator.defines])

				projectData = generator.projectData

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
					fileItem.supportedPlatforms.add(target)


class VsFileProxy(object):
	"""
	Handler for copying a temp file to it's final location.
	"""
	def __init__(self, realFilePath, tempFilePath):
		self.realFilePath = realFilePath
		self.tempFilePath = tempFilePath

	def Check(self):
		"""
		Check the temp file to see if it differs from the output file, then copy if they don't match.
		"""
		outDirPath = os.path.dirname(self.realFilePath)

		# Create the output directory if it doesn't exist.
		if not os.access(outDirPath, os.F_OK):
			os.makedirs(outDirPath)

		# Open the input file and get a hash of its data.
		with open(self.tempFilePath, "rb") as inputFile:
			inputFileData = inputFile.read()
			inputHash = hashlib.md5()

			inputHash.update(inputFileData)

			inputHash = inputHash.hexdigest()

		if os.access(self.realFilePath, os.F_OK):
			# Open the output file and get a hash of its data.
			with open(self.realFilePath, "rb") as outputFile:
				outputFileData = outputFile.read()
				outputHash = hashlib.md5()

				outputHash.update(outputFileData)

				outputHash = outputHash.hexdigest()

		else:
			# The output file doesn't exist, so use an empty string to stand in for the hash.
			outputHash = ""

		# Do a consistency check using the MD5 hashes of the input and output files to determine if we
		# need to copy the data to the output file.
		if inputHash != outputHash:
			log.Build("[WRITING] {}".format(self.realFilePath))

			with open(self.realFilePath, "wb") as outputFile:
				outputFile.write(inputFileData)

		else:
			log.Build("[UP-TO-DATE] {}".format(self.realFilePath))

		os.remove(self.tempFilePath)


def _createBuildTarget(generator):
	return generator.projectData.toolchainName  \
		, generator.projectData.architectureName \
		, _fixConfigName(generator.projectData.targetName)


def _getToolchainArchPair(target):
	return target[0], target[1]


def _getBuildTargets(generators):
	global PLATFORM_HANDLERS

	buildTargets = set()

	for gen in generators:
		target = _createBuildTarget(gen)
		toolchainArch = _getToolchainArchPair(target)

		# Only add the generator's platform if we have a handler registered for it.
		if toolchainArch in PLATFORM_HANDLERS:
			buildTargets.add(target)

	return sorted(buildTargets)


def _buildProjectHierarchy(buildTargets, generators):
	rootProject = VsProject(None, "", VsProjectType.Root)
	buildAllProject = VsProject("(BUILD_ALL)", "", VsProjectType.Standard)
	regenProject = VsProject("(REGENERATE_SOLUTION)", "", VsProjectType.Standard)

	# Set the default project special types so they can be identified.
	buildAllProject.subType = VsProjectSubType.BuildAll
	regenProject.subType = VsProjectSubType.Regen

	# The default projects can be used with all build targets.
	for target in buildTargets:
		buildAllProject.MergeProjectData(target, None)
		regenProject.MergeProjectData(target, None)

	# Add the default projects to the hierarchy.
	rootProject.children.update({
		buildAllProject.name: buildAllProject,
		regenProject.name: regenProject,
	})

	# Parse the data from each project generator.
	for gen in generators:
		target = _createBuildTarget(gen)
		parent = rootProject

		# Find the appropriate parent project if this project is part of a group.
		for segment in gen.groupSegments:
			# If the current segment in the group is not represented in the current parent's child project list yet,
			# create it and insert it.
			if segment not in parent.children:
				parent.children.update({ segment: VsProject(segment, os.path.join(parent.relFilePath, segment), VsProjectType.Filter) })

			parent = parent.children[segment]

		projName = gen.projectData.name

		if projName not in parent.children:
			# The current project does not exist yet, so create it and map it as a child to the parent project.
			proj = VsProject(projName, parent.relFilePath, VsProjectType.Standard)
			parent.children.update({ projName: proj })

		else:
			# Get the existing project entry from the parent.
			proj = parent.children[projName]

		# Merge the generator's platform data into the project.
		proj.MergeProjectData(target, gen)


	return rootProject


def _writeSolutionFile(buildTargets, rootProject, outputRootPath, solutionName, vsVersion):
	global FILE_FORMAT_VERSION_INFO
	global PLATFORM_HANDLERS

	def GetVsBuildTarget(target): # pylint: disable=missing-docstring
		toolchainArch = _getToolchainArchPair(target)
		handler = PLATFORM_HANDLERS[toolchainArch]
		vsTarget = "{}|{}".format(target[2], handler.GetVisualStudioPlatformName())
		return vsTarget

	class SolutionWriter(object): # pylint: disable=missing-docstring
		def __init__(self, fileHandle):
			self.fileHandle = fileHandle
			self.indentation = 0

		def Line(self, text): # pylint: disable=missing-docstring
			self.fileHandle.write("{}{}\r\n".format("\t" * self.indentation, text))

		@contextlib.contextmanager
		def Section(self, sectionName, headerSuffix): # pylint: disable=missing-docstring
			self.Line("{}{}".format(sectionName, headerSuffix))

			self.indentation += 1

			try:
				yield

			finally:
				self.indentation -= 1

				self.Line("End{}".format(sectionName))

	realFilePath = os.path.join(outputRootPath, "{}.sln".format(solutionName))
	tmpFd, tempFilePath = tempfile.mkstemp(prefix="vs_sln_")

	# Close the file since it needs to be re-opened with a specific encoding.
	os.close(tmpFd)

	vsFileInfo = FILE_FORMAT_VERSION_INFO[vsVersion]

	# Visual Studio solution files need to be UTF-8 with the byte order marker because Visual Studio is VERY picky
	# about these files. If ANYTHING is missing or not formatted properly, the Visual Studio version selector may
	# not open the right version or Visual Studio itself may refuse to even attempt to load the file.
	with codecs.open(tempFilePath, "w", "utf-8-sig") as f:
		writer = SolutionWriter(f)

		writer.Line("") # Required empty line.
		writer.Line("Microsoft Visual Studio Solution File, Format Version {}".format(vsFileInfo.fileVersion))
		writer.Line("# Visual Studio {}".format(vsFileInfo.versionId))

		flatProjectList = []
		projectStack = [rootProject]

		# Build a flat list of all projects and filters.
		while projectStack:
			project = projectStack.pop(0)

			# Add each child project to the stack.
			for projKey in sorted(list(project.children)):
				childProject = project.children[projKey]

				flatProjectList.append(childProject)
				projectStack.append(childProject)

		# Write out the initial setup data for each project and filter.
		for project in flatProjectList:
			projectFilePath = os.path.join(project.relFilePath, project.name)
			data = "(\"{}\") = \"{}\", \"{}.vcxproj\", \"{}\"".format(project.slnTypeGuid, project.name, projectFilePath, project.guid)

			with writer.Section("Project", data):
				pass

		# Begin setting the global configuration data.
		with writer.Section("Global", ""):

			# Write out the build targets supported by this solution.
			with writer.Section("GlobalSection", "(SolutionConfigurationPlatforms) = preSolution"):
				for target in buildTargets:
					vsTarget = GetVsBuildTarget(target)

					writer.Line("{0} = {0}".format(vsTarget))

			# Write out the supported project-to-target mappings.
			with writer.Section("GlobalSection", "(ProjectConfigurationPlatforms) = postSolution"):
				for project in flatProjectList:
					# Only standard projects should be listed here.
					if project.projType == VsProjectType.Standard:
						for target in sorted(project.supportedTargets):
							# Only write out for the current target if it's a supported target.
							if target in buildTargets:
								vsTarget = GetVsBuildTarget(target)
								writer.Line("{0}.{1}.ActiveCfg = {1}".format(project.guid, vsTarget))

								# Only enable the BuildAll project.  This will make sure the global build command only
								# builds this project and none of the others (which can still be selectively built).
								if project.subType == VsProjectSubType.BuildAll:
									writer.Line("{0}.{1}.Build.0 = {1}".format(project.guid, vsTarget))

			# Write out any standalone solution properties.
			with writer.Section("GlobalSection", "(SolutionProperties) = preSolution"):
				writer.Line("HideSolutionNode = FALSE")

			# Write out the mapping that describe the solution hierarchy.
			with writer.Section("GlobalSection", "(NestedProjects) = preSolution"):
				for parentProject in flatProjectList:
					for childProject in parentProject.children:
						writer.Line("{} = {}".format(childProject.guid, parentProject.guid))

	# Transfer the temp file to the final output location.
	VsFileProxy(realFilePath, tempFilePath).Check()


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
	if not generators:
		log.Error("No projects available, cannot generate solution")
		return

	log.Build("Creating project files for Visual Studio {}".format(vsVersion))

	buildTargets = _getBuildTargets(generators)
	rootProject = _buildProjectHierarchy(buildTargets, generators)

	_writeSolutionFile(buildTargets, rootProject, outputRootPath, solutionName, vsVersion)
