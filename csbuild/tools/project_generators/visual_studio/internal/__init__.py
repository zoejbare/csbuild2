# Copyright (C) 2018 Jaedyn K. Draper
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
.. package:: internal
	:synopsis: Internal functionality for the Visual Studio solution generator.

.. moduleauthor:: Brandon Bare
"""

from __future__ import unicode_literals, division, print_function

from csbuild import log
from csbuild._utils.ordered_set import OrderedSet


# Dictionary of MSVC version numbers to tuples of items needed for the file format.
#   Tuple[0] = Friendly version name for logging output.
#   Tuple[1] = File format version (e.g., "Microsoft Visual Studio Solution File, Format Version XX").
#   Tuple[2] = Version of Visual Studio the solution belongs to (e.g., "# Visual Studio XX").
FILE_FORMAT_VERSION_INFO = {
	100: ("2010", "11.00", "2010"),
	110: ("2012", "12.00", "2012"),
	120: ("2013", "12.00", "2013"),
	140: ("2015", "12.00", "14"),
	141: ("2017", "12.00", "15"),
}

# Set of file extensions to use when determining whether or not a file should be considered a header/include file.
HEADER_FILE_EXTENSIONS = { ".h", ".hh", ".hpp", ".hxx", ".inl", ".inc", ".def" }
