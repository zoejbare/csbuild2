#pragma once

#ifdef _WIN32
#	ifdef CSB_SHARED_LIBRARY
#		define EXPORT __declspec(dllexport)
#	else
#		define EXPORT __declspec(dllimport)
#	endif
#else
#	define EXPORT
#endif

EXPORT void goodbye_world();
