# Next standalone build: agreed changes

Recorded from user feedback after 0.2.0. These are requirements, not implemented features.

- Settings: a dropdown selecting one Master keyboard from MIDI input devices.
  Keep additional controller inputs separately selectable. Master keyboard uses
  the SMK pad/keyboard mapping. Additional input roles need explicit handling.
- Keep the DAW MIDI output for sequencer notes and clock.
- Add an independent controller-feedback output selector. It must not replace
  or automatically receive the DAW clock stream. Opening an output alone does
  not implement LEDs.
- Channel 6, CC 56: velocity used when entering new steps. Existing steps must
  retain their velocity. Proposed range 1–127; decide zero handling explicitly.
- Channel 6, CC 57: length used when entering new notes. Store per step, not
  just globally. Mapping/range is not yet agreed.
- Channel 6, CC 63: tempo. Proposed mapping uses current 30–300 BPM range;
  confirm feel and range during use.
- Space: Start / Stop. Text fields and settings must not trigger transport.
- Ctrl + physical slash key (English '/', Russian '.'): Settings.
  Plain slash retains Audition. Handle the modified shortcut first.

## LED investigation

Source: https://github.com/spectalive/smc-pad
Inspected HEAD: 8297442586df3ba1239485b54b272789eb4f1ade.

The author's SMC-PAD LEDs do not respond to ordinary Note On/Off or CC.
The repo documents USB SysEx on the device's configuration port, and BLE GATT
commands, with discovery, a configuration-read handshake and a keepalive.
Colour commands are named flash writes and address device-specific configuration
records. USB logical packets are packed into 7-bit SysEx; BLE uses raw packets.

This is evidence for SMC-PAD, not proof of compatibility with SMK 37 Pro.
Do not replay SMC-PAD unlock/configuration frames, flash addresses, or colour
writes on SMK blindly. First identify SMK ports, firmware and official editor;
capture the editor's discovery/configuration/colour traffic for this exact model.
Compare USB and BLE transport framing and whether colour changes are persistent.

Suggested sequence: add independent feedback port and MIDI/SysEx logging;
observe official-editor traffic; validate one pad; then map all 16 pads to the
selected drum's step state. Keep controller protocol isolated from sequencer
notes/clock. Do not enable repeated flash writes for playhead animation until
volatile control or write endurance is understood.

First feedback goal: occupied versus empty steps, refreshed on drum/pattern
changes and edits. Playhead animation is a separate follow-up after protocol
support and update cost are established. Hardware verification is required.

## Scope update: standalone only

User froze VST3. CI now builds and packages only MeetStepApp; plugin source is
retained for a possible later explicit request. Docs and LED utility changes
no longer trigger the expensive JUCE application build.

LED probe UI now separates pad selection, ten colours, and five brightness
levels. Apply writes only the selected pad, up to four acknowledged bytes.
Pads 1–5 are captured; bank-1 pads 6–16 use the matching preset layout with
inferred command applicability. Bank-2 pads 17–32 are shown disabled pending
address mapping. Auto-select the confirmed SMK-37 Pro Midi ports by name, not
transient global numeric indices. Colour/brightness control changes do not
transmit until Apply. GUI controls may be changed while sending, but the active
operation uses its original captured selection.

For bank 2: capture colour plus brightness changes on physical pad 1 and pad 16
with bank 2 selected, and preferably export the resulting .smk37 preset. This
can locate the bank and validate its stride without 16 separate captures.
