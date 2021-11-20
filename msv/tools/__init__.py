import logging
from multiprocessing.connection import Connection
from msv import driver
from msv.util import get_config
from msv.util import ConnLoggerHandler
from msv.input_manager import InputManager
from msv.macro_script import Aborted
from msv.screen_processor import ScreenProcessor, GameCaptureError


def tool_macro_process(conn: Connection, tool_class, args):
    try:
        config = get_config()
        tool = tool_class(ScreenProcessor(), config, conn)
        tool.run(args)
        conn.send(('stopped', None))
    except GameCaptureError:
        conn.send(('log', 'failed to capture game window'))
        conn.send(('stopped', None))
    except Aborted:
        conn.send(('stopped', None))
    except Exception as e:
        conn.send(('exception', e))

    conn.close()


class ToolBase:
    def __init__(self, screen_processor, config, conn=None):
        config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG if config.get('debug') else logging.INFO)
        if conn and not self.logger.hasHandlers():
            self.logger.addHandler(ConnLoggerHandler(logging.DEBUG, conn))

        kernel_driver = config.get('kernel_driver', False)
        if kernel_driver:
            # need to get driver handle on this new process
            driver.get_driver_handle()
        self.conn = conn
        self.screen_processor = screen_processor
        self.screen_processor.get_game_hwnd()
        self.input_mgr = InputManager(use_driver=kernel_driver)
        self.scale_ratio = None
        self.img = None
        self.ms_rect = None
        self.area_pos = (0, 0)

    def run(self, args):
        raise NotImplementedError

    def poll_conn(self):
        try:
            return self.conn and self.conn.poll()
        except EOFError:
            return True

    def _map_pos(self, pos):
        return (self.ms_rect[0] + (self.area_pos[0]+pos[0]) * self.scale_ratio,
                self.ms_rect[1] + (self.area_pos[1]+pos[1]) * self.scale_ratio)

