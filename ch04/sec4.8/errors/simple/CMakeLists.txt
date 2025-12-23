# Minimum version required for Pico SDK
cmake_minimum_required(VERSION 3.13)

# Project name
set(PROJECT_NAME display_tester)
project(${PROJECT_NAME} C CXX ASM) # simple e.g.

# Set the path to the Pico SDK (usually set via environment variable PICO_SDK_PATH)
# If not set, you can uncomment and set it manually:
# set(PICO_SDK_PATH "/path/to/pico-sdk")

include(pico_sdk_import.cmake)

# Initialize the Pico SDK
pico_sdk_init()

# Add the executable with your source files
add_executable(${PROJECT_NAME}
    main.c
    display.c
)

# Link required Pico libraries
target_link_libraries(${PROJECT_NAME}
    pico_stdlib      # Standard library (includes time, stdio, etc.)
    hardware_spi     # SPI peripheral
    hardware_dma     # DMA support
    hardware_gpio    # GPIO control (used extensively)
    hardware_irq     # Interrupt handling (for DMA IRQ)
)

# Enable USB serial output (for printf/debug) and disable UART by default
# (Common for development with Pico connected via USB)
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 0)

# Generate extra output files: .uf2, .hex, .bin, etc.
pico_add_extra_outputs(${PROJECT_NAME})

# Include the current directory for header files (display.h)
target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_CURRENT_LIST_DIR})
