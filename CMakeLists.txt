cmake_minimum_required(VERSION 3.20)
project(MeetStep VERSION 0.1.0 LANGUAGES C CXX)
include(CTest)
add_library(meetstep_core INTERFACE)
target_include_directories(meetstep_core INTERFACE src)
target_compile_features(meetstep_core INTERFACE cxx_std_17)
if(BUILD_TESTING)
  add_executable(pattern_tests tests/pattern.cpp)
  target_link_libraries(pattern_tests PRIVATE meetstep_core)
  add_test(NAME controller_patterns COMMAND pattern_tests)
endif()

option(MEETSTEP_BUILD_PLUGIN "Build JUCE VST3 editor prototype" OFF)
if(MEETSTEP_BUILD_PLUGIN)
  include(FetchContent)
  FetchContent_Declare(JUCE GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 51a8a6d7aeae7326956d747737ccf1575e61e209)
  FetchContent_MakeAvailable(JUCE)
  juce_add_plugin(MeetStep COMPANY_NAME MitraYar PLUGIN_MANUFACTURER_CODE Mtry
    PLUGIN_CODE Mtsp FORMATS VST3 PRODUCT_NAME MeetStep
    IS_SYNTH TRUE NEEDS_MIDI_INPUT TRUE NEEDS_MIDI_OUTPUT TRUE
    COPY_PLUGIN_AFTER_BUILD FALSE)
  target_sources(MeetStep PRIVATE src/Plugin.cpp)
  target_link_libraries(MeetStep PRIVATE meetstep_core juce::juce_audio_utils)
  if(BUILD_TESTING)
    add_executable(editor_tests tests/ui.cpp)
    target_link_libraries(editor_tests PRIVATE MeetStep)
    target_include_directories(editor_tests PRIVATE src "${juce_SOURCE_DIR}/modules")
    target_compile_definitions(editor_tests PRIVATE JUCE_GLOBAL_MODULE_SETTINGS_INCLUDED=1)
    add_test(NAME editor_interaction COMMAND editor_tests)
  endif()
  target_compile_definitions(MeetStep PUBLIC JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0)
endif()
