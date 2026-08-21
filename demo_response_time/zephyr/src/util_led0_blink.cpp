#include "util_led0_blink.hpp"

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_DECLARE(app, LOG_LEVEL_INF);

#define LED0_NODE DT_ALIAS(led0)

#if !DT_NODE_HAS_STATUS(LED0_NODE, okay)
#error "led0 alias missing or disabled"
#endif

namespace {

static const struct gpio_dt_spec gpio_led0 = GPIO_DT_SPEC_GET(LED0_NODE, gpios);

#define LED_BLINK_STACK_SIZE 512
#define LED_BLINK_PRIORITY 5
K_THREAD_STACK_DEFINE(led_blink_stack, LED_BLINK_STACK_SIZE);
static struct k_thread led_blink_thread;

static void led0_thread_entry(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	while (1) {
		(void)gpio_pin_toggle_dt(&gpio_led0);
		k_sleep(K_MSEC(500));
	}
}

} // namespace


int util_led0_blink_init()
{
	if (!device_is_ready(gpio_led0.port)) {
		LOG_ERR("LED 0 device not ready");
		return -ENODEV;
	}

	const int ret = gpio_pin_configure_dt(&gpio_led0, GPIO_OUTPUT_INACTIVE);
	if (ret != 0) {
		LOG_ERR("LED 0 configure failed: %d", ret);
		return ret;
	}

	k_thread_create(&led_blink_thread,
			led_blink_stack,
			K_THREAD_STACK_SIZEOF(led_blink_stack),
			led0_thread_entry,
			nullptr,
			nullptr,
			nullptr,
			LED_BLINK_PRIORITY,
			0,
			K_NO_WAIT);

	LOG_INF("LED 0 blink thread ready (interval: 500 ms)");

	return 0;
}
