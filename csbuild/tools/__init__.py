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
.. package:: tools
	:synopsis: Set of built-in tools that ship with csbuild

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import csbuild

from .cpp_compilers import CppCompileChecker

from .cpp_compilers.gcc_cpp_compiler import GccCppCompiler
from .cpp_compilers.msvc_cpp_compiler import MsvcCppCompiler

from .linkers.gcc_linker import GccLinker
from .linkers.msvc_linker import MsvcLinker

def InitTools():
	"""
	Initialize the built-in csbuild tools
	"""
	systemArchitecture = csbuild.GetSystemArchitecture()
	checkers = {}
	cppChecker = CppCompileChecker()

	for inputExtension in GccCppCompiler.inputFiles | MsvcCppCompiler.inputFiles:
		checkers[inputExtension] = cppChecker

	csbuild.RegisterToolchain("gcc", systemArchitecture, GccCppCompiler, GccLinker, checkers=checkers)
	csbuild.RegisterToolchain("msvc", systemArchitecture, MsvcCppCompiler, MsvcLinker, checkers=checkers)