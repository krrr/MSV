import cv2, win32gui, time, math
import os
import d3dshot
import numpy as np, ctypes, ctypes.wintypes
import sys
from PIL import ImageGrab
import util


class GameCaptureError(Exception):
    pass


class MapleWindowNotFoundError(GameCaptureError):
    pass


class ScreenProcessor:
    d3dshot = None

    """Container for capturing MS screen"""
    def __init__(self):
        self.hwnd = None
        if not ctypes.windll.user32.IsProcessDPIAware():
            ctypes.windll.user32.SetProcessDPIAware()

        if sys.getwindowsversion().major == 10 and ScreenProcessor.d3dshot is None:
            ScreenProcessor.d3dshot = d3dshot.create()

    def ms_get_screen_hwnd(self):
        return win32gui.FindWindowEx(0, 0, "MapleStoryClass", None)

    def ms_get_screen_rect(self, hwnd=None):
        """
        Get client rect of game window
        :param hwnd: window handle from self.ms_get_screen_hwnd
        :return: window rect (x1, y1, x2, y2) of MS rect.
        """
        hwnd = self.hwnd if hwnd is None else hwnd

        try:
            rect = win32gui.GetClientRect(hwnd)
        except Exception:
            return None
        if rect[2] == 0:  # (0, 0, width, height)
            return None
        pos = win32gui.ClientToScreen(hwnd, (0, 0))

        return pos[0], pos[1], pos[0]+rect[2], pos[1]+rect[3]  # returns x1, y1, x2, y2

    def is_foreground(self):
        return win32gui.GetForegroundWindow() == self.hwnd

    def set_foreground(self):
        win32gui.SetForegroundWindow(self.hwnd)
        time.sleep(0.1)
        if win32gui.GetForegroundWindow() != self.hwnd:
            time.sleep(0.1)
        if win32gui.GetForegroundWindow() != self.hwnd:
            return False
        return True

    def capture(self, set_focus=True, hwnd=None, rect=None):
        """Returns MapleStory window screenshot (not np.array!)
        :param set_focus : True if MapleStory window is to be focusesd before capture, False if not
        :param hwnd : Default: None Win32API screen handle to use. If None, sets and uses self.hwnd
        :param rect : If defined, captures specified ScreenRect area (x1, y1, x2, y2). Else, uses MS window rect.
        :return : returns PIL Image"""
        if hwnd:
            self.hwnd = hwnd
        if not self.hwnd:
            self.hwnd = self.ms_get_screen_hwnd()
        if not rect:
            rect = self.ms_get_screen_rect(self.hwnd)
            if rect is None:  # window not visible etc.
                return None
        if set_focus and win32gui.GetForegroundWindow() != self.hwnd:
            self.set_foreground()

        if self.d3dshot is None:
            return ImageGrab.grab(rect)
        else:
            return self.d3dshot.screenshot(rect)


class StaticImageProcessor:
    DIALOG_W = 517
    DIALOG_H = 188
    EXP_COLOR_BGR = (99, 237, 229)  # bgr

    def __init__(self, img_handle=None):
        """

        :param img_handle: handle to MapleScreenCapturer
        """
        if not img_handle:
            raise Exception("img_handle must reference an MapleScreenCapturer class!!")

        self.img_handle = img_handle
        self.bgr_img = None
        self.gray_img = None
        self.processed_img = None
        self.minimap_area = 0
        self.minimap_rect = None

        self.eboss_min_tpl = cv2.imread(os.path.dirname(__file__) + '/resources/eboss_minute_tpl.png', cv2.IMREAD_GRAYSCALE)
        self.eboss_sec_tpl = cv2.imread(os.path.dirname(__file__) + '/resources/eboss_second_tpl.png', cv2.IMREAD_GRAYSCALE)
        self.dialog_end_btn_tpl = cv2.imread(os.path.dirname(__file__) + '/resources/dialog_end_chat_button.png', cv2.IMREAD_GRAYSCALE)

        self.maximum_minimap_area = 40000

        self.default_minimap_scan_area = [0, 50, 420, 260]  # x1, y1, x2, y2

        # Minimap player marker original BGR: 68, 221, 255
        self.lower_player_marker = np.array([67, 220, 254])  # B G R
        self.upper_player_marker = np.array([69, 222, 256])
        self.lower_rune_marker = np.array([254, 101, 220])  # B G R
        self.upper_rune_marker = np.array([255, 103, 222])

        self.hwnd = self.img_handle.ms_get_screen_hwnd()

        if not self.hwnd:
            raise MapleWindowNotFoundError

    def update_image(self, src=None, set_focus=True):
        """
        Calls ScreenCapturer's update function and updates images.
        :param src : rgb image data from PIL ImageGrab
        :param set_focus : True if win32api setfocus shall be called before capturing"""
        if src:
            rgb_img = src
        else:
            rgb_img = self.img_handle.capture(set_focus, self.hwnd)

        if rgb_img is None:
            raise GameCaptureError

        self.bgr_img = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
        self.gray_img = cv2.cvtColor(self.bgr_img, cv2.COLOR_BGR2GRAY)

    def get_minimap_rect(self):
        """
        Processes self.gray images, returns minimap bounding box
        :return: Array [x,y,w,h] bounding box of minimap if found, else 0
        """
        cropped = self.gray_img[self.default_minimap_scan_area[1]:self.default_minimap_scan_area[3], self.default_minimap_scan_area[0]:self.default_minimap_scan_area[2]]
        blurred_img = cv2.GaussianBlur(cropped, (3,3), 3)
        morphed_img = cv2.erode(blurred_img, (7,7))
        canny = cv2.Canny(morphed_img, threshold1=180, threshold2=255)  # canny edge detect
        contours, hierachy = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            biggest_contour = max(contours, key=cv2.contourArea)
            if 100 <= cv2.contourArea(biggest_contour) <= self.maximum_minimap_area and cv2.contourArea(biggest_contour) >= self.minimap_area:
                minimap_coords = cv2.boundingRect(biggest_contour)
                if minimap_coords[0] > 0 and minimap_coords[1] > 0 and minimap_coords[2] > 0 and minimap_coords[2] > 0:
                    contour_area = cv2.contourArea(biggest_contour)
                    self.minimap_area = contour_area
                    minimap_coords = [minimap_coords[0], minimap_coords[1], minimap_coords[2], minimap_coords[3]]
                    minimap_coords[0] += self.default_minimap_scan_area[0]
                    minimap_coords[1] += self.default_minimap_scan_area[1]
                    self.minimap_rect = minimap_coords
                    return minimap_coords
                else:
                    pass

        return None

    def reset_minimap_area(self):
        """
        Resets self.minimap_area which is used to reset self.get_minimap_rect search.
        :return: None
        """
        self.minimap_area = 0

    def find_player_minimap_marker(self, rect=None):
        """
        Processes self.bgr_image to return player coordinate on minimap.
        The player marker has exactly 12 pixels of the detection color to form a pixel circle(2,4,4,2 pixels). Therefore
        before calculation the mean pixel value of the mask, we remove "false positives", which are not part of the
        player color by finding pixels which do not have between 10 to 12 other pixels(including itself) of the same color in a
        distance of 3.
        :param rect: [x,y,w,h] bounding box of minimap in MapleStory screen. Call self.get_minimap_rect to obtain
        :return: x,y coordinate of player relative to ms_screen_rect if found, else 0
        """
        if not rect and not self.minimap_rect:
            rect = self.get_minimap_rect()
        else:
            rect = self.minimap_rect

        assert rect, "Invalid minimap coordinates"

        cropped = self.bgr_img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]
        mask = cv2.inRange(cropped, self.lower_player_marker, self.upper_player_marker)
        td = np.transpose(np.where(mask > 0)).tolist()

        if len(td) > 0:
            avg_x = 0
            avg_y = 0
            totalpoints = 0
            for coord in td:
                nearest_points = 0  # Points which are close to coord pixel
                for ref_coord in td:
                    # Calculate the range between every single pixel
                    if math.sqrt(abs(ref_coord[0]-coord[0])**2 + abs(ref_coord[1]-coord[1])**2) <= 3:
                        nearest_points += 1

                if 10 <= nearest_points <= 13:
                    avg_y += coord[0]
                    avg_x += coord[1]
                    totalpoints += 1

            if totalpoints == 0:
                return None

            avg_y = int(avg_y / totalpoints)
            avg_x = int(avg_x / totalpoints)
            return avg_x, avg_y

        return None

    def find_other_player_marker(self, rect=None):
        """
        Processes self.bgr_image to return coordinate of other players on minimap if exists.
        Does not behave as expected when there are more than one other player on map. Use this function to just detect.
        :param rect: [x,y,w,h] bounding box of minimap. Call self.get_minimap_rect
        :return: x,y coord of marker if found, else 0
        """
        if not rect and not self.minimap_rect:
            rect = self.get_minimap_rect()
        else:
            rect = self.minimap_rect
        assert rect, "Invalid minimap coordinates"
        cropped = self.bgr_img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]

        stranger = (np.array((0, 0, 255)), np.array((0, 0, 255)))
        guild = (np.array((255, 102, 102)), np.array((255, 153, 153)))
        friend = (np.array((238, 204, 0)), np.array((255, 221, 17)))

        for i in (stranger, guild, friend):
            mask = cv2.inRange(cropped, i[0], i[1])
            td = np.transpose(np.where(mask > 0)).tolist()

            if len(td) >= 5:
                avg_x = 0
                avg_y = 0
                totalpoints = 0
                for coord in td:
                    avg_y += coord[0]
                    avg_x += coord[1]
                    totalpoints += 1
                avg_y = int(avg_y / totalpoints)
                avg_x = int(avg_x / totalpoints)
                return avg_x, avg_y

        return None

    def find_rune_marker(self, rect=None):
        """
        Processes self.bgr_image to return coordinates of rune marker on minimap.
        :param rect: [x,y,w,h] bounding box of minimap. Call self.get_minimap_rect
        :return: x,y of rune minimap coordinates if found, else 0
        """
        if not rect and not self.minimap_rect:
            rect = self.get_minimap_rect()
        else:
            rect = self.minimap_rect
        assert rect, "Invalid minimap coordinates"
        cropped = self.bgr_img[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
        mask = cv2.inRange(cropped, self.lower_rune_marker, self.upper_rune_marker)
        td = np.transpose(np.where(mask > 0)).tolist()
        if len(td) > 0:
            avg_x = 0
            avg_y = 0
            totalpoints = 0
            for coord in td:
                nearest_points = 0  # Points which are close to coord pixel
                for ref_coord in td:
                    # Calculate the range between every single pixel
                    if math.sqrt(abs(ref_coord[0] - coord[0]) ** 2 + abs(ref_coord[1] - coord[1]) ** 2) <= 6:
                        nearest_points += 1

                if nearest_points >= 20 and nearest_points <= 25:
                    avg_y += coord[0]
                    avg_x += coord[1]
                    totalpoints += 1

            if totalpoints == 0:
                return 0

            avg_y = int(avg_y / totalpoints)
            avg_x = int(avg_x / totalpoints)
            return avg_x, avg_y

        return 0

    def check_elite_boss(self):
        h, w = self.gray_img.shape
        # countdown area
        area_w = 216
        area_h = 56
        x = (w // 2) - (area_w // 2)
        y = 30
        # search smaller area only
        x += area_w // 2
        area_w //= 2
        y += area_h // 2
        area_h //= 2

        cropped = self.gray_img[y:y+area_h, x:x+area_w]
        match_res = cv2.matchTemplate(cropped, self.eboss_min_tpl, cv2.TM_SQDIFF_NORMED)
        loc = np.where(match_res < 0.03)
        if len(loc[0]) != 1:
            return False

        match_res = cv2.matchTemplate(cropped, self.eboss_sec_tpl, cv2.TM_SQDIFF_NORMED)
        loc = np.where(match_res < 0.03)
        return len(loc[0]) == 1

    def check_white_room(self):
        """Assume in white room if 70% or more pixels are pure white. Percentage of sample in unittest is 79%"""
        area = self.bgr_img.shape[0] * self.bgr_img.shape[1]
        return ((self.bgr_img == (255, 255, 255)).all(axis=-1).sum() / area) > 0.7

    def check_dialog(self):
        """Match 'End Chat' button of dialog (at left bottom)"""
        h, w = self.gray_img.shape
        x = (w // 2) - (self.DIALOG_W // 2)
        y = (h // 2) - (self.DIALOG_H // 2)
        cropped = self.gray_img[y+self.DIALOG_H-28:y+self.DIALOG_H, x:x+103]

        match_res = cv2.matchTemplate(cropped, self.dialog_end_btn_tpl, cv2.TM_SQDIFF_NORMED)
        loc = np.where(match_res < 0.015)

        return len(loc[0] == 1)

    def check_exp_full(self):
        """exp >= 90%"""
        h, w = self.gray_img.shape
        x, y = int(w*0.9), h-2

        return any(util.color_distance(self.bgr_img[y][i], self.EXP_COLOR_BGR) < 10 for i in range(x, x + 9, 3))


if __name__ == "__main__":
    dx = ScreenProcessor()
    hwnd = dx.ms_get_screen_hwnd()
    rect = dx.ms_get_screen_rect(hwnd)
    print('ms rect:', rect)
    image = dx.capture(rect=rect)
    # image.show()
    processor = StaticImageProcessor(dx)
    processor.update_image()
    print('minimap rect:', processor.get_minimap_rect())
    print('player_pos:', processor.find_player_minimap_marker())
