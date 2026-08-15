#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

#include "generated_pid_controller_struct.h"

#include "generated_pid_controller_initializer.h"

void bytes_to_hex(const void *data, size_t len, char *out)
{
	static const char hex[] = "0123456789ABCDEF";
	const uint8_t *p = (const uint8_t *)data;

	for (size_t i = 0; i < len; ++i)
	{
		out[2 * i] = hex[p[i] >> 4];
		out[2 * i + 1] = hex[p[i] & 0x0F];
	}
	out[2 * len] = '\0';
}

int main()
{
	/*
	Dump pid_controller structure as binary blob
	*/
	char hexbuf[4096];
	bytes_to_hex(&pid_controller, sizeof(pid_controller), hexbuf);
	printf(">0x%s<\n", hexbuf);

	/*
	Print out some variables.
	Note: Code completion.
	Note: Help text when hovering.
	Note: Failures when variable names change.
	*/
	fprintf(stderr, "name='%s', value=%d, i_param=%f\n", pid_controller.name, pid_controller.value, pid_controller.i_param);

	return 0;
}