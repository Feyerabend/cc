cmake_minimum_required(VERSION 3.13)

# Import the pico-sdk
include(pico_sdk_import.cmake)

project(uart_communication C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Init the SDK
pico_sdk_init()

# Full duplex UART program (main device)
add_executable(device
    device.c
)

target_link_libraries(device
    pico_stdlib
    pico_multicore
    hardware_uart
    hardware_gpio
    hardware_adc
    pico_util
)

# Enable USB output and UART output
pico_enable_stdio_usb(device 1)
pico_enable_stdio_uart(device 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(device)

# Controller program
add_executable(controller
    controller.c
)

target_link_libraries(controller 
    pico_stdlib 
    pico_multicore
    hardware_uart
    hardware_gpio
    pico_util
)

# Enable USB output and UART output
pico_enable_stdio_usb(controller 1)
pico_enable_stdio_uart(controller 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(controller)