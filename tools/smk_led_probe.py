"""SMK bank-1 colour/brightness probe with acknowledged, bounded writes."""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
import mido
mido.set_backend('mido.backends.rtmidi')
from smk_protocol import PRESET_SIZE, decode, request, write_byte, read_data
VERSION = '0.3.0'


root = tk.Tk()
root.title('MeetStep — SMK LED palette ' + VERSION)
root.geometry('980x800')
ui = queue.Queue()
cancel = threading.Event()
busy = False
replies = queue.Queue(maxsize=64)
for text in ['Close MidiSuite, MeetStep and DAWs. Read status first; no automatic preset switching.',
             'Bank 1: pads 1–5 captured; 6–16 inferred from your preset layout.',
             'Apply reads the active MidiSuite preset and checks the pad record before writing.']:
    ttk.Label(root, text=text).pack(anchor='w', padx=12, pady=3)
ttk.Label(root, text='SMK MIDI input (receives acknowledgements)').pack(anchor='w', padx=12)
inbox = ttk.Combobox(root, state='readonly', width=85)
inbox.pack(padx=12, pady=5)
ttk.Label(root, text='SMK MIDI output (sends RGB)').pack(anchor='w', padx=12)
outbox = ttk.Combobox(root, state='readonly', width=85)
outbox.pack(padx=12, pady=5)

selected_pad = tk.IntVar(value=1)
selected_colour = tk.StringVar(value='4CE437')
selected_brightness = tk.IntVar(value=255)
notes = (40,41,42,43,48,49,50,51,36,37,38,39,44,45,46,47)
pads = ttk.LabelFrame(root, text='1. Select pad — Bank 1')
pads.pack(fill='x', padx=12, pady=5)
for index, note in enumerate(notes):
    ttk.Radiobutton(pads, text=f'{index+1} ({note})', variable=selected_pad,
                    value=index+1).grid(row=index//8,column=index%8,padx=5,pady=8)
bank2 = ttk.LabelFrame(root, text='Bank 2 — addresses not yet confirmed')
bank2.pack(fill='x', padx=12, pady=5)
for index in range(16):
    ttk.Button(bank2, text=str(index+17), state='disabled', width=8).grid(
        row=index//8,column=index%8,padx=4,pady=3)
colours = ttk.LabelFrame(root, text='2. Select colour')
colours.pack(fill='x', padx=12, pady=5)
for index, (name, rgb) in enumerate([
    ('White','FFFFFF'),('Red','FF0000'),('Orange','FF8000'),('Yellow','FFFF00'),
    ('Green','00FF00'),('Lime','4CE437'),('Cyan','00FFFF'),('Blue','0000FF'),
    ('Purple','8000FF'),('Pink','FF00FF')]):
    tk.Radiobutton(colours,text=name,variable=selected_colour,value=rgb,
                   background='#'+rgb,foreground='black' if rgb!='0000FF' else 'white',
                   indicatoron=False,width=11,selectcolor='#'+rgb).grid(
                       row=index//5,column=index%5,padx=5,pady=5)
brightness = ttk.LabelFrame(root, text='3. Brightness')
brightness.pack(fill='x', padx=12,pady=5)
for index, (label,value) in enumerate([('0%',0),('25%',64),('50%',128),('75%',192),('100%',255)]):
    ttk.Radiobutton(brightness,text=label,variable=selected_brightness,value=value).grid(
        row=0,column=index,padx=18,pady=6)

preset_label = tk.StringVar(value='Active MidiSuite preset: not read yet')
ttk.Label(root, textvariable=preset_label).pack(anchor='w', padx=12)
log = tk.Text(root, height=7, state='disabled')
log.pack(fill='both', expand=True, padx=12, pady=8)
bar = ttk.Frame(root)
bar.pack(pady=8)


def refresh():
    try:
        inbox['values'] = mido.get_input_names()
        outbox['values'] = mido.get_output_names()
        inbox.set(''); outbox.set('')
        for box in (inbox,outbox):
            for name in box['values']:
                if name.startswith('SMK-37 Pro Midi'):
                    box.set(name); break
    except Exception as error:
        ui.put(str(error))


def receive(message):
    if message.type == 'sysex':
        try:
            replies.put_nowait((time.monotonic(), bytes(message.bytes())))
        except queue.Full:
            pass


def exchange(output, wire, matcher, description):
    if cancel.is_set():
        raise RuntimeError('Stopped by user.')
    while True:
        try: replies.get_nowait()
        except queue.Empty: break
    sent = time.monotonic()
    output.send(mido.Message.from_bytes(list(wire)))
    ui.put(description)
    deadline = sent + 2
    ignored = 0
    while time.monotonic() < deadline and not cancel.is_set():
        try: timestamp, raw = replies.get(timeout=0.05)
        except queue.Empty: continue
        if timestamp < sent:
            continue
        decoded = decode(raw)
        result = matcher(decoded)
        if result is not None:
            return result
        ignored += 1
    raise RuntimeError(f'{description}: no matching reply ({ignored} unrelated/invalid SysEx). '
                       'Stopped; no retries. Check input/output ports or session setup.')


def read(output, region, address, length):
    return exchange(output, request(region, address, length),
                    lambda decoded: read_data(decoded, region, address, length),
                    f'Read region {region}, address 0x{address:X}, {length} bytes')


def read_profile_bytes(output, active, offset, length):
    # Use the same 1009-byte chunk reads observed in MidiSuite's capture.
    start = (offset // 1009) * 1009
    count = min(1009, PRESET_SIZE - start)
    chunk = read(output, 5, active * PRESET_SIZE + start, count)
    within = offset-start
    if within + length > len(chunk):
        raise RuntimeError('Requested pad record spans an unsupported read boundary.')
    return chunk[within:within+length]


def run_probe(input_name, output_name, pad, rgb, level, read_only=False):
    try:
        ui.put(f'LED probe {VERSION} | Input: {input_name} | Output: {output_name}')
        with mido.open_input(input_name, callback=receive), mido.open_output(output_name) as output:
            status = read(output, 4, 0, 100)
            active = status[0]
            if not 0 <= active <= 7:
                raise RuntimeError(f'Unsupported active preset index {active}; no writes sent.')
            ui.put(('preset', active))
            ui.put(f'Active MidiSuite preset index {active}; base 0x{active * PRESET_SIZE:X}.')
            base = active * PRESET_SIZE + 0x11B + (pad-1)*74
            record = read_profile_bytes(output, active, base-active*PRESET_SIZE-4, 8)
            expected = bytes((9, notes[pad-1], 0, 127))
            if record[:4] != expected:
                raise RuntimeError(f'Pad {pad} record does not match the known layout: '
                                   f'{record.hex(" ")}. No writes sent.')
            ui.put(f'Pad {pad}: current RGB #{record[4:7].hex().upper()}, brightness {record[7]}/255.')
            if read_only:
                ui.put('Read complete. No writes sent.'); return
            # Abort if the user changed preset while the record was being read.
            if read(output, 4, 0, 100)[0] != active:
                raise RuntimeError('Active preset changed during read. No writes sent; try again.')
            values = [int(rgb[i:i+2],16) for i in (0,2,4)] + [level]
            for address, value in zip(range(base,base+4),values):
                exchange(output, write_byte(address, value),
                         lambda decoded: True if decoded == (0, b'\x00') else None,
                         f'Write 0x{address:X} = {value:02X}; waiting for ACK')
                ui.put('ACK received.')
                if cancel.wait(0.1):
                    raise RuntimeError('Stopped by user. Already acknowledged bytes may have changed.')
            actual = read_profile_bytes(output, active, base-active*PRESET_SIZE, 4)
            if actual != bytes(values):
                raise RuntimeError(f'Writes acknowledged but readback differs: {actual.hex(" ")}.')
            final_status = read(output, 4, 0, 100)
            if final_status[0] != active:
                raise RuntimeError('Preset changed during the operation; inspect the selected preset.')
            ui.put(f'Preset index {active}, pad {pad}: #{rgb}, brightness {level}/255. '
                   'All 4 ACKs and readback confirmed; check the physical LED.')
    except Exception as error:
        ui.put(f'Cannot complete probe: {error}')
    finally:
        ui.put(None)


def begin(read_only=False):
    global busy
    if busy: return
    if not inbox.get() or not outbox.get():
        ui.put('Choose both SMK ports first.'); return
    busy = True
    cancel.clear()
    send_button['state'] = 'disabled'
    refresh_button['state'] = read_button['state'] = 'disabled'
    inbox['state'] = outbox['state'] = 'disabled'
    threading.Thread(target=run_probe, args=(inbox.get(), outbox.get(), selected_pad.get(), selected_colour.get(), selected_brightness.get(), read_only), daemon=True).start()


def update():
    global busy
    try:
        while True:
            item = ui.get_nowait()
            if item is None:
                busy = False
                send_button['state'] = refresh_button['state'] = read_button['state'] = 'normal'
                inbox['state'] = outbox['state'] = 'readonly'
            elif isinstance(item, tuple):
                preset_label.set(f'Active MidiSuite preset: index {item[1]} (slot {item[1]+1})')
            else:
                log['state'] = 'normal'; log.insert('end', item+'\n'); log.see('end'); log['state'] = 'disabled'
    except queue.Empty:
        pass
    root.after(50, update)


def close():
    cancel.set()
    if busy: root.after(100, close)
    else: root.destroy()


refresh_button = ttk.Button(bar, text='Refresh ports', command=refresh)
refresh_button.pack(side='left', padx=5)
read_button = ttk.Button(bar, text='Read preset + pad', command=lambda: begin(True))
read_button.pack(side='left', padx=5)
send_button = ttk.Button(bar, text='Apply colour + brightness to selected pad', command=begin)
send_button.pack(side='left', padx=5)
ttk.Button(bar, text='Stop', command=cancel.set).pack(side='left', padx=5)
def copy_log():
    root.clipboard_clear()
    root.clipboard_append(log.get('1.0', 'end-1c'))

ttk.Button(bar, text='Copy log', command=copy_log).pack(side='left', padx=5)
root.protocol('WM_DELETE_WINDOW', close)
refresh(); update(); root.mainloop()
