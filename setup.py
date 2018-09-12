from setuptools import setup
import datetime

with open("csbuild/version", "r") as f:
	csbuildVersion = f.read().strip()

setup(
	name = "csbuild",
	version = csbuildVersion,
	packages = ["csbuild"],
	include_package_data = True,
	author = "Jaedyn K. Draper",
	author_email = "jaedyn.pypi@jaedyn.co",
	url = "https://github.com/SleepingCatGames/csbuild2",
	description = "Programming language-agnostic build system",
	long_description = """CSBuild is a language-agnostic build system focused on maximizing developer iteration time and providing tools for enabling developers to improve their build workflow. """,
	classifiers = [
		"Development Status :: 2 - Pre-Alpha",
		"Environment :: Console",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Natural Language :: English",
		"Operating System :: Microsoft :: Windows",
		"Operating System :: MacOS :: MacOS X",
		"Operating System :: POSIX :: Linux",
		"Programming Language :: C",
		"Programming Language :: C++",
		"Programming Language :: Objective C",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3.4",
		"Programming Language :: Python :: 3.5",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"Topic :: Software Development :: Build Tools"
	]
)
