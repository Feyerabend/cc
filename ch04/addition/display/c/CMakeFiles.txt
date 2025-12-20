cmake_minimum_required(VERSION 3.13)

# Include the Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# Project configuration
project(pico_osd_display C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# Main executable
add_executable(${PROJECT_NAME}
    main.c
    display.c
    osd.c
)

# Enable USB output for printf, disable UART output
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 0)

# Link against the Pico SDK libraries
target_link_libraries(${PROJECT_NAME}
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_gpio
    hardware_irq
    hardware_sync
    hardware_timer
)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(${PROJECT_NAME})

# Optional: Set compiler warnings
target_compile_options(${PROJECT_NAME} PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
)

# Optional: Add compile definitions
target_compile_definitions(${PROJECT_NAME} PRIVATE
    PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS=1000
)
