cmake_minimum_required(VERSION 3.13)

# Pull in SDK (must be before project)
include(pico_sdk_import.cmake)

project(diffie_hellman_demo C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the SDK
pico_sdk_init()

# Initiator executable
add_executable(initiator
    initiator.c
)

target_link_libraries(initiator
    pico_stdlib
    pico_multicore
    hardware_uart
    pico_rand
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(initiator 1)
pico_enable_stdio_uart(initiator 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(initiator)

# Responder executable
add_executable(responder
    responder.c
)

target_link_libraries(responder
    pico_stdlib
    pico_multicore
    hardware_uart
    pico_rand
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(responder 1)
pico_enable_stdio_uart(responder 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(responder)