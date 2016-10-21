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
.. package:: csbuild
	:synopsis: cross-platform c/c++ build system

.. moduleauthor:: Jaedyn K. Draper, Brandon M. Bare
.. attention:: To support CSBuild's operation, Python's import lock is DISABLED once CSBuild has started.
This should not be a problem for most makefiles, but if you do any threading within your makefile, take note:
anything that's imported and used by those threads should always be implemented on the main thread before that
thread's execution starts. Otherwise, CSBuild does not guarantee that the import will have completed
once that thread tries to use it. Long story short: Don't import modules within threads.
"""

from __future__ import unicode_literals, division, print_function

from . import perf_timer
from ._utils import StrType

with perf_timer.PerfTimer("csbuild module init"):
	import sys
	import signal
	import os
	import platform

	from collections import Callable

	if sys.version_info[0] >= 3:
		_typeType = type
		_classType = type
	else:
		import types
		# pylint: disable=invalid-name
		_typeType = types.TypeType
		_classType = types.ClassType

	from ._utils import shared_globals

	__author__ = "Jaedyn K. Draper, Brandon M. Bare"
	__copyright__ = 'Copyright (C) 2012-2014 Jaedyn K. Draper'
	__credits__ = ["Jaedyn K. Draper", "Brandon M. Bare", "Jeff Grills", "Randy Culley"]
	__license__ = 'MIT'

	__maintainer__ = "Jaedyn K. Draper"
	__email__ = "jaedyn.csbuild-contact@jaedyn.co"
	__status__ = "Development"

	_standardArchName = None

	try:
		with open(os.path.join(os.path.dirname(__file__), "version"), "r") as f:
			__version__ = f.read()
	except IOError:
		__version__ = "ERR_VERSION_FILE_MISSING"

	def _getElementFromToolchains(selfobj, allToolchains, item):
		funcs = set()
		hasNonFunc = False
		for tempToolchain in allToolchains:
			found = False
			for tool in tempToolchain.GetAllTools():
				if hasattr(tool, item):
					cls = None
					func = None
					for cls in tool.mro():
						if item in cls.__dict__:
							func = cls.__dict__[item]
							break

					if not (isinstance(func, Callable) or isinstance(func, property) or isinstance(func, staticmethod))\
							or isinstance(func, _classType) or isinstance(func, _typeType):
						hasNonFunc = True
					else:
						assert isinstance(func, staticmethod), "Only static tool methods can be called by makefiles"
					funcs.add((tempToolchain, cls, func))
					found = True
			if not found and hasattr(tempToolchain, item):
				funcs.add((tempToolchain, None, getattr(tempToolchain, item)))

		if not funcs:
			return object.__getattribute__(selfobj, item)

		if hasNonFunc:
			if len(funcs) != 0:
				raise AttributeError(
					"Toolchain attribute {} is ambiguous (exists on multiple tools). Try accessing on the class directly, or through toolchain.Tool(class)".format(item)
				)
			return funcs.pop()[2]

		def _runFuncs(*args, **kwargs):
			for tempToolchain, tool, func in funcs:
				if tool is None:
					func(*args, **kwargs)
				else:
					with tempToolchain.Use(tool):
						func.__get__(tool)(*args, **kwargs)

		return _runFuncs

	class Csbuild(object):
		"""
		Class that represents the actual csbuild module and replaces this module before anything can interact with it.
		This is done this way so context managers work - within a context manager, new methods have to become
		accessible, so there has to be a __getattr__ overload on the module. This is the only method by which
		such an overload is possible.

		Note that while this could be considered a "hack", it is a hack that's officially endorsed by Guido Van Rossum,
		and the import machinery goes out of its way to intentionally support this behavior.
		"""
		def __init__(self):
			class _toolchainMethodResolver(object):
				def __getattribute__(self, item):
					try:
						currentPlan.EnterContext(("toolchain", shared_globals.allToolchains))
						allToolchains = currentPlan.GetValuesInCurrentContexts("_tempToolchain")
						currentPlan.LeaveContext()
					except NameError:
						# Can and do get here before currentPlan is defined,
						# in which case we don't care because we're not ready to look there anyway,
						# so just go ahead and raise an error.
						return object.__getattribute__(self, item)
					return _getElementFromToolchains(self, allToolchains, item)

			self._resolver = _toolchainMethodResolver()
			self._module = sys.modules["csbuild"]

		def __getattr__(self, name):
			if hasattr(self._module, name):
				return getattr(self._module, name)

			if self._resolver is not None:
				previousResolver = self._resolver
				self._resolver = None
				if hasattr(previousResolver, name):
					ret = getattr(previousResolver, name)
					self._resolver = previousResolver
					return ret
				self._resolver = previousResolver

			return object.__getattribute__(self, name)


	sys.modules["csbuild"] = Csbuild()

	# pylint: disable=wrong-import-position
	from ._build.context_manager import ContextManager
	from ._build import project_plan, project, input_file

	from . import _build, log
	from ._utils import system
	from ._utils.string_abc import String
	from ._utils.decorators import TypeChecked
	from ._utils import ordered_set
	from ._utils import PlatformString

	from .toolchain import toolchain

	#Avoid double init if this module's imported twice for some reason
	#Test framework does this because run_unit_tests.py needs to import to get access to RunTests and logging
	#and then test discovery ends up importing it again and causing havok if this block happens twice
	if not hasattr(sys.modules["csbuild"], "currentPlan"):
		currentPlan = None # Set to None because ProjectPlan constructor needs to access it.
		currentPlan = project_plan.ProjectPlan("", "", [], 0, False, False)

	class ProjectType(object):
		"""
		'enum' representing the available project types.
		"""
		Application = 0
		SharedLibrary = 1
		StaticLibrary = 2

	class ScopeDef(object):
		"""
		'enum' representing the types of valid scopes
		"""
		Intermediate = "intermediate"
		Final = "final"
		Children = "children"
		All = "all"

	class StaticLinkMode( object ):
		"""
		'enum' representing the manner by which to handle static linking
		"""
		LinkLibs = 0
		LinkIntermediateObjects = 1

	class RunMode( object ):
		"""
		'enum' representing the way csbuild has been invoked
		"""
		Normal = 0
		Help = 1
		Version = 2
		GenerateSolution = 3
		QUALAP = 4

	class BuildFailureException(Exception):
		"""
		Notify a build failed.

		:param buildProject: Project being built
		:type buildProject: project.Project
		:param inputFile: The file being built
		:type inputFile: input_file.InputFile
		:param info: Extra details about the failure
		:type info: str
		"""
		@TypeChecked(buildProject=project.Project, inputFile=input_file.InputFile, info=String)
		def __init__(self, buildProject, inputFile, info=""):
			Exception.__init__(self)
			self.project = buildProject
			self.inputFile = inputFile
			self.info = info

		def __repr__(self):
			ret = "Build for {} in project {} failed!".format(
				self.inputFile.filename,
				self.project
			)
			if self.info:
				ret += "\n\t" + "\n\t".join(self.info.splitlines())
			return ret

	@TypeChecked(_return=int)
	def GetRunMode():
		"""
		Get information on how csbuild was invoked.

		:return: Run mode class member
		:rtype: int
		"""
		return shared_globals.runMode

	@TypeChecked(_return=StrType)
	def GetSystemArchitecture():
		"""
		Get the standard name for the architecture of the system currently running csbuild.

		:return: System standard architecture name.
		:rtype: str
		"""
		global _standardArchName
		if _standardArchName is None:
			def _is64Bit():
				return True if platform.architecture()[0].lower() == "64bit" else False

			x86Archs = ["x64", "x86_64", "amd64", "x86", "i386", "i686"]
			ppcArchs = ["powerpc", "ppc64"]
			machine = platform.machine().lower()

			# x86 compatible architectures
			if machine in x86Archs:
				_standardArchName = "x64" if _is64Bit() else "x86"

			# ppc architectures
			elif machine in ppcArchs:
				_standardArchName = "ppc64" if _is64Bit() else "ppc"

			# arm architectures
			elif machine.startswith("arm"):
				_standardArchName = "arm64" if _is64Bit() else "arm"

			# mips architectures
			elif machine.startswith("mips"):
				_standardArchName = "mips64" if _is64Bit() else "mips"

			# sparc architectures
			elif machine.startswith("sparc"):
				_standardArchName = "sparc64" if _is64Bit() else "sparc"

			# unknown
			else:
				# Architecture type is unknown, so use whatever was returned by platform.machine().
				_standardArchName = machine

		return _standardArchName

	@TypeChecked(name=String, projectType=int)
	def SetOutput(name, projectType=ProjectType.Application):
		"""
		Set the project output name and type

		:param name: Project name
		:type name: str, bytes
		:param projectType: Type of project
		:type projectType: ProjectType
		:return:
		"""
		currentPlan.SetValue("outputName", name)
		currentPlan.SetValue("projectType", projectType)

	@TypeChecked(name=String, defaultArchitecture=String)
	def RegisterToolchain(name, defaultArchitecture, *tools, **kwargs):
		"""
		Register a new toolchain to be used by the project for building

		:param name: The name of the toolchain, which will be used to reference it
		:type name: str, bytes
		:param defaultArchitecture: The default architecture to be used for this toolchain
		:type defaultArchitecture: str, bytes
		:param tools: List of tools to be used to make the toolchain.
		:type tools: class
		:param kwargs: Specify parameter `checkers` to include a dictionary of extension to csbuild.toolchain.CompileChecker instances
			These checkers will be used to determine whether or not to recompile files
		:type kwargs: any
		:return:
		"""
		shared_globals.allToolchains.add(name)

		checkers = kwargs.get("checkers", {})
		if checkers:
			currentPlan.UpdateDict("checkers", checkers)

		currentPlan.EnterContext(("toolchain", (name,)))
		currentPlan.SetValue("tools", ordered_set.OrderedSet(tools))
		currentPlan.SetValue("_tempToolchain", toolchain.Toolchain({}, *tools, runInit=False, checkers=checkers))
		currentPlan.defaultArchitectureMap[name] = defaultArchitecture
		currentPlan.LeaveContext()


		for tool in tools:
			if tool.supportedArchitectures is not None:
				shared_globals.allArchitectures.update(tool.supportedArchitectures)

	@TypeChecked(name=String)
	def RegisterToolchainGroup(name, *toolchains):
		"""
		Add a toolchain group, a single identifier to serve as an alias for multiple toolchains

		:param name: Name of the group
		:type name: str
		:param toolchains: Toolchain to alias
		:type toolchains: str
		:return:
		"""
		shared_globals.toolchainGroups[name] = set(toolchains)

	@TypeChecked(toolchainName=String)
	def SetDefaultToolchain(toolchainName):
		"""
		Set the default toolchain to be used.
		:param toolchainName: Name of the toolchain
		:type toolchainName: str, bytes
		"""
		currentPlan.defaultToolchain = toolchainName

	@TypeChecked(architectureName=String)
	def SetDefaultArchitecture(architectureName):
		"""
		Set the default architecture to be used.
		:param architectureName: Name of the architecture
		:type architectureName: str, bytes
		"""
		currentPlan.defaultArchitecture = architectureName

	@TypeChecked(targetName=String)
	def SetDefaultTarget(targetName):
		"""
		Set the default target to be used.
		:param targetName: Name of the target
		:type targetName: str, bytes
		"""
		currentPlan.defaultTarget = targetName

	def SetSupportedArchitectures(*args):
		"""
		Set the supported architectures for the enclosing scope
		:param args: Architectures to support
		:type args: str
		"""
		architectures = currentPlan.selfLimits["architecture"]
		if architectures:
			architectures.intersection_update(args)
		else:
			architectures.update(args)

	def SetSupportedToolchains(*args):
		"""
		Set the supported toolchains for the enclosing scope
		:param args: Toolchains to support
		:type args: str
		"""
		toolchains = currentPlan.selfLimits["toolchain"]
		if toolchains:
			toolchains.intersection_update(args)
		else:
			toolchains.update(args)

	def SetSupportedTargets(*args):
		"""
		Set the supported targets for the enclosing scope
		:param args: Targets to support
		:type args: str
		"""
		targets = currentPlan.selfLimits["target"]
		if targets:
			targets.intersection_update(args)
		else:
			targets.update(args)

	def SetSupportedPlatforms(*args):
		"""
		Set the supported platforms for the enclosing scope
		:param args: Platforms to support
		:type args: str
		"""
		platforms = currentPlan.selfLimits["platform"]
		if platforms:
			platforms.intersection_update(args)
		else:
			platforms.update(args)

	def SetUserData(key, value):
		"""
		Adds miscellaneous data to a project. This can be used later in a build event or in a format string.

		This becomes an attribute on the project's userData member variable. As an example, to set a value:

		csbuild.SetUserData("someData", "someValue")

		Then to access it later:

		project.userData.someData

		:param key: name of the variable to set
		:type key: str
		:param value: value to set to that variable
		:type value: any
		"""
		currentPlan.UpdateDict("_userData", {key : value})

	def SetOutputDirectory(outputDirectory):
		"""
		Specifies the directory in which to place the output file.

		:param outputDirectory: The output directory, relative to the current script location, NOT to the project working directory.
		:type outputDirectory: str
		"""
		currentPlan.SetValue("outputDir", os.path.abspath(outputDirectory))

	def SetIntermediateDirectory(intermediateDirectory):
		"""
		Specifies the directory in which to place the intermediate files.

		:param intermediateDirectory: The output directory, relative to the current script location, NOT to the project working directory.
		:type intermediateDirectory: str
		"""
		currentPlan.SetValue("intermediateDir", os.path.abspath(intermediateDirectory))

	class Scope(ContextManager):
		"""
		Enter a scope. Settings within this scope will be passed on to libraries that include this lib for intermediate,
		or to applications that include it for final. Anything that depends on this lib will inherit a value set to children,
		and a value set to all will be applied to this lib as well as inherited by children.

		:param scopeTypes: Scope type to enter
		:type scopeTypes: ScopeDef
		"""
		def __init__(self, *scopeTypes):
			for scopeType in scopeTypes:
				assert scopeType == Csbuild.ScopeDef.Intermediate or scopeType == Csbuild.ScopeDef.Final, "Invalid scope type"
			ContextManager.__init__(self, (("scope", scopeTypes),))

	class Toolchain(ContextManager):
		"""
		Apply values to a specific toolchain

		:param toolchainNames: Toolchain identifier
		:type toolchainNames: str, bytes
		"""
		def __init__(self, *toolchainNames):
			class _toolchainMethodResolver(object):
				def __getattribute__(self, item):
					allToolchains = currentPlan.GetValuesInCurrentContexts("_tempToolchain")
					return _getElementFromToolchains(self, allToolchains, item)

			ContextManager.__init__(self, (("toolchain", toolchainNames),), [_toolchainMethodResolver()])

	def ToolchainGroup(*names):
		"""
		Apply values to toolchains in a toolchain group
		:param names: Toolchain group names
		:type names: str
		:return: A context manager for the toolchains in the group
		:rtype: Toolchain
		"""
		toolchains = set()
		for name in names:
			toolchains |= shared_globals.toolchainGroups[name]
		return Toolchain(*toolchains)

	class Architecture(ContextManager):
		"""
		Apply values to a specific architecture

		:param architectureNames: Architecture identifier
		:type architectureNames: str, bytes
		"""
		def __init__(self, *architectureNames):
			ContextManager.__init__(self, (("architecture", architectureNames),))

	class Platform(ContextManager):
		"""
		Apply values to a specific platform

		:param platformNames: Platform identifier
		:type platformNames: str, bytes
		"""
		def __init__(self, *platformNames):
			ContextManager.__init__(self, (("platform", platformNames),))

	class Target(ContextManager):
		"""
		Apply values to a specific target

		:param targetNames: target identifiers
		:type targetNames: str, bytes
		:param kwargs: if addToCurrentScope is set to False as a keyword argument, only projects inside the scope of this
					   target will be made aware of this target's existence; other projects will be excluded
		"""
		def __init__(self, *targetNames, **kwargs):
			def _processKwargs(addToCurrentScope=True):
				if addToCurrentScope:
					currentPlan.knownTargets.update(targetNames)
					currentPlan.childTargets.update(targetNames)

			_processKwargs(**kwargs)

			self.oldChildTargets = set(currentPlan.childTargets)
			self.targetNames = targetNames

			shared_globals.allTargets.update(targetNames)

			ContextManager.__init__(self, (("target", targetNames),))

		def __enter__(self):
			currentPlan.childTargets.update(object.__getattribute__(self, "targetNames"))
			ContextManager.__enter__(self)

		def __exit__(self, exc_type, exc_val, exc_tb):
			currentPlan.childTargets = object.__getattribute__(self, "oldChildTargets")
			return ContextManager.__exit__(self, exc_type, exc_val, exc_tb)

	class MultiContext(ContextManager):
		"""
		Combine multiple contexts into a single context where the code within it will apply if
		ANY of the supplied contexts are valid

		:param contexts: List of other context manager instances
		:type contexts: ContextManager
		"""
		def __init__(self, *contexts):
			contextsDict = {}
			methodResolvers = set()

			for contextManager in contexts:
				object.__setattr__(contextManager, "inself", True)

				contextTuple = contextManager.contexts
				for subTuple in contextTuple:
					contextsDict.setdefault(subTuple[0], set()).update(subTuple[1])

				resolvers = contextManager.resolvers
				if resolvers:
					methodResolvers.update(resolvers)

				object.__setattr__(contextManager, "inself", False)

			if not methodResolvers:
				methodResolvers = None

			ContextManager.__init__(self, tuple(contextsDict.items()), methodResolvers)

	class Project(object):
		"""
		Apply settings to a specific project. If a project does not exist with the given name, it will be created.
		If it does exist, these settings will apply to the existing project.

		:param name: The project's name.
		:type name: str, bytes
		:param workingDirectory: The location on disk containing the project's files, which should be examined to collect source files.
			If autoDiscoverSourceFiles is False, this parameter is ignored.
		:type workingDirectory: str, bytes
		:param depends: List of names of other prjects this one depends on.
		:type depends: list(str, bytes)
		:param priority: Priority in the build queue, used to cause this project to get built first in its dependency ordering. Higher number means higher priority.
		:type priority: bool
		:param ignoreDependencyOrdering: Treat priority as a global value and use priority to raise this project above, or lower it below, the dependency order
		:type ignoreDependencyOrdering: bool
		:param autoDiscoverSourceFiles: If False, do not automatically search the working directory for files, but instead only build files that are manually added.
		:type autoDiscoverSourceFiles: bool
		"""

		@TypeChecked(name=String, workingDirectory=String, depends=(list,type(None)), priority=int, ignoreDependencyOrdering=bool, autoDiscoverSourceFiles=bool)
		def __init__(self, name, workingDirectory, depends=None, priority=0, ignoreDependencyOrdering=False, autoDiscoverSourceFiles=True):
			assert name != "", "Project name cannot be empty."
			assert workingDirectory != "", "Working directory cannot be empty (use '.' to use the makefile's local directory)"
			if depends is None:
				depends = []

			self._name = name
			self._workingDirectory = os.path.abspath(workingDirectory)
			self._depends = depends
			self._priority = priority
			self._ignoreDependencyOrdering = ignoreDependencyOrdering
			self._autoDiscoverSourceFiles = autoDiscoverSourceFiles
			self._prevPlan = None

		def __enter__(self):
			"""
			Enter project context
			"""
			global currentPlan
			self._prevPlan = currentPlan
			currentPlan = project_plan.ProjectPlan(
				self._name,
				self._workingDirectory,
				self._depends,
				self._priority,
				self._ignoreDependencyOrdering,
				self._autoDiscoverSourceFiles
			)
			if not shared_globals.projectFilter or self._name in shared_globals.projectFilter:
				shared_globals.sortedProjects.Add(currentPlan, self._depends)

		def __exit__(self, excType, excValue, traceback):
			"""
			Leave the project context

			:param excType: type of exception thrown in the context (ignored)
			:type excType: type
			:param excValue: value of thrown exception (ignored)
			:type excValue: any
			:param traceback: traceback attached to the thrown exception (ignored)
			:type traceback: traceback
			:return: Always false
			:rtype: bool
			"""
			global currentPlan
			currentPlan = self._prevPlan
			return False

	def Run():
		"""
		Run a build. This is called automatically if the environment variable CSBUILD_NO_AUTO_RUN is not equal to 1.
		If the build runs automatically, it will execute the csbuild makefile as part of running.
		If the build does not run automatically, the csbuild makefile is expected to finish executing before
		calling this function. The default and recommended behavior is to allow csbuild to run on its own;
		however, it can be beneficial to defer calling Run for use in environments such as tests and the
		interactive console.
		"""
		def _exitsig(sig, _):
			if sig == signal.SIGINT:
				log.Error("Keyboard interrupt received. Aborting build.")
			else:
				log.Error("Received terminate signal. Aborting build.")
			system.Exit(sig)

		signal.signal(signal.SIGINT, _exitsig)
		signal.signal(signal.SIGTERM, _exitsig)

		shared_globals.runMode = RunMode.Normal

		try:
			#Regular sys.exit can't be called because we HAVE to re-acquire the import lock at exit.
			#We stored sys.exit earlier, now we overwrite it to call our wrapper.
			sys.exit = system.Exit

			_build.Run()
			system.Exit(0)
		except:
			system.CleanUp()
			raise

if os.getenv(PlatformString("CSBUILD_NO_AUTO_RUN")) != "1":
	Run()
