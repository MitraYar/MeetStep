# Source of the 32 RGB address fixture

`smk-32-rgb-addresses.json` was extracted offline from the user capture
`all black to all white.pcapng` (240528 bytes), SHA256
`6f5ad66f8e61cda9183d0078014977745c81484989d0783d962d3bb2653c3d5d`.

There are 1982 USBPcap packets and 174 complete validated SysEx messages.
Two region-5 preset uploads each cover offsets 0–18914 exactly once:
18 chunks of 1024 bytes plus 483 bytes. The following readback for each
covers the same range exactly once and matches the sent image byte-for-byte.
The only differences between the images are 32 RGB triples, all 000000 to
FFFFFF, at offsets `0x11B + (record - 1) * 0x4A` for records 1–32.

This fixture records those observed offsets, note fields and unchanged bytes
after RGB. It does not infer physical ordering for records 17–32. The user
confirmed two banks of 16 and Apply without Save. Byte after RGB is deliberately
excluded from the new sender: its interpretation is not uniform across the
records. No whole-preset upload is used for the simple colour test.

The simple sender targets preset 0 addresses only, matching both this capture
and the short working pad-one capture. The user must select that preset before
testing. Acceptance by every physical pad remains to be checked on hardware.
