from unittest import TestCase
from terrain_analyzer import PathAnalyzer, MoveMethod


class TestScreenProcessor(TestCase):
    pathextractor = None

    def setUp(self):
        self.pathextractor = PathAnalyzer()

    def test_2_4(self):
        self._load("../msv/resources/platform/end_of_the_world2_4.platform")

        solution = self.pathextractor.pathfind('444ae3dc', 'e8c6644f')  # really high
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == MoveMethod.JUMPTELEPORTUP)

        solution = self.pathextractor.pathfind('444ae3dc', 'bcd4711b')  # vertical close platform
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == MoveMethod.TELEPORTDOWN)

    def test_1_4(self):
        self._load("../msv/resources/platform/end_of_the_world1_4.platform")

        solution = self.pathextractor.pathfind('c214856a', '6865257d')  # center top to middle
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == MoveMethod.DROP)

        solution = self.pathextractor.pathfind('c214856a', '5b53ae83')  # center top to bottom
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == MoveMethod.TELEPORTDOWN)

        solution = self.pathextractor.pathfind('6865257d', '5b53ae83')  # center middle to bottom
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == MoveMethod.TELEPORTDOWN)

    def test_dclp1(self):
        self._load("../msv/resources/platform/deep_cavern_lower_path1.platform")

    def test_mirror_touched_sea2(self):
        self._load("unittest_data/mirror_touched_sea2.platform")

        solution = self.pathextractor.pathfind('6029314b', '0f9c84c4')
        self.assertTrue(solution and len(solution) == 1 and solution[0].method == MoveMethod.JUMPTELEPORTUP)

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
