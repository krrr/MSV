from unittest import TestCase
from src.screen_processor import MockScreenProcessor
from src.rune_solver.rune_solver_simple import RuneSolverSimple
import time


class TestRuneSolver(TestCase):
    processor = solver = None

    def setUp(self):
        self.processor = MockScreenProcessor()
        self.solver = RuneSolverSimple(self.processor)

    def test_limina(self):
        self.processor.set_test_img('unittest_data/rune/limina1.png')
        t = time.perf_counter()
        self.assertEqual(self.solver.solve(), ('right', 'right', 'right', 'right'))
        print('solve took %.3fs' % (time.perf_counter() - t,))
        self.processor.set_test_img('unittest_data/rune/limina2.png')
        self.assertEqual(self.solver.solve(), ('left', 'left', 'right', 'down'))

