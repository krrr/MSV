from unittest import TestCase
from src.screen_processor import StaticImageProcessor, MapleScreenCapturer
from PIL import Image


class MockMapleScreenCapturer(MapleScreenCapturer):
    def ms_get_screen_hwnd(self):
        return 1

    def ms_get_screen_rect(self, _):
        return (0, 0, 500, 500)


class TestScreenProcessor(TestCase):
    processor = None

    def setUp(self):
        self.processor = StaticImageProcessor(MockMapleScreenCapturer())

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
