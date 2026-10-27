# MeetStep handoff / current project status

This file is the entry point for resuming work in a new Codex task.

**2026-10-28: LED transport rollback.** Only commit `2770a7a` (Build bounded
Windows SMK pad-one LED diagnostic) is accepted as the MIDI/SysEx baseline.
The later LED implementations at 5b53c6e, d373abe, ec35bf8 and 0feb67f
are rejected by user instruction; do not reuse their transport. `tools/smk_led_probe.py` is restored verbatim to that
baseline. Rejected RGB tester/launcher removed; the baseline has manual Actions
packaging. See [regression evidence](protocol/smk-led-regression.md).

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

Probe tools are separate from MeetStep, not integrated feedback. The accepted
pad-one baseline only writes captured preset-0 offsets 0x11B–0x11D and waits
for ACKs. It does not detect the active preset or support arbitrary pads.
The user confirmed two banks of 16 and Apply without Save. The all-black to
all-white capture identifies 32 RGB triples; physical ordering of records
17–32 is still unconfirmed. The requested 32-pad RGB sliders and random
colour/GUI selection on pad press remain pending a replacement based on the
accepted transport. No hardware-ready replacement is claimed.

## Evidence availability

Source, docs and extracted findings are committed. Raw uploaded .pcapng/.smk37
files are not in Git and may need reattachment in a new task. Attachment paths
and /tmp files are not durable. No claim that all hardware details or firmware
behavior are resolved. Some earlier documents describe historical milestones;
this file and the latest capture-specific findings take precedence.

### Latest utility status

The new 788-byte user capture proves three 21-byte SysEx writes and three
12-byte ACKs for the original pad-one baseline. The last LED and RGB utilities
fail before either MIDI port opens on Windows: `python-rtmidi==1.5.8` does not
expose the `set_buffer_size` method called by those implementations. The
previous Linux GUI tests did not exercise that Windows path. The initial
palette failure remains unexplained; it did not contain this call. See the
regression report for confirmed facts versus hypotheses and regression tests.

### Simple pad-colour replacement, 0.1.0

The user requested a new simple manual colour utility after the rollback.
`tools/smk_pad_colour.py` and `tools/smk_pad_colour_gui.py` implement it from
the accepted pad-one packet encoder and Mido input/output/callback path.
32 selectable RGB records; explicit Send button; three short writes with ACKs
and 100 ms spacing. No raw RtMidi API, buffer override, preset reads, Save,
brightness writes or automatic slider traffic. Select preset 1 (index 0) in
MidiSuite before use, then close MidiSuite. Bank-2 physical ordering remains
unconfirmed. Random-on-note behaviour is deferred from this simplified test.

The original pad-one source is unchanged. The previously rejected builds stay
withdrawn. The new implementation is a test candidate, not yet hardware-verified.
14 local tests pass, including the real Mido adapter with API-constrained RtMidi
test doubles, captured bytes, ACK/timeout/cancel, cleanup and GUI Send flow.
A separate `SMK Simple Pad Colour Windows` workflow builds the new EXE and
requires a packaged GUI/backend smoke test before artifact upload. Local Linux
checks do not establish successful Windows Actions execution or hardware results.
See `tools/SMK-PAD-COLOUR.md` for user instructions.

### Brightness and batch test, 0.2.0

User reports the simple 0.1.0 colour test appears to work; stability is not yet
established. New capture `all white to lights off.pcapng` independently proves
32 brightness fields at 0x11E + (record-1)*0x4A: exactly 32 FF→00 differences,
RGB unchanged FFFFFF, both full uploads match readback. This supersedes the
previous uncertainty about the byte following RGB for bank 2. See
`protocol/smk-32-brightness.md` and the extracted JSON address fixture.

0.2.0 adds a single-pad brightness slider, one-pass All pads, and optional
full/reduced alternation by record number. The slider controls one or all
pads on a 0–255 scale (default 255). With alternation it controls the reduced
percentage, default 80%: odd records 255, even records 204. Switching modes
restores the previous normal/percentage slider values.
The same accepted short-write Mido transport is retained, with one pair of
ports per batch, ACK per byte, 100 ms spacing and stop on first error.
128 messages take about 13 seconds. No Save. Hardware acceptance of the new
brightness/batch behaviour remains to be checked; bank-2 physical order is
still provisional.
