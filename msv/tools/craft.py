import time
import logging
import random
import cv2
import numpy as np
import msv.directinput_constants as dc
from msv.tools import ToolBase
from msv.util import read_qt_resource, random_number
from msv.screen_processor import ScreenProcessor, GameCaptureError


class Craft(ToolBase):
    def __init__(self, screen_processor, log_level=logging.DEBUG, conn=None):
        super().__init__(screen_processor, log_level, conn)

        self.craft_btn_tpl = cv2.imdecode(read_qt_resource(':/template/craft_btn.png', True), cv2.IMREAD_COLOR)
        self.craft_ok_btn_tpl = cv2.imdecode(read_qt_resource(':/template/craft_ok_btn.png', True), cv2.IMREAD_COLOR)

    def run(self, args):
        self.logger.info('start crafting')

        while True:
            self.update_image()

            # check craft button clickable
            res = cv2.matchTemplate(self.img, self.craft_btn_tpl, cv2.TM_SQDIFF_NORMED)
            loc = np.where(res <= 0.04)
            if len(loc[0]) == 0:
                time.sleep(1)
                continue
            craft_btn_pos = next(zip(*loc[::-1]))

            # click craft button
            craft_btn_pos = (craft_btn_pos[0]+random.randint(3, 45), craft_btn_pos[1]+random.randint(3, 12))
            self.input_mgr.mouse_left_click_at(*self._map_pos(craft_btn_pos))
            time.sleep(0.1 + random_number(0.1))
            self.input_mgr.mouse_left_click()
            time.sleep(0.5 + random_number(0.15))
            # confirm dialog
            self.input_mgr.single_press(dc.DIK_RETURN)
            # wait crafting
            time.sleep(4 + random_number(0.3))
            # result dialog
            self.update_image()
            res = cv2.matchTemplate(self.img, self.craft_ok_btn_tpl, cv2.TM_SQDIFF_NORMED)
            loc = np.where(res <= 0.04)
            if len(loc[0]) == 0:
                raise Exception('ok button not detected')
            btn_pos = next(zip(*loc[::-1]))
            self.logger.info('crafted ')
            btn_pos = (btn_pos[0]+random.randint(3, 31), btn_pos[1]+random.randint(3, 10))
            self.input_mgr.mouse_left_click_at(*self._map_pos(btn_pos))
            time.sleep(0.1 + random_number(0.15))
            self.input_mgr.mouse_move(*self._map_pos((craft_btn_pos[0]+random.randint(-130, 30), craft_btn_pos[1]+random.randint(25, 80))))
            time.sleep(1 + random_number(0.2))

    def _map_pos(self, pos):
        return (self.ms_rect[0] + (pos[0]) * self.scale_ratio,
                self.ms_rect[1] + (pos[1]) * self.scale_ratio)

    def update_image(self):
        if self.ms_rect is None:  # setup window rect
            self.scale_ratio = self.screen_processor.get_scale_ratio()
            self.ms_rect = self.screen_processor.ms_get_screen_rect()
            if self.ms_rect is None:
                raise GameCaptureError

            self.screen_processor.set_foreground()

        self.img = self.screen_processor.capture()


if __name__ == "__main__":
    craft = Craft(ScreenProcessor())
    craft.run(())