from unittest import TestCase
from src.screen_processor import StaticImageProcessor, ScreenProcessor
from PIL import Image


class MockScreenProcessor(ScreenProcessor):
    def ms_get_screen_hwnd(self):
        return 1

    def ms_get_screen_rect(self, _):
        return (0, 0, 500, 500)


class TestScreenProcessor(TestCase):
    processor = None

    def setUp(self):
        self.processor = StaticImageProcessor(MockScreenProcessor())

    def test_find_minimap_rect(self):
        self.processor.update_image(Image.open('unittest_data/minimap_guild.png'))
        self.assertIsNotNone(self.processor.get_minimap_rect())

    def test_find_player(self):
        self.processor.update_image(Image.open('unittest_data/minimap_guild.png'))
        self.assertIsNotNone(self.processor.find_player_minimap_marker())

    def test_find_other_player(self):
        self.processor.update_image(Image.open('unittest_data/minimap_none.png'))
        self.assertIsNone(self.processor.find_other_player_marker(), 'false positive')

        self.processor.update_image(Image.open('unittest_data/minimap_guild.png'))
        self.assertIsNotNone(self.processor.find_other_player_marker(), 'guild not found')

        self.processor.update_image(Image.open('unittest_data/minimap_friend.png'))
        self.assertIsNotNone(self.processor.find_other_player_marker(), 'friend not found')

        self.processor.update_image(Image.open('unittest_data/minimap_stranger.png'))
        self.assertIsNotNone(self.processor.find_other_player_marker(), 'stranger not found')

    def test_check_elite_boss(self):
        self.processor.update_image(Image.open('unittest_data/eboss_sample1.png'))
        self.assertTrue(self.processor.check_elite_boss())
        self.processor.update_image(Image.open('unittest_data/eboss_sample2.png'))
        self.assertTrue(self.processor.check_elite_boss())
        self.processor.update_image(Image.open('unittest_data/eboss_false_sample.png'))
        self.assertFalse(self.processor.check_elite_boss())

    def test_check_white_room(self):
        self.processor.update_image(Image.open('unittest_data/white_room.png'))
        self.assertTrue(self.processor.check_white_room())

    def test_check_dialog(self):
        self.processor.update_image(Image.open('unittest_data/bounty_hunter_dialog.png'))
        self.assertTrue(self.processor.check_dialog())

    def test_exp_full(self):
        self.processor.update_image(Image.open('unittest_data/exp_full.jpg'))
        self.assertTrue(self.processor.check_exp_full())
        self.processor.update_image(Image.open('unittest_data/bounty_hunter_dialog.png'))
        self.assertFalse(self.processor.check_exp_full())
