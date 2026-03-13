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

set(PICO_BOARD pico2 CACHE STRING "Board type")

cmake_minimum_required(VERSION 3.13)

include(${CMAKE_CURRENT_LIST_DIR}/pico_sdk_import.cmake)

project(tensor_proof_nets C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(tensor_proof_nets
    tensor_proof_nets.c
    display.c
)

target_link_libraries(tensor_proof_nets
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_gpio
    hardware_irq
    m
)

target_include_directories(tensor_proof_nets PRIVATE ${CMAKE_CURRENT_LIST_DIR})

pico_enable_stdio_usb(tensor_proof_nets 1)
pico_enable_stdio_uart(tensor_proof_nets 0)

pico_add_extra_outputs(tensor_proof_nets)

target_compile_options(tensor_proof_nets PRIVATE
    -Wall
    -O1
)
