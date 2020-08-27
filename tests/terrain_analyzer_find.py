from unittest import TestCase
import terrain_analyzer
from terrain_analyzer import PathAnalyzer


class TestScreenProcessor(TestCase):
    pathextractor = None

    def setUp(self):
        self.pathextractor = PathAnalyzer()

    def test_dclp1(self):
        self._load("../src/mapscripts/deep_cavern_lower_path1.platform")

    def test_cup(self):
        self._load("../src/mapscripts/cavern_upper_path.platform")

        solution = self.pathextractor.pathfind('9769210f', '4768c4f7')
        # teleport between platforms with high y position diff
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == terrain_analyzer.METHOD_TELEPORTL)

    def test_mirror_touched_sea2(self):
        self._load("unittest_data/mirror_touched_sea2.platform")

        solution = self.pathextractor.pathfind('6029314b', '0f9c84c4')
        self.assertTrue(solution and len(solution) == 2 and solution[0].method == terrain_analyzer.METHOD_TELEPORTUP and solution[1].method == terrain_analyzer.METHOD_TELEPORTUP)

        solution = self.pathextractor.pathfind('a12ed5e3', '0f9c84c4')
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == terrain_analyzer.METHOD_JUMPL)

        solution = self.pathextractor.pathfind('304c485d', '0f9c84c4')
        self.assertTrue(solution and len(solution) == 2 and solution[0].method == terrain_analyzer.METHOD_TELEPORTR and solution[1].method == terrain_analyzer.METHOD_TELEPORTUP)

    def _load(self, path):
        self.pathextractor.load(path)
        print('#### Platforms', self.pathextractor.platforms)
        self.pathextractor.generate_solution_dict()

        for key, val in self.pathextractor.platforms.items():
            print(val)
            print(val.solutions)
            print("----")
        print('\n\n\n')
