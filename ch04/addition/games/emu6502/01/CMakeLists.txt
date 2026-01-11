cmake_minimum_required(VERSION 3.13)

# Include Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# Project name and language
project(pico_6502_emulator C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK
pico_sdk_init()

# Add executable
add_executable(${PROJECT_NAME}
    main.c
    display.c
    fake6502.c
)

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Link libraries
target_link_libraries(${PROJECT_NAME}
    pico_stdlib          # Standard library
    hardware_spi         # SPI support for display
    hardware_gpio        # GPIO control
    hardware_dma         # DMA for fast display updates
    hardware_irq         # Interrupt handling
    hardware_timer       # Timer support
    hardware_sync        # Synchronization primitives
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(${PROJECT_NAME})

# Optional: Set binary info (shows up in picotool)
pico_set_program_name(${PROJECT_NAME} "6502 Emulator C64")
pico_set_program_version(${PROJECT_NAME} "1.0")
pico_set_program_description(${PROJECT_NAME} "6502 CPU Emulator with C64-style display")
pico_set_program_url(${PROJECT_NAME} "https://github.com/yourusername/pico-6502")

# Optional: Optimization flags for performance
target_compile_options(${PROJECT_NAME} PRIVATE
    -O2                  # Optimize for performance
    -Wall                # Enable warnings
    -Wextra              # Extra warnings
)

# Optional: Increase stack size if needed (default is 2KB)
# target_compile_definitions(${PROJECT_NAME} PRIVATE
#     PICO_STACK_SIZE=0x1000
# )
