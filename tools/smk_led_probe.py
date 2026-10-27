"""Bounded SMK pad-1 probe, using only captured RGB addresses and values."""
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
root.title('MeetStep — SMK pad 1 LED probe')
root.geometry('720x460')
ui = queue.Queue()
cancel = threading.Event()
busy = False
replies = queue.Queue(maxsize=64)
for text in ['Close MidiSuite, MeetStep and DAWs before connecting.',
             'Select SMK input/output explicitly. Only pad 1 RGB is written.',
             'Target: #4CE437. Three writes maximum; no retries or device Save.']:
    ttk.Label(root, text=text).pack(anchor='w', padx=12, pady=3)
ttk.Label(root, text='SMK MIDI input (receives acknowledgements)').pack(anchor='w', padx=12)
inbox = ttk.Combobox(root, state='readonly', width=85)
inbox.pack(padx=12, pady=5)
ttk.Label(root, text='SMK MIDI output (sends RGB)').pack(anchor='w', padx=12)
outbox = ttk.Combobox(root, state='readonly', width=85)
outbox.pack(padx=12, pady=5)
log = tk.Text(root, height=11, state='disabled')
log.pack(fill='both', expand=True, padx=12, pady=8)
bar = ttk.Frame(root)
bar.pack(pady=8)


def refresh():
    try:
        inbox['values'] = mido.get_input_names()
        outbox['values'] = mido.get_output_names()
        inbox.set(''); outbox.set('')
    except Exception as error:
        ui.put(str(error))


def receive(message):
    if message.type == 'sysex':
        try:
            replies.put_nowait((time.monotonic(), bytes(message.bytes())))
        except queue.Full:
            pass


def run_probe(input_name, output_name):
    try:
        with mido.open_input(input_name, callback=receive), mido.open_output(output_name) as output:
            for address, value in zip((0x11B, 0x11C, 0x11D), (0x4C, 0xE4, 0x37)):
                if cancel.is_set():
                    ui.put('Stopped. No further writes.'); return
                while True:
                    try: replies.get_nowait()
                    except queue.Empty: break
                sent = time.monotonic()
                output.send(packet(address, value))
                ui.put(f'Sent RGB byte at 0x{address:X}: {value:02X}; waiting for ACK...')
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
            ui.put('All 3 writes acknowledged. Check pad 1 on the keyboard.')
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
    threading.Thread(target=run_probe, args=(inbox.get(), outbox.get()), daemon=True).start()


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
send_button = ttk.Button(bar, text='Set pad 1 to #4CE437 once', command=begin)
send_button.pack(side='left', padx=5)
ttk.Button(bar, text='Stop', command=cancel.set).pack(side='left', padx=5)
root.protocol('WM_DELETE_WINDOW', close)
refresh(); update(); root.mainloop()
