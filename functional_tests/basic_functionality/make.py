import csbuild

with csbuild.Project("hello_world", "./"):
	csbuild.SetOutput("hello_world")
