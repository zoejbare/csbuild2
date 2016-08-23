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
.. module:: tests
	:synopsis: Test to ensure inter-tool dependencies with files not taken as input files work correctly

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

from csbuild._testing.functional_test import FunctionalTest

class ToolDependencyTest(FunctionalTest):
	"""Tool dependency test"""
	# pylint: disable=invalid-name
	def test(self):
		"""Tool dependency test"""
		self.assertMakeSucceeds()
		for i in range(1, 11):
			self.assertFileContents("./intermediate/{}.second".format(i), str(i*3))
			self.assertFileContents("./intermediate/{}.firstcopy".format(i), str(i))
			self.assertFileContents("./intermediate/{}.secondcopy".format(i), str(i*3))
		#This is (1..10) * 6 despite the above assertions counting them seven times
		#Reason for this is that firstcopy is already counted in second and not added into third again
		self.assertFileContents("./out/Foo.third", "330")
