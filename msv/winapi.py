import ctypes.wintypes

BI_RGB = 0
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020
LOGPIXELSX = 88
LOGPIXELSY = 90
DPI_AWARENESS_UNAWARE = 0

IsProcessDPIAware = ctypes.windll.user32.IsProcessDPIAware
IsProcessDPIAware.restype = ctypes.wintypes.BOOL

SetProcessDPIAware = ctypes.windll.user32.SetProcessDPIAware
SetProcessDPIAware.restype = ctypes.wintypes.BOOL

GetClientRect = ctypes.windll.user32.GetClientRect
GetClientRect.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.PRECT]
GetClientRect.restype = ctypes.wintypes.BOOL

BitBlt = ctypes.windll.gdi32.BitBlt
BitBlt.argtypes = [ctypes.wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.wintypes.HDC,
                   ctypes.c_int, ctypes.c_int, ctypes.wintypes.DWORD]
BitBlt.restype = ctypes.wintypes.BOOL

CreateCompatibleDC = ctypes.windll.gdi32.CreateCompatibleDC
CreateCompatibleDC.argtypes = [ctypes.wintypes.HDC]
CreateCompatibleDC.restype = ctypes.wintypes.BOOL

DeleteDC = ctypes.windll.gdi32.DeleteDC
DeleteDC.argtypes = [ctypes.wintypes.HDC]

GetDC = ctypes.windll.user32.GetDC
GetDC.argtypes = [ctypes.wintypes.HWND]
GetDC.restype = ctypes.wintypes.HDC

ReleaseDC = ctypes.windll.user32.ReleaseDC
ReleaseDC.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HDC]

SelectObject = ctypes.windll.gdi32.SelectObject
SelectObject.argtypes = [ctypes.wintypes.HDC, ctypes.wintypes.HGDIOBJ]
SelectObject.restype = ctypes.wintypes.HGDIOBJ

DeleteObject = ctypes.windll.gdi32.DeleteObject
DeleteObject.argtypes = [ctypes.wintypes.HGDIOBJ]

CreateDIBSection = ctypes.windll.gdi32.CreateDIBSection
CreateDIBSection.argtypes = [ctypes.wintypes.HDC, ctypes.c_void_p,
                             ctypes.c_uint,
                             ctypes.POINTER(ctypes.c_void_p),
                             ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD]
CreateDIBSection.restype = ctypes.wintypes.HBITMAP

GetDeviceCaps = ctypes.windll.gdi32.GetDeviceCaps
GetDeviceCaps.argtypes = [ctypes.wintypes.HGDIOBJ, ctypes.c_int]

try:
    GetDpiForSystem = ctypes.windll.user32.GetDpiForSystem
    GetDpiForSystem.restype = ctypes.wintypes.UINT
except AttributeError:
    pass

try:
    GetWindowDpiAwarenessContext = ctypes.windll.user32.GetWindowDpiAwarenessContext
    GetWindowDpiAwarenessContext.argtypes = [ctypes.wintypes.HWND]
except AttributeError:
    pass

try:
    GetAwarenessFromDpiAwarenessContext = ctypes.windll.user32.GetAwarenessFromDpiAwarenessContext
except AttributeError:
    pass


class BITMAPINFOHEADER(ctypes.Structure):
    _pack_ = 2
    _fields_ = [
        ('biSize', ctypes.wintypes.DWORD),
        ('biWidth', ctypes.wintypes.LONG),
        ('biHeight', ctypes.wintypes.LONG),
        ('biPlanes', ctypes.wintypes.WORD),
        ('biBitCount', ctypes.wintypes.WORD),
        ('biCompression', ctypes.wintypes.DWORD),
        ('biSizeImage', ctypes.wintypes.DWORD),
        ('biXPelsPerMeter', ctypes.wintypes.LONG),
        ('biYPelsPerMeter', ctypes.wintypes.LONG),
        ('biClrUsed', ctypes.wintypes.DWORD),
        ('biClrImportant', ctypes.wintypes.DWORD),
    ]