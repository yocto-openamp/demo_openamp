#include "util_gpio_response.hpp"

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_DECLARE(app, LOG_LEVEL_INF);

#define ZEPHYR_USER_NODE DT_PATH(zephyr_user)

#if !DT_NODE_EXISTS(ZEPHYR_USER_NODE)
#error "Missing zephyr,user devicetree node"
#endif

#if !DT_NODE_HAS_STATUS(ZEPHYR_USER_NODE, okay)
#error "zephyr,user devicetree node is disabled"
#endif

#if !DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, gpio_direct_in_gpios)
#error "gpio_direct_in_gpios alias missing"
#endif

#if !DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, gpio_direct_out_gpios)
#error "gpio_direct_out_gpios alias missing"
#endif

#define GPIO_DIRECT_IN_CTLR DT_GPIO_CTLR(ZEPHYR_USER_NODE, gpio_direct_in_gpios)
#define GPIO_DIRECT_OUT_CTLR DT_GPIO_CTLR(ZEPHYR_USER_NODE, gpio_direct_out_gpios)

#if !DT_NODE_HAS_STATUS(GPIO_DIRECT_IN_CTLR, okay)
#error "GPIO controller for gpio-direct-in-gpios is disabled"
#endif

#if !DT_NODE_HAS_STATUS(GPIO_DIRECT_OUT_CTLR, okay)
#error "GPIO controller for gpio-direct-out-gpios is disabled"
#endif

namespace {

static const struct gpio_dt_spec gpio_direct_in =
	GPIO_DT_SPEC_GET(ZEPHYR_USER_NODE, gpio_direct_in_gpios);
static const struct gpio_dt_spec gpio_direct_out =
	GPIO_DT_SPEC_GET(ZEPHYR_USER_NODE, gpio_direct_out_gpios);

static struct gpio_callback gpio_callback_isr_gpioHAL;

static void callback_isr_gpioHAL(const struct device *port,
				 struct gpio_callback *cb,
				 uint32_t pins)
{
	ARG_UNUSED(port);
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);

	const int in_val = gpio_pin_get_dt(&gpio_direct_in);
	(void)gpio_pin_set_dt(&gpio_direct_out, in_val > 0);
}

} // namespace

int util_gpio_response_init()
{
	int ret;

	if (!device_is_ready(gpio_direct_in.port)) {
		LOG_ERR("GPIO input device not ready");
		return -ENODEV;
	}

	if (!device_is_ready(gpio_direct_out.port)) {
		LOG_ERR("GPIO output device not ready");
		return -ENODEV;
	}

	ret = gpio_pin_configure_dt(&gpio_direct_in, GPIO_INPUT);
	if (ret != 0) {
		LOG_ERR("gpio_direct_in configure failed: %d", ret);
		return ret;
	}

	ret = gpio_pin_configure_dt(&gpio_direct_out, GPIO_OUTPUT_INACTIVE);
	if (ret != 0) {
		LOG_ERR("gpio_direct_out configure failed: %d", ret);
		return ret;
	}

	ret = gpio_pin_interrupt_configure_dt(&gpio_direct_in, GPIO_INT_EDGE_BOTH);
	if (ret != 0) {
		LOG_ERR("gpio_direct_in irq configure failed: %d", ret);
		return ret;
	}

	gpio_init_callback(&gpio_callback_isr_gpioHAL,
			   callback_isr_gpioHAL,
			   BIT(gpio_direct_in.pin));
	ret = gpio_add_callback(gpio_direct_in.port, &gpio_callback_isr_gpioHAL);
	if (ret != 0) {
		LOG_ERR("gpio_direct_in add callback failed: %d", ret);
		return ret;
	}

	LOG_INF("ISR_GPIO_HAL ready (in: port=%s pin=%d, out: port=%s pin=%d)",
		gpio_direct_in.port->name,
		gpio_direct_in.pin,
		gpio_direct_out.port->name,
		gpio_direct_out.pin);
	return 0;
}
