import cv2
import win32gui
import win32con
import time
import math
import numpy as np
import ctypes
import ctypes.wintypes
from PIL import Image
from msv import winapi
from msv.util import read_qt_resource


_bmp_info_header = None
_rect = None


def is_window_scaled(hwnd):
    if hasattr(winapi, 'GetAwarenessFromDpiAwarenessContext'):  # win10 1607+
        return winapi.GetAwarenessFromDpiAwarenessContext(winapi.GetWindowDpiAwarenessContext(hwnd)) == winapi.DPI_AWARENESS_UNAWARE
    else:
        return False


def gdi_capture(hwnd, force_scaled=None, rect=None):
    """
    Use Windows GDI API to capture singe window.
    :return: BGR numpy array
    """
    global _rect, _bmp_info_header
    if not hwnd:
        raise ValueError('invalid hwnd')

    game_hdc = winapi.GetDC(hwnd)  # client area only, not GetWindowDC
    if not game_hdc:
        raise GameCaptureError("can't get DC of game window")

    if rect is None:
        # get window client size
        if _rect is None:
            _rect = ctypes.wintypes.RECT()
        if not winapi.GetClientRect(hwnd, ctypes.byref(_rect)):
            raise GameCaptureError("can't get rect of game window")
        x = y = 0
        width = _rect.right - _rect.left
        height = _rect.bottom - _rect.top
        # fix window size if scaled
        is_scaled = is_window_scaled(hwnd) if force_scaled is None else force_scaled
        if is_scaled:
            screen_dpi = winapi.GetDeviceCaps(game_hdc, winapi.LOGPIXELSX)
            if screen_dpi != 96:
                width = round(width * 96 / screen_dpi)
                height = round(height * 96 / screen_dpi)
    else:
        x, y, width, height = rect

    if _bmp_info_header is None:
        _bmp_info_header = winapi.BITMAPINFOHEADER()
        _bmp_info_header.biSize = 40  # ctypes.sizeof(hdr)
        _bmp_info_header.biPlanes = 1
        _bmp_info_header.biBitCount = 32
        _bmp_info_header.biCompression = winapi.BI_RGB
        _bmp_info_header.biClrUsed = 0
        _bmp_info_header.biYPelsPerMeter = 0
        _bmp_info_header.biClrImportant = 0
    _bmp_info_header.biWidth = width
    _bmp_info_header.biHeight = -height
    _bmp_info_header.biSizeImage = width * height * 4

    hbitmap = cdc = None
    try:
        bitmap_ptr = ctypes.c_void_p()
        hbitmap = winapi.CreateDIBSection(game_hdc, ctypes.byref(_bmp_info_header), winapi.DIB_RGB_COLORS, ctypes.byref(bitmap_ptr), None, 0)
        if not hbitmap:
            raise GameCaptureError('CreateDIBSection error')
        cdc = winapi.CreateCompatibleDC(game_hdc)
        if not cdc or not winapi.SelectObject(cdc, hbitmap):  # selects bitmap into cdc
            raise GameCaptureError()
        if not winapi.BitBlt(cdc, 0, 0, width, height, game_hdc, x, y, winapi.SRCCOPY):  # copy game_dc to cdc
            raise GameCaptureError('BitBlt error')
        bitmap_ptr = ctypes.cast(bitmap_ptr, ctypes.POINTER(ctypes.c_uint8))
        # highest byte of DWORD is not used... but can't set biBitCount to 24 instead of 32, because of stride
        # (https://stackoverflow.com/a/3688558/3737373)
        arr = np.ctypeslib.as_array(bitmap_ptr, (height, width, 4))
        return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
    finally:
        if cdc:
            winapi.DeleteDC(cdc)
        if game_hdc:
            winapi.ReleaseDC(0, game_hdc)
        if hbitmap:
            winapi.DeleteObject(hbitmap)


def read_alpha_as_mask(path):
    image_4channel = cv2.imdecode(read_qt_resource(path, True), cv2.IMREAD_UNCHANGED)
    alpha_channel = image_4channel[:,:,3]
    return alpha_channel


class GameCaptureError(Exception):
    pass


class MapleWindowNotFoundError(GameCaptureError):
    pass


class MiniMapError(Exception):
    pass


class ScreenProcessor:
    """
    Container for capturing MS screen
    Capture methods speed comparison @ 4K resolution:
     - GDI all screen to PIL.Image (PIL ImageGrab): 15FPS
     - D3DShot to numpy array: 91FPS
     - GDI single window to numpy array: 310FPS  (will double if D3DShot initialized)
    """
    def __init__(self):
        self.hwnd = None
        self.is_window_scaled = None
        if not winapi.IsProcessDPIAware():
            winapi.SetProcessDPIAware()

    def get_game_hwnd(self):
        self.hwnd = win32gui.FindWindowEx(0, 0, "MapleStoryClass", None)
        if self.hwnd:
            self.hwnd = win32gui.GetWindow(self.hwnd, win32con.GW_OWNER) or self.hwnd  # if hwnd is external chat window
        self.is_window_scaled = is_window_scaled(self.hwnd) if self.hwnd else None
        return self.hwnd

    def ms_get_screen_rect(self):
        """
        Get client rect of game window
        :return: window rect (x1, y1, x2, y2) of MS rect.
        """
        try:
            rect = win32gui.GetClientRect(self.hwnd)
        except Exception:
            return None
        if rect[2] == 0:  # (0, 0, width, height)
            return None
        pos = win32gui.ClientToScreen(self.hwnd, (0, 0))

        return pos[0], pos[1], pos[0]+rect[2], pos[1]+rect[3]  # returns x1, y1, x2, y2

    def get_scale_ratio(self):
        if not self.is_window_scaled:
            return 1

        game_hdc = winapi.GetDC(self.hwnd)
        if not game_hdc:
            return None
        screen_dpi = winapi.GetDeviceCaps(game_hdc, winapi.LOGPIXELSX)
        return screen_dpi / 96

    def is_foreground(self):
        return win32gui.GetForegroundWindow() == self.hwnd

    def set_foreground(self):
        try:
            win32gui.SetForegroundWindow(self.hwnd)
        except Exception:
            return False

        time.sleep(0.1)
        if win32gui.GetForegroundWindow() != self.hwnd:
            time.sleep(0.1)
        if win32gui.GetForegroundWindow() != self.hwnd:
            return False
        return True

    def capture(self, hwnd=None, rect=None):
        """Capture game window content
        :param hwnd : Default: None win32 window handle. If None, sets and uses self.hwnd
        :return : numpy BGR Image"""
        if hwnd:
            self.hwnd = hwnd
        if not self.hwnd:
            self.hwnd = self.get_game_hwnd()

        return gdi_capture(self.hwnd, self.is_window_scaled, rect)

    def capture_pil(self, rect=None):
        img = self.capture(rect=rect)
        return None if img is None else Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


class StaticImageProcessor:
    DIALOG_W = 517
    DIALOG_H = 188
    EXP_COLOR_BGR = (0, 250, 243)  # bottom of exp bar

    def __init__(self, img_handle=None):
        """

        :param img_handle: handle to MapleScreenCapturer
        """
        if not img_handle:
            raise Exception("img_handle must reference an MapleScreenCapturer class!!")

        self.img_handle = img_handle
        self.detect_friend = True
        self.bgr_img = None
        self._gray_img = None
        self.minimap_area = 0
        self.minimap_rect = None

        self.cv_templates = {}
        for i in ('gm_cap', 'dialog_end_chat', 'hp0'):
            path = ':/template/' + i + '_tpl.png'
            self.cv_templates[i] = cv2.imdecode(read_qt_resource(path, True), cv2.IMREAD_GRAYSCALE)
            if self.cv_templates[i] is None:
                raise FileNotFoundError(path)
        self.cv_templates['gm_cap_r'] = np.fliplr(self.cv_templates['gm_cap'])
        self.cv_templates['gm_cap_mask'] = read_alpha_as_mask(':/template/gm_cap_tpl.png')
        self.cv_templates['gm_cap_r_mask'] = np.fliplr(self.cv_templates['gm_cap_mask'])

        self.maximum_minimap_area = 40000

        self.default_minimap_scan_area = [0, 50, 420, 260]  # x1, y1, x2, y2

        # Minimap player marker original BGR: 68, 221, 255
        self.lower_player_marker = np.array([67, 220, 254])  # B G R
        self.upper_player_marker = np.array([69, 222, 256])
        self.lower_rune_marker = np.array([254, 101, 220])  # B G R
        self.upper_rune_marker = np.array([255, 103, 222])

        self.img_handle.get_game_hwnd()
        if not self.img_handle.hwnd:
            raise MapleWindowNotFoundError

    @property
    def gray_img(self):
        if self._gray_img is not None:
            return self._gray_img
        elif self.bgr_img is not None:
            self._gray_img = cv2.cvtColor(self.bgr_img, cv2.COLOR_BGR2GRAY)
            return self._gray_img
        else:
            return None

    def update_image(self, src=None, set_focus=True):
        """
        Calls ScreenCapturer's update function and updates images.
        :param src : rgb image data from PIL ImageGrab
        :param set_focus : True if win32api setfocus shall be called before capturing"""
        if set_focus and not self.img_handle.is_foreground():
            self.img_handle.set_foreground()

        if src:
            bgr_img = cv2.cvtColor(np.array(src), cv2.COLOR_RGB2BGR)
        else:
            bgr_img = self.img_handle.capture()

        if bgr_img is None:
            raise GameCaptureError('failed to capture game window')

        self.bgr_img = bgr_img
        self._gray_img = None

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

        if not rect:
            raise MiniMapError('Invalid minimap coordinates')

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

        if not rect:
            raise MiniMapError('Invalid minimap coordinates')

        cropped = self.bgr_img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]

        stranger = (np.array((0, 0, 255)), np.array((0, 0, 255)))
        guild = (np.array((255, 102, 102)), np.array((255, 153, 153)))
        friend = (np.array((238, 204, 0)), np.array((255, 221, 17)))

        for i in (stranger, guild, friend) if self.detect_friend else (stranger, guild):
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

        if not rect:
            raise MiniMapError('Invalid minimap coordinates')

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

                if 20 <= nearest_points <= 25:
                    avg_y += coord[0]
                    avg_x += coord[1]
                    totalpoints += 1

            if totalpoints == 0:
                return 0

            avg_y = int(avg_y / totalpoints)
            avg_x = int(avg_x / totalpoints)
            return avg_x, avg_y

        return 0

    def check_death(self):
        h, w = self.gray_img.shape
        # countdown area
        area_w = 174
        area_h = 17
        x = (w // 2) - (area_w // 2) + 12
        y = h - 54

        cropped = self.gray_img[y:y+area_h, x:x+area_w]
        match_res = cv2.matchTemplate(cropped, self.cv_templates['hp0'], cv2.TM_SQDIFF_NORMED)
        loc = np.where(match_res < 0.06)
        return len(loc[0]) == 1

    def check_monster(self, name, crop_dir=None):
        tpl = self.cv_templates.get(name)
        if tpl is None:  # lazy load
            path = ':/template/monster/' + name + '_tpl.png'
            tpl = self.cv_templates[name] = cv2.imdecode(read_qt_resource(path, True), cv2.IMREAD_GRAYSCALE)
            if tpl is None:
                raise FileNotFoundError(path)
            tpl_mask = self.cv_templates[name + '_mask'] = read_alpha_as_mask(path)
            tpl_r = self.cv_templates[name + '_r'] = np.fliplr(tpl)
            tpl_r_mask = self.cv_templates[name + '_r_mask'] = np.fliplr(tpl_mask)
        else:
            tpl_mask = self.cv_templates[name + '_mask']
            tpl_r = self.cv_templates[name + '_r']
            tpl_r_mask = self.cv_templates[name + '_r_mask']

        img_h, img_w = self.gray_img.shape[:2]
        img = self.gray_img
        if crop_dir == 'l':
            img = img[50:img_h-100, 0:img_w//2]
        elif crop_dir == 'r':
            img = img[50:img_h-100, img_w//2:img_w]

        res = cv2.matchTemplate(img, tpl, cv2.TM_SQDIFF_NORMED, mask=tpl_mask)
        if len(np.where(res <= 0.04)[0]) > 0:
            return True
        res = cv2.matchTemplate(img, tpl_r, cv2.TM_SQDIFF_NORMED, mask=tpl_r_mask)
        return len(np.where(res <= 0.04)[0]) > 0

    def check_white_room(self):
        """Assume in white room if 40% or more pixels are pure white. Percentage of sample in unittest is 79%"""
        area = self.bgr_img.shape[0] * self.bgr_img.shape[1]
        return ((self.bgr_img == (255, 255, 255)).all(axis=-1).sum() / area) > 0.4

    def check_gm_cap(self):
        """Check Game Master's white cap with letter 'W'"""
        for i in ('gm_cap', 'gm_cap_r'):
            match_res = cv2.matchTemplate(self.gray_img, self.cv_templates[i], cv2.TM_SQDIFF_NORMED, mask=self.cv_templates[i+'_mask'])
            loc = np.where(match_res < 0.001)
            if len(loc[0]) == 1:
                return True
        return False

    def check_dialog(self):
        """Match 'End Chat' button of dialog (at left bottom)"""
        h, w = self.gray_img.shape
        x = (w // 2) - (self.DIALOG_W // 2)
        y = (h // 2) - (self.DIALOG_H // 2)
        cropped = self.gray_img[y+self.DIALOG_H-28:y+self.DIALOG_H, x:x+103]

        match_res = cv2.matchTemplate(cropped, self.cv_templates['dialog_end_chat'], cv2.TM_SQDIFF_NORMED)
        loc = np.where(match_res < 0.015)

        return len(loc[0] == 1)


class MockScreenProcessor(ScreenProcessor):
    """For unit test"""
    def __init__(self):
        super().__init__()
        self.hwnd = 1
        self.img = None

    def get_game_hwnd(self):
        return self.hwnd

    def set_test_img(self, path):
        self.img = cv2.imread(path)

    def set_foreground(self):
        pass

    def ms_get_screen_rect(self, _=None):
        return (0, 0, 500, 500)

    def capture(self, hwnd=None, rect=None):
        return self.img


class MockStaticImageProcessor(StaticImageProcessor):
    """For unit test"""
    def __init__(self):
        super().__init__(MockScreenProcessor())

    def set_test_img(self, path):
        self.img_handle.set_test_img(path)
        self.update_image()


if __name__ == "__main__":
    dx = ScreenProcessor()
    dx.get_game_hwnd()
    rect = dx.ms_get_screen_rect()
    print('ms rect:', rect)
    image = dx.capture_pil()
    # image.show()
    processor = StaticImageProcessor(dx)
    processor.update_image()
    print('minimap rect:', processor.get_minimap_rect())
    print('player_pos:', processor.find_player_minimap_marker())
