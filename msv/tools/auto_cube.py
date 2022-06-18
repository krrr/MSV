# import re
# import cv2
# import time
# import logging
# import random
# import numpy as np
# from PIL import ImageOps, ImageEnhance
# import msv.directinput_constants as dc
# from msv.tools import ToolBase
# from msv.util import setup_tesseract_ocr, color_distance, random_number
# from msv.screen_processor import ScreenProcessor, GameCaptureError


## DEATH WARNING
## TRASH GARBAGE GAME
## SANITY/BEHAVIOR CHECK KILLED ME
# class AutoCube(ToolBase):
#     RED_AREA_SIZE = (196, 483)
#     RED_AREA_POS = (585, 242)
#     RED_POTENTIAL_RECT = (18, 187, 176, 227)
#     TRY_BTN_POS = (83, 263)
#     LINE_PATTERN = {
#         'all': re.compile('^All Stats: \\+(\\d+)%'),
#         'str': re.compile('^STR: \\+(\\d+)%'),
#         'int': re.compile('^INT: \\+(\\d+)%'),
#         'dex': re.compile('^DEX: \\+(\\d+)%'),
#         'luk': re.compile('^LUK: \\+(\\d+)%'),
#         'invi': re.compile('^(\\d+)% chance to become invin.+'),
#         'invi2': re.compile('^[Ii]nvincible for.+'),
#         'hp': re.compile('^Max HP.+'),
#         'mp': re.compile('^Max MP.+'),
#         'ignore_dam': re.compile('^\\d+% chance to ignore.+'),
#         'reflect_dam': re.compile('^\\d+% chance to reflect.+'),
#         'hp_rec_items': re.compile('^HP Recovery I?tems.+'),
#         'def': re.compile('^DEF: \\+\\d+%'),
#     }
#
#     def __init__(self, screen_processor, config=None, conn=None):
#         super().__init__(screen_processor, config, conn)
#
#         self._setup_ocr()
#         from pyocr.builders import TextBuilder
#         self._orc_txt_builder = TextBuilder
#         self.rect = None
#         self.area_pos = self.RED_AREA_POS
#
#     def run(self, args):
#         retry_count = 0
#         while True:
#             self.update_image()
#             try:
#                 lines = self.get_current_potential()
#             except Exception as e:
#                 if retry_count >= 3:
#                     raise e
#                 retry_count += 1
#                 time.sleep(1)
#                 continue
#             retry_count = 0
#             print(lines)
#             if len(tuple(i for i in lines if i[0] == 'all' or i[0] == 'int')) == 3 and any(i for i in lines if i[0] == 'int' and i[1] >= 12):
#                 break
#             self.input_mgr.mouse_left_click_at(*self._map_pos(self.TRY_BTN_POS), 4)
#             for _ in range(3):
#                 time.sleep(0.04 + random_number(0.03))
#                 self.input_mgr.single_press(dc.DIK_RETURN)
#
#             time.sleep(1.7 + random_number(0.1))
#             print('------------')
#         while True:
#             time.sleep(1)
#
#     def update_image(self):
#         if self.rect is None:  # setup window rect
#             self.scale_ratio = self.screen_processor.get_scale_ratio()
#             self.ms_rect = self.screen_processor.ms_get_screen_rect()
#             if self.ms_rect is None:
#                 raise GameCaptureError
#             x, y = self.RED_AREA_POS[0], self.RED_AREA_POS[1]
#             self.rect = (x, y, x+self.RED_AREA_SIZE[0], y+self.RED_AREA_SIZE[1])
#
#             self.screen_processor.set_foreground()
#
#         self.img = self.screen_processor.capture_pil(rect=self.rect)
#
#     def get_current_potential(self):
#         ret = []
#         for i in range(3):
#             rect = (self.RED_POTENTIAL_RECT[0], self.RED_POTENTIAL_RECT[1] + 14 * i,
#                     self.RED_POTENTIAL_RECT[2], self.RED_POTENTIAL_RECT[1] + 14 * (i + 1))
#             line_img = ImageOps.invert(self.img.crop(rect).convert('L').point(lambda x: x if x > 50 else 0))
#             enhancer = ImageEnhance.Contrast(line_img)
#             line_img = enhancer.enhance(2)
#             # line_img.show()
#             txt = self.tool.image_to_string(line_img, 'eng', self._orc_txt_builder(7))
#             if not txt:
#                 continue
#                 # raise Exception('no txt')
#             print(txt)
#             for t, pattern in self.LINE_PATTERN.items():
#                 match = pattern.match(txt)
#                 if match:
#                     ret.append((t, int(match.group(1)) if match.lastindex else None))
#                     break
#             # else:
#             #     raise Exception('unknown potential line: ' + txt)
#
#         return ret
#
#
# if __name__ == "__main__":
#     auto_star_force = AutoCube(ScreenProcessor())
#     auto_star_force.run(None)
