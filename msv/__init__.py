# Copyright (C) 2021 krrr <guogaishiwo@gmail.com>


APP_TITLE = 'MSV'
__version__ = '210930'


def main_entry():
    import argparse
    from msv import util, winapi
    from msv.ui import gui_loop

    winapi.SetProcessDPIAware()

    parser = argparse.ArgumentParser(description="MSV-Kanna-Ver, a macro to farm MapleStory")
    parser.add_argument("-t", dest="title", help="change application title")
    parser.add_argument("-c", dest="config", help="specify config file path")
    parser.add_argument("-l", dest="limit", help="limited", action='store_true')
    args = vars(parser.parse_args())

    if args['config']:
        util.config_file = args['config']

    return gui_loop(args)