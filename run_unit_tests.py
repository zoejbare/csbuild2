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
.. module:: run_unit_tests
	:synopsis: Execute this file directly to run the unit tests.
"""

from __future__ import unicode_literals, division, print_function


if __name__ == "__main__":
	import os
	import sys
	import glob
	import subprocess
	from xml.etree import ElementTree
	from xml.dom import minidom
	import time

	# Copied from csbuild._utils because we can't import that before we set environ, and we need this to do that
	if sys.version_info[0] >= 3:
		def PlatformString(inputStr):
			"""In the presence of unicode_literals, get an object that is type str in both python2 and python3."""
			if isinstance(inputStr, str):
				return inputStr
			return inputStr.decode("UTF-8")
	else:
		def PlatformString(inputStr):
			"""In the presence of unicode_literals, get an object that is type str in both python2 and python3."""
			if isinstance(inputStr, str):
				return inputStr
			return inputStr.encode("UTF-8")

	os.environ[PlatformString("CSBUILD_NO_AUTO_RUN")] = PlatformString("1")
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	from csbuild._zz_testing.run_unit_tests import RunTests
	from csbuild._utils import log

	totalret = RunTests()

	root = ElementTree.Element("testsuites")
	add = ElementTree.SubElement

	del os.environ[PlatformString("CSBUILD_NO_AUTO_RUN")]
	os.environ[PlatformString("PYTHONPATH")] = os.pathsep.join(sys.path)
	functionalTests = glob.glob(os.path.join("functional_tests", "*", "make.py"))
	for test in functionalTests:
		suiteName = os.path.basename(os.path.dirname(test))
		print("\n")
		log.Test("==================================================")
		log.Test("RUNNING FUNCTIONAL TEST: {}", suiteName)
		log.Test("==================================================")
		print("")
		start = time.time()

		argsPath = os.path.join(os.path.dirname(test), "args")
		execstr = "{} {}".format(sys.executable, test)
		if os.path.exists(argsPath):
			with open(argsPath, "r") as f:
				execstr += " " + f.read()
		ret = subprocess.call(execstr, shell=True)
		if ret != 0:
			totalret += ret

		suiteTime = time.time() - start

		suite = add(
			root,
			"testsuite",
			name = suiteName,
			tests="functional.{}".format(suiteName),
			errors=str(ret),
			failures=str(ret),
			skipped="0",
			time="{:.3f}".format(suiteTime)
		)

		case = add(suite, "testcase", classname="{}.{}".format(suiteName, "run"), name="Functional test: {}".format(suiteName), time="{:.3f}".format(suiteTime))
		if ret != 0:
			add(case, "failure").text = "Functional test {} returned exit code {}".format(suiteName, ret)
		print("")
		log.Test("==================================================")

	with open("functional_tests.xml", "w") as f:
		f.write(minidom.parseString(ElementTree.tostring(root)).toprettyxml("\t", "\n"))

	sys.exit(totalret)

