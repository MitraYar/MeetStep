# MeetStep handoff / current project status

## Simple standalone 0.2.4

This slice keeps the 0.2.0 sequencer core and adds a separate SMK colour output
and reply input in Settings. Pads 1–16 show occupied/empty steps of the
keyboard-selected drum (editor green/black); pads 17–32 have a fixed varied
palette. Physical pad 25 is channel-10 Note 52 and toggles Play/Stop, as does
Space. Start resets position; Continue remains separate. No velocity engine
or other larger specification features are added.

LED exchange follows the frozen Python tester's Maximum mode (one RGB+enable
block, mandatory ACK, no added pause/retry). A timeout stops colour updates
without stopping the music. Shared input is opened once. Preset index 0 is
required; bank-2 physical LED mapping and JUCE delivery need hardware checks.
Source provenance and captured fixtures are in tests/reference/README.md.
The run IDs supplied by the user cannot yet be mapped to commits because the
environment blocks GitHub Actions API access. Do not claim that mapping.

Windows Actions now runs the frozen-oracle tests and three CTest suites,
including the standalone's transport and LED-worker checks; reports are
uploaded separately. Check actual run results before claiming they passed.
The older LED investigation notes below describe historical work, not this
slice's transport. The original tools remain unchanged.

This file is the entry point for resuming work in a new Codex task.
Use the existing checkout; do not create a worktree for routine tasks.

## Scope and product

Windows standalone MIDI drum step sequencer driven by SMK 37 Pro, aimed at
working mostly on the controller rather than looking at the monitor.
VST3 is frozen by user instruction: no VST3 work/builds/resources. Current
Windows CI builds/packages standalone only. Original ambition was 32 steps;
current prototype is 16. Six independent patterns, each with drum-note rows.
Pad bank 2 is reserved for future pattern/utility functions, not automatically
steps 17–32. Proposed undo/redo/hold-to-clear mappings are not implemented.
KeyStep Pro and Launchpad Pro MK3 are design references for future planning.

## Implemented and user-validated

Standalone 0.2.0 runs on the user's Windows PC. It has multiple MIDI inputs,
one output, device settings with Apply/Close, master Clock/Start/Stop/Continue
and sequence-note output. DAW should be the MIDI clock slave (Ableton tested
by user at a broad functional level; precise clock performance not measured).
Computer shortcuts act with MeetStep focused. Audition is off by default;
physical slash toggles it ('/' English, '.' Russian). Comma/period ('б'/'ю')
page notes. MIDI drum selection follows the visible range automatically.
Six patterns; mouse left draws/right erases; drags stay on one row. Notes start
at C1=36 at the bottom. BPM/patterns save on normal exit; device choices do not.
Fixed velocity 100, one-step gate, output channel 1. See source for exact logic.

## Agreed but pending main-app features

Master keyboard dropdown separate from additional inputs; independent keyboard
feedback output; channel-6 CC56 new-step velocity, CC57 new-step length,
CC63 tempo. Existing steps should retain stored properties. Value mappings are
not all agreed. Space Start/Stop and Ctrl+physical slash Settings are pending.
Plain slash retains Audition. Details: next-build.md.

## Controller and LED evidence

Full MIDI note/CC map: controller.md. Keyboard is USB-connected; official
editor is MidiSuite. User-confirmed LED output candidate is SMK-37 Pro Midi
(the first logical port; Windows numeric suffix/index can change).
SMC-PAD reference: https://github.com/spectalive/smc-pad, inspected commit
8297442586df3ba1239485b54b272789eb4f1ade. Shared packet framing/encoding is now
supported by actual SMK captures; do not copy SMC-PAD memory addresses.

LED changes require Apply in MidiSuite and disappear on power cycle unless
Save to device is used separately. Do not use persistent Save for feedback.
Pad-1 original probe changed colour according to user. The newer 16-pad palette
probe was reported not to work; exact ACK/timeout log is unknown.

Findings:
- smk-preset-findings.md: offline two-export RGB comparison and USB port names.
- protocol/smk-usb-colour.md: captured pad-1 RGB writes and ACKs.
- protocol/smk-pad1-to-five-capture.md: pads 1–5, per-pad RGB + brightness byte.
- protocol/smk-preset-switch.md: complete presets 0/7, active selector, stride;
  likely missing active-preset handling in the current probe.
- protocol/*.json: extracted evidence, not commands to replay blindly.
- smk-diagnostics.md: passive input monitoring limitations.

Probe tools are separate from MeetStep, not integrated feedback. The palette
probe has 16 active pads (6–16 inferred from preset layout), 10 colours, five
brightness levels, ACK waits, Stop, no retries and no device Save. Bank 2 is
disabled; its address mapping is still unknown. Changing preset is NOT changing
pad bank. Next task: active-preset-aware, bounded diagnostic; establish session
requirements and actual device behavior before real-time LED animation.

## Evidence availability

Source, docs and extracted findings are committed. Raw uploaded .pcapng/.smk37
files are not in Git and may need reattachment in a new task. Attachment paths
and /tmp files are not durable. No claim that all hardware details or firmware
behavior are resolved. Some earlier documents describe historical milestones;
this file and the latest capture-specific findings take precedence.

### Latest utility update

LED probe 0.3.0 adds active MidiSuite preset detection, validated pad record
reads, ACK-gated writes with per-preset addressing, readback, and Copy log.
Codecs/read parsing were verified offline against the last 102-message capture.
Hardware confirmation is pending. If reading fails, it sends no colour writes.
Source updates trigger only the lightweight LED probe build, not JUCE/VST3.
