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
.. module:: gcc_cpp_compiler
	:synopsis: gcc compiler tool for C++

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import os
import csbuild

from .cpp_compiler_base import CppCompilerBase

class GccCppCompiler(CppCompilerBase):
	"""
	GCC compiler implementation
	"""
	supportedArchitectures = {"x86", "x64"}
	outputFiles = {".o"}

	def _getOutputFiles(self, project, inputFile):
		filename = os.path.splitext(os.path.basename(inputFile.filename))[0] + ".o"
		return os.path.join(project.GetIntermediateDirectory(inputFile), filename)

	def _getCommand(self, project, inputFile, isCpp):
		cmd = "g++" if isCpp else "gcc"
		ret = [
			cmd,
			"-c", inputFile.filename,
			"-o", self._getOutputFiles(project, inputFile),
		] + ["-I"+directory for directory in self._includeDirectories]

		if project.projectType == csbuild.ProjectType.SharedLibrary:
			ret += ["-fPIC"]
		return ret
