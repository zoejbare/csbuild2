# Copyright (C) 2016 Jaedyn K. Draper
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
.. module:: make
	:synopsis: Makefile for this test

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import subprocess

from csbuild.tools.cpp_compilers import msvc_cpp_compiler, gcc_cpp_compiler
from csbuild.tools.linkers import msvc_linker, gcc_linker

csbuild.SetOutputDirectory("out")

#pylint: disable=missing-docstring
class ExecutingGccLinker(gcc_linker.GccLinker):
	def RunGroup(self, project, inputFiles):
		outputFiles = gcc_linker.GccLinker.RunGroup(self, project, inputFiles)
		subprocess.check_output([outputFiles[0]])
		return outputFiles

#pylint: disable=missing-docstring
class ExecutingMsvcLinker(msvc_linker.MsvcLinker):
	def RunGroup(self, project, inputFiles):
		outputFiles = msvc_linker.MsvcLinker.RunGroup(self, project, inputFiles)
		subprocess.check_output([outputFiles[0]])
		return outputFiles

csbuild.RegisterToolchain("gcc", csbuild.GetSystemArchitecture(), gcc_cpp_compiler.GccCppCompiler, ExecutingGccLinker)
csbuild.RegisterToolchain("msvc", csbuild.GetSystemArchitecture(), msvc_cpp_compiler.MsvcCppCompiler, ExecutingMsvcLinker)

with csbuild.Project("hello_world", "hello_world"):
	csbuild.SetOutput("hello_world", csbuild.ProjectType.Application)
