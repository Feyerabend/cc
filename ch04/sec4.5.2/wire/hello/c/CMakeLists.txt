cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)
project(uart_example C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
add_executable(uart_example
    uart_send.c # Replace with uart_receive.c for the receiver
)
pico_enable_stdio_usb(uart_example 1)
pico_enable_stdio_uart(uart_example 0)
pico_add_extra_outputs(uart_example)
target_link_libraries(uart_example pico_stdlib hardware_uart)
