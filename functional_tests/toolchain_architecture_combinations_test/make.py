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

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import csbuild
from csbuild.toolchain import Tool
import os

class WriteOutput(Tool):
	"""Dummy class"""
	inputFiles = None

	def __init__(self, projectSettings, ext):
		self._ext = ext
		Tool.__init__(self, projectSettings)

	def Run(self, project, inputFile):
		outFile = os.path.join(project.outputDir, project.outputName + "." + project.architectureName + "." + project.targetName + "." + self._ext)
		csbuild.log.Build("Writing {}", outFile)
		with open(outFile, "w") as f:
			f.write("foo")
		return outFile

class WriteA(WriteOutput):
	"""Dummy class"""
	supportedArchitectures = {"A", "B", "C", "D"}
	def __init__(self, projectSettings):
		WriteOutput.__init__(self, projectSettings, "A")

class WriteB(WriteOutput):
	"""Dummy class"""
	supportedArchitectures = {"A", "B", "C", "D"}
	def __init__(self, projectSettings):
		WriteOutput.__init__(self, projectSettings, "B")

class WriteC(WriteOutput):
	"""Dummy class"""
	supportedArchitectures = {"A", "B", "C", "D"}
	def __init__(self, projectSettings):
		WriteOutput.__init__(self, projectSettings, "C")

class WriteD(WriteOutput):
	"""Dummy class"""
	supportedArchitectures = {"A", "B", "C", "D", "E"}
	def __init__(self, projectSettings):
		WriteOutput.__init__(self, projectSettings, "D")

class WriteWindows(WriteOutput):
	"""Dummy class"""
	supportedArchitectures = {"A", "B", "C", "D"}
	supportedPlatforms = {"Windows"}
	def __init__(self, projectSettings):
		WriteOutput.__init__(self, projectSettings, "Windows")

class WriteLinux(WriteOutput):
	"""Dummy class"""
	supportedArchitectures = {"A", "B", "C", "D"}
	supportedPlatforms = {"Linux"}
	def __init__(self, projectSettings):
		WriteOutput.__init__(self, projectSettings, "Linux")

csbuild.RegisterToolchain("A", "A", WriteA)
csbuild.RegisterToolchain("B", "B", WriteB)
csbuild.RegisterToolchain("C", "C", WriteC)
csbuild.RegisterToolchain("D", "D", WriteD)
csbuild.RegisterToolchain("Windows", "A", WriteWindows)
csbuild.RegisterToolchain("Linux", "A", WriteLinux)

csbuild.SetDefaultToolchain("A")
csbuild.SetDefaultTarget("A")

with csbuild.Target("A"):
	pass

with csbuild.Target("B"):
	pass

with csbuild.Project("AlwaysWorks", "."):
	csbuild.SetOutput("foo", csbuild.ProjectType.Application)

with csbuild.Project("ProjectWithLimitedArchitectures", "."):
	csbuild.SetSupportedArchitectures("A", "B", "C")
	csbuild.SetOutput("arch", csbuild.ProjectType.Application)

with csbuild.Project("ProjectWithExcludedTarget", "."):
	csbuild.SetSupportedTargets("A")
	csbuild.SetOutput("target", csbuild.ProjectType.Application)

with csbuild.Project("ProjectWithSpecialTarget", "."):
	with csbuild.Target("special"):
		csbuild.SetOutput("special", csbuild.ProjectType.Application)
	csbuild.SetOutput("unspecial", csbuild.ProjectType.Application)

with csbuild.Project("LimitedToolchains", "."):
	csbuild.SetSupportedToolchains("B", "C", "D")
	csbuild.SetOutput("toolchain", csbuild.ProjectType.Application)

with csbuild.Project("WindowsProject", "."):
	csbuild.SetSupportedPlatforms("Windows")
	csbuild.SetOutput("Windows", csbuild.ProjectType.Application)

with csbuild.Project("LinuxProject", "."):
	csbuild.SetSupportedPlatforms("Linux")
	csbuild.SetOutput("Linux", csbuild.ProjectType.Application)
