import cv2
import numpy as np
from msv.rune_solver.rune_solver_base import RuneSolverBase
from msv.util import read_qt_resource


class RuneSolverSimple(RuneSolverBase):
    THRESHOLD = 0.2

    """
    Using OpenCV's static template matching to solve rune.
    v216 update changed rune's pattern: circle is removed, arrow have no transparency anymore,
    arrow's color is fixed.
    """
    def __init__(self, screen_capturer=None, key_mgr=None):
        super().__init__(screen_capturer, key_mgr)

        # load template
        down_tpl = cv2.imdecode(read_qt_resource(':/template/down_arrow_template.png', True), cv2.IMREAD_COLOR)
        right_tpl = np.rot90(down_tpl)
        up_tpl = np.rot90(right_tpl)
        left_tpl = np.rot90(up_tpl)
        self.templates = {'left': left_tpl, 'up': up_tpl, 'right': right_tpl, 'down': down_tpl}

        down_sm_tpl = cv2.imdecode(read_qt_resource(':/template/down_arrow_template_small.png', True), cv2.IMREAD_COLOR)
        right_sm_tpl = np.rot90(down_sm_tpl)
        up_sm_tpl = np.rot90(right_sm_tpl)
        left_sm_tpl = np.rot90(up_sm_tpl)
        self.templates_small = {'left': left_sm_tpl, 'up': up_sm_tpl, 'right': right_sm_tpl, 'down': down_sm_tpl}

    def do_match(self, img, template, threshold):
        # make mask
        __, mask = cv2.threshold(cv2.cvtColor(template, cv2.COLOR_BGR2GRAY), 1, 255, cv2.THRESH_BINARY)
        res = cv2.matchTemplate(img, template, cv2.TM_SQDIFF_NORMED, mask=mask)
        return np.where(res <= threshold)  # matched locations

    def solve(self):
        img = self.capture_roi()
        return self.try_solve(img)

    def try_solve(self, img):
        result = []
        for dir in self.templates:
            pos_list = self.match_one_direction(img, dir)
            for i in pos_list:
                result.append({'dir': dir, 'pos': i})

        if len(result) != 4:
            self.logger.warning('wrong rune result: ' + str(result))
            return None

        result.sort(key=lambda i: i['pos'][0])
        return tuple(i['dir'] for i in result)

    def match_one_direction(self, img, direction):
        template = self.templates[direction]
        template_sm = self.templates_small[direction]

        loc = self.do_match(img, template, self.THRESHOLD)
        loc_sm = self.do_match(img, template_sm, self.THRESHOLD)
        loc = (np.concatenate((loc[0], loc_sm[0])), np.concatenate((loc[1], loc_sm[1])))

        ret = []

        for pt in zip(*loc[::-1]):
            if any(abs(i[0]-pt[0]) < 12 and abs(i[1]-pt[1]) < 12 for i in ret):
                continue
            ret.append(pt)
        return ret
