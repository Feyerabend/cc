cmake_minimum_required(VERSION 3.13)

# Include the Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(simple_vga_test)

# Initialize the SDK
pico_sdk_init()

# Add executable
add_executable(simple_vga_test
    test.c
)

# Pull in our pico_stdlib and other required libraries
target_link_libraries(simple_vga_test 
    pico_stdlib
    hardware_pio
    hardware_dma
    hardware_clocks
    hardware_irq
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(simple_vga_test 1)
pico_enable_stdio_uart(simple_vga_test 0)

# Create map/bin/hex/uf2 file etc.
pico_add_extra_outputs(simple_vga_test)