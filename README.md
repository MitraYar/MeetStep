# MeetStep

Windows standalone MIDI drum sequencer for SMK 37 Pro. VST3 is frozen and
excluded from current CI. See [current status and handoff](docs/PROJECT_STATUS.md)
for implemented features, pending requirements and LED protocol evidence.

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

## Windows standalone build

```powershell
cmake -S . -B build -A x64 -DMEETSTEP_BUILD_STANDALONE=ON -DMEETSTEP_BUILD_PLUGIN=OFF -DBUILD_TESTING=OFF
cmake --build build --config Release --target MeetStepApp --parallel 2
```

JUCE 8.0.6 is pinned in CMake. Visual Studio 2022 with C++ desktop development
is required. GitHub Actions workflow `Windows Standalone` publishes the app;
`SMK LED probe Windows` publishes the separate diagnostic utility.
See [installation/routing](packaging/INSTALL-WINDOWS.txt) and
[controller map](docs/controller.md).
