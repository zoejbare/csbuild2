
.text

#ifdef IS_PLATFORM_MACOS

; MacOS function name
.global _getnum
_getnum:

#else

; Linux function name
.global getnum
getnum:

#endif

	; Move the integer value "4" into the output register.
#ifdef IS_ARCH_X86
	mov $4, %eax
#else
	mov $4, %rax
#endif

	ret
