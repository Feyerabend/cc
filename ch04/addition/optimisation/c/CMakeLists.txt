cmake_minimum_required(VERSION 3.13)

# Include the Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(space_invaders C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# Display library
add_library(display STATIC
    display.c
)

target_link_libraries(display
    pico_stdlib
    hardware_spi
    hardware_gpio
    hardware_dma
    hardware_irq
    hardware_sync
)

target_include_directories(display PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Baseline version - clean reference implementation
add_executable(inv_baseline
    inv_baseline.c
)

target_link_libraries(inv_baseline
    pico_stdlib
    display
)

pico_add_extra_outputs(inv_baseline)
pico_enable_stdio_usb(inv_baseline 1)
pico_enable_stdio_uart(inv_baseline 0)

# Algorithm comparison version - simple vs spatial grid
add_executable(inv_compare
    inv_compare.c
)

target_link_libraries(inv_compare
    pico_stdlib
    display
)

pico_add_extra_outputs(inv_compare)
pico_enable_stdio_usb(inv_compare 1)
pico_enable_stdio_uart(inv_compare 0)

# Complete game with full algorithm comparison
add_executable(inv_compfull
    inv_compfull.c
)

target_link_libraries(inv_compfull
    pico_stdlib
    display
)

pico_add_extra_outputs(inv_compfull)
pico_enable_stdio_usb(inv_compfull 1)
pico_enable_stdio_uart(inv_compfull 0)

# Framebuffer optimization demonstration
add_executable(inv_framebuf
    inv_framebuf.c
)

target_link_libraries(inv_framebuf
    pico_stdlib
    display
)

pico_add_extra_outputs(inv_framebuf)
pico_enable_stdio_usb(inv_framebuf 1)
pico_enable_stdio_uart(inv_framebuf 0)

# Optional: Set default build to inv_compfull (or your preferred version)
# You can change this to inv_baseline, inv_compare, or inv_framebuf
set_target_properties(inv_compfull PROPERTIES OUTPUT_NAME "space_invaders")
