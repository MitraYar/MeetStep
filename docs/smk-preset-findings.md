# SMK 37 Pro preset comparison

User supplied two MidiSuite .smk37 exports differing only in pad 1 colour.
Analysis is offline; no commands were sent to hardware.

- Both files: 18,915 bytes.
- `pad 1 color 76E1FF.smk37`: SHA256
  `1041379838e0fd248564b67c085334b006ba6eb87b90150dcb4170b524b66cd0`.
- `pad 1 color E8E225.smk37`: SHA256
  `a2ae5543dced532022486b345d020fe408c06edc8d566a78e4cec3ab53d87c86`.
- Exactly three changed bytes, at zero-based offsets 283–285 (0x11B–0x11D).
  They match the filename RGB values in R,G,B order.
- At offset 279 (0x117): `09 28 00 7F RR GG BB FF`.
  0x28 is note 40, matching the user's physical pad 1. The 09 field is
  consistent with zero-based MIDI channel 10, but its semantics are not
  independently established by this colour-only comparison.
- First 16 candidate records occur every 74 bytes (0x4A), beginning at 279.
  Their note bytes match the previously measured bank-1 mapping exactly:
  40 41 42 43 48 49 50 51 36 37 38 39 44 45 46 47.
- No other exported bytes change: no changing file-wide checksum was observed.
  This does not imply that transport packets have no checksum.

The first eight bytes match the colour-record form described by
https://github.com/spectalive/smc-pad/blob/main/reference/decode_preset.py.
This supports shared storage conventions, not confirmed wire compatibility.
SMC-PAD's documented record stride/flash addresses must not be reused for SMK.
A file offset is not established as a device flash address.

More record-like structures follow the first 16, but their note values do NOT
match the previously measured second bank. Do not label them bank 2 without
more evidence, or replace the measured controller mapping from this export.

## User-reported Windows ports

Inputs:
- 0: SMK-37 Pro Midi 0
- 1: MIDIIN2 (SMK-37 Pro Midi) 1
- 2: MIDIIN3 (SMK-37 Pro Midi) 2

Outputs (user omitted unrelated ports):
- 1: SMK-37 Pro Midi 1
- 2: MIDIOUT2 (SMK-37 Pro Midi) 2
- 3: MIDIOUT3 (SMK-37 Pro Midi) 3

The numeric indices are enumeration indices, not USB endpoints or stable IDs.
Three pairs exist; their playing/configuration/DIN roles remain unverified.

## Next evidence

Capture the official editor's USB exchange while changing this single pad's
colour, including connection/setup if needed. Compare packets, not just export
bytes. Determine whether the colour updates instantly or requires Apply/Send,
and whether it persists after a power cycle. Confirm the actual transport and
port before implementing a one-pad diagnostic write. Do not replay the preset
or an SMC-PAD session to the keyboard based on this offline comparison alone.
