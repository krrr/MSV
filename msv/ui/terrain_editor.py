import threading
import os
import time
import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from msv.ui import fix_sizes_for_high_dpi
from msv.screen_processor import StaticImageProcessor, ScreenProcessor, GameCaptureError
from msv.terrain_analyzer import PathAnalyzer


class PlatformList(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.del_act = QAction("Delete selected item", self)
        self.toggle_n_act = QAction("Toggle selected no monster", self)

    def contextMenuEvent(self, event):
        if len(self.selectedIndexes()):
            menu = QMenu()
            menu.addAction(self.toggle_n_act)
            # menu.addSeparator()
            menu.addAction(self.del_act)
            menu.exec_(event.globalPos())


class TerrainEditorWindow(QWidget):
    set_skill_color = {'paotai': (107, 50, 135), 'paochuan': (196, 0, 0),
                       'nightmare_invite': (226, 142, 185)}

    def __init__(self, parent=None, open_file_path=None):
        super().__init__(parent, Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setMinimumSize(250, 400)
        self.setWindowTitle("Terrain Editor")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self.last_coord_x = None
        self.last_coord_y = None
        self.current_coords = []
        self.other_attrs = {}

        # image label
        self.screen_capturer = ScreenProcessor()
        self.image_processor = StaticImageProcessor(self.screen_capturer)
        self.terrain_analyzer = PathAnalyzer()
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(40)
        self.image_label.setStyleSheet('color: red')
        main_layout.addWidget(self.image_label)

        # master tool frame
        self.master_tool_frame = QFrame(self)
        self.master_tool_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.master_tool_frame.setLineWidth(2)
        master_tool_frame_layout = QVBoxLayout(self.master_tool_frame)
        master_tool_frame_layout.setContentsMargins(4, 4, 4, 4)
        master_tool_frame_layout.setSpacing(4)
        self.master_tool_frame.setLayout(master_tool_frame_layout)
        main_layout.addWidget(self.master_tool_frame)

        tool_frame_1 = QWidget(self.master_tool_frame)
        master_tool_frame_layout.addWidget(tool_frame_1)
        tool_frame_1_layout = QHBoxLayout(tool_frame_1)
        tool_frame_1_layout.setContentsMargins(0, 0, 0, 0)
        tool_frame_1_layout.setSpacing(4)
        self.coord_label = QLabel(tool_frame_1)
        tool_frame_1_layout.addWidget(self.coord_label)
        btn = QPushButton(tool_frame_1)
        btn.setText('Relocate minimap')
        btn.clicked.connect(self.find_minimap_coords)
        tool_frame_1_layout.addWidget(btn)

        # set skill buttons
        tool_frame_2 = QFrame(self.master_tool_frame)
        tool_frame_2_layout = QHBoxLayout(tool_frame_2)
        tool_frame_2_layout.setContentsMargins(0, 0, 0, 0)
        tool_frame_2_layout.setAlignment(Qt.AlignCenter)
        tool_frame_2_layout.setSpacing(4)
        tool_frame_2.setLayout(tool_frame_2_layout)
        master_tool_frame_layout.addWidget(tool_frame_2)
        ico_w = 24 * self.logicalDpiX() // 96
        ico_sz = QSize(ico_w, ico_w)
        set_paochuan_coord_1_btn = QPushButton(tool_frame_2)
        set_paochuan_coord_1_btn.setToolTip('Toggle paochuan 1')
        set_paochuan_coord_1_btn.clicked.connect(lambda: self._set_place_skill_coord('paochuan', 'paochuan_dir', 1))
        set_paochuan_coord_1_btn.setIcon(QIcon(QPixmap(':/skill_icon/paochuan.png')))
        set_paochuan_coord_2_btn = QPushButton(tool_frame_2)
        set_paochuan_coord_2_btn.setToolTip('Toggle paochuan 2')
        set_paochuan_coord_2_btn.clicked.connect(lambda: self._set_place_skill_coord('paochuan', 'paochuan_dir', 2))
        set_paochuan_coord_2_btn.setIcon(QIcon(QPixmap.fromImage(QImage(':/skill_icon/paochuan.png').mirrored(True, False))))
        set_kishin_coord_btn = QPushButton(tool_frame_2)
        set_kishin_coord_btn.setToolTip('Toggle paotai position')
        set_kishin_coord_btn.clicked.connect(lambda: self._set_place_skill_coord('paotai'))
        set_kishin_coord_btn.setIcon(QIcon(QPixmap(':/skill_icon/paotai.png')))
        set_nightmare_invite_btn = QPushButton(tool_frame_2)
        set_nightmare_invite_btn.setToolTip('Toggle Erda Shower position')
        set_nightmare_invite_btn.clicked.connect(lambda: self._set_place_skill_coord('nightmare_invite'))
        set_nightmare_invite_btn.setIcon(QIcon(QPixmap(':/skill_icon/nightmare_invite.png')))
        for i in (set_paochuan_coord_1_btn, set_paochuan_coord_2_btn, set_kishin_coord_btn, set_nightmare_invite_btn):
            i.setIconSize(ico_sz)
            i.setFixedSize(24, 24)
            tool_frame_2_layout.addWidget(i)

        # toggle record button
        self.toggle_record_btn = QPushButton(self.master_tool_frame)
        self.toggle_record_btn.setText('Start record platform')
        self.toggle_record_btn.clicked.connect(self.toggle_record)
        master_tool_frame_layout.addWidget(self.toggle_record_btn)

        # save and reset button
        tool_frame_5 = QFrame(self.master_tool_frame)
        tool_frame_5_layout = QHBoxLayout(tool_frame_5)
        tool_frame_5_layout.setContentsMargins(0, 0, 0, 0)
        tool_frame_5_layout.setSpacing(4)
        tool_frame_5.setLayout(tool_frame_5_layout)
        master_tool_frame_layout.addWidget(tool_frame_5)
        self.save_btn = QPushButton(tool_frame_5)
        self.save_btn.setText('Save')
        self.save_btn.clicked.connect(self.on_save)
        tool_frame_5_layout.addWidget(self.save_btn)
        self.reset_btn = QPushButton(tool_frame_5)
        self.reset_btn.setText('Reset')
        self.reset_btn.clicked.connect(self.on_reset_platforms)
        tool_frame_5_layout.addWidget(self.reset_btn)

        self.platform_list = PlatformList(self)
        self.platform_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.platform_list.toggle_n_act.triggered.connect(self._on_toggle_no_monster)
        self.platform_list.del_act.triggered.connect(self.on_listbox_delete)
        main_layout.addWidget(self.platform_list)

        fix_sizes_for_high_dpi(self)

        self.minimap_rect = None
        self.record_mode = 0  # 0 if not recording, 1 if normal platform

        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.update_image)
        self.thread.start()

        if open_file_path:
            self.load_platform_file(open_file_path)

    def _set_place_skill_coord(self, skill_name, extra_attr=None, extra_attr_value=None):
        old = self.other_attrs.get(skill_name + '_coord')
        if old == (self.last_coord_x, self.last_coord_y):
            del self.other_attrs[skill_name + '_coord']
            if extra_attr:
                del self.other_attrs[extra_attr]
        else:
            self.other_attrs[skill_name + '_coord'] = (self.last_coord_x, self.last_coord_y)
            if extra_attr:
                self.other_attrs[extra_attr] = extra_attr_value

    def load_platform_file(self, path):
        self.terrain_analyzer.load(path)
        self.other_attrs = self.terrain_analyzer.other_attrs.copy()
        for i in self.set_skill_color:
            if i in self.terrain_analyzer.set_skill_coord:
                self.other_attrs[i + '_coord'] = self.terrain_analyzer.set_skill_coord[i]
        self.update_listbox()

    def closeEvent(self, ev):
        if hasattr(self, 'stop_event'):
            self.stop_event.set()
        super().closeEvent(ev)

    def on_listbox_delete(self):
        selected = self.platform_list.selectedItems()
        if not selected:
            return

        if QMessageBox.question(self, "Terrain Editor", "Are you sure to delete %d platforms?" % (len(selected))) == QMessageBox.Yes:
            if self.record_mode != 0:
                QMessageBox.warning(self, "Terrain Editor", "Please close the ongoing record first")
            else:
                for i in selected:
                    del self.terrain_analyzer.platforms[i.data(Qt.UserRole)]
                self.update_listbox()

    def _on_toggle_no_monster(self):
        for i in self.platform_list.selectedItems():
            platform = self.terrain_analyzer.platforms[i.data(Qt.UserRole)]
            platform.no_monster = not platform.no_monster

        self.update_listbox()

    def update_listbox(self):
        self.platform_list.clear()
        for key, p in self.terrain_analyzer.platforms.items():
            label = "%s:  (%d,%d), (%d,%d)" % (key, p.start_x, p.start_y, p.end_x, p.end_y)
            other_attrs = []
            tooltip = 'platform'
            if p.no_monster:
                other_attrs.append('N')
                tooltip += ' (no monster)'
            if other_attrs:
                label += ' (' + ', '.join(other_attrs) + ')'
            item = QListWidgetItem(label, self.platform_list)
            item.setToolTip(tooltip)
            item.setData(Qt.UserRole, key)

    def toggle_record(self):
        if self.record_mode == 0:
            self.record_mode = 1
            self.coord_label.setStyleSheet("color: green")
            self.toggle_record_btn.setText('Stop record platform')
        else:
            self.record_mode = 0
            self.coord_label.setStyleSheet("color: black")
            self.terrain_analyzer.flush_input_coords_to_platform(coord_list=self.current_coords)
            self.current_coords = []
            self.update_listbox()
            self.toggle_record_btn.setText('Start record platform')

    def on_save(self):
        assert self.minimap_rect

        minimap_rect = self.minimap_rect  # dialog may cover minimap
        path = QFileDialog.getSaveFileName(self, "Save platform file", os.getcwd(), "Terrain File (*.platform)")[0]
        if path:
            if not path.endswith(".platform"):
                path += ".platform"
            self.other_attrs['minimap'] = minimap_rect
            self.terrain_analyzer.save(path, self.other_attrs)
            QMessageBox.information(self, "Terrain Editor", "File path {0}\n has been saved.".format(path))
            self.close()

    def on_reset_platforms(self):
        if QMessageBox.question(self, "Terrain Editor", "Really delete all terrain?") == QMessageBox.Yes:
            if self.record_mode != 0:
                self.toggle_record()
            self.coord_label.setStyleSheet("color: black")
            self.terrain_analyzer.reset()
            self.update_listbox()

    def find_minimap_coords(self):
        self.image_processor.update_image(set_focus=False)
        self.minimap_rect = self.image_processor.get_minimap_rect()

    def update_image(self):
        while not self.stop_event.is_set():
            try:
                self.image_processor.update_image(set_focus=False)
            except GameCaptureError:
                self.image_label.setText('Failed to capture game')
                time.sleep(0.1)
                continue

            if not self.minimap_rect:
                self.find_minimap_coords()
                if not self.minimap_rect:
                    self.image_label.setText('Minimap not found')
                    time.sleep(0.1)
                    continue

            playerpos = self.image_processor.find_player_minimap_marker(self.minimap_rect)
            if not playerpos:
                self.coord_label.setText('N/A')
                time.sleep(0.1)
                continue

            self.last_coord_x, self.last_coord_y = playerpos
            if self.record_mode == 1:
                if (self.last_coord_x, self.last_coord_y) not in self.current_coords:
                    self.current_coords.append((self.last_coord_x, self.last_coord_y))

            self.coord_label.setText("player: %d,%d" % (playerpos[0], playerpos[1]))
            if self.minimap_rect == 0:
                continue

            cropped_img = cv2.cvtColor(self.image_processor.bgr_img[self.minimap_rect[1]:self.minimap_rect[1] + self.minimap_rect[3], self.minimap_rect[0]:self.minimap_rect[0] + self.minimap_rect[2]], cv2.COLOR_BGR2RGB)
            if self.record_mode:
                cv2.line(cropped_img, (playerpos[0], 0), (playerpos[0], cropped_img.shape[0]), (0, 0, 255), 1)
                cv2.line(cropped_img, (0, playerpos[1]), (cropped_img.shape[1], playerpos[1]), (0, 0, 255), 1)
            else:
                cv2.line(cropped_img, (playerpos[0], 0), (playerpos[0], cropped_img.shape[0]), (0,0,0), 1)
                cv2.line(cropped_img, (0, playerpos[1]), (cropped_img.shape[1], playerpos[1]), (0, 0, 0), 1)

            selected = self.platform_list.selectedIndexes()
            if selected:
                for i in selected:
                    p = self.terrain_analyzer.platforms[i.data(Qt.UserRole)]
                    cv2.line(cropped_img, (p.start_x, p.start_y), (p.end_x, p.end_y), (0, 255, 0), 2)
                    break
            else:
                for key, p in self.terrain_analyzer.platforms.items():
                    cv2.line(cropped_img, (p.start_x, p.start_y), (p.end_x, p.end_y), (0, 255, 0), 2)

            for k in self.set_skill_color.keys():
                coord = self.other_attrs.get(k + '_coord')
                if coord:
                    color = self.set_skill_color[k]
                    cv2.circle(cropped_img, (coord[0], coord[1]), 4, (255, 255, 255), -1)  # white border
                    cv2.circle(cropped_img, (coord[0], coord[1]), 3, color, -1)

            h, w = cropped_img.shape[:2]
            img = QImage(cropped_img.data, w, h, w*3, QImage.Format_RGB888)
            img = img.scaledToWidth(min(self.image_label.width(), int(w * self.logicalDpiX() // 96)))
            self.image_label.setPixmap(QPixmap.fromImage(img))

            self.update()
            time.sleep(0.04)


if __name__ == "__main__":
    app = QApplication([])
    win = TerrainEditorWindow()
    win.show()
    app.exec_()
