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
.. package:: _build
	:synopsis: Logic related to actually running a build
"""

# Import this stuff to appease pylint
from __future__ import unicode_literals, division, print_function

import shutil

import csbuild
import argparse
import os
import sys
import imp
import math
import multiprocessing
import time
import encodings
import importlib
import pkgutil
import threading

from . import project_plan, project, input_file
from .. import log, commands, perf_timer
from .._utils import system, shared_globals, thread_pool, terminfo, ordered_set, FormatTime, queue
from .._utils.decorators import TypeChecked
from .._utils.string_abc import String

if sys.version_info[0] >= 3:
	_typeType = type
	_classType = type
else:
	import types
	# pylint: disable=invalid-name
	_typeType = types.TypeType
	_classType = types.ClassType

class _dummy(object):
	def __setattr__(self, key, value):
		pass
	def __getattribute__(self, item):
		return ""

class MultiBreak(Exception):
	"""
	Simple exception type to quickly break out of deeply nested loops.
	"""
	pass

_runningBuilds = 0

def _canRun(tool):
	return tool.maxParallel <= 0 or tool.curParallel < tool.maxParallel

def _enqueueBuild(buildProject, tool, buildInput, pool, projectList, outputExtension):
	with perf_timer.PerfTimer("Enqueuing build tasks"):
		global _runningBuilds
		_runningBuilds += 1
		tool.curParallel += 1

		buildProject.toolchain.CreateReachability(tool)

		if buildInput is None:
			buildProject.toolchain.DeactivateTool(tool)
			log.Info("Enqueuing null-input build for {} for project {}", tool.__name__, buildProject)
			pool.AddTask(
				(_logThenRun, tool.Run, tool, buildProject.toolchain, buildProject, None),
				(_buildFinished, pool, projectList, buildProject, tool, None, None)
			)
		elif isinstance(buildInput, input_file.InputFile):
			buildInput.AddUsedTool(tool)
			log.Info("Enqueuing build for {} using {} for project {}", buildInput, tool.__name__, buildProject)
			pool.AddTask(
				(_logThenRun, tool.Run, tool, buildProject.toolchain, buildProject, buildInput),
				(_buildFinished, pool, projectList, buildProject, tool, outputExtension, [buildInput])
			)
		else:
			for inputFile in buildInput:
				inputFile.AddUsedTool(tool)

			log.Info("Enqueuing multi-build task for {} using {} for project {}", buildProject, buildInput, tool.__name__, buildProject)
			pool.AddTask(
				(_logThenRun, tool.RunGroup, tool, buildProject.toolchain, buildProject, buildInput),
				(_buildFinished, pool, projectList, buildProject, tool, None, buildInput)
			)

def _dependenciesMet(buildProject, tool):
	with perf_timer.PerfTimer("Dependency checks"):
		log.Info("Checking if we can enqueue a new build for tool {} for project {}", tool.__name__, buildProject)
		for dependProject in buildProject.dependencies:
			for dependency in tool.crossProjectDependencies:
				if dependProject.toolchain.IsOutputActive(dependency):
					return False

		for dependency in tool.dependencies:
			if buildProject.toolchain.IsOutputActive(dependency):
				return False
		return True

def _getGroupInputFiles(buildProject, tool):
	with perf_timer.PerfTimer("Collecting group inputs"):
		fileList = ordered_set.OrderedSet()
		for inputFile in tool.inputGroups:
			log.Info("Checking if all builds for {} are done yet", inputFile)
			if buildProject.toolchain.IsOutputActive(inputFile):
				log.Info("Extension {} is still active, can't build yet.", inputFile)
				return None
			log.Info("{} is ok to build.", inputFile)
			fileList.update([x for x in buildProject.inputFiles.get(inputFile, []) if not x.WasToolUsed(tool)])
		return fileList

def _logThenRun(function, buildTool, buildToolchain, buildProject, inputFiles):
	with perf_timer.PerfTimer("Tool execution"):
		log.Build("Processing {} with {} for project {}", "null-input build" if inputFiles is None else inputFiles, buildTool.__name__, buildProject)
		with buildToolchain.Use(buildTool):
			return function(buildToolchain, buildProject, inputFiles)

def _checkDependenciesPreBuild(checkProject, tool, dependencies):
	with perf_timer.PerfTimer("Dependency checks"):
		log.Info("Checking if we can enqueue a new build for tool {} for project {}", checkProject, tool.__name__, checkProject)
		for dependency in dependencies:
			for tool in checkProject.toolchain.GetAllTools():
				if tool.inputFiles is None:
					extensionSet = tool.inputGroups
				else:
					extensionSet = tool.inputFiles | tool.inputGroups
				hasExtension = False
				for dependentExtension in extensionSet:
					if checkProject.inputFiles.get(dependentExtension):
						hasExtension = True
						break
				if hasExtension and checkProject.toolchain.CanCreateOutput(tool, dependency):
					return False
		return True

@TypeChecked(
	pool=thread_pool.ThreadPool,
	projectList=list,
	buildProject=project.Project,
	toolUsed=(_classType, _typeType),
	inputExtension=(String, type(None)),
	inputFiles=(list, ordered_set.OrderedSet, type(None)),
	outputFiles=(String, tuple)
)
def _buildFinished(pool, projectList, buildProject, toolUsed, inputExtension, inputFiles, outputFiles):
	"""
	Build has finished, enqueue another one.

	:param pool: thread pool
	:type pool: thread_pool.ThreadPool
	:param projectList: list of all projects
	:type projectList: list[project.Project]
	:param buildProject: project
	:type buildProject: project.Project
	:param toolUsed: tool used to build it
	:type toolUsed: type
	:param inputExtension: Extension taken as input
	:type inputExtension: str, bytes
	:param inputFiles: inputs used for this build
	:type inputFiles: list[input_file.InputFile]
	:param outputFiles: output generated by the build
	:type outputFiles: tuple, str, bytes
	"""
	with perf_timer.PerfTimer("Post-build processing"):
		toolUsed.curParallel -= 1
		global _runningBuilds
		_runningBuilds -= 1
		buildProject.toolchain.ReleaseReachability(toolUsed)

		if buildProject.toolchain.IsToolActive(toolUsed):
			done = True

			remainingInputs = [x for x in buildProject.inputFiles.get(inputExtension, []) if not x.WasToolUsed(toolUsed)]

			if not remainingInputs:
				# Technically this will happen before the tool is finished building, so we need the
				# above guard to keep from doing it twice and tossing up exceptions.
				# The important thing here is that this will stop us from doing a lot of logic further
				# down to see if we can build for tools that we know we can't build for.
				if toolUsed.inputFiles is not None:
					for inputFile in toolUsed.inputFiles:
						if buildProject.toolchain.IsOutputActive(inputFile):
							done = False
							break
				if done:
					for inputFile in toolUsed.inputGroups:
						if buildProject.toolchain.IsOutputActive(inputFile):
							done = False
							break
				if done:
					log.Info("Tool {} has finished building for project {}", toolUsed.__name__, buildProject)
					buildProject.toolchain.DeactivateTool(toolUsed)

		if not isinstance(outputFiles, tuple):
			outputFiles = (outputFiles, )
		for outputFile in outputFiles:
			buildProject.AddArtifact(outputFile)
			log.Info(
				"Finished building {} => {}",
				 "null-input for {} for project {}".format(toolUsed.__name__, buildProject) if inputFiles is None
					else [os.path.basename(f.filename) for f in inputFiles],
				os.path.basename(outputFile)
			)

			outputExtension = os.path.splitext(outputFile)[1]

			if inputExtension == outputExtension:
				newInput = input_file.InputFile(outputFile, inputFiles)
			else:
				newInput = input_file.InputFile(outputFile)

			buildProject.inputFiles.setdefault(outputExtension, ordered_set.OrderedSet()).add(newInput)

			# Enqueue this file immediately in any tools that take it as a single input, unless they're marked to delay.
			tools = buildProject.toolchain.GetToolsFor(outputExtension)
			for tool in tools:
				if not buildProject.toolchain.IsToolActive(tool):
					continue

				if not _canRun(tool):
					continue

				if not _dependenciesMet(buildProject, tool):
					continue

				if newInput.WasToolUsed(tool):
					continue

				_enqueueBuild(buildProject, tool, newInput, pool, projectList, outputExtension)

			isActive = buildProject.toolchain.IsOutputActive(outputExtension)
			log.Info("Checking if {} is still active... {}", outputExtension, "yes" if isActive else "no")

			# If this was the last file being built of its extension, check whether we can pass it and maybe others to relevant group input tools
			if not isActive:
				tools = buildProject.toolchain.GetActiveTools()
				for tool in tools:
					if not _canRun(tool):
						continue

					if not tool.inputGroups:
						continue

					if not _dependenciesMet(buildProject, tool):
						continue

					# Check for group inputs that have been freed and queue up if all are free
					fileList = _getGroupInputFiles(buildProject, tool)

					if not fileList:
						continue

					_enqueueBuild(buildProject, tool, fileList, pool, projectList, None)

				# Check to see if we've freed up any pending builds in other projects as well
				for proj in projectList:
					tools = proj.toolchain.GetActiveTools()
					for tool in tools:
						if not _dependenciesMet(proj, tool):
							continue

						if tool.inputFiles is None:
							if not _canRun(tool):
								continue

							_enqueueBuild(proj, tool, None, pool, projectList, None)
						else:
							for inputExtension in tool.inputFiles:
								for projectInput in [x for x in proj.inputFiles.get(inputExtension, []) if not x.WasToolUsed(tool)]:
									if not _canRun(tool):
										break
									_enqueueBuild(proj, tool, projectInput, pool, projectList, inputExtension)

						if not _canRun(tool):
							continue

						fileList = _getGroupInputFiles(proj, tool)

						if not fileList:
							continue

						_enqueueBuild(proj, tool, fileList, pool, projectList, None)

		if _runningBuilds == 0:
			# We have no builds running and finishing this build did not spawn a new one
			# Time to exit.
			pool.Stop()


@TypeChecked(numThreads=int, projectBuildList=list, _return=int)
def _build(numThreads, projectBuildList):
	"""
	Run a build.

	:param numThreads: Number of threads
	:type numThreads: int
	:param projectBuildList: List of projects
	:type projectBuildList: list[project.Project]
	:return: Number of failures
	:rtype: int
	"""
	with perf_timer.PerfTimer("Enqueuing initial builds"):
		log.Info("Starting builds")
		buildStart = time.time()
		global _runningBuilds
		callbackQueue = queue.Queue()
		log.SetCallbackQueue(callbackQueue)
		pool = thread_pool.ThreadPool(numThreads, callbackQueue)
		queuedSomething = False
		for buildProject in projectBuildList:
			for tool in buildProject.toolchain.GetAllTools():
				tool.curParallel = 0

		failures = 0
		pool.Start()

		for buildProject in projectBuildList:
			for extension, fileList in [(None, None)] + list(buildProject.inputFiles.items()):
				log.Info("Enqueuing tasks for extension {}", extension)
				tools = buildProject.toolchain.GetToolsFor(extension)
				for tool in tools:
					try:
						# For the first pass, if ANY tool in the toolchain is capable of producing this output
						# anywhere in its path, AND any inputs exist for that tool, we won't queue up a build
						for dependProject in buildProject.dependencies:
							if not _checkDependenciesPreBuild(dependProject, tool, tool.crossProjectDependencies):
								raise MultiBreak

						if not _checkDependenciesPreBuild(buildProject, tool, tool.dependencies):
							raise MultiBreak

					except MultiBreak:
						continue

					if fileList is None and extension is None:
						if not _canRun(tool):
							continue

						if not buildProject.toolchain.IsToolActive(tool):
							continue

						_enqueueBuild(buildProject, tool, None, pool, projectBuildList, None)
						queuedSomething = True
					else:
						log.Info("Looking at files {}", fileList)
						for inputFile in fileList:
							if not _canRun(tool):
								break
							_enqueueBuild(buildProject, tool, inputFile, pool, projectBuildList, extension)
							queuedSomething = True

			tools = buildProject.toolchain.GetAllTools()
			log.Info("Checking for group inputs we can run already")
			for tool in tools:
				if not _canRun(tool):
					continue

				if not tool.inputGroups:
					continue

				try:
					for dependProject in buildProject.dependencies:
						if not _checkDependenciesPreBuild(dependProject, tool, tool.crossProjectDependencies):
							raise MultiBreak()

					if not _checkDependenciesPreBuild(buildProject, tool, tool.dependencies):
						raise MultiBreak()

				except MultiBreak:
					continue

				fileList = _getGroupInputFiles(buildProject, tool)

				if not fileList:
					break

				_enqueueBuild(buildProject, tool, fileList, pool, projectBuildList, None)
				queuedSomething = True

	if not queuedSomething:
		log.Build("Nothing to build.")
		pool.Stop()
		return 0

	with perf_timer.PerfTimer("Running builds"):
		callbackQueue.ThreadInit()
		while True:
			callback = callbackQueue.GetBlocking()
			if callback is thread_pool.ThreadPool.exitEvent:
				break

			toReraise = None
			try:
				callback()
			except thread_pool.ThreadedTaskException as e:
				_runningBuilds -= 1
				if _runningBuilds == 0:
					# We have no builds running and finishing this build did not spawn a new one
					# Time to exit.
					pool.Stop()
				failures += 1
				try:
					toReraise = e
				except csbuild.BuildFailureException as buildExc:
					log.Error(repr(buildExc))
				except:
					pool.Abort()
					raise
			except:
				pool.Abort()
				raise

			if toReraise is not None:
				toReraise.Reraise()

	for buildProject in projectBuildList:
		if buildProject.toolchain.HasAnyReachability():
			log.Error("Project {} did not finish building (likely a toolchain flow error)", buildProject)
			failures += 1

	log.Build("Build finished. Total build time: {}", FormatTime(time.time() - buildStart))
	return failures

@TypeChecked(projectCleanList=list)
def _clean(projectCleanList):
	"""
	Clean the files built in previous builds.

	:param projectCleanList: List of projects
	:type projectCleanList: list[project.Project]
	:return:
	"""
	with perf_timer.PerfTimer("Cleaning build artifacts"):
		for cleanProject in projectCleanList:
			for artifact in cleanProject.lastRunArtifacts:
				if os.path.exists(artifact):
					log.Build("Removing {}", artifact)
					os.remove(artifact)

			cleanProject.artifactsFile.flush()
			os.fsync(cleanProject.artifactsFile.fileno())
			cleanProject.artifactsFile.close()

			system.SyncDir(os.path.dirname(cleanProject.artifactsFileName))

			cleanProject.artifactsFile = None

			log.Build("Removing {}", cleanProject.artifactsFileName)
			os.remove(cleanProject.artifactsFileName)

			def _rmDirIfPossible(dirname):
				if os.path.exists(dirname):
					containsOnlyDirs = True
					for _, _, files in os.walk(dirname):
						if files:
							containsOnlyDirs = False
							break
					if containsOnlyDirs:
						log.Build("Removing {}", dirname)
						#If it contains only directories and no files, remove everything
						shutil.rmtree(dirname)
						#Then if its parent directory is empty, remove it and any dirs above it that are also empty
						parentDir = os.path.dirname(dirname)
						if not os.listdir(parentDir):
							os.removedirs(parentDir)

			_rmDirIfPossible(cleanProject.csbuildDir)
			_rmDirIfPossible(cleanProject.intermediateDir)
			_rmDirIfPossible(cleanProject.outputDir)


def _execfile(filename, glob, loc):
	with perf_timer.PerfTimer("Parsing Makefiles"):
		with open(filename, "r") as f:
			glob["__file__"] = filename
			# pylint: disable=exec-used
			exec(compile(f.read(), filename, "exec"), glob, loc)

def Run():
	"""
	Run the build! This is the main entry point for csbuild.
	"""
	with perf_timer.PerfTimer("Argument Parsing"):
		mainFileDir = ""
		mainFile = sys.modules['__main__'].__file__
		scriptFiles = []
		makefileDict = {}

		if mainFile is not None:
			mainFileDir = os.path.abspath(os.path.dirname(mainFile))
			if mainFileDir:
				os.chdir(mainFileDir)
				mainFile = os.path.basename(os.path.abspath(mainFile))
			else:
				mainFileDir = os.path.abspath(os.getcwd())
			scriptFiles.append(os.path.join(mainFileDir, mainFile))
			if "-h" in sys.argv or "--help" in sys.argv:
				_execfile(mainFile, makefileDict, makefileDict)
				shared_globals.runMode = csbuild.RunMode.Help
		else:
			log.Error("csbuild cannot be run from the interactive console.")
			system.Exit(1)

		epilog = "    ------------------------------------------------------------    \n\nProjects available in this makefile (listed in build order):\n\n"

		projtable = [[]]
		i = 1
		j = 0

		maxcols = min(math.floor(len(shared_globals.sortedProjects) / 4), 4)

		for proj in shared_globals.sortedProjects:
			projtable[j].append(proj.name)
			if i < maxcols:
				i += 1
			else:
				projtable.append([])
				i = 1
				j += 1

		if projtable:
			maxlens = [15] * len(projtable[0])
			for col in projtable:
				for subindex, item in enumerate(col):
					maxlens[subindex] = max(maxlens[subindex], len(item))

			for col in projtable:
				for subindex, item in enumerate(col):
					item = col[subindex]
					epilog += "  "
					epilog += item
					for _ in range(maxlens[subindex] - len(item)):
						epilog += " "
					epilog += "  "
				epilog += "\n"

		epilog += "\nTargets available in this makefile:\n\n"

		targtable = [[]]
		i = 1
		j = 0

		maxcols = min(math.floor(len(shared_globals.allTargets) / 4), 4)

		for targ in shared_globals.allTargets:
			targtable[j].append(targ)
			if i < maxcols:
				i += 1
			else:
				targtable.append([])
				i = 1
				j += 1

		if targtable:
			maxlens = [15] * len(targtable[0])
			for col in targtable:
				for subindex, item in enumerate(col):
					maxlens[subindex] = max(maxlens[subindex], len(item))

			for col in targtable:
				for subindex, item in enumerate(col):
					epilog += "  "
					epilog += item
					for _ in range(maxlens[subindex] - len(item)):
						epilog += " "
					epilog += "  "
				epilog += "\n"

		parser = shared_globals.parser = argparse.ArgumentParser(
			prog = mainFile, epilog = epilog, formatter_class = argparse.RawDescriptionHelpFormatter)

		parser.add_argument('--version', action = "store_true", help = "Print version information and exit")

		group = parser.add_mutually_exclusive_group()
		group.add_argument('-t', '--target', action='append', help = 'Target(s) for build', default=[])
		group.add_argument('--at', "--all-targets", action = "store_true", help = "Build all targets")

		parser.add_argument("-p", "--project",
							action="append", help = "Build only the specified project. May be specified multiple times.")

		group = parser.add_mutually_exclusive_group()
		group.add_argument('-c', '--clean', action = "store_true", help = 'Clean the target build')
		#group.add_argument('--install', action = "store_true", help = 'Install the target build')
		#group.add_argument('--install-headers', action = "store_true", help = 'Install only headers for the target build')
		#group.add_argument('--install-output', action = "store_true", help = 'Install only the output for the target build')
		group.add_argument('-r', '--rebuild', action = "store_true", help = 'Clean the target build and then build it')

		group2 = parser.add_mutually_exclusive_group()
		group2.add_argument('-v', '--verbose', action = "store_const", const = 0, dest = "verbosity",
			help = "Verbose. Enables additional INFO-level logging.", default = 1)
		group2.add_argument('-q', '--quiet', action = "store_const", const = 2, dest = "verbosity",
			help = "Quiet. Disables all logging except for WARN and ERROR.", default = 1)
		group2.add_argument('-qq', '--very-quiet', action = "store_const", const = 3, dest = "verbosity",
			help = "Very quiet. Disables all csb-specific logging.", default = 1)

		parser.add_argument("-j", "--jobs", action = "store", dest = "jobs", type = int, help = "Number of simultaneous build processes")

		#parser.add_argument("-g", "--gui", action = "store_true", dest = "gui", help = "Show GUI while building (experimental)")
		#parser.add_argument("--auto-close-gui", action = "store_true", help = "Automatically close the gui on build success (will stay open on failure)")
		#parser.add_argument("--profile", action="store_true", help="Collect detailed line-by-line profiling information on compile time. --gui option required to see this information.")

		parser.add_argument('--show-commands', help = "Show all commands sent to the system.", action = "store_true")
		parser.add_argument('--force-color', help = "Force color on or off.",
			action = "store", choices = ["on", "off"], default = None, const = "on", nargs = "?")
		parser.add_argument('--force-progress-bar', help = "Force progress bar on or off.",
			action = "store", choices = ["on", "off"], default = None, const = "on", nargs = "?")

		#parser.add_argument('--prefix', help = "install prefix (default /usr/local)", action = "store")
		#parser.add_argument('--libdir', help = "install location for libraries (default {prefix}/lib)", action = "store")
		#parser.add_argument('--incdir', help = "install prefix (default {prefix}/include)", action = "store")

		group = parser.add_mutually_exclusive_group()
		group.add_argument('-o', '--toolchain', help = "Toolchain to use for compiling.",
			default=[], action = "append")
		group.add_argument("--ao", '--all-toolchains', help="Build with all toolchains", action = "store_true")

		group = parser.add_mutually_exclusive_group()

		#for toolchainName, toolchainArchStrings in shared_globals.allToolchainArchStrings.items():
		#	archStringLong = "--" + toolchainArchStrings[0]
		#	archStringShort = "--" + toolchainArchStrings[1]
		#	parser.add_argument(archStringLong, archStringShort, help = "Architecture to compile for the {} toolchain.".format(toolchainName), action = "append")

		group.add_argument("-a", "--architecture", "--arch", help = 'Architecture to compile for each toolchain.', action = "append")
		group.add_argument("--aa", "--all-architectures", "--all-arch", action = "store_true", help = "Build all architectures supported by this toolchain")

		parser.add_argument("--stop-on-error", help = "Stop compilation after the first error is encountered.", action = "store_true")
		#parser.add_argument('--no-precompile', help = "Disable precompiling globally, affects all projects",
		#	action = "store_true")
		#parser.add_argument('--no-chunks', help = "Disable chunking globally, affects all projects",
		#	action = "store_true")
		#parser.add_argument('--dg', '--dependency-graph', help="Generate dependency graph", action="store_true")
		#parser.add_argument('--with-libs', help="Include linked libraries in dependency graph", action="store_true")

		parser.add_argument("--perf-report", help="Collect and show perf report at the end of execution", action="store_true")

		#parser.add_argument("-d", "--define", help = "Add defines to each project being built.", action = "append")

		# group = parser.add_argument_group("Solution generation", "Commands to generate a solution")
		# group.add_argument('--generate-solution', help = "Generate a solution file for use with the given IDE.",
		# 	choices = _shared_globals.allgenerators.keys(), action = "store")
		# group.add_argument('--solution-path',
		# 	help = "Path to output the solution file (default is ./Solutions/<solutiontype>)", action = "store",
		# 	default = "")
		# group.add_argument('--solution-name', help = "Name of solution output file (default is csbuild)", action = "store",
		# 	default = "csbuild")
		# group.add_argument('--solution-args', help = 'Arguments passed to the build script executed by the solution',
		# 	action = "store", default = "")

		#TODO: Additional args here
		# for chain in _shared_globals.alltoolchains.items():
		# 	chainInst = chain[1]()
		# 	argfuncs = set()
		# 	for tool in chainInst.tools.values():
		# 		if(
		# 			hasattr(tool.__class__, "AdditionalArgs")
		# 			and tool.__class__.AdditionalArgs != toolchain.compilerBase.AdditionalArgs
		# 			and tool.__class__.AdditionalArgs != toolchain.linkerBase.AdditionalArgs
		# 		):
		# 			argfuncs.add(tool.__class__.AdditionalArgs)
		#
		# 	if argfuncs:
		# 		group = parser.add_argument_group("Options for toolchain {}".format(chain[0]))
		# 		for func in argfuncs:
		# 			func(group)
		#
		# for gen in _shared_globals.allgenerators.items():
		# 	if gen[1].AdditionalArgs != project_generator.project_generator.AdditionalArgs:
		# 		group = parser.add_argument_group("Options for solution generator {}".format(gen[0]))
		# 		gen[1].AdditionalArgs(group)
		#
		# if _options:
		# 	group = parser.add_argument_group("Local makefile options")
		# 	for option in _options:
		# 		group.add_argument(*option[0], **option[1])

		args, remainder = parser.parse_known_args()
		args.remainder = remainder

		if args.version:
			shared_globals.runMode = csbuild.RunMode.Version

			print("CSBuild version {}".format(csbuild.__version__))
			print(csbuild.__copyright__)
			print("Code by {}".format(csbuild.__author__))
			print("Additional credits: {}\n".format(", ".join(csbuild.__credits__)))
			print("Maintainer: {} - {}".format(csbuild.__maintainer__, csbuild.__email__))
			return

		shared_globals.verbosity = args.verbosity
		shared_globals.showCommands = args.show_commands
		shared_globals.runPerfReport = args.perf_report

		if args.force_color:
			shared_globals.colorSupported = True
		else:
			shared_globals.colorSupported = terminfo.TermInfo.SupportsColor()

		if args.project:
			shared_globals.projectFilter = set(args.project)

		#Create the default targets...
		with csbuild.Target("release"):
			pass

		with csbuild.Target("debug"):
			pass

		with csbuild.Target("fastdebug"):
			pass

		_execfile(mainFile, makefileDict, makefileDict)

		if args.at:
			targetList = list(shared_globals.allTargets)
		elif args.target:
			targetList = args.target
		else:
			targetList = [project_plan.useDefault]

		if hasattr(args, "aa") and args.aa:
			archList = list(shared_globals.allArchitectures)
		elif hasattr(args, "architecture") and args.architecture:
			archList = args.architecture
		else:
			archList = [project_plan.useDefault]

		if args.ao:
			toolchainList = list(shared_globals.allToolchains)
		elif args.toolchain:
			toolchainList = args.toolchain
		else:
			toolchainList = [project_plan.useDefault]

		if not args.jobs:
			args.jobs = multiprocessing.cpu_count()

	projectBuildList = []

	preparationStart = time.time()

	with perf_timer.PerfTimer("Project plan execution"):
		for toolchainName in toolchainList:
			log.Info("Collecting projects for toolchain {}", toolchainName)
			for archName in archList:
				log.Info("-- {}", archName)
				for targetName in targetList:
					log.Info("---- {}", targetList)
					for plan in shared_globals.sortedProjects:
						log.Info("------ {}", plan.name)
						proj = plan.ExecutePlan(toolchainName, archName, targetName)
						if proj is None:
							continue
						shared_globals.projectMap.setdefault(proj.toolchainName, {}) \
							.setdefault(proj.architectureName, {}) \
							.setdefault(proj.targetName, {})[plan.name] = proj
						projectBuildList.append(proj)

	if not projectBuildList:
		log.Error("No projects were found supporting the requested architecture, toolchain, target, and platform combination")
		system.Exit(1)

	with perf_timer.PerfTimer("Dependency resolution"):
		for proj in projectBuildList:
			proj.ResolveDependencies()

	shared_globals.projectBuildList = projectBuildList

	totaltime = time.time() - preparationStart
	log.Build("Build preparation took {}".format(FormatTime(totaltime)))

	def _ignoreError(_):
		pass

	# Encodings are handled by trying to import a module and then failing to encode if they can't
	# Import all encodings and cache before releasing the import lock to make sure this can be done in a safe way
	for _, name, _ in pkgutil.walk_packages(encodings.__path__, onerror=_ignoreError):
		try:
			module = importlib.import_module('encodings.' + name)
			sys.modules[name] = module
		except:
			continue

	# Note:
	# The reason for this line of code is that the import lock, in the way that CSBuild operates, prevents
	# us from being able to call subprocess.Popen() or any other process execution function other than os.popen().
	# This exists to prevent multiple threads from importing at the same time, so... Within csbuild, never import
	# within any thread but the main thread. Any import statements used by threads should be in the module those
	# thread objects are defined in so they're completed in full on the main thread before that thread starts.
	#
	# After this point, the LOCK IS RELEASED. Importing is NO LONGER THREAD-SAFE. DON'T DO IT.

	#Past this point, disable importing entirely! Anything not already in the cache will raise an error on import
	class _importBlocker(object):
		"""
		This import hook prevents any module from being imported. Ever.
		"""
		#pylint: disable=invalid-name, unused-argument
		def find_module(self, fullname, path=None):
			"""
			Find the module loader, always returns self so the load_module will be called
			:param fullname: name of module
			:type fullname: str
			:param path: path to look in
			:type path: str
			:return: self
			:rtype: _importBlocker
			"""
			return self

		def load_module(self, name):
			"""
			Always raises import error
			:param name: name of module
			:type name: str
			:raises ImportError: always
			"""
			raise ImportError(
				"All modules must be imported prior to build starting. If you need local imports, "
				"make a global import first, or import in a pre-build step, or in plugin/tool static "
				"init, so that it is cached."
			)

	sys.meta_path.insert(0, _importBlocker())

	failures = 0

	if args.clean or args.rebuild:
		_clean(projectBuildList)

	if not args.clean or args.rebuild:
		if imp.lock_held():
			imp.release_lock()

		shared_globals.commandOutputThread = threading.Thread(target=commands.PrintStaggeredRealTimeOutput)
		shared_globals.commandOutputThread.start()
		failures = _build(args.jobs, projectBuildList)

	totaltime = time.time() - preparationStart
	log.Build("Build took {}".format(FormatTime(totaltime)))
	system.Exit(failures)
