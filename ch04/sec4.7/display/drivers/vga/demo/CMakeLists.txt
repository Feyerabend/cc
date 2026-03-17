# CMakeLists.txt — pico_gfx
# Pico 2 (RP2350) VGA 2D graphics demo
#
# Prerequisites:
#   export PICO_SDK_PATH=/path/to/pico-sdk
#   export PICO_EXTRAS_PATH=/path/to/pico-extras
#
# Build:
#   mkdir build && cd build
#   cmake .. -DPICO_BOARD=pico2
#   make -j$(nproc)
#
# Flash:
#   Hold BOOTSEL, plug in USB, then:
#   cp pico_gfx.uf2 /Volumes/RPI-RP2    (macOS)
#   cp pico_gfx.uf2 /media/$USER/RPI-RP2 (Linux)

cmake_minimum_required(VERSION 3.13)

# Board selection — override with -DPICO_BOARD=pico2w for wireless variant
set(PICO_BOARD pico2 CACHE STRING "Pico board type (pico2 or pico2w)")

# Pull in Pico SDK and pico-extras (order matters)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
include($ENV{PICO_EXTRAS_PATH}/external/pico_extras_import.cmake)

project(pico_gfx C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialise the Pico SDK
pico_sdk_init()

# ── executable ───────────────────────────────────────────────────────────────
add_executable(pico_gfx
    src/main.c
    src/gfx.c
    src/raster.c
    src/vga.c
    src/demo.c
)

# All headers are in src/
target_include_directories(pico_gfx PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)

# Optimise for speed (rendering is CPU-bound)
target_compile_options(pico_gfx PRIVATE
    -O2
    -Wall
    -Wextra
    -ffunction-sections
    -fdata-sections
)

# ── link libraries ───────────────────────────────────────────────────────────
target_link_libraries(pico_gfx PRIVATE
    pico_stdlib          # stdio, time, sleep
    pico_multicore       # multicore_launch_core1
    pico_scanvideo_dpi   # VGA scanline engine (from pico-extras)
    hardware_pio         # PIO used by scanvideo internally
    hardware_dma         # DMA used by scanvideo internally
    hardware_irq         # IRQ support
    pico_sync            # spin locks, semaphores
    m                    # libm — sinf, cosf, sqrtf in demo/raster
)

# Enable USB serial output (handy for printf debugging)
pico_enable_stdio_usb (pico_gfx 1)
pico_enable_stdio_uart(pico_gfx 0)

# Generate .uf2 and .hex alongside the ELF
pico_add_extra_outputs(pico_gfx)

# ── memory layout sanity check ────────────────────────────────────────────────
# Two 320×240 RGB565 framebuffers = 307,200 bytes ≈ 300 KB
# RP2350 has 520 KB SRAM — leaves ~213 KB for code/stack/heap.
# If the linker complains about RAM overflow, enable XIP cache or reduce
# GFX_MAX_EDGES in raster.h.
message(STATUS "Board: ${PICO_BOARD}")
message(STATUS "Framebuffer RAM: ~307 KB (2 × 320×240×2)")
