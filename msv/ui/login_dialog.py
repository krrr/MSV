import os
import hashlib
import json
from datetime import datetime
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from msv.ui import fix_sizes_for_high_dpi
from msv.ui.progress_indicator import ProgressIndicator
from msv.ui.login_dialog_ui import Ui_LoginDialog
from msv.vendor import wmi
from msv import util


class LoginDialog(QDialog, Ui_LoginDialog):
    URL = 'https://msv.hazama.cc/api'
    URL_BACKUP = 'https://lisa.hazama.cc/api'

    def __init__(self):
        super().__init__(None)
        self.retryCount = 0
        self.setupUi(self)
        fix_sizes_for_high_dpi(self)
        self.progressBg = self.progress = None
        self.icoLabel.setPixmap(self.icoLabel.pixmap().scaled(
            self.icoLabel.width(), self.icoLabel.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.usernameEdit.setText(util.get_config().get('username', ''))
        self.passwordEdit.setText(util.get_config().get('password', ''))

        self.netMgr = QNetworkAccessManager(self)
        self.netMgr.setTransferTimeout(7000)

        if util.get_config().get('auto_login', False):
            self.on_loginBtn_clicked()

    def accept(self):
        util.get_config()['username'] = self.usernameEdit.text()
        util.get_config()['password'] = self.passwordEdit.text()
        util.get_config()['auto_login'] = True
        super().accept()

    def showProgress(self):
        self.progressBg = QFrame(self)
        self.progressBg.setStyleSheet('background: rgba(255, 255, 255, .7)')
        hbox = QHBoxLayout(self.progressBg)
        hbox.setAlignment(Qt.AlignHCenter)
        self.progressBg.setLayout(hbox)
        self.progress = ProgressIndicator(self.progressBg)
        self.progress.setFixedSize(40, 40)
        self.progress.startAnimation()
        hbox.addWidget(self.progress)
        fix_sizes_for_high_dpi(self.progressBg)
        self.progressBg.setFixedSize(self.size())

    def hideProgress(self):
        if self.progressBg:
            self.progress.stopAnimation()
            self.progressBg.hide()
            self.progressBg.deleteLater()
            self.progress = self.progressBg = None

    @pyqtSlot()
    def on_loginBtn_clicked(self):
        if not self.usernameEdit.text() or not self.passwordEdit.text():
            QMessageBox.critical(self, 'Error', 'empty field')
            return
        self.showProgress()
        self.usernameEdit.setEnabled(False)
        self.passwordEdit.setEnabled(False)
        self.loginBtn.setEnabled(False)
        self.setCursor(Qt.WaitCursor)

        request = QNetworkRequest(QUrl((self.URL_BACKUP if self.retryCount > 0 else self.URL) + '/login'))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")

        r = WmiInfoReader()
        data = {'username': self.usernameEdit.text(), 'password': self.passwordEdit.text(),
                'device_id': r.generate_device_id(), 'computer_name': r.get_computer_name()}
        reply = self.netMgr.post(request, QByteArray(json.dumps(data).encode('utf-8')))
        reply.finished.connect(self.onLoginReqFinished)

    @pyqtSlot()
    def onLoginReqFinished(self):
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            resp = json.loads(bytes(reply.readAll()))
            if resp['status'] == 0:
                util.runtime_info['username'] = self.usernameEdit.text()
                due = resp['data'].get('due')
                util.runtime_info['due'] = datetime.fromisoformat(due) if due else None
                self.accept()
            else:
                util.get_config()['auto_login'] = False
                QMessageBox.information(self, 'Login Failed', resp['msg'] or 'Unknown error')
        elif reply.error() == QNetworkReply.OperationCanceledError:
            self.retryCount += 1
            if self.retryCount >= 2:
                QMessageBox.critical(self, 'Login Failed', 'Server timeout, please try again later')
            else:
                self.on_loginBtn_clicked()
                return
        else:
            QMessageBox.critical(self, 'Login Failed', 'Server error: ' + reply.errorString())

        reply.deleteLater()

        self.usernameEdit.setEnabled(True)
        self.passwordEdit.setEnabled(True)
        self.loginBtn.setEnabled(True)
        self.setCursor(Qt.ArrowCursor)
        self.hideProgress()


class WmiInfoReader:
    """
    Use WMI to read system information
    wmi module doc: http://timgolden.me.uk/python/wmi/cookbook.html
    """
    def __init__(self):
        self._conn = wmi.WMI()

    def get_computer_name(self):
        return self._conn.Win32_ComputerSystem(('Name',))[0].Name

    def get_mother_board_info(self):
        # https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-baseboard
        info = self._conn.Win32_BaseBoard(('SerialNumber', 'Product', 'Manufacturer'))[0]
        return {'model': info.Product, 'serial': info.SerialNumber, 'manufacturer': info.Manufacturer}

    def get_sys_disk_info(self):
        sys_letter = os.environ['SystemDrive']
        sys_part_id = self._conn.query('ASSOCIATORS OF {Win32_LogicalDisk.DeviceID="%s"} WHERE AssocClass = Win32_LogicalDiskToPartition' % sys_letter)[0].DeviceID
        sys_disk = self._conn.query('ASSOCIATORS OF {Win32_DiskPartition.DeviceID="%s"} WHERE AssocClass = Win32_DiskDriveToDiskPartition' % sys_part_id)[0]

        return {'model': sys_disk.Model, 'serial': sys_disk.SerialNumber}

    def generate_device_id(self):
        dic = {}
        try:
            dic['sys_disk'] = self.get_sys_disk_info()
        except Exception as e:
            raise Exception('failed to get disk info %s' + str(e))
        try:
            dic['motherboard'] = self.get_mother_board_info()
        except Exception as e:
            raise Exception('failed to get motherboard info %s' + str(e))

        return hashlib.sha1(json.dumps(dic, sort_keys=True).encode('utf-8')).hexdigest()


# 1）磁盘序列号。
# 2）网卡的mac地址。
# 4）Nvidia Gpu UUID。
# 5）相邻设备（例如路由器）的MAC。
# 6）注册表项
# 7）文件系统UUID（例如卷guid和diskid）
# 8）EFI uuid。
# 9）监控序列
# 10）缓存的USB 序列。
# 11）等等
# 12）文件时间
# 13）具有HWID的文件
# 14）系统卷影副本。
# 15）UPnP / SSDP USN。
# 16）启动GUID / bcdedit UUID。
# 17）USN日志ID

