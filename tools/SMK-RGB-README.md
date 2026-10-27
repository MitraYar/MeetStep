# RGB tester withdrawn

The 32-record RGB tester from commit `0feb67f` is rejected for MIDI/SysEx use
by the user. Its executable entry point, launcher and Actions packaging have
been removed. Do not use old `MeetStep-SMK-RGB-Windows-x64` artifacts or reuse
its MIDI implementation. Historical source remains in Git for diagnosis only.

The only accepted hardware-tested transport baseline is commit `2770a7a`
(`Build bounded Windows SMK pad-one LED diagnostic`), restored verbatim as
`tools/smk_led_probe.py`. It writes only pad 1 RGB = #4CE437 at preset-0
offsets, waits for three ACKs, and does not read/switch presets or Save.
This is a diagnostic baseline, not the requested 32-pad product.

See [the regression investigation](../docs/protocol/smk-led-regression.md).
Future RGB controls/randomisation must be rebuilt on the accepted transport
and validated on Windows and the physical controller before being called working.
