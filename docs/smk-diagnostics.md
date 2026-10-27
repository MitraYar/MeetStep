# SMK USB diagnostics

The user connects SMK 37 Pro over USB and configures it using MidiSuite.

## Input-only observer

`tools/midi_observer.py` lists MIDI port names and records a selected input.
It never opens an output, never sends SysEx, and does not replay any captures.
Install Python on Windows, then from the checkout:

```
py -m pip install mido python-rtmidi
py tools/midi_observer.py
py tools/midi_observer.py --input 0 --seconds 30 --log smk-input.jsonl
```

Replace 0 with the selected input index. Listing ports alone opens no MIDI port.
Capture files are created exclusively, so existing files are not overwritten.
Listening is limited to 300 seconds; the queue and recorded message size are
bounded. Dropped messages or truncated records mean the capture is incomplete.

Close MeetStep and DAWs before opening an SMK input if the driver is exclusive.
Do not open the official editor concurrently unless the driver supports it.
The input-only observer can record replies and input events on exposed ports,
but does not spy on MidiSuite's output or proprietary USB traffic. It cannot
establish the LED protocol by itself.

First useful evidence: names of all USB MIDI ports, firmware/editor versions,
and a preset export if MidiSuite supports one. Change one pad colour in the
editor and compare two exported presets. This reveals configuration structure,
not necessarily a live LED command.

If direct output capture is needed, determine whether MidiSuite lets the user
select a MIDI destination. Only then consider an explicit forwarding bridge.
If it uses its own USB interface, a USB capture may be required instead.

Do not transmit SMC-PAD's flash addresses or unlock replay to SMK. Rate limiting
reduces traffic, but cannot make an incorrect memory-write command correct.
A later transmitting diagnostic tool must use model-confirmed commands,
one explicit operation at a time, bounded retries and a visible stop control.
