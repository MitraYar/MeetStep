"""Exercise the accepted probe against captured wire data without opening MIDI."""
import ast
import json
import queue
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import mido

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = json.loads((ROOT / 'docs/protocol/smk-pad-one-working-capture.json').read_text())


def load_probe():
    # The accepted original launches Tk on import. Execute its unchanged
    # packet/callback/run functions only; avoid changing the accepted source.
    tree = ast.parse((ROOT / 'tools/smk_led_probe.py').read_text())
    names = {'packet', 'receive', 'run_probe'}
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    scope = dict(mido=mido, queue=queue, time=time, ui=queue.Queue(),
                 replies=queue.Queue(), cancel=threading.Event(),
                 ACK=bytes.fromhex(CAPTURE['messages'][1]['wire']))
    exec(compile(ast.Module(body=functions, type_ignores=[]), 'smk_led_probe.py', 'exec'), scope)
    return scope


class Port:
    def __init__(self, send=None):
        self.send = send
        self.closed = False
    def __enter__(self): return self
    def __exit__(self, *args): self.closed = True


class BaselineTests(unittest.TestCase):
    def test_packet_bytes_match_capture(self):
        probe = load_probe()
        for entry in CAPTURE['messages'][::2]:
            msg = probe['packet'](entry['address'], int(entry['value'], 16))
            self.assertEqual(bytes(msg.bytes()).hex(), entry['wire'])

    def run_probe(self, acknowledge):
        probe = load_probe()
        sent = []
        def open_input(name, *, callback):
            self.assertEqual(name, 'SMK input')
            probe['input_callback'] = callback
            return input_port
        def send(msg):
            sent.append(bytes(msg.bytes()).hex())
            if acknowledge:
                reply = CAPTURE['messages'][len(sent)*2-1]['wire']
                probe['input_callback'](mido.Message.from_bytes(bytes.fromhex(reply)))
        input_port, output_port = Port(), Port(send)
        with patch.object(mido, 'open_input', side_effect=open_input), patch.object(mido, 'open_output', return_value=output_port) as output:
            probe['run_probe']('SMK input', 'SMK output')
            output.assert_called_once_with('SMK output')
        self.assertTrue(input_port.closed)
        self.assertTrue(output_port.closed)
        return sent, list(probe['ui'].queue)

    def test_three_sends_require_three_captured_acks(self):
        sent, log = self.run_probe(True)
        self.assertEqual(sent, [x['wire'] for x in CAPTURE['messages'][::2]])
        self.assertIn('All 3 writes acknowledged. Check pad 1 on the keyboard.', log)
        self.assertIsNone(log[-1])

    def test_no_ack_stops_after_one_write(self):
        sent, log = self.run_probe(False)
        self.assertEqual(sent, [CAPTURE['messages'][0]['wire']])
        self.assertTrue(any(isinstance(x, str) and 'no matching ACK' in x for x in log))
        self.assertIsNone(log[-1])


if __name__ == '__main__': unittest.main()
