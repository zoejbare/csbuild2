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

import sys
import imp
import signal
import os

__author__ = "Jaedyn K. Draper, Brandon M. Bare"
__copyright__ = 'Copyright (C) 2012-2014 Jaedyn K. Draper'
__credits__ = ["Jaedyn K. Draper", "Brandon M. Bare", "Jeff Grills", "Randy Culley"]
__license__ = 'MIT'

__maintainer__ = "Jaedyn K. Draper"
__email__ = "jaedyn.csbuild-contact@jaedyn.co"
__status__ = "Development"

try:
	with open(os.path.join(os.path.dirname(__file__), "version"), "r") as f:
		__version__ = f.read()
except IOError:
	__version__ = "ERR_VERSION_FILE_MISSING"

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
		self._resolver = None
		self._module = sys.modules["csbuild"]

	def __getattr__(self, name):
		if hasattr(self._module, name):
			return getattr(self._module, name)

		if self._resolver is not None and hasattr(self._resolver, name):
			return getattr(self._resolver, name)

		return object.__getattribute__(self, name)


sys.modules["csbuild"] = Csbuild()

# pylint: disable=wrong-import-position
from ._build.context_manager import ContextManager
from ._build import project_plan, project, input_file

from . import _build, log
from ._utils import system
from ._utils.string_abc import String
from ._utils.decorators import TypeChecked, Overload
from ._utils import shared_globals
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

class DebugLevel( object ):
	"""
	'enum' representing various levels of debug information
	"""
	Disabled = 0
	EmbeddedSymbols = 1
	ExternalSymbols = 2
	ExternalSymbolsPlus = 3

class OptimizationLevel( object ):
	"""
	'enum' representing various optimization levels
	"""
	Disabled = 0
	Size = 1
	Speed = 2
	Max = 3

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
def RegisterToolchain(name, defaultArchitecture, *tools):
	"""
 	Register a new toolchain to be used by the project for building

 	:param name: The name of the toolchain, which will be used to reference it
 	:type name: str, bytes
 	:param defaultArchitecture: The default architecture to be used for this toolchain
 	:type defaultArchitecture: str, bytes
 	:param tools: List of tools to be used to make the toolchain.
 	:type tools: class
 	:return:
 	"""
	shared_globals.allToolchains.add(name)
	currentPlan.EnterContext("toolchain", name)
	currentPlan.SetValue("tools", ordered_set.OrderedSet(tools))
	currentPlan.SetValue("_tempToolchain", toolchain.Toolchain({}, *tools, runInit=False))
	currentPlan.defaultArchitectureMap[name] = defaultArchitecture
	currentPlan.LeaveContext()

	for tool in tools:
		if tool.supportedArchitectures is not None:
			shared_globals.allArchitectures.intersection_update(set(tool.supportedArchitectures))

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
	currentPlan.UnionSet("supportedArchitectures", args)

def SetSupportedToolchains(*args):
	"""
	Set the supported toolchains for the enclosing scope
	:param args: Toolchains to support
	:type args: str
	"""
	currentPlan.UnionSet("supportedToolchains", args)

def SetSupportedTargets(*args):
	"""
	Set the supported targets for the enclosing scope
	:param args: Targets to support
	:type args: str
	"""
	currentPlan.UnionSet("supportedTargets", args)

def SetSupportedPlatforms(*args):
	"""
	Set the supported platforms for the enclosing scope
	:param args: Platforms to support
	:type args: str
	"""
	currentPlan.UnionSet("supportedPlatforms", args)

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
		ContextManager.__init__(self, "scope", scopeTypes)

class Toolchain(ContextManager):
	"""
	Apply values to a specific toolchain

	:param toolchainNames: Toolchain identifier
	:type toolchainNames: str, bytes
	"""
	def __init__(self, *toolchainNames):
		class _toolchainMethodResolver(object):
			def __getattribute__(self, item):
				funcs = []
				allToolchains = currentPlan.GetValuesInCurrentContexts("_tempToolchain")
				for tempToolchain in allToolchains:
					funcs.append(getattr(tempToolchain, item))

				def _runFuncs(*args, **kwargs):
					for func in funcs:
						func(*args, **kwargs)

				return _runFuncs

		ContextManager.__init__(self, "toolchain", toolchainNames, [_toolchainMethodResolver()])

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
		ContextManager.__init__(self, "architecture", architectureNames)

class Platform(ContextManager):
	"""
	Apply values to a specific platform

	:param platformNames: Platform identifier
	:type platformNames: str, bytes
	"""
	def __init__(self, *platformNames):
		ContextManager.__init__(self, "platform", platformNames)

class Target(ContextManager):
	"""
	Apply values to a specific target

	:param targetNames: target identifiers
	:type targetNames: str, bytes
	"""
	def __init__(self, *targetNames):
		shared_globals.allTargets.update(targetNames)
		currentPlan.UnionSet("targets", targetNames)
		ContextManager.__init__(self, "target", targetNames)

class Language(ContextManager):
	"""
	Apply values within a specific language

	:param langNames: Language identifier
	:type langNames: str, bytes
	"""
	def __init__(self, *langNames):
		langs = [shared_globals.languages[lang] for lang in langNames]
		class _languageMethodResolver(object):
			def __getattribute__(self, item):
				funcs = []
				for lang in langs:
					funcs.append(getattr(lang, item))

				def _runFuncs(*args, **kwargs):
					for func in funcs:
						func(*args, **kwargs)

				return _runFuncs

		ContextManager.__init__(self, None, (), [_languageMethodResolver()])

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
		if not shared_globals.projectFilter or self._name not in shared_globals.projectFilter:
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
