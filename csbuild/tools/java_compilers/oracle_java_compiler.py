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
.. module:: oracle_java_compiler
	:synopsis: Oracle Java compiler tool.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import platform
import os

from .java_compiler_base import JavaCompilerBase

class OracleJavaCompiler(JavaCompilerBase):
	"""
	Oracle Java compiler implementation.
	"""
	def __init__(self, projectSettings):
		JavaCompilerBase.__init__(self, projectSettings)

		self._javaCompilerPath = os.path.join(self._javaHomePath, "bin", "javac{}".format(".exe" if platform.system() == "Windows" else ""))
		assert os.access(self._javaCompilerPath, os.F_OK), "Oracle Java compiler not found at path: {}".format(self._javaCompilerPath)


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def _getOutputFiles(self, project, inputFile):
		intermediateRootPath = project.GetIntermediateDirectory(inputFile)
		outputFiles = set()

		# Find each .class file in the input file's intermediate directory.
		for root, _, files in os.walk(intermediateRootPath):
			for filePath in files:
				outputFiles.add(os.path.join(root, filePath))

		return tuple(sorted(outputFiles))

	def _getCommand(self, project, inputFile):
		cmd = [self._javaCompilerPath] \
			+ self._getClassPathArgs() \
			+ self._getSourcePathArgs() \
			+ self._getOutputPathArgs(project, inputFile) \
			+ [inputFile.filename]
		return [arg for arg in cmd if arg]


	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getClassPathArgs(self):
		if self._classPaths:
			arg = ";".join(self._classPaths)
			return [
				"-classpath",
				arg,
			]
		else:
			return []

	def _getSourcePathArgs(self):
		if self._srcPaths:
			arg = ";".join(self._srcPaths)
			return [
				"-sourcepath",
				arg,
			]
		else:
			return []

	def _getOutputPathArgs(self, project, inputFile):
		return [
			"-d",
			project.GetIntermediateDirectory(inputFile),
		]
