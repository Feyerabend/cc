cmake_minimum_required(VERSION 3.13)

# Pull in SDK (must be before project)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(display_test_pattern C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Init the Raspberry Pi Pico SDK
pico_sdk_init()

# Add executable
add_executable(display_test_pattern
    main.c
    display.c
)

# Pull in common dependencies
target_link_libraries(display_test_pattern
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_gpio
    hardware_timer
    hardware_irq
    hardware_sync
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(display_test_pattern 1)
pico_enable_stdio_uart(display_test_pattern 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(display_test_pattern)
