cmake_minimum_required(VERSION 3.10)
include(CMakePrintHelpers)


project(windowcapture_win_py LANGUAGES CXX)
add_subdirectory(../extern/pybind11 ../extern/build)

if (MSVC)
    # warning level 4 and all warnings as errors
    add_compile_options(/std:c++17 /await /Zi /MT /EHsc /Oy- /Ob0)
endif()

## common

include_directories(SYSTEM
    ../extern/pybind11/include
    C:/Users/Yu/AppData/Local/Programs/Python/Python310/include
    "C:/Program Files (x86)/Windows Kits/10/Include/10.0.20348.0/cppwinrt/winrt"
    "C:/Program Files (x86)/Windows Kits/10/Include/10.0.20348.0/shared"
    "C:/Program Files (x86)/Windows Kits/10/Include/10.0.20348.0/um"
)

set(SOURCE
    capture.cpp
    capture_winrt.cpp
    semaphore.cpp
)

## testcase.exe

add_executable(testcase
    test.cpp
    ${SOURCE}
)
target_link_directories(testcase PRIVATE
    C:/Users/Yu/AppData/Local/Programs/Python/Python310/libs
)
target_link_libraries(testcase PRIVATE
    python3
    windowsapp
)

## windowcapture_win_py

pybind11_add_module(windowcapture_win_py
    main.cpp
    ${SOURCE}
)

target_precompile_headers(windowcapture_win_py PRIVATE pch.hpp)
target_link_libraries(windowcapture_win_py PRIVATE windowsapp)
