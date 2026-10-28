# Frozen LED oracle

`smk_pad_colour.py` is copied unchanged from commit
`d8cbffdc243b7e60ef136542bf1daf10b366d81c` on `build/smk-rgb-tester`.
Its blob is also unchanged at `e5fd6fb6ec8dc4f32b16bea2adda7e50405cdff3`.
Use `speed='maximum'`: contiguous RGB+enable, one exact ACK per packet,
no inserted delay, no retry or automatic fallback. Do not edit this oracle to
make an integration pass. The utility is not released or rebuilt by this change.

The user identifies Actions run 40612063252 as the hardware-tested LED utility
and run 40550476978 as the baseline sequencer. Their Actions metadata is not
accessible from this environment; these run-to-commit mappings are unconfirmed.
The base sequencer `src/Standalone.cpp` at main 8db4580 is byte-identical to
commit 4b25c729260907daa4ebf422943c26723aab9b86 (standalone 0.2.0).

`led-maximum.tsv` is a fixed oracle-derived wire fixture for all 32 addresses
and four RGBA boundary/mixed values. Captured JSON files retain their original
provenance fields. CI compares the fixture and C++ encoder with the frozen
oracle and checks the oracle against captured block-write framing. Fixture
changes require an explained protocol change, not simply a green CI.

No byte test or simulated ACK test establishes JUCE delivery or physical pad
mapping. Physical bank-2 positions still require controller verification.
