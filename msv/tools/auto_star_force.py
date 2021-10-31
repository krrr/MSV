import re
import time
import logging
import random
from PIL import ImageOps
import msv.directinput_constants as dc
from msv.tools import ToolBase
from msv.util import setup_tesseract_ocr, color_distance
from msv.screen_processor import ScreenProcessor, GameCaptureError


class AutoStarForce(ToolBase):
    AREA_SIZE = (342, 295)
    AREA_POS = (513, 218)
    CURR_STAR_RECT = (138, 92, 138+115, 92+16)
    STAR_CATCH_OPTION_POINT = (144, 207)
    SAFE_GUARD_OPTION_POINT = (302, 207)
    OPTION_DISABLED, OPTION_UNCHECKED, OPTION_CHECKED = range(3)
    RESULT_SUCCESS, RESULT_FAILED, RESULT_DESTROYED = range(3)
    OPTION_PIXEL_MAP = {(238, 0, 102): OPTION_CHECKED, (255, 255, 255): OPTION_UNCHECKED, (187, 187, 187): OPTION_DISABLED}
    ENHANCE_BTN_POS = (129, 265)
    CONFIRM_OK_BTN_POS = (94, 226)
    RESULT_OK_BTN_POS = (183, 226)
    CATCHER_CHECK_POS = (49, 52)
    GREEN_COLOR = (136, 170, 17)
    STAR_TRACK_COLOR = (204, 204, 204)
    SUCCESS_FONT_COLOR = (255, 255, 34)
    RESULT_TEXT_RECT = (55, 171, 293, 200)
    DIALOG_BLUE_COLOR = (24, 139, 198)

    def __init__(self, screen_processor, log_level=logging.DEBUG, conn=None):
        super().__init__(screen_processor, log_level, conn)

        setup_tesseract_ocr()
        import pyocr.libtesseract
        if not pyocr.libtesseract.is_available():
            raise Exception('no OCR tool available')
        self.tool = pyocr.libtesseract
        if 'eng' not in self.tool.get_available_languages():
            raise Exception('tesseract english data not available')

        self.current_star_regexp = re.compile('(\\d+)\\s?Star\\s?>\\s?\\d+\\s?Star')
        self.rect = None
        self.center_pos = None
        self.area_pos = self.AREA_POS

    def run(self, args):
        target_star, star_catch, safe_guard = args
        self.logger.info('start enhancing to %s', target_star)
        count = 0
        next_star = None
        while True:
            self.update_image()

            if next_star is None:
                curr = self.get_current_star()
                if curr is None:
                    raise Exception('failed to determine current star')
            else:
                curr = next_star

            if curr >= target_star:
                break

            self.logger.info('current star: %s', curr)

            options = self.get_enhance_options()
            if (star_catch and options[0] == self.OPTION_CHECKED) or (not star_catch and options[0] == self.OPTION_UNCHECKED):
                self.input_mgr.mouse_left_click_at(*self._map_pos(self.STAR_CATCH_OPTION_POINT), 4)
                time.sleep(0.08)
            if (safe_guard and options[1] == self.OPTION_UNCHECKED) or (not safe_guard and options[1] == self.OPTION_CHECKED):
                self.input_mgr.mouse_left_click_at(*self._map_pos(self.SAFE_GUARD_OPTION_POINT), 4)
                time.sleep(0.08)

            if self.poll_conn():
                return

            self.input_mgr.mouse_left_click_at(*self._map_pos(self.ENHANCE_BTN_POS), 8)
            time.sleep(random.uniform(0.06, 0.09))
            self.input_mgr.mouse_left_click_at(*self._map_pos(self.CONFIRM_OK_BTN_POS), 8)

            time.sleep(random.uniform(0.1, 0.2))
            self.input_mgr.mouse_move(*self._map_pos((random.randint(5, 110), self.AREA_SIZE[1]+random.randint(-60, -5))))

            if star_catch:
                time.sleep(0.1)
                if self.wait(catcher=True) == 0:
                    time.sleep(0.1)
                    self.wait_star_center()
                    self.input_mgr.single_press(dc.DIK_RETURN)

            # game showing slow shining animation
            self.wait(result=True)
            result = self.get_result()

            if self.poll_conn():
                return

            time.sleep(random.uniform(0.06, 0.09))
            self.input_mgr.mouse_left_click_at(*self._map_pos(self.RESULT_OK_BTN_POS), 8)
            time.sleep(random.uniform(0.25, 0.35))
            if result == self.RESULT_SUCCESS:
                self.logger.debug('success')
                time.sleep(0.1)
                for _ in range(20):
                    time.sleep(0.1)
                    self.update_image()
                    if self.get_current_star() != curr:  # text update delays
                        break
                # maybe star is capped after this enhancement, so check again in the next iteration
                next_star = None
                if safe_guard:
                    self.input_mgr.single_press(dc.DIK_RETURN)
                    time.sleep(random.uniform(0.04, 0.06))
                    self.input_mgr.single_press(dc.DIK_RETURN)
            elif result == self.RESULT_FAILED:
                self.logger.debug('fail')
                next_star = curr - 1 if (curr > 10 and curr != 15 and curr != 20) else curr
                time.sleep(0.8)

                # self.logger.info(self.img.getpixel(self.center_pos))
                # if color_distance(self.img.getpixel(self.center_pos), self.DIALOG_BLUE_COLOR) < 20:
                if safe_guard:
                    self.input_mgr.single_press(dc.DIK_RETURN)
                    time.sleep(random.uniform(0.04, 0.06))
                    self.input_mgr.single_press(dc.DIK_RETURN)
            elif result == self.RESULT_DESTROYED:
                self.logger.info('destroyed!!!')
                return
            else:
                raise Exception('unknown result')

            if self.poll_conn():
                return

            self.logger.debug('-------------------------------')
            count += 1

    def get_current_star(self):
        curr_star_img = ImageOps.invert(self.img.crop(self.CURR_STAR_RECT).convert('L'))
        txt = self.tool.image_to_string(curr_star_img, lang='eng')
        txt = txt.replace('O', '0')
        match = self.current_star_regexp.match(txt)
        return int(match.group(1)) if match else None

    def update_image(self):
        if self.rect is None:  # setup window rect
            self.scale_ratio = self.screen_processor.get_scale_ratio()
            self.ms_rect = self.screen_processor.ms_get_screen_rect()
            if self.ms_rect is None:
                raise GameCaptureError
            x, y = self.AREA_POS[0], self.AREA_POS[1]
            self.rect = (x, y, x+self.AREA_SIZE[0], y+self.AREA_SIZE[1])
            self.center_pos = (self.AREA_SIZE[0] // 2, self.AREA_SIZE[1] // 2)

            self.screen_processor.set_foreground()

        self.img = self.screen_processor.capture_pil(rect=self.rect)

    def get_enhance_options(self):
        star_catch_pixel = self.img.getpixel(self.STAR_CATCH_OPTION_POINT)[:3]
        safe_guard_pixel = self.img.getpixel(self.SAFE_GUARD_OPTION_POINT)[:3]
        return self.OPTION_PIXEL_MAP.get(star_catch_pixel), self.OPTION_PIXEL_MAP.get(safe_guard_pixel)

    def is_catcher_present(self):
        return self.img.getpixel(self.CATCHER_CHECK_POS)[:3] == (0, 0, 0)

    def is_result_present(self):
        return self.img.getpixel(self.RESULT_OK_BTN_POS)[:3] == self.GREEN_COLOR

    def get_result(self):
        area = self.img.crop(self.RESULT_TEXT_RECT)
        for x in range(area.width):
            for y in range(area.height):
                px = area.getpixel((x, y))[:3]
                if px == (255, 255, 34):  # yellow
                    return self.RESULT_SUCCESS
                elif px == (255, 34, 34):  # red
                    return self.RESULT_FAILED
                elif px == (0, 0, 0):  # black
                    return self.RESULT_DESTROYED
        return None

    # this method should be fast
    def wait_star_center(self):
        target_zone_width = 99999
        # determine advance x
        for x in range(123, 151):
            if color_distance(self.img.getpixel((x, 217)), (221, 112, 41)) < 20:
                target_zone_width = (170 - x) * 2
                break

        # print('target_zone_width:', target_zone_width)
        x, y, w, h = 163, 215, 8, 1  # check this area on star track border

        rect = (self.rect[0]+x, self.rect[1]+y, self.rect[0]+x+w, self.rect[1]+y+h)
        start = time.time()
        while True:
            img = self.screen_processor.capture_pil(rect=rect)  # faster than self.update_image
            if any(color_distance(img.getpixel((x, 0)), self.STAR_TRACK_COLOR) > 50 for x in range(w)):
                break

            if time.time() - start > 2:
                self.logger.warning('wait_star_center timeout')
                break

    def wait(self, catcher=False, result=False):
        start = time.time()
        while True:
            self.update_image()
            if catcher:
                if self.is_catcher_present():
                    return 0
                elif self.is_result_present():
                    return 1
            elif result:
                if self.is_result_present():
                    return 0
            else:
                raise Exception('wrong argument')

            if time.time() - start > 10:
                raise Exception('timeout')
            time.sleep(0.02)


if __name__ == "__main__":
    auto_star_force = AutoStarForce(ScreenProcessor())
    auto_star_force.run((17, True, True))