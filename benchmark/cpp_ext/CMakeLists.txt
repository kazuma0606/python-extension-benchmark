cmake_minimum_required(VERSION 3.12)
project(benchmark_cpp_ext)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python and pybind11
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# Enable optimization
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    if(MSVC)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /O2")
    else()
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3")
    endif()
endif()

# Create numeric module
pybind11_add_module(numeric numeric.cpp)
target_compile_definitions(numeric PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})

# Create memory module
pybind11_add_module(memory memory.cpp)
target_compile_definitions(memory PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})

# Create parallel module
pybind11_add_module(parallel parallel.cpp)
target_compile_definitions(parallel PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})

# Link threading library for parallel module
find_package(Threads REQUIRED)
target_link_libraries(parallel PRIVATE Threads::Threads)