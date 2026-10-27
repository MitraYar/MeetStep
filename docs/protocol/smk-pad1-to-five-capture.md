# SMK USB SysEx: pads 1–5 and brightness

Source: user-provided `pad 1 to 5 test.pcapng`, 23,212 bytes.
USBPcap device address 14 during this capture; USB-MIDI OUT endpoint 0x04,
IN endpoint 0x84, cable 0. Address 14 differs from the previous capture's 8:
USB device addresses are temporary. Device address 14 sends/responds on the
same endpoints and protocol observed in the prior capture.

The five RGB triplets are at:
`0x11B`, `0x165`, `0x1AF`, `0x1F9`, `0x243`.
Each triplet advances by `0x4A` bytes (74 decimal). All 15 RGB writes in this
capture have value `FF`, white. Each write gets an acknowledgement before the
next component write. The output is only three small one-byte writes per pad,
not a preset upload.

The next address following each RGB triplet is a separate byte:
`0x11E`, `0x168`, `0x1B2`, `0x1FC`, `0x246`.
At each, the trace records `FE` followed by `FF`. This matches the user's
255→254→255 brightness manipulation. It is strong evidence that this field
controls per-pad brightness, though color export alone cannot establish its
full range or visual curve.

All traffic uses the already-polled session: approximately one read/status
poll per second, command 0x23 / region 0x04 / address 0 / length 100. This
trace does not include initial connection/session establishment, so a fresh
MeetStep connection may need a handshake. It contains five colors and five
brightness toggles, with successful 0x00 replies following each write.

There are 218 USBPcap packets total. The attached normalized JSON retains only
the 25 changed-byte writes; no raw packet data for unrelated devices is saved.
The packet decoder verified logical lengths and complement checksums, and
verified that USB-MIDI SysEx re-encodes to the captured wire bytes.

This makes LED feedback much more practical: updating a pad requires only
three acknowledged writes when its color changes; brightness is a fourth byte.
Before continuous sequencer updates, implement and validate session startup,
then probe one pad with an explicit output selection and a one-shot write.
Avoid redundant writes and never call the device's persistent Save command.
