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
import sys
import types

from .._utils import StrType, BytesType
from .._utils.decorators import TypeChecked

if sys.version_info[0] >= 3:
	_typeType = type
	_classType = type
else:
	# pylint: disable=invalid-name
	_typeType = types.TypeType
	_classType = types.ClassType

class NestedContext(object):
	"""
	Represents a nested context, allowing context managers to be chained, a la csbuild.Toolchain("foo").Architecture("bar")

	:param cls: The ContextManager being nested
	:type cls: ContextManager
	:param currentContext: The ContextManager it's being nested into
	:type currentContext: ContextManager
	"""
	def __init__(self, cls, currentContext):
		self.cls = cls
		self.ctx = currentContext

	def __call__(self, *args, **kwargs):
		ret = self.cls(*args, **kwargs)
		# pylint: disable=protected-access
		ret._parentContext = self.ctx
		return ret

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

	methodResolvers = []

	@TypeChecked(contextType=(StrType, BytesType, type(None)), contextNames=tuple, methodResolvers=list)
	def __init__(self, contextType, contextNames, methodResolvers=None):
		object.__setattr__(self, "inself", True)
		self._type = contextType
		self._names = contextNames
		self._methodResolvers = methodResolvers
		self._previousResolver = None
		self._parentContext = None
		object.__setattr__(self, "inself", False)

	def __enter__(self):
		"""
		Enter the context, making the listed contexts active
		"""
		object.__setattr__(self, "inself", True)
		if self._parentContext is not None:
			object.__getattribute__(self._parentContext, "__enter__")()
		if self._type is not None:
			csbuild.currentPlan.EnterContext(self._type, *self._names)

		if self._methodResolvers:
			ContextManager.methodResolvers.append(self._methodResolvers)

		# pylint: disable=protected-access
		self._previousResolver = csbuild._resolver
		csbuild._resolver = self
		object.__setattr__(self, "inself", False)

	def __exit__(self, excType, excValue, traceback):
		"""
		Leave the context

		:param excType: type of exception thrown in the context (ignored)
		:type excType: type
		:param excValue: value of thrown exception (ignored)
		:type excValue: any
		:param traceback: traceback attached to the thrown exception (ignored)
		:type traceback: traceback
		:return: Always false
		:rtype: bool
		"""
		object.__setattr__(self, "inself", True)
		# pylint: disable=protected-access
		csbuild._resolver = self._previousResolver

		if self._methodResolvers:
			ContextManager.methodResolvers.pop()

		if self._type is not None:
			csbuild.currentPlan.LeaveContext()

		if self._parentContext is not None:
			object.__getattribute__(self._parentContext, "__exit__")(excType, excValue, traceback)

		object.__setattr__(self, "inself", False)
		return False

	def __getattribute__(self, name):
		if object.__getattribute__(self, "inself"):
			return object.__getattribute__(self, name)

		if ContextManager.methodResolvers:
			funcs = set()

			numResolvers = 0
			for resolverList in ContextManager.methodResolvers:
				for resolver in resolverList:
					numResolvers += 1
					if hasattr(resolver, name):
						funcs.add(getattr(resolver, name))

			if funcs and len(funcs) != numResolvers:
				for resolverList in ContextManager.methodResolvers:
					for resolver in resolverList:
						# If we didn't get a valid result for all resolvers, do getattr on each without a guard
						# to force an appropriate exception to be thrown.
						getattr(resolver, name)

			if funcs:
				def _wrapResolverMethods(*args, **kwargs):
					with self:
						for func in funcs:
							func(*args, **kwargs)

				return _wrapResolverMethods

		if hasattr(csbuild, name):
			obj = getattr(csbuild, name)
			if isinstance(obj, types.FunctionType):
				def _wrapCsbuildMethod(*args, **kwargs):
					with self:
						obj(*args, **kwargs)

				return _wrapCsbuildMethod
			else:
				if (isinstance(obj, _classType) or isinstance(obj, _typeType)) and issubclass(obj, ContextManager):
					return NestedContext(obj, self)
				return obj

		return object.__getattribute__(self, name)
