import sys
import os
import time
import subprocess
from pathlib import Path


def _open_folder(path: str):
    """跨平台打开文件夹"""
    if os.name == "nt":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QFileDialog, QSpinBox, QDoubleSpinBox,
    QGroupBox, QRadioButton, QButtonGroup, QProgressBar, QFrame,
    QSizePolicy, QLineEdit, QComboBox, QMessageBox, QSplitter, QTabWidget,
    QRubberBand
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl, QRect, QSize, QPoint
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPainter, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from gif_converter import GifConverter
from utils import (format_time, parse_time, get_video_info,
                   resource_path, estimate_gif_bytes, format_size)


# ───────────────────────────── Stylesheet ─────────────────────────────
LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #E8E8E8;
    color: #1D1D1F;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #CBCBCE;
    background: #E8E8E8;
    border-radius: 0 8px 8px 8px;
}
QTabBar::tab {
    background: #DCDCDE;
    border: 1px solid #CBCBCE;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
    color: #6E6E73;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: #E8E8E8;
    color: #1D1D1F;
    font-weight: 600;
}
QTabBar::tab:hover:!selected { background: #E0E0E2; color: #1D1D1F; }

QGroupBox {
    background-color: #F4F4F4;
    border: 1px solid #CBCBCE;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: 600;
    color: #1D1D1F;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #1D1D1F;
    background-color: #E8E8E8;
}

QPushButton {
    background-color: #F9F9F9;
    border: 1px solid #CBCBCE;
    border-radius: 8px;
    padding: 6px 14px;
    color: #1D1D1F;
    font-size: 13px;
}
QPushButton:hover { background-color: #EFEFEF; border-color: #AEAEB2; }
QPushButton:pressed { background-color: #E0E0E0; }
QPushButton:disabled { background-color: #EBEBEB; color: #AEAEB2; border-color: #DCDCDE; }

QPushButton#primaryBtn {
    background-color: #0071E3;
    border: none;
    color: #FFFFFF;
    font-weight: bold;
    padding: 9px 24px;
    border-radius: 8px;
}
QPushButton#primaryBtn:hover { background-color: #0077ED; }
QPushButton#primaryBtn:pressed { background-color: #005BBB; }
QPushButton#primaryBtn:disabled { background-color: #A8C8F0; }

QPushButton#iconBtn {
    background-color: #EBEBEB;
    border: 1px solid #CBCBCE;
    border-radius: 6px;
    padding: 4px 6px;
    color: #1D1D1F;
    font-size: 14px;
    min-width: 30px;
    max-width: 38px;
}
QPushButton#iconBtn:hover { background-color: #DCDCDE; }
QPushButton#iconBtn:disabled { color: #AEAEB2; }

QPushButton#setRangeBtn {
    background-color: #E8F5E9;
    border: 1px solid #A5D6A7;
    border-radius: 6px;
    padding: 4px 10px;
    color: #2E7D32;
    font-size: 12px;
}
QPushButton#setRangeBtn:hover { background-color: #C8E6C9; }
QPushButton#setRangeBtn:disabled { background-color: #F5F5F5; color: #BDBDBD; border-color: #E0E0E0; }

QPushButton#matchBtn {
    background-color: #EEF2FF;
    border: 1px solid #C5CAE9;
    border-radius: 6px;
    padding: 3px 8px;
    color: #3949AB;
    font-size: 11px;
}
QPushButton#matchBtn:hover { background-color: #E8EAF6; }
QPushButton#matchBtn:disabled { background-color: #F5F5F5; color: #BDBDBD; border-color: #E0E0E0; }

QPushButton#reverseBtn {
    background-color: #FFF3E0;
    border: 1px solid #FFCC80;
    border-radius: 6px;
    padding: 4px 8px;
    color: #E65100;
    font-size: 12px;
    min-width: 70px;
    max-width: 90px;
}
QPushButton#reverseBtn:hover { background-color: #FFE0B2; }
QPushButton#reverseBtn:checked {
    background-color: #E65100;
    color: #FFFFFF;
    border-color: #BF360C;
}

QSlider::groove:horizontal { height: 4px; background: #CBCBCE; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #0071E3; border: none;
    width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
}
QSlider::handle:horizontal:hover { background: #0077ED; }
QSlider::sub-page:horizontal { background: #0071E3; border-radius: 2px; }

QSlider#rangeSlider::groove:horizontal { height: 6px; background: #CBCBCE; border-radius: 3px; }
QSlider#rangeSlider::handle:horizontal {
    background: #FF9500; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px;
}
QSlider#rangeSlider::sub-page:horizontal { background: #FFCC00; border-radius: 3px; }

QProgressBar {
    border: 1px solid #CBCBCE; border-radius: 5px; background: #F4F4F4;
    text-align: center; color: #6E6E73; height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0071E3, stop:1 #34AADC);
    border-radius: 4px;
}

QLabel { color: #1D1D1F; }
QLabel#titleLabel { font-size: 20px; font-weight: bold; color: #1D1D1F; }
QLabel#subLabel { color: #6E6E73; font-size: 11px; }
QLabel#timeLabel { font-family: 'Consolas', monospace; font-size: 13px; color: #FF9500; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #F9F9F9;
    border: 1px solid #CBCBCE;
    border-radius: 6px;
    padding: 5px 8px;
    color: #1D1D1F;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #0071E3; }
QLineEdit#timeEdit {
    font-family: 'Consolas', monospace;
    font-size: 13px;
    color: #E65100;
    background-color: #FFF8EE;
    border-color: #FFD080;
    padding: 3px 6px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #F9F9F9; border: 1px solid #CBCBCE;
    selection-background-color: #E5F0FB; color: #1D1D1F;
}

QRadioButton { spacing: 6px; color: #1D1D1F; }
QRadioButton::indicator {
    width: 14px; height: 14px; border-radius: 7px;
    border: 2px solid #AEAEB2; background: #F9F9F9;
}
QRadioButton::indicator:checked { background: #0071E3; border-color: #0071E3; }

QFrame#separator { background: #CBCBCE; max-height: 1px; }
QFrame#dropZone {
    border: 2px dashed #AEAEB2; border-radius: 10px; background: #EBEBEB;
}
QFrame#dropZone:hover { border-color: #0071E3; background: #E0ECF8; }
QSplitter::handle { background: #CBCBCE; width: 1px; }

QPushButton#ratioBtn {
    background-color: #EBEBEB;
    border: 1px solid #CBCBCE;
    border-radius: 6px;
    padding: 4px 6px;
    color: #AEAEB2;
    font-size: 14px;
    min-width: 30px;
    max-width: 38px;
}
QPushButton#ratioBtn:checked {
    background-color: #E5F0FB;
    border: 2px solid #0071E3;
    color: #0071E3;
}
QPushButton#ratioBtn:hover { background-color: #DCDCDE; }

QMenu {
    background-color: #F9F9F9;
    border: 1px solid #CBCBCE;
    border-radius: 8px;
    padding: 4px;
    color: #1D1D1F;
}
QMenu::item {
    padding: 7px 22px;
    border-radius: 5px;
}
QMenu::item:selected { background-color: #E5F0FB; color: #0071E3; }
QMenu::separator { height: 1px; background: #CBCBCE; margin: 4px 8px; }
"""

# ─────────────────────────── Dark Theme ───────────────────────────────
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1C1C1E;
    color: #E8E8E8;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #48484A;
    background: #1C1C1E;
    border-radius: 0 8px 8px 8px;
}
QTabBar::tab {
    background: #2C2C2E;
    border: 1px solid #48484A;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
    color: #8E8E93;
    font-size: 13px;
}
QTabBar::tab:selected { background: #1C1C1E; color: #E8E8E8; font-weight: 600; }
QTabBar::tab:hover:!selected { background: #3A3A3C; color: #E8E8E8; }

QGroupBox {
    background-color: #2C2C2E;
    border: 1px solid #48484A;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: 600;
    color: #E8E8E8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #E8E8E8;
    background-color: #1C1C1E;
}

QPushButton {
    background-color: #3A3A3C;
    border: 1px solid #48484A;
    border-radius: 8px;
    padding: 6px 14px;
    color: #E8E8E8;
    font-size: 13px;
}
QPushButton:hover { background-color: #4A4A4C; border-color: #636366; }
QPushButton:pressed { background-color: #5A5A5C; }
QPushButton:disabled { background-color: #2C2C2E; color: #636366; border-color: #3A3A3C; }

QPushButton#primaryBtn {
    background-color: #0071E3;
    border: none;
    color: #FFFFFF;
    font-weight: bold;
    padding: 9px 24px;
    border-radius: 8px;
}
QPushButton#primaryBtn:hover { background-color: #0077ED; }
QPushButton#primaryBtn:pressed { background-color: #005BBB; }
QPushButton#primaryBtn:disabled { background-color: #1A3A6E; }

QPushButton#iconBtn {
    background-color: #3A3A3C;
    border: 1px solid #48484A;
    border-radius: 6px;
    padding: 4px 6px;
    color: #E8E8E8;
    font-size: 14px;
    min-width: 30px;
    max-width: 38px;
}
QPushButton#iconBtn:hover { background-color: #4A4A4C; }
QPushButton#iconBtn:disabled { color: #636366; }

QPushButton#ratioBtn {
    background-color: #3A3A3C;
    border: 1px solid #636366;
    border-radius: 6px;
    padding: 4px 6px;
    color: #636366;
    font-size: 14px;
    min-width: 30px;
    max-width: 38px;
}
QPushButton#ratioBtn:checked {
    background-color: #1A2A3E;
    border: 2px solid #0071E3;
    color: #34AADC;
}
QPushButton#ratioBtn:hover { background-color: #4A4A4C; }

QPushButton#setRangeBtn {
    background-color: #1A3A1E;
    border: 1px solid #2E5A2E;
    border-radius: 6px;
    padding: 4px 10px;
    color: #4CAF50;
    font-size: 12px;
}
QPushButton#setRangeBtn:hover { background-color: #2A4A2A; }
QPushButton#setRangeBtn:disabled { background-color: #1C2020; color: #3A5A3A; border-color: #2A3A2A; }

QPushButton#matchBtn {
    background-color: #1A1A3E;
    border: 1px solid #2A2A6E;
    border-radius: 6px;
    padding: 3px 8px;
    color: #7986CB;
    font-size: 11px;
}
QPushButton#matchBtn:hover { background-color: #2A2A5E; }
QPushButton#matchBtn:disabled { background-color: #1C1C2E; color: #404060; border-color: #2A2A3A; }

QPushButton#reverseBtn {
    background-color: #3E2A00;
    border: 1px solid #6E4A00;
    border-radius: 6px;
    padding: 4px 8px;
    color: #FF9500;
    font-size: 12px;
    min-width: 70px;
    max-width: 90px;
}
QPushButton#reverseBtn:hover { background-color: #4E3A10; }
QPushButton#reverseBtn:checked { background-color: #FF9500; color: #1C1C1E; border-color: #CC7700; }

QSlider::groove:horizontal { height: 4px; background: #48484A; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #0071E3; border: none;
    width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
}
QSlider::handle:horizontal:hover { background: #0077ED; }
QSlider::sub-page:horizontal { background: #0071E3; border-radius: 2px; }

QSlider#rangeSlider::groove:horizontal { height: 6px; background: #48484A; border-radius: 3px; }
QSlider#rangeSlider::handle:horizontal {
    background: #FF9500; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px;
}
QSlider#rangeSlider::sub-page:horizontal { background: #FFCC00; border-radius: 3px; }

QProgressBar {
    border: 1px solid #48484A; border-radius: 5px; background: #2C2C2E;
    text-align: center; color: #8E8E93; height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0071E3, stop:1 #34AADC);
    border-radius: 4px;
}

QLabel { color: #E8E8E8; }
QLabel#titleLabel { font-size: 20px; font-weight: bold; color: #E8E8E8; }
QLabel#subLabel { color: #8E8E93; font-size: 11px; }
QLabel#timeLabel { font-family: 'Consolas', monospace; font-size: 13px; color: #FF9500; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #3A3A3C;
    border: 1px solid #48484A;
    border-radius: 6px;
    padding: 5px 8px;
    color: #E8E8E8;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #0071E3; }
QLineEdit#timeEdit {
    font-family: 'Consolas', monospace;
    font-size: 13px;
    color: #FF9500;
    background-color: #3E3018;
    border-color: #996600;
    padding: 3px 6px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #3A3A3C; border: 1px solid #48484A;
    selection-background-color: #0071E3; color: #E8E8E8;
}

QRadioButton { spacing: 6px; color: #E8E8E8; }
QRadioButton::indicator {
    width: 14px; height: 14px; border-radius: 7px;
    border: 2px solid #636366; background: #3A3A3C;
}
QRadioButton::indicator:checked { background: #0071E3; border-color: #0071E3; }

QFrame#separator { background: #48484A; max-height: 1px; }
QFrame#dropZone {
    border: 2px dashed #636366; border-radius: 10px; background: #2C2C2E;
}
QFrame#dropZone:hover { border-color: #0071E3; background: #1A2A3E; }
QSplitter::handle { background: #48484A; width: 1px; }

QMenu {
    background-color: #2C2C2E;
    border: 1px solid #48484A;
    border-radius: 8px;
    padding: 4px;
    color: #E8E8E8;
}
QMenu::item { padding: 7px 22px; border-radius: 5px; }
QMenu::item:selected { background-color: #1A2A3E; color: #34AADC; }
QMenu::separator { height: 1px; background: #48484A; margin: 4px 8px; }
"""


# ─────────────────── 主题图标映射 ─────────────────────────────────────
# 浅色主题图标
ICONS_LIGHT = {
    "play":       "1.png",
    "pause":      "17.png",
    "prev_frame": "2.png",
    "next_frame": "3.png",
    "reverse":    "5.png",
    "home":       "6.png",
    "end":        "7.png",
}
# 深色主题图标
ICONS_DARK = {
    "play":       "9.png",
    "pause":      "16.png",
    "prev_frame": "10.png",
    "next_frame": "11.png",
    "reverse":    "12.png",
    "home":       "13.png",
    "end":        "14.png",
}
ICON_SETTINGS = "8.png"   # 设置按钮（两主题相同）
ICON_THEME    = "15.png"  # 主题菜单图标（两主题相同）

# 当前版本号（发布新版时修改此处，并在 GitHub 创建同名 tag 的 Release）
VERSION = "1.0.2"
GITHUB_REPO = "DJpygeigei/GifCreatorTool"


# ───────────────────────────── 图标辅助 ──────────────────────────────
def _set_btn_icon(btn: QPushButton, icon_file: str, size: int = 20):
    """强制更新按钮图标（文件不存在则保留当前状态）"""
    from PySide6.QtGui import QIcon
    from PySide6.QtCore import QSize
    p = resource_path(icon_file)
    if os.path.exists(p):
        btn.setIcon(QIcon(p))
        btn.setIconSize(QSize(size, size))
        btn.setText("")
def _apply_icon(btn: QPushButton, icon_file: str, size: int = 16,
                keep_text: bool = False):
    """
    若 PNG 存在则设置按钮图标。
    keep_text=False（默认）：清除文字，纯图标显示（适合小方形按钮）。
    keep_text=True：保留文字，图标显示在左侧（适合带文字的功能按钮）。
    PNG 不存在时一律保持原有文字不变。
    """
    from PySide6.QtGui import QIcon
    from PySide6.QtCore import QSize
    p = resource_path(icon_file)
    if os.path.exists(p):
        btn.setIcon(QIcon(p))
        btn.setIconSize(QSize(size, size))
        if not keep_text:
            btn.setText("")


# ───────────────────────────── DropZone ───────────────────────────────
class DropZone(QFrame):
    fileDropped = Signal(str)

    def __init__(self, accept_exts=None, parent=None):
        super().__init__(parent)
        self._exts = accept_exts or {
            ".mp4", ".avi", ".mov", ".mkv", ".wmv",
            ".flv", ".webm", ".m4v", ".mpeg", ".mpg"
        }
        self._filter = self._build_filter()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setFixedHeight(64)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(8)
        icon = QLabel("🎬" if ".gif" not in self._exts else "🖼", self)
        icon.setStyleSheet("font-size:22px; border:none; background:transparent;")
        self.hint = QLabel("拖拽文件到此处，或点击选择", self)
        self.hint.setStyleSheet("font-size:13px; color:#6E6E73; border:none; background:transparent;")
        lay.addWidget(icon)
        lay.addWidget(self.hint)

    def _build_filter(self):
        exts = " ".join(f"*{e}" for e in self._exts)
        return f"文件 ({exts})"

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._open_dialog()

    def _open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", self._filter)
        if path:
            self.fileDropped.emit(path)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            u = e.mimeData().urls()
            if u and self._ok(u[0].toLocalFile()):
                e.acceptProposedAction()
                self.setStyleSheet(
                    "QFrame#dropZone{border:2px dashed #0071E3;"
                    "border-radius:10px;background:#E5F0FB;}"
                )

    def dragLeaveEvent(self, e):
        self.setStyleSheet("")

    def dropEvent(self, e: QDropEvent):
        self.setStyleSheet("")
        u = e.mimeData().urls()
        if u:
            p = u[0].toLocalFile()
            if self._ok(p):
                self.fileDropped.emit(p)

    def _ok(self, p):
        return Path(p).suffix.lower() in self._exts


# ───────────────────────────── RangeSlider ────────────────────────────
class RangeSliderWidget(QWidget):
    rangeChanged      = Signal(float, float)
    preview_requested = Signal()   # 请求预览选取片段
    goto_start_req    = Signal()   # 请求跳到片段开始

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0.0
        self._start = 0.0
        self._end = 0.0
        self._block = False

        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)

        # sliders
        sr = QHBoxLayout()
        sr.setSpacing(6)
        self.s_slider = QSlider(Qt.Horizontal)
        self.s_slider.setObjectName("rangeSlider")
        self.s_slider.setRange(0, 1000)
        self.e_slider = QSlider(Qt.Horizontal)
        self.e_slider.setObjectName("rangeSlider")
        self.e_slider.setRange(0, 1000)
        self.e_slider.setValue(1000)
        sr.addWidget(self.s_slider)
        sr.addWidget(self.e_slider)
        vl.addLayout(sr)

        # manual input row
        ir = QHBoxLayout()
        ir.setSpacing(5)
        ir.addWidget(QLabel("开始:"))
        self.s_edit = QLineEdit("00:00.000")
        self.s_edit.setObjectName("timeEdit")
        self.s_edit.setFixedWidth(88)
        self.s_edit.setToolTip("格式: MM:SS.mmm")
        ir.addWidget(self.s_edit)
        self.s_ok = QPushButton("✔")
        self.s_ok.setObjectName("iconBtn")
        self.s_ok.setFixedWidth(30)
        _apply_icon(self.s_ok, "10.png")
        ir.addWidget(self.s_ok)
        ir.addSpacing(10)
        ir.addWidget(QLabel("结束:"))
        self.e_edit = QLineEdit("00:00.000")
        self.e_edit.setObjectName("timeEdit")
        self.e_edit.setFixedWidth(88)
        self.e_edit.setToolTip("格式: MM:SS.mmm")
        ir.addWidget(self.e_edit)
        self.e_ok = QPushButton("✔")
        self.e_ok.setObjectName("iconBtn")
        self.e_ok.setFixedWidth(30)
        _apply_icon(self.e_ok, "10.png")
        ir.addWidget(self.e_ok)
        ir.addStretch()
        self.dur_lbl = QLabel("片段: --")
        self.dur_lbl.setObjectName("subLabel")
        ir.addWidget(self.dur_lbl)
        vl.addLayout(ir)

        # 片段预览按钮行
        pr = QHBoxLayout()
        pr.setSpacing(6)
        self.btn_goto_start = QPushButton("回到开始")
        self.btn_goto_start.setObjectName("setRangeBtn")
        self.btn_goto_start.setToolTip("跳转到片段开始点")
        self.btn_goto_start.setEnabled(False)
        _apply_icon(self.btn_goto_start, ICONS_LIGHT["home"], size=14, keep_text=True)
        self.btn_preview = QPushButton("▶ 预览片段")
        self.btn_preview.setObjectName("setRangeBtn")
        self.btn_preview.setToolTip("从开始点播放到结束点后自动暂停")
        self.btn_preview.setEnabled(False)
        _apply_icon(self.btn_preview, "1.png", size=14, keep_text=True)
        pr.addWidget(self.btn_goto_start)
        pr.addWidget(self.btn_preview)
        pr.addStretch()
        vl.addLayout(pr)

        self.s_slider.valueChanged.connect(self._s_moved)
        self.e_slider.valueChanged.connect(self._e_moved)
        self.s_ok.clicked.connect(self._apply_s)
        self.e_ok.clicked.connect(self._apply_e)
        self.s_edit.returnPressed.connect(self._apply_s)
        self.e_edit.returnPressed.connect(self._apply_e)
        self.btn_goto_start.clicked.connect(self.goto_start_req)
        self.btn_preview.clicked.connect(self.preview_requested)

    def set_duration(self, d):
        self._duration = d
        self._start = 0.0
        self._end = d
        self._block = True
        self.s_slider.setValue(0)
        self.e_slider.setValue(1000)
        self._block = False
        self._refresh()
        self.rangeChanged.emit(0.0, d)
        # 有时长才启用预览按钮
        has = d > 0
        self.btn_goto_start.setEnabled(has)
        self.btn_preview.setEnabled(has)

    def apply_theme_icons(self, theme: str):
        """随主题切换更新预览按钮图标"""
        icons = ICONS_DARK if theme == "dark" else ICONS_LIGHT
        _apply_icon(self.btn_goto_start, icons["home"], size=14, keep_text=True)
        _apply_icon(self.btn_preview,    icons["play"], size=14, keep_text=True)

    def set_start(self, sec):
        if self._duration <= 0:
            return
        sec = max(0.0, min(sec, self._end - 0.001))
        self._start = sec
        self._block = True
        self.s_slider.setValue(int(sec / self._duration * 1000))
        self._block = False
        self._refresh()
        self.rangeChanged.emit(self._start, self._end)

    def set_end(self, sec):
        if self._duration <= 0:
            return
        sec = max(self._start + 0.001, min(sec, self._duration))
        self._end = sec
        self._block = True
        self.e_slider.setValue(int(sec / self._duration * 1000))
        self._block = False
        self._refresh()
        self.rangeChanged.emit(self._start, self._end)

    def _s_moved(self, v):
        if self._block or self._duration <= 0:
            return
        if v >= self.e_slider.value():
            self.s_slider.setValue(self.e_slider.value() - 1)
            return
        self._start = v / 1000 * self._duration
        self._refresh()
        self.rangeChanged.emit(self._start, self._end)

    def _e_moved(self, v):
        if self._block or self._duration <= 0:
            return
        if v <= self.s_slider.value():
            self.e_slider.setValue(self.s_slider.value() + 1)
            return
        self._end = v / 1000 * self._duration
        self._refresh()
        self.rangeChanged.emit(self._start, self._end)

    def _apply_s(self):
        self.set_start(parse_time(self.s_edit.text().strip()))

    def _apply_e(self):
        self.set_end(parse_time(self.e_edit.text().strip()))

    def _refresh(self):
        self.s_edit.setText(format_time(self._start))
        self.e_edit.setText(format_time(self._end))
        dur = self._end - self._start
        self.dur_lbl.setText(
            f"片段: {format_time(dur)} ({self._start:.2f}s → {self._end:.2f}s)"
        )

    @property
    def start_sec(self): return self._start
    @property
    def end_sec(self): return self._end


# ───────────────────────────── GIF Params Widget ──────────────────────
class GifParamsWidget(QGroupBox):
    """⚙ GIF 参数 面板（复用于两个 Tab）"""
    def __init__(self, parent=None):
        super().__init__("⚙ GIF 参数", parent)
        self._src_w = 0
        self._src_h = 0
        self._src_fps = 0.0
        self._aspect = 0.0

        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        # FPS row
        fps_row = QHBoxLayout()
        fps_row.addWidget(QLabel("帧率 (FPS):"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 50)
        self.fps_spin.setValue(15)
        self.fps_spin.setToolTip("GIF 格式最高支持 50fps（帧延迟精度为 0.01 秒）")
        fps_row.addWidget(self.fps_spin)
        self.fps_match_btn = QPushButton("⊙ 匹配源文件")
        self.fps_match_btn.setObjectName("matchBtn")
        self.fps_match_btn.setEnabled(False)
        self._apply_btn_icon(self.fps_match_btn, "8.png", keep_text=True)
        fps_row.addWidget(self.fps_match_btn)
        self.fps_hint_lbl = QLabel("* GIF 最高 50fps")
        self.fps_hint_lbl.setObjectName("subLabel")
        self.fps_hint_lbl.setVisible(False)
        fps_row.addWidget(self.fps_hint_lbl)
        fps_row.addStretch()
        lay.addLayout(fps_row)

        # Resolution row
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("分辨率:"))
        res_row.addWidget(QLabel("宽"))
        self.w_spin = QSpinBox()
        self.w_spin.setRange(2, 4096)
        self.w_spin.setValue(480)
        self.w_spin.setSingleStep(2)
        self.w_spin.setFixedWidth(72)
        res_row.addWidget(self.w_spin)
        res_row.addWidget(QLabel("×"))
        res_row.addWidget(QLabel("高"))
        self.h_spin = QSpinBox()
        self.h_spin.setRange(2, 4096)
        self.h_spin.setValue(270)
        self.h_spin.setSingleStep(2)
        self.h_spin.setFixedWidth(72)
        res_row.addWidget(self.h_spin)
        self.ratio_btn = QPushButton("🔗")
        self.ratio_btn.setObjectName("ratioBtn")
        self.ratio_btn.setCheckable(True)
        self.ratio_btn.setChecked(True)
        self.ratio_btn.setToolTip("保持宽高比（蓝色=生效，灰色=不生效）")
        self.ratio_btn.setFixedWidth(34)
        self._apply_btn_icon(self.ratio_btn, "9.png")          # 纯图标，清除文字
        res_row.addWidget(self.ratio_btn)
        self.res_match_btn = QPushButton("⊙ 匹配源文件")
        self.res_match_btn.setObjectName("matchBtn")
        self.res_match_btn.setEnabled(False)
        self._apply_btn_icon(self.res_match_btn, "8.png", keep_text=True)
        res_row.addWidget(self.res_match_btn)
        res_row.addStretch()
        lay.addLayout(res_row)

        # Dither row
        dither_row = QHBoxLayout()
        dither_row.addWidget(QLabel("抖动算法:"))
        self.dither_combo = QComboBox()
        self.dither_combo.addItems(["bayer (推荐)", "floyd_steinberg", "none"])
        dither_row.addWidget(self.dither_combo)
        dither_row.addStretch()
        lay.addLayout(dither_row)

        self.fps_match_btn.clicked.connect(self._match_fps)
        self.res_match_btn.clicked.connect(self._match_res)
        self.w_spin.valueChanged.connect(self._w_changed)
        self.h_spin.valueChanged.connect(self._h_changed)
        self._updating = False

    @staticmethod
    def _apply_btn_icon(btn: QPushButton, icon_file: str, fallback: str = "",
                        keep_text: bool = False):
        """若 PNG 存在则为按钮设置图标；keep_text=True 时保留文字"""
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        p = resource_path(icon_file)
        if os.path.exists(p):
            btn.setIcon(QIcon(p))
            btn.setIconSize(QSize(16, 16))
            if not keep_text:
                btn.setText("")

    def set_source_info(self, info: dict):
        self._src_w = info.get("width", 0)
        self._src_h = info.get("height", 0)
        self._src_fps = info.get("fps", 0.0)
        if self._src_w > 0 and self._src_h > 0:
            self._aspect = self._src_w / self._src_h
        self.fps_match_btn.setEnabled(self._src_fps > 0)
        self.res_match_btn.setEnabled(self._src_w > 0)

    def _match_fps(self):
        if self._src_fps > 0:
            capped = min(50, max(1, int(round(self._src_fps))))
            self.fps_spin.setValue(capped)
            # 若源文件超过 50fps，显示提示
            self.fps_hint_lbl.setVisible(self._src_fps > 50)

    def _match_res(self):
        if self._src_w > 0:
            self._updating = True
            self.w_spin.setValue(self._src_w)
            self.h_spin.setValue(self._src_h)
            self._updating = False

    def _w_changed(self, v):
        if self._updating or not self.ratio_btn.isChecked() or self._aspect <= 0:
            return
        self._updating = True
        h = max(2, int(round(v / self._aspect)))
        h = h + (h % 2)
        self.h_spin.setValue(h)
        self._updating = False

    def _h_changed(self, v):
        if self._updating or not self.ratio_btn.isChecked() or self._aspect <= 0:
            return
        self._updating = True
        w = max(2, int(round(v * self._aspect)))
        w = w + (w % 2)
        self.w_spin.setValue(w)
        self._updating = False

    @property
    def fps(self): return self.fps_spin.value()
    @property
    def width(self): return self.w_spin.value()
    @property
    def height(self): return self.h_spin.value()
    @property
    def dither(self):
        m = {"bayer (推荐)": "bayer", "floyd_steinberg": "floyd_steinberg", "none": "none"}
        return m.get(self.dither_combo.currentText(), "bayer")


# ───────────────────────────── Compress Options ───────────────────────
class CompressOptionsWidget(QGroupBox):
    """🗜 GIF 压缩 面板（复用于两个 Tab）"""
    def __init__(self, parent=None):
        super().__init__("🗜 GIF 压缩", parent)
        lay = QVBoxLayout(self)
        lay.setSpacing(6)

        self.grp = QButtonGroup(self)
        self.r_none = QRadioButton("不压缩（保留原始质量）")
        self.r_keep_res = QRadioButton("保持分辨率（降低帧率压缩）")
        self.r_keep_fps = QRadioButton("保持帧率（降低分辨率压缩）")
        self.r_target = QRadioButton("指定目标文件大小")
        self.r_none.setChecked(True)

        for r in [self.r_none, self.r_keep_res, self.r_keep_fps, self.r_target]:
            self.grp.addButton(r)
            lay.addWidget(r)

        # Target sub-panel
        sub = QWidget()
        sub_lay = QVBoxLayout(sub)
        sub_lay.setContentsMargins(20, 2, 0, 0)
        sub_lay.setSpacing(5)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("目标大小:"))
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(0.1, 500.0)
        self.size_spin.setValue(5.0)
        self.size_spin.setSuffix(" MB")
        self.size_spin.setDecimals(1)
        self.size_spin.setEnabled(False)
        size_row.addWidget(self.size_spin)
        size_row.addStretch()
        sub_lay.addLayout(size_row)

        self.sub_grp = QButtonGroup(self)
        self.r_ts_auto = QRadioButton("自动（同时调整帧率和分辨率）")
        self.r_ts_res = QRadioButton("保持分辨率，改变帧率")
        self.r_ts_fps = QRadioButton("保持帧率，改变分辨率")
        self.r_ts_auto.setChecked(True)
        for r in [self.r_ts_auto, self.r_ts_res, self.r_ts_fps]:
            self.sub_grp.addButton(r)
            r.setEnabled(False)
            sub_lay.addWidget(r)

        lay.addWidget(sub)
        self.r_target.toggled.connect(self._on_target_toggled)

    def _on_target_toggled(self, checked):
        self.size_spin.setEnabled(checked)
        for r in [self.r_ts_auto, self.r_ts_res, self.r_ts_fps]:
            r.setEnabled(checked)

    @property
    def mode(self):
        if self.r_none.isChecked(): return "none"
        if self.r_keep_res.isChecked(): return "keep_resolution"
        if self.r_keep_fps.isChecked(): return "keep_fps"
        if self.r_ts_auto.isChecked(): return "target_size"
        if self.r_ts_res.isChecked(): return "target_size_keep_res"
        if self.r_ts_fps.isChecked(): return "target_size_keep_fps"
        return "none"

    @property
    def target_mb(self):
        return self.size_spin.value() if self.r_target.isChecked() else None


# ───────────────────────────── Convert Thread ─────────────────────────
class ConvertThread(QThread):
    progress = Signal(int, str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            c = GifConverter(progress_callback=lambda p, m: self.progress.emit(p, m))
            out = c.convert(**self.params)
            self.finished.emit(out)
        except Exception as ex:
            self.error.emit(str(ex))


# ───────────────────────────── Preview Player ─────────────────────────
class PreviewPlayer(QWidget):
    """通用视频/GIF 预览播放器，含倒放、变速、逐帧、手动时间输入"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fps = 25.0
        self._theme = "light"         # 当前主题，用于选择对应图标
        self._current_speed = 1.0
        self._is_reversing = False
        self._manual_pos = 0.0          # 倒放时自己维护位置，避免依赖 player.position()
        self._range_widget: RangeSliderWidget = None
        self._range_playing = False   # 片段预览模式
        self._range_end_ms  = 0

        # 倒放定时器
        self._reverse_timer = QTimer(self)
        self._reverse_timer.timeout.connect(self._reverse_step)
        # 倒放时需短暂 play 才能刷新画面（Windows MediaFoundation 限制）
        self._frame_flush_timer = QTimer(self)
        self._frame_flush_timer.setSingleShot(True)
        self._frame_flush_timer.timeout.connect(self._flush_pause)

        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(4)

        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(220)
        self.video_widget.setStyleSheet("background:#DCDCDE; border-radius:6px;")
        vl.addWidget(self.video_widget, stretch=1)

        # Media player
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        self.player.positionChanged.connect(self._on_pos)
        self.player.playbackStateChanged.connect(self._on_state)

        # Seek slider
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self._seek_by_slider)
        vl.addWidget(self.seek_slider)

        # ── Controls row 1 ──
        row1 = QHBoxLayout()
        row1.setSpacing(4)

        self.btn_home  = self._mk_btn("⏮", "跳到开头")
        self.btn_prev  = self._mk_btn("⏪", "上一帧")
        self.btn_play  = self._mk_btn("▶", "播放/暂停")
        self.btn_play.setFixedWidth(40)
        self.btn_next  = self._mk_btn("⏩", "下一帧")
        self.btn_end   = self._mk_btn("⏭", "跳到结尾")
        self.btn_reverse = self._mk_btn("倒放", "倒放")
        self.btn_reverse.setObjectName("reverseBtn")
        self.btn_reverse.setCheckable(True)
        self.btn_reverse.setMinimumWidth(0)
        self.btn_reverse.setMaximumWidth(16777215)

        # 可编辑时间显示
        self.time_edit = QLineEdit("00:00.000")
        self.time_edit.setObjectName("timeEdit")
        self.time_edit.setFixedWidth(90)
        self.time_edit.setToolTip("当前时间，可直接输入后回车跳转\n格式: MM:SS.mmm")

        # 速率控制
        row1.addWidget(self.btn_home)
        row1.addWidget(self.btn_prev)
        row1.addWidget(self.btn_play)
        row1.addWidget(self.btn_next)
        row1.addWidget(self.btn_end)
        row1.addWidget(self.btn_reverse)
        row1.addSpacing(6)
        row1.addWidget(self.time_edit)
        row1.addSpacing(6)
        row1.addWidget(QLabel("速率:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x","0.5x","0.75x","1x","1.25x","1.5x","2x"])
        self.speed_combo.setCurrentIndex(3)
        self.speed_combo.setFixedWidth(72)
        row1.addWidget(self.speed_combo)
        self.speed_edit = QLineEdit("1.0")
        self.speed_edit.setFixedWidth(50)
        self.speed_edit.setToolTip("自定义速率，回车确认")
        row1.addWidget(self.speed_edit)
        row1.addStretch()
        vl.addLayout(row1)

        # ── Controls row 2: set range ──
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        self.btn_set_start = QPushButton("[ 设为开始")
        self.btn_set_start.setObjectName("setRangeBtn")
        self.btn_set_start.setToolTip("将当前时间设为截取起点")
        _apply_icon(self.btn_set_start, "11.png", keep_text=True)
        self.btn_set_end = QPushButton("设为结束 ]")
        self.btn_set_end.setObjectName("setRangeBtn")
        self.btn_set_end.setToolTip("将当前时间设为截取终点")
        _apply_icon(self.btn_set_end, "12.png", keep_text=True)
        row2.addWidget(self.btn_set_start)
        row2.addWidget(self.btn_set_end)
        row2.addStretch()
        vl.addLayout(row2)

        # Wire signals
        self.btn_home.clicked.connect(lambda: self.player.setPosition(0))
        self.btn_end.clicked.connect(lambda: self.player.setPosition(max(0, self.player.duration()-1)))
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_prev.clicked.connect(self._prev_frame)
        self.btn_next.clicked.connect(self._next_frame)
        self.btn_reverse.clicked.connect(self._toggle_reverse)
        self.time_edit.returnPressed.connect(self._seek_by_time_edit)
        self.speed_combo.currentIndexChanged.connect(self._speed_combo_changed)
        self.speed_edit.returnPressed.connect(self._speed_edit_changed)
        self.btn_set_start.clicked.connect(self._set_start)
        self.btn_set_end.clicked.connect(self._set_end)

        self._set_enabled(False)
        self.apply_theme_icons("light")   # 初始化图标

    @staticmethod
    def _mk_btn(fallback: str, tooltip: str) -> QPushButton:
        """创建图标按钮（图标由 apply_theme_icons 统一设置）"""
        b = QPushButton(fallback)
        b.setObjectName("iconBtn")
        b.setToolTip(tooltip)
        return b

    def apply_theme_icons(self, theme: str):
        """切换主题时更新所有播放控制按钮的图标"""
        self._theme = theme
        icons = ICONS_DARK if theme == "dark" else ICONS_LIGHT
        _set_btn_icon(self.btn_home,    icons["home"])
        _set_btn_icon(self.btn_prev,    icons["prev_frame"])
        _set_btn_icon(self.btn_next,    icons["next_frame"])
        _set_btn_icon(self.btn_end,     icons["end"])
        _set_btn_icon(self.btn_reverse, icons["reverse"])
        # 播放/暂停按钮根据当前播放状态选择图标
        is_playing = (self.player.playbackState() == QMediaPlayer.PlayingState)
        key = "pause" if is_playing else "play"
        _set_btn_icon(self.btn_play, icons[key])

    def link_range(self, rw: RangeSliderWidget):
        self._range_widget = rw

    def play_range(self, start_sec: float, end_sec: float):
        """从 start_sec 播放到 end_sec 后自动暂停"""
        if self._is_reversing:
            self._stop_reverse()
        self._range_end_ms = int(end_sec * 1000)
        self._range_playing = True
        self.player.setPosition(int(start_sec * 1000))
        self.player.play()

    def goto_range_start(self, start_sec: float):
        """跳转到 start_sec 并暂停"""
        if self._is_reversing:
            self._stop_reverse()
        self.player.pause()
        self.player.setPosition(int(start_sec * 1000))
        self.player.play()
        QTimer.singleShot(20, self.player.pause)

    def load(self, path: str, fps: float):
        self._fps = fps if fps > 0 else 25.0
        self.player.setSource(QUrl.fromLocalFile(path))
        self._set_enabled(True)

    def _set_enabled(self, v):
        for w in [self.btn_home, self.btn_end, self.btn_play, self.btn_prev,
                  self.btn_next, self.btn_reverse, self.seek_slider,
                  self.btn_set_start, self.btn_set_end, self.time_edit]:
            w.setEnabled(v)

    # ── Playback ──────────────────────────────────────────────────
    def _toggle_play(self):
        if self._is_reversing:
            self._stop_reverse()
            return
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_state(self, state):
        if self._is_reversing:
            return
        icons = ICONS_DARK if self._theme == "dark" else ICONS_LIGHT
        is_playing = (state == QMediaPlayer.PlayingState)
        key = "pause" if is_playing else "play"
        _set_btn_icon(self.btn_play, icons[key])

    def _prev_frame(self):
        self.player.pause()
        fms = max(1, int(1000 / self._fps))
        new_pos = max(0, self.player.position() - fms)
        self.player.setPosition(new_pos)
        # 短暂 play 刷新画面
        self.player.play()
        QTimer.singleShot(20, self.player.pause)

    def _next_frame(self):
        self.player.pause()
        dur = self.player.duration()
        fms = max(1, int(1000 / self._fps))
        new_pos = min(max(0, dur - 1), self.player.position() + fms)
        self.player.setPosition(new_pos)
        self.player.play()
        QTimer.singleShot(20, self.player.pause)

    # ── Reverse playback ─────────────────────────────────────────
    # 修复说明：Windows 的 MediaFoundation 后端在 paused 状态下调用
    # setPosition() 后不一定刷新画面。解决方法：seek 后短暂 play(8ms)
    # 再 pause，强制解码器输出新帧。同时用 _manual_pos 自维护位置，
    # 不依赖 player.position()（该值在 seek 未完成时会返回旧值）。
    def _toggle_reverse(self, checked):
        if checked:
            self.player.pause()
            self._is_reversing = True
            self._manual_pos = float(self.player.position())
            interval = max(50, int(1000 / min(self._fps, 20)))
            self._reverse_timer.start(interval)
        else:
            self._stop_reverse()

    def _stop_reverse(self):
        self._reverse_timer.stop()
        self._frame_flush_timer.stop()
        self._is_reversing = False
        self.btn_reverse.setChecked(False)

    def _reverse_step(self):
        speed = max(0.25, self._current_speed)
        fms = 1000.0 / (self._fps * speed)
        self._manual_pos = max(0.0, self._manual_pos - fms)
        # seek 到新位置
        self.player.setPosition(int(self._manual_pos))
        # 短暂 play 强制画面刷新（8ms 后暂停）
        if not self._frame_flush_timer.isActive():
            self.player.play()
            self._frame_flush_timer.start(8)
        if self._manual_pos <= 0.0:
            QTimer.singleShot(20, self._stop_reverse)

    def _flush_pause(self):
        """倒放帧刷新：短暂 play 后立即 pause"""
        if self._is_reversing:
            self.player.pause()

    # ── Speed ─────────────────────────────────────────────────────
    def _speed_combo_changed(self, idx):
        vals = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        v = vals[idx]
        self.speed_edit.setText(str(v))
        self._apply_speed(v)

    def _speed_edit_changed(self):
        try:
            v = max(0.1, min(8.0, float(self.speed_edit.text())))
            self._apply_speed(v)
        except ValueError:
            pass

    def _apply_speed(self, v: float):
        self._current_speed = v
        if not self._is_reversing:
            self.player.setPlaybackRate(v)

    # ── Seek ──────────────────────────────────────────────────────
    def _seek_by_slider(self, val):
        dur = self.player.duration()
        if dur > 0:
            self.player.setPosition(int(val / 1000 * dur))

    def _seek_by_time_edit(self):
        sec = parse_time(self.time_edit.text().strip())
        dur = self.player.duration()
        if dur > 0:
            self.player.setPosition(max(0, min(int(sec * 1000), dur - 1)))

    def _on_pos(self, pos_ms: int):
        dur = self.player.duration()
        if dur > 0:
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(int(pos_ms / dur * 1000))
            self.seek_slider.blockSignals(False)
        self.time_edit.blockSignals(True)
        self.time_edit.setText(format_time(pos_ms / 1000))
        self.time_edit.blockSignals(False)
        # 片段预览：到达结束点后自动暂停
        if self._range_playing and pos_ms >= self._range_end_ms:
            self._range_playing = False
            self.player.pause()

    # ── Set range ─────────────────────────────────────────────────
    def _set_start(self):
        if self._range_widget:
            self._range_widget.set_start(self.player.position() / 1000)

    def _set_end(self):
        if self._range_widget:
            self._range_widget.set_end(self.player.position() / 1000)


# ───────────────────────────── Video → GIF Tab ────────────────────────
class VideoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ""
        self._info = {}
        self._thread = None

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.addWidget(splitter)

        # ── Left ──
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)
        ll.setSpacing(8)

        # Import
        imp_grp = QGroupBox("📂 导入视频")
        imp_lay = QVBoxLayout(imp_grp)
        imp_lay.setContentsMargins(8, 14, 8, 8)
        imp_lay.setSpacing(5)

        self.drop = DropZone()
        self.drop.fileDropped.connect(self._load)
        imp_lay.addWidget(self.drop)

        fr = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("视频文件路径...")
        self.path_edit.setReadOnly(True)
        br = QPushButton("浏览...")
        br.setFixedWidth(68)
        br.clicked.connect(self.drop._open_dialog)
        fr.addWidget(self.path_edit)
        fr.addWidget(br)
        imp_lay.addLayout(fr)
        self.info_lbl = QLabel("")
        self.info_lbl.setObjectName("subLabel")
        imp_lay.addWidget(self.info_lbl)
        ll.addWidget(imp_grp)

        # Preview
        prev_grp = QGroupBox("🎬 视频预览")
        pg = QVBoxLayout(prev_grp)
        pg.setContentsMargins(8, 14, 8, 8)
        self.player = PreviewPlayer()
        pg.addWidget(self.player)
        ll.addWidget(prev_grp, stretch=1)

        # Range
        rng_grp = QGroupBox("✂ 选取时间范围")
        rg = QVBoxLayout(rng_grp)
        rg.setContentsMargins(8, 14, 8, 8)
        self.range_w = RangeSliderWidget()
        self.player.link_range(self.range_w)
        self.range_w.preview_requested.connect(
            lambda: self.player.play_range(self.range_w.start_sec, self.range_w.end_sec))
        self.range_w.goto_start_req.connect(
            lambda: self.player.goto_range_start(self.range_w.start_sec))
        rg.addWidget(self.range_w)
        ll.addWidget(rng_grp)

        splitter.addWidget(left)

        # ── Right ──
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 0, 0, 0)
        rl.setSpacing(8)

        self.params = GifParamsWidget()
        rl.addWidget(self.params)

        self.compress = CompressOptionsWidget()
        rl.addWidget(self.compress)

        out_grp = QGroupBox("💾 输出设置")
        og = QVBoxLayout(out_grp)
        or_ = QHBoxLayout()
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("输出路径（留空自动生成）...")
        ob = QPushButton("浏览...")
        ob.setFixedWidth(68)
        ob.clicked.connect(self._browse_out)
        or_.addWidget(self.out_edit)
        or_.addWidget(ob)
        og.addLayout(or_)
        rl.addWidget(out_grp)

        # 预估大小
        est_grp = QGroupBox("📊 预估文件大小")
        eg = QVBoxLayout(est_grp)
        eg.setContentsMargins(10, 14, 10, 10)
        eg.setSpacing(3)
        self.est_size_lbl = QLabel("--")
        self.est_size_lbl.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#0071E3;"
        )
        self.est_detail_lbl = QLabel("导入视频后自动计算")
        self.est_detail_lbl.setObjectName("subLabel")
        eg.addWidget(self.est_size_lbl)
        eg.addWidget(self.est_detail_lbl)
        rl.addWidget(est_grp)

        rl.addStretch()

        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setObjectName("primaryBtn")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self._start)
        _apply_icon(self.convert_btn, "13.png", size=20, keep_text=True)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("subLabel")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        rl.addWidget(self.convert_btn)
        rl.addWidget(self.progress)
        rl.addWidget(self.status_lbl)

        splitter.addWidget(right)
        splitter.setSizes([640, 400])

        # 连接预估更新信号
        self.range_w.rangeChanged.connect(self._update_estimate)
        self.params.fps_spin.valueChanged.connect(self._update_estimate)
        self.params.w_spin.valueChanged.connect(self._update_estimate)
        self.params.h_spin.valueChanged.connect(self._update_estimate)
        self.compress.grp.buttonToggled.connect(self._update_estimate)
        self.compress.sub_grp.buttonToggled.connect(self._update_estimate)
        self.compress.size_spin.valueChanged.connect(self._update_estimate)

    def _load(self, path):
        self._path = path
        self.path_edit.setText(path)
        info = get_video_info(path)
        self._info = info
        if info:
            d = info.get("duration", 0)
            w = info.get("width", 0)
            h = info.get("height", 0)
            fps = info.get("fps", 0)
            self.info_lbl.setText(
                f"时长: {format_time(d)}  |  分辨率: {w}×{h}  |  帧率: {fps:.1f} fps"
            )
            self.range_w.set_duration(d)
            self.params.set_source_info(info)
            self.params.fps_spin.setValue(min(15, max(1, int(fps))))
            sw = min(480, w)
            sh = max(2, int(sw * h / w)) if w > 0 else 270
            sh = sh + (sh % 2)
            self.params.w_spin.setValue(sw)
            self.params.h_spin.setValue(sh)
            self.player.load(path, fps)
        self.out_edit.setText(str(Path(path).with_suffix(".gif")))
        self.convert_btn.setEnabled(True)
        self._update_estimate()

    def _update_estimate(self, *_):
        dur = self.range_w.end_sec - self.range_w.start_sec
        if dur <= 0 or not self._path:
            self.est_size_lbl.setText("--")
            self.est_detail_lbl.setText("导入视频后自动计算")
            return
        fps = self.params.fps
        w = self.params.width
        h = self.params.height
        mode = self.compress.mode
        target_mb = self.compress.target_mb
        est = estimate_gif_bytes(dur, fps, w, h, mode, target_mb)
        frames = max(1, int(dur * fps))
        size_str = format_size(est)
        prefix = "" if mode in ("target_size","target_size_keep_res","target_size_keep_fps") else "~"
        self.est_size_lbl.setText(f"{prefix}{size_str}")
        self.est_detail_lbl.setText(
            f"{frames} 帧 · {w}×{h}px · {fps}fps · {dur:.1f}秒"
        )

    def _browse_out(self):
        p, _ = QFileDialog.getSaveFileName(self, "保存 GIF", self.out_edit.text(), "GIF (*.gif)")
        if p:
            self.out_edit.setText(p)

    def _start(self):
        if not self._path:
            return
        out = self.out_edit.text().strip() or str(Path(self._path).with_suffix(".gif"))
        self.out_edit.setText(out)
        params = dict(
            input_path=self._path, output_path=out,
            start_sec=self.range_w.start_sec, end_sec=self.range_w.end_sec,
            fps=self.params.fps, width=self.params.width, height=self.params.height,
            dither=self.params.dither,
            compress_mode=self.compress.mode, target_size_mb=self.compress.target_mb,
        )
        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_lbl.setText("准备中...")
        self._thread = ConvertThread(params)
        self._thread.progress.connect(lambda p, m: (self.progress.setValue(p), self.status_lbl.setText(m)))
        self._thread.finished.connect(self._done)
        self._thread.error.connect(self._err)
        self._thread.start()

    def _done(self, out):
        self.progress.setValue(100)
        mb = os.path.getsize(out) / 1024 / 1024
        self.status_lbl.setText(f"✅ 完成！大小: {mb:.2f} MB")
        self.convert_btn.setEnabled(True)
        r = QMessageBox.question(self, "完成",
            f"GIF 已保存:\n{out}\n\n大小: {mb:.2f} MB\n\n打开文件夹？",
            QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            _open_folder(str(Path(out).parent))

    def _err(self, msg):
        self.progress.setVisible(False)
        self.status_lbl.setText(f"❌ 错误: {msg}")
        self.convert_btn.setEnabled(True)
        QMessageBox.critical(self, "失败", f"错误:\n{msg}")


# ───────────────────────────── GIF Editor Tab ─────────────────────────
class GifEditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ""
        self._info = {}
        self._thread = None

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.addWidget(splitter)

        # ── Left ──
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)
        ll.setSpacing(8)

        imp_grp = QGroupBox("🖼 导入 GIF")
        il = QVBoxLayout(imp_grp)
        il.setContentsMargins(8, 14, 8, 8)
        il.setSpacing(5)

        self.drop = DropZone(accept_exts={".gif"})
        self.drop.fileDropped.connect(self._load)
        il.addWidget(self.drop)

        fr = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("GIF 文件路径...")
        self.path_edit.setReadOnly(True)
        br = QPushButton("浏览...")
        br.setFixedWidth(68)
        br.clicked.connect(self.drop._open_dialog)
        fr.addWidget(self.path_edit)
        fr.addWidget(br)
        il.addLayout(fr)
        self.info_lbl = QLabel("")
        self.info_lbl.setObjectName("subLabel")
        il.addWidget(self.info_lbl)
        ll.addWidget(imp_grp)

        prev_grp = QGroupBox("🎞 GIF 预览")
        pg = QVBoxLayout(prev_grp)
        pg.setContentsMargins(8, 14, 8, 8)
        self.player = PreviewPlayer()
        pg.addWidget(self.player)
        ll.addWidget(prev_grp, stretch=1)

        rng_grp = QGroupBox("✂ 选取时间范围")
        rg = QVBoxLayout(rng_grp)
        rg.setContentsMargins(8, 14, 8, 8)
        self.range_w = RangeSliderWidget()
        self.player.link_range(self.range_w)
        self.range_w.preview_requested.connect(
            lambda: self.player.play_range(self.range_w.start_sec, self.range_w.end_sec))
        self.range_w.goto_start_req.connect(
            lambda: self.player.goto_range_start(self.range_w.start_sec))
        rg.addWidget(self.range_w)
        ll.addWidget(rng_grp)

        splitter.addWidget(left)

        # ── Right ──
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 0, 0, 0)
        rl.setSpacing(8)

        self.params = GifParamsWidget()
        rl.addWidget(self.params)

        self.compress = CompressOptionsWidget()
        rl.addWidget(self.compress)

        out_grp = QGroupBox("💾 输出设置")
        og = QVBoxLayout(out_grp)
        or_ = QHBoxLayout()
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("输出路径（留空自动生成）...")
        ob = QPushButton("浏览...")
        ob.setFixedWidth(68)
        ob.clicked.connect(self._browse_out)
        or_.addWidget(self.out_edit)
        or_.addWidget(ob)
        og.addLayout(or_)
        rl.addWidget(out_grp)

        # 预估大小
        est_grp = QGroupBox("📊 预估文件大小")
        eg = QVBoxLayout(est_grp)
        eg.setContentsMargins(10, 14, 10, 10)
        eg.setSpacing(3)
        self.est_size_lbl = QLabel("--")
        self.est_size_lbl.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#0071E3;"
        )
        self.est_detail_lbl = QLabel("导入 GIF 后自动计算")
        self.est_detail_lbl.setObjectName("subLabel")
        eg.addWidget(self.est_size_lbl)
        eg.addWidget(self.est_detail_lbl)
        rl.addWidget(est_grp)

        rl.addStretch()

        self.convert_btn = QPushButton("✂ 开始编辑导出")
        self.convert_btn.setObjectName("primaryBtn")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self._start)
        _apply_icon(self.convert_btn, "13.png", size=20, keep_text=True)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("subLabel")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        rl.addWidget(self.convert_btn)
        rl.addWidget(self.progress)
        rl.addWidget(self.status_lbl)

        splitter.addWidget(right)
        splitter.setSizes([640, 400])

        # 连接预估更新信号
        self.range_w.rangeChanged.connect(self._update_estimate)
        self.params.fps_spin.valueChanged.connect(self._update_estimate)
        self.params.w_spin.valueChanged.connect(self._update_estimate)
        self.params.h_spin.valueChanged.connect(self._update_estimate)
        self.compress.grp.buttonToggled.connect(self._update_estimate)
        self.compress.sub_grp.buttonToggled.connect(self._update_estimate)
        self.compress.size_spin.valueChanged.connect(self._update_estimate)

    def _load(self, path):
        self._path = path
        self.path_edit.setText(path)
        info = get_video_info(path)
        self._info = info
        if info:
            d = info.get("duration", 0)
            w = info.get("width", 0)
            h = info.get("height", 0)
            fps = info.get("fps", 0)
            self.info_lbl.setText(
                f"时长: {format_time(d)}  |  分辨率: {w}×{h}  |  帧率: {fps:.1f} fps"
            )
            self.range_w.set_duration(d)
            self.params.set_source_info(info)
            self.params.fps_spin.setValue(min(30, max(1, int(fps))))
            self.params.w_spin.setValue(w)
            self.params.h_spin.setValue(h)
            self.player.load(path, fps)
        # auto output: _edit suffix
        p = Path(path)
        self.out_edit.setText(str(p.parent / (p.stem + "_edit.gif")))
        self.convert_btn.setEnabled(True)
        self._update_estimate()

    def _update_estimate(self, *_):
        dur = self.range_w.end_sec - self.range_w.start_sec
        if dur <= 0 or not self._path:
            self.est_size_lbl.setText("--")
            self.est_detail_lbl.setText("导入 GIF 后自动计算")
            return
        fps = self.params.fps
        w = self.params.width
        h = self.params.height
        mode = self.compress.mode
        target_mb = self.compress.target_mb
        est = estimate_gif_bytes(dur, fps, w, h, mode, target_mb)
        frames = max(1, int(dur * fps))
        size_str = format_size(est)
        prefix = "" if mode in ("target_size","target_size_keep_res","target_size_keep_fps") else "~"
        self.est_size_lbl.setText(f"{prefix}{size_str}")
        self.est_detail_lbl.setText(
            f"{frames} 帧 · {w}×{h}px · {fps}fps · {dur:.1f}秒"
        )

    def _browse_out(self):
        p, _ = QFileDialog.getSaveFileName(self, "保存 GIF", self.out_edit.text(), "GIF (*.gif)")
        if p:
            self.out_edit.setText(p)

    def _start(self):
        if not self._path:
            return
        out = self.out_edit.text().strip()
        if not out:
            p = Path(self._path)
            out = str(p.parent / (p.stem + "_edit.gif"))
            self.out_edit.setText(out)
        params = dict(
            input_path=self._path, output_path=out,
            start_sec=self.range_w.start_sec, end_sec=self.range_w.end_sec,
            fps=self.params.fps, width=self.params.width, height=self.params.height,
            dither=self.params.dither,
            compress_mode=self.compress.mode, target_size_mb=self.compress.target_mb,
        )
        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_lbl.setText("准备中...")
        self._thread = ConvertThread(params)
        self._thread.progress.connect(lambda p, m: (self.progress.setValue(p), self.status_lbl.setText(m)))
        self._thread.finished.connect(self._done)
        self._thread.error.connect(self._err)
        self._thread.start()

    def _done(self, out):
        self.progress.setValue(100)
        mb = os.path.getsize(out) / 1024 / 1024
        self.status_lbl.setText(f"✅ 完成！大小: {mb:.2f} MB")
        self.convert_btn.setEnabled(True)
        r = QMessageBox.question(self, "完成",
            f"GIF 已保存:\n{out}\n\n大小: {mb:.2f} MB\n\n打开文件夹？",
            QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            _open_folder(str(Path(out).parent))

    def _err(self, msg):
        self.progress.setVisible(False)
        self.status_lbl.setText(f"❌ 错误: {msg}")
        self.convert_btn.setEnabled(True)
        QMessageBox.critical(self, "失败", f"错误:\n{msg}")


# ───────────────────────── Screen Region Selector ─────────────────────
class ScreenRegionSelector(QWidget):
    """全屏半透明遮罩，拖拽框选录制区域"""
    region_selected = Signal(int, int, int, int)   # x, y, w, h (屏幕坐标)
    cancelled       = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setCursor(Qt.CrossCursor)
        self._origin = None
        self._rubber = QRubberBand(QRubberBand.Shape.Rectangle, self)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.showFullScreen()
        self._tip_pos = QPoint(screen.width() // 2, screen.height() // 2)

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90))
        p.setPen(QColor(255, 255, 255, 180))
        p.drawText(self._tip_pos.x() - 120, self._tip_pos.y() - 10, 240, 30,
                   Qt.AlignCenter, "拖拽鼠标选择录制区域，ESC 取消")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._origin = e.pos()
            self._rubber.setGeometry(QRect(self._origin, QSize()))
            self._rubber.show()

    def mouseMoveEvent(self, e):
        if self._origin:
            self._rubber.setGeometry(
                QRect(self._origin, e.pos()).normalized()
            )
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._origin:
            rect = QRect(self._origin, e.pos()).normalized()
            if rect.width() > 20 and rect.height() > 20:
                # 转换为屏幕坐标
                sp = self.mapToGlobal(rect.topLeft())
                # 宽高必须为偶数（ffmpeg 要求）
                w = rect.width() & ~1
                h = rect.height() & ~1
                self.region_selected.emit(sp.x(), sp.y(), w, h)
            else:
                self._origin = None
                self._rubber.hide()
                return
            self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.cancelled.emit()
            self.close()


# ───────────────────────────── Record Thread ──────────────────────────
class RecordThread(QThread):
    """
    PIL.ImageGrab 截帧 → 实时 pipe 给 ffmpeg rawvideo 编码。
    绕开 gdigrab 兼容性问题，Pillow 是已有依赖无需额外安装。
    """
    tick     = Signal(int)   # 已录制秒数
    finished = Signal(str)   # 输出文件路径
    error    = Signal(str)

    def __init__(self, x: int, y: int, w: int, h: int, fps: int, output_path: str):
        super().__init__()
        # 宽高必须为偶数（libx264 要求）
        self.x = x; self.y = y
        self.w = w & ~1
        self.h = h & ~1
        self.fps = fps
        self.output_path = output_path
        self._stop_flag = False
        self._proc = None

    def run(self):
        from PIL import ImageGrab, Image
        from utils import FFMPEG

        bbox = (self.x, self.y, self.x + self.w, self.y + self.h)
        interval = 1.0 / max(1, self.fps)

        # ffmpeg 通过 stdin 接收 rawvideo（RGB24）
        cmd = [
            FFMPEG, "-y",
            "-f", "rawvideo",
            "-pixel_format", "rgb24",
            "-video_size", f"{self.w}x{self.h}",
            "-framerate", str(self.fps),
            "-i", "pipe:0",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            self.output_path  # 先不加 faststart，录制完再 remux
        ]
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.DEVNULL,   # 不管道化 stderr，避免 pipe buffer 死锁
                stdout=subprocess.DEVNULL,
                creationflags=flags
            )

            start = time.time()
            frame_count = 0

            while not self._stop_flag:
                t0 = time.time()
                try:
                    img = ImageGrab.grab(bbox=bbox, all_screens=True)
                    # 确保尺寸精确（部分系统会偏差 1px）
                    if img.size != (self.w, self.h):
                        img = img.resize((self.w, self.h), Image.LANCZOS)
                    self._proc.stdin.write(img.tobytes())
                    frame_count += 1
                except BrokenPipeError:
                    break
                except Exception:
                    break

                self.tick.emit(int(time.time() - start))

                elapsed_frame = time.time() - t0
                sleep_t = interval - elapsed_frame
                if sleep_t > 0:
                    time.sleep(sleep_t)

            # 关闭 stdin 通知 ffmpeg 结束
            try:
                self._proc.stdin.close()
            except Exception:
                pass

            # 等待 ffmpeg 完成编码（给足够时间，不能用短超时）
            try:
                self._proc.wait(timeout=120)
            except Exception:
                self._proc.terminate()

            if frame_count < 2:
                self.error.emit(f"录制帧数不足（仅 {frame_count} 帧），请录制更长时间")
                return

            raw_size = os.path.getsize(self.output_path) if os.path.exists(self.output_path) else 0
            if raw_size < 1024:
                self.error.emit(f"编码失败，输出文件为空（已截取 {frame_count} 帧）")
                return

            # ── Remux: 加 faststart，QMediaPlayer 才能正常播放 ──
            raw_path = self.output_path.replace(".mp4", "_raw.mp4")
            final_path = self.output_path
            try:
                os.rename(self.output_path, raw_path)
                remux_cmd = [
                    FFMPEG, "-y", "-i", raw_path,
                    "-c", "copy", "-movflags", "+faststart",
                    final_path
                ]
                subprocess.run(remux_cmd, capture_output=True, timeout=60, creationflags=flags)
            except Exception:
                # remux 失败则直接用原始文件
                if os.path.exists(raw_path) and not os.path.exists(final_path):
                    try:
                        os.rename(raw_path, final_path)
                    except Exception:
                        pass
            finally:
                if raw_path != final_path and os.path.exists(raw_path):
                    try:
                        os.remove(raw_path)
                    except Exception:
                        pass

            if os.path.exists(final_path) and os.path.getsize(final_path) > 1024:
                self.finished.emit(final_path)
            else:
                self.error.emit("视频文件生成失败，请重试")

        except Exception as ex:
            import traceback
            self.error.emit(f"录制出错:\n{traceback.format_exc()}")

    def stop(self):
        """设置停止标志，捕帧循环将在下一帧后退出"""
        self._stop_flag = True


# ───────────────────────────── Record Tab ─────────────────────────────
class RecordTab(QWidget):
    """屏幕录制 → GIF 转换标签页"""

    def __init__(self):
        super().__init__()
        self._region = None          # (x, y, w, h)
        self._record_thread = None
        self._record_sec = 0
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)
        self._src_video = None       # 录制完成的临时视频路径
        self._src_fps   = 0.0
        self._src_w = 0
        self._src_h = 0
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # ════════════════ 左侧：录制控制 + 预览 ════════════════
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 4, 0)
        lv.setSpacing(8)

        # ── 录制控制组 ──
        rec_box = QGroupBox("录制控制")
        rb_lay = QVBoxLayout(rec_box)
        rb_lay.setSpacing(6)

        # 区域信息行
        region_row = QHBoxLayout()
        self.region_lbl = QLabel("未选择区域")
        self.region_lbl.setObjectName("subLabel")
        region_row.addWidget(self.region_lbl, stretch=1)
        self.select_btn = QPushButton("框选录制区域")
        self.select_btn.setObjectName("matchBtn")
        self.select_btn.clicked.connect(self._select_region)
        region_row.addWidget(self.select_btn)
        rb_lay.addLayout(region_row)

        # 录制帧率
        fps_row = QHBoxLayout()
        fps_row.addWidget(QLabel("录制帧率:"))
        self.rec_fps_spin = QSpinBox()
        self.rec_fps_spin.setRange(1, 50)
        self.rec_fps_spin.setValue(15)
        self.rec_fps_spin.setToolTip("录制时的帧率，GIF 最高 50fps")
        self.rec_fps_spin.setFixedWidth(70)
        fps_row.addWidget(self.rec_fps_spin)
        fps_row.addWidget(QLabel("fps"))
        fps_row.addStretch()
        rb_lay.addLayout(fps_row)

        # 开始 / 停止按钮 + 计时
        ctrl_row = QHBoxLayout()
        self.record_btn = QPushButton("⏺  开始录制")
        self.record_btn.setObjectName("primaryBtn")
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self._toggle_record)
        ctrl_row.addWidget(self.record_btn, stretch=1)
        self.rec_timer_lbl = QLabel("00:00")
        self.rec_timer_lbl.setObjectName("timeLabel")
        self.rec_timer_lbl.setFixedWidth(60)
        ctrl_row.addWidget(self.rec_timer_lbl)
        rb_lay.addLayout(ctrl_row)

        # 状态
        self.rec_status_lbl = QLabel("请先框选录制区域")
        self.rec_status_lbl.setObjectName("subLabel")
        rb_lay.addWidget(self.rec_status_lbl)

        lv.addWidget(rec_box)

        # ── 视频预览 ──
        self.player = PreviewPlayer()
        self.player.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lv.addWidget(self.player, stretch=1)

        # ── 时间范围 ──
        rng_grp = QGroupBox("✂ 选取时间范围")
        rg = QVBoxLayout(rng_grp)
        rg.setContentsMargins(8, 14, 8, 8)
        self.range_w = RangeSliderWidget()
        self.player.link_range(self.range_w)
        self.range_w.preview_requested.connect(
            lambda: self.player.play_range(self.range_w.start_sec, self.range_w.end_sec))
        self.range_w.goto_start_req.connect(
            lambda: self.player.goto_range_start(self.range_w.start_sec))
        rg.addWidget(self.range_w)
        lv.addWidget(rng_grp)

        splitter.addWidget(left)

        # ════════════════ 右侧：参数 + 输出 ════════════════
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 0, 0, 0)
        rv.setSpacing(8)

        self.params = GifParamsWidget()
        rv.addWidget(self.params)

        self.compress = CompressOptionsWidget()
        rv.addWidget(self.compress)

        # 输出路径
        out_box = QGroupBox("输出设置")
        out_lay = QVBoxLayout(out_box)
        out_row = QHBoxLayout()
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("输出 GIF 路径（留空则保存到桌面）")
        out_row.addWidget(self.out_edit)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse_out)
        out_row.addWidget(browse_btn)
        out_lay.addLayout(out_row)

        # 预估大小
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("预估文件大小:"))
        self.size_lbl = QLabel("--")
        self.size_lbl.setObjectName("timeLabel")
        size_row.addWidget(self.size_lbl)
        size_row.addStretch()
        out_lay.addLayout(size_row)
        rv.addWidget(out_box)

        rv.addStretch()

        # 转换按钮
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setObjectName("primaryBtn")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self._start_convert)
        rv.addWidget(self.convert_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        rv.addWidget(self.progress)
        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("subLabel")
        rv.addWidget(self.status_lbl)

        splitter.addWidget(right)
        splitter.setSizes([600, 380])
        main_layout.addWidget(splitter, stretch=1)

        # ── 信号连接（预估大小实时更新）──
        self.range_w.rangeChanged.connect(self._update_estimate)
        self.params.fps_spin.valueChanged.connect(self._update_estimate)
        self.params.w_spin.valueChanged.connect(self._update_estimate)
        self.params.h_spin.valueChanged.connect(self._update_estimate)
        self.compress.grp.buttonToggled.connect(self._update_estimate)
        self.compress.sub_grp.buttonToggled.connect(self._update_estimate)
        self.compress.size_spin.valueChanged.connect(self._update_estimate)

    # ── 框选区域 ─────────────────────────────────────────────────
    def _select_region(self):
        # 最小化主窗口避免遮挡
        win = self.window()
        win.showMinimized()
        QTimer.singleShot(300, self._open_selector)

    def _open_selector(self):
        self._selector = ScreenRegionSelector()
        self._selector.region_selected.connect(self._on_region_selected)
        self._selector.cancelled.connect(self._on_selector_cancelled)

    def _on_selector_cancelled(self):
        self.window().showNormal()

    def _on_region_selected(self, x, y, w, h):
        self.window().showNormal()
        self._region = (x, y, w, h)
        self.region_lbl.setText(f"区域: ({x}, {y})  {w} × {h} px")
        self.record_btn.setEnabled(True)
        self.rec_status_lbl.setText("已选择区域，可开始录制")
        # 同步 GIF 参数宽高
        self.params.set_source_info({
            "width": w, "height": h,
            "fps": float(self.rec_fps_spin.value()),
            "duration": 0.0
        })
        self._src_w = w
        self._src_h = h

    # ── 录制控制 ─────────────────────────────────────────────────
    def _toggle_record(self):
        if self._record_thread and self._record_thread.isRunning():
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        if not self._region:
            return
        x, y, w, h = self._region
        fps = self.rec_fps_spin.value()
        import uuid, tempfile
        # 优先用系统临时目录（ASCII 路径），Windows 下用 C:\Windows\Temp 保底
        if os.name == "nt":
            sys_temp = os.environ.get("SystemRoot", "C:\\Windows") + "\\Temp"
            if not os.path.isdir(sys_temp):
                sys_temp = tempfile.gettempdir()
                try:
                    sys_temp.encode("ascii")
                except UnicodeEncodeError:
                    sys_temp = "C:\\Temp"
                    os.makedirs(sys_temp, exist_ok=True)
        else:
            sys_temp = tempfile.gettempdir()
        self._tmp_video = os.path.join(sys_temp, f"giftool_{uuid.uuid4().hex[:8]}.mp4")
        self._record_sec = 0
        self.rec_timer_lbl.setText("00:00")
        self.record_btn.setText("⏹  停止录制")
        self.select_btn.setEnabled(False)
        self.rec_fps_spin.setEnabled(False)
        self.rec_status_lbl.setText("录制中...")
        self.convert_btn.setEnabled(False)

        self._record_thread = RecordThread(x, y, w, h, fps, self._tmp_video)
        self._record_thread.tick.connect(self._on_record_tick)
        self._record_thread.finished.connect(self._on_record_finished)
        self._record_thread.error.connect(self._on_record_error)
        self._record_thread.start()
        self._tick_timer.start(500)

    def _stop_record(self):
        self._tick_timer.stop()
        self.rec_status_lbl.setText("正在停止录制，等待编码完成...")
        self.record_btn.setEnabled(False)
        if self._record_thread:
            self._record_thread.stop()  # 只设置标志位，不阻塞主线程

    def _on_tick(self):
        self._record_sec += 1
        m = self._record_sec // 60
        s = self._record_sec % 60
        self.rec_timer_lbl.setText(f"{m:02d}:{s:02d}")

    def _on_record_tick(self, sec):
        pass  # 由 _tick_timer 驱动，避免竞争

    def _on_record_finished(self, path):
        self._tick_timer.stop()
        self.record_btn.setText("⏺  开始录制")
        self.record_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.rec_fps_spin.setEnabled(True)
        self._src_video = path

        # 检查文件是否有效
        if not os.path.exists(path) or os.path.getsize(path) < 1024:
            self.rec_status_lbl.setText("录制文件无效，请重试")
            return

        self.rec_status_lbl.setText(f"录制完成（{self._record_sec}秒），可预览并转换")

        # 获取视频信息
        info = get_video_info(path)
        src_fps = float(self.rec_fps_spin.value())
        dur = 0.0
        if info:
            src_fps = info.get("fps", src_fps)
            dur = info.get("duration", 0.0)
            self._src_fps = src_fps
            self._src_w   = info.get("width", self._src_w)
            self._src_h   = info.get("height", self._src_h)
            self.params.set_source_info(info)

        # 加载预览（必须传 fps）
        self.player.load(path, src_fps)

        # 设置时间范围
        if dur > 0:
            self.range_w.set_duration(dur)

        self.convert_btn.setEnabled(True)
        self._update_estimate()

    def _on_record_error(self, msg):
        self._tick_timer.stop()
        self.record_btn.setText("⏺  开始录制")
        self.record_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.rec_fps_spin.setEnabled(True)
        short = msg.split("\n")[0]
        self.rec_status_lbl.setText(f"录制失败: {short}")
        QMessageBox.critical(self, "录制失败", msg)

    # ── 浏览输出路径 ──────────────────────────────────────────────
    def _browse_out(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存 GIF", "", "GIF 文件 (*.gif)")
        if path:
            if not path.lower().endswith(".gif"):
                path += ".gif"
            self.out_edit.setText(path)

    # ── 预估大小 ─────────────────────────────────────────────────
    def _update_estimate(self, *_):
        try:
            s, e = self.range_w.start_sec, self.range_w.end_sec
            dur = max(0.0, e - s)
            fps = self.params.fps
            w = self.params.width
            h = self.params.height if self.params.height > 0 else self._src_h
            mode = self.compress.mode
            tmb = self.compress.target_mb
            nb = estimate_gif_bytes(dur, fps, w, h, mode, tmb)
            self.size_lbl.setText(format_size(nb))
        except Exception:
            self.size_lbl.setText("--")

    # ── 开始转换 ─────────────────────────────────────────────────
    def _start_convert(self):
        if not self._src_video or not os.path.exists(self._src_video):
            QMessageBox.warning(self, "提示", "请先完成屏幕录制")
            return
        out = self.out_edit.text().strip()
        if not out:
            desk = Path.home() / "Desktop"
            out = str(desk / "recorded.gif")
        if not out.lower().endswith(".gif"):
            out += ".gif"

        s = self.range_w.start_sec
        e = self.range_w.end_sec
        if e <= s:
            QMessageBox.warning(self, "时间范围错误", "结束时间必须大于开始时间")
            return

        params = dict(
            input_path=self._src_video,
            output_path=out,
            start_sec=s,
            end_sec=e,
            fps=self.params.fps,
            width=self.params.width,
            height=self.params.height,
            dither=self.params.dither,
            compress_mode=self.compress.mode,
            target_size_mb=self.compress.target_mb,
        )

        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_lbl.setText("转换中...")

        self._conv_thread = ConvertThread(params)
        self._conv_thread.progress.connect(self._on_prog)
        self._conv_thread.finished.connect(self._on_done)
        self._conv_thread.error.connect(self._on_err)
        self._conv_thread.start()

    def _on_prog(self, pct, msg):
        self.progress.setValue(pct)
        self.status_lbl.setText(msg)

    def _on_done(self, out):
        self.progress.setValue(100)
        self.progress.setVisible(False)
        self.status_lbl.setText(f"完成: {out}")
        self.convert_btn.setEnabled(True)
        r = QMessageBox.question(
            self, "转换完成",
            f"GIF 已保存到:\n{out}\n\n是否打开所在文件夹？",
            QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            _open_folder(str(Path(out).parent))

    def _on_err(self, msg):
        self.progress.setVisible(False)
        self.status_lbl.setText(f"❌ 错误: {msg}")
        self.convert_btn.setEnabled(True)
        QMessageBox.critical(self, "转换失败", msg)


# ───────────────────────── Update Checker ────────────────────────────
class UpdateChecker(QThread):
    """后台检查 GitHub Release 是否有新版本"""
    update_available = Signal(str, str, str)  # latest_ver, download_url, release_notes
    no_update        = Signal()
    check_error      = Signal(str)

    def run(self):
        import urllib.request
        import urllib.error
        import json

        # ── 每天只检查一次，结果缓存到本地 ──────────────────────
        cache_file = self._cache_path()
        today = time.strftime("%Y-%m-%d")
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("date") == today:
                # 今天已检查过，直接用缓存结果
                if cached.get("has_update"):
                    self.update_available.emit(
                        cached["version"],
                        cached["url"],
                        cached["notes"]
                    )
                else:
                    self.no_update.emit()
                return
        except Exception:
            pass  # 缓存不存在或损坏，继续请求

        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "GIFTool-Updater"})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self._save_cache(cache_file, today, False)
                    self.no_update.emit()
                    return
                if e.code == 403:
                    self.check_error.emit("rate_limit")
                    return
                raise

            latest_tag = data.get("tag_name", "").lstrip("v")
            notes = data.get("body", "") or ""

            download_url = ""
            for asset in data.get("assets", []):
                if asset.get("name", "").lower() == "giftool.exe":
                    download_url = asset.get("browser_download_url", "")
                    break

            if not download_url:
                self.check_error.emit("Release 中未找到 GIFTool.exe 资产\n请确认 Release 中上传了名为 GIFTool.exe 的文件")
                return

            has_update = self._is_newer(latest_tag, VERSION)
            self._save_cache(cache_file, today, has_update,
                             latest_tag, download_url, notes)

            if has_update:
                self.update_available.emit(latest_tag, download_url, notes)
            else:
                self.no_update.emit()

        except Exception as ex:
            self.check_error.emit(str(ex))

    @staticmethod
    def _cache_path() -> str:
        """缓存文件放在 AppData/Local/GIFTool/ 下"""
        app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        cache_dir = os.path.join(app_data, "GIFTool")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, "update_cache.json")

    @staticmethod
    def _save_cache(path, date, has_update,
                    version="", url="", notes=""):
        import json
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "date":       date,
                    "has_update": has_update,
                    "version":    version,
                    "url":        url,
                    "notes":      notes,
                }, f, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def _is_newer(latest: str, current: str) -> bool:
        try:
            def parse(v):
                return [int(x) for x in v.strip().split(".")]
            return parse(latest) > parse(current)
        except Exception:
            return latest.strip() != current.strip()


class DownloadThread(QThread):
    """后台下载新版 EXE，报告进度"""
    progress = Signal(int)   # 0-100
    finished = Signal(str)   # 下载完成的文件路径
    dl_error = Signal(str)

    def __init__(self, url: str, dest: str):
        super().__init__()
        self.url = url
        self.dest = dest

    def run(self):
        import urllib.request
        try:
            def _hook(count, block, total):
                if total > 0:
                    self.progress.emit(min(100, int(count * block * 100 / total)))
            urllib.request.urlretrieve(self.url, self.dest, _hook)
            self.progress.emit(100)
            self.finished.emit(self.dest)
        except Exception as ex:
            self.dl_error.emit(str(ex))


# ───────────────────────────── Main Window ────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF 工具")
        self.setMinimumSize(960, 700)
        self.resize(1120, 800)
        self._current_theme = "light"

        central = QWidget()
        self.setCentralWidget(central)
        vl = QVBoxLayout(central)
        vl.setContentsMargins(14, 10, 14, 10)
        vl.setSpacing(8)

        # ── Title bar ──
        title_row = QHBoxLayout()
        tl = QLabel("🎞 GIF Tool")
        tl.setObjectName("titleLabel")
        sl = QLabel("视频转 GIF / 屏幕录制 / GIF 编辑")
        sl.setObjectName("subLabel")
        sl.setAlignment(Qt.AlignBottom)
        title_row.addWidget(tl)
        title_row.addWidget(sl)
        title_row.addStretch()

        # ── 设置按钮（右上角）──
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("iconBtn")
        self.settings_btn.setToolTip("设置")
        self.settings_btn.setFixedSize(34, 34)
        _apply_icon(self.settings_btn, "8.png", size=20)
        self.settings_btn.clicked.connect(self._show_settings)
        title_row.addWidget(self.settings_btn)

        vl.addLayout(title_row)

        sep = QFrame()
        sep.setObjectName("separator")
        vl.addWidget(sep)

        self.tabs = QTabWidget()
        self.video_tab  = VideoTab()
        self.record_tab = RecordTab()
        self.gif_tab    = GifEditorTab()
        self.tabs.addTab(self.video_tab,  "🎬 视频转 GIF")
        self.tabs.addTab(self.record_tab, "⏺ 录制 GIF")
        self.tabs.addTab(self.gif_tab,    "🖼 GIF 编辑")
        vl.addWidget(self.tabs, stretch=1)

        # 启动后 2 秒静默检查更新（避免影响启动速度）
        QTimer.singleShot(2000, self._silent_check_update)

    # ── 设置菜单 ─────────────────────────────────────────────────
    def _show_settings(self):
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction, QIcon
        menu = QMenu(self)

        # ── 主题子菜单 ──
        theme_menu = menu.addMenu(" 界面主题")
        # 用 15.png 替代 emoji 作为子菜单图标
        theme_icon_p = resource_path(ICON_THEME)
        if os.path.exists(theme_icon_p):
            theme_menu.setIcon(QIcon(theme_icon_p))

        light_act = QAction("☀ 浅色主题", self)
        light_act.setCheckable(True)
        light_act.setChecked(self._current_theme == "light")
        light_act.triggered.connect(lambda: self._apply_theme("light"))
        theme_menu.addAction(light_act)

        dark_act = QAction("🌙 深色主题", self)
        dark_act.setCheckable(True)
        dark_act.setChecked(self._current_theme == "dark")
        dark_act.triggered.connect(lambda: self._apply_theme("dark"))
        theme_menu.addAction(dark_act)

        # ── 分隔线 + 检查更新 ──
        menu.addSeparator()
        update_act = QAction(f"检查更新  (当前 v{VERSION})", self)
        update_act.triggered.connect(self._manual_check_update)
        menu.addAction(update_act)

        # ── 分隔线 + 联系开发者 ──
        menu.addSeparator()
        contact_act = QAction("联系开发者", self)
        contact_act.setEnabled(False)
        menu.addAction(contact_act)
        popo_act = QAction("POPO：wupengyu1@corp.netease.com", self)
        popo_act.setEnabled(False)
        menu.addAction(popo_act)

        # 在设置按钮正下方弹出
        pos = self.settings_btn.mapToGlobal(
            self.settings_btn.rect().bottomLeft()
        )
        menu.exec(pos)

    # ── 更新相关 ──────────────────────────────────────────────────
    def _silent_check_update(self):
        """启动时静默检查，有新版才弹窗"""
        self._updater = UpdateChecker()
        self._updater.update_available.connect(self._on_update_available)
        self._updater.no_update.connect(lambda: None)   # 静默忽略
        self._updater.check_error.connect(lambda _: None)  # 静默忽略网络错误
        self._updater.start()

    def _manual_check_update(self):
        """手动触发：删除今日缓存，强制重新请求"""
        try:
            cache = UpdateChecker._cache_path()
            if os.path.exists(cache):
                os.remove(cache)
        except Exception:
            pass

        self._check_dlg = QMessageBox(self)
        self._check_dlg.setWindowTitle("检查更新")
        self._check_dlg.setText("正在检查更新，请稍候...")
        self._check_dlg.setStandardButtons(QMessageBox.Cancel)
        self._check_dlg.show()

        self._updater2 = UpdateChecker()
        self._updater2.update_available.connect(self._on_update_available)
        self._updater2.no_update.connect(self._on_no_update)
        self._updater2.check_error.connect(self._on_check_error)
        self._updater2.start()

    def _on_no_update(self):
        try:
            self._check_dlg.close()
        except Exception:
            pass
        QMessageBox.information(self, "检查更新", f"当前已是最新版本 v{VERSION} ✓")

    def _on_check_error(self, msg):
        try:
            self._check_dlg.close()
        except Exception:
            pass
        if msg == "rate_limit":
            QMessageBox.information(self, "检查更新",
                "GitHub 请求次数已达上限（每小时 60 次），请稍后再试。\n\n"
                f"当前版本: v{VERSION}")
        else:
            QMessageBox.warning(self, "检查更新失败", f"无法连接到 GitHub:\n{msg}")

    def _on_update_available(self, latest_ver: str, download_url: str, notes: str):
        """有新版本时弹提示"""
        try:
            self._check_dlg.close()
        except Exception:
            pass

        notes_short = notes[:300] + "..." if len(notes) > 300 else notes
        msg = (f"发现新版本 v{latest_ver}（当前 v{VERSION}）\n\n"
               f"{notes_short}\n\n是否立即下载更新？")
        ret = QMessageBox.question(self, "发现新版本", msg,
                                   QMessageBox.Yes | QMessageBox.No)
        if ret != QMessageBox.Yes:
            return

        self._start_download(latest_ver, download_url)

    def _start_download(self, ver: str, url: str):
        """弹下载进度对话框，后台下载"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        self._dl_dialog = QDialog(self)
        self._dl_dialog.setWindowTitle(f"下载 v{ver}")
        self._dl_dialog.setFixedSize(380, 100)
        self._dl_dialog.setWindowFlags(
            self._dl_dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dv = QVBoxLayout(self._dl_dialog)
        lbl = QLabel(f"正在下载 GIFTool v{ver}...")
        bar = QProgressBar()
        bar.setRange(0, 100)
        dv.addWidget(lbl)
        dv.addWidget(bar)

        # 下载到当前 EXE 同目录
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        dest = os.path.join(base_dir, "GIFTool_update.exe")

        self._downloader = DownloadThread(url, dest)
        self._downloader.progress.connect(bar.setValue)
        self._downloader.finished.connect(lambda p: self._on_download_done(p, ver))
        self._downloader.dl_error.connect(self._on_download_error)
        self._downloader.start()
        self._dl_dialog.exec()

    def _on_download_done(self, new_exe: str, ver: str):
        self._dl_dialog.close()

        if not getattr(sys, "frozen", False):
            QMessageBox.information(self, "下载完成",
                                    f"新版本已下载到:\n{new_exe}\n\n"
                                    "（开发模式下请手动替换）")
            return

        current_exe = sys.executable
        base_dir = os.path.dirname(current_exe)

        try:
            if os.name == "nt":
                # Windows：bat 脚本自替换
                # 策略：ren 旧→bak，ren 新→正式名，start 新，延迟删 bak
                # 避免 del /f /q 在文件锁未释放时失败导致 ren 也失败
                script_path = os.path.join(base_dir, "_giftool_update.bat")
                target_exe  = os.path.join(base_dir, "GIFTool.exe")
                backup_exe  = os.path.join(base_dir, "GIFTool_old.exe")
                script = (
                    "@echo off\n"
                    "chcp 65001 >nul\n"
                    # 等旧进程释放文件锁（约 4 秒）
                    "ping -n 5 127.0.0.1 >nul\n"
                    # 先把旧 exe 重命名为 _old（rename 不需要删除即可执行）
                    f'if exist "{backup_exe}" del /f /q "{backup_exe}"\n'
                    f'ren "{current_exe}" "GIFTool_old.exe"\n'
                    # 把下载的新文件重命名为正式名
                    f'ren "{new_exe}" "GIFTool.exe"\n'
                    # 启动新版本
                    f'start "" "{target_exe}"\n'
                    # 稍等新进程启动后删除备份和脚本
                    "ping -n 3 127.0.0.1 >nul\n"
                    f'del /f /q "{backup_exe}"\n'
                    'del /f /q "%~f0"\n'
                )
                with open(script_path, "w", encoding="gbk", errors="replace") as f:
                    f.write(script)
                subprocess.Popen(
                    ["cmd", "/c", script_path],
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
                )
            else:
                # macOS / Linux：sh 脚本自替换
                script_path = os.path.join(base_dir, "_giftool_update.sh")
                script = (
                    "#!/bin/bash\n"
                    "sleep 2\n"
                    f'rm -f "{current_exe}"\n'
                    f'mv "{new_exe}" "{current_exe}"\n'
                    f'chmod +x "{current_exe}"\n'
                    f'open "{current_exe}"\n'
                    f'rm -f "$0"\n'
                )
                with open(script_path, "w") as f:
                    f.write(script)
                os.chmod(script_path, 0o755)
                subprocess.Popen(["bash", script_path])

            QApplication.instance().quit()
        except Exception as ex:
            QMessageBox.critical(self, "更新失败",
                                 f"无法写入更新脚本:\n{ex}\n\n"
                                 f"请手动将以下文件替换原 EXE:\n{new_exe}")

    def _on_download_error(self, msg):
        self._dl_dialog.close()
        QMessageBox.critical(self, "下载失败", f"下载出错:\n{msg}")

    def _apply_theme(self, theme: str):
        self._current_theme = theme
        app = QApplication.instance()
        if theme == "dark":
            app.setStyleSheet(DARK_STYLE)
        else:
            app.setStyleSheet(LIGHT_STYLE)
        # 同步更新三个 Tab 的播放按钮图标
        self.video_tab.player.apply_theme_icons(theme)
        self.record_tab.player.apply_theme_icons(theme)
        self.gif_tab.player.apply_theme_icons(theme)
        # 同步更新时间范围栏预览按钮图标
        self.video_tab.range_w.apply_theme_icons(theme)
        self.record_tab.range_w.apply_theme_icons(theme)
        self.gif_tab.range_w.apply_theme_icons(theme)
        # 设置按钮图标保持不变（两主题相同）
        _set_btn_icon(self.settings_btn, ICON_SETTINGS, size=20)


# ───────────────────────────── Entry Point ────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_STYLE)
    app.setFont(QFont("Segoe UI", 10))

    # Set app icon if logo.ico exists
    base = Path(__file__).parent
    for ico in ("logo.ico", "logo.jpg", "logo.png"):
        p = base / ico
        if p.exists():
            from PySide6.QtGui import QIcon
            app.setWindowIcon(QIcon(str(p)))
            break

    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
