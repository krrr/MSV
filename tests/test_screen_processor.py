from unittest import TestCase
from msv.screen_processor import MockStaticImageProcessor
import time


class TestScreenProcessor(TestCase):
    processor = None

    def setUp(self):
        self.processor = MockStaticImageProcessor()

    def test_find_minimap_rect(self):
        self.processor.set_test_img('unittest_data/minimap_guild.png')
        # self.processor.set_test_img('unittest_data/minimap_guild.png'))
        t = time.perf_counter()
        self.assertIsNotNone(self.processor.get_minimap_rect())
        print('find_minimap_rect took %.3fs' % (time.perf_counter() - t,))

    def test_find_player(self):
        self.processor.set_test_img('unittest_data/minimap_guild.png')
        t = time.perf_counter()
        self.assertIsNotNone(self.processor.find_player_minimap_marker())
        print('find_player took %.3fs' % (time.perf_counter() - t,))

    def test_find_other_player(self):
        self.processor.set_test_img('unittest_data/minimap_none.png')
        self.assertIsNone(self.processor.find_other_player_marker(), 'false positive')

        self.processor.set_test_img('unittest_data/minimap_guild.png')
        self.assertIsNotNone(self.processor.find_other_player_marker(), 'guild not found')

        self.processor.set_test_img('unittest_data/minimap_friend.png')
        self.assertIsNotNone(self.processor.find_other_player_marker(), 'friend not found')

        self.processor.set_test_img('unittest_data/minimap_stranger.png')
        t = time.perf_counter()
        self.assertIsNotNone(self.processor.find_other_player_marker(), 'stranger not found')
        print('find_other_player took %.3fs' % (time.perf_counter() - t,))

    def test_check_elite_boss(self):
        self.processor.set_test_img('unittest_data/eboss_sample1.png')
        self.assertTrue(self.processor.check_elite_boss())
        self.processor.set_test_img('unittest_data/eboss_sample2.png')
        self.assertTrue(self.processor.check_elite_boss())
        self.processor.set_test_img('unittest_data/eboss_false_sample.png')
        t = time.perf_counter()
        self.assertFalse(self.processor.check_elite_boss())
        print('check_elite_boss took %.3fs' % (time.perf_counter() - t,))

    def test_check_white_room(self):
        self.processor.set_test_img('unittest_data/white_room.png')
        self.assertTrue(self.processor.check_white_room())
        self.processor.set_test_img('unittest_data/white_room1.png')
        t = time.perf_counter()
        self.assertTrue(self.processor.check_white_room())
        print('check_white_room took %.3fs' % (time.perf_counter() - t,))

    def test_check_dialog(self):
        self.processor.set_test_img('unittest_data/bounty_hunter_dialog.png')
        t = time.perf_counter()
        self.assertTrue(self.processor.check_dialog())
        print('check_dialog took %.3fs' % (time.perf_counter() - t,))

    def test_check_gm_cap(self):
        self.processor.set_test_img('unittest_data/white_room1.png')
        self.assertTrue(self.processor.check_gm_cap())
        self.processor.set_test_img('unittest_data/white_room2.png')
        t = time.perf_counter()
        self.assertTrue(self.processor.check_gm_cap())
        print('check_gm_cap took %.3fs' % (time.perf_counter() - t,))
