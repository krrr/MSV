# -*- coding:utf-8 -*-
from screen_processor import StaticImageProcessor, ScreenProcessor
from terrain_analyzer import PathAnalyzer
import cv2, threading, os
import tkinter as tk
import time
from tkinter.constants import *
from PIL import Image, ImageTk
from tkinter.messagebox import showinfo, showerror, showwarning
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import askyesno


class TerrainEditorWindow(tk.Toplevel):
    set_skill_color = {'kishin_shoukan': (107, 50, 135), 'yaksha_boss': (196, 0, 0),
                       'nightmare_invite': (226, 142, 185)}

    def __init__(self, master=None, open_file_path=None):
        tk.Toplevel.__init__(self, master)
        self.wm_minsize(100, 30)
        if master is not None:
            self.geometry('+%d+%d' % (master.winfo_x(), master.winfo_y()))
        self.resizable(0, 0)
        self.focus_get()
        self.grab_set()
        self.title("Terrain file generator")

        self.last_coord_x = None
        self.last_coord_y = None
        self.current_coords = []
        self.other_attrs = {}

        self.screen_capturer = ScreenProcessor()
        if not self.screen_capturer.ms_get_screen_hwnd():
            showerror('Error', 'The MapleStory window was not found.')
            self.destroy()
            return

        self.image_processor = StaticImageProcessor(self.screen_capturer)
        self.terrain_analyzer = PathAnalyzer()
        self.image_label = tk.Label(self)
        self.image_label.pack(expand=YES, fill=BOTH)

        self.master_tool_frame = tk.Frame(self, borderwidth=2, relief=GROOVE)
        self.master_tool_frame.pack(expand=YES, fill=BOTH)

        self.tool_frame_1 = tk.Frame(self.master_tool_frame)
        self.tool_frame_1.pack(fill=X)
        tk.Button(self.tool_frame_1, text="Find minimap again", command=self.find_minimap_coords).pack(side=LEFT)
        self.coord_label = tk.Label(self.tool_frame_1, text="x,y")
        self.coord_label.pack(side=RIGHT, fill=Y, expand=YES)

        self.tool_frame_2 = tk.Frame(self.master_tool_frame)
        self.tool_frame_2.pack(fill=X)
        self.start_platform_record_button = tk.Button(self.tool_frame_2, text="Start record platform", command=self.start_record_platform)
        self.start_platform_record_button.pack(side=LEFT, expand=YES, fill=X)
        self.stop_platform_record_button = tk.Button(self.tool_frame_2, text="Stop record platform", command=self.stop_record_platform, state=DISABLED)
        self.stop_platform_record_button.pack(side=RIGHT, expand=YES, fill=X)

        self.set_yaksha_coord_button0 = tk.Button(self.master_tool_frame, text="Toggle yaksha boss pos (face left)",
                                                 command=lambda: self._set_place_skill_coord('yaksha_boss', 'yaksha_boss_dir', 'left'))
        self.set_yaksha_coord_button0.pack(fill=X)
        self.set_yaksha_coord_button1 = tk.Button(self.master_tool_frame, text="Toggle yaksha boss pos (face right)",
                                                 command=lambda: self._set_place_skill_coord('yaksha_boss', 'yaksha_boss_dir', 'right'))
        self.set_yaksha_coord_button1.pack(fill=X)
        self.set_kishin_coord_button = tk.Button(self.master_tool_frame, text="Toggle kishin shoukan pos",
                                                 command=lambda: self._set_place_skill_coord('kishin_shoukan'))
        self.set_kishin_coord_button.pack(fill=X)
        self.set_nightmare_invite_button = tk.Button(self.master_tool_frame, text="Toggle nightmare invite pos",
                                                     command=lambda: self._set_place_skill_coord('nightmare_invite'))
        self.set_nightmare_invite_button.pack(fill=X)

        self.tool_frame_5 = tk.Frame(self.master_tool_frame)
        self.tool_frame_5.pack(fill=X, side=BOTTOM)
        tk.Button(self.tool_frame_5, text="reset", command=self.on_reset_platforms).pack(side=LEFT, expand=YES, fill=X)
        tk.Button(self.tool_frame_5, text="save", command=self.on_save).pack(side=RIGHT, expand=YES, fill=X)

        self.platform_listbox = tk.Listbox(self, selectmode=MULTIPLE)
        self.platform_listbox.pack(expand=YES, fill=BOTH)
        self.platform_listbox_platform_index = {}
        self.platform_listbox.bind("<Button-3>", self.on_platform_list_rclick)

        self.platform_listbox_menu = tk.Menu(self, tearoff=0)
        self.platform_listbox_menu.add_command(label="Delete selected item", command=self.on_listbox_delete)
        self.platform_listbox_menu.add_command(label="Toggle selected no monster", command=self._on_toggle_no_monster)

        self.image_processor.update_image(set_focus=False)
        self.minimap_rect = self.image_processor.get_minimap_rect()
        if not self.minimap_rect:
            self.image_label.configure(text="Minimap not found", fg="red")

        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.update_image, args=())
        self.thread.start()

        self.record_mode = 0  # 0 if not recording, 1 if normal platform

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.focus_set()

        if open_file_path:
            self.load_platform_file(open_file_path)

    def _set_place_skill_coord(self, skill_name, extra_attr=None, extra_attr_value=None):
        old = self.other_attrs.get(skill_name + '_coord')
        if old == (self.last_coord_x, self.last_coord_y):
            del self.other_attrs[skill_name + '_coord']
            if extra_attr:
                del self.other_attrs[extra_attr]
        else:
            self.other_attrs[skill_name + '_coord'] = (self.last_coord_x, self.last_coord_y)
            if extra_attr:
                self.other_attrs[extra_attr] = extra_attr_value

    def load_platform_file(self, path):
        self.terrain_analyzer.load(path)
        for i in self.set_skill_color:
            if i in self.terrain_analyzer.set_skill_coord:
                self.other_attrs[i + '_coord'] = self.terrain_analyzer.set_skill_coord[i]
        self.other_attrs = self.terrain_analyzer.other_attrs.copy()
        self.update_listbox()

    def on_close(self):
        self.stopEvent.set()
        self.after(200, self.destroy)

    def on_platform_list_rclick(self, event):
        try:
            self.platform_listbox_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.platform_listbox_menu.grab_release()

    def on_listbox_delete(self):
        selected = self.platform_listbox.curselection()
        if not selected:
            return

        if askyesno("Terrain file generator", "Are you sure you want to delete %d entries??"%(len(selected))):
            if self.record_mode != 0:
                showwarning("Terrain File Generator", "Please close the ongoing record first")
            else:
                for idx in selected:
                    for key, hash in self.platform_listbox_platform_index.items():
                        if idx == key:
                            del self.terrain_analyzer.platforms[hash]
                self.update_listbox()

    def _on_toggle_no_monster(self):
        selected = self.platform_listbox.curselection()
        for idx in selected:
            hash = self.platform_listbox_platform_index[idx]
            platform = self.terrain_analyzer.platforms[hash]
            platform.no_monster = not platform.no_monster

        self.update_listbox()

    def update_listbox(self):
        self.platform_listbox_platform_index = {}
        self.platform_listbox.delete(0, END)
        cindex = 0
        for key, platform in self.terrain_analyzer.platforms.items():
            label = "(%d,%d), (%d,%d) platform" % (platform.start_x, platform.start_y, platform.end_x, platform.end_y)
            other_attrs = []
            if platform.no_monster:
                other_attrs.append('N')
            if other_attrs:
                label += ' (' + ', '.join(other_attrs) + ')'
            self.platform_listbox.insert(END, label)
            self.platform_listbox_platform_index[cindex] = key
            self.platform_listbox.itemconfigure(cindex, fg="green")
            cindex += 1

    def start_record_platform(self):
        self.record_mode = 1
        self.start_platform_record_button.configure(state=DISABLED)
        self.stop_platform_record_button.configure(state=NORMAL)

    def stop_record_platform(self):
        self.record_mode = 0
        self.start_platform_record_button.configure(state=NORMAL)
        self.stop_platform_record_button.configure(state=DISABLED)
        self.coord_label.configure(fg="black")
        self.terrain_analyzer.flush_input_coords_to_platform(coord_list=self.current_coords)
        self.current_coords = []
        self.update_listbox()

    def on_save(self):
        assert self.minimap_rect

        minimap_rect = self.minimap_rect  # dialog may cover minimap
        path = asksaveasfilename(initialdir=os.getcwd(), title="Save path setting", filetypes=(("Terrain file (*.platform)","*.platform"),))
        if path:
            if not path.endswith(".platform"):
                path += ".platform"
            self.other_attrs['minimap'] = minimap_rect
            self.terrain_analyzer.save(path, self.other_attrs)
            showinfo("Terrain file generator", "File path {0}\n has been saved.".format(path))
            self.on_close()

    def on_reset_platforms(self):
        if askyesno("Terrain file generator", "Really delete all terrain?"):
            self.record_mode = 0
            self.coord_label.configure(fg="black")
            self.terrain_analyzer.reset()
            self.start_platform_record_button.configure(state=NORMAL)
            self.stop_platform_record_button.configure(state=DISABLED)
            self.update_listbox()

    def find_minimap_coords(self):
        self.image_processor.update_image(set_focus=False)
        self.minimap_rect = self.image_processor.get_minimap_rect()

    def update_image(self):
        while not self.stopEvent.is_set():
            self.image_processor.update_image(set_focus=False)
            if not self.minimap_rect:
                self.image_label.configure(text="Minimap not found", fg="red")
                self.find_minimap_coords()
                continue

            playerpos = self.image_processor.find_player_minimap_marker(self.minimap_rect)

            if not playerpos:
                self.image_label.configure(text="Player location not found", fg="red")
                self.find_minimap_coords()
                continue

            self.last_coord_x, self.last_coord_y = playerpos
            if self.record_mode == 1 or self.record_mode == 2:
                if (self.last_coord_x, self.last_coord_y) not in self.current_coords:
                    self.current_coords.append((self.last_coord_x, self.last_coord_y))
                if self.record_mode == 1:
                    self.coord_label.configure(fg="green")

            self.coord_label.configure(text="%d,%d"%(playerpos[0], playerpos[1]))
            if self.minimap_rect == 0:
                continue

            cropped_img = cv2.cvtColor(self.image_processor.bgr_img[self.minimap_rect[1]:self.minimap_rect[1] + self.minimap_rect[3], self.minimap_rect[0]:self.minimap_rect[0] + self.minimap_rect[2]], cv2.COLOR_BGR2RGB)
            if self.record_mode:
                cv2.line(cropped_img, (playerpos[0], 0), (playerpos[0], cropped_img.shape[0]), (0, 0, 255), 1)
                cv2.line(cropped_img, (0, playerpos[1]), (cropped_img.shape[1], playerpos[1]), (0, 0, 255), 1)
            else:
                cv2.line(cropped_img, (playerpos[0], 0), (playerpos[0], cropped_img.shape[0]), (0,0,0), 1)
                cv2.line(cropped_img, (0, playerpos[1]), (cropped_img.shape[1], playerpos[1]), (0, 0, 0), 1)

            selected = self.platform_listbox.curselection()
            if selected:
                for idx in selected:
                    for key, hash in self.platform_listbox_platform_index.items():
                        if idx == key:
                            platform_obj = self.terrain_analyzer.platforms[hash]
                            cv2.line(cropped_img, (platform_obj.start_x, platform_obj.start_y),(platform_obj.end_x, platform_obj.end_y), (0, 255, 0), 2)
                            break
            else:
                for key, platform in self.terrain_analyzer.platforms.items():
                    cv2.line(cropped_img, (platform.start_x, platform.start_y), (platform.end_x, platform.end_y), (0,255,0), 2)

            for k in self.set_skill_color.keys():
                coord = self.other_attrs.get(k + '_coord')
                if coord:
                    color = self.set_skill_color[k]
                    cv2.circle(cropped_img, (coord[0], coord[1]), 4, (255, 255, 255), -1)  # white border
                    cv2.circle(cropped_img, (coord[0], coord[1]), 3, color, -1)

            img = Image.fromarray(cropped_img)
            img_tk = ImageTk.PhotoImage(image=img)
            self.image_label.image = img_tk
            self.image_label.configure(image=img_tk)

            self.update()
            time.sleep(0.04)


if __name__ == "__main__":
    root = tk.Tk()
    TerrainEditorWindow()
    root.mainloop()