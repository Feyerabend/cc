cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(power_management_demo C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(power_demo
    main.c
    display.c
)

target_link_libraries(power_demo
    pico_stdlib
    hardware_spi
    hardware_gpio
    hardware_dma
    hardware_irq
    hardware_sync
    hardware_clocks
    hardware_xosc
    hardware_pll
    hardware_vreg
    hardware_watchdog
)

pico_add_extra_outputs(power_demo)
pico_enable_stdio_usb(power_demo 1)
pico_enable_stdio_uart(power_demo 0)
