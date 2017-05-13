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

from .assemblers import AsmCompileChecker
from .cpp_compilers import CppCompileChecker

from .assemblers.msvc_assembler import MsvcAssembler
from .assemblers.gcc_assembler import GccAssembler

from .cpp_compilers.gcc_cpp_compiler import GccCppCompiler
from .cpp_compilers.clang_cpp_compiler import ClangCppCompiler
from .cpp_compilers.msvc_cpp_compiler import MsvcCppCompiler

from .linkers.gcc_linker import GccLinker
from .linkers.msvc_linker import MsvcLinker

def InitTools():
	"""
	Initialize the built-in csbuild tools
	"""
	systemArchitecture = csbuild.GetSystemArchitecture()

	for name, compiler, linker, assembler in [
		( "gcc", GccCppCompiler, GccLinker, GccAssembler ),
		( "clang", ClangCppCompiler, GccLinker, GccAssembler ),
		( "msvc", MsvcCppCompiler, MsvcLinker, MsvcAssembler )
	]:
		checkers = {}
		cppChecker = CppCompileChecker(compiler)
		asmChecker = AsmCompileChecker(assembler)

		for inputExtension in compiler.inputFiles:
			checkers[inputExtension] = cppChecker

		for inputExtension in assembler.inputFiles:
			checkers[inputExtension] = asmChecker

		csbuild.RegisterToolchain(name, systemArchitecture, compiler, linker, assembler, checkers=checkers)

	csbuild.RegisterToolchainGroup("gnu", "gcc", "clang")
