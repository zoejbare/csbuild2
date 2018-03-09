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
import platform

from .assemblers import AsmCompileChecker
from .cpp_compilers import CppCompileChecker
from .java_compilers import JavaCompileChecker

from .assemblers.android_gcc_assembler import AndroidGccAssembler
from .assemblers.clang_assembler import ClangAssembler
from .assemblers.gcc_assembler import GccAssembler
from .assemblers.msvc_assembler import MsvcAssembler

from .cpp_compilers.android_gcc_cpp_compiler import AndroidGccCppCompiler
from .cpp_compilers.clang_cpp_compiler import ClangCppCompiler
from .cpp_compilers.gcc_cpp_compiler import GccCppCompiler
from .cpp_compilers.mac_os_clang_cpp_compiler import MacOsClangCppCompiler
from .cpp_compilers.msvc_cpp_compiler import MsvcCppCompiler

from .java_archivers.oracle_java_archiver import OracleJavaArchiver

from .java_compilers.oracle_java_compiler import OracleJavaCompiler

from .linkers.android_gcc_linker import AndroidGccLinker
from .linkers.clang_linker import ClangLinker
from .linkers.gcc_linker import GccLinker
from .linkers.mac_os_clang_linker import MacOsClangLinker
from .linkers.msvc_linker import MsvcLinker

def InitTools():
	"""
	Initialize the built-in csbuild tools
	"""
	systemArchitecture = csbuild.GetSystemArchitecture()

	# Get either the platform-specific clang tools or the default clang tools.
	clangCompiler, clangLinker = {
		"Darwin": (MacOsClangCppCompiler, MacOsClangLinker),
	}.get(platform.system(), (ClangCppCompiler, ClangLinker))

	# Register C/C++ toolchains.
	for name, compiler, linker, assembler in [
		( "gcc", GccCppCompiler, GccLinker, GccAssembler ),
		( "clang", clangCompiler, clangLinker, ClangAssembler ),
		( "msvc", MsvcCppCompiler, MsvcLinker, MsvcAssembler ),
		( "android-gcc", AndroidGccCppCompiler, AndroidGccLinker, AndroidGccAssembler ),
	]:
		checkers = {}
		cppChecker = CppCompileChecker(compiler)
		asmChecker = AsmCompileChecker(assembler)

		for inputExtension in compiler.inputFiles:
			checkers[inputExtension] = cppChecker

		for inputExtension in assembler.inputFiles:
			checkers[inputExtension] = asmChecker

		csbuild.RegisterToolchain(name, systemArchitecture, compiler, linker, assembler, checkers=checkers)

	# Register Java toolchains.
	for name, compiler, archiver in [
		( "oracle-java", OracleJavaCompiler, OracleJavaArchiver ),
	]:
		checkers = {}
		javaChecker = JavaCompileChecker(compiler)

		for inputExtension in compiler.inputFiles:
			checkers[inputExtension] = javaChecker

		csbuild.RegisterToolchain(name, systemArchitecture, compiler, archiver, checkers=checkers)

	# Register toolchain groups.
	csbuild.RegisterToolchainGroup("gnu", "gcc", "clang")
	csbuild.RegisterToolchainGroup("android", "android-gcc")
