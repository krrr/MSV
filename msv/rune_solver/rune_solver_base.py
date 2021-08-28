"""Classifier model verifier"""
import logging
import random
import time
from msv.screen_processor import ScreenProcessor
from msv.input_manager import InputManager
from msv.directinput_constants import DIK_UP, DIK_DOWN, DIK_LEFT, DIK_RIGHT
from msv.util import get_file_log_handler


class RuneSolverBase:
    def __init__(self, screen_capturer=None, key_mgr=None):
        """
        Run just Once to initialize
        example: {'down': 0, 'left': 1, 'right': 2, 'up': 3}
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(get_file_log_handler())

        self.rune_roi_1366 = (450, 165, 500, 110)  # x, y, w, h
        self.rune_roi_1024 = (295, 165, 500, 110)
        self.rune_roi_800 = (170, 200, 440, 120)
        self.rune_roi = self.rune_roi_800  # set as default rune roi
        self.screen_processor = ScreenProcessor() if not screen_capturer else screen_capturer
        self.key_mgr = InputManager() if not key_mgr else key_mgr

    def capture_roi(self):
        captured_image = self.screen_processor.capture()
        screen_width = captured_image.shape[1]
        if screen_width > 1300:
            self.rune_roi = self.rune_roi_1366
        elif screen_width > 1000:
            self.rune_roi = self.rune_roi_1024
        elif screen_width > 800:
            self.rune_roi = self.rune_roi_800
        captured_roi = captured_image[self.rune_roi[1]:self.rune_roi[1]+self.rune_roi[3], self.rune_roi[0]:self.rune_roi[0]+self.rune_roi[2]]

        return captured_roi

    def solve_auto(self):
        """
        Solves rune if present and sends key presses.
        :return: -1 if rune not detected, result of classify() if successful
        """
        result = self.solve()
        if result is None:
            return None

        self.logger.debug("Solved rune with solution %s" % str(result))
        for inp in result:
            if inp == "up":
                self.key_mgr.single_press(DIK_UP)
            elif inp == "down":
                self.key_mgr.single_press(DIK_DOWN)
            elif inp == "left":
                self.key_mgr.single_press(DIK_LEFT)
            elif inp == "right":
                self.key_mgr.single_press(DIK_RIGHT)
            # https://www.reddit.com/r/Maplestory/comments/a9b0lj/nexons_new_autoban_system_explained/?st=JQ35N82V&sh=3eeba9e3
            time.sleep(0.2 + random.uniform(0, 0.15))

        return len(result)

    def solve(self):
        """
        Solves rune if present and just returns solution.
        :return: None if rune not detected, result of classify() if successful
        """
        raise NotImplementedError
