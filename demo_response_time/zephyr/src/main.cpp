#include "util_gpio_response.hpp"
#include "util_led0_blink.hpp"

#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(app, LOG_LEVEL_INF);

int main(void)
{
	int ret = util_gpio_response_init();
	if (ret != 0) {
		return ret;
	}

	ret = util_led0_blink_init();
	if (ret != 0) {
		return ret;
	}

	return 0;
}
