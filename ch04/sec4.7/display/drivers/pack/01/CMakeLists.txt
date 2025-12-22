cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(breakout C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(breakout
    main.c
    display.c
)

target_link_libraries(breakout
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_irq
)

pico_enable_stdio_usb(breakout 1)
pico_enable_stdio_uart(breakout 0)

pico_add_extra_outputs(breakout)
