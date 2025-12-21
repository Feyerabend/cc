cmake_minimum_required(VERSION 3.13)

# Pull in Pico SDK (must be before project)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# Project name and language
project(reaction_timer C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# Create the main executable
add_executable(reaction_timer
    main.c
    display.c
)

# Link libraries
target_link_libraries(reaction_timer
    pico_stdlib          # Standard library (stdio, time, etc.)
    hardware_spi         # SPI hardware support
    hardware_gpio        # GPIO control
    hardware_dma         # DMA support for fast transfers
    hardware_irq         # Interrupt handling
    hardware_sync        # Synchronization primitives
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(reaction_timer 1)
pico_enable_stdio_uart(reaction_timer 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(reaction_timer)

# Optional: Set compile options for optimization
# Uncomment for production builds:
# target_compile_options(reaction_timer PRIVATE
#     -O3                  # Maximum optimization
#     -Wall                # All warnings
#     -Wextra              # Extra warnings
# )

# Debug build options (default)
target_compile_options(reaction_timer PRIVATE
    -O2                  # Moderate optimization with debug
    -g                   # Debug symbols
    -Wall                # All warnings
    -Wextra              # Extra warnings
)

# Optional: Print memory usage after build
# add_custom_command(TARGET reaction_timer POST_BUILD
#     COMMAND ${CMAKE_SIZE_UTIL} $<TARGET_FILE:reaction_timer>
#     COMMENT "Memory usage:"
# )
