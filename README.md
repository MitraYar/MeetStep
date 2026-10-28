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

Version 0.2.4 adds a separate **Pad colour MIDI output** and matching SMK reply
input in Settings. Pads 1-16 follow the keyboard-selected drum: the editor's
green for occupied steps, black for empty steps. Pads 17-32 use a fixed varied
palette. Pad 25 (channel 10, note 52) and Space toggle Play/Stop. Start resets to
step 1; Continue remains available separately. See
[setup and colour-port instructions](packaging/INSTALL-WINDOWS.txt).

LED exchange uses the frozen tester's Maximum mode: one RGB+enable block,
ACK per packet, no added delay, no retry. A timeout stops colours without
stopping playback. Preset index 0 is required; physical bank-2 mapping still
needs hardware confirmation. Frozen oracle provenance is in
[tests/reference](tests/reference/README.md).

```powershell
cmake -S . -B build -A x64 -DMEETSTEP_BUILD_STANDALONE=ON -DMEETSTEP_BUILD_PLUGIN=OFF -DBUILD_TESTING=ON
cmake --build build --config Release --parallel 2
ctest --test-dir build -C Release --output-on-failure --no-tests=error
```

JUCE 8.0.6 is pinned in CMake. Visual Studio 2022 with C++ desktop development
is required. GitHub Actions workflow `Windows Standalone` publishes the app;
`SMK LED probe Windows` publishes the separate diagnostic utility.
See [installation/routing](packaging/INSTALL-WINDOWS.txt) and
[controller map](docs/controller.md).
