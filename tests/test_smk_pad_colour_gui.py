"""GUI-to-worker check; run with an X display on Linux, or on Windows."""
from pathlib import Path
import sys
import time
import tkinter as tk
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from smk_pad_colour import ACK
from smk_pad_colour_gui import App


class Backend:
    def __init__(self):
        self.messages = []
        self.callback = None

    def get_input_names(self): return ['SMK IN']
    def get_output_names(self): return ['SMK OUT']

    def open_input(self, name, callback):
        self.callback = callback
        return Port()

    def open_output(self, name):
        return Port(self)


class Port:
    def __init__(self, backend=None): self.backend = backend
    def __enter__(self): return self
    def __exit__(self, *args): pass

    def send(self, message):
        import mido
        self.backend.messages.append(message)
        self.backend.callback(mido.Message.from_bytes(ACK))


class GuiTests(unittest.TestCase):
    def test_send_button_uses_selected_pad_colour_and_returns_to_idle(self):
        root = tk.Tk()
        root.withdraw()
        backend = Backend()
        app = App(root, backend)
        try:
            app.send_button.invoke()
            self.assertIsNone(app.worker)  # Empty port selection must not send.
            app.input.set('SMK IN')
            app.output.set('SMK OUT')
            app.pad_buttons[-1].invoke()
            app.set_colour((255, 0, 127))
            root.update()
            self.assertEqual(app.pad.get(), 32)
            self.assertFalse(backend.messages)  # Selection/sliders are preview-only.
            app.send_button.invoke()
            self.assertEqual(str(app.send_button['state']), 'disabled')
            deadline = time.monotonic() + 5
            while app.worker is not None and time.monotonic() < deadline:
                root.update()
                time.sleep(.01)
            self.assertIsNone(app.worker)
            self.assertEqual(str(app.send_button['state']), 'normal')
            self.assertEqual(len(backend.messages), 4)
            from smk_protocol import decode
            decoded = [decode(bytes(msg.bytes()))[1] for msg in backend.messages]
            self.assertEqual([int.from_bytes(d[1:5], 'little') for d in decoded], [0xA11, 0xA12, 0xA13, 0xA14])
            self.assertEqual([d[-1] for d in decoded], [255, 0, 127, 255])
            self.assertIn('Все 4 ACK получены', app.log.get('1.0', 'end'))
            self.assertEqual(app.preview['bg'], '#FF007F')
        finally:
            app.cancel.set()
            if app.worker is not None: app.worker.join(timeout=3)
            root.after_cancel(app.poll_id)
            root.destroy()

    def test_all_mode_percentage_and_slider_restore(self):
        from smk_pad_colour import send_colour
        from smk_protocol import decode
        root=tk.Tk(); root.withdraw()
        backend=Backend(); app=App(root,backend)
        try:
            app.input.set('SMK IN'); app.output.set('SMK OUT')
            app.brightness.set(120)
            app.all_pads.set(True); app.update_modes()
            self.assertEqual(app.brightness.get(),120)
            self.assertEqual(str(app.brightness_slider['state']),'normal')
            app.alternate.set(True); app.update_modes()
            self.assertEqual(app.brightness.get(),80)
            self.assertEqual(float(app.brightness_slider['to']),100)
            app.brightness.set(40)
            with patch('smk_pad_colour_gui.send_colour', side_effect=lambda *a,**kw:send_colour(*a,**kw,spacing=0)):
                app.begin()
                deadline=time.monotonic()+5
                while app.worker is not None and time.monotonic()<deadline:
                    root.update();time.sleep(.01)
            self.assertIsNone(app.worker)
            self.assertEqual(len(backend.messages),128)
            levels=[decode(bytes(m.bytes()))[1][-1] for m in backend.messages[3::4]]
            self.assertEqual(levels,[255,102]*16)
            app.alternate.set(False); app.update_modes()
            self.assertEqual(app.brightness.get(),120)
            self.assertEqual(float(app.brightness_slider['to']),255)
            app.alternate.set(True); app.update_modes()
            self.assertEqual(app.brightness.get(),40)
            app.all_pads.set(False); app.update_modes()
            self.assertFalse(app.alternate.get())
            self.assertEqual(app.brightness.get(),120)
        finally:
            app.cancel.set()
            if app.worker is not None:app.worker.join(timeout=3)
            root.after_cancel(app.poll_id);root.destroy()


if __name__ == '__main__': unittest.main()
