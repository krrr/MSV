import base64
import sys
import os
import logging
from PyQt5.QtCore import QLibraryInfo, QByteArray
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory, QWidget, QLayout, QGridLayout, QFormLayout
from msv import util, winapi
# noinspection PyUnresolvedReferences
import msv.resources_rc

QWIDGETSIZE_MAX = 16777215


def fix_sizes_for_high_dpi(widget):
    dpi_scale_ratio = widget.logicalDpiX() / 96
    if dpi_scale_ratio == 1:
        return

    _fix_sizes_for_high_dpi_internal(widget, dpi_scale_ratio)


def _fix_sizes_for_high_dpi_internal(widget, ratio):
    if isinstance(widget, QWidget):
        widget.setMinimumSize(widget.minimumSize() * ratio)
        size = widget.maximumSize()
        if size.width() < QWIDGETSIZE_MAX:
            size.setWidth(size.width() * ratio)
        if size.height() < QWIDGETSIZE_MAX:
            size.setHeight(size.height() * ratio)
        widget.setMaximumSize(size)
    elif isinstance(widget, QGridLayout) or isinstance(widget, QFormLayout):
        widget.setHorizontalSpacing(widget.horizontalSpacing() * ratio)
        widget.setVerticalSpacing(widget.verticalSpacing() * ratio)
        widget.setContentsMargins(*(i * ratio for i in widget.getContentsMargins()))
    elif isinstance(widget, QLayout):
        widget.setSpacing(widget.spacing() * ratio)
        widget.setContentsMargins(*(i * ratio for i in widget.getContentsMargins()))

    if isinstance(widget, QWidget) or isinstance(widget, QLayout):
        for i in widget.children():
            _fix_sizes_for_high_dpi_internal(i, ratio)


def set_app_icon_exe(app):
    from PyQt5.QtWinExtras import QtWin

    hico = winapi.LoadIcon(winapi.GetModuleHandle(None), 1)
    if hico != 0:
        app.setWindowIcon(QIcon(QtWin.fromHICON(hico)))
    else:
        logging.error('LoadIcon failed')


def gui_loop(args):
    is_compiled = not os.path.isfile(__file__)
    logging.debug('Qt lib path: %s', QLibraryInfo.location(QLibraryInfo.LibrariesPath))
    app = QApplication(sys.argv)
    if is_compiled:
        set_app_icon_exe(app)
    else:
        app.setWindowIcon(QIcon(":/appicon.ico"))
    app.setFont(QApplication.font('QMenu'))
    app.setStyle(QStyleFactory.create("Fusion"))

    from msv.ui.main_window import MainWindow
    main_win = MainWindow(args['title'], args['limit'])

    geo = util.get_config().get('geometry')
    if geo:
        try:
            main_win.restoreGeometry(QByteArray(base64.b64decode(geo)))
        except Exception as e:
            logging.warning('restoreGeometry failed: %s', str(e))

    if is_compiled:
        from msv.ui.login_dialog import LoginDialog
        dialog = LoginDialog()
        if args['title']:
            dialog.setWindowTitle(args['title'] + ' Login')
        dialog.accepted.connect(main_win.show)
        dialog.show()
    else:
        main_win.show()

    return app.exec_()