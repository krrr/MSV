# -*- coding:utf-8 -*-
"""Classifier model verifier"""
import logging
import random
from screen_processor import ScreenProcessor
import cv2, time
import numpy as np
from keystate_manager import KeyboardInputManager
from directinput_constants import DIK_UP, DIK_DOWN, DIK_LEFT, DIK_RIGHT, DIK_NUMLOCK
from win32con import VK_NUMLOCK
from win32api import GetKeyState
from util import get_file_log_handler


class RuneSolverBase:
    def __init__(self, screen_capturer=None, key_mgr=None):
        """
        Run just Once to initialize
        example: {'down': 0, 'left': 1, 'right': 2, 'up': 3}
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(get_file_log_handler())

        self.rune_roi_1366 = [450, 180, 500, 130]  # x, y, w, h
        self.rune_roi_1024 = [295, 180, 500, 133]
        self.rune_roi_800 = [170, 200, 440, 135]
        self.rune_roi = self.rune_roi_800  # set as default rune roi
        self.screen_processor = ScreenProcessor() if not screen_capturer else screen_capturer
        self.key_mgr = KeyboardInputManager() if not key_mgr else key_mgr

    def capture_roi(self):
        screen_rect = self.screen_processor.ms_get_screen_rect(self.screen_processor.ms_get_screen_hwnd())
        screen_width = screen_rect[2]-screen_rect[0]

        if screen_width > 1300:
            self.rune_roi = self.rune_roi_1366
        elif screen_width > 1000:
            self.rune_roi = self.rune_roi_1024
        elif screen_width > 800:
            self.rune_roi = self.rune_roi_800

        captured_image = self.screen_processor.capture(set_focus=False, rect=screen_rect)
        captured_roi = cv2.cvtColor(np.array(captured_image), cv2.COLOR_RGB2BGR)
        captured_roi = captured_roi[self.rune_roi[1]:self.rune_roi[1]+self.rune_roi[3], self.rune_roi[0]:self.rune_roi[0]+self.rune_roi[2]]

        return captured_roi

    def solve_auto(self):
        """
        Solves rune if present and sends key presses.
        :return: -1 if rune not detected, result of classify() if successful
        """
        result = self.solve()
        if result is None:
            return None

        if GetKeyState(VK_NUMLOCK):
            self.key_mgr.single_press(DIK_NUMLOCK)
            time.sleep(0.2)
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
            time.sleep(0.17 + random.uniform(0, 0.1))

        return len(result)

    def solve(self):
        """
        Solves rune if present and just returns solution.
        :return: None if rune not detected, result of classify() if successful
        """
        raise NotImplementedError
