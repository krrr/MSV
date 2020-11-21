import ctypes
import win32api, win32con, win32gui
from PIL import Image, ImageWin


class FakeGameWindow:
    def __init__(self):
        ctypes.windll.user32.SetProcessDPIAware()
        win32gui.InitCommonControls()
        self.hinst = win32api.GetModuleHandle(None)
        className = 'MapleStoryClass'
        message_map = {
            win32con.WM_DESTROY: self.OnDestroy,
            win32con.WM_PAINT: self.OnPaint,
        }
        wc = win32gui.WNDCLASS()
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wc.lpfnWndProc = message_map
        wc.lpszClassName = className
        win32gui.RegisterClass(wc)
        style = (win32con.WS_OVERLAPPED | win32con.WS_CAPTION | win32con.WS_SYSMENU | win32con.WS_MINIMIZEBOX)
        self.hwnd = win32gui.CreateWindow(
            className,
            'MapleStory',
            style,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            500,
            500,
            0,
            0,
            self.hinst,
            None
        )
        rect = win32gui.GetClientRect(self.hwnd)
        win32gui.SetWindowPos(self.hwnd, 0, 5, 5, 1366+500-rect[2], 768+500-rect[3], 0)
        win32gui.UpdateWindow(self.hwnd)
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
        self.im = Image.open('..\\unittest_data\\eboss_sample1.png')

    def OnPaint(self, hwnd, message, wparam, lparam):
        hdc, ps = win32gui.BeginPaint(hwnd)

        dib = ImageWin.Dib(self.im)
        dib.expose(hdc)

        win32gui.EndPaint(hwnd, ps)

    def OnDestroy(self, hwnd, message, wparam, lparam):
        win32gui.PostQuitMessage(0)
        return True


w = FakeGameWindow()
win32gui.PumpMessages()