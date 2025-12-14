cmake_minimum_required(VERSION 3.13)

# Initialize the Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(mandelbrot_display C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# Add executable
add_executable(mandelbrot
    main.c
    display.c
)

# Link libraries
target_link_libraries(mandelbrot
    pico_stdlib
    pico_multicore
    hardware_spi
    hardware_gpio
    hardware_dma
    hardware_irq
    hardware_sync
    hardware_timer
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(mandelbrot 1)
pico_enable_stdio_uart(mandelbrot 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(mandelbrot)
