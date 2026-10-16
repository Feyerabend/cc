cmake_minimum_required(VERSION 3.13)

# Pico 2 (RP2350). The VM and the framebuffer need its 520 KB of RAM.
set(PICO_BOARD pico2 CACHE STRING "Board type")

# Include Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(picolisp_game C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the SDK
pico_sdk_init()

# The game to build in: a file in examples/, for example
#   cmake -DGAME=snake ..
set(GAME "shooter" CACHE STRING "Game in examples/ to embed (without .lisp)")
set(GAME_FILE ${CMAKE_CURRENT_SOURCE_DIR}/examples/${GAME}.lisp)
if(NOT EXISTS ${GAME_FILE})
    message(FATAL_ERROR "No such game: ${GAME_FILE}")
endif()

# Turn the .lisp file into a C header holding a string. The bytes are
# written as numbers, so quotes and backslashes in the source need no care.
file(READ ${GAME_FILE} GAME_HEX HEX)
string(REGEX REPLACE "([0-9a-f][0-9a-f])" "0x\\1," GAME_BYTES "${GAME_HEX}")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/game_script.h
    "// Generated from ${GAME_FILE}\nstatic const char GAME_SCRIPT[] = { ${GAME_BYTES} 0 };\n")
# Run CMake again when the game changes
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GAME_FILE})

# Main executable
add_executable(picolisp_game
    main.c
    display.c
    lisp_vm.c
    lisp_builtins.c
    lisp_game.c
)

target_include_directories(picolisp_game PRIVATE ${CMAKE_CURRENT_BINARY_DIR})

# The interpreter runs on core 1 with a stack of LISP_STACK_SIZE bytes.
# LISP_MAX_DEPTH limits the nesting so that the stack cannot overflow;
# each level needs about 60 to 80 bytes (measured with -fstack-usage), plus
# room for printf and the garbage collector.
target_compile_definitions(picolisp_game PRIVATE
    LISP_STACK_SIZE=32768
    LISP_MAX_DEPTH=200
)

# Link libraries
target_link_libraries(picolisp_game
    pico_stdlib
    pico_multicore
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

# Print memory usage after build (CMAKE_SIZE is not set by the Pico SDK)
get_filename_component(TOOLCHAIN_BIN ${CMAKE_C_COMPILER} DIRECTORY)
find_program(ARM_SIZE arm-none-eabi-size HINTS ${TOOLCHAIN_BIN})
if(ARM_SIZE)
    add_custom_command(TARGET picolisp_game POST_BUILD
        COMMAND ${ARM_SIZE} $<TARGET_FILE:picolisp_game>
        COMMENT "Memory usage:"
    )
endif()
