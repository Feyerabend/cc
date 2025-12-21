cmake_minimum_required(VERSION 3.13)

# Pull in Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(pimoroni_display C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# Main executable
add_executable(pimoroni_display
    main.c
    display.c
)

# Pull in common dependencies
target_link_libraries(pimoroni_display
    pico_stdlib
    hardware_spi
    hardware_gpio
    hardware_dma
    hardware_irq
    hardware_sync
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(pimoroni_display 1)
pico_enable_stdio_uart(pimoroni_display 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(pimoroni_display)

# Compiler optimization flags (optional but recommended)
target_compile_options(pimoroni_display PRIVATE
    -Wall
    -Wextra
    -O2  # Optimize for performance
)
