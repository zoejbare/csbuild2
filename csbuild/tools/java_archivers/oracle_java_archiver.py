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
.. module:: oracle_java_archiver
	:synopsis: Oracle Java archiver tool.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import platform
import os

from .java_archiver_base import JavaArchiverBase

class OracleJavaArchiver(JavaArchiverBase):
	"""
	Oracle Java archiver implementation.
	"""
	def __init__(self, projectSettings):
		JavaArchiverBase.__init__(self, projectSettings)

		self._javaArchiverPath = os.path.join(self._javaHomePath, "bin", "jar{}".format(".exe" if platform.system() == "Windows" else ""))
		assert os.access(self._javaArchiverPath, os.F_OK), "Oracle Java archiver not found at path: {}".format(self._javaArchiverPath)


	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def _getOutputFiles(self, project):
		return tuple({ self._getOutputFilePath(project) })

	def _getCommand(self, project, inputFiles):
		if project.projectType == csbuild.ProjectType.Application:
			assert self._entryPointClass, "No entry point class defined"
			manifestFilePath = os.path.join(project.csbuildDir, "app_manifest.txt")
			with open(manifestFilePath, "w") as f:
				f.write("Main-Class: {}\n".format(self._entryPointClass))
		else:
			manifestFilePath = None

		cmd = [self._javaArchiverPath] \
			+ ["cf" + "m" if manifestFilePath else ""] \
			+ [self._getOutputFilePath(project)] \
			+ [manifestFilePath] if manifestFilePath else [] \
			+ [f.filename for f in inputFiles]
		return [arg for arg in cmd if arg]


	####################################################################################################################
	### Internal methods
	####################################################################################################################

	def _getOutputFilePath(self, project):
		return os.path.join(project.outputDir, "{}.jar".format(project.outputName))
