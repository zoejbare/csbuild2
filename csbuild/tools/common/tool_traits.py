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
.. module:: tool_traits
	:synopsis: Optional add-ins for tools.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild

from ...toolchain import Tool

class HasDebugLevel(Tool):
	"""
	Helper class to add debug level support to a tool.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	class DebugLevel(object):
		"""
		'enum' representing various levels of debug information
		"""
		Disabled = 0
		EmbeddedSymbols = 1
		ExternalSymbols = 2
		ExternalSymbolsPlus = 3

	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)
		self._debugLevel = projectSettings.get("debugLevel", HasDebugLevel.DebugLevel.Disabled)

	@staticmethod
	def SetDebugLevel(debugLevel):
		"""
		Set a project's desired debug level.

		:param debugLevel: Project debug level.
		:type debugLevel: :class:`csbuild.tools.common.has_debug_level.DebugLevel`
		"""
		csbuild.currentPlan.SetValue("debugLevel", debugLevel)


class HasOptimizationLevel(Tool):
	"""
	Helper class to add optimization level support to a tool.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	class OptimizationLevel(object):
		"""
		'enum' representing various optimization levels
		"""
		Disabled = 0
		Size = 1
		Speed = 2
		Max = 3

	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)
		self._optLevel = projectSettings.get("optLevel", HasOptimizationLevel.OptimizationLevel.Disabled)

	@staticmethod
	def SetOptimizationLevel(optLevel):
		"""
		Set a project's desired optimization level.

		:param optLevel: Project optimization level.
		:type optLevel: :class:`csbuild.tools.common.has_debug_level.OptimizationLevel`
		"""
		csbuild.currentPlan.SetValue("optLevel", optLevel)


class HasStaticRuntime(Tool):
	"""
	Helper class to add static runtime support to a tool.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)
		self._staticRuntime = projectSettings.get("staticRuntime", False)

	@staticmethod
	def SetStaticRuntime(staticRuntime):
		"""
		Set whether or not a project should use the static runtime library.

		:param staticRuntime: Use the static runtime library.
		:type staticRuntime: bool
		"""
		csbuild.currentPlan.SetValue("staticRuntime", staticRuntime)


class HasDebugRuntime(Tool):
	"""
	Helper class to add debug runtime support to a tool.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)
		self._debugRuntime = projectSettings.get("debugRuntime", False)

	@staticmethod
	def SetDebugRuntime(debugRuntime):
		"""
		Set whether or not a project should use the debug runtime library.

		:param debugRuntime: Use the debug runtime library.
		:type debugRuntime: bool
		"""
		csbuild.currentPlan.SetValue("debugRuntime", debugRuntime)