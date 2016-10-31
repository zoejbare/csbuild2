## **Current test status:**

**Test Suite**        | **Status** | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
:-------------------: | :---------------------------------------------------------------------------------------------------------------------------:  | ---
**Linux/Python2.7**   | [![TeamCity](http://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_UnitTests_Python2_Linux)/statusIcon)]()
**Linux/Python3.5**   | [![TeamCity](http://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_UnitTests_Python3_Linux)/statusIcon)]()
**Windows/Python2.7** | [![TeamCity](http://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_UnitTests_Python2_Windows)/statusIcon)]()
**Windows/Python3.5** | [![TeamCity](http://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_UnitTests_Python3_Windows)/statusIcon)]()

<br><br>
CSBuild is a language-agnostic build system focused on maximizing developer iteration time and providing tools for enabling
developers to improve their build workflow. Currently, CSBuild is undergoing a complete rewrite to address some core architecture
issues with the original iteration. It gets closer every day, but hasn't quite reached feature parity with the original CSBuild.

What it currently can do:
- Build basic C++ files for Windows and Linux systems
- Be extended with tools to work in any language (a new feature that old CSBuild did not support)
- Support macro processing in all strings (i.e., SetOutputDirectory("{toolchainName}/{architectureName}/{targetName}"))

What's still missing that exists in old CSBuild:
- OSX, Android, and iOS support
- "Chunking" - intelligently combining multiple translation units into one and breaking them back apart to improve build tunaround
- Solution generation for Visual Studio and QtCreator
- Build GUI showing the progress of individual files and projects as they're build
- Dependency graph generation
- Build profiler to analyze and identify headers and lines of code that are expensive to compile

The core architecture is much more stable and maintainable than old CSBuild's, and tools are easier to implement than
they were before. The new architecture also successfully decouples csbuild from the c++ language, allowing it to be
truly versatile and language-agnostic. The new csbuild also cuts down considerably on wasted time during initial startup.
Now that the majority of the core features have been implemented, we expect feature parity for the tools and target platforms
supported by old CSBuild to start coming online very quickly, shortly followed by solution generation, chunking,
and the gui tools.

Code for old csbuild, for those interested in it, can be found here: https://swarm.workshop.perforce.com/projects/shadauxcat-csbuild/files/mainline/csbuild