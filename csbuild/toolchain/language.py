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
.. module:: language
	:synopsis: language class

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import sys

from . import Tool, toolchain
from .._utils import shared_globals
from .._utils.decorators import TypeChecked

if sys.version_info[0] >= 3:
	_typeType = type
	_classType = type
else:
	# pylint: disable=invalid-name
	import types
	_typeType = types.TypeType
	_classType = types.ClassType

class Language(object):
	"""
	Represents the base tools that make up a language.
	Unlike toolchain, all tools in a language must have the same interface, though that interface is user-defined.
	In the vast majority of cases, languages will likely only have one tool each (the base class shared by all tools
	implementing that language), so this requirement will be irrelevant to most users.
	"""
	def __init__(self):
		self._tools =[]

	@TypeChecked(tool=(_typeType, _classType))
	def AddTool(self, tool):
		"""
		Add a tool to the language
		:param tool: The BASE CLASS that will be shared by all tools implementing that language
		:type tool: class inheriting from Tool
		"""
		assert issubclass(tool, Tool)
		self._tools.append(tool)

	def __getattr__(self, item):
		def _runMultiFunc(*args, **kwargs):
			lastToolId = toolchain.currentToolId
			for tool in self._tools:
				toolchain.currentToolId = id(tool)
				getattr(tool, item)(*args, **kwargs)
			toolchain.currentToolId = lastToolId
		return _runMultiFunc

def LanguageBaseClass(lang):
	"""
	Decorator that should be applied to a base class implementing a language.
	:param lang: The name of the language (i.e., c++)
	:type lang: str
	:return: The original class
	:rtype: type
	"""
	def _wrap(cls):
		shared_globals.languages.setdefault(lang, Language()).AddTool(cls)
		return cls
	return _wrap
