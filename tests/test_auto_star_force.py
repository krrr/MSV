from unittest import TestCase
from tools.auto_star_force import AutoStarForce
from PIL import Image
from screen_processor import ScreenProcessor
import time


class MockScreenProcessor(ScreenProcessor):
    img = None

    def get_game_hwnd(self):
        return 1

    def ms_get_screen_rect(self, hwnd=None):
        return (0, 0, 1366, 768)

    def capture_pil(self, hwnd=None, rect=None):
        return self.img.crop(rect) if rect else self.img


class TestScreenProcessor(TestCase):
    auto_star_force = None
    processor = None

    def setUp(self):
        self.processor = MockScreenProcessor()
        self.auto_star_force = AutoStarForce(self.processor)

    def test_get_current_star(self):
        self.processor.img = Image.open('unittest_data/star_force/before.png')
        self.auto_star_force.update_image()
        t = time.perf_counter()
        self.assertEqual(self.auto_star_force.get_current_star(), 0)
        print('get_current_star time:', time.perf_counter() - t)

        self.processor.img = Image.open('unittest_data/star_force/before1.png')
        self.auto_star_force.update_image()
        self.assertEqual(self.auto_star_force.get_current_star(), 2)

    def test_get_options(self):
        self.processor.img = Image.open('unittest_data/star_force/before.png')
        self.auto_star_force.update_image()
        self.assertEqual(self.auto_star_force.get_enhance_options(),
                         (AutoStarForce.OPTION_UNCHECKED, AutoStarForce.OPTION_DISABLED))

        self.processor.img = Image.open('unittest_data/star_force/before1.png')
        self.auto_star_force.update_image()
        self.assertEqual(self.auto_star_force.get_enhance_options(),
                         (AutoStarForce.OPTION_CHECKED, AutoStarForce.OPTION_DISABLED))

        self.processor.img = Image.open('unittest_data/star_force/catch0.png')
        self.auto_star_force.update_image()
        self.assertEqual(self.auto_star_force.is_result_present(), False)
        self.assertEqual(self.auto_star_force.is_catcher_present(), True)

        self.processor.img = Image.open('unittest_data/star_force/result.png')
        self.auto_star_force.update_image()
        self.assertEqual(self.auto_star_force.is_result_present(), True)
        self.assertEqual(self.auto_star_force.is_catcher_present(), False)

        self.processor.img = Image.open('unittest_data/star_force/confirm.png')
        self.auto_star_force.update_image()
        self.assertEqual(self.auto_star_force.is_result_present(), False)
