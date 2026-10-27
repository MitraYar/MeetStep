# SMK RGB tester (Windows)

Install Python 3.12 for Windows, then double-click `run-smk-rgb.cmd`.
The launcher creates a local venv and installs pinned MIDI dependencies.
Alternatively run `python smk_rgb.py` with mido 1.3.3 and python-rtmidi 1.5.8.
The existing **SMK LED probe Windows** GitHub workflow also builds
`MeetStep-SMK-RGB.exe` as a separate artifact after the changes are pushed.

Close MidiSuite and other applications holding the MIDI ports. Choose the
controller input and output, then Connect. Input must receive SysEx ACKs
and pad Note On messages. If they arrive on different logical ports, this
version requires a suitable shared port/routing; a separate pad input is
not implemented. Refresh while disconnected if the device is reconnected.

Select one of 32 records and adjust RGB sliders (0–255). Values are sent
after a 180 ms pause; Apply RGB also sends explicitly. The app checks the
active preset, writes only three RGB bytes with individual ACKs, reads them
back and checks the preset again. On error it stops and closes the ports;
reconnect after correcting the cause. Stop may leave an already sent colour
partially applied. Colours are not automatically restored on exit.

Bank 1 starts with the previously measured channel-10 note mapping.
Bank 2 is deliberately unbound: the capture establishes 32 RGB addresses,
but not the physical order of the second bank. Test a record manually,
select that record, click Bind, then press its physical pad. Learning does
not send a colour. Conflicting note/channel bindings are rejected.
Bindings last for the current session only. The two groups in the UI label
record ranges; bank-2 physical order requires verification.

With the random-colour checkbox enabled (default), each positive-velocity
Note On from a bound pad selects its record in the GUI, generates RGB and
queues the colour. Note Off/zero-velocity Note On do not trigger it.
Unbound notes are logged. Colours shown in the sliders are requested local
values, not a full palette read from the controller. Successful readback is
reported in the log; verify the physical LED as well.

No preset switching, full-preset upload, brightness or Save-to-device
commands are used. Nonzero preset writes and actual device behaviour still
require hardware testing. Windows executable packaging is configured but
has not been executed on this Linux machine.
