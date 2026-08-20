#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(app, LOG_LEVEL_INF);

#define ZEPHYR_USER_NODE DT_PATH(zephyr_user)

#if !DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, gpio_direct_in_gpios)
#error "Missing gpio-direct-in-gpios in zephyr,user devicetree node"
#endif

#if !DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, gpio_direct_out_gpios)
#error "Missing gpio-direct-out-gpios in zephyr,user devicetree node"
#endif

#define LED0_NODE DT_ALIAS(led0)

static const struct gpio_dt_spec gpio_direct_in = GPIO_DT_SPEC_GET(ZEPHYR_USER_NODE, gpio_direct_in_gpios);
static const struct gpio_dt_spec gpio_direct_out = GPIO_DT_SPEC_GET(ZEPHYR_USER_NODE, gpio_direct_out_gpios);

static const struct gpio_dt_spec gpio_led0 = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
#define LED_BLINK_STACK_SIZE 512
#define LED_BLINK_PRIORITY 5
K_THREAD_STACK_DEFINE(led_blink_stack, LED_BLINK_STACK_SIZE);
static struct k_thread led_blink_thread;

static struct gpio_callback gpio_callback_isr_gpioHAL;

/*
Interrupt Service Routine (ISR) using the zephyr HAL
*/
static void callback_isr_gpioHAL(const struct device *port, struct gpio_callback *cb, uint32_t pins)
{
	ARG_UNUSED(port);
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);

	int in_val = gpio_pin_get_dt(&gpio_direct_in);
	(void)gpio_pin_set_dt(&gpio_direct_out, in_val > 0);
}

static int init_isr_gpioHAL(void)
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

	gpio_init_callback(&gpio_callback_isr_gpioHAL, callback_isr_gpioHAL, BIT(gpio_direct_in.pin));
	ret = gpio_add_callback(gpio_direct_in.port, &gpio_callback_isr_gpioHAL);
	if (ret != 0) {
		LOG_ERR("gpio_direct_in add callback failed: %d", ret);
		return ret;
	}

	LOG_INF("ISR_GPIO_HAL ready (in: port=%s pin=%d, out: port=%s pin=%d)",
		gpio_direct_in.port->name, gpio_direct_in.pin, gpio_direct_out.port->name, gpio_direct_out.pin);
	return 0;
}

static void blink_led1green(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	while (1) {
		(void)gpio_pin_toggle_dt(&gpio_led0);
		k_sleep(K_MSEC(500));
	}
}

static int init_led0_blink(void)
{
	if (!device_is_ready(gpio_led0.port)) {
		LOG_ERR("LED 0 device not ready");
		return -ENODEV;
	}

	int ret = gpio_pin_configure_dt(&gpio_led0, GPIO_OUTPUT_INACTIVE);
	if (ret != 0) {
		LOG_ERR("LED 0 configure failed: %d", ret);
		return ret;
	}

	k_thread_create(&led_blink_thread, led_blink_stack,
		K_THREAD_STACK_SIZEOF(led_blink_stack), blink_led1green, NULL, NULL, NULL,
		LED_BLINK_PRIORITY, 0, K_NO_WAIT);

	LOG_INF("LED 0 blink thread ready (interval: 500 ms)");
	return 0;
}

int main(void)
{
	int ret = init_isr_gpioHAL();
	if (ret != 0) {
		return ret;
	}

#if DT_NODE_EXISTS(LED0_NODE)
	ret = init_led0_blink();
	if (ret != 0) {
		return ret;
	}
#endif

}
