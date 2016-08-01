import csbuild
from csbuild.toolchain import Tool

class NullClass(Tool):
	pass

csbuild.RegisterToolchain("msvc", "dummy", NullClass)
csbuild.RegisterToolchain("gcc", "dummy", NullClass)

with csbuild.Project("hello_world_2", "./", ["hello_world"]):
	with csbuild.Target("debug"):
		csbuild.SetOutput("hello_world_2_debug")

	with csbuild.Target("release"):
		csbuild.SetOutput("hello_world_2")

with csbuild.Project("hello_world", "./"):
	with csbuild.Target("debug"):
		csbuild.SetOutput("hello_world_debug")

	csbuild.SetOutput("hello_world")
