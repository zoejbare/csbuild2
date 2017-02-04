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
.. module:: msvc_tool_base
	:synopsis: Abstract base class for msvc tools.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

import csbuild
import os

from abc import ABCMeta
from collections import OrderedDict

from csbuild import log
from ..._utils.decorators import MetaClass
from ..._utils import PlatformString
from ...toolchain import Tool
from ... import commands

def _ignore(_):
	pass

class Vcvarsall(object):
	"""
	Class for maintaining data output by vcvarsall.bat.

	:param binPath: Path to the msvc binaries.
	:type binPath: str

	:param libPaths: List of paths to Windows SDK libraries.
	:type libPaths: list

	:param env: Custom environment dictionary extracted from the vcvarsall.bat output.
	:type env: dict
	"""

	Instances = dict()

	def __init__(self, binPath, libPaths, env):
		self.binPath = binPath
		self.libPaths = libPaths
		self.env = env

@MetaClass(ABCMeta)
class MsvcToolBase(Tool):
	"""
	Parent class for all msvc tools.

	:param projectSettings: A read-only scoped view into the project settings dictionary
	:type projectSettings: toolchain.ReadOnlySettingsView
	"""
	def __init__(self, projectSettings):
		Tool.__init__(self, projectSettings)

		self._msvcVersion = None
		self._vcvarsall = None

	def SetMsvcVersion(self, version):
		"""
		Set the version of msvc to compile with.

		:param version: Msvc version (e.g., "11.0", "12.0", "14.0", etc)
		:type version: str
		"""
		self._msvcVersion = version

	def SetupForProject(self, project):
		Tool.SetupForProject(self, project)
		currentArch = csbuild.GetSystemArchitecture()
		supportedSystemArchs = {
			"x86",
			"x64",
			"arm",
		}

		# Msvc can only be run from a certain set of supported architectures.
		assert currentArch in supportedSystemArchs, \
			'Invalid system architecture "{}"; msvc tools can only be run on the following architectures: {}'.format(currentArch, supportedSystemArchs)

		args = {
			"x64": {
				"x64": "amd64",
				"x86": "amd64_x86",
				"arm": "amd64_arm",
			},
			"x86": {
				"x64": "x86_amd64",
				"x86": "x86",
				"arm": "x86_arm",
			},
			"arm": {
				"x64": None,
				"x86": None,
				"arm": "arm",
			},
		}

		vcvarsArch = args[currentArch][project.architectureName]

		assert vcvarsArch is not None, "Building for {} on {} is unsupported.".format(project.architectureName, currentArch)

		# Only run vcvarsall.bat if we haven't already for the selected architecture.
		if vcvarsArch not in Vcvarsall.Instances:
			msvcVersionMacros = OrderedDict([
				("14.0", "VS140COMNTOOLS"),
				("12.0", "VS120COMNTOOLS"),
				("11.0", "VS110COMNTOOLS"),
				("10.0", "VS100COMNTOOLS"),
			])
			vsVersions = {
				"14.0": "2015",
				"12.0": "2013",
				"11.0": "2012",
				"10.0": "2010",
			}

			msvcMacro = None

			if self._msvcVersion is None:
				# When no version is provided, try to find a version installed, starting with the latest supported.
				for msvcVersion, macroName in msvcVersionMacros.items():
					if macroName in os.environ:
						log.Info("No Visual Studio version specified; defaulting to {}".format(vsVersions[msvcVersion]))
						msvcMacro = macroName
						break
				assert msvcMacro is not None, "Unable to find any supported installation of Visual Studio."
			else:
				# Attempt to resolve the macro using the provided version of Visual Studio.
				msvcMacro = msvcVersionMacros.get(self._msvcVersion, None)
				assert msvcMacro is not None, "Unknown msvc version: {}".format(self._msvcVersion)
				assert msvcMacro in os.environ, "Unable to find installation of Visual Studio {}.".format(vsVersions[self._msvcVersion])

			msvcRootPath = os.path.normpath(os.path.join(os.environ[msvcMacro], "..", "..", "VC" ) )
			vcvarsallFilePath = os.path.join(msvcRootPath, "vcvarsall.bat")

			cmd = [
				vcvarsallFilePath,
				vcvarsArch,
				"&",
				"set",
			]

			def _noLog(shared, msg):
				_ignore(shared)
				_ignore(msg)

			_, output, _ = commands.Run(cmd, stdout=_noLog, stderr=_noLog)
			outputLines = output.splitlines()

			binPath = ""
			libPaths = []
			env = dict()

			for line in outputLines:
				line = PlatformString(line)

				# Skip empty lines.
				if not line:
					continue

				keyValue = line.split("=", 1)
				key = PlatformString(keyValue[0])
				value = PlatformString(keyValue[1])

				env[key] = value
				keyLowered = key.lower()

				if keyLowered == "path":
					# Passing a custom environment to subprocess.Popen() does not always help in locating a command
					# to execute on Windows (seems to be a bug with CreateProcess()), so we still need to find the
					# path where the tools live.
					for envPath in [path for path in value.split(";") if path]:
						if os.access(os.path.join(envPath, "cl.exe"), os.F_OK):
							binPath = PlatformString(envPath)
							break
				elif keyLowered == "lib":
					# Extract the SDK library directory paths.
					libPaths = [PlatformString(path) for path in value.split(";") if path]

			# Memoize the vcvarsall data.
			Vcvarsall.Instances[vcvarsArch] = Vcvarsall(binPath, libPaths, env)

		# Retrieve the memoized data.
		self._vcvarsall = Vcvarsall.Instances[vcvarsArch]
