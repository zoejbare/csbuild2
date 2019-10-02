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
.. module:: clang_cpp_compiler
	:synopsis: Clang compiler tool for C++.

.. moduleauthor:: Zoe Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild

from .gcc_cpp_compiler import GccCppCompiler

class ClangCppCompiler(GccCppCompiler):
	"""
	Clang compiler implementation
	"""

	####################################################################################################################
	### Methods implemented from base classes
	####################################################################################################################

	def _getComplierName(self, isCpp):
		return "clang++" if isCpp else "clang"

	def _getDefaultArgs(self, project):
		args = []
		if project.projectType == csbuild.ProjectType.SharedLibrary:
			args.append("-fPIC")
		return args

	def _getArchitectureArgs(self, project):
		baseArgs = GccCppCompiler._getArchitectureArgs(self, project)

		# When necessary fill in the architecture name with something clang expects.
		architecture = {
			"x86": "i386",
			"x64": "x86_64",
		}.get(project.architectureName, project.architectureName)

		return baseArgs + [
			"-arch", architecture,
		]
