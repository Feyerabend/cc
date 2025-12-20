cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)
project(vm_game C CXX ASM)
pico_sdk_init()

add_executable(vm_game
    vm_game.c
    display.c
)

target_link_libraries(vm_game 
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_gpio
)

pico_add_extra_outputs(vm_game)
