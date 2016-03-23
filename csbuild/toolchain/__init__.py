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
.. package:: toolchain
	:synopsis: General-purpose toolchain infrastructure

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import abc
from .._utils.decorators import MetaClass

@MetaClass(abc.ABCMeta)
class Tool(object):
	"""
	Tool base class. Derive from this class to provide a tool for use in building things.

	Tool constructor should take at least one argument, which will be the project.

	If the constructor takes a second argument, that argument will be a list of commands that are queued
	to be run on this tool and should be run with self.RunCommands(commands)

	If the constructor does not take a second argument, or doesn't call self.RunCommands(), then self.RunCommands()
	will be called automatically after the constructor finishes.

	After the constructor has finished and self.RunCommands() is called, self.Finalize() will be called. If you
	call self.RunCommands() yourself, there is no need to delay any object initialization to Finalize(); if you
	allow csbuild to call it for you, anything that accesses post-makefile-processing tool state must be deferred
	to the Finalize() function.
	"""

	#: List of file extensions to be passed to Run as individual inputs.
	#  Run() will be called once per file as soon as each file is available to build
	#  Example: A C++ compiler would take individual inputs of types [".c", ".cc", ".cxx", ".cpp"]
	#  An empty string indicates a file with no extension
	inputFiles = []

	#: List of file extensions to be passed to Run as a group input.
	#  Run() will be called only once all tools that output this type have finished running
	#  and will be called only once on the entire group.
	#  Example: A C++ linker would take group inputs of types [".o"] or [".obj"] depending on the platform
	#  An empty string indicates a file with no extension
	inputGroups = []

	#: List of dependencies that will prevent Run() from being called if they're still being created,
	#  even if they're not taken as inputs.
	#  Example: A C++ compiler might add dependencies of type [".pch"] or [".gch"] to wait on a precompile step
	#  An empty string indicates a file with no extension
	dependencies = []

	#: The file extensions of files created by this toolchain
	#  Example: A C++ compiler would have output files of type [".o"] or [".obj"] depending on the platform
	#  Or a C++ linker would have output files of type [".exe", ".dll", ".lib"] or ["", ".so", ".a"]
	#  An empty string indicates a file with no extension
	outputFiles = []

	def Finalize(self):
		"""
		Called once all makefile commands are guaranteed to have run and it is safe to access that data.
		"""
		pass

	def RunCommands(self, commandList):
		"""
		Execute the enqqueued commands for this tool

		:param commandList: List of deferred makefile commands to run
		:type commandList: implementation defiled, please pass what you are handed.
		"""
		for command, args, kwargs in commandList:
			command(self, *args, **kwargs)

	@abc.abstractmethod
	def Run(self, project, files):
		"""
		Execute a single build step. Note that this method is run massively in parallel with other build steps.
		It is NOT thread-safe in ANY way. If you need to change shared state within this method, you MUST use a
		mutex.

		:param project:
		:type project: csbuild._build.project.Project
		:param files: List of files to build (for the inputFiles case, this will always be a list of size 1)
		:type files: list(.._utils.StrType)
		:return: List of files created by the tool - all files must have an extension in the outputFiles list
		:rtype: list(.._utils.StrType)
		"""
		pass

