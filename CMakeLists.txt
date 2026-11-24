cmake_minimum_required(VERSION 3.16)
project(ProjectAssignmentScheduling LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(alns solutions/alns/main.cpp)
add_executable(heuristics solutions/heuristics/main.cpp)

foreach(target IN ITEMS alns heuristics)
    target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
endforeach()
