# MeetStep

Windows VST3 drum step-sequencer project for SMK 37 Pro and Ableton Live.

**Current milestone: pattern editor, not a playable sequencer yet.** The VST3
receives MIDI for editing and stores six patterns in host state. It currently
outputs no MIDI or sound. Host-clock playback and Live routing verification
are still pending. No standalone application is included yet.

## Editing

- Six square buttons select independent patterns immediately.
- `Clear pattern` erases all notes in the selected pattern; `Clear all` erases
  all six. These actions are immediate, with no undo in this prototype.
- 16 columns are steps, left to right. The initial 16-note range is 36–51,
  ascending from bottom to top. Labels use Ableton's C1 = MIDI note 36.
- Left click sets a cell; right click erases it. Repeated clicks do not toggle.
- Drag with either button edits a continuous span in the original row, even
  when the pointer moves vertically or skips cells between mouse events.
- `-16 notes` / `+16 notes` changes the visible range, clamped to MIDI 0–127.
- Keyboard notes outside channel 10 select the drum for hardware editing.
  The selected note is highlighted when visible; mouse editing does not
  change the keyboard-selected drum.
- First-bank pads on channel 10 toggle steps in physical row order. Second
  bank is reserved. See [controller mapping](docs/controller.md).

## Build core tests (C++17, CMake 3.20+)

```sh
cmake -S . -B build
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

## Windows VST3 (Visual Studio 2022, Desktop development with C++)

```powershell
cmake -S . -B build-plugin -DMEETSTEP_BUILD_PLUGIN=ON
cmake --build build-plugin --config Release --parallel 2
ctest --test-dir build-plugin -C Release --output-on-failure
```

CMake downloads pinned JUCE 8.0.6 from its official repository. Review JUCE's
license before distribution. The VST3 bundle is in
`build-plugin/MeetStep_artefacts/Release/VST3/MeetStep.vst3`.
Copy the whole bundle to your configured VST3 folder and rescan Live.
The Windows GitHub Actions workflow builds/tests and uploads this bundle;
it has not yet been run from this workspace.

Linux JUCE builds additionally need ALSA, X11/Xext/Xinerama/Xrandr/Xcursor,
FreeType and fontconfig development packages. GUI tests may require Xvfb
on a machine without a display. `editor_tests` writes `meetstep-editor.png`
in its working directory after exercising mouse input and buttons.

## First Windows build via GitHub

Open the repository's **Actions → Windows VST3**, choose a successful run,
and download **MeetStep-0.1.0-Windows-x64** from Artifacts. Extract the
artifact archive and the enclosed ZIP; follow `INSTALL-WINDOWS.txt`.
The full `MeetStep.vst3` directory must stay together. The screenshot is
also uploaded separately as **MeetStep-editor-screenshot**.

## Standalone 0.2.0

The Windows package now also includes `MeetStep Standalone.exe`.
It owns MIDI devices directly, supports multiple inputs and one output, and
sends sequence notes plus MIDI Clock/Start/Stop/Continue as the clock master.
See `packaging/INSTALL-WINDOWS.txt` for routing, shortcuts and limitations.
The VST3 remains the previous editor milestone; standalone playback is separate.
