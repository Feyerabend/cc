cmake_minimum_required(VERSION 3.13)

# Include the Pico SDK import script
include(pico_sdk_import.cmake)

# Project name and languages
project(particle_system C CXX ASM)

# Set C/C++ standards
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# Add executable
add_executable(particle_system
    main.c
    display.c
)

# Link required libraries
target_link_libraries(particle_system
    pico_stdlib
    pico_multicore
    pico_sync
    hardware_spi
    hardware_gpio
    hardware_dma
    hardware_irq
    hardware_timer
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(particle_system 1)
pico_enable_stdio_uart(particle_system 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(particle_system)

# Optional: Set compile options for optimization
target_compile_options(particle_system PRIVATE
    -Wall
    -Wextra
    -O3
)
