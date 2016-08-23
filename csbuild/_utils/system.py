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
.. module:: system
	:synopsis: functions with functionality analogous to the sys module, but specialized for csbuild

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import imp
import os
import csbuild
import sys
import platform

from . import shared_globals
from .. import log

if platform.system() == "Windows":
	def SyncDir(_):
		"""
		Synchronize a directory to ensure its contents are visible to other applications.
		Does nothing on Windows.
		:param _: Directory name
		:type _: str
		"""
		pass
else:
	def SyncDir(dirname):
		"""
		Synchronize a directory to ensure its contents are visible to other applications.
		Does nothing on Windows.
		:param dirname: Directory name
		:type dirname: str
		"""
		dirfd = os.open(dirname, os.O_DIRECTORY)
		os.fsync(dirfd)
		os.close(dirfd)

def Exit(code = 0):
	"""
	Exit the build process early

	:param code: Exit code to exit with
	:type code: int
	"""

	if not imp.lock_held():
		imp.acquire_lock()

	sys.meta_path = []

	if shared_globals.runMode == csbuild.RunMode.Normal:
		log.Build("Cleaning up")

	for proj in shared_globals.projectBuildList:
		if proj.artifactsFile is not None:
			proj.artifactsFile.flush()
			os.fsync(proj.artifactsFile.fileno())
			proj.artifactsFile.close()

			SyncDir(os.path.dirname(proj.artifactsFileName))

	if not imp.lock_held():
		imp.acquire_lock()

	# TODO: Kill running subprocesses
	# TODO: Exit events for plugins

	# Die hard, we don't need python to clean up and we want to make sure this exits.
	# sys.exit just throws an exception that can be caught. No catching allowed.
	# pylint: disable=protected-access
	os._exit(code)
