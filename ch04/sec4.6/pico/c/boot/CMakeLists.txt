cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)
project(boot_demo C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()

add_executable(boot_demo
    main.c
    display.c
)

target_link_libraries(boot_demo
    pico_stdlib
    hardware_gpio
    hardware_timer
    hardware_spi
    hardware_dma
)

pico_enable_stdio_usb(boot_demo 1)
pico_enable_stdio_uart(boot_demo 0)
pico_add_extra_outputs(boot_demo)
