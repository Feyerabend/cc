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

set(PICO_BOARD pico CACHE STRING "Board type")

cmake_minimum_required(VERSION 3.13)

include(${CMAKE_CURRENT_LIST_DIR}/pico_sdk_import.cmake)

project(linear_logic_game C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(linear_logic_game
    linear_logic_game.c
    display.c
)

target_link_libraries(linear_logic_game
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_gpio
    hardware_irq
    m
)

target_include_directories(linear_logic_game PRIVATE ${CMAKE_CURRENT_LIST_DIR})

pico_enable_stdio_usb(linear_logic_game 1)
pico_enable_stdio_uart(linear_logic_game 0)

pico_add_extra_outputs(linear_logic_game)

target_compile_options(linear_logic_game PRIVATE
    -Wall
    -O1
)
