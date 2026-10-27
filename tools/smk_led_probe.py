"""SMK bank-1 colour/brightness probe with acknowledged, bounded writes."""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
import mido
mido.set_backend('mido.backends.rtmidi')
ACK = bytes.fromhex('f0 00 32 01 08 00 00 00 00 7f 01 f7')


def packet(address, value):
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


root = tk.Tk()
root.title('MeetStep — SMK LED palette')
root.geometry('820x770')
ui = queue.Queue()
cancel = threading.Event()
busy = False
replies = queue.Queue(maxsize=64)
for text in ['Close MidiSuite, MeetStep and DAWs before connecting.',
             'Bank 1: pads 1–5 captured; 6–16 inferred from your preset layout.',
             'Bank 2 is disabled until its address mapping is confirmed.']:
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


def run_probe(input_name, output_name, pad, rgb, level):
    try:
        with mido.open_input(input_name, callback=receive), mido.open_output(output_name) as output:
            base = 0x11B + (pad-1)*74
            values = [int(rgb[i:i+2],16) for i in (0,2,4)] + [level]
            for address, value in zip(range(base,base+4),values):
                if cancel.is_set():
                    ui.put('Stopped. No further writes.'); return
                while True:
                    try: replies.get_nowait()
                    except queue.Empty: break
                sent = time.monotonic()
                output.send(packet(address, value))
                ui.put(f'Sent byte at 0x{address:X}: {value:02X}; waiting for ACK...')
                deadline = sent + 2
                acknowledged = False
                while time.monotonic() < deadline and not cancel.is_set():
                    try: timestamp, raw = replies.get(timeout=0.05)
                    except queue.Empty: continue
                    if timestamp >= sent and raw == ACK:
                        acknowledged = True; break
                if not acknowledged:
                    ui.put('Stopped: no matching ACK (or Stop pressed). No retries.'); return
                ui.put('ACK received.')
                if cancel.wait(0.1):
                    ui.put('Stopped.'); return
            ui.put(f'Pad {pad}: RGB #{rgb}, brightness {level}/255 — all 4 writes acknowledged.')
    except Exception as error:
        ui.put(f'Cannot complete probe: {error}')
    finally:
        ui.put(None)


def begin():
    global busy
    if busy: return
    if not inbox.get() or not outbox.get():
        ui.put('Choose both SMK ports first.'); return
    busy = True
    cancel.clear()
    send_button['state'] = 'disabled'
    refresh_button['state'] = 'disabled'
    inbox['state'] = outbox['state'] = 'disabled'
    threading.Thread(target=run_probe, args=(inbox.get(), outbox.get(), selected_pad.get(), selected_colour.get(), selected_brightness.get()), daemon=True).start()


def update():
    global busy
    try:
        while True:
            item = ui.get_nowait()
            if item is None:
                busy = False
                send_button['state'] = refresh_button['state'] = 'normal'
                inbox['state'] = outbox['state'] = 'readonly'
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
send_button = ttk.Button(bar, text='Apply colour + brightness to selected pad', command=begin)
send_button.pack(side='left', padx=5)
ttk.Button(bar, text='Stop', command=cancel.set).pack(side='left', padx=5)
root.protocol('WM_DELETE_WINDOW', close)
refresh(); update(); root.mainloop()
