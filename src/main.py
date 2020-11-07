import sys
if sys.path[0].endswith('.zip'):  # python embeddable version
    sys.path.insert(0, '')

import logging
import ctypes
import multiprocessing, tkinter as tk, time, os, signal, pickle, argparse

from tkinter import ttk
from tkinter.constants import *
from tkinter.messagebox import showerror
from tkinter.filedialog import askopenfilename
from tkinter.scrolledtext import ScrolledText

from macro_script import MacroController
import mapscripts
from util import get_config, save_config
from keybind_setup_window import KeyBindSetupWindow
from terrain_editor import TerrainEditorWindow
from screen_processor import MapleScreenCapturer
# from macro_script_astar import MacroControllerAStar as MacroController


default_logger = logging.getLogger("main")
default_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh = logging.FileHandler("logging.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
default_logger.addHandler(fh)


APP_TITLE = "MSV Kanna Ver"
VERSION = 0.3


def macro_loop(input_queue, output_queue):
    logger = logging.getLogger("macro_loop")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler("logging.log", encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    try:
        while True:
            if input_queue.empty():
                time.sleep(0.5)
                continue

            command = input_queue.get()
            logger.debug("received command {}".format(command))
            if command[0] == "start":
                logger.debug("starting MacroController...")
                keymap, platform_file_dir, preset = command[1:]
                if preset:
                    macro = mapscripts.map_scripts[preset](keymap, output_queue)
                else:
                    macro = MacroController(keymap, log_queue=output_queue)
                macro.load_and_process_platform_map(platform_file_dir)

                while True:
                    macro.loop()
                    if not input_queue.empty():
                        command = input_queue.get()
                        if command[0] == "stop":
                            macro.abort()
                            break
    except Exception:
        logger.exception("Exception during loop execution:")
        output_queue.put(["exception", "exception"])


class MainScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack(expand=YES, fill=BOTH)

        self._menubar = tk.Menu()
        terrain_menu = tk.Menu(tearoff=False)
        terrain_menu.add_command(label="Create", command=lambda: TerrainEditorWindow(self.master))
        terrain_menu.add_command(label="Edit Current", command=lambda: self._on_edit_terrain())
        self._menubar.add_cascade(label="Terrain", menu=terrain_menu)
        options_menu = tk.Menu(tearoff=False)
        options_menu.add_command(label="Set Keys", command=lambda: KeyBindSetupWindow(self.master))
        self.auto_solve_rune = tk.BooleanVar()
        self.auto_solve_rune.set(get_config().get('auto_solve_rune', True))
        options_menu.add_checkbutton(label="Auto Solve Rune", onvalue=True, offvalue=False,
                                     variable=self.auto_solve_rune, command=self._on_auto_solve_rune_check)
        self._menubar.add_cascade(label="Options", menu=options_menu)
        help_menu = tk.Menu(tearoff=False)
        self._menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label='About', command=self._popup_about)

        self.master.config(menu=self._menubar)

        self.platform_file_path = tk.StringVar()
        self.platform_file_name = tk.StringVar()

        self.keymap = None

        self.macro_running = False
        self.macro_pid = 0
        self.macro_process = None
        self.macro_process_out_queue = multiprocessing.Queue()
        self.macro_process_in_queue = multiprocessing.Queue()

        self.macro_pid_infotext = tk.StringVar()
        self.macro_pid_infotext.set("Not executed")

        self.log_text_area = ScrolledText(self, height=10, width=20)
        self.log_text_area.pack(side=BOTTOM, expand=YES, fill=BOTH)
        self.log_text_area.bind("<Key>", lambda e: "break")

        self.action_btn_frame = ttk.Frame(self)
        self.action_btn_frame.pack(side=BOTTOM, anchor=S, expand=NO, fill=BOTH, pady=5)
        self.macro_toggle_button = ttk.Button(self.action_btn_frame, text="Start Macro", width=21,
                                              command=lambda: self.stop_macro() if self.macro_running else self.start_macro())
        self.macro_toggle_button.pack()

        self.macro_info_frame = ttk.Frame(self, borderwidth=4, relief=GROOVE)
        self.macro_info_frame.pack(side=BOTTOM, anchor=S, expand=NO, fill=BOTH)

        ttk.Label(self.macro_info_frame, text="Bot process status:").grid(row=0, column=0)

        self.macro_process_label = tk.Label(self.macro_info_frame, textvariable=self.macro_pid_infotext, fg="red")
        self.macro_process_label.grid(row=0, column=1, sticky=W, padx=5)
        self.macro_process_toggle_button = ttk.Button(self.macro_info_frame, text="Run", command=self.toggle_macro_process)
        self.macro_process_toggle_button.grid(row=0, column=2, sticky=N+S+E+W)
        ttk.Label(self.macro_info_frame, text="Terrain file:").grid(row=1, column=0, sticky=N+S+E+W)
        ttk.Label(self.macro_info_frame, textvariable=self.platform_file_name).grid(row=1, column=1, sticky=W, padx=5)
        self.platform_file_button = ttk.Button(self.macro_info_frame, text="Open...", command=self._on_platform_file_select)
        self.platform_file_button.grid(row=1, column=2, sticky=N+S+E+W)
        self.platform_file_button.config(width=8)
        for i in (self.macro_process_toggle_button, self.platform_file_button):
            i.config(width=8)

        ttk.Label(self.macro_info_frame, text="Preset:").grid(row=2, column=0, sticky=N+S+E+W)
        self.preset_names = list(mapscripts.map_scripts.keys())
        self.preset_combobox = ttk.Combobox(self.macro_info_frame, values=self.preset_names, state="readonly")
        self.preset_combobox.grid(row=2, column=1, columnspan=2, sticky=W, padx=5)
        self.preset_combobox.bind("<<ComboboxSelected>>", self._on_preset_platform_set)

        self.macro_info_frame.grid_columnconfigure(1, weight=1)

        self.log("MS-Visionify Kanna Ver v" + str(VERSION))
        self.log('\n')

        last_opened_platform_file = get_config().get('platform_file')
        if last_opened_platform_file and os.path.isfile(last_opened_platform_file):
            self.set_platform_file(last_opened_platform_file)
        selected_preset = get_config().get('preset')

        if selected_preset is not None:
            try:
                self.preset_combobox.current(self.preset_names.index(selected_preset))
            except tk.TclError:
                pass

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(500, self.toggle_macro_process)
        self.after(1000, self.check_input_queue)

    def on_close(self):
        if self.macro_process:
            try:
                self.macro_process_out_queue.put("stop")
                os.kill(self.macro_pid, signal.SIGTERM)
            except Exception:
                pass

        get_config()['geometry'] = self.master.geometry()
        save_config()

        self.master.destroy()

    def check_input_queue(self):
        while not self.macro_process_in_queue.empty():
            output = self.macro_process_in_queue.get()
            if output[0] == "log":
                self.log("Process - "+str(output[1]))
            elif output[0] == "stopped":
                self.log("Bot process has ended.")
            elif output[0] == "exception":
                self.macro_running = False
                self.macro_toggle_button.configure(text="Start Macro")
                self.platform_file_button.configure(state=NORMAL)
                self.preset_combobox.configure(state=NORMAL)
                self.macro_process = None
                self.macro_pid = 0
                self.macro_process_toggle_button.configure(state=NORMAL)
                self.macro_pid_infotext.set("Not executed")
                self.macro_process_label.configure(fg="red")
                self.macro_process_toggle_button.configure(text="Running")
                self.log("Bot process terminated due to an error. Please check the log file.")

        self.after(1000, self.check_input_queue)

    def start_macro(self):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            showerror(APP_TITLE, 'Please run as administrator')
            return

        if not self.macro_process:
            self.toggle_macro_process()
        keymap = get_config().get('keymap')
        if not keymap:
            showerror(APP_TITLE, "The key setting could not be read. Please reset the key.")
            return

        if not self.platform_file_path.get():
            showerror(APP_TITLE, "Please select a terrain file.")
            return

        cap = MapleScreenCapturer()
        cap.hwnd = cap.ms_get_screen_hwnd()
        if not cap.hwnd:
            showerror(APP_TITLE, "MapleStory window not found")
            return

        rect = cap.ms_get_screen_rect(cap.hwnd)
        self.log("MS hwnd", cap.hwnd)
        self.log("MS rect", rect)
        self.log("Out Queue put:", self.platform_file_path.get())
        if rect[0] < 0 or rect[1] < 0:
            showerror(APP_TITLE, "Failed to get Maple Window location.\nMove MapleStory window so"
                                 "that the top left corner of the window is within the screen.")
            return

        cap.capture()
        self.macro_process_out_queue.put(("start", keymap, self.platform_file_path.get(), self._get_preset()))
        self.macro_running = True
        self.macro_toggle_button.configure(text="Stop Macro")
        self.platform_file_button.configure(state=DISABLED)
        self.preset_combobox.configure(state=DISABLED)

    def stop_macro(self):
        self.macro_process_out_queue.put(("stop",))
        self.log("Bot stop request completed. Please wait for a while.")
        self.macro_running = False
        self.macro_toggle_button.configure(text="Start Macro")
        self.platform_file_button.configure(state=NORMAL)
        self.preset_combobox.configure(state=NORMAL)

    def log(self, *args):
        res_txt = []
        for arg in args:
            res_txt.append(str(arg))
        self.log_text_area.insert(END, " ".join(res_txt)+"\n")
        self.log_text_area.see(END)

    def toggle_macro_process(self):
        if not self.macro_process:
            self.macro_process_toggle_button.configure(state=DISABLED)
            self.macro_pid_infotext.set("Running..")
            self.macro_process_label.configure(fg="orange")
            self.log("Bot process starting...")
            self.macro_process_out_queue = multiprocessing.Queue()
            self.macro_process_in_queue = multiprocessing.Queue()
            p = multiprocessing.Process(target=macro_loop, args=(self.macro_process_out_queue, self.macro_process_in_queue))
            p.daemon = True

            self.macro_process = p
            p.start()
            self.macro_pid = p.pid
            self.log("Process creation complete (pid: %d)" % self.macro_pid)
            self.macro_pid_infotext.set("Executed (%d)" % self.macro_pid)
            self.macro_process_label.configure(fg="green")
            self.macro_process_toggle_button.configure(state=NORMAL)
            self.macro_process_toggle_button.configure(text="Stop")
        else:
            self.stop_macro()
            self.macro_process_toggle_button.configure(state=DISABLED)
            self.macro_pid_infotext.set("Stopping..")
            self.macro_process_label.configure(fg="orange")

            self.log("SIGTERM %d" % self.macro_pid)
            os.kill(self.macro_pid, signal.SIGTERM)
            self.log("Process terminated")
            self.macro_process = None
            self.macro_pid = 0
            self.macro_process_toggle_button.configure(state=NORMAL)
            self.macro_pid_infotext.set("Not executed")
            self.macro_process_label.configure(fg="red")
            self.macro_process_toggle_button.configure(text="Run")

    def _on_platform_file_select(self):
        platform_file_path = askopenfilename(initialdir=os.getcwd(), title="Terrain file selection",
                                             filetypes=(("terrain file (*.platform)", "*.platform"),))
        if platform_file_path and os.path.exists(platform_file_path):
            self.set_platform_file(platform_file_path)
            get_config()['platform_file'] = platform_file_path
            if self.preset_combobox.current() != -1:
                self.preset_combobox.set('')
                get_config()['preset'] = None

    def _on_preset_platform_set(self, __):
        preset = self._get_preset()
        get_config()['preset'] = preset
        path = 'mapscripts/' + mapscripts.map2platform[preset] + '.platform'
        self.set_platform_file(path)
        get_config()['platform_file'] = path

    def _get_preset(self):
        idx = self.preset_combobox.current()
        return self.preset_names[idx] if idx != -1 else None

    def set_platform_file(self, path):
        with open(path, "rb") as f:
            try:
                data = pickle.load(f)
                platforms = data["platforms"]
                # minimap_coords = data["minimap"]
                self.log("Terrain file loaded (platforms: %s)" % len(platforms.keys()))
            except:
                showerror(APP_TITLE, "File verification error\n file: %s\nFile verification failed. Please check if it is a broken file." % path)
            else:
                self.platform_file_path.set(path)
                self.platform_file_name.set(os.path.basename(path).split('.')[0])

    def _on_edit_terrain(self):
        if not self.platform_file_path.get():
            showerror(APP_TITLE, 'No terrain file opened')
        else:
            TerrainEditorWindow(self.master, self.platform_file_path.get())

    def _on_auto_solve_rune_check(self):
        get_config()['auto_solve_rune'] = self.auto_solve_rune.get()

    def _popup_about(self):
        tk.messagebox.showinfo('About', '''\
Version: v%s
Author: Dashadower, krrr
Source code: https://github.com/krrr/MSV-Kanna-Ver

Please be known that using this bot may get your account banned. By using this software,
you acknowledge that the developers are not liable for any damages caused to you or your account.
''' % (VERSION,))


def main():
    ctypes.windll.user32.SetProcessDPIAware()

    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description="MS-Visionify, a bot to play MapleStory")
    parser.add_argument("-title", dest="title", help="change main window title to designated value")
    args = vars(parser.parse_args())
    root = tk.Tk()

    root.title(args["title"] if args["title"] else APP_TITLE)
    try:
        root.iconbitmap('appicon.ico')
    except tk.TclError:
        pass
    root.wm_minsize(400, 600)

    MainScreen(root)

    geo = get_config().get('geometry')
    if geo:
        root.geometry(geo)
    root.mainloop()


if __name__ == "__main__":
    main()
