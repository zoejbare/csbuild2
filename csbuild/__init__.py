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
.. package:: CSBuild
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

from ._build.context_manager import ContextManager
from ._build import project_plan

from . import _build
from ._utils import system
from ._utils.string_abc import String
from ._utils.decorators import TypeChecked, Overload
from ._utils import shared_globals
from ._utils import ordered_set

from .toolchain import toolchain

class ProjectType(object):
	"""
	Enum representing the available project types.
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
	project_plan.currentPlan.SetValue("outputName", name)
	project_plan.currentPlan.SetValue("projectType", projectType)

@TypeChecked(name=String)
def RegisterToolchain(name, *tools):
	"""
 	Register a new toolchain to be used by the project for building

 	:param name: The name of the toolchain, which will be used to reference it
 	:type name: str, bytes
 	:param tools: List of tools to be used to make the toolchain.
 	:type tools: class
 	:return:
 	"""
	project_plan.currentPlan.EnterContext("toolchain", name)
	project_plan.currentPlan.SetValue("tools", ordered_set.OrderedSet(tools))
	project_plan.currentPlan.SetValue("_tempToolchain", toolchain.Toolchain(*tools))
	project_plan.currentPlan.LeaveContext()

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
				allToolchains = project_plan.currentPlan.GetValuesInCurrentContexts("_tempToolchain")
				for tempToolchain in allToolchains:
					funcs.append(getattr(tempToolchain, item))

				def _runFuncs(*args, **kwargs):
					for func in funcs:
						func(*args, **kwargs)

				return _runFuncs

		ContextManager.__init__(self, "toolchain", toolchainNames, [_toolchainMethodResolver()])

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
		ContextManager.__init__(self, "target", targetNames)

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
		if depends is None:
			depends = []

		self._name = name
		self._workingDirectory = workingDirectory
		self._depends = depends
		self._priority = priority
		self._ignoreDependencyOrdering = ignoreDependencyOrdering
		self._autoDiscoverSourceFiles = autoDiscoverSourceFiles
		self._prevPlan = None

	def __enter__(self):
		"""
		Enter project context
		"""
		project_plan.currentPlan = project_plan.ProjectPlan(
			self._name,
			self._workingDirectory,
			self._depends,
			self._priority,
			self._ignoreDependencyOrdering,
			self._autoDiscoverSourceFiles
		)

	def __exit__(self, excType, excValue, traceback):
		"""
		Leave the project context

		:param excType: type of exception thrown in the context (ignored)
		:type excType: type
		:param excValue: value of thrown exception (ignored)
		:type excValue: any
		:param traceback: traceback attached to the thrown exception (ignored)
		:type traceback: traceback
		"""
		project_plan.currentPlan = self._prevPlan
		return False

if not hasattr(sys, "runningSphinx") and not hasattr(sys, "runningUnitTests"):
	try:
		#Regular sys.exit can't be called because we HAVE to reacquore the import lock at exit.
		#We stored sys.exit earlier, now we overwrite it to call our wrapper.
		sys.exit = system.Exit

		_build.Run()
		system.Exit(0)
	except Exception as e:
		if not imp.lock_held():
			imp.acquire_lock()
		raise
