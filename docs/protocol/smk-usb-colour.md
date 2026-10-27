# SMK 37 Pro USB colour change: captured evidence

Capture: `colors 76E1FF to 4CE437.pcapng`, 7,979,136 bytes.
USBPcap linktype 249, 17,786 packets. Only relevant MIDI frames are retained
in the adjacent JSON; unrelated USB devices' traffic is not committed.
Analysis was offline; no commands sent to hardware.

## Transport

Device address 8 in this capture, VID 4353 / PID B64B. USB MIDIStreaming
interface 4, OUT endpoint 0x04, IN endpoint 0x84, USB-MIDI cable number 0.
Descriptors associate these endpoints with three logical MIDI jacks.
This suggests trying the first logical MIDI port, but the exact Windows
friendly-name mapping must still be verified; USB addresses are not Windows
MIDI enumeration indices.

USB-MIDI event framing is stripped before decoding SysEx. The payload uses
the same LSB-first 8-to-7-bit packing as the SMC-PAD reference. Decoded logical
packets are `00 59 command length24LE data checksum`. All 38 complete messages
have valid lengths and checksums (`~sum(data) & 255`). Re-encoding produces
the original wire bytes (verified offline).

## Colour operation

| Frame | Command | Region | Address | Length | Value | Reply frame |
|---|---|---|---|---|---|---|
|12153|0x22|0x05|0x11B|1|0x4C|12155|
|12157|0x22|0x05|0x11C|1|0xE4|12159|
|12161|0x22|0x05|0x11D|1|0x37|12163|

Each outbound message is 20 MIDI bytes including F0/F7. Each reply is the
same 12-byte SysEx, decoded `00 59 00 01 00 00 00 FF`, consistent with the
reference protocol's success acknowledgement. First write to final reply:
approximately 2.685 ms in this capture, not a guaranteed sustained update rate.

First write decoded:
`00 59 22 09 00 00 05 1B 01 00 00 01 00 00 4C 91`.

Addresses exactly match the pad-1 RGB offsets established by preset comparison.
This establishes the correspondence for this pad in the captured session only.
Do not generalize to other profiles or pads without validation.
Only the new RGB 4C E4 37 appears in these writes; the old colour is reported
by the user/filename, not read back by this capture.

## Session and limits

There are 16 identical read/status requests at approximately 1 Hz, each with
one response: command 0x23, region 0x04, address 0, length 100.
The colour operation is three single-byte writes with replies between them;
no full preset transfer accompanies it in the captured interval.
The capture starts with an already-active polling session; discovery and
initial configuration-reading/unlock are not present. It cannot prove whether
the writes work from a fresh connection without MidiSuite.

Combined with the user's Apply-versus-Save observations, this is strong evidence
for temporary colour updates. The capture alone does not prove internal memory
technology or endurance; no device Save operation was identified or exercised.

Next diagnostic: explicitly select the keyboard's input/output, send only the
three captured pad-1 writes once, waiting for a reply to each and stopping on
timeout; no automatic retries or address scanning. Initially use the exact
captured target colour. Validate cold-session requirements before integrating
step feedback. A separate capture including MidiSuite connection is needed
only if session initialization blocks the bounded probe.
