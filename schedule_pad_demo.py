import sys
import os
import json
import uuid
import time
from PySide6.QtCore import Qt, QSize, QPoint, QEvent
from PySide6.QtGui import QIcon, QColor, QFont, QCursor
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QWidget, QFrame, QMessageBox, QAbstractItemView,
    QToolButton, QToolTip
)

# Test prototype for SchedulePadDialog
class SchedulePadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📅 任务排期表 - PromptDock")
        self.resize(780, 560)
        self.setMinimumSize(640, 440)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
        self.schedules = [
            {
                "id": str(uuid.uuid4()),
                "content": "灵滞短剧王爷",
                "ratio": "16:9",
                "deadline": "9/4 周五",
                "status": "done",
                "created_at": int(time.time()),
            },
            {
                "id": str(uuid.uuid4()),
                "content": "AI产品功能宣传短视频",
                "ratio": "9:16",
                "deadline": "今天",
                "status": "doing",
                "created_at": int(time.time()),
            },
            {
                "id": str(uuid.uuid4()),
                "content": "新角色三视图生成与实机演示",
                "ratio": "16:9",
                "deadline": "本周日",
                "status": "pending",
                "created_at": int(time.time()),
            }
        ]
        self.current_filter = "all"
        self._init_style()
        self._init_ui()
        self._refresh_table()

    def _init_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit, QComboBox {
                background-color: #2b2d42;
                border: 1px solid #3b3d54;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
                selection-background-color: #6c5ce7;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #8075e8;
                background-color: #31334d;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2d42;
                color: #ffffff;
                selection-background-color: #6c5ce7;
                border: 1px solid #3b3d54;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton {
                background-color: #3b3d54;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #4b4d66;
            }
            QPushButton:pressed {
                background-color: #2f3144;
            }
            QPushButton#PrimaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a7cf8, stop:1 #6c5ce7);
                color: #ffffff;
                font-weight: bold;
                padding: 8px 18px;
            }
            QPushButton#PrimaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #988bfb, stop:1 #7a6bf0);
            }
            QPushButton#TabActive {
                background-color: #6c5ce7;
                color: #ffffff;
                font-weight: 600;
            }
            QTableWidget {
                background-color: #1a1a28;
                border: 1px solid #2e3046;
                border-radius: 10px;
                gridline-color: #2b2d42;
                color: #cdd6f4;
                selection-background-color: #353752;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #242638;
                color: #a6adc8;
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid #363a4f;
                font-size: 12px;
                font-weight: 600;
            }
        """)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # 1. 顶部 Header
        header_layout = QHBoxLayout()
        back_btn = QPushButton("← 返回卡片")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2d42;
                border: 1px solid #3b3d54;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                color: #cdd6f4;
            }
            QPushButton:hover {
                background-color: #3b3d54;
                color: #ffffff;
            }
        """)
        back_btn.clicked.connect(self.close)
        header_layout.addWidget(back_btn)

        title_label = QLabel("📅 任务排期表")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; margin-left: 6px;")
        header_layout.addWidget(title_label)

        self.summary_badge = QLabel("共 3 项 · 1 进行中 · 1 已完成")
        self.summary_badge.setStyleSheet("color: #a6adc8; font-size: 12px; margin-left: 10px;")
        header_layout.addWidget(self.summary_badge)

        header_layout.addStretch(1)

        hotkey_tip = QLabel("快捷键: Shift+A / Esc 返回")
        hotkey_tip.setStyleSheet("color: #6c7086; font-size: 12px;")
        header_layout.addWidget(hotkey_tip)

        main_layout.addLayout(header_layout)

        # 2. 快速录入卡片区 (4个字段输入：序号自动生成、视频内容、视频比例、结束时间)
        add_card = QFrame()
        add_card.setStyleSheet("background-color: #25273a; border-radius: 10px; border: 1px solid #33364f;")
        add_card_layout = QHBoxLayout(add_card)
        add_card_layout.setContentsMargins(12, 10, 12, 10)
        add_card_layout.setSpacing(8)

        # 字段1: 视频内容
        self.input_content = QLineEdit()
        self.input_content.setPlaceholderText("📝 视频内容 / 任务名称 (如：灵滞短剧第2集)...")
        self.input_content.returnPressed.connect(self._on_add_task)
        add_card_layout.addWidget(self.input_content, 4)

        # 字段2: 视频比例
        self.combo_ratio = QComboBox()
        self.combo_ratio.setEditable(True)
        self.combo_ratio.addItems(["16:9", "9:16", "1:1", "4:3", "2.35:1"])
        self.combo_ratio.setFixedWidth(100)
        self.combo_ratio.setToolTip("视频比例 (支持下拉或直接自定义输入)")
        add_card_layout.addWidget(self.combo_ratio, 1)

        # 字段3: 结束时间
        self.input_deadline = QLineEdit()
        self.input_deadline.setPlaceholderText("⏰ 结束时间 (如 9/4 周五、今天)")
        self.input_deadline.setFixedWidth(145)
        self.input_deadline.returnPressed.connect(self._on_add_task)
        add_card_layout.addWidget(self.input_deadline, 2)

        # 快捷填日期按钮 (今天 / 明天 / 本周五)
        quick_date_btn = QToolButton()
        quick_date_btn.setText("📅")
        quick_date_btn.setToolTip("快速填入今天日期")
        quick_date_btn.setCursor(Qt.PointingHandCursor)
        quick_date_btn.setStyleSheet("QToolButton { background: #3b3d54; border-radius: 6px; padding: 6px; } QToolButton:hover { background: #4b4d66; }")
        quick_date_btn.clicked.connect(self._quick_set_date)
        add_card_layout.addWidget(quick_date_btn)

        # 添加按钮
        self.btn_add = QPushButton("＋ 添加任务")
        self.btn_add.setObjectName("PrimaryBtn")
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self._on_add_task)
        add_card_layout.addWidget(self.btn_add)

        main_layout.addWidget(add_card)

        # 3. 筛选栏与搜索
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)

        self.tab_all = QPushButton("全部")
        self.tab_doing = QPushButton("进行中")
        self.tab_done = QPushButton("已完成")

        for b, f in [(self.tab_all, "all"), (self.tab_doing, "doing"), (self.tab_done, "done")]:
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(28)
            b.clicked.connect(lambda _, flt=f: self._set_filter(flt))
            filter_row.addWidget(b)

        filter_row.addSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 快速检索任务...")
        self.search_input.setFixedHeight(28)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._refresh_table)
        filter_row.addWidget(self.search_input, 1)

        copy_all_btn = QPushButton("📋 复制全部排期")
        copy_all_btn.setFixedHeight(28)
        copy_all_btn.setCursor(Qt.PointingHandCursor)
        copy_all_btn.setStyleSheet("background: #2b2d42; color: #a6adc8; font-size: 12px;")
        copy_all_btn.clicked.connect(self._copy_schedule_table)
        filter_row.addWidget(copy_all_btn)

        clear_done_btn = QPushButton("🗑️ 清理已完成")
        clear_done_btn.setFixedHeight(28)
        clear_done_btn.setCursor(Qt.PointingHandCursor)
        clear_done_btn.setStyleSheet("background: #2b2d42; color: #f38ba8; font-size: 12px;")
        clear_done_btn.clicked.connect(self._clear_done_tasks)
        filter_row.addWidget(clear_done_btn)

        main_layout.addLayout(filter_row)

        # 4. 任务表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["序号", "视频内容", "视频比例", "结束时间", "完成状态", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(2, 95)
        self.table.setColumnWidth(3, 115)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 95)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table.cellChanged.connect(self._on_cell_changed)
        main_layout.addWidget(self.table, 1)

        # 5. 底部提示
        footer_layout = QHBoxLayout()
        tip_lbl = QLabel("💡 提示：双击视频内容可直接就地修改；点击【状态标签】可直接一键切换进度。")
        tip_lbl.setStyleSheet("color: #6c7086; font-size: 11px;")
        footer_layout.addWidget(tip_lbl)
        footer_layout.addStretch()
        main_layout.addLayout(footer_layout)

        self._update_tab_buttons()

    def _set_filter(self, flt):
        self.current_filter = flt
        self._update_tab_buttons()
        self._refresh_table()

    def _update_tab_buttons(self):
        for b, f in [(self.tab_all, "all"), (self.tab_doing, "doing"), (self.tab_done, "done")]:
            if self.current_filter == f:
                b.setStyleSheet("background-color: #6c5ce7; color: #ffffff; font-weight: bold; border-radius: 6px; padding: 4px 12px;")
            else:
                b.setStyleSheet("background-color: #2b2d42; color: #a6adc8; border-radius: 6px; padding: 4px 12px;")

    def _quick_set_date(self):
        now = time.localtime()
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        date_str = f"{now.tm_mon}/{now.tm_mday} {weekdays[now.tm_wday]}"
        self.input_deadline.setText(date_str)

    def _on_add_task(self):
        content = self.input_content.text().strip()
        if not content:
            QMessageBox.information(self, "提示", "请先输入视频/任务内容！")
            self.input_content.setFocus()
            return

        ratio = self.combo_ratio.currentText().strip() or "16:9"
        deadline = self.input_deadline.text().strip() or "待定"

        item = {
            "id": str(uuid.uuid4()),
            "content": content,
            "ratio": ratio,
            "deadline": deadline,
            "status": "doing",
            "created_at": int(time.time()),
        }
        self.schedules.insert(0, item)
        self.input_content.clear()
        self.input_deadline.clear()
        self.input_content.setFocus()
        self._refresh_table()

    def _refresh_table(self):
        self.table.blockSignals(True)
        search_kw = self.search_input.text().strip().lower()

        filtered = []
        for s in self.schedules:
            if self.current_filter == "doing" and s.get("status") == "done":
                continue
            if self.current_filter == "done" and s.get("status") != "done":
                continue
            if search_kw and (search_kw not in s.get("content", "").lower() and search_kw not in s.get("deadline", "").lower()):
                continue
            filtered.append(s)

        # 更新汇总统计
        total = len(self.schedules)
        doing_count = sum(1 for s in self.schedules if s.get("status") != "done")
        done_count = total - doing_count
        self.summary_badge.setText(f"共 {total} 项 · {doing_count} 进行中 · {done_count} 已完成")
        self.tab_all.setText(f"全部 ({total})")
        self.tab_doing.setText(f"进行中 ({doing_count})")
        self.tab_done.setText(f"已完成 ({done_count})")

        self.table.setRowCount(len(filtered))

        for row, item in enumerate(filtered):
            is_done = (item.get("status") == "done")

            # 0. 序号
            item_idx = QTableWidgetItem(f"#{row + 1}")
            item_idx.setTextAlignment(Qt.AlignCenter)
            item_idx.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item_idx.setForeground(QColor("#7f849c"))
            self.table.setItem(row, 0, item_idx)

            # 1. 视频内容
            content_str = item.get("content", "")
            item_content = QTableWidgetItem(content_str)
            item_content.setData(Qt.UserRole, item.get("id"))
            font = QFont()
            font.setPointSize(10)
            if is_done:
                font.setStrikeOut(True)
                item_content.setForeground(QColor("#6c7086"))
            else:
                font.setBold(True)
                item_content.setForeground(QColor("#ffffff"))
            item_content.setFont(font)
            self.table.setItem(row, 1, item_content)

            # 2. 视频比例 (胶囊标签)
            ratio_w = QWidget()
            ratio_layout = QHBoxLayout(ratio_w)
            ratio_layout.setContentsMargins(0, 0, 0, 0)
            ratio_layout.setAlignment(Qt.AlignCenter)
            ratio_btn = QPushButton(item.get("ratio", "16:9"))
            ratio_btn.setFixedHeight(24)
            ratio_btn.setCursor(Qt.PointingHandCursor)
            ratio_val = item.get("ratio", "16:9")
            if "16:9" in ratio_val:
                bg = "rgba(137, 180, 250, 0.18)"
                fg = "#89b4fa"
            elif "9:16" in ratio_val:
                bg = "rgba(203, 166, 247, 0.18)"
                fg = "#cba6f7"
            else:
                bg = "rgba(148, 226, 213, 0.18)"
                fg = "#94e2d5"
            ratio_btn.setStyleSheet(f"background:{bg}; color:{fg}; font-size:11px; font-weight:600; border-radius:6px; padding:2px 8px; border:none;")
            ratio_btn.clicked.connect(lambda _, it=item: self._edit_ratio(it))
            ratio_layout.addWidget(ratio_btn)
            self.table.setCellWidget(row, 2, ratio_w)

            # 3. 结束时间
            item_date = QTableWidgetItem(item.get("deadline", "-"))
            item_date.setTextAlignment(Qt.AlignCenter)
            date_fg = "#a6adc8"
            if "今天" in item.get("deadline", ""):
                date_fg = "#fab387"
            elif "周五" in item.get("deadline", ""):
                date_fg = "#f9e2af"
            item_date.setForeground(QColor(date_fg))
            self.table.setItem(row, 3, item_date)

            # 4. 完成状态 (点击可循环切换状态)
            status_w = QWidget()
            status_layout = QHBoxLayout(status_w)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.setAlignment(Qt.AlignCenter)
            status_btn = QPushButton()
            status_btn.setFixedHeight(24)
            status_btn.setCursor(Qt.PointingHandCursor)

            status = item.get("status", "pending")
            if status == "done":
                status_btn.setText("● 已完成")
                status_btn.setStyleSheet("background:rgba(166, 227, 161, 0.18); color:#a6e3a1; font-size:11px; font-weight:bold; border-radius:6px; padding:2px 8px; border:none;")
            elif status == "doing":
                status_btn.setText("● 进行中")
                status_btn.setStyleSheet("background:rgba(250, 179, 135, 0.18); color:#fab387; font-size:11px; font-weight:bold; border-radius:6px; padding:2px 8px; border:none;")
            else:
                status_btn.setText("○ 待制作")
                status_btn.setStyleSheet("background:rgba(147, 153, 178, 0.18); color:#9399b2; font-size:11px; font-weight:bold; border-radius:6px; padding:2px 8px; border:none;")

            status_btn.clicked.connect(lambda _, it=item: self._toggle_status(it))
            status_layout.addWidget(status_btn)
            self.table.setCellWidget(row, 4, status_w)

            # 5. 操作 (复制 / 删除)
            op_w = QWidget()
            op_layout = QHBoxLayout(op_w)
            op_layout.setContentsMargins(0, 0, 0, 0)
            op_layout.setSpacing(4)
            op_layout.setAlignment(Qt.AlignCenter)

            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(26, 24)
            copy_btn.setCursor(Qt.PointingHandCursor)
            copy_btn.setToolTip("复制该任务内容")
            copy_btn.setStyleSheet("background:transparent; border-radius:4px; font-size:12px;")
            copy_btn.clicked.connect(lambda _, c=content_str: self._copy_text(c))
            op_layout.addWidget(copy_btn)

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(26, 24)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip("删除该任务")
            del_btn.setStyleSheet("background:transparent; border-radius:4px; font-size:12px;")
            del_btn.clicked.connect(lambda _, it=item: self._delete_task(it))
            op_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 5, op_w)

        self.table.blockSignals(False)

    def _copy_text(self, text):
        QApplication.clipboard().setText(text)
        QToolTip.showText(QCursor.pos(), "✅ 已复制到剪贴板！", self, QPoint(), 1500)

    def _toggle_status(self, item):
        cur = item.get("status", "pending")
        if cur == "pending":
            item["status"] = "doing"
        elif cur == "doing":
            item["status"] = "done"
        else:
            item["status"] = "doing"
        self._refresh_table()

    def _edit_ratio(self, item):
        ratios = ["16:9", "9:16", "1:1", "4:3", "2.35:1"]
        cur = item.get("ratio", "16:9")
        try:
            next_idx = (ratios.index(cur) + 1) % len(ratios)
            item["ratio"] = ratios[next_idx]
        except ValueError:
            item["ratio"] = "16:9"
        self._refresh_table()

    def _on_cell_changed(self, row, col):
        if col == 1:
            item_w = self.table.item(row, col)
            if item_w:
                task_id = item_w.data(Qt.UserRole)
                for it in self.schedules:
                    if it.get("id") == task_id:
                        it["content"] = item_w.text().strip()
                        break
        elif col == 3:
            item_w = self.table.item(row, col)
            if item_w:
                content_item = self.table.item(row, 1)
                if content_item:
                    task_id = content_item.data(Qt.UserRole)
                    for it in self.schedules:
                        if it.get("id") == task_id:
                            it["deadline"] = item_w.text().strip()
                            break

    def _delete_task(self, item):
        if item in self.schedules:
            self.schedules.remove(item)
            self._refresh_table()

    def _clear_done_tasks(self):
        before = len(self.schedules)
        self.schedules = [s for s in self.schedules if s.get("status") != "done"]
        cleared = before - len(self.schedules)
        if cleared > 0:
            QToolTip.showText(QCursor.pos(), f"已清理 {cleared} 项已完成任务", self, QPoint(), 1500)
            self._refresh_table()

    def _copy_schedule_table(self):
        if not self.schedules:
            return
        lines = ["【视频任务排期表】"]
        for idx, s in enumerate(self.schedules, 1):
            st = "✅已完成" if s.get("status") == "done" else "⏳进行中"
            lines.append(f"{idx}. {s.get('content')} | 比例:{s.get('ratio')} | 截止:{s.get('deadline')} ({st})")
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        QToolTip.showText(QCursor.pos(), "✅ 排期表已复制为文本格式！", self, QPoint(), 2000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = SchedulePadDialog()
    dlg.show()
    pix = dlg.grab()
    pix.save(r'C:\Users\WELL\.gemini\antigravity\brain\3295a9b4-e916-4f41-b664-e7e110e14fa4\schedule_pad_preview.png')
    print('Preview rendered successfully!')
