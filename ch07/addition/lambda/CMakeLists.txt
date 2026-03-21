# CMakeLists.txt — pico-lambda
# Stateless Forth HTTP dispatcher for Raspberry Pi Pico 2W (RP2350 + CYW43 WiFi)
#
# Prerequisites:
#   export PICO_SDK_PATH=/path/to/pico-sdk
#   export PICO_EXTRAS_PATH=/path/to/pico-extras   (only needed if pico-extras is used)
#
# Build:
#   mkdir build && cd build
#   cmake .. -DPICO_BOARD=pico2w
#   make -j$(nproc)
#
# Flash:
#   Hold BOOTSEL, plug in USB, then:
#   cp pico_lambda.uf2 /Volumes/RPI-RP2    (macOS)
#   cp pico_lambda.uf2 /media/$USER/RPI-RP2 (Linux)

cmake_minimum_required(VERSION 3.13)

# Must be pico2w — the CYW43 WiFi chip only ships on the 'w' variant
set(PICO_BOARD pico2_w CACHE STRING "Board type — must be pico2_w for WiFi")

# Pull in Pico SDK (pico-extras not required for lwIP polling mode)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(pico_lambda C CXX ASM)
set(CMAKE_C_STANDARD 11)

pico_sdk_init()

# -- executable
add_executable(pico_lambda
    main.c
    net.c
    forth.c
    dispatch.c
    sandbox.c
    display.c
    ui.c
)

target_include_directories(pico_lambda PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

target_compile_options(pico_lambda PRIVATE -O2 -Wall -Wextra -ffunction-sections -fdata-sections)

# -- link libraries
target_link_libraries(pico_lambda PRIVATE
    pico_stdlib                   # stdio, time, sleep
    pico_cyw43_arch_lwip_poll     # CYW43 WiFi + lwIP in polling (no-RTOS) mode
    hardware_spi                  # SPI bus for Display Pack 2.0
    hardware_dma                  # DMA-accelerated display transfers
)

# USB serial for debug printf; UART off
pico_enable_stdio_usb (pico_lambda 1)
pico_enable_stdio_uart(pico_lambda 0)

# Generate .uf2 and .hex alongside the ELF
pico_add_extra_outputs(pico_lambda)

message(STATUS "Board : ${PICO_BOARD}")
message(STATUS "Target: pico_lambda — Forth-over-HTTP, no RTOS, lwIP poll mode")
