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
.. module:: CSBuild
	:synopsis: cross-platform c/c++ build system

.. moduleauthor:: Jaedyn K. Draper, Brandon M. Bare
.. attention:: To support CSBuild's operation, Python's import lock is DISABLED once CSBuild has started.
This should not be a problem for most makefiles, but if you do any threading within your makefile, take note:
anything that's imported and used by those threads should always be implemented on the main thread before that
thread's execution starts. Otherwise, CSBuild does not guarantee that the import will have completed
once that thread tries to use it. Long story short: Don't import modules within threads.
"""

from __future__ import unicode_literals, division, print_function
