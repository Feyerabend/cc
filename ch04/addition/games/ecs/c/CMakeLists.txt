cmake_minimum_required(VERSION 3.13)

# Pull in SDK (must be before project)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(platformer_game C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Init Pico SDK
pico_sdk_init()

# Add executable
add_executable(platformer
    main.c
    game.c
    display.c
)

# Pull in common dependencies
target_link_libraries(platformer
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_gpio
    hardware_irq
    hardware_timer
    hardware_sync
)

# Enable USB serial output for debugging (optional)
pico_enable_stdio_usb(platformer 1)
pico_enable_stdio_uart(platformer 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(platformer)

# Compiler optimisations
target_compile_options(platformer PRIVATE
    -O2
    -Wall
    -Wextra
)
