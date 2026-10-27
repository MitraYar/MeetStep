# SMK preset switching: captured evidence

Source: `pad 1 to 16 change presets.pcapng`, 123,832 bytes, 1,024 captured
USBPcap packets. Device address 16, OUT 0x04, IN 0x84, MIDI cable 0.
All 102 reconstructed M-VAVE SysEx messages have matching declared lengths
and complement checksums. Analysis is offline; no hardware writes were sent.

There are two writes, both command 0x22, region 4, address 0, length 1:
- Frame 21 writes 07, acknowledged in frame 22.
- Frame 519 writes 00, acknowledged in frame 520.
Subsequent status reads (command 0x23, region 4, address 0, length 100) expose
07 and then 00 as the first response data byte. This strongly identifies a
zero-based active preset selector. User-facing preset numbers may be 8 and 1;
the exact GUI labels were not supplied.

After each write MidiSuite READS a complete preset from region 5; it does not
upload the palette during this operation. Each preset is 18,915 bytes (0x49E3),
read as 18 chunks of 1,009 bytes plus a final 753-byte chunk. All byte positions
were covered exactly once per reconstructed preset.
- Preset 7: base address 0x20535 = 7 * 18,915.
- Preset 0: base address 0.

The first 16 pad records begin at relative offset 0x117 with stride 0x4A.
Preset 7 has pads 1–8 RGB 00 AA 7F and pads 9–16 FF 00 FF. All brightness
bytes are FF. Preset 0 has varied light blue colours, with pad 1 76 E1 FF.
This matches the user's description and earlier exports. Both presets have the
same bank-1 MIDI note mapping. See adjacent JSON for decoded colour tables.

## Consequence for the diagnostic tool

The current LED probe always writes region 5 offsets relative to preset 0
(0x11B + (pad-1)*74), without reading the active preset. With preset 7 active,
those writes may target a different preset and produce no visible change.
This is a plausible explanation for acknowledged-but-invisible writes, not a
confirmed diagnosis of the reported failure: the probe's log was not provided.
A timeout remains a separate possible port/session/transport issue.

Next fix should first read current preset status through the selected MIDI
ports, validate the response and selector range, then use the confirmed
per-preset base when preparing colour writes. Do not hard-code preset 7 or
switch the user's preset automatically. Cross-preset write semantics and
cold-session initialization still need device validation. The capture begins
inside an established session; it does not show full connection setup.

This capture confirms 16 physical pads in two presets. It does not establish
the 16 pad-bank-2 addresses. Preset switching and pad-bank switching are
separate concepts.

## Diagnostic 0.3.0 implementation

The updated utility reads region-4 status and validates active index 0–7,
then reads the pad record through the same 1,009-byte preset chunk requests
observed in the capture. It validates the known channel/note record prefix,
checks the active preset again, and only then sends up to four one-byte writes
using `active * 18915 + 0x11B + (pad-1)*74`. Each write requires its own ACK.
It reads back the affected bytes and checks that the active preset has not
changed. It never selects a preset or calls Save to device. No retries.

`Read preset + pad` performs only reads; `Copy log` provides portable diagnosis.
The raw packet codec was verified against all 102 reconstructed capture
messages with exact decode/encode round trips; the status request matches the
captured bytes exactly. Real-device success for nonzero preset writes and cold
connection setup is still to be confirmed by the user. Slot labels in the UI
are index+1, but logs retain the actual zero-based index.
