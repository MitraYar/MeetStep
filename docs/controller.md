# MeetStep: SMK 37 Pro

Target: Windows standalone. VST3 is frozen. See PROJECT_STATUS.md.
Stock firmware preset, MIDI channels numbered 1–16.

## Pads (channel 10)

Physical order: top row left to right, then bottom row left to right.

| Bank | Top row | Bottom row |
| --- | --- | --- |
| 1 | 40 41 42 43 48 49 50 51 | 36 37 38 39 44 45 46 47 |
| 2 | 56 57 58 59 64 65 66 67 | 52 53 54 55 60 61 62 63 |

Bank 1 maps to steps 1–16. Bank 2 does not edit the pattern; pad 25
(bottom row leftmost, MIDI Note 52 on channel 10) toggles Play/Stop.
Banks switch on the hardware; incoming note numbers identify the bank.
Positive-velocity Note On toggles a step. Note Off and zero-velocity
Note On do not toggle. Notes on channels other than 10 select the drum
note. Each drum note has its own pattern. Until a note is selected,
pads do nothing. Standalone Audition and MIDI output are implemented; see PROJECT_STATUS.md.

## Other controls

- Knob bank 1: channel 6, CC 48–55.
- Knob bank 2: channel 6, CC 56–63.
- Fader bank 1: channel 1, CC 64–67.
- Fader bank 2: channel 1, CC 68–71.

CC56 velocity, CC57 note length and CC63 tempo on channel 6 are planned,
not yet implemented. LED colours use a separate SMK output selected in Settings.
Pads 1–16 show enabled/empty steps of the keyboard-selected note; pads 17–32
receive a fixed varied palette. Physical bank-2 colour mapping still needs
hardware confirmation. See packaging/INSTALL-WINDOWS.txt for Maximum-mode setup.
Standalone master clock and note output are implemented.

## Pattern editor milestone

Six independent patterns, 16 steps each, with storage for all 128 MIDI notes.
The visible range defaults to notes 36–51 (C1 at the bottom).
Mouse editing is explicit set/erase, whereas hardware pads toggle.
Each drag stays on its starting row and pattern; switching patterns or note
ranges cancels the current stroke. Clear-current affects all 128 notes in
one pattern; clear-all affects all six. Both retain the selected drum and
pattern index. No hardware assignments for pattern switching/clearing yet.
