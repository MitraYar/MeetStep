"""GUI for the simple, manually triggered SMK RGB diagnostic."""
import json
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import colorchooser, ttk

import mido
from smk_pad_colour import VERSION, send_colour


class App:
    def __init__(self, root, backend=None, enumerate_ports=True):
        self.root = root
        self.backend = backend or mido.Backend('mido.backends.rtmidi')
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.worker = None
        self.closing = False
        self.controls = []
        root.title(f'MeetStep — цвет пэдов {VERSION}')
        root.minsize(720, 680)
        body = ttk.Frame(root, padding=12)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Перед тестом выберите пресет 1 в MidiSuite, затем закройте MidiSuite.').pack(anchor='w')
        ttk.Label(body, text='Цвет отправляется только кнопкой «Отправить цвет».').pack(anchor='w', pady=(0, 8))
        self.input = self.port_box(body, 'MIDI-вход — ответы контроллера')
        self.output = self.port_box(body, 'MIDI-выход — контроллер')
        self.refresh_button = ttk.Button(body, text='Обновить список портов', command=self.refresh)
        self.refresh_button.pack(anchor='w', pady=6)
        self.controls.append(self.refresh_button)
        self.pad = tk.IntVar(root, value=1)
        self.pad_buttons = []
        for bank in range(2):
            title = 'Банк 1 — пэды 1–16' if bank == 0 else 'Банк 2 — ячейки 17–32; физический порядок проверяем'
            frame = ttk.LabelFrame(body, text=title, padding=6)
            frame.pack(fill='x', pady=4)
            for j in range(16):
                number = bank * 16 + j + 1
                button = ttk.Radiobutton(frame, text=str(number), variable=self.pad, value=number)
                button.grid(row=j // 8, column=j % 8, padx=10, pady=3)
                self.pad_buttons.append(button)
                self.controls.append(button)
        self.rgb = [tk.IntVar(root, value=v) for v in (0x4C, 0xE4, 0x37)]
        for label, variable in zip('RGB', self.rgb):
            scale = tk.Scale(body, label=label, variable=variable, from_=0, to=255,
                             orient='horizontal', command=lambda _: self.preview_colour())
            scale.pack(fill='x')
            self.controls.append(scale)
        self.preview = tk.Label(body, text='', height=2)
        self.preview.pack(fill='x', pady=4)
        colours = ttk.Frame(body)
        colours.pack(fill='x')
        for label, rgb in [('Чёрный', (0, 0, 0)), ('Белый', (255, 255, 255)),
                           ('Красный', (255, 0, 0)), ('Зелёный', (0, 255, 0)), ('Синий', (0, 0, 255))]:
            b = ttk.Button(colours, text=label, command=lambda rgb=rgb: self.set_colour(rgb))
            b.pack(side='left', padx=2)
            self.controls.append(b)
        chooser = ttk.Button(colours, text='Палитра…', command=self.choose_colour)
        chooser.pack(side='left', padx=2)
        self.controls.append(chooser)
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=8)
        self.send_button = ttk.Button(actions, text='Отправить цвет', command=self.begin)
        self.send_button.pack(side='left', padx=3)
        self.controls.append(self.send_button)
        self.stop_button = ttk.Button(actions, text='Стоп', command=self.cancel.set, state='disabled')
        self.stop_button.pack(side='left', padx=3)
        ttk.Button(actions, text='Копировать лог', command=self.copy_log).pack(side='right')
        self.status = tk.StringVar(root, value='Выберите MIDI-вход и выход.')
        ttk.Label(body, textvariable=self.status, wraplength=680).pack(anchor='w')
        self.log = tk.Text(body, height=9, width=85, state='disabled')
        self.log.pack(fill='both', expand=True, pady=6)
        self.preview_colour()
        self.append_log(f'Pad Colour {VERSION}; основа MIDI: рабочий pad-one 2770a7a.')
        if enumerate_ports:
            self.refresh()
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.poll_id = root.after(40, self.poll)

    def port_box(self, parent, label):
        ttk.Label(parent, text=label).pack(anchor='w')
        box = ttk.Combobox(parent, state='readonly', width=82)
        box.pack(fill='x', pady=(0, 4))
        return box

    def refresh(self):
        try:
            for box, names in ((self.input, self.backend.get_input_names()),
                               (self.output, self.backend.get_output_names())):
                previous = box.get()
                box['values'] = names
                box.set(previous if previous in names else '')
            self.status.set('Выберите оба порта контроллера. Номера портов могут меняться.')
        except Exception as error:
            self.status.set('Не удалось получить список портов.')
            self.append_log(f'Ошибка MIDI: {error}')

    def preview_colour(self):
        rgb = tuple(v.get() for v in self.rgb)
        colour = '#' + bytes(rgb).hex().upper()
        foreground = 'black' if sum(rgb) > 380 else 'white'
        self.preview.configure(text=f'Выбранный цвет {colour}', bg=colour, fg=foreground)

    def set_colour(self, rgb):
        for variable, value in zip(self.rgb, rgb):
            variable.set(value)
        self.preview_colour()

    def choose_colour(self):
        rgb, _ = colorchooser.askcolor(parent=self.root, color=self.preview['bg'])
        if rgb is not None:
            self.set_colour(tuple(round(v) for v in rgb))

    def append_log(self, message):
        self.log.configure(state='normal')
        self.log.insert('end', message + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log.get('1.0', 'end-1c'))

    def set_busy(self, busy):
        for widget in self.controls:
            widget.configure(state='disabled' if busy else 'normal')
        for box in (self.input, self.output):
            box.configure(state='disabled' if busy else 'readonly')
        self.stop_button.configure(state='normal' if busy else 'disabled')

    def begin(self):
        if self.worker is not None:
            return
        if not self.input.get() or not self.output.get():
            self.status.set('Сначала выберите MIDI-вход и MIDI-выход.')
            return
        args = self.input.get(), self.output.get(), self.pad.get(), tuple(v.get() for v in self.rgb)
        self.cancel.clear()
        self.set_busy(True)
        self.status.set(f'Отправка цвета на пэд {args[2]}…')

        def work():
            success = False
            try:
                send_colour(*args, self.cancel, lambda line: self.events.put(('log', line)), backend=self.backend)
                success = True
            except Exception as error:
                self.events.put(('log', f'{type(error).__name__}: {error}'))
            finally:
                self.events.put(('done', success))

        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'log':
                    self.append_log(value)
                else:
                    self.worker.join()
                    self.worker = None
                    self.set_busy(False)
                    self.status.set('3 ACK получены — проверьте цвет пэда.' if value else 'Отправка остановлена. Подробности в логе.')
        except queue.Empty:
            pass
        if self.closing and self.worker is None:
            self.root.destroy()
            return
        self.poll_id = self.root.after(40, self.poll)

    def close(self):
        self.closing = True
        self.cancel.set()


def run():
    # CI verifies the packaged Windows executable can load Tk and RtMidi.
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-test':
        import rtmidi
        root = tk.Tk()
        root.withdraw()
        app = App(root, enumerate_ports=False)
        app.pad.set(32)
        app.set_colour((255, 0, 127))
        root.update()
        assert app.pad.get() == 32 and tuple(v.get() for v in app.rgb) == (255, 0, 127)
        assert len(app.pad_buttons) == 32
        app.backend.load()
        apis = rtmidi.get_compiled_api()
        if sys.platform == 'win32':
            assert rtmidi.API_WINDOWS_MM in apis
        root.after_cancel(app.poll_id)
        root.destroy()
        Path(sys.argv[2]).write_text(json.dumps({'version': VERSION, 'gui': 'ok', 'backend': 'loaded', 'midi_hardware': 'not tested'}))
        return
    root = tk.Tk()
    App(root)
    root.mainloop()
