# SMK LED diagnostic regression — 2026-10-28

## Accepted baseline and rejected builds

User decision: only **2770a7a, Build bounded Windows SMK pad-one LED diagnostic**
is accepted as a working MIDI/SysEx transport baseline. All later LED utility
implementations are rejected for reuse, including `5b53c6e`, `d373abe`,
`ec35bf8` and `0feb67f`. This decision does not discard independently verified
capture data or mean every rejected version has the same root cause.

`tools/smk_led_probe.py` is restored byte-for-byte from 2770a7a. The RGB tester
and its launcher are removed; its UI requirements remain pending. Actions is
manual-only and packages only the pad-one baseline with a distinct artifact
name. Old GitHub artifacts have not been deleted or relabelled remotely; do
not use them. Historical sources remain in Git solely for investigation.
The sequencer and frozen VST3 scope are unaffected.

## New capture proves a complete short exchange

Source: `Build bounded Windows SMK pad-one LED diagnostic.pcapng`, 788 bytes.
SHA256: `93ac496beb45cb3fb2e840459ff507d7a9cd58b6d0e8329b554a11ad83e19a9a`.
The adjacent `smk-pad-one-working-capture.json` preserves all decoded messages
and original SysEx bytes, including frame numbers and timestamps.

USBPcap bus 1/device 16, OUT 0x04, IN 0x84, MIDI cable 0. Six USB packets,
six complete SysEx messages; no partial messages or checksum/length failures.
All six re-encode to exactly their original bytes.

| Frames | Operation | Reply | Observed OUT-to-IN interval |
| --- | --- | --- | --- |
| 1 → 2 | CMD 22, region 5, address 0x11B, length 1, value 4C | CMD 00, data 00 | 0.401 ms |
| 3 → 4 | CMD 22, region 5, address 0x11C, length 1, value E4 | CMD 00, data 00 | 0.413 ms |
| 5 → 6 | CMD 22, region 5, address 0x11D, length 1, value 37 | CMD 00, data 00 | 0.999 ms |

The writes are 21-byte SysEx, ACKs 12 bytes. OUT messages are approximately
107/109 ms apart, consistent with the baseline's 100 ms delay after each ACK.
These are measurements of this capture, not a sustained throughput guarantee.

The captured writes exactly match the baseline `packet()` output for RGB
#4CE437. Given the baseline's ACK-gated loop, sending writes 2 and 3 is also
consistent with its input callback accepting the preceding ACK. The trace
contains no status/read requests, full-preset upload, preset switching or
separate Save operation. It confirms the short exchange in this session;
it does not establish cold-session initialization or 32-pad addressing.

## Confirmed failure: nonexistent Python API, before either port opens

The workflow pins **mido 1.3.3 / python-rtmidi 1.5.8** in both the working
baseline and the rejected builds. Changing package versions is not needed
to explain the difference.

Commit ec35bf8 replaced `mido.open_input(name, callback=receive)` with a raw
`rtmidi.MidiIn()` wrapper. Under `sys.platform == 'win32'` it calls
`device.set_buffer_size(4096, 4)` before `open_port`. The RGB tester 0feb67f
copied this into `Session.__init__` before input and output opening.

**python-rtmidi 1.5.8 has no Python method `MidiIn.set_buffer_size`.** Its
bundled C++ RtMidi has `setBufferSize`, but the Cython wrapper does not expose
it. The Python method cannot be inferred from the C++ API name.

Therefore the Windows branch raises AttributeError, unwinds initialization,
and never reaches `mido.open_output` or `send`. This fully explains the
reported error and absence of SysEx for those two versions. It is not a
bad RGB address/checksum, rejected controller command, or a failure to Save.
The failure is before transmission.

Both Windows branches were reproduced offline using a MidiIn test double
without the nonexistent method and port-open sentinels: neither input-open
nor output-open was reached. This is a control-flow reproduction, not a
Windows hardware test. The installed 1.5.8 class and published 1.5.8 Cython
source independently confirm the missing method.

## Why the baseline succeeds

2770a7a uses `mido.open_input(..., callback=receive)` and `mido.open_output`.
Mido 1.3.3's RtMidi input calls `ignore_types(False, False, True)`, enabling
SysEx. There is no custom buffer API call. It immediately sends the three
known short writes, waiting for each captured ACK before continuing. No
status read or large preset read gates the writes.

The baseline and later byte encoder produce identical wire bytes for these
three writes. The new trace therefore supports retaining the packet format;
it does not support retaining the failed transport initialization.

## Earlier rejected versions: separate findings and limits

- **5b53c6e palette:** still uses Mido input/output and the original encoder.
  It adds address selection, a fourth byte labelled brightness, and port
  preselection. It does not contain `set_buffer_size` or a prerequisite read.
  Its exact reported hardware failure cannot be diagnosed from this working
  build's capture. Wrong port/preset or another runtime error remain hypotheses,
  not established causes. It remains rejected by user decision.
- **d373abe active-preset probe:** still uses Mido, but gates writes on status
  and 1009-byte preset-chunk reads. The full data reply occupies **1173 SysEx
  bytes**. The published 1.5.8 source initializes `inputData_.bufferSize` to
  **1024**, and WinMM allocates from that field. Its callback forwards each
  WinMM buffer; Mido attempts to parse each as a complete message. A split
  reply can thus be dropped or fail the checksum matcher and time out before
  colour writes. This is a source-level incompatibility; no failed-build
  capture is supplied to prove that this was the user's actual failure.
  A working status-read request would still appear on USB, so this cannot by
  itself explain a capture with zero outbound SysEx.

Important source-documentation inconsistency: the wrapper docstring claims
8192-byte default buffers and RtMidi.cpp retains an unused 8196 macro. The
actual allocation reads the 1024 field initialized in RtMidi.h. Do not use
the stale docstring or macro alone to claim large reads work. This analysis
has not measured the actual deployed Windows wheel's receive capacity.

Published package integrity checked against PyPI SHA256:

- Windows CPython 3.12 amd64 wheel:
  `052c89933cae4fca354012d8ca7248f4f9e1e3f062471409d48415a7f7d7e59e`
- 1.5.8 source archive:
  `7f9ade68b068ae09000ecb562ae9521da3a234361ad5449e83fc734544d004fa`

## Verification and future work

The previous RGB tests covered GUI selection, simulated notes and an isolated
read helper. They substituted the Session and never exercised Windows
initialization. PyInstaller success likewise cannot validate Connect.
This explains how the programming error escaped those checks.

Current tests compare all three baseline sends and ACKs against this capture,
exercise the real baseline run loop with fake ports, check context cleanup,
and verify that a missing ACK prevents subsequent writes. They do not claim
physical hardware success beyond the user's capture.

Future 32-pad controls/randomisation must be built from the accepted Mido
transport and validated incrementally: Windows Connect, one short captured
write/ACK, then pad selection and note callbacks. Status/long-read additions
need separate Windows receive-path evidence; do not restore the nonexistent
buffer call or quietly make large read success a prerequisite for every write.
Do not reuse the byte after RGB as a universal brightness field: the 32-record
capture shows it has differing values in the second half.
