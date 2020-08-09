import tkinter as tk
import tkinter.ttk as ttk
from tkinter.constants import *
from util import get_config
from tkinter.messagebox import showinfo, showwarning
from directinput_constants import keysym_map
from keystate_manager import DEFAULT_KEY_MAP


class SetKeyMap(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.wm_minsize(200, 30)
        self.geometry('+%d+%d' % (master.winfo_x(), master.winfo_y()))
        self.title("Key Setting")
        self.focus_get()
        self.grab_set()
        if not get_config().get('keymap'):
            self.create_default_keymap()
        self.keymap_data = self.read_keymap_file()
        self.labels = {}
        keycount = 0
        _keyname = ""

        ttk.Style().configure("KEY.TLabel", borderwidth=1, relief=SOLID, padx=2)
        ttk.Style().configure("KEY.TButton", borderwidth=1, relief=SOLID)

        self.columnconfigure(1, weight=1, minsize=150)
        self.columnconfigure(0, weight=1)
        for keyname, value in self.keymap_data.items():
            dik_code, kor_name = value
            ttk.Label(self, text=kor_name, style='KEY.TLabel').grid(row=keycount, column=0, sticky=N+S+E+W, pady=5, padx=(5,0))
            _keyname = keyname
            self.labels[_keyname] = tk.StringVar()
            self.labels[_keyname].set(self.dik2keysym(dik_code))
            ttk.Button(self, textvariable=self.labels[_keyname], command=lambda _keyname=_keyname: self.set_key(_keyname)).grid(row=keycount, column=1, sticky=N+S+E+W, pady=5, padx=(0,5))
            self.rowconfigure(keycount, weight=1)

            keycount += 1

        ttk.Button(self, text="Restore default", command=self.set_default_keymap).grid(row=keycount, column=0)
        ttk.Button(self, text="Save", command=self.onSave).grid(row=keycount, column=1)
        self.focus_set()

    def set_default_keymap(self):
        self.create_default_keymap()
        showinfo("key config", "default restored")
        self.destroy()

    def keysym2dik(self, keysym):
        try:
            dik = keysym_map[keysym]
            return dik
        except:
            return 0

    def onSave(self):
        get_config()['keymap'] = self.keymap_data.copy()
        self.destroy()

    def on_press(self, event,  key_name):
        found = False
        for key, value in keysym_map.items():
            if event.keysym == key or str(event.keysym).upper() == key:
                self.keymap_data[key_name] = [value, self.keymap_data[key_name][1]]
                self.labels[key_name].set(key)
                found = True
                break
        if not found:
            showwarning("key config", "unsupported key: " + str(event.keysym))
            self.keymap_data[key_name] = DEFAULT_KEY_MAP[key_name]
            self.labels[key_name].set(self.dik2keysym(DEFAULT_KEY_MAP[key_name][0]))

        self.unbind("<Key>")

    def set_key(self, key_name):
        self.labels[key_name].set("please input")
        self.unbind("<Key>")
        self.bind("<Key>", lambda event: self.on_press(event, key_name))

    def dik2keysym(self, dik):
        for keysym, _dik in keysym_map.items():
            if dik == _dik:
                return keysym

    def read_keymap_file(self):
        return get_config().get('keymap') or DEFAULT_KEY_MAP.copy()

    def create_default_keymap(self):
        get_config()['keymap'] = DEFAULT_KEY_MAP.copy()
