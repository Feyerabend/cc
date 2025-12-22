cmake_minimum_required(VERSION 3.13)

# Include Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(picolisp_game C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the SDK
pico_sdk_init()

# Main executable
add_executable(picolisp_game
    main.c
    display.c
    lisp_vm.c
    lisp_builtins.c
)

# Link libraries
target_link_libraries(picolisp_game
    pico_stdlib
    hardware_spi
    hardware_gpio
    hardware_dma
    hardware_irq
    hardware_sync
)

# Enable USB output for printf debugging
pico_enable_stdio_usb(picolisp_game 1)
pico_enable_stdio_uart(picolisp_game 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(picolisp_game)

# Optimization flags for better performance
target_compile_options(picolisp_game PRIVATE
    -O2                    # Optimize for speed
    -ffunction-sections    # Dead code elimination
    -fdata-sections
)

target_link_options(picolisp_game PRIVATE
    -Wl,--gc-sections      # Remove unused sections
)

# Print memory usage after build
add_custom_command(TARGET picolisp_game POST_BUILD
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:picolisp_game>
    COMMENT "Memory usage:"
)