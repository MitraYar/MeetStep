"""Read-only checks of frozen oracle and captured framing; no hardware access."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('frozen', ROOT/'reference/smk_pad_colour.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


class OracleTests(unittest.TestCase):
    def test_all_fixed_golden_packets_match_frozen_maximum(self):
        lines = (ROOT/'fixtures/led-maximum.tsv').read_text().splitlines()
        self.assertEqual(len(lines), 128)
        for line in lines:
            pad, r, g, b, enable, expected = line.split()
            self.assertEqual(bytes(oracle.block_packet(0x11b+int(pad)*0x4a,
                [int(r), int(g), int(b), int(enable)]).bytes()).hex(), expected)

    def test_oracle_block_encoder_matches_independent_capture(self):
        capture = json.loads((ROOT/'fixtures/smk-captured-block-write.json').read_text())
        self.assertEqual(bytes(oracle.block_packet(capture['address'],
            bytes.fromhex(capture['value'])).bytes()).hex(), capture['wire'])

    def test_short_write_and_ack_match_working_capture(self):
        capture = json.loads((ROOT/'fixtures/smk-pad-one-working-capture.json').read_text())
        for entry in capture['messages']:
            if entry['command'] == 34:
                self.assertEqual(bytes(oracle.packet(entry['address'], int(entry['value'],16)).bytes()).hex(), entry['wire'])
            else:
                self.assertEqual(oracle.ACK.hex(), entry['wire'])


if __name__ == '__main__':
    unittest.main()
