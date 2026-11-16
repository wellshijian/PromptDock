# -*- coding: utf-8 -*-
import sys
import os
import json
import uuid
import time
from PySide6.QtCore import Qt, QRect, QDate, QDateTime, QTimer, QEvent
from PySide6.QtGui import QColor, QFont, QCursor, QTextCharFormat, QIcon
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QWidget, QFrame, QMessageBox, QAbstractItemView,
    QToolTip, QDateEdit, QCalendarWidget, QMenu
)

APP_NAME = "PromptDock"
IS_WINDOWS = sys.platform == "win32"
WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def get_data_dir():
    base = os.environ.get("APPDATA", os.path.expanduser("~")) if IS_WINDOWS else os.path.expanduser("~")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d

SCHEDULE_FILE = os.path.join(get_data_dir(), "schedules.json")
PEOPLE_FILE = os.path.join(get_data_dir(), "schedule_people.json")
THEME_FILE = os.path.join(get_data_dir(), "schedule_theme.json")

def load_theme():
    data = _load_json(THEME_FILE, {"theme": "dark"})
    return data.get("theme", "dark") if isinstance(data, dict) else "dark"

def save_theme(name):
    _save_json(THEME_FILE, {"theme": name})

STATUS = {
    "pending": ("未开始", "#9399b2", "rgba(147,153,178,0.16)"),
    "doing":   ("进行中", "#fab387", "rgba(250,179,135,0.16)"),
    "done":    ("已完成", "#a6e3a1", "rgba(166,227,161,0.16)"),
}
STATUS_ORDER = {"pending": 0, "doing": 1, "done": 2}
NEXT_STATUS = {"pending": "doing", "doing": "done", "done": "pending"}

def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, type(default)) else default
    except Exception:
        return default

def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_schedules():
    items = _load_json(SCHEDULE_FILE, [])
    done_items = [x for x in items if isinstance(x, dict) and x.get("status") == "done"]
    other_items = [x for x in items if isinstance(x, dict) and x.get("status") != "done"]
    return done_items + other_items
def save_schedules(s): _save_json(SCHEDULE_FILE, s)
def load_people(): return _load_json(PEOPLE_FILE, [])
def save_people(p): _save_json(PEOPLE_FILE, p)

def parse_date(s):
    s = (s or "").strip()
    for fmt in ("yyyy-MM-dd", "yyyy-MM-dd HH:mm"):
        d = QDate.fromString(s[:len(fmt)] if fmt == "yyyy-MM-dd" else s, fmt)
        if d.isValid():
            return d
    return QDate()

def fmt_date(d):
    if not d.isValid():
        return "未设置"
    return f"{d.month()}/{d.day()} {WEEK[d.dayOfWeek() - 1]}"

_FUSION = None
def fusion_style():
    global _FUSION
    if _FUSION is None:
        from PySide6.QtWidgets import QStyleFactory
        _FUSION = QStyleFactory.create("Fusion")
    return _FUSION

def style_calendar(cal, theme="dark"):
    cal.setGridVisible(False)
    cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
    cal.setFirstDayOfWeek(Qt.Monday)
    fmt = QTextCharFormat()
    fmt.setForeground(QColor("#ffffff"))
    fmt.setBackground(QColor("#e8762b"))
    fmt.setFontWeight(QFont.Bold)
    cal.setDateTextFormat(QDate.currentDate(), fmt)
    cal.setStyle(fusion_style())
    if theme == "light":
        cal.setStyleSheet("""
            QCalendarWidget QWidget#qt_calendar_navigationbar {background:#e8eaf0;}
            QCalendarWidget QToolButton {color:#1e1e2e; background:transparent; font-weight:bold; padding:4px 8px;}
            QCalendarWidget QToolButton:hover {background:#d5d8e3; border-radius:6px;}
            QCalendarWidget QAbstractItemView {background:#ffffff; color:#1e1e2e; selection-background-color:#6c5ce7; selection-color:#fff; outline:0;}
            QCalendarWidget QAbstractItemView:disabled {color:#9ca0b0;}
        """)
    else:
        cal.setStyleSheet("""
            QCalendarWidget QWidget#qt_calendar_navigationbar {background:#2b2d42;}
            QCalendarWidget QToolButton {color:#fff; background:transparent; font-weight:bold; padding:4px 8px;}
            QCalendarWidget QToolButton:hover {background:#3b3d54; border-radius:6px;}
            QCalendarWidget QAbstractItemView {background:#1f2033; color:#cdd6f4; selection-background-color:#6c5ce7; selection-color:#fff; outline:0;}
            QCalendarWidget QAbstractItemView:disabled {color:#585b70;}
        """)



class ScheduleTable(QTableWidget):
    """拖拽排序：在 Python 里接管 drop，避免 C++ 默认 InternalMove 搞乱单元格。"""
    def __init__(self, pad, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pad = pad
        self._drag_row = -1

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            self._drag_row = self.rowAt(pos.y())
            # 只有按住序号列才拖拽排序，其它列留给多选
            self.setDragEnabled(self.columnAt(pos.x()) == 0)
        super().mousePressEvent(event)

    def dropEvent(self, event):
        self._pad._on_table_drop(event, self._drag_row)
        # 不调用 super，避免默认移动破坏 cell widget


class SchedulePadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任务排期表 - PromptDock")
        self.resize(900, 580)
        self.setMinimumSize(780, 440)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self._apply_window_icon(parent)
        self.schedules = load_schedules()
        self.people = load_people()
        self.current_filter = "all"
        self.sort_col, self.sort_desc = None, False  # None=手动顺序（拖拽）
        self.theme = load_theme()
        if self.theme not in ("dark", "light"):
            self.theme = "dark"
        self._init_style()
        self._init_ui()
        self._refresh_table()


    def _apply_window_icon(self, parent):
        icon = QIcon()
        candidates = []
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", "")
            if meipass:
                candidates += [
                    os.path.join(meipass, "icon.ico"),
                    os.path.join(meipass, "icon_src.png"),
                ]
            candidates.append(sys.executable)
            here = os.path.dirname(sys.executable)
        else:
            here = os.path.dirname(os.path.abspath(__file__))
        candidates += [
            os.path.join(here, "icon.ico"),
            os.path.join(here, "icon_src.png"),
            os.path.join(here, "..", "icon.ico"),
            os.path.join(here, "dist", "icon.ico"),
        ]
        if parent is not None and not parent.windowIcon().isNull():
            icon = parent.windowIcon()
        if icon.isNull():
            for path in candidates:
                path = os.path.normpath(path)
                if path and os.path.exists(path):
                    cand = QIcon(path)
                    if not cand.isNull():
                        icon = cand
                        break
        if not icon.isNull():
            self.setWindowIcon(icon)
            app = QApplication.instance()
            if app is not None and app.windowIcon().isNull():
                app.setWindowIcon(icon)
        self._icon_file = None
        for path in candidates:
            path = os.path.normpath(path)
            if path.lower().endswith('.ico') and os.path.exists(path):
                self._icon_file = path
                break

    def _force_taskbar_icon(self):
        """Windows 任务栏对全透明图标常显示白纸，需不透明 ico + WM_SETICON。"""
        if not IS_WINDOWS:
            return
        paths = []
        p0 = getattr(self, '_icon_file', None)
        if p0:
            paths.append(p0)
        if getattr(sys, 'frozen', False):
            mei = getattr(sys, '_MEIPASS', '')
            if mei:
                paths += [os.path.join(mei, 'icon.ico'), os.path.join(mei, 'icon_taskbar.png')]
            paths.append(sys.executable)
        here = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
        paths += [os.path.join(here, 'icon.ico'), os.path.join(here, 'icon_taskbar.png')]
        path = next((os.path.normpath(x) for x in paths if x and os.path.exists(x) and str(x).lower().endswith(('.ico', '.png', '.exe'))), None)
        if not path:
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x0010
            WM_SETICON = 0x0080
            ICON_SMALL, ICON_BIG = 0, 1
            hwnd = int(self.winId())
            # 先设 Qt 图标
            ic = QIcon(path if not path.lower().endswith('.exe') else path)
            if not ic.isNull():
                self.setWindowIcon(ic)
            if path.lower().endswith('.exe'):
                # 从 exe 取图标
                large = ctypes.c_void_p()
                small = ctypes.c_void_p()
                ctypes.windll.shell32.ExtractIconExW(path, 0, ctypes.byref(large), ctypes.byref(small), 1)
                if large.value:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, large.value)
                if small.value:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small.value)
                return
            for size, which in ((256, ICON_BIG), (32, ICON_BIG), (16, ICON_SMALL)):
                hicon = user32.LoadImageW(None, path, IMAGE_ICON, size if path.lower().endswith('.ico') else 0, size if path.lower().endswith('.ico') else 0, LR_LOADFROMFILE)
                if hicon:
                    user32.SendMessageW(hwnd, WM_SETICON, which, hicon)
        except Exception:
            pass

    def showEvent(self, e):
        super().showEvent(e)
        self.schedules = load_schedules()
        self.people = load_people()
        self._set_new_date(QDate.currentDate())
        self._refresh_table()
        # 避免一进来就聚焦可编辑的比例框，看起来像在改 16:9
        if hasattr(self, "input_content"):
            self.input_content.setFocus(Qt.OtherFocusReason)
        QTimer.singleShot(0, self._force_taskbar_icon)
        QTimer.singleShot(200, self._force_taskbar_icon)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Key_Delete:
            self._delete_selected()
        else:
            super().keyPressEvent(e)

    def _save_my_pos(self):
        p = self.parent()
        if p is not None and hasattr(p, "settings") and isinstance(p.settings, dict):
            pos = self.pos()
            p.settings["schedule_x"] = pos.x()
            p.settings["schedule_y"] = pos.y()
            _save_json(os.path.join(get_data_dir(), "settings.json"), p.settings)

    def moveEvent(self, e):
        super().moveEvent(e)
        if self.isVisible() and not self.isMinimized():
            self._save_my_pos()

    def closeEvent(self, e):
        self._save_my_pos()
        save_schedules(self.schedules)
        super().closeEvent(e)

    def changeEvent(self, e):
        # 保留：真正拦截在 nativeEvent，这里兜底
        if e.type() == QEvent.WindowStateChange and self.windowState() & Qt.WindowMinimized:
            self.setWindowState(Qt.WindowNoState)
            QTimer.singleShot(0, self.close)
            return
        super().changeEvent(e)

    def nativeEvent(self, eventType, message):
        # 点标题栏最小化时直接关闭，不走系统最小化动画，避免闪一下
        if IS_WINDOWS:
            try:
                import ctypes
                from ctypes import wintypes
                et = bytes(eventType) if not isinstance(eventType, (bytes, bytearray)) else eventType
                if et in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
                    msg = wintypes.MSG.from_address(int(message))
                    WM_SYSCOMMAND = 0x0112
                    SC_MINIMIZE = 0xF020
                    if msg.message == WM_SYSCOMMAND and (msg.wParam & 0xFFF0) == SC_MINIMIZE:
                        QTimer.singleShot(0, self.close)
                        return True, 0
            except Exception:
                pass
        return super().nativeEvent(eventType, message)

    def eventFilter(self, obj, event):
        # 比例框：默认只读显示，避免一打开就像在改 16:9；双击可手改，下拉可选
        if hasattr(self, "combo_ratio"):
            le = self.combo_ratio.lineEdit()
            if obj is le:
                if event.type() == QEvent.MouseButtonDblClick:
                    le.setReadOnly(False)
                    le.selectAll()
                elif event.type() == QEvent.FocusOut:
                    le.setReadOnly(True)
                    le.deselect()
            elif obj is self.combo_ratio and event.type() == QEvent.MouseButtonPress:
                # 点开下拉前清掉反白，看起来不像正在编辑
                le.deselect()
        return super().eventFilter(obj, event)

    def _palette(self):
        if self.theme == "light":
            return {
                "title": "#1e1e2e", "muted": "#6c7086", "text": "#1e1e2e",
                "content": "#11111b", "content_done": "#9ca0b0",
                "idx": "#8b90a5", "ratio": "#1e66f5", "date": "#e8762b",
                "date_empty": "#6c7086", "person": "#1e1e2e", "person_empty": "#9ca0b0",
                "clear_btn": "QPushButton{color:#d20f39;} QPushButton:hover{background:#fce8ec; color:#d20f39;}",
                "date_btn": "QPushButton{color:#e8762b; font-weight:bold;}",
                "menu": "QMenu{background:#ffffff; border:1px solid #d5d8e3; padding:6px;}",
                "menu_head": "color:#e8762b; font-weight:bold; font-size:13px;",
                "today_btn": "QPushButton{background:#e8762b; color:#fff; border:none; border-radius:6px; min-height:30px; font-weight:bold;}",
                "theme_btn": "QPushButton{background:transparent; border:1px solid #d5d8e3; border-radius:8px; font-size:16px; min-height:34px; min-width:34px; padding:0;}"
            }
        return {
            "title": "#fff", "muted": "#7f849c", "text": "#cdd6f4",
            "content": "#ffffff", "content_done": "#6c7086",
            "idx": "#7f849c", "ratio": "#89b4fa", "date": "#e8762b",
            "date_empty": "#a6adc8", "person": "#cdd6f4", "person_empty": "#585b70",
            "clear_btn": "QPushButton{color:#f38ba8;} QPushButton:hover{background:#4b2d3a; color:#fff;}",
            "date_btn": "QPushButton{color:#e8762b; font-weight:bold;}",
            "menu": "QMenu{background:#1f2033; border:1px solid #3b3d54; padding:6px;}",
            "menu_head": "color:#e8762b; font-weight:bold; font-size:13px;",
            "today_btn": "QPushButton{background:#e8762b; color:#fff; border:none; border-radius:6px; min-height:30px; font-weight:bold;}",
            "theme_btn": "QPushButton{background:transparent; border:1px solid #3b3d54; border-radius:8px; font-size:16px; min-height:34px; min-width:34px; padding:0;}"
        }

    def _init_style(self):
        if self.theme == "light":
            self.setStyleSheet("""
                QDialog {background:#f5f6fa; color:#1e1e2e; font-family:"Microsoft YaHei","PingFang SC","Segoe UI",sans-serif; font-size:13px;}
                QLabel {color:#1e1e2e;}
                QLineEdit, QComboBox, QDateEdit {background:#ffffff; border:1px solid #d5d8e3; border-radius:8px;
                    padding:0 10px; min-height:34px; color:#1e1e2e; selection-background-color:#6c5ce7;}
                QLineEdit:focus, QComboBox:focus, QDateEdit:focus {border:1px solid #6c5ce7;}
                QComboBox::drop-down, QDateEdit::drop-down {border:none; width:20px;}
                QComboBox QAbstractItemView {background:#ffffff; color:#1e1e2e; selection-background-color:#6c5ce7; selection-color:#fff; border:1px solid #d5d8e3; outline:0;}
                QPushButton {background:#ffffff; color:#1e1e2e; border:1px solid #d5d8e3; border-radius:8px; padding:0 14px; min-height:34px;}
                QPushButton:hover {background:#eceef5; color:#111;}
                QPushButton#Primary {background:#6c5ce7; border:none; color:#fff; font-weight:bold;}
                QPushButton#Primary:hover {background:#7d6ef0;}
                QPushButton#TabActive {background:#6c5ce7; border:none; color:#fff; font-weight:bold;}
                QTableWidget {background:#ffffff; border:1px solid #d5d8e3; border-radius:10px; gridline-color:transparent;
                    color:#1e1e2e; selection-background-color:#e8eaf8; selection-color:#1e1e2e; outline:0;}
                QTableWidget::item {border:none; border-bottom:1px solid #eceef3; padding:4px;}
                QTableWidget::item:hover {background:#f0f2f8;}
                QHeaderView::section {background:#eef0f6; color:#5c6178; padding:8px 4px; border:none; border-bottom:1px solid #d5d8e3; font-weight:bold;}
                QHeaderView::section:hover {color:#1e1e2e;}
                QMenu {background:#ffffff; color:#1e1e2e; border:1px solid #d5d8e3; padding:4px;}
                QMenu::item {padding:6px 20px; border-radius:4px;}
                QMenu::item:selected {background:#6c5ce7; color:#fff;}
            """)
        else:
            self.setStyleSheet("""
                QDialog {background:#1e1e2e; color:#cdd6f4; font-family:"Microsoft YaHei","PingFang SC","Segoe UI",sans-serif; font-size:13px;}
                QLabel {color:#cdd6f4;}
                QLineEdit, QComboBox, QDateEdit {background:#2b2d42; border:1px solid #3b3d54; border-radius:8px;
                    padding:0 10px; min-height:34px; color:#fff; selection-background-color:#6c5ce7;}
                QLineEdit:focus, QComboBox:focus, QDateEdit:focus {border:1px solid #8075e8;}
                QComboBox::drop-down, QDateEdit::drop-down {border:none; width:20px;}
                QComboBox QAbstractItemView {background:#2b2d42; color:#fff; selection-background-color:#6c5ce7; border:1px solid #3b3d54; outline:0;}
                QPushButton {background:#2b2d42; color:#cdd6f4; border:1px solid #3b3d54; border-radius:8px; padding:0 14px; min-height:34px;}
                QPushButton:hover {background:#3b3d54; color:#fff;}
                QPushButton#Primary {background:#6c5ce7; border:none; color:#fff; font-weight:bold;}
                QPushButton#Primary:hover {background:#7d6ef0;}
                QPushButton#TabActive {background:#6c5ce7; border:none; color:#fff; font-weight:bold;}
                QTableWidget {background:#1a1a28; border:1px solid #2e3046; border-radius:10px; gridline-color:transparent;
                    color:#cdd6f4; selection-background-color:#2f3150; selection-color:#fff; outline:0;}
                QTableWidget::item {border:none; border-bottom:1px solid #26283a; padding:4px;}
                QTableWidget::item:hover {background:#24263a;}
                QHeaderView::section {background:#242638; color:#a6adc8; padding:8px 4px; border:none; border-bottom:1px solid #363a4f; font-weight:bold;}
                QHeaderView::section:hover {color:#fff;}
                QMenu {background:#2b2d42; color:#fff; border:1px solid #3b3d54; padding:4px;}
                QMenu::item {padding:6px 20px; border-radius:4px;}
                QMenu::item:selected {background:#6c5ce7;}
            """)

    def _init_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(16, 14, 16, 12)
        main.setSpacing(10)

        # 第一行：标题 + 添加人员
        top = QHBoxLayout()
        self.title_label = QLabel("任务排期表")
        top.addWidget(self.title_label)
        self.summary = QLabel("")
        top.addWidget(self.summary)
        top.addStretch(1)
        self.btn_theme = QPushButton()
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setFixedSize(36, 34)
        self.btn_theme.setToolTip("切换白天 / 黑夜主题")
        self.btn_theme.clicked.connect(self._toggle_theme)
        top.addWidget(self.btn_theme)
        self._sync_theme_button()
        main.addLayout(top)

        # 第二行：新建任务
        add = QHBoxLayout()
        add.setSpacing(8)
        self.input_content = QLineEdit()
        self.input_content.setPlaceholderText("输入视频内容后回车添加")
        self.input_content.returnPressed.connect(self._on_add_task)
        self.input_content.setFocusPolicy(Qt.StrongFocus)
        add.addWidget(self.input_content, 1)
        self.combo_ratio = QComboBox()
        self.combo_ratio.setEditable(True)
        self.combo_ratio.addItems(["16:9", "9:16", "1:1", "4:3", "2.35:1"])
        self.combo_ratio.setFixedWidth(96)
        self.combo_ratio.lineEdit().setAlignment(Qt.AlignCenter)
        # 点击才聚焦，避免窗口一开就进入编辑态
        self.combo_ratio.setFocusPolicy(Qt.ClickFocus)
        self.combo_ratio.lineEdit().setFocusPolicy(Qt.ClickFocus)
        self.combo_ratio.lineEdit().setReadOnly(True)
        self.combo_ratio.lineEdit().installEventFilter(self)
        self.combo_ratio.installEventFilter(self)
        add.addWidget(self.combo_ratio)
        self.new_date = QDate.currentDate()
        self.btn_date = QPushButton()
        self.btn_date.setFixedWidth(160)
        self.btn_date.setCursor(Qt.PointingHandCursor)
        self.btn_date.clicked.connect(lambda: self._pick_date(self.btn_date, self.new_date, self._set_new_date))
        add.addWidget(self.btn_date)
        btn_add = QPushButton("＋ 添加任务")
        btn_add.setObjectName("Primary")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._on_add_task)
        add.addWidget(btn_add)
        main.addLayout(add)
        self._set_new_date(QDate.currentDate())

        # 第三行：筛选 + 搜索 + 工具
        row = QHBoxLayout()
        row.setSpacing(6)
        self.tabs = {}
        for key, label in [("all", "全部"), ("pending", "未开始"), ("doing", "进行中"), ("done", "已完成")]:
            b = QPushButton(label)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, k=key: self._set_filter(k))
            self.tabs[key] = b
            row.addWidget(b)
        row.addStretch(1)
        b_copy = QPushButton("复制全部")
        b_copy.setCursor(Qt.PointingHandCursor)
        b_copy.clicked.connect(self._copy_schedule_table)
        row.addWidget(b_copy)
        self.btn_clear_done = QPushButton("清理已完成")
        self.btn_clear_done.setCursor(Qt.PointingHandCursor)
        self.btn_clear_done.clicked.connect(self._clear_done_tasks)
        row.addWidget(self.btn_clear_done)
        main.addLayout(row)

        # 表格：序号 / 视频内容 / 比例 / 结束时间 / 状态 / 人员
        self.headers = ["序号", "视频内容", "比例", "结束时间", "状态", "操作"]
        self.table = ScheduleTable(self, 0, len(self.headers))
        hh = self.table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignCenter)
        hh.setSectionResizeMode(QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        for col, w in [(0, 56), (2, 80), (3, 150), (4, 100), (5, 130)]:
            self.table.setColumnWidth(col, w)
        hh.sectionClicked.connect(self._on_header_clicked)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setShowGrid(False)
        self.table.setStyle(fusion_style())
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.cellChanged.connect(self._on_cell_changed)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDropIndicatorShown(True)
        self.table.setDragDropMode(QAbstractItemView.InternalMove)
        self.table.setDefaultDropAction(Qt.MoveAction)
        self.table.setDragDropOverwriteMode(False)
        main.addWidget(self.table, 1)

        self._update_tabs()
        self._apply_chrome_colors()

    # ---------- 拖拽排序 ----------
    def _on_table_drop(self, event, drag_row):
        if self.current_filter != "all":
            self._tip("请先切到「全部」再拖拽改序号")
            event.ignore()
            return
        src = self.table.currentRow()
        if src < 0:
            src = drag_row
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        dst = self.table.rowAt(pos.y())
        if dst < 0:
            dst = self.table.rowCount() - 1
        ind = self.table.dropIndicatorPosition()
        insert_at = dst + 1 if ind == QAbstractItemView.BelowItem else dst
        event.acceptProposedAction()
        if src < 0 or self.table.rowCount() == 0:
            return
        ids = []
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 0)
            if it:
                ids.append(it.data(Qt.UserRole))
        if src >= len(ids):
            return
        tid = ids.pop(src)
        if insert_at > src:
            insert_at -= 1
        insert_at = max(0, min(insert_at, len(ids)))
        ids.insert(insert_at, tid)
        by_id = {s.get("id"): s for s in self.schedules}
        seen = set(ids)
        self.schedules = [by_id[i] for i in ids if i in by_id] + [s for s in self.schedules if s.get("id") not in seen]
        self.sort_col = None
        save_schedules(self.schedules)
        QTimer.singleShot(0, self._refresh_table)

    # ---------- 主题 ----------
    def _sync_theme_button(self):
        if not hasattr(self, "btn_theme"):
            return
        if self.theme == "light":
            self.btn_theme.setText("☀")
            self.btn_theme.setToolTip("当前白天主题，点击切换黑夜")
        else:
            self.btn_theme.setText("☾")
            self.btn_theme.setToolTip("当前黑夜主题，点击切换白天")

    def _apply_chrome_colors(self):
        c = self._palette()
        if hasattr(self, "title_label"):
            self.title_label.setStyleSheet(f"font-size:17px; font-weight:bold; color:{c['title']};")
        if hasattr(self, "summary"):
            self.summary.setStyleSheet(f"color:{c['muted']}; margin-left:8px;")
        if hasattr(self, "btn_theme"):
            self.btn_theme.setStyleSheet(c["theme_btn"])
        if hasattr(self, "btn_clear_done"):
            self.btn_clear_done.setStyleSheet(c["clear_btn"])
        if hasattr(self, "btn_date"):
            self.btn_date.setStyleSheet(c["date_btn"])
        self._sync_theme_button()

    def _toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        save_theme(self.theme)
        self._init_style()
        self._apply_chrome_colors()
        self._update_tabs()
        self._refresh_table()

    # ---------- 工具 ----------
    def _set_new_date(self, d):
        self.new_date = d
        self.btn_date.setText(fmt_date(d))
        self.btn_date.setStyleSheet(self._palette()["date_btn"])

    def _pick_date(self, anchor, cur, on_pick, global_pos=None):
        from PySide6.QtWidgets import QWidgetAction
        menu = QMenu(self)
        c = self._palette()
        menu.setStyleSheet(c["menu"])
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)
        today = QDate.currentDate()
        head = QLabel(f"今天：{today.month()}月{today.day()}日 {WEEK[today.dayOfWeek()-1]}")
        head.setAlignment(Qt.AlignCenter)
        head.setStyleSheet(c["menu_head"])
        lay.addWidget(head)
        cal = QCalendarWidget()
        style_calendar(cal, self.theme)
        cal.setMinimumSize(300, 230)
        cal.setSelectedDate(cur if cur.isValid() else today)
        lay.addWidget(cal)
        bt = QPushButton("回到今天")
        bt.setCursor(Qt.PointingHandCursor)
        bt.setStyleSheet(c["today_btn"])
        lay.addWidget(bt)
        act = QWidgetAction(menu)
        act.setDefaultWidget(box)
        menu.addAction(act)
        def done(d):
            on_pick(d)
            menu.close()
        cal.clicked.connect(done)
        bt.clicked.connect(lambda: done(today))
        pos = global_pos or anchor.mapToGlobal(anchor.rect().bottomLeft())
        menu.exec(pos)

    def _find(self, tid):
        return next((s for s in self.schedules if s.get("id") == tid), None)

    def _center(self, w):
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(w)
        return box

    def _tip(self, text):
        QToolTip.showText(QCursor.pos(), text, self, QRect(), 1500)

    # ---------- 过滤 / 排序 ----------
    def _set_filter(self, k):
        self.current_filter = k
        self._update_tabs()
        self._refresh_table()

    def _update_tabs(self):
        for k, b in self.tabs.items():
            b.setObjectName("TabActive" if k == self.current_filter else "")
            b.style().unpolish(b)
            b.style().polish(b)

    def _on_header_clicked(self, col):
        if col == 0:
            self.sort_col, self.sort_desc = None, False
            self._refresh_table()
            return
        if col not in (1, 2, 3, 4, 5):
            return
        if self.sort_col == col:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_col, self.sort_desc = col, False
        self._refresh_table()

    def _sorted(self, items):
        c = self.sort_col
        if c is None:
            order = {s.get("id"): i for i, s in enumerate(self.schedules)}
            return sorted(items, key=lambda s: order.get(s.get("id"), 10**9))
        far = QDate(9999, 12, 31)
        keyf = {
            1: lambda s: s.get("content", ""),
            2: lambda s: s.get("ratio", ""),
            3: lambda s: (parse_date(s.get("deadline")) if parse_date(s.get("deadline")).isValid() else far).toJulianDay(),
            4: lambda s: STATUS_ORDER.get(s.get("status", "pending"), 0),
            5: lambda s: s.get("person") or "\uffff",
        }.get(c, lambda s: s.get("created_at", 0))
        return sorted(items, key=keyf, reverse=self.sort_desc)

    # ---------- 表格 ----------
    def _refresh_table(self):
        self.table.blockSignals(True)
        kw = ""
        rows = []
        for s in self.schedules:
            st = s.get("status", "pending")
            if self.current_filter != "all" and st != self.current_filter:
                continue
            if kw and not any(kw in str(s.get(f) or "").lower() for f in ("content", "person", "ratio")) \
                    and kw not in fmt_date(parse_date(s.get("deadline"))):
                continue
            rows.append(s)
        rows = self._sorted(rows)

        cnt = {k: sum(1 for s in self.schedules if s.get("status", "pending") == k) for k in STATUS}
        self.summary.setText(f"共 {len(self.schedules)} 项")
        self.tabs["all"].setText(f"全部 {len(self.schedules)}")
        for k in STATUS:
            self.tabs[k].setText(f"{STATUS[k][0]} {cnt[k]}")
        for i, h in enumerate(self.headers):
            arrow = (" ↓" if self.sort_desc else " ↑") if i == self.sort_col else ""
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(h + arrow))

        self.table.clearContents()
        self.table.setRowCount(len(rows))
        today = QDate.currentDate()
        for r, s in enumerate(rows):
            tid = s.get("id")
            done = s.get("status") == "done"

            def cell(text, color="#cdd6f4", editable=False):
                it = QTableWidgetItem(text)
                it.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                it.setData(Qt.UserRole, tid)
                it.setForeground(QColor(color))
                flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
                if editable:
                    flags |= Qt.ItemIsEditable
                it.setFlags(flags)
                return it

            pal = self._palette()
            self.table.setItem(r, 0, cell(str(r + 1), pal["idx"]))

            c = cell(s.get("content", ""), pal["content_done"] if done else pal["content"], editable=True)
            f = QFont(); f.setStrikeOut(done); f.setBold(not done)
            c.setFont(f)
            c.setToolTip(s.get("content", ""))
            self.table.setItem(r, 1, c)

            self.table.setItem(r, 2, cell(s.get("ratio", "16:9"), pal["ratio"]))

            d = parse_date(s.get("deadline"))
            dcol = pal["date"] if d.isValid() else pal["date_empty"]
            if d.isValid() and not done and d < today:
                dcol = "#f38ba8" if self.theme == "dark" else "#d20f39"
            self.table.setItem(r, 3, cell(fmt_date(d), dcol))

            name, fg, bg = STATUS.get(s.get("status", "pending"), STATUS["pending"])
            sb = QPushButton(name)
            sb.setCursor(Qt.PointingHandCursor)
            sb.setFixedSize(76, 26)
            sb.setStyleSheet(f"QPushButton{{background:{bg}; color:{fg}; border:none; border-radius:13px; font-weight:bold; min-height:0; padding:0;}}")
            sb.clicked.connect(lambda _, t=tid: self._cycle_status(t))
            self.table.setCellWidget(r, 4, self._center(sb))

            person = s.get("person", "")
            self.table.setItem(r, 5, cell(person, pal["person"] if person else pal["person_empty"]))
        self.table.blockSignals(False)

    def _on_cell_clicked(self, row, col):
        it = self.table.item(row, col)
        if not it:
            return
        tid = it.data(Qt.UserRole)
        s = self._find(tid)
        if col == 3:
            d = parse_date(s.get("deadline") if s else "")
            def picked(date):
                self._set_field(tid, "deadline", date.toString("yyyy-MM-dd"))
                QTimer.singleShot(0, self._refresh_table)
            rect = self.table.visualItemRect(it)
            self._pick_date(self.table, d, picked, self.table.viewport().mapToGlobal(rect.bottomLeft()))
        elif col == 2:
            self._ratio_pick_menu(tid, self.table.viewport().mapToGlobal(self.table.visualItemRect(it).bottomLeft()))
        elif col == 5:
            self._person_pick_menu(tid, self.table.viewport().mapToGlobal(self.table.visualItemRect(it).bottomLeft()))

    def _on_context_menu(self, pos):
        it = self.table.itemAt(pos)
        col = self.table.columnAt(pos.x())
        if it is None:
            r = self.table.rowAt(pos.y())
            it = self.table.item(r, 0) if r >= 0 else None
        tid = it.data(Qt.UserRole) if it else None
        if not tid:
            return
        # 右键行若未在选中里，则只选这一行
        row = it.row()
        selected_rows = {i.row() for i in self.table.selectedIndexes()}
        if row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(row)

        menu = QMenu(self)
        a_add = None
        if col == 5:
            a_add = menu.addAction("添加人员")
            if self.people:
                menu.addSeparator()
                for p in self.people:
                    menu.addAction(p)
                menu.addSeparator()
                a_clear = menu.addAction("清空人员")
            else:
                a_clear = None
            menu.addSeparator()
        else:
            a_clear = None

        n = len(self._selected_tids())
        a_copy = menu.addAction("复制内容")
        a_del = menu.addAction(f"删除选中（{n}）" if n > 1 else "删除任务")
        act = menu.exec(self.table.viewport().mapToGlobal(pos))
        if act is None:
            return
        s = self._find(tid)
        if not s:
            return
        if a_add is not None and act == a_add:
            self._prompt_add_person(tid)
            return
        if a_clear is not None and act == a_clear:
            self._set_field(tid, "person", "")
            self._refresh_table()
            return
        if act.text() in self.people:
            self._set_field(tid, "person", act.text())
            self._refresh_table()
            return
        if act == a_del:
            self._delete_selected()
        elif act == a_copy:
            QApplication.clipboard().setText(s.get("content", ""))
            self._tip("已复制")

    # ---------- 增删改 ----------
    def _selected_tids(self):
        tids = []
        seen = set()
        for it in self.table.selectedItems():
            tid = it.data(Qt.UserRole)
            if tid and tid not in seen:
                seen.add(tid)
                tids.append(tid)
        if not tids:
            rows = sorted({i.row() for i in self.table.selectedIndexes()})
            for r in rows:
                it = self.table.item(r, 0)
                if it:
                    tid = it.data(Qt.UserRole)
                    if tid and tid not in seen:
                        seen.add(tid)
                        tids.append(tid)
        return tids

    def _delete_selected(self):
        tids = self._selected_tids()
        if not tids:
            return
        if len(tids) == 1:
            s = self._find(tids[0])
            msg = f"确定删除任务？\n\n{(s or {}).get('content','')}"
        else:
            msg = f"确定删除选中的 {len(tids)} 项任务？\n此操作无法撤销。"
        r = QMessageBox.question(self, "确认删除", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        kill = set(tids)
        self.schedules = [s for s in self.schedules if s.get("id") not in kill]
        save_schedules(self.schedules)
        self._refresh_table()

    def _on_add_task(self):
        content = self.input_content.text().strip()
        if not content:
            self.input_content.setFocus()
            return
        self.schedules.append({
            "id": str(uuid.uuid4()),
            "content": content,
            "ratio": self.combo_ratio.currentText().strip() or "16:9",
            "deadline": self.new_date.toString("yyyy-MM-dd"),
            "status": "pending",
            "person": "",
            "created_at": int(time.time()),
        })
        save_schedules(self.schedules)
        self.input_content.clear()
        self.input_content.setFocus()
        self._refresh_table()

    RATIOS = ["16:9", "9:16", "1:1", "4:3", "2.35:1"]

    def _ratio_pick_menu(self, tid, pos):
        menu = QMenu(self)
        for r in self.RATIOS:
            menu.addAction(r)
        menu.addSeparator()
        a_custom = menu.addAction("自定义…")
        act = menu.exec(pos)
        if act is None:
            return
        if act == a_custom:
            from PySide6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, "比例", "输入比例：", text=self._find(tid).get("ratio", "16:9") if self._find(tid) else "16:9")
            text = text.strip()
            if ok and text:
                self._set_field(tid, "ratio", text)
                self._refresh_table()
            return
        if act.text() in self.RATIOS:
            self._set_field(tid, "ratio", act.text())
            self._refresh_table()

    def _prompt_add_person(self, tid):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "添加人员", "人员名字：")
        name = name.strip()
        if ok and name:
            if name not in self.people:
                self.people.append(name)
                save_people(self.people)
            self._set_field(tid, "person", name)
            self._refresh_table()

    def _person_pick_menu(self, tid, pos):
        menu = QMenu(self)
        a_add = menu.addAction("添加人员")
        a_clear = None
        if self.people:
            menu.addSeparator()
            for p in self.people:
                menu.addAction(p)
            menu.addSeparator()
            a_clear = menu.addAction("清空人员")
        act = menu.exec(pos)
        if act is None:
            return
        if act == a_add:
            self._prompt_add_person(tid)
            return
        if a_clear is not None and act == a_clear:
            self._set_field(tid, "person", "")
            self._refresh_table()
            return
        if act.text() in self.people:
            self._set_field(tid, "person", act.text())
            self._refresh_table()

    def _set_field(self, tid, key, val):
        s = self._find(tid)
        if s is not None:
            s[key] = val
            save_schedules(self.schedules)

    def _cycle_status(self, tid):
        s = self._find(tid)
        if s is None:
            return
        old_status = s.get("status", "pending")
        new_status = NEXT_STATUS.get(old_status, "pending")
        s["status"] = new_status
        if new_status == "done":
            done_items = [x for x in self.schedules if x.get("status") == "done" and x.get("id") != tid]
            other_items = [x for x in self.schedules if x.get("status") != "done" and x.get("id") != tid]
            self.schedules = done_items + [s] + other_items
            self.sort_col = None
        elif old_status == "done":
            done_items = [x for x in self.schedules if x.get("status") == "done"]
            other_items = [x for x in self.schedules if x.get("status") != "done"]
            self.schedules = done_items + other_items
            self.sort_col = None
        save_schedules(self.schedules)
        QTimer.singleShot(0, self._refresh_table)

    def _on_cell_changed(self, row, col):
        if col == 1:
            it = self.table.item(row, 1)
            if it:
                it.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self._set_field(it.data(Qt.UserRole), "content", it.text().strip())

    def _clear_done_tasks(self):
        n = sum(1 for s in self.schedules if s.get("status") == "done")
        if not n:
            self._tip("没有已完成的任务")
            return
        r = QMessageBox.question(
            self, "清理已完成",
            f"确定删除 {n} 项已完成任务？\n此操作无法撤销。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        self.schedules = [s for s in self.schedules if s.get("status") != "done"]
        save_schedules(self.schedules)
        self._refresh_table()
        self._tip(f"已清理 {n} 项")

    def _copy_schedule_table(self):
        if not self.schedules:
            return
        lines = ["【任务排期表】"]
        for i, s in enumerate(self._sorted(list(self.schedules)), 1):
            who = f" | {s.get('person')}" if s.get("person") else ""
            st = STATUS.get(s.get("status", "pending"), STATUS["pending"])[0]
            lines.append(f"{i}. {s.get('content')} | {s.get('ratio')} | {fmt_date(parse_date(s.get('deadline')))}{who} | {st}")
        QApplication.clipboard().setText("\n".join(lines))
        self._tip("排期表已复制")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = SchedulePadDialog()
    dlg.show()
    sys.exit(app.exec())
