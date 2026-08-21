cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(demo_response_time)

target_sources(app PRIVATE
	src/main.cpp
	src/util_gpio_response.cpp
	src/util_led0_blink.cpp
)
