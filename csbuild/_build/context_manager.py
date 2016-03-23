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
.. module:: context_manager
	:synopsis: base context manager class

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

import csbuild
from types import FunctionType

from .._utils import StrType, BytesType

from .project_plan import currentPlan
from .._utils.decorators import TypeChecked

class ContextManager(object):
	"""
	Base type for a context manager, used to set context for project plan settings
	:param contextType: The type of context to manage
	:type contextType: str, bytes
	:param contextNames: list of contexts to activate within this manager's scope
	:type contextNames: tuple(str, bytes)
	:param methodResolvers: List of objects on which to look for additional methods for, i.e., csbuild.Toolchain("tc").ToolchainSpecificFunction()
	:type methodResolvers: list(objects)
	"""

	@TypeChecked(contextType=(StrType, BytesType), contextNames=tuple, methodResolvers=list)
	def __init__(self, contextType, contextNames, methodResolvers=None):
		self._type = contextType
		self._names = contextNames
		self._methodResolvers = methodResolvers

	def __enter__(self):
		"""
		Enter the context, making the listed contexts active
		"""
		currentPlan.EnterContext(self._type, self._names)
		# pylint: disable=protected-access
		csbuild._resolver = self

	def __exit__(self, excType, excValue, traceback):
		"""
		Leave the context

		:param excType: type of exception thrown in the context (ignored)
		:type excType: type
		:param excValue: value of thrown exception (ignored)
		:type excValue: any
		:param traceback: traceback attached to the thrown exception (ignored)
		:type traceback: traceback
		"""
		# pylint: disable=protected-access
		csbuild._resolver = None
		currentPlan.LeaveContext()
		return False

	def __getattribute__(self, name):
		funcs = []

		for resolver in self._methodResolvers:
			if hasattr(resolver, name):
				funcs.append(getattr(resolver, name))

		if funcs and len(funcs) != len(self._methodResolvers):
			for resolver in self._methodResolvers:
				getattr(resolver, name)

		if funcs:
			def _wrap(*args, **kwargs):
				with self:
					for func in funcs:
						currentPlan.AppendList("commandList", (func, args, kwargs))

			return _wrap

		elif hasattr(csbuild, name):
			obj = getattr(csbuild, name)
			if isinstance(obj, FunctionType):
				def _wrap(*args, **kwargs):
					with self:
						obj(*args, **kwargs)

				return _wrap

		return object.__getattribute__(self, name)
