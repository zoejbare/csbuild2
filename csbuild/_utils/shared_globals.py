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
.. module:: shared_globals
	:synopsis: Global variables that need to be accessed by multiple modules

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

from . import dag

errors = []
warnings = []
colorSupported = False
logFile = None

toolchains = {}

sortedProjects = dag.DAG(lambda x: x.name)
allTargets = set()
allToolchains = set()
allArchitectures = set()

runPerfReport = True # Default to true because if we start false, we'll be unable to collect before parsing args.

toolchainGroups = {}

runMode = None

defaultTarget = "release"

parser = None

class Verbosity(object):
	"""
	'enum' representing verbosity
	"""
	Verbose = 0
	Normal = 1
	Quiet = 2
	Mute = 3

#Has to default to Verbose for tests to print Info since they don't take command line params
verbosity = Verbosity.Verbose

showCommands = False

projectMap = {}

projectBuildList = []

commandOutputThread = None

columns = 0
clearBar = ""

startTime = 0

totalBuilds = 0
completedBuilds = 0
