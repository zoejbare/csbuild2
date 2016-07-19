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
.. module:: project_plan
	:synopsis: Contains non-finalized settings for building a project.
		This class is amalgamated with all possible settings this project can have, with all possible
		toolchain, architecture, and platform combinations. This plan will be executed per toolchain and architecture
		to create a concrete Project
"""

from __future__ import unicode_literals, division, print_function

import platform
import copy
import sys

import collections

if sys.version_info[0] >= 3:
	from collections.abc import Callable
else:
	from collections import Callable

from . import project
from .._utils import ordered_set
from .._utils.decorators import TypeChecked
from .._utils.string_abc import String
from .._zz_testing import testcase


allPlans = {}

class ProjectPlan(object):
	"""
	A plan to create one or more finalized projects.

	:param name: The project's name. Must be unique.
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
	@TypeChecked(name=String, workingDirectory=String, depends=list, priority=int, ignoreDependencyOrdering=bool, autoDiscoverSourceFiles=bool)
	def __init__(self, name, workingDirectory, depends, priority, ignoreDependencyOrdering, autoDiscoverSourceFiles):
		assert name not in allPlans, "Duplicate project name: {}".format(name)
		self._name = name
		self._workingDirectory = workingDirectory
		self._depends = depends
		self._priority = priority
		self._ignoreDependencyOrdering = ignoreDependencyOrdering
		self._autoDiscoverSourceFiles = autoDiscoverSourceFiles

		try:
			# pylint: disable=protected-access
			self._settings = copy.deepcopy(currentPlan._settings)
		except:
			self._settings = {}

		self._workingSettingsStack = [[self._settings]]
		self._currentSettingsDicts = self._workingSettingsStack[0]
		allPlans[name] = self

	_validContextTypes = {"toolchain", "architecture", "platform", "scope"}

	@TypeChecked(contextType=String)
	def EnterContext(self, contextType, *names):
		"""
		Enter a context for storing settings overrides.
		:param contextType: Must be in _validContextTypes
		:type contextType: str, bytes
		:param names: The identifiers for the context
		:type names: str, bytes
		"""
		assert contextType in ProjectPlan._validContextTypes, "Invalid context type!"
		newSettingsDicts = []
		for name in names:
			for settings in self._currentSettingsDicts:
				newSettingsDicts.append(settings.setdefault("overrides", {}).setdefault(contextType, {}).setdefault(name, {}))
		self._currentSettingsDicts = newSettingsDicts
		self._workingSettingsStack.append(self._currentSettingsDicts)

	def LeaveContext(self):
		"""Leave the context and return to the previous one"""
		self._workingSettingsStack.pop()
		self._currentSettingsDicts = self._workingSettingsStack[-1]

	def _absorbSettings(self, settings, overrideDict, toolchain, architecture, scopeType, inScope):
		if overrideDict is None:
			return

		if not scopeType or inScope:
			for key, val in overrideDict.items():
				if key == "overrides":
					continue

				# Libraries are a special case.
				# Any time any project references a library, that library should be moved later in the list.
				# Referenced libraries have to be linked after all the libraries that reference them.
				if key == "libraries":
					settings[key] = ordered_set.OrderedSet(settings.get(key, []))
					settings[key] -= val
					settings[key] |= val
					continue
				if isinstance(val, dict) or isinstance(val, collections.OrderedDict):
					settings[key] = dict(settings.get(key, {}))
					settings[key].update(val)
				elif isinstance(val, list):
					settings[key] = list(settings.get(key, []))
					settings[key] += val
				elif isinstance(val, ordered_set.OrderedSet) or isinstance(val, set):
					settings[key] = ordered_set.OrderedSet(settings.get(key, []))
					settings[key] |= val
				else:
					if not inScope or key not in self._settings:
						settings[key] = val
		# Else this function just recurses down to the next override dict to look for a dict of scopeType

		self._flattenOverrides(settings, overrideDict.get("overrides"), toolchain, architecture, scopeType, inScope)

	def _flattenOverrides(self, settings, overrideDict, toolchain, architecture, scopeType="", inScope=False):
		if overrideDict is None:
			return

		self._absorbSettings(settings, overrideDict.get("toolchain", {}).get(toolchain), toolchain, architecture, scopeType, inScope)
		self._absorbSettings(settings, overrideDict.get("architecture", {}).get(architecture), toolchain, architecture, scopeType, inScope)
		self._absorbSettings(settings, overrideDict.get("platform", {}).get(platform.system()), toolchain, architecture, scopeType, inScope)
		if scopeType:
			self._absorbSettings(settings, overrideDict.get("scope", {}).get(scopeType), toolchain, architecture, scopeType, True)

	def _getFinalValueFromOverride(self, overrideDict, name, toolchain, architecture, default):
		if overrideDict is not None:
			default = overrideDict.get(name, default)
			default = self._getFinalValue(overrideDict.get("overrides"), name, toolchain, architecture, default)
		return default

	def _getFinalValue(self, overrideDict, name, toolchain, architecture, default):
		if overrideDict is not None:
			default = overrideDict.get("scope", {}).get(name, default)
			default = self._getFinalValueFromOverride(overrideDict.get("toolchain", {}).get(toolchain), name, toolchain, architecture, default)
			default = self._getFinalValueFromOverride(overrideDict.get("architecture", {}).get(architecture), name, toolchain, architecture, default)
			default = self._getFinalValueFromOverride(overrideDict.get("platform", {}).get(platform.system()), name, toolchain, architecture, default)
		return default

	def _flattenDepends(self, flattenedDepends, dependObj):
		# pylint: disable=protected-access
		for depend in dependObj._depends:
			assert depend in allPlans, "Project {} references unknown dependency {}".format(dependObj._name, depend)
			if depend == self._name:
				continue
			self._flattenDepends(flattenedDepends, allPlans[depend])
			flattenedDepends.add(depend)

	@TypeChecked(toolchain=String, architecture=String)
	def ExecutePlan(self, toolchain, architecture):
		"""
		Execute the project plan for a given toolchain and architecture to create a concrete project.

		:param toolchain: The toolchain to execute the plan for
		:type toolchain: str, bytes
		:param architecture: The architecture to execute the plan for
		:type architecture: str, bytes
		:return: A concrete project
		:rtype: project.Project
		"""
		assert len(self._workingSettingsStack) == 1 and \
				len(self._workingSettingsStack[0]) == 1 and \
				self._workingSettingsStack[0][0] == self._settings and \
				len(self._currentSettingsDicts) == 1 and \
				self._currentSettingsDicts[0] == self._settings, \
				"Flatten() called from within a context!"

		from .. import ProjectType

		assert "overrides" in self._settings \
			and "toolchain" in self._settings["overrides"] \
			and toolchain in self._settings["overrides"]["toolchain"], \
			"Toolchain {} has not been registered for project {}".format(toolchain, self._name)

		projectType = self._settings.get("projectType", ProjectType.Application)
		projectType = self._getFinalValue(self._settings.get("overrides"), "projectType", toolchain, architecture, projectType)

		settings = {}
		for key, value in self._settings.items():
			if key == "overrides":
				continue
			settings[key] = copy.deepcopy(value)

		flattenedDepends = ordered_set.OrderedSet()
		self._flattenDepends(flattenedDepends, self)

		libraries = ordered_set.OrderedSet()
		if "libraries" in settings:
			libraries = settings["libraries"]
			del settings["libraries"]

		self._flattenOverrides(
			settings,
			self._settings.get("overrides", {}),
			toolchain,
			architecture,
			"all"
		)

		for depend in flattenedDepends:
			# pylint: disable=protected-access
			dependObj = allPlans[depend]
			# type: ProjectPlan

			if projectType == ProjectType.Application:
				settings["libraries"] = ordered_set.OrderedSet(settings.get("libraries")) | ordered_set.OrderedSet(
					[
						dependObj._getFinalValue(
							dependObj._settings.get("overrides"),
							"outputName",
							toolchain,
							architecture,
							dependObj._name
						)
					]
				)
				self._flattenOverrides(
					settings,
					dependObj._settings.get("overrides", {}),
					toolchain,
					architecture,
					"all"
				)
				self._flattenOverrides(
					settings,
					dependObj._settings.get("overrides", {}),
					toolchain,
					architecture,
					"children"
				)
				self._flattenOverrides(
					settings,
					dependObj._settings.get("overrides", {}),
					toolchain,
					architecture,
					"final"
				)
			else:
				self._flattenOverrides(
					settings,
					dependObj._settings.get("overrides", {}),
					toolchain,
					architecture,
					"all"
				)
				self._flattenOverrides(
					settings,
					dependObj._settings.get("overrides", {}),
					toolchain,
					architecture,
					"children"
				)
				self._flattenOverrides(
					settings,
					dependObj._settings.get("overrides", {}),
					toolchain,
					architecture,
					"scope"
				)

		if "libraries" in settings:
			settings["libraries"] |= libraries
		else:
			settings["libraries"] = libraries

		self._flattenOverrides(settings, self._settings.get("overrides"), toolchain, architecture)

		return project.Project(
			self._name,
			self._workingDirectory,
			flattenedDepends,
			self._priority,
			self._ignoreDependencyOrdering,
			self._autoDiscoverSourceFiles,
			settings
		)


	@TypeChecked(key=String, value=object)
	def SetValue(self, key, value):
		"""
		Set a value in the project settings

		:param key: The setting key
		:type key: str, bytes
		:param value: The value
		:type value: Any
		"""
		for settings in self._currentSettingsDicts:
			settings[key] = value

	@TypeChecked(key=String)
	def Unset(self, key):
		"""
		Set a value in the project settings

		:param key: The setting key
		:type key: str, bytes
		"""
		for settings in self._currentSettingsDicts:
			del settings[key]

	@TypeChecked(key=String, value=object)
	def ExtendList(self, key, value):
		"""
		Extend a list in the project settings

		:param key: The setting key
		:type key: str, bytes
		:param value: The value
		:type value: Any
		"""
		for settings in self._currentSettingsDicts:
			settings.setdefault(key, []).extend(value)

	@TypeChecked(key=String, value=object)
	def AppendList(self, key, value):
		"""
		Append to a list in the project settings

		:param key: The setting key
		:type key: str, bytes
		:param value: The value
		:type value: Any
		"""
		for settings in self._currentSettingsDicts:
			settings.setdefault(key, []).append(value)

	@TypeChecked(key=String, value=object)
	def UpdateDict(self, key, value):
		"""
		Update a dict in the project settings

		:param key: The setting key
		:type key: str, bytes
		:param value: The value
		:type value: Any
		"""
		for settings in self._currentSettingsDicts:
			settings.setdefault(key, {}).update(value)

	@TypeChecked(key=String, value=object)
	def UnionSet(self, key, value):
		"""
		Combine two sets in the project settings

		:param key: The setting key
		:type key: str, bytes
		:param value: The value
		:type value: Any
		"""
		for settings in self._currentSettingsDicts:
			settings.setdefault(key, ordered_set.OrderedSet()).union(value)

	@TypeChecked(key=String, value=object)
	def AddToSet(self, key, value):
		"""
		Add to a set in the project settings

		:param key: The setting key
		:type key: str, bytes
		:param value: The value
		:type value: Any
		"""
		for settings in self._currentSettingsDicts:
			settings.setdefault(key, ordered_set.OrderedSet()).add(value)

	@TypeChecked(key=String)
	def GetValuesInCurrentContexts(self, key):
		"""
		Get a list of all values in the currently active contexts.
		:param key: The setting key
		:type key: str, bytes
		:return: list
		"""
		ret = []
		for settings in self._currentSettingsDicts:
			ret.append(settings[key])
		return ret

	@TypeChecked(key=String, action=Callable)
	def PerformAction(self, key, action):
		"""
		Perform a complex action on values in the settings dictionary.

		:param key: The value to act on
		:type key: str, bytes
		:param action: The action to take
		:type action: A callable accepting a single parameter representing the current value and returning the new value.
			If the key has not been set for this scope, the current value passed in will be None.
			Note that the value passed in will represent only values in the CURRENT scope, not including
			values inherited from parent scopes.

			Any type may be stored this way, but if the types are to be merged with values from the parent scope, they
			should be one of the following types:
				- list
				- dict
				- collections.OrderedDict
				- set
				- csbuild._utils.ordered_set.OrderedSet
			Any other value will not be merged with values in parent scopes, but will override them.
		"""
		for settings in self._currentSettingsDicts:
			settings[key] = action(settings.setdefault(key, None))


currentPlan = ProjectPlan("", "", [], 0, False, False)

### Unit Tests ###

class TestProjectPlan(testcase.TestCase):
	"""Test the project plan"""
	# pylint: disable=invalid-name
	def setUp(self):
		from csbuild.toolchain import Tool
		class _nullTool(Tool):
			def Run(self, inputProject, inputFiles):
				pass

		global allPlans
		allPlans = {}
		global currentPlan
		# pylint: disable=protected-access
		currentPlan._settings = {}
		currentPlan = ProjectPlan("", "", [], 0, False, False)

		# Create some mocked in toolchains...
		currentPlan.EnterContext(
			"toolchain",
			"tc1",
			"tc2",
			"none",
			"scope-then-toolchain",
			"toolchain-then-scope",
			"no-toolchain"
		)

		currentPlan.SetValue("tools", ordered_set.OrderedSet((_nullTool,)))

		currentPlan.LeaveContext()

		self._oldPlan = currentPlan

	def tearDown(self):
		global currentPlan
		currentPlan = self._oldPlan


	def testProjectPlan(self):
		"""Ensure all overrides apply properly to the project plan"""
		plan = ProjectPlan("test", "test", [], 0, False, True)

		plan.SetValue("value", 1)
		plan.AppendList("list", 2)
		plan.AddToSet("set", 3)
		plan.UpdateDict("dict", {4: 5})

		plan.EnterContext("toolchain", "tc1")
		# pylint: disable=using-constant-test
		# The constant tests here are just so I can add indents to make the contexts easier to see
		if True:
			plan.SetValue("value", 6)
			plan.AppendList("list", 7)
			plan.AddToSet("set", 3)
			plan.AddToSet("set", 8)
			plan.UpdateDict("dict", {9: 10})
			plan.UpdateDict("dict", {4: 11})

			plan.EnterContext("architecture", "ar1")
			if True:
				plan.SetValue("value", 12)
				plan.AppendList("list", 13)
				plan.AddToSet("set", 3)
				plan.AddToSet("set", 14)
				plan.UpdateDict("dict", {15: 16})
				plan.UpdateDict("dict", {4: 17})

			plan.LeaveContext()

			plan.EnterContext("architecture", "ar2")
			if True:
				plan.SetValue("value", 18)
				plan.AppendList("list", 19)
				plan.AddToSet("set", 3)
				plan.AddToSet("set", 20)
				plan.UpdateDict("dict", {21: 22})
				plan.UpdateDict("dict", {4: 23})

				plan.LeaveContext()
			plan.LeaveContext()

		plan.EnterContext("architecture", "ar2")
		if True:
			plan.AppendList("list", 24)
			plan.AddToSet("set", 25)
			plan.UpdateDict("dict", {26: 27})

			plan.LeaveContext()

		plan.EnterContext("architecture", "ar3")
		if True:

			plan.SetValue("value", 28)
			plan.AppendList("list", 29)
			plan.AddToSet("set", 3)
			plan.AddToSet("set", 30)
			plan.UpdateDict("dict", {31: 32})
			plan.UpdateDict("dict", {4: 33})

			plan.EnterContext("toolchain", "tc2")
			if True:
				plan.SetValue("value", 34)
				plan.AppendList("list", 35)
				plan.AddToSet("set", 3)
				plan.AddToSet("set", 36)
				plan.UpdateDict("dict", {37: 38})
				plan.UpdateDict("dict", {4: 39})

				plan.LeaveContext()
			plan.LeaveContext()

		plan.EnterContext("toolchain", "tc2")
		if True:
			plan.AppendList("list", 40)
			plan.AddToSet("set", 41)
			plan.UpdateDict("dict", {42: 43})

			plan.LeaveContext()

		proj1 = plan.ExecutePlan("tc1", "ar1")
		proj2 = plan.ExecutePlan("tc1", "ar2")
		proj3 = plan.ExecutePlan("tc1", "ar3")
		proj4 = plan.ExecutePlan("tc2", "ar1")
		proj5 = plan.ExecutePlan("tc2", "ar2")
		proj6 = plan.ExecutePlan("tc2", "ar3")

		self.assertIn("value", proj1.settings)
		self.assertIn("list", proj1.settings)
		self.assertIn("set", proj1.settings)
		self.assertIn("dict", proj1.settings)

		self.assertIn("value", proj2.settings)
		self.assertIn("list", proj2.settings)
		self.assertIn("set", proj2.settings)
		self.assertIn("dict", proj2.settings)

		self.assertIn("value", proj3.settings)
		self.assertIn("list", proj3.settings)
		self.assertIn("set", proj3.settings)
		self.assertIn("dict", proj3.settings)

		self.assertIn("value", proj4.settings)
		self.assertIn("list", proj4.settings)
		self.assertIn("set", proj4.settings)
		self.assertIn("dict", proj4.settings)

		self.assertIn("value", proj5.settings)
		self.assertIn("list", proj5.settings)
		self.assertIn("set", proj5.settings)
		self.assertIn("dict", proj5.settings)

		self.assertIn("value", proj6.settings)
		self.assertIn("list", proj6.settings)
		self.assertIn("set", proj6.settings)
		self.assertIn("dict", proj6.settings)

		def _assertListOrSetMembers(listToCheck, *args):
			self.assertEqual(len(listToCheck), len(args))
			listToCheck = list(listToCheck)
			for i, arg in enumerate(args):
				self.assertEqual(arg, listToCheck[i])

		_assertListOrSetMembers(proj1.settings["list"], 2, 7, 13)
		_assertListOrSetMembers(proj2.settings["list"], 2, 7, 19, 24)
		_assertListOrSetMembers(proj3.settings["list"], 2, 7, 29)
		_assertListOrSetMembers(proj4.settings["list"], 2, 40)
		_assertListOrSetMembers(proj5.settings["list"], 2, 40, 24)
		_assertListOrSetMembers(proj6.settings["list"], 2, 40, 29, 35)

		_assertListOrSetMembers(proj1.settings["set"], 3, 8, 14)
		_assertListOrSetMembers(proj2.settings["set"], 3, 8, 20, 25)
		_assertListOrSetMembers(proj3.settings["set"], 3, 8, 30)
		_assertListOrSetMembers(proj4.settings["set"], 3, 41)
		_assertListOrSetMembers(proj5.settings["set"], 3, 41, 25)
		_assertListOrSetMembers(proj6.settings["set"], 3, 41, 30, 36)

		def _assertDictMembers(dictToCheck, *args):
			self.assertEqual(len(dictToCheck), len(args))
			for key, val in args:
				self.assertEqual(val, dictToCheck[key])

		_assertDictMembers(proj1.settings["dict"], (9, 10), (15, 16), (4, 17))
		_assertDictMembers(proj2.settings["dict"], (9, 10), (26, 27), (21, 22), (4, 23))
		_assertDictMembers(proj3.settings["dict"], (9, 10), (31, 32), (4, 33))
		_assertDictMembers(proj4.settings["dict"], (4, 5), (42, 43))
		_assertDictMembers(proj5.settings["dict"], (4, 5), (26, 27), (42, 43))
		_assertDictMembers(proj6.settings["dict"], (31, 32), (37, 38), (4, 39), (42, 43))


		self.assertEqual(proj1.settings["value"], 12)
		self.assertEqual(proj2.settings["value"], 18)
		self.assertEqual(proj3.settings["value"], 28)
		self.assertEqual(proj4.settings["value"], 1)
		self.assertEqual(proj5.settings["value"], 1)
		self.assertEqual(proj6.settings["value"], 34)

	def testScope(self):
		"""Ensure all scope overrides apply properly to dependent project plans"""
		from .. import ProjectType

		first = ProjectPlan("first", "test", [], 0, False, True)
		second = ProjectPlan("second", "test", ["first"], 0, False, True)
		third = ProjectPlan("third", "test", ["second"], 0, False, True)

		first.SetValue("projectType", ProjectType.StaticLibrary)
		second.SetValue("projectType", ProjectType.StaticLibrary)
		third.SetValue("projectType", ProjectType.Application)

		third.AddToSet("libraries", "lib1")

		first.EnterContext("scope", "final")
		# pylint: disable=using-constant-test
		# The constant tests here are just so I can add indents to make the contexts easier to see
		if True:
			first.AddToSet("libraries", "lib2")
			first.SetValue("should_be_one", 2)
			first.AddToSet("someSet", "final")
			first.EnterContext("toolchain", "scope-then-toolchain")
			if True:
				first.AddToSet("otherSet", "final")
				first.AddToSet("libraries", "lib3")
				first.LeaveContext()
			first.LeaveContext()

		first.EnterContext("scope", "intermediate")
		if True:
			first.AddToSet("someSet", "intermediate")
			first.EnterContext("toolchain", "scope-then-toolchain")
			if True:
				first.AddToSet("otherSet", "intermediate")
				first.LeaveContext()
			first.LeaveContext()

		first.EnterContext("toolchain", "toolchain-then-scope")
		if True:
			first.EnterContext("scope", "final")
			if True:
				first.AddToSet("thirdSet", "final")
				first.AddToSet("libraries", "lib4")
				first.LeaveContext()
			if True:
				first.EnterContext("scope", "intermediate")
				first.AddToSet("thirdSet", "intermediate")
				first.LeaveContext()
			first.LeaveContext()

		second.EnterContext("scope", "final")
		if True:
			second.AddToSet("libraries", "lib5")
			second.SetValue("should_be_one", 3)
			second.LeaveContext()

		third.SetValue("should_be_one", 1)
		third.AddToSet("libraries", "lib6")

		first1 = first.ExecutePlan("scope-then-toolchain", "none")
		first2 = first.ExecutePlan("toolchain-then-scope", "none")
		first3 = first.ExecutePlan("no-toolchain", "none")
		second1 = second.ExecutePlan("scope-then-toolchain", "none")
		second2 = second.ExecutePlan("toolchain-then-scope", "none")
		second3 = second.ExecutePlan("no-toolchain", "none")
		third1 = third.ExecutePlan("scope-then-toolchain", "none")
		third2 = third.ExecutePlan("toolchain-then-scope", "none")
		third3 = third.ExecutePlan("no-toolchain", "none")

		self.assertEqual(third1.settings["should_be_one"], 1)
		self.assertEqual(third2.settings["should_be_one"], 1)
		self.assertEqual(third3.settings["should_be_one"], 1)

		def _assertSetMembersInOrder(setToCheck, *args):
			self.assertEqual(len(setToCheck), len(args))
			setToCheck = list(setToCheck)
			for i, arg in enumerate(args):
				self.assertEqual(arg, setToCheck[i])

		_assertSetMembersInOrder(first1.settings["libraries"])
		_assertSetMembersInOrder(first2.settings["libraries"])
		_assertSetMembersInOrder(first3.settings["libraries"])
		_assertSetMembersInOrder(second1.settings["libraries"])
		_assertSetMembersInOrder(second2.settings["libraries"])
		_assertSetMembersInOrder(second3.settings["libraries"])
		_assertSetMembersInOrder(third1.settings["libraries"], "first", "lib2", "lib3", "second", "lib5", "lib1", "lib6")
		_assertSetMembersInOrder(third2.settings["libraries"], "first", "lib4", "lib2", "second", "lib5", "lib1", "lib6")
		_assertSetMembersInOrder(third3.settings["libraries"], "first", "lib2", "second", "lib5", "lib1", "lib6")

	def testInheritance(self):
		"""Test that project inheritance works correctly"""
		global currentPlan
		currentPlan = ProjectPlan("first", "test", [], 0, False, True)
		currentPlan.AppendList("list", 1)
		currentPlan.AppendList("list", 2)
		currentPlan.AppendList("list", 3)
		currentPlan.UpdateDict("dict", {1: 2})
		currentPlan.UpdateDict("dict", {3: 4})
		currentPlan.UpdateDict("dict", {5: 6})

		first = currentPlan
		currentPlan = ProjectPlan("second", "test", ["first"], 0, False, True)
		currentPlan.AppendList("list", 4)
		currentPlan.AppendList("list", 5)
		currentPlan.AppendList("list", 6)
		currentPlan.UpdateDict("dict", {7: 8})
		currentPlan.UpdateDict("dict", {9: 10})
		currentPlan.UpdateDict("dict", {11: 12})
		second = currentPlan


		first1 = first.ExecutePlan("none", "none")
		second1 = second.ExecutePlan("none", "none")

		self.assertEqual(first1.settings["list"], [1,2,3])
		self.assertEqual(second1.settings["list"], [1,2,3,4,5,6])
		self.assertEqual(first1.settings["dict"], {1:2,3:4,5:6})
		self.assertEqual(second1.settings["dict"], {1:2,3:4,5:6,7:8,9:10,11:12})

	def testMultiNameContext(self):
		"""Test that entering multiple contexts simultaneously works"""
		first = ProjectPlan("first", "test", [], 0, False, True)
		first.SetValue("a", 1)
		first.EnterContext("toolchain", "tc1", "tc2")
		first.SetValue("a", 2)
		first.LeaveContext()

		first1 = first.ExecutePlan("none", "none")
		first2 = first.ExecutePlan("tc1", "none")
		first3 = first.ExecutePlan("tc2", "none")

		self.assertEqual(first1.settings["a"], 1)
		self.assertEqual(first2.settings["a"], 2)
		self.assertEqual(first3.settings["a"], 2)

