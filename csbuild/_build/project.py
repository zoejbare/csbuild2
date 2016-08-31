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
.. module:: project
	:synopsis: A project that's been finalized for building.
		Unlike ProjectPlan, Project is a completely finalized class specialized on a single toolchain, and is ready to build
"""

from __future__ import unicode_literals, division, print_function

import os
import fnmatch
import collections

from .. import log
from .._utils import ordered_set, shared_globals, StrType, BytesType, PlatformString
from .._utils.decorators import TypeChecked
from .._utils.string_abc import String
from .._build import input_file
from ..toolchain.toolchain import Toolchain

class UserData(object):
	def __init__(self, dataDict):
		self.dataDict = dataDict

	def __getattr__(self, item):
		return object.__getattribute__(self, "dataDict")[item]

class Project(object):
	"""
	A finalized, concrete project

	:param name: The project's name. Must be unique.
	:type name: String
	:param workingDirectory: The location on disk containing the project's files, which should be examined to collect source files.
		If autoDiscoverSourceFiles is False, this parameter is ignored.
	:type workingDirectory: String
	:param depends: List of names of other prjects this one depends on.
	:type depends: list(String)
	:param priority: Priority in the build queue, used to cause this project to get built first in its dependency ordering. Higher number means higher priority.
	:type priority: int
	:param ignoreDependencyOrdering: Treat priority as a global value and use priority to raise this project above, or lower it below, the dependency order
	:type ignoreDependencyOrdering: bool
	:param autoDiscoverSourceFiles: If False, do not automatically search the working directory for files, but instead only build files that are manually added.
	:type autoDiscoverSourceFiles: bool
	:param projectSettings: Finalized settings from the project plan
	:type projectSettings: dict
	:param toolchainName: Toolchain name
	:type toolchainName: str, bytes
	:param archName: Architecture name
	:type archName: str, bytes
	:param targetName: Target name
	:type targetName: str, bytes
	"""
	def __init__(self, name, workingDirectory, depends, priority, ignoreDependencyOrdering, autoDiscoverSourceFiles, projectSettings, toolchainName, archName, targetName):
		self.name = name
		self.workingDirectory = workingDirectory
		self.dependencyNames = depends
		self.dependencies = []
		self.priority = priority
		self.ignoreDependencyOrdering = ignoreDependencyOrdering
		self.autoDiscoverSourceFiles = autoDiscoverSourceFiles

		self.toolchainName = toolchainName
		self.architectureName = archName
		self.targetName = targetName

		log.Build("Preparing build tasks for {}", self)

		#: type: list[Tool]
		self.tools = projectSettings["tools"]

		self.toolchain = Toolchain(projectSettings, *self.tools)

		self.userData = UserData(projectSettings.get("_userData", {}))

		def _convertSet(toConvert):
			ret = toConvert.__class__()
			for item in toConvert:
				ret.add(_convertItem(item))
			return ret

		def _convertDict(toConvert):
			for key, val in toConvert.items():
				toConvert[key] = _convertItem(val)
			return toConvert

		def _convertList(toConvert):
			for i, item in enumerate(toConvert):
				toConvert[i] = _convertItem(item)
			return toConvert

		def _convertItem(toConvert):
			if isinstance(toConvert, list):
				return _convertList(toConvert)
			elif isinstance(toConvert, dict) or isinstance(toConvert, collections.OrderedDict):
				return _convertDict(toConvert)
			elif isinstance(toConvert, set) or isinstance(toConvert, ordered_set.OrderedSet):
				return _convertSet(toConvert)
			elif isinstance(toConvert, StrType) or isinstance(toConvert, BytesType):
				return self.FormatMacro(toConvert)
			else:
				return toConvert

		# We set self.settings here because _convertItem calls FormatMacro and FormatMacro uses self.settings
		self.settings = projectSettings
		self.settings = _convertItem(projectSettings)

		self.projectType = projectSettings["projectType"]

		#: type: set[str]
		self.extraDirs = projectSettings.get("extraDirs", set())
		#: type: set[str]
		self.excludeDirs = projectSettings.get("excludeDirs", set())
		#: type: set[str]
		self.excludeFiles = projectSettings.get("excludeFiles", set())
		#: type: set[str]
		self.sourceFiles = projectSettings.get("sourceFiles", set())

		#: type: str
		self.intermediateDir = projectSettings.get("intermediateDir", os.path.join(self.workingDirectory, "intermediate"))
		#: type: str
		self.outputDir = projectSettings.get("outputDir", os.path.join(self.workingDirectory, "out"))
		#: type: str
		self.csbuildDir = os.path.join(self.intermediateDir, ".csbuild")

		if not os.path.exists(self.csbuildDir):
			os.makedirs(self.csbuildDir)

		#: type: str
		self.artifactsFileName = os.path.join(
			self.csbuildDir,
			"{}_{}_{}_{}.artifacts".format(
				self.name,
				self.toolchainName,
				self.architectureName,
				self.targetName
			)
		)

		if os.path.exists(self.artifactsFileName):
			with open(self.artifactsFileName, "r") as f:
				self.lastRunArtifacts = ordered_set.OrderedSet(f.read().splitlines())
		else:
			self.lastRunArtifacts = ordered_set.OrderedSet()

		self.artifacts = ordered_set.OrderedSet()
		self.artifactsFile = open(
			self.artifactsFileName,
			"w"
		)

		self.outputName = projectSettings.get("outputName", self.name)

		if not os.path.exists(self.intermediateDir):
			os.makedirs(self.intermediateDir)
		if not os.path.exists(self.outputDir):
			os.makedirs(self.outputDir)
		if not os.path.exists(self.csbuildDir):
			os.makedirs(self.csbuildDir)

		#: type: dict[str, ordered_set.OrderedSet]
		self.inputFiles = {}

		self.RediscoverFiles()

	def __repr__(self):
		return "{} ({}/{}/{})".format(self.name, self.toolchainName, self.architectureName, self.targetName)

	def FormatMacro(self, toConvert):
		# TODO: This could be optimized:
		# Make a proxy class that gets items from the list of valid items
		# and convert them as we come across them, using memoization to avoid redundant
		# conversions. If we do that, we could do each string in one pass.
		if "{" in toConvert:
			prev = ""
			while toConvert != prev:
				log.Info("Formatting {}", toConvert)
				prev = toConvert
				toConvert = toConvert.format(
					name=self.name,
					workingDirectory=self.workingDirectory,
					dependencyNames=self.dependencyNames,
					priority=self.priority,
					ignoreDependencyOrdering=self.ignoreDependencyOrdering,
					autoDiscoverSourceFiles=self.autoDiscoverSourceFiles,
					settings=self.settings,
					toolchainName=self.toolchainName,
					architectureName=self.architectureName,
					targetName=self.targetName,
					toolchain=self.toolchain,
					userData=self.userData,
					**self.settings
				)
				log.Info("  => {}", toConvert)
		return PlatformString(toConvert)

	def ResolveDependencies(self):
		"""
		Called after shared_globals.projectMap is filled out, this will populate the dependencies map.
		"""
		for name in self.dependencyNames:
			self.dependencies.append(shared_globals.projectMap[self.toolchainName][self.architectureName][self.targetName][name])

	@TypeChecked(artifact=String)
	def AddArtifact(self, artifact):
		"""
		Add an artifact - i.e., a file created by the build
		:param artifact: absolute path to the file
		:type artifact: str
		:return:
		"""
		if artifact not in self.artifacts:
			self.artifacts.add(artifact)
			self.artifactsFile.write(artifact)
			self.artifactsFile.write("\n")

	def RediscoverFiles(self):
		"""
		(Re)-Run source file discovery.
		If autoDiscoverSourceFiles is enabled, this will recursively search the working directory and all extra directories
		to find source files.
		Manually specified source files are then added to this list.
		Note that even if autoDiscoverSourceFiles is disabled, this must be called again in order to update the source
		file list after a preBuildStep.
		"""
		log.Info("Discovering files for {}...", self)
		self.inputFiles = {}

		if self.autoDiscoverSourceFiles:
			extensionList = self.toolchain.GetSearchExtensions()

			for sourceDir in ordered_set.OrderedSet([self.workingDirectory]) | self.extraDirs:
				log.Build("Collecting files from {}", sourceDir)
				for root, _, filenames in os.walk(sourceDir):
					absroot = os.path.abspath(root)
					if absroot in self.excludeDirs:
						if absroot != self.csbuildDir:
							log.Info("Skipping dir {}", root)
						continue
					if ".csbuild" in root \
							or root.startswith(self.intermediateDir) \
							or (root.startswith(self.outputDir) and self.outputDir != self.workingDirectory):
						continue
					if absroot == self.csbuildDir or absroot.startswith(self.csbuildDir):
						continue
					bFound = False
					for testDir in self.excludeDirs:
						if absroot.startswith(testDir):
							bFound = True
							continue
					if bFound:
						if not absroot.startswith(self.csbuildDir):
							log.Info("Skipping directory {}", root)
						continue
					log.Info("Looking in directory {}", root)
					for extension in extensionList:
						log.Info("Checking for {}", extension)
						self.inputFiles.setdefault(extension, ordered_set.OrderedSet()).update(
							[
								input_file.InputFile(
									os.path.join(absroot, filename)
								) for filename in fnmatch.filter(filenames, "*{}".format(extension))
								if os.path.join(absroot, filename) not in self.lastRunArtifacts
							]
						)

		for filename in self.sourceFiles:
			extension = os.path.splitext(filename)[1]
			self.inputFiles.setdefault(extension, ordered_set.OrderedSet()).add(filename)
		log.Info("Discovered {}", self.inputFiles)
