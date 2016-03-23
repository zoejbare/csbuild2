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
	:type priority: bool
	:param ignoreDependencyOrdering: Treat priority as a global value and use priority to raise this project above, or lower it below, the dependency order
	:type ignoreDependencyOrdering: bool
	:param autoDiscoverSourceFiles: If False, do not automatically search the working directory for files, but instead only build files that are manually added.
	:type autoDiscoverSourceFiles: bool
	:param projectSettings: Finalized settings from the project plan
	:type projectSettings: dict
	"""
	def __init__(self, name, workingDirectory, depends, priority, ignoreDependencyOrdering, autoDiscoverSourceFiles, projectSettings):
		self.name = name
		self.workingDirectory = workingDirectory
		self.depends = depends
		self.priority = priority
		self.ignoreDependencyOrdering = ignoreDependencyOrdering
		self.autoDiscoverSourceFiles = autoDiscoverSourceFiles
		self.settings = projectSettings
