# Generated Cmake Pico project file

cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Initialise pico_sdk from installed location
# (note this can come from environment, CMake cache etc)

# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.2.0)
set(toolchainVersion 14_2_Rel1)
set(picotoolVersion 2.2.0-a4)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================
set(PICO_BOARD pico2_w CACHE STRING "Board type")

# Pull in Raspberry Pi Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(tcpdisplay C CXX ASM)

# Initialise the Raspberry Pi Pico SDK
pico_sdk_init()

# Add executable. Default name is the project name, version 0.1

if (TARGET tinyusb_device)
    add_executable(tcpdisplay
        main.c
        tcpdisplay.c
        display.c
        net.c
    )

    # pull in common dependencies
    target_link_libraries(tcpdisplay
        pico_stdlib
        hardware_sync
        hardware_spi
        hardware_dma
        pico_multicore
        pico_cyw43_arch_lwip_poll
    )

    # enable both usb and uart output for debugging
    pico_enable_stdio_usb(tcpdisplay 1)
    pico_enable_stdio_uart(tcpdisplay 1)

    # create map/bin/hex/uf2 file etc.
    pico_add_extra_outputs(tcpdisplay)

    target_include_directories(tcpdisplay PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

    target_compile_options(tcpdisplay PRIVATE
        -Wall
        -Wextra
        -O1
    )

elseif(PICO_ON_DEVICE)
    message("Skipping tcpdisplay because TinyUSB submodule is not initialized in the SDK")
endif()
