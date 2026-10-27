#!/usr/bin/env python3
"""Read-only MIDI observer: never opens an output or sends messages.
Windows: py -m pip install mido python-rtmidi
List: py tools/midi_observer.py
Listen: py tools/midi_observer.py --input 0 --seconds 30
"""
import argparse
import json
import queue
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=int, help='Input index shown by the list command')
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--log', type=Path, default=Path('meetstep-midi-observer.jsonl'))
    args = parser.parse_args()
    if not 1 <= args.seconds <= 300:
        parser.error('--seconds must be between 1 and 300')
    try:
        import mido
        mido.set_backend('mido.backends.rtmidi')
        inputs = mido.get_input_names()
        outputs = mido.get_output_names()
    except (ImportError, RuntimeError) as error:
        parser.exit(1, f'MIDI backend unavailable: {error}\nInstall: py -m pip install mido python-rtmidi\n')
    print('INPUTS:')
    for index, name in enumerate(inputs):
        print(f'  {index}: {name}')
    print('OUTPUTS (listed only; never opened):')
    for index, name in enumerate(outputs):
        print(f'  {index}: {name}')
    if args.input is None:
        return
    if not 0 <= args.input < len(inputs):
        parser.error('Invalid input index; list ports again')
    messages = queue.Queue(maxsize=1024)
    dropped = 0

    def receive(message):
        nonlocal dropped
        try:
            messages.put_nowait((time.monotonic(), message))
        except queue.Full:
            dropped += 1

    started = time.monotonic()
    try:
        # Exclusive creation preserves any existing capture.
        with args.log.open('x', encoding='utf-8') as log:
            with mido.open_input(inputs[args.input], callback=receive):
                print(f'Listening for {args.seconds}s. No MIDI output is opened. Ctrl+C stops.')
                log.write(json.dumps({'port': inputs[args.input], 'mode': 'input-only'}) + '\n')
                try:
                    while time.monotonic() - started < args.seconds:
                        try:
                            timestamp, message = messages.get(timeout=0.1)
                        except queue.Empty:
                            continue
                        raw = message.bytes()
                        record = {'seconds': round(timestamp-started, 6),
                                  'type': message.type, 'length': len(raw),
                                  'hex': ' '.join(f'{byte:02X}' for byte in raw[:4096]),
                                  'truncated': len(raw) > 4096}
                        log.write(json.dumps(record) + '\n')
                        print(json.dumps(record))
                except KeyboardInterrupt:
                    pass
                finally:
                    log.write(json.dumps({'dropped_messages': dropped}) + '\n')
    except (OSError, RuntimeError) as error:
        parser.exit(1, f'Capture failed: {error}\nClose other apps using this input, or choose another log filename.\n')
    print(f'Saved: {args.log}; dropped messages: {dropped}')


if __name__ == '__main__':
    main()
