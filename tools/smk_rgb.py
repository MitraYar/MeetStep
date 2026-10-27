"""32-record RGB tester. Run on Windows with mido/python-rtmidi installed."""
import queue
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
import mido
import rtmidi
from smk_protocol import PRESET_SIZE, decode, request, read_data, write_byte

NOTES = [40,41,42,43,48,49,50,51,36,37,38,39,44,45,46,47]


class Session:
    def __init__(self, incoming, outgoing, events):
        self.events = events
        self.replies = queue.Queue(maxsize=256)
        self.pending = {}
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.input = rtmidi.MidiIn()
        self.output = None
        try:
            if sys.platform == 'win32':
                self.input.set_buffer_size(4096, 4)
            self.input.ignore_types(sysex=False, timing=True, active_sense=True)
            self.input.set_callback(self.receive)
            self.input.open_port(self.input.get_ports().index(incoming))
            self.output = mido.open_output(outgoing)
        except Exception:
            self.input.close_port()
            raise
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def receive(self, event, _):
        try:
            msg = mido.Message.from_bytes(event[0])
            if msg.type == 'sysex':
                self.replies.put_nowait((time.monotonic(), bytes(msg.bytes())))
            elif msg.type == 'note_on' and msg.velocity > 0:
                self.events.put(('note', (msg.channel, msg.note)))
        except (ValueError, queue.Full):
            pass

    def exchange(self, wire, match):
        while not self.replies.empty():
            try: self.replies.get_nowait()
            except queue.Empty: break
        sent = time.monotonic()
        self.output.send(mido.Message.from_bytes(wire))
        while time.monotonic() - sent < 2 and not self.stop.is_set():
            try: stamp, raw = self.replies.get(timeout=.05)
            except queue.Empty: continue
            if stamp >= sent:
                value = match(decode(raw))
                if value is not None: return value
        raise RuntimeError('Reply timeout / stopped. Writes disabled; reconnect to resume.')

    def read(self, region, address, count):
        return self.exchange(request(region, address, count),
                             lambda d: read_data(d, region, address, count))

    def profile(self, active, offset, count):
        result = bytearray()
        while count:
            start = offset // 1009 * 1009
            size = min(1009, PRESET_SIZE-start)
            data = self.read(5, active*PRESET_SIZE+start, size)
            take = min(count, size-(offset-start))
            result.extend(data[offset-start:offset-start+take])
            offset += take
            count -= take
        return bytes(result)

    def submit(self, pad, rgb):
        with self.lock:
            self.pending[pad] = tuple(rgb)  # Coalesce slider updates per record.

    def run(self):
        try:
            active = self.read(4, 0, 100)[0]
            if active > 7: raise RuntimeError('Unsupported preset index')
            self.events.put(('log', f'Connected: preset index {active}. RGB only; no Save.'))
            while not self.stop.wait(.02):
                with self.lock:
                    item = next(iter(self.pending.items()), None)
                    if item: del self.pending[item[0]]
                if not item: continue
                pad, rgb = item
                offset = 0x11B + pad*74
                if self.read(4, 0, 100)[0] != active:
                    raise RuntimeError('Preset changed. Reconnect before writing.')
                record = self.profile(active, offset-4, 8)
                if record[0] != 9 or record[2:4] != bytes((0,127)):
                    raise RuntimeError(f'Record {pad+1} has unexpected layout; stopped.')
                for index, value in enumerate(rgb):
                    if self.stop.is_set(): raise RuntimeError('Stopped')
                    self.exchange(write_byte(active*PRESET_SIZE+offset+index, value),
                                  lambda d: True if d == (0,b'\0') else None)
                actual = self.profile(active, offset, 3)
                if actual != bytes(rgb): raise RuntimeError('RGB readback mismatch')
                if self.read(4,0,100)[0] != active: raise RuntimeError('Preset changed during write')
                self.events.put(('log', f'Record {pad+1}: #{actual.hex().upper()} verified'))
        except Exception as error:
            self.events.put(('log', str(error)))
        finally:
            self.stop.set()
            self.input.cancel_callback()
            self.input.close_port()
            if self.output: self.output.close()
            self.events.put(('closed', self))


class App:
    def __init__(self, root):
        self.root = root
        self.session = None
        self.events = queue.Queue()
        self.selected = 0
        self.colors = [(0,0,0)]*32
        self.bindings = {(9,n):i for i,n in enumerate(NOTES)}
        self.learn = False
        self.loading = False
        self.debounce = None
        root.title('SMK RGB tester — 32 records')
        ttk.Label(root, text='Close MidiSuite. Bank 2 record order requires physical verification. No Save commands.').pack()
        self.input = ttk.Combobox(root, width=65, state='readonly'); self.input.pack()
        self.output = ttk.Combobox(root, width=65, state='readonly'); self.output.pack()
        bar = ttk.Frame(root); bar.pack()
        self.refresh_button = ttk.Button(bar,text='Refresh ports',command=self.refresh); self.refresh_button.pack(side='left')
        self.connect_button = ttk.Button(bar,text='Connect',command=self.connect); self.connect_button.pack(side='left')
        ttk.Button(bar,text='Disconnect / Stop',command=self.disconnect).pack(side='left')
        self.buttons = []
        for bank in range(2):
            group = ttk.LabelFrame(root,text=f'Bank {bank+1} / records {bank*16+1}–{bank*16+16}'); group.pack()
            for j in range(16):
                i=bank*16+j
                b=tk.Button(group,text=str(i+1),width=7,command=lambda i=i:self.select(i))
                b.grid(row=j//8,column=j%8); self.buttons.append(b)
        self.label = ttk.Label(root); self.label.pack()
        self.sliders=[]
        for name in 'RGB':
            scale=tk.Scale(root,label=name,from_=0,to=255,orient='horizontal',length=560,command=self.slider)
            scale.pack(); self.sliders.append(scale)
        self.random = tk.BooleanVar(value=True)
        ttk.Checkbutton(root,text='Random colour on pad press + select in GUI',variable=self.random).pack()
        ttk.Button(root,text='Bind selected record to next pad press',command=self.arm).pack()
        ttk.Button(root,text='Apply RGB',command=self.apply).pack()
        self.log=tk.Text(root,height=8,width=90);self.log.pack()
        ttk.Button(root,text='Copy log',command=self.copy).pack()
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.refresh();self.select(0);self.poll()

    def copy(self):
        self.root.clipboard_clear();self.root.clipboard_append(self.log.get('1.0','end-1c'))

    def refresh(self):
        try:
            self.input['values']=mido.get_input_names();self.output['values']=mido.get_output_names()
            for box in (self.input,self.output):
                if box['values']: box.current(0)
        except Exception as e: self.events.put(('log',str(e)))

    def connect(self):
        if self.session: return
        try:
            self.session=Session(self.input.get(),self.output.get(),self.events)
            for box in (self.input,self.output): box.configure(state='disabled')
            self.refresh_button.configure(state='disabled')
        except Exception as e: self.events.put(('log',str(e)))

    def disconnect(self):
        if self.session: self.session.stop.set()

    def arm(self):
        self.learn=True
        self.events.put(('log',f'Press pad to bind record {self.selected+1}; this press will not send RGB.'))

    def select(self, i):
        if self.debounce: self.root.after_cancel(self.debounce); self.debounce=None
        self.learn=False
        self.selected=i;self.loading=True
        for s,v in zip(self.sliders,self.colors[i]):s.set(v)
        for j,b in enumerate(self.buttons):b.configure(relief='sunken' if i==j else 'raised')
        bound=[f'ch {ch+1}, note {note}' for (ch,note),p in self.bindings.items() if p==i]
        self.label.configure(text=f'Record {i+1} — '+(', '.join(bound) or 'unbound; verify address then bind'))
        self.loading=False

    def slider(self, _):
        if self.loading:return
        values=tuple(s.get() for s in self.sliders)
        if values==self.colors[self.selected]:return
        self.colors[self.selected]=values
        if self.debounce:self.root.after_cancel(self.debounce)
        self.debounce=self.root.after(180,self.apply)

    def apply(self):
        self.debounce=None
        if self.session and not self.session.stop.is_set():
            self.session.submit(self.selected,self.colors[self.selected])

    def poll(self):
        while not self.events.empty():
            kind,value=self.events.get()
            if kind=='log':self.log.insert('end',value+'\n');self.log.see('end')
            elif kind=='closed' and value is self.session:
                self.session=None
                for box in (self.input,self.output):box.configure(state='readonly')
                self.refresh_button.configure(state='normal')
            elif kind=='note':
                if self.learn:
                    old=self.bindings.get(value)
                    if old is not None and old!=self.selected:
                        self.events.put(('log',f'Conflict: note already bound to record {old+1}; unchanged.'))
                        continue
                    self.bindings={k:v for k,v in self.bindings.items() if v!=self.selected}
                    self.bindings[value]=self.selected;self.select(self.selected)
                elif value in self.bindings:
                    self.select(self.bindings[value])
                    if self.random.get():
                        self.colors[self.selected]=tuple(random.randrange(256) for _ in range(3))
                        self.select(self.selected);self.apply()
                else:self.events.put(('log',f'Unbound: ch {value[0]+1}, note {value[1]}. Select record and Bind.'))
        self.root.after(30,self.poll)

    def close(self):
        self.disconnect()
        if self.session:self.root.after(100,self.close)
        else:self.root.destroy()


if __name__=='__main__':
    mido.set_backend('mido.backends.rtmidi')
    root=tk.Tk();App(root);root.mainloop()
