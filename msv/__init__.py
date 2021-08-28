# Copyright (C) 2021 krrr <guogaishiwo@gmail.com>


APP_TITLE = 'MSV'
__version__ = '0.5'


def main_entry():
    import tkinter as tk, argparse
    from msv.main_window import MainWindow
    from msv import util, winapi

    winapi.SetProcessDPIAware()

    parser = argparse.ArgumentParser(description="MSV-Kanna-Ver, a macro to farm MapleStory")
    parser.add_argument("-t", dest="title", help="change main window title to designated value")
    parser.add_argument("-c", dest="config", help="specify config file path")
    args = vars(parser.parse_args())

    if args['config']:
        util.config_file = args['config']

    root = tk.Tk()

    root.title(args["title"] if args["title"] else APP_TITLE)
    try:
        root.iconbitmap(util.resource_path + 'appicon.ico')
    except tk.TclError:
        pass
    root.wm_minsize(400, 600)

    MainWindow(root)

    geo = util.get_config().get('geometry')
    if geo:
        root.geometry(geo)
    root.mainloop()

    return 0
