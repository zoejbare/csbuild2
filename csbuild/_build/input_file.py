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
.. module:: input_file
	:synopsis: Information about a file used as a tool input

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import os

from .._utils.decorators import TypeChecked
from .._utils.string_abc import String
from .._utils import PlatformString
from ..toolchain import Tool

class InputFile(object):
	"""
	Represents an input file along with its tool history.
	Stores both the full set of tools used to create the file,
	as well as a link to the previous input source that created it

	:param filename: The filename
	:type filename: str, bytes

	:param sourceInput: The previous input in the chain (if None, this represents the first input)
	:type sourceInput: InputFile
	"""
	def __init__(self, filename, sourceInput=None):
		# Can't do @TypeChecked with type InputFile due to incomplete type issue, so have to do this check manually
		if not isinstance(filename, String):
			raise TypeError("Argument 'filename' is type {}, expected {}".format(filename.__class__, String))

		if sourceInput is not None and not isinstance(sourceInput, InputFile):
			raise TypeError("Argument 'sourceInput' is type {}, expected {}".format(sourceInput.__class__, InputFile))

		self._filename = os.path.abspath(PlatformString(filename))
		self._sourceInput = sourceInput
		if sourceInput is not None:
			# pylint: disable=protected-access
			self._toolsUsed = sourceInput._toolsUsed
		else:
			self._toolsUsed = set()

	@TypeChecked(tool=Tool)
	def AddUsedTool(self, tool):
		"""
		Add a tool to the set of tools that have been used on this file

		:param tool: The used tool
		:type tool: Tool
		"""
		self._toolsUsed.add(tool)

	@TypeChecked(tool=Tool, _return=bool)
	def WasToolUsed(self, tool):
		"""
		Check if a tool was used in the process of creating this file (or any file used in the input chain that led to it)

		:param tool: The tool to check
		:type tool: Tool
		:return: True if the tool was used, False otherwise
		:rtype: bool
		"""
		return tool in self._toolsUsed

	@property
	def filename(self):
		"""
		Get the absolute path to the file

		:return: Absolute path to the file
		:rtype: str
		"""
		return self._filename

	@property
	def sourceInput(self):
		"""
		Get the InputFile that was used to create this file, if any

		:return: The InputFile that was used to create this file
		:rtype: InputFile or None
		"""
		return self._sourceInput
