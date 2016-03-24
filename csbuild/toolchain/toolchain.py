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
.. module:: toolchain
	:synopsis: Mixin class to join tools together

.. moduleauthor:: Jaedyn K. Draper
"""

from __future__ import unicode_literals, division, print_function

from collections import Callable

from . import Tool
from .._utils import PlatformString
from .._zz_testing import testcase

def ToolchainFactory(*classes):
	"""
	Creates a toolchain mixin class from the given list of classes.
	This mixin class has the following special behaviors:

	* If two classes both inherit from the same class, variables initialized in the base class's __init__ will be shared
	  between all subclasses
	* Private functions and data members are specific to the class they're defined in, even if they share a name in
	  two different classes - the code will intelligently call the correct (intended) function based on the location
	  it's called from
	* Public functions will be called as a group - all tools that have a certain function on it will have that function
	  called when the toolchain's function of that name is called.

	:param classes: list of Tool classes
	:type classes: class inherited from Tool
	:return: generated Toolchain class
	:rtype: Toolchain
	"""
	for cls in classes:
		assert issubclass(cls, Tool), "Toolchains must be composed only of classes that inherit from Tool"

	# Keep track of some state data...
	class _classTrackr(object):
		# The last class to have a public function called on it
		# This is used to resolve private function calls and private member variable access - only
		# those elements that exist on this class or its bases will be visible
		lastClass = None

		# List of classes that have had __init__ called on them.
		# Since base class data is shared, we don't want to initialize them more than once
		initialized = set()

		# Limited class lookup table. When non-empty, only classes in this set will be
		# visible when performing member lookups
		limit = set()

		# List of inits that are already overloaded so we don't wrap them multiple times
		overloadedInits = set()

	# Replace each class's __init__ function with one that will prevent double-init
	# and will ensure that _classTrackr.lastClass is set properly so that variables
	# initialize with the correct visibility
	def _setinit(base):
		# Use a variable on the function to prevent us from wrapping this over and over
		if base.__init__ not in _classTrackr.overloadedInits:
			oldinit = base.__init__

			def _initwrap(self):
				# Don't re-init if already initialized
				if base not in _classTrackr.initialized:
					_classTrackr.initialized.add(base)
					# Track the current class for __setattr__
					oldLastClass = _classTrackr.lastClass
					_classTrackr.lastClass = base
					oldinit(self)
					_classTrackr.lastClass = oldLastClass

			# Replace existing init and set the memoization value
			base.__init__ = _initwrap
			_classTrackr.overloadedInits.add(base.__init__)

	# Collect a list of all the base classes
	bases = set()
	for cls in classes:
		# mro() - "method resolution order", which happens to also be a list of all classes in the inheritance
		# tree, including the class itself (but we only care about its base classes
		for base in cls.mro():
			if base is cls:
				continue
			if base is Tool:
				break
			# Replace the base class's __init__ so we can track members properly
			_setinit(base)
			bases.add(base)

	# Set up a map of class to member variable dict
	# All member variables will be stored here instead of in the class's __dict__
	# This is what allows for both sharing of base class values, and separation of
	# derived class values that share the same name, so they don't overwrite each other
	classValues = {cls : {} for cls in set(classes) | bases}


	def _init(self):
		# Initialize all dynamically created bases.
		for cls in classes:
			oldLastClass = _classTrackr.lastClass
			_classTrackr.lastClass = cls
			cls.__init__(self)
			_classTrackr.lastClass = oldLastClass
		_classTrackr.lastClass = None

	def _setattr(_, name, val):
		# Because public data is wrapped and combined, but private data is kept separate, classes should never
		# try and SET public data. They should only set private data and provide a public accessor or property
		# to retrieve it if necessary (though it's unlikely tools will ever need to provide data back
		# to a makefile)
		assert name.startswith("_"), "Tool instance attributes must start with an underscore"

		# Likewise because we have to keep a clear separation of which data belongs to who, disallow
		# access to this private data when we don't have a view of who owns it. We only have that view
		# while executing a public method of a class.
		assert _classTrackr.lastClass, "Cannot access private tool data from outside tool class"

		cls = _classTrackr.lastClass

		# Iterate all the base classes until we find one that's already set this value.
		# If we don't find one that's set this value, this value is being initialized and should
		# be placed within the scope of the class that's initializing it. That class and its children
		# will then be able to see it, but its bases and siblings (classes that share a common base)
		# will not.
		for base in _classTrackr.lastClass.mro():
			if base == Tool:
				break
			if name in classValues[base]:
				cls = base
		classValues[cls][name] = val

	def _getattr(self, name):
		if name == "Tool":
			# Tool is a special function for toolchain.
			# This function returns a LimitView class that limits operations
			# to only affecting a specific tool or set of tools.
			obj = self

			# Create a class so that we can call methods on that class
			class LimitView(object):
				"""Represents a limited view into a toolchain"""
				# The constructor takes the list of tools to limit to - i.e., toolchain.Tool(SomeClass, OtherClass)
				def __init__(self, *tools):
					self.tools = set(tools)

				# When asked for an attribute, set the class tracker's limit set and then retrieve the attribute
				# from the toolchain class (this class) that generated the LimitView. Resolution will be limited
				# to the tools provided above.
				def __getattr__(self, item):
					def _limit(*args, **kwargs):
						_classTrackr.limit = self.tools
						getattr(obj, item)(*args, **kwargs)
						_classTrackr.limit = set()
					_limit.__name__ = item
					return _limit
			return LimitView

		if name.startswith("_") and not name.startswith("__"):
			# For private variables, as mentioned above, we have to know the scope we're looking in.
			assert _classTrackr.lastClass, "Cannot access private tool data from outside tool class"

			# Iterate the class's mro looking for the first one that has this name present for it.
			# This starts with the class itself and then goes through its bases
			for cls in _classTrackr.lastClass.mro():
				if cls == Tool:
					break
				if name in classValues[cls]:
					return classValues[cls][name]

			# If we didn't find it there, then look for it on the class itself
			# This is either a function, method, or static variable, not an instance variable.
			# Would love to guarantee this is a function...
			# But for some reason python lets you access statics through self, so whatever...
			if hasattr(_classTrackr.lastClass, name):
				val = getattr(_classTrackr.lastClass, name)
				if isinstance(val, Callable):
					def _runPrivateFunc(*args, **kwargs):
						return val(self, *args, **kwargs)
					return _runPrivateFunc
				else:
					return val

			# If we didn't find it, delegate to the normal attribute location method.
			# For 99.9% of cases this means "throw an AttributeError" but we're letting
			# python's internals do that
			return object.__getattribute__(self, name)
		else:
			# For public variables we want to return a wrapper function that calls all
			# matching functions. This should definitely be a function. If it's not a function,
			# things will not work.
			def _runMultiFunc(*args, **kwargs):
				calledSomething = False
				functions = {}

				# Iterate through all classes and collect functions that match this name
				# We'll keep a list of all the functions that match, but only call each matching
				# function once. And when we call it we'll use the most base class we find that
				# has it - which should be the one that defined it - and only call each one once
				# (so if there are two subclasses of a base that base's functions won't get called twice)
				for cls in classes:
					if _classTrackr.limit and cls not in _classTrackr.limit:
						continue
					if hasattr(cls, name):
						func = getattr(cls, name)
						if func not in functions or issubclass(functions[func], cls):
							functions[func] = cls
						calledSomething = True

				# Having collected all functions, iterate and call them
				for func, cls in functions.items():
					oldLastClass = _classTrackr.lastClass
					_classTrackr.lastClass = cls
					func(self, *args, **kwargs)
					_classTrackr.lastClass = oldLastClass

				_classTrackr.lastClass = None

				# Finding one tool without this function present on it is not an error.
				# However, if no tools had this function, that is an error - let python internals
				# throw us an AttributeError
				if not calledSomething:
					return object.__getattribute__(self, name)
			return _runMultiFunc

	return type(PlatformString("Toolchain"), classes, {"__init__":_init, "__setattr__":_setattr, "__getattribute__":_getattr})()


class TestToolchainMixin(testcase.TestCase):
	"""Test the toolchain mixin"""
	# pylint: disable=invalid-name

	def setUp(self):
		"""Test the toolchain mixin"""
		# pylint: disable=missing-docstring

		self.maxDiff = None

		class _sharedLocals(object):
			doBaseThingCalledInBase = 0
			doBaseThing2CalledInBase = 0
			overloadFnCalledInBase = 0
			overloadFnCalledInDerived1 = 0
			overloadFnCalledInDerived2 = 0
			setSomeValCalledInBase = 0
			baseInternalThingCalledInBase = 0
			basePrivateThingCalledInBase = 0
			derived1AccessSomeValResult = None
			derived1AccessTestResult = None
			derived2AccessSomeValResult = None
			derived2AccessTestResult = None
			derived1PrivateThingCalled = 0
			derived1SameNameThingCalled = 0
			derived2PrivateThingCalled = 0
			derived2SameNameThingCalled = 0
			doDerived1ThingCalled = 0
			doDerived2ThingCalled = 0
			doBaseThingCalledInDerived2 = 0
			baseInternalThingCalledInDerived1 = 0
			basePrivateThingCalledInDerived2 = 0
			doMultiThingCalledInDerived1 = 0
			doMultiThingCalledInDerived2 = 0


		class _base(Tool):
			def __init__(self):
				self._someval = 0

			def Run(self, *args):
				pass

			def DoBaseThing(self):
				_sharedLocals.doBaseThingCalledInBase += 1

			def DoBaseThing2(self):
				_sharedLocals.doBaseThing2CalledInBase += 1

			def OverloadedFn(self):
				_sharedLocals.overloadFnCalledInBase += 1

			def SetSomeVal(self):
				_sharedLocals.setSomeValCalledInBase += 1
				self._someval = 12345

			def _baseInternalThing(self):
				_sharedLocals.baseInternalThingCalledInBase += 1

			def _basePrivateThing(self):
				self._baseInternalThing()
				_sharedLocals.basePrivateThingCalledInBase += 1


		class _derived1(_base):
			def __init__(self):
				self._test = 1
				_base.__init__(self)

			def Derived1CallInternals(self):
				self._basePrivateThing()
				self._derived1PrivateThing()
				self._sameNamePrivateThing()

			def Derived1AccessSomeVal(self):
				_sharedLocals.derived1AccessSomeValResult = self._someval
				_sharedLocals.derived1AccessTestResult = self._test

			def OverloadedFn(self):
				_sharedLocals.overloadFnCalledInDerived1 += 1

			def _baseInternalThing(self):
				_sharedLocals.baseInternalThingCalledInDerived1 += 1

			def _derived1PrivateThing(self):
				_sharedLocals.derived1PrivateThingCalled += 1

			def _sameNamePrivateThing(self):
				_sharedLocals.derived1SameNameThingCalled += 1

			def DoDerived1Thing(self):
				_sharedLocals.doDerived1ThingCalled += 1

			def DoMultiThing(self):
				_sharedLocals.doMultiThingCalledInDerived1 += 1

		class _derived2(_base):
			def __init__(self):
				self._test = 2
				_base.__init__(self)

			def Derived2CallInternals(self):
				self._basePrivateThing()
				self._derived2PrivateThing()
				self._sameNamePrivateThing()

			def Derived2AccessSomeVal(self):
				_sharedLocals.derived2AccessSomeValResult = self._someval
				_sharedLocals.derived2AccessTestResult = self._test

			def OverloadedFn(self):
				_sharedLocals.overloadFnCalledInDerived2 += 1

			def DoBaseThing(self):
				_sharedLocals.doBaseThingCalledInDerived2 += 1

			def Derived2SetSomeVal(self):
				self._someval = 54321

			def _basePrivateThing(self):
				self._baseInternalThing()
				_sharedLocals.basePrivateThingCalledInDerived2 += 1

			def _derived2PrivateThing(self):
				_sharedLocals.derived2PrivateThingCalled += 1

			def _sameNamePrivateThing(self):
				_sharedLocals.derived2SameNameThingCalled += 1

			def DoDerived2Thing(self):
				_sharedLocals.doDerived2ThingCalled += 1

			def DoMultiThing(self):
				_sharedLocals.doMultiThingCalledInDerived2 += 1

		self.expectedState = {key: val for key, val in _sharedLocals.__dict__.items() if not key.startswith("_")}
		self.mixin = ToolchainFactory(_derived1, _derived2)
		self._sharedLocals = _sharedLocals
		self._derived1 = _derived1
		self._derived2 = _derived2
		self._base = _base

	def assertChanged(self, **kwargs):
		"""Assert that the listed changes (and ONLY the listed changes) have occurred in the state dict"""
		#Set the expected changes on our expected state and assert that the changed expected state
		#(including the previous values in that state) matches the actual state
		for key, val in kwargs.items():
			self.assertNotEqual(self.expectedState[key], val)
		self.expectedState.update(kwargs)
		actualState = {key: val for key, val in self._sharedLocals.__dict__.items() if not key.startswith("_")}
		self.assertEqual(self.expectedState, actualState)

	def testPrivateFunctionCalls(self):
		"""Test that internal private function calls work with a variety of inheritance scenarios"""
		# Call internal functions on derived 1
		# This should call _basePrivateThing on the base class and _baseInternalThing on the child
		# And it should call Derived1PrivateThing on Derived1
		# And it should call the function named _sameNamePrivateThing defined in Derived1, but NOT the one defined in Derived2
		self.mixin.Derived1CallInternals()

		self.assertChanged(
			basePrivateThingCalledInBase=1,
			derived1PrivateThingCalled=1,
			derived1SameNameThingCalled=1,
			baseInternalThingCalledInDerived1=1
		)

		# Call internal functions on derived 2
		# This should call _basePrivateThing on the derived class and _baseInternalThing on the base
		# And it should call Derived2PrivateThing on Derived2
		# And it should call the function named _sameNamePrivateThing defined in Derived2, but NOT the one defined in Derived1
		self.mixin.Derived2CallInternals()

		self.assertChanged(
			baseInternalThingCalledInBase=1,
			derived2PrivateThingCalled=1,
			derived2SameNameThingCalled=1,
			basePrivateThingCalledInDerived2=1
		)

	def testMultiFunctionCall(self):
		"""Test that calling a function with multiple implementations calls all implementations"""
		# This should call the functioned defined on the base class by way of Derived1
		# as well as the overload defined on Derived2
		self.mixin.DoBaseThing()

		self.assertChanged(
			doBaseThingCalledInBase=1,
			doBaseThingCalledInDerived2=1
		)

	def testFunctionCallDeduplication(self):
		"""Test that a given function implementation is only called once"""
		# This should call DoBaseThing2 on the base class and should only call it ONCE
		self.mixin.DoBaseThing2()

		self.assertChanged(
			doBaseThing2CalledInBase=1
		)

	def testBaseClassFunctionNotCalledIfOverloaded(self):
		"""Test that a base class implementation is not called if all derived classes override it"""
		# This should call the overloaded functions on both Derived1 and Derived2 and should NOT call the base implementation
		self.mixin.OverloadedFn()

		self.assertChanged(
			overloadFnCalledInDerived1=1,
			overloadFnCalledInDerived2=1
		)

	def testAccessSharedData(self):
		"""Test that accessing data initialized by the base class accesses shared data, and
		that accessing data initialized by the child class is isolated from other classes using the same name"""
		# This should access self._someVal and self._test in Derived1 as set up by their constructors
		# self._test should be 1 because it should see the Derived1 instance of it, and not the Derived2 instance
		self.mixin.Derived1AccessSomeVal()

		self.assertChanged(
			derived1AccessSomeValResult=0,
			derived1AccessTestResult=1
		)

		# This should access self._someVal and self._test in Derived2 as set up by their constructors
		# self._test should be 2 because it should see the Derived2 instance of it, and not the Derived1 instance
		self.mixin.Derived2AccessSomeVal()

		self.assertChanged(
			derived2AccessSomeValResult=0,
			derived2AccessTestResult=2
		)

	def testChangeSharedDataInBase(self):
		"""Test that changes to shared data by the base class are seen by all children"""
		# Set self._someVal to 12345 in the base class. This should affect both child classes
		self.mixin.SetSomeVal()

		self.assertChanged(
			setSomeValCalledInBase=1,
		)

		# Access values again via Derived1. self.someVal should be 12345 now.
		self.mixin.Derived1AccessSomeVal()

		self.assertChanged(
			derived1AccessSomeValResult=12345,
			derived1AccessTestResult=1,
		)

		# Access values again via Derived2. Just like with Derived1, self.someVal should be 12345 now.
		self.mixin.Derived2AccessSomeVal()

		self.assertChanged(
			derived2AccessSomeValResult=12345,
			derived2AccessTestResult=2,
		)

	def testChangeSharedDataInDerived(self):
		"""Test that changes to shared data by a derived class are seen by other derived classes"""
		# Set SomeVal by way of Derived2, which despite being a child class should still set the base class instance
		self.mixin.Derived2SetSomeVal()

		# Access values again via Derived1. self.someVal should be 54321 now as set by Derived2.
		self.mixin.Derived1AccessSomeVal()

		self.assertChanged(
			derived1AccessSomeValResult=54321,
			derived1AccessTestResult=1,
		)

		# Access values again via Derived2. Just like with Derived1, self.someVal should be 54321 now.
		self.mixin.Derived2AccessSomeVal()

		self.assertChanged(
			derived2AccessSomeValResult=54321,
			derived2AccessTestResult=2,
		)

	def testFunctionsImplementedOnlyInOneClass(self):
		"""Test that functions work correctly even if not all tools support it"""
		# Call a function defined only in Derived1 and not in the base class
		self.mixin.DoDerived1Thing()

		self.assertChanged(
			doDerived1ThingCalled=1,
		)

		# Call a function defined only in Derived2 and not in the base class
		self.mixin.DoDerived2Thing()

		self.assertChanged(
			doDerived2ThingCalled=1,
		)

	def testLimitByTool(self):
		"""Test that the Tool() function correctly limits a function call to only the specified tools"""
		# Call a function defined in both Derived1 and Derived2, but only call the Derived2 version
		self.mixin.Tool(self._derived2).DoMultiThing()

		self.assertChanged(
			doMultiThingCalledInDerived2=1,
		)

		# Call a function defined in both Derived1 and Derived2, but only call the Derived1 version
		self.mixin.Tool(self._derived1).DoMultiThing()

		self.assertChanged(
			doMultiThingCalledInDerived1=1,
		)

		# Call a function defined in both Derived1 and Derived2, and this time call both versions to verify
		# that multiple arguments to Tool works as expected
		self.mixin.Tool(self._derived1, self._derived2).DoMultiThing()

		self.assertChanged(
			doMultiThingCalledInDerived1=2,
			doMultiThingCalledInDerived2=2,
		)

		# Call a function defined in both Derived1 and Derived2, and this time call them both without going through Tool()
		self.mixin.DoMultiThing()

		self.assertChanged(
			doMultiThingCalledInDerived1=3,
			doMultiThingCalledInDerived2=3,
		)
