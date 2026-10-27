"""Simple RGB sender derived from the accepted 2770a7a pad-one transport."""
import queue
import threading
import time

import mido

VERSION = '0.1.0'
ACK = bytes.fromhex('f0 00 32 01 08 00 00 00 00 7f 01 f7')


def packet(address, value):
    # Encoding copied verbatim from the hardware-tested pad-one baseline.
    data = [5, *address.to_bytes(4, 'little'), 1, 0, 0, value]
    logical = [0, 0x59, 0x22, len(data), 0, 0, *data, (~sum(data)) & 255]
    encoded = []
    acc = bits = 0
    for byte in logical:
        acc |= byte << bits
        bits += 8
        while bits >= 7:
            encoded.append(acc & 127)
            acc >>= 7
            bits -= 7
    if bits:
        encoded.append(acc & 127)
    return mido.Message('sysex', data=encoded)


def colour_packets(pad, rgb):
    if type(pad) is not int or not 1 <= pad <= 32:
        raise ValueError('Номер пэда должен быть от 1 до 32.')
    if len(rgb) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in rgb):
        raise ValueError('RGB: три целых числа от 0 до 255.')
    base = 0x11B + (pad - 1) * 0x4A
    return [packet(base + i, v) for i, v in enumerate(rgb)]


def send_colour(input_name, output_name, pad, rgb, cancel, log,
                *, backend=None, timeout=2.0, spacing=0.1):
    """Open Mido ports, send three short writes, require each ACK, close ports.

    Addresses belong to preset index 0. No reads, buffer overrides, brightness,
    full-preset transfers, preset switching or persistent Save are performed.
    """
    messages = colour_packets(pad, rgb)
    if not input_name or not output_name:
        raise ValueError('Выберите MIDI-вход и MIDI-выход.')
    if cancel.is_set():
        raise InterruptedError('Остановлено до открытия портов.')
    backend = backend or mido.Backend('mido.backends.rtmidi')
    replies = queue.Queue(maxsize=64)

    def receive(message):
        if message.type == 'sysex':
            try:
                replies.put_nowait((time.monotonic(), bytes(message.bytes())))
            except queue.Full:
                pass

    log(f'Пэд {pad}, RGB #{bytes(rgb).hex().upper()}; пресет 1 (индекс 0).')
    log(f'IN: {input_name}\nOUT: {output_name}')
    # Keep the same public Mido open/callback/send path as 2770a7a.
    with backend.open_input(input_name, callback=receive), backend.open_output(output_name) as output:
        log('Оба MIDI-порта открыты.')
        for index, message in enumerate(messages):
            if cancel.is_set():
                raise InterruptedError(f'Остановлено; отправлено {index} из 3 байтов RGB.')
            while True:
                try:
                    replies.get_nowait()
                except queue.Empty:
                    break
            sent = time.monotonic()
            output.send(message)
            log(f'TX {"RGB"[index]}: {bytes(message.bytes()).hex(" ").upper()}')
            while time.monotonic() - sent < timeout and not cancel.is_set():
                try:
                    stamp, raw = replies.get(timeout=min(0.05, timeout))
                except queue.Empty:
                    continue
                if stamp >= sent and raw == ACK:
                    log('RX ACK: ' + raw.hex(' ').upper())
                    break
                log('RX другой SysEx: ' + raw[:64].hex(' ').upper())
            else:
                if cancel.is_set():
                    raise InterruptedError('Остановлено во время ожидания ACK. Цвет мог измениться частично.')
                raise TimeoutError('Нет ACK за 2 секунды. Отправка остановлена без повторов; цвет мог измениться частично.')
            if index < 2 and cancel.wait(spacing):
                raise InterruptedError('Остановлено между компонентами RGB. Цвет мог измениться частично.')
    log('Все 3 ACK получены. Проверьте цвет физического пэда.')


def main():
    from smk_pad_colour_gui import run
    run()


if __name__ == '__main__':
    main()
