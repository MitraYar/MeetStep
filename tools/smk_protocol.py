"""SMK SysEx framing from captured MidiSuite traffic; no device I/O."""
PRESET_SIZE = 18915


def encode(command, data):
    body = bytes(data)
    logical = bytes((0, 0x59, command)) + len(body).to_bytes(3, 'little') + body + bytes(((~sum(body)) & 255,))
    wire = bytearray([240])
    accumulator = bits = 0
    for value in logical:
        accumulator |= value << bits
        bits += 8
        while bits >= 7:
            wire.append(accumulator & 127)
            accumulator >>= 7
            bits -= 7
    if bits:
        wire.append(accumulator & 127)
    wire.append(247)
    return bytes(wire)


def decode(wire):
    if len(wire) < 3 or wire[0] != 240 or wire[-1] != 247:
        return None
    accumulator = bits = 0
    logical = bytearray()
    for value in wire[1:-1]:
        if value > 127:
            return None
        accumulator |= value << bits
        bits += 7
        while bits >= 8:
            logical.append(accumulator & 255)
            accumulator >>= 8
            bits -= 8
    if len(logical) < 7 or logical[:2] != b'\x00\x59':
        return None
    if len(logical) != 7 + int.from_bytes(logical[3:6], 'little'):
        return None
    if logical[-1] != ((~sum(logical[6:-1])) & 255):
        return None
    return logical[2], bytes(logical[6:-1])


def request(region, address, length):
    return encode(0x23, bytes([region]) + address.to_bytes(4, 'little') + length.to_bytes(3, 'little'))


def write_byte(address, value):
    return encode(0x22, bytes([5]) + address.to_bytes(4, 'little') + b'\x01\x00\x00' + bytes([value]))


def read_data(decoded, region, address, length):
    if decoded is None:
        return None
    command, data = decoded
    prefix = bytes([region]) + address.to_bytes(4, 'little') + length.to_bytes(3, 'little')
    if command == 0x23 and len(data) == 8 + length and data[:8] == prefix:
        return data[8:]
    return None
