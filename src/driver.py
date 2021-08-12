import win32service
import win32con
import win32file
import winioctlcon
import pywintypes
import struct
import os


DRIVER_NAME = 'MsvDriver'
DRIVER_DISPLAY_NAME = 'MSV Driver'
DRIVER_REL_PATH = '../driver/MSVDriver.sys'
SEND_INPUT_CODE = winioctlcon.CTL_CODE(winioctlcon.FILE_DEVICE_UNKNOWN, 0x801, winioctlcon.METHOD_BUFFERED, winioctlcon.FILE_ANY_ACCESS)


_driver_handle = None


def load_driver():
    sc_manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
    while True:
        try:
            srv = win32service.OpenService(sc_manager, DRIVER_NAME, win32service.SERVICE_ALL_ACCESS)
            break
        except pywintypes.error as e:
            if e.args[0] == 1060:  # service not installed
                install_driver(sc_manager)

    try:
        win32service.StartService(srv, [])
    except pywintypes.error as e:
        if e.args[0] != 1056:  # already running
            raise e

    win32service.CloseServiceHandle(srv)
    win32service.CloseServiceHandle(sc_manager)
    get_driver_handle()


def get_driver_handle():
    global _driver_handle
    _driver_handle = win32file.CreateFile(r"\\.\msvdriver",
                                          win32con.GENERIC_WRITE | win32con.GENERIC_READ,
                                          0, None, win32file.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_DEVICE, 0)


def unload_driver(delete=False):
    global _driver_handle

    if _driver_handle:
        win32file.CloseHandle(_driver_handle)
        _driver_handle = None

    sc_manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
    srv = win32service.OpenService(sc_manager, DRIVER_NAME, win32service.SERVICE_ALL_ACCESS)
    win32service.ControlService(srv, win32service.SERVICE_CONTROL_STOP)
    if delete:
        win32service.DeleteService(srv)
    win32service.CloseServiceHandle(srv)
    win32service.CloseServiceHandle(sc_manager)


def install_driver(sc_manager):
    win32service.CreateService(sc_manager, DRIVER_NAME, DRIVER_DISPLAY_NAME, win32service.SERVICE_ALL_ACCESS,
                               win32service.SERVICE_KERNEL_DRIVER, win32service.SERVICE_DEMAND_START,
                               win32service.SERVICE_ERROR_IGNORE, os.path.realpath(DRIVER_REL_PATH),
                               None, False, None, None, None)


def send_input(input_count, inputs, input_bytes):
    args = struct.pack('<IIQ', input_count, input_bytes, inputs)
    ret = win32file.DeviceIoControl(_driver_handle, SEND_INPUT_CODE, args, 4)  # return type is UINT32, 4 bytes
    return struct.unpack('<I', ret)  # returns send count


if __name__ == "__main__":
    load_driver()
    print(_driver_handle)
    unload_driver()

