from unittest import TestCase
from terrain_analyzer import PathAnalyzer, MoveMethod


class TestScreenProcessor(TestCase):
    pathextractor = None

    def setUp(self):
        self.pathextractor = PathAnalyzer()

    def test_dclp1(self):
        self._load("../msv/resources/platform/deep_cavern_lower_path1.platform")

    def test_train(self):
        self._load("../msv/resources/platform/train_no_dest1.platform")

    def test_mirror_touched_sea2(self):
        self._load("unittest_data/mirror_touched_sea2.platform")

        solution = self.pathextractor.pathfind('a12ed5e3', '0f9c84c4')
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == MoveMethod.JUMPL)

        solution = self.pathextractor.pathfind('304c485d', '0f9c84c4')
        self.assertTrue(solution and len(solution) == 2 and solution[0].method == MoveMethod.TELEPORTR and solution[1].method == MoveMethod.TELEPORTUP)

    def _load(self, path):
        self.pathextractor.load(path)
        print('#### Platforms', self.pathextractor.platforms)

        for key, val in self.pathextractor.platforms.items():
            print(val)
            print(val.solutions)
            print("----")
        print('\n\n\n')
