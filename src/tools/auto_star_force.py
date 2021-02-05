import tkinter as tk
import tkinter.ttk as ttk
from tkinter.constants import *
from tkinter.messagebox import showerror
from screen_processor import ScreenProcessor, GameCaptureError
from input_manager import InputManager
import directinput_constants as dc
import pyocr
import pyocr.builders
import pyocr.libtesseract
import re
import time
import math
import logging
import multiprocessing
import random
from PIL import ImageOps
from util import get_file_log_handler


def macro_process_main(input_q, output_q):
    logger = logging.getLogger("macro_loop")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_file_log_handler())


def color_distance(c1, c2):
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2)


class AutoStarForce:
    AREA_SIZE = (342, 295)
    AREA_POS = (513, 218)
    CURR_STAR_RECT = (138, 92, 138+115, 92+16)
    STAR_CATCH_OPTION_POINT = (144, 207)
    SAFE_GUARD_OPTION_POINT = (302, 207)
    OPTION_DISABLED, OPTION_UNCHECKED, OPTION_CHECKED = range(3)
    RESULT_SUCCESS, RESULT_FAILED, RESULT_DESTROYED = range(3)
    OPTION_PIXEL_MAP = {(238, 0, 102): OPTION_CHECKED, (255, 255, 255): OPTION_UNCHECKED, (187, 187, 187): OPTION_DISABLED}
    ENHANCE_BTN_POS = (129, 265)
    CONFIRM_OK_BTN_POS = (94, 226)
    RESULT_OK_BTN_POS = (183, 226)
    CATCHER_CHECK_POS = (49, 52)
    GREEN_COLOR = (136, 170, 17)
    STAR_TRACK_COLOR = (204, 204, 204)
    SUCCESS_FONT_COLOR = (255, 255, 34)
    RESULT_TEXT_RECT = (55, 171, 293, 200)

    def __init__(self, screen_processor):
        if not pyocr.libtesseract.is_available():
            raise Exception('no OCR tool available')
        self.tool = pyocr.libtesseract
        if 'eng' not in self.tool.get_available_languages():
            raise Exception('tesseract english data not available')
        self.current_star_regexp = re.compile('(\\d+)\\s?Star\\s?>\\s?\\d+\\s?Star')

        self.screen_processor = screen_processor
        self.screen_processor.hwnd = self.screen_processor.ms_get_screen_hwnd()
        self.input_mgr = InputManager()
        self.img = None
        self.ms_rect = None
        self.rect = None

    def run(self, target_star, star_catch, safe_guard):
        count = 0
        next_star = None
        while True:
            self.update_image()

            curr = None
            if next_star is None:
                curr = self.get_current_star()
                if curr is None:
                    raise Exception('failed to determine current star')
                next_star = None
            else:
                curr = next_star

            if curr >= target_star:
                break

            print('current star:', curr)

            options = self.get_enhance_options()
            if (star_catch and options[0] == self.OPTION_CHECKED) or (not star_catch and options[0] == self.OPTION_UNCHECKED):
                self.input_mgr.mouse_left_click_at(*self._map_pos(self.STAR_CATCH_OPTION_POINT), 4)
                time.sleep(0.1)
            if (safe_guard and options[1] == self.OPTION_UNCHECKED) or (not safe_guard and options[1] == self.OPTION_CHECKED):
                self.input_mgr.mouse_left_click_at(*self._map_pos(self.SAFE_GUARD_OPTION_POINT), 4)
                time.sleep(0.1)

            self.input_mgr.mouse_left_click_at(*self._map_pos(self.ENHANCE_BTN_POS), 4)
            time.sleep(0.08)
            self.input_mgr.mouse_left_click_at(*self._map_pos(self.CONFIRM_OK_BTN_POS), 4)

            if star_catch:
                time.sleep(0.1)
                if self.wait(catcher=True) == 0:
                    time.sleep(0.2)
                    self.wait_star_center()
                    self.input_mgr.single_press(dc.DIK_RETURN)

            # game showing slow shining animation
            self.wait(result=True)
            result = self.get_result()
            self.input_mgr.mouse_left_click_at(*self._map_pos(self.RESULT_OK_BTN_POS), 4)
            if random.random() > 0.5:
                time.sleep(0.1)
                self.input_mgr.mouse_left_click_at(self.rect[0] + random.randint(0, 8), self.rect[3] - random.randint(0, 5), 4)
            else:
                time.sleep(0.3)
            if result == self.RESULT_SUCCESS:
                print('success')
                time.sleep(0.1)
                for _ in range(20):
                    time.sleep(0.1)
                    self.update_image()
                    if self.get_current_star() != curr:  # text update delays
                        break
                # maybe star is capped after this enhancement, so check again in the next iteration
                next_star = None
                time.sleep(0.4)
            elif result == self.RESULT_FAILED:
                print('fail')
                next_star = curr - 1 if curr > 10 else curr
                time.sleep(0.8)
            elif result == self.RESULT_DESTROYED:
                return
            else:
                raise Exception('unknown result')

            print('-------------------------------')
            count += 1
            if count != 0 and count % 7 == 0:
                time.sleep(1.5)

    def _map_pos(self, pos):
        return self.ms_rect[0] + self.AREA_POS[0] + pos[0], self.ms_rect[1] + self.AREA_POS[1] + pos[1]

    def get_current_star(self):
        curr_star_img = ImageOps.invert(self.img.crop(self.CURR_STAR_RECT).convert('L'))
        txt = self.tool.image_to_string(curr_star_img, lang='eng')
        txt = txt.replace('O', '0')
        match = self.current_star_regexp.match(txt)
        return int(match.group(1)) if match else None

    def update_image(self):
        if self.rect is None:  # setup window rect
            self.ms_rect = self.screen_processor.ms_get_screen_rect()
            if self.ms_rect is None:
                raise GameCaptureError
            x, y = self.ms_rect[0] + self.AREA_POS[0], self.ms_rect[1] + self.AREA_POS[1]
            self.rect = (x, y, x+self.AREA_SIZE[0], y+self.AREA_SIZE[1])

        self.img = self.screen_processor.capture(set_focus=True, rect=self.rect)

    def get_enhance_options(self):
        star_catch_pixel = self.img.getpixel(self.STAR_CATCH_OPTION_POINT)[:3]
        safe_guard_pixel = self.img.getpixel(self.SAFE_GUARD_OPTION_POINT)[:3]
        return self.OPTION_PIXEL_MAP.get(star_catch_pixel), self.OPTION_PIXEL_MAP.get(safe_guard_pixel)

    def is_catcher_present(self):
        return self.img.getpixel(self.CATCHER_CHECK_POS)[:3] == (0, 0, 0)

    def is_result_present(self):
        return self.img.getpixel(self.RESULT_OK_BTN_POS)[:3] == self.GREEN_COLOR

    def get_result(self):
        area = self.img.crop(self.RESULT_TEXT_RECT)
        for x in range(area.width):
            for y in range(area.height):
                px = area.getpixel((x, y))[:3]
                if px == (255, 255, 34):  # yellow
                    return self.RESULT_SUCCESS
                elif px == (255, 34, 34):  # red
                    return self.RESULT_FAILED
                elif px == (0, 0, 0):  # black
                    return self.RESULT_DESTROYED
        area.show()
        return None

    # this method should be fast
    def wait_star_center(self):
        target_zone_width = 99999
        # determine advance x
        for x in range(123, 151):
            if color_distance(self.img.getpixel((x, 217)), (221, 112, 41)) < 20:
                target_zone_width = (170 - x) * 2
                break

        # print('target_zone_width:', target_zone_width)
        x, y, w, h = 156, 215, 8, 1  # check this area on star track border
        if target_zone_width <= 45:
            x = 151

        rect = (self.rect[0]+x, self.rect[1]+y, self.rect[0]+x+w, self.rect[1]+y+h)
        start = time.time()
        while True:
            img = self.screen_processor.capture(rect=rect)  # faster than self.update_image
            if any(color_distance(img.getpixel((x, 0)), self.STAR_TRACK_COLOR) > 50 for x in range(w)):
                break

            if time.time() - start > 5:
                raise Exception('timeout')

    def wait(self, catcher=False, result=False):
        start = time.time()
        while True:
            self.update_image()
            if catcher:
                if self.is_catcher_present():
                    return 0
                elif self.is_result_present():
                    return 1
            elif result:
                if self.is_result_present():
                    return 0
            else:
                raise Exception('wrong argument')

            if time.time() - start > 10:
                raise Exception('timeout')
            time.sleep(0.02)


class AutoStarForceWindow(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.wm_minsize(400, 80)
        self.geometry('+%d+%d' % (master.winfo_x(), master.winfo_y()))
        self.title("Auto Star Force")
        self.running = False
        self.macro_process = None

        self.frame = ttk.Frame(self)
        self.frame.pack(expand=NO, fill=BOTH)

        ttk.Label(self.frame, text="Open enhance window (leave it at initial position)\n and set equipment first.").pack(padx=5)

        self.opt_frame = ttk.Frame(self.frame, borderwidth=4, relief=GROOVE)
        self.opt_frame.pack(anchor=S, expand=NO, pady=5)

        ttk.Label(self.opt_frame, text="Target Star:").grid(row=1, column=0, sticky=N+S+E+W, pady=3)
        vcmd = (self.register(lambda x: x == '' or str.isdigit(x)))
        self.target_star_input = ttk.Entry(self.opt_frame, validate='all', validatecommand=(vcmd, '%P'))
        self.target_star_input.grid(row=1, column=1, sticky=W, padx=5)

        self.star_catch_opt = tk.BooleanVar()
        self.star_catch_opt.set(True)
        self.safe_guard_opt = tk.BooleanVar()
        self.safe_guard_opt.set(False)

        self.star_catch_btn = ttk.Checkbutton(self.opt_frame, variable=self.star_catch_opt, text='Star Catch',
                                              offvalue=False, onvalue=True)
        self.star_catch_btn.grid(row=2, column=0, sticky=E, padx=6)
        self.safe_guard_btn = ttk.Checkbutton(self.opt_frame, variable=self.safe_guard_opt, text='Safe Guard',
                                              offvalue=False, onvalue=True)
        self.safe_guard_btn.grid(row=2, column=1, padx=6)

        self.action_btn_frame = ttk.Frame(self)
        self.action_btn_frame.pack(side=BOTTOM, anchor=S, expand=NO, fill=BOTH, pady=5)
        self.toggle_button = ttk.Button(self.action_btn_frame, text="Enhance", width=18,
                                        command=lambda: self.toggle())
        self.toggle_button.pack()

        self.focus_set()

    def toggle(self):
        if self.running:
            pass
        else:
            target_star = self.target_star_input.get()
            if not target_star:
                showerror('Error', 'target star not set')
                return
            target_star = int(target_star)
            print(self.safe_guard_opt.get())
            # auto_star_force = AutoStarForce(ScreenProcessor())
            # auto_star_force.run(17, True, True)
            self.macro_process = multiprocessing.Process(
                target=macro_process_main, args=(self.macro_process_out_q, self.macro_process_in_q), daemon=True)
            self.macro_process.start()


if __name__ == "__main__":
    auto_star_force = AutoStarForce(ScreenProcessor())
    auto_star_force.run(17, True, True)