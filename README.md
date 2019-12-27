## **Current test status:**

**Test Suite**            | **Status (master)** | **Status (develop)**
:-----------------------: | :-----------------: | :------------------:
**Linux/Python 2.7.12**   | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_LinuxPython2),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_LinuxPython2&branch_Csbuild=master&guest=1)       | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_LinuxPython2),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_LinuxPython2&branch_Csbuild=develop&guest=1)
**Linux/Python 3.5.2**    | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_LinuxPython3),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_LinuxPython3&branch_Csbuild=master&guest=1)       | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_LinuxPython3),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_LinuxPython3&branch_Csbuild=develop&guest=1)
**macOS/Python 2.7.12**   | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_MacOSPython2),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_MacOSPython2&branch_Csbuild=master&guest=1)       | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_MacOSPython2),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_MacOSPython2&branch_Csbuild=develop&guest=1)
**macOS/Python 3.5.2**    | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_MacOSPython3),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_MacOSPython3&branch_Csbuild=master&guest=1)       | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_MacOSPython3),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_MacOSPython3&branch_Csbuild=develop&guest=1)
**Windows/Python 2.7.12** | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython27),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython27&branch_Csbuild=master&guest=1) | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython27),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython27&branch_Csbuild=develop&guest=1)
**Windows/Python 3.4.4**  | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython34),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython34&branch_Csbuild=master&guest=1) | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython34),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython34&branch_Csbuild=develop&guest=1)
**Windows/Python 3.5.3**  | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython35),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython35&branch_Csbuild=master&guest=1) | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython35),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython35&branch_Csbuild=develop&guest=1)
**Windows/Python 3.6.1**  | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython36),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython36&branch_Csbuild=master&guest=1) | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython36),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython36&branch_Csbuild=develop&guest=1)
**Windows/Python 3.7.0**  | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython37),branch:(master)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython37&branch_Csbuild=master&guest=1) | [![TeamCity](https://dev.aegresco.com/teamcity/app/rest/builds/buildType:(id:Csbuild_WindowsPython37),branch:(develop)/statusIcon)](https://dev.aegresco.com/teamcity/viewType.html?buildTypeId=Csbuild_WindowsPython37&branch_Csbuild=develop&guest=1)

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
- "Chunking" - intelligently combining multiple translation units into one and breaking them back apart to improve build turn-around
- Solution generation for Visual Studio and QtCreator
- Build GUI showing the progress of individual files and projects as they're build
- Dependency graph generation
- Build profiler to analyze and identify headers and lines of code that are expensive to compile
- Full whitelisting and blacklisting support for adding and excluding files and directories to projects

The core architecture is much more stable and maintainable than old CSBuild's, and tools are easier to implement than
they were before. The new architecture also successfully decouples csbuild from the c++ language, allowing it to be
truly versatile and language-agnostic. The new csbuild also cuts down considerably on wasted time during initial startup.
Now that the majority of the core features have been implemented, we expect feature parity for the tools and target platforms
supported by old CSBuild to start coming online very quickly, shortly followed by solution generation, chunking,
and the gui tools.

Code for old csbuild, for those interested in it, can be found here: https://github.com/SleepingCatGames/csbuild
