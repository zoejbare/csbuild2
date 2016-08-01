import csbuild
from csbuild.toolchain import Tool
import os

class Doubler(Tool):
	inputFiles = {".first"}

	outputFiles = {".second"}

	def Run(self, project, inputFile):
		with open(inputFile.filename, "r") as f:
			value = int(f.read())
		value *= 2
		outFile = os.path.join(project.intermediateDir, os.path.splitext(os.path.basename(inputFile.filename))[0] + ".second")
		with open(outFile, "w") as f:
			f.write(str(value))
		return outFile

class Adder(Tool):
	inputGroups = {".second"}
	outputFiles = {".third"}

	def RunGroup(self, project, inputFiles):
		value = 0
		for file in inputFiles:
			with open(file.filename, "r") as f:
				value += int(f.read())
		outFile = os.path.join(project.outputDir, project.outputName + ".third")
		with open(outFile, "w") as f:
			f.write(str(value))
		return outFile

csbuild.RegisterToolchain("AddDoubles", "", Doubler, Adder)
csbuild.SetDefaultToolchain("AddDoubles")

with csbuild.Project("TestProject", "."):
	csbuild.SetOutput("Foo", csbuild.ProjectType.Application)

#TODO: Need a way for tests to verify output (likely postBuildStep)
#TODO: Need a way for tests to return specific error messages and failure counts to go into the result xml
