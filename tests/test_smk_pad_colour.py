"""Exercise the actual Mido/RtMidi adapter using API-constrained fake devices."""
import importlib
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock, patch

import mido
import rtmidi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from smk_pad_colour import ACK, colour_packets, send_colour
from smk_protocol import decode  # Independent capture-validated decoder, no device I/O.

CAPTURE = json.loads((ROOT / 'docs/protocol/smk-pad-one-working-capture.json').read_text())
ADDRESSES = json.loads((ROOT / 'docs/protocol/smk-32-rgb-addresses.json').read_text())


class ColourTests(unittest.TestCase):
    def setUp(self):
        self.adapter = importlib.import_module('mido.backends.rtmidi')
        # These specs deliberately prohibit invented methods such as set_buffer_size.
        self.input = Mock(spec_set=rtmidi.MidiIn)
        self.output = Mock(spec_set=rtmidi.MidiOut)
        for device, name in ((self.input, 'SMK IN'), (self.output, 'SMK OUT')):
            device.get_ports.return_value = [name]
            device.get_current_api.return_value = rtmidi.API_WINDOWS_MM
        self.callback = None
        self.input.set_callback.side_effect = lambda cb: setattr(self, 'callback', cb)
        self.reply = ACK
        self.cancel = threading.Event()
        self.logs = []
        self.sent = []

        def send(wire):
            self.sent.append(bytes(wire))
            if self.reply is not None:
                self.callback((list(self.reply), 0.001), None)
        self.output.send_message.side_effect = send
        self.patches = [patch.object(self.adapter.rtmidi, 'MidiIn', return_value=self.input),
                        patch.object(self.adapter.rtmidi, 'MidiOut', return_value=self.output)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def send(self, pad=1, rgb=(0x4C, 0xE4, 0x37)):
        # Run the real backend/port opening path, not a replacement Session.
        send_colour('SMK IN', 'SMK OUT', pad, rgb, self.cancel, self.logs.append,
                    timeout=.03, spacing=0)

    def test_real_mido_adapter_opens_ports_and_matches_working_capture(self):
        self.send()
        self.assertEqual(self.sent, [bytes.fromhex(x['wire']) for x in CAPTURE['messages'][::2]])
        self.input.open_port.assert_called_once_with(0)
        self.output.open_port.assert_called_once_with(0)
        self.input.ignore_types.assert_called_once_with(False, False, True)
        self.input.close_port.assert_called_once()
        self.output.close_port.assert_called_once()
        self.input.delete.assert_called_once()
        self.output.delete.assert_called_once()
        self.assertIn('Все 3 ACK получены', self.logs[-1])

    def test_all_32_addresses_match_black_white_capture_only_rgb_written(self):
        for record in ADDRESSES:
            for colour in ((0, 0, 0), (255, 255, 255), (1, 127, 128)):
                messages = colour_packets(record['record'], colour)
                self.assertEqual(len(messages), 3)
                for message, address, value in zip(messages, record['rgb_offsets'], colour):
                    command, data = decode(bytes(message.bytes()))
                    self.assertEqual(command, 0x22)
                    self.assertEqual(data, b'\x05' + address.to_bytes(4, 'little') + b'\x01\0\0' + bytes([value]))

    def test_last_pad_uses_same_send_path(self):
        self.send(32, (255, 0, 127))
        self.assertEqual([int.from_bytes(decode(x)[1][1:5], 'little') for x in self.sent], [0xA11, 0xA12, 0xA13])

    def test_no_ack_sends_only_one_byte_and_closes_ports(self):
        self.reply = None
        with self.assertRaises(TimeoutError): self.send()
        self.assertEqual(len(self.sent), 1)
        self.input.close_port.assert_called_once()
        self.output.close_port.assert_called_once()

    def test_wrong_sysex_is_not_accepted_as_ack(self):
        self.reply = bytes.fromhex(CAPTURE['messages'][0]['wire'])
        with self.assertRaises(TimeoutError): self.send()
        self.assertEqual(len(self.sent), 1)

    def test_cancel_after_first_ack_stops_remaining_writes(self):
        original = self.output.send_message.side_effect
        def send(wire):
            original(wire)
            self.cancel.set()
        self.output.send_message.side_effect = send
        with self.assertRaises(InterruptedError): self.send()
        self.assertEqual(len(self.sent), 1)
        self.input.close_port.assert_called_once()

    def test_output_open_error_closes_input_and_sends_nothing(self):
        self.output.open_port.side_effect = RuntimeError('port busy')
        with self.assertRaises(OSError): self.send()
        self.input.close_port.assert_called_once()
        self.assertFalse(self.sent)

    def test_input_open_error_never_opens_output(self):
        self.input.open_port.side_effect = RuntimeError('port busy')
        with self.assertRaises(OSError): self.send()
        self.output.open_port.assert_not_called()
        self.assertFalse(self.sent)

    def test_invalid_pad_or_rgb_never_opens_a_port(self):
        for pad, rgb in [(0,(1,2,3)),(33,(1,2,3)),(1,(256,0,0)),(1,(1,2)),(1,(-1,2,3))]:
            with self.assertRaises(ValueError): self.send(pad,rgb)
        self.input.open_port.assert_not_called()

    def test_single_brightness_endpoints_and_midpoint(self):
        for value in (0, 204, 255):
            self.sent.clear()
            send_colour('SMK IN', 'SMK OUT', 32, (255,255,255), self.cancel,
                        self.logs.append, brightness=value, spacing=0)
            self.assertEqual(len(self.sent), 4)
            data=decode(self.sent[-1])[1]
            self.assertEqual(int.from_bytes(data[1:5], 'little'), 0xA14)
            self.assertEqual(data[-1], value)

    def test_all_brightness_addresses_match_capture_and_alternate(self):
        fixture=json.loads((ROOT/'docs/protocol/smk-32-brightness.json').read_text())
        for alternate in (False, True):
            self.sent.clear()
            send_colour('SMK IN', 'SMK OUT', 7, (1,2,3), self.cancel,
                        self.logs.append, all_pads=True, alternate=alternate,
                        brightness=0, spacing=0)
            self.assertEqual(len(self.sent), 128)
            for i,change in enumerate(fixture['changes']):
                group=[decode(w)[1] for w in self.sent[i*4:i*4+4]]
                self.assertEqual([int.from_bytes(d[1:5],'little') for d in group],
                                 list(range(change['address']-3,change['address']+1)))
                self.assertEqual([d[-1] for d in group[:3]], [1,2,3])
                self.assertEqual(group[-1][-1], (204 if i%2 else 255) if alternate else 0)

    def test_alternating_slider_percentage(self):
        for percent, expected in [(0,0),(40,102),(80,204),(100,255)]:
            self.sent.clear()
            send_colour('SMK IN','SMK OUT',1,(1,2,3),self.cancel,self.logs.append,
                        all_pads=True,alternate=True,alternate_percent=percent,spacing=0)
            levels=[decode(w)[1][-1] for w in self.sent[3::4]]
            self.assertEqual(levels,[255,expected]*16)

    def test_all_batch_stops_at_first_missing_ack(self):
        original=self.output.send_message.side_effect
        def send(wire):
            if len(self.sent)==5: self.reply=None
            original(wire)
        self.output.send_message.side_effect=send
        with self.assertRaises(TimeoutError):
            send_colour('SMK IN','SMK OUT',1,(1,2,3),self.cancel,self.logs.append,
                        all_pads=True,timeout=.03,spacing=0)
        self.assertEqual(len(self.sent),6)
        self.input.open_port.assert_called_once_with(0)
        self.output.open_port.assert_called_once_with(0)
        self.input.close_port.assert_called_once()
        self.output.close_port.assert_called_once()

    def test_speed_modes_packet_counts_values_and_waits(self):
        for mode, count, pause in [('maximum',32,0),('fast',128,0),('balanced',128,.005)]:
            self.sent.clear()
            with patch.object(self.cancel,'wait',return_value=False) as wait:
                result=send_colour('SMK IN','SMK OUT',1,(1,127,255),self.cancel,self.logs.append,
                                   all_pads=True,alternate=True,alternate_percent=80,speed=mode)
            self.assertEqual(len(self.sent),count)
            self.assertEqual(result['acknowledged'],count)
            self.assertTrue(result['success'])
            self.assertEqual(wait.call_count,127 if pause else 0)
            if pause: wait.assert_called_with(pause)
            for pad in range(32):
                if mode=='maximum':
                    command,data=decode(self.sent[pad])
                    self.assertEqual(command,0x22)
                    self.assertEqual(data[0],5)
                    self.assertEqual(int.from_bytes(data[1:5],'little'),0x11b+pad*74)
                    self.assertEqual(data[5:8],bytes([4,0,0]))
                    self.assertEqual(list(data[8:]),[1,127,255,204 if pad%2 else 255])

    def test_packed_matches_captured_block_format(self):
        from smk_pad_colour import block_packet
        capture=json.loads((ROOT/'docs/protocol/smk-captured-block-write.json').read_text())
        message=block_packet(capture['address'],bytes.fromhex(capture['value']))
        self.assertEqual(bytes(message.bytes()).hex(),capture['wire'])

    def test_exchange_timing_excludes_port_open_and_close(self):
        clock=[0.0]
        def add(seconds):clock[0]+=seconds
        self.input.open_port.side_effect=lambda _:add(1)
        self.output.open_port.side_effect=lambda _:add(2)
        original=self.output.send_message.side_effect
        def send(wire):add(.002);original(wire)
        self.output.send_message.side_effect=send
        self.output.close_port.side_effect=lambda:add(10)
        with patch('smk_pad_colour.time.monotonic',side_effect=lambda:clock[0]):
            result=send_colour('SMK IN','SMK OUT',1,(1,2,3),self.cancel,self.logs.append,
                               brightness=255,all_pads=True,speed='maximum')
        self.assertAlmostEqual(result['elapsed_ms'],64)
        self.assertAlmostEqual(result['ack_mean_ms'],2)

    def test_packed_timeout_stops_without_fallback(self):
        self.reply=None
        with self.assertRaises(TimeoutError):
            send_colour('SMK IN','SMK OUT',1,(1,2,3),self.cancel,self.logs.append,
                        all_pads=True,speed='maximum',timeout=.03)
        self.assertEqual(len(self.sent),1)
        self.assertTrue(any('ПРЕРВАНО' in line and 'ACK 0/32' in line for line in self.logs))

    def test_pre_cancelled_operation_does_not_open_ports(self):
        self.cancel.set()
        with self.assertRaises(InterruptedError): self.send()
        self.input.open_port.assert_not_called()


if __name__ == '__main__': unittest.main()
