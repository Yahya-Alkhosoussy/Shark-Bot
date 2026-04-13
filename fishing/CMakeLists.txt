cmake_minimum_required(VERSION 3.11)

include(FetchContent)

project(fishMultipleTimesQuickly)

# Find Python
# Use venv Python if it exists, otherwise fall back to system Python
string(FIND "${CMAKE_SOURCE_DIR}" "fishing" FOUND_POS)
if (FOUND_POS GREATER -1) # -1 is if not found
  get_filename_component(PARENT_DIR "${CMAKE_SOURCE_DIR}" DIRECTORY)
  message("USING PARENT DIRECTORY")
  set(DIR "${PARENT_DIR}")
  message("${PARENT_DIR}")
else()
  set(DIR "${CMAKE_SOURCE_DIR}")
endif()

if(EXISTS "${DIR}/.venv/Scripts/python.exe")
  set(Python3_EXECUTABLE "${DIR}/.venv/Scripts/python.exe")
  message("USING VENV")
elseif(EXISTS "${DIR}/.venv/bin/python")
  set(Python3_EXECUTABLE "${DIR}/.venv/bin/python")
  message("USING VENV")
else()
  message("USING SOURCE")
endif()

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Ask Python where pybind11 is
execute_process(
  COMMAND "${Python3_EXECUTABLE}" -m pybind11 --cmakedir
  OUTPUT_VARIABLE pybind11_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
  RESULT_VARIABLE PYBIND11_NOT_FOUND
)

message(STATUS "pybind11_DIR: ${pybind11_DIR}")

# Fail loudly if pybind11 isn't installed in the current Python env
if(PYBIND11_NOT_FOUND)
  message(STATUS "Result code: ${PYBIND11_NOT_FOUND}")

  message(FATAL_ERROR 
    "pybind11 not found in Python environment: ${Python3_EXECUTABLE}\n"
    "Make sure your venv is activated and run: pip install pybind11"
  )
endif()

# 3. download pybind11
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG        v2.13.6
)
FetchContent_MakeAvailable(pybind11)
# 4. Create the Python extension module
pybind11_add_module(fish_multiple src/fish_multiple.cpp)

# 5. Set C++ standard
target_compile_features(fish_multiple PRIVATE cxx_std_17)