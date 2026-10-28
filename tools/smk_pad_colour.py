"""Simple RGB sender derived from the accepted 2770a7a pad-one transport."""
import queue
import threading
import time

import mido

VERSION = '0.3.1'
SPEED_MODES = {'fast': (False, 0.0), 'maximum': (True, 0.0), 'balanced': (False, 0.005)}
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


def block_packet(address, values):
    """Experimental contiguous write; same framing/checksum as short writes."""
    values = bytes(values)
    data = bytes([5]) + address.to_bytes(4, 'little') + len(values).to_bytes(3, 'little') + values
    logical = bytes([0, 0x59, 0x22]) + len(data).to_bytes(3, 'little') + data + bytes([(~sum(data)) & 255])
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
                *, backend=None, timeout=2.0, spacing=0.1, brightness=None,
                all_pads=False, alternate=False, alternate_percent=80, speed=None):
    """Send a bounded RGB/brightness batch using the accepted Mido transport."""
    colour_packets(pad, rgb)  # Validate before opening either port.
    if brightness is not None and (type(brightness) is not int or not 0 <= brightness <= 255):
        raise ValueError('Яркость должна быть от 0 до 255.')
    if alternate and not all_pads:
        raise ValueError('Чередование применяется в режиме «Все пэды».')
    if type(alternate_percent) is not int or not 0 <= alternate_percent <= 100:
        raise ValueError('Процент чередования должен быть от 0 до 100.')
    packed = False
    if speed is not None:
        if speed not in SPEED_MODES:
            raise ValueError('Неизвестный режим скорости.')
        packed, spacing = SPEED_MODES[speed]
    targets = list(range(1, 33)) if all_pads else [pad]
    messages, labels = [], []
    for target in targets:
        level = (255 if target % 2 else round(255 * alternate_percent / 100)) if alternate else brightness
        if all_pads and level is None:
            level = 255
        if packed:
            values = list(rgb) + ([] if level is None else [level])
            messages.append(block_packet(0x11B + (target-1)*0x4A, values))
            labels.append(f'пэд {target} RGB' + (f' + яркость {level}' if level is not None else ''))
        else:
            messages.extend(colour_packets(target, rgb))
            labels.extend(f'пэд {target} {channel}' for channel in 'RGB')
            if level is not None:
                messages.append(packet(0x11E + (target - 1) * 0x4A, level))
                labels.append(f'пэд {target} яркость {level}')
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

    log(f'Пэды {targets}, RGB #{bytes(rgb).hex().upper()}; пресет 1 (индекс 0).')
    log(f'IN: {input_name}\nOUT: {output_name}')
    log(f'Скорость: {speed or "legacy"}; сообщений: {len(messages)}; пауза {spacing*1000:g} мс; ACK обязателен.')
    wire = [bytes(message.bytes()) for message in messages]
    traces = []  # Format and render details only after timing the exchange.
    started = last_ack = None
    tx = acknowledged = unrelated = 0
    latencies = []
    success = False
    try:
        with backend.open_input(input_name, callback=receive), backend.open_output(output_name) as output:
            log('Оба MIDI-порта открыты.')
            for index, message in enumerate(messages):
                if cancel.is_set():
                    raise InterruptedError(f'Остановлено; отправлено {tx} из {len(messages)} сообщений.')
                while True:
                    try: replies.get_nowait()
                    except queue.Empty: break
                sent = time.monotonic()
                if started is None: started = sent
                output.send(message)
                tx += 1
                traces.append(('TX', index, wire[index]))
                while time.monotonic() - sent < timeout and not cancel.is_set():
                    try: stamp, raw = replies.get(timeout=min(0.05, timeout))
                    except queue.Empty: continue
                    if stamp >= sent and raw == ACK:
                        acknowledged += 1
                        last_ack = stamp
                        latencies.append((stamp-sent)*1000)
                        traces.append(('ACK', index, raw))
                        break
                    unrelated += 1
                    traces.append(('RX другой SysEx', index, raw[:64]))
                else:
                    if cancel.is_set():
                        raise InterruptedError('Остановлено во время ожидания ACK. Изменения могут быть частичными.')
                    raise TimeoutError(f'Нет ACK за {timeout:g} с. Отправка остановлена без повторов.')
                if index < len(messages)-1 and spacing > 0 and cancel.wait(spacing):
                    raise InterruptedError('Остановлено между сообщениями. Изменения могут быть частичными.')
            success = True
    finally:
        finished = time.monotonic()
        elapsed = ((last_ack if success else finished) - started)*1000 if started is not None else None
        result = dict(success=success, sent=tx, acknowledged=acknowledged, planned=len(messages),
                      elapsed_ms=elapsed, unrelated=unrelated,
                      ack_mean_ms=sum(latencies)/len(latencies) if latencies else None,
                      ack_max_ms=max(latencies) if latencies else None)
        for kind, index, raw in traces:
            log(f'{kind} {index+1}/{len(messages)} {labels[index]}: {raw.hex(" ").upper()}')
        timing = f'{elapsed:.2f} мс' if elapsed is not None else 'обмен не начат'
        log(f'ИТОГ [{"УСПЕХ" if success else "ПРЕРВАНО"}]: TX {tx}/{len(messages)}, ACK {acknowledged}/{len(messages)}, {timing}; посторонних SysEx: {unrelated}.')
        if latencies:
            log(f'ACK среднее {result["ack_mean_ms"]:.3f} мс, максимум {result["ack_max_ms"]:.3f} мс.')
    log(f'Все {acknowledged} ACK получены. Проверьте физические пэды.')
    return result


def main():
    from smk_pad_colour_gui import run
    run()


if __name__ == '__main__':
    main()
