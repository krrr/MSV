from unittest import TestCase
from src.macro_script import MacroController


class TestMacroController(TestCase):
    macro_controller = None

    def setUp(self):
        self.macro_controller = MacroController()
        ret = self.macro_controller.load_and_process_platform_map(r"unittest_data/mirror_touched_sea2.platform")
        assert ret != 0

    def test_ddd(self):
        print(self.macro_controller.terrain_analyzer.platforms)