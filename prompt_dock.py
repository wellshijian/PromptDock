# -*- coding: utf-8 -*-
"""
PromptDock - 提示词悬浮卡工具

功能：
- 悬浮窗口，可拖动、可置顶（窗口级）
- 每条提示词可以有多段内容，每段单独复制
- 文件夹分类，列表内可折叠分组；"置顶"是常驻展开的分组
- 卡片直接按住拖动排序，拖到别的文件夹分组下会自动改变分类
- 卡片颜色 + 整体主题色（含护眼配色）+ 窗口透明度
- 全局快捷键呼出/隐藏
- txt 导入导出
- 系统托盘

运行方法：
    python prompt_dock.py
打包方法见 README.md
"""

import sys
import os
import json
import uuid
import re
import base64
import ctypes
import time
import threading
import datetime
import urllib.request
import urllib.error
import random
import hashlib
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from PySide6.QtCore import (
    Qt, QTimer, Signal, QAbstractNativeEventFilter, QByteArray, QSize,
    QPointF, QMimeData, QPropertyAnimation, QEasingCurve, QPoint,
    QBuffer, QIODevice, QRectF, QEvent, QThread, QUrl, QRect
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFont, QAction, QKeySequence,
    QPen, QDrag, QTextCursor, QTextCharFormat, QShortcut, QPainterPath,
    QPolygonF, QImage, QDesktopServices, QCursor, QGuiApplication
)
from schedule_pad import SchedulePadDialog
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QToolButton, QFrame,
    QDialog, QTextEdit, QSystemTrayIcon, QMenu, QMessageBox,
    QGraphicsDropShadowEffect, QFileDialog, QSlider, QListWidget,
    QListWidgetItem, QAbstractItemView, QComboBox, QInputDialog, QScrollArea,
    QButtonGroup, QStackedWidget, QCheckBox, QProgressBar, QToolTip
)

APP_NAME = "PromptDock"
APP_VERSION = "1.0.2"
GITHUB_REPO = "wellshijian/PromptDock"
GITHUB_MIRRORS = [
    ("极速 CDN 节点", "https://cdn.gh-proxy.com/"),
    ("GitHub 官方通道", ""),
    ("加速节点 A", "https://gh-proxy.com/"),
    ("加速节点 Edge", "https://edgeone.gh-proxy.com/"),
]
WINDOW_W = 380
WINDOW_H = 520
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes.wintypes as wintypes

LOGO_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAWBElEQVR4nO1dfZBU1ZX/nXvf637dPdMD0wwMzDgC4vDhKgxkFF0gKGYpTU1ESddszFqQBVPBLBpiEquyVlrjVmJSUPmgNgStpSxYaxOhajdxsSxFE9YPNKKoRSDylRgiwYmA8jUz3e/ds3+893re9PR0zwzd069n+ld1anpev37345x7zrnnnncvUEEFFVRQQQUVjEZQqStQAuRrMw9LLXyCkSoA5CEX7KFi/bbsMFIEQKCnLQq5GSUABADozmf3NymHrDxlSefviBCKchUA7yjNxrBaAE0ApgohpiilmgBMBGEcMWoYCBNRAGDJDBBgMZAEcJGIzjLzKQB/FUL8mUj90bJwDMCfAXyUpSyJMhaGchMAd6RnMn0KgHlEmM+MFgDNAOoBaAUq1yLgJAhHmLFPCPGaUupNAEcy7nOFQRWo3KKjHASAYDPeq9o1TdPmKqWWKqWWAJgDoCbLb7OZg8E6gW75va8wzhHRuwBelJKfNU3sha1F+qtzBYMEocfeAgACgcAsCDxIRG/A1gJe1WsBMB2y0NP5hSCV5fm97iHCPiJ6GMA1Ge2QKI+B5htkMl6XUn6OiP6biC6gd8e7DCkkswcjFG753utdgminlPLzl19+ueFpR0UQBoA04ydOnBgWQvwzEb1B1IfphR7hhdQQ6euC6G0hxJra2tpotjZW0APhEObNm6frur6SiN5B39HmJ6bn0wxpM0FEB4UQX/FohL5+xSiGBAAiQjgcvoWIXkVPZ1rIYm/LiHppBSJ6MxAI3E6UtgSj2iw4UzrC+PHjp0optxHRSGF8TkEQQuyIxWIzHEEYldpAAoAQAsFg8G4hxEn0qM+RxPhsgqAAsCA6FQgE7mVmVwOMGt9AAsC0adMadV3fjp7OyfSm8xKVnqFDpXRbNU373yuvvHKqow1GtEkgAEIIgbFjxy4VQhxDT2eUg3NXaHKdRdak/KCmpuZ2IuH204gTAgEAUkpUV1d/QwiRwhBH/QgkEwATkaqqCiekTFuCEeMXCAD4yU9+EgyFQo+hp+Ej2dYPliwAigAOBoNP3hOPVzl9V/Z+gQSAeDxeGwoZO9Ej8aNR5eejtEnQdf03ra2t9d4+LEdIAFi6dOnEQCDwKgAme7291B3td0oBYE3T9jU3N0/x9mU5QQDATTfd1BAIBN6Ep2EVGoQQSHlw2rRpVzh9WjZCIACgra1tQiAQ2IsK84dE5JgDKeWBlpaWy71962cIAHjggQdqgsHgSygy88s4DjBQcs3BW9dff/14bx/7EQRAMLMeNoxfocjMx+gQgHQfBnT9hXXr1oXg0zgBAZBSStTU1PwUw8D8QlGZCFEKAAeDwSecOIHvIoZSCIG6+ro1zoJOWTC/zCgFgMeOrXlACDuuNmDuFBkCAK666qobpJQX4b9kjYJTibSGAmASUWrixImfcfq+5EJAAGjVqlW1wWDwIOyKViJ8xRM6CwBrmvanpUuXToQPlpKllBqi0eh/OBWtxPaLTyYADoeN7ZqmASXUApKI0NjYeLtj9yvMH0YhICKura1d4VlGHlYIAHTXXXfFdF13l3Urqn/4yAKgpJR/nT9/fgNKYAqEEAJjxoz5kVOhyugffjIBcCQS2SKEnWCVj2mFggCAq6++eq4QohOjwOv3KSkAFhGZjY2TFzm8GRZTIJiZQqHQ0/BIYoVKQiYADgaDv2VmiWHQAhIALrvsss8Q0UhP4CwXsoiI6+vrl3t5VCwQMwvDMF6ARwIrVFJytcDv9u/fH0AR1wokADQ1Nd3sjP6K3fcPuVrgDi+vCg0hpUQ4HHZX+iqj3z9kAmDDCPyGmb27peTFQDdQEADU1KlT5xw9cnSpU6gv16WJCJ7M2iGDmcFKQTEXoFZFhwTAyaS5sKmp6QYALzvX8m13M/AChBCIVlX9CKNs9EspWQhR8noMgEwAXFVVtcUZAAMaoANRFQSAP/vZz4599tln37Es6zLY9t9XGoCIwMxobGxEIpEAYI9i90VMzjKS7d8oEAgKDDBgmiZOnDiB/fv34/XXX8fJkycB2O80KKWyPscnYACk69qpT3968TW7du06gZ5dSi4JEgAmTJjQDhDDp1M/d5S2tn6KC4VTp07xk08+ydddd12fcnxKFgBuaGj4siP3BXEGbecvFHoKntx1v5HLmNmzZ3MqleJUMslJh7yfk/1cTyVTvb9LpdKCYFkW//jHP2bDMPwuBCYAVVVV9ayu6UABpoMEALfeemu9pmkdTiG+nP65TJkzZw4zMyulWFmW/XeIZFkWp5JJtiyLmZl3797NdXV1fhYCBYA1TTu7ZMmSqQ4Pc5rqfHZcAMBbb7210LKsOqcAX+WiZSK9+UI/ttq14cxs3+OhTPtORJCaBiJCsjuJRYsWYefOnaiqqupdln9AAJRlmdXHDh++yXOtX+QTABZC4Ny5c59hZjhZKf6GW0NnYyEviAhCiJ6/GeTk2sEyTSjV23fSAzqSySRaW1vx2GOPQSmVvt9nYGbgzNmzNzsJI0PmGQHAoUOHgkYwuN95kC8dQHhUcktLi8cEZFHpqRSnUik2TbMvpcxeTqBpmr2fY1mcTCaZmXn58uUM2NPEUrc9gywAHAwG/7Rt2zZ3c6p+tUAu9SAAqOnTp1995PDhvZZSAacA3+k9wN5tRCmFOXPmYN++fWDl9gdBsYKUEqtWrcJLL70EXdftKR0YBEpPIQEgGq3GggULcffquzFj5gxYpgnhBpYYsJQFKSXee+89zJkzB8mkvTekz6aHrGmSW1tbFu7Zs/dVDDEoJAGgrq5uhaNNfTv6gRxOoKXYNO2RvWDBggE/LxwO8xNPPGFrglSqlyZJOc+79dZb/aoFTADc1NB0b76UsdweohDo7Oyc5/pNue71C7x+md0bPdU2DANCCOi6DuHY/Gyk6zouXryIlStX4pmdOyE1DZZlDyA3RMzMiMfjw9y6weHCxXNzhRRADt7lEgAlhIBpmn9X8JoVEa4mdlWy114ppQZEqVQKmmYPmvu+9jV0dnba6wvc25FsbW2FpklYlgVfTQjIbnZXMnmVmTIlcsze+hMAAsDt7e1R0zSneK7lKbd06Jn99Wb8UNWWaVoQQuDIkSN49ZVXQUSwVG8zOmnSJMRi45zyCzcjuOR+ZPsRqVTq8vvuu29crltzCQDeeOONSUqpeu+13OWWDu7IT1cyLRFDf6Y70n9/4PcAkJ4auvP/SCSCaDTa7++HikL1o1Kqdu/evZc5/w5aA+D8+fMNABvwsfefCc78VIhau1qFqJdPQST8GgsgAEopJc+ePTskAQAApLq6GpRioIwOQHCR1giXYJzd1b/p02d4HtzzsaurE+fPnxvy84sMVkqhs7OzMddN/QoAESFpWfX9fV9WGIJOFUKAmdHQ0IAb/v4GMHPaJLh+xqlTp3Dq1Gm7iBLFAfJFeC5cuFCfS0vl1ACmadYNsV4lR688gH56iYj6kBAEzYn/MzN+8OgPUF1dDdM00+re1QwHDx5EV1dXWlhKgf5KdZucTCbrcmnBflPC7B+pMUOuWamRpWe8THIjh33vAZQyAQDf/e4j+OI/fRGWZaXTzNjjDzzzzDM5n1VKeJo6xhGArLLSnwDYhl8hUuiKDRdcZ82rst2RIIRAKpVCtLoaUpNQqidzKBKO4FOtn8LatWuxZMkSWJYFQZSeVTAzpJT45JNPsGPHDgCAsgqWeldwWJYZGYoAAACUUkau7/0EV8l51V2m4nODOKlUCnfeeSc2bNjg2HYCkT2KI5EIqqurAaAP8wFb/eu6jscffxwnT56ElDIdJfQjLEsFcn2fLyu45DtQDBSZ4k3uNY8u1HQNSincdttt2Lp1a7/Zw6Zpm4DM713mHz9+HN/73vcc2+8v1e8i3f48PMwnAGUR/weQJRTr6QIHHR92YG7LXPziF78AEaUdO1tGGO75DTKL12xZCkIQLMvCXXfdhTNnzji2399dlCUtohdyzgKIKFXY6hQPfZxwj0AIIWBZFpYsWYJfP/1rGIbh2HLheP/ujECkhcBr803ThKZJCCGwYsVK7N69O50l7Fe43cEMcyi/F0IIhILBrfAsL/qZZOZysGWx5eQEsupJ7kgnelh2gkhfMtmyLDZNk5PJZPo3H374Ibe1tTEA1qRW8vbmIyIyAXA0Gv2VkxmUdbD3GwpmZjCRb8NcmchUAN7/3SCO/dmJ8QtPelivVDF7pEspoes6TNPC1q1bcW1rK55++mlIKWFaQxpUwwp35hPQtLO57svpA+i6frqrq6uA1So+elYDnbg99/7OMlPpDB/OeHGEyLbxZ8+dxbEjx7DrhV345S9/iXfffRcAfO/xZ4UQZ5w+yRoN6lcAnPluR19XqkzgVNwWAoYQdkrYyy+9jKARgGla3tvsz0RIpVI4feYMTp86lX6UEAJgLj/mA9A0rSOXr5JTAwghThRwTW1YkPkqWPq1LwCHDh3C4SOHB/YckBMkUr529vIhHA5/kCtMnXMWEAqF/uJsASdQJorAmxBiO/Q9ZiAUCg0oJcxd9jWzpIeXEYSUErW1tcdz3tTPdQaAhoaGD6QUHxe6ZsMD58Bhj9gONCXMZxm+QwEDICFEZywWO+651gc5BWDLli0dQsgPcj3AN8gwUt7EDfc79nkTCggGACnlyXg8fsJ7LRO5BEDMvmZ2UhAdyvUA36BP7bK4LZfYgrJxhJyWapp2ZM2aNeeQLSzqIJcPQIoVNF1/u/D1Kz68EdDM1cChwt8joC8Mw3jXmbn0y+ecTiAzwzCMN52O82XymwuXt5RlnPrwJc5ig4gINTU1b+RzYnMxlQHgmmumvSOlOI0casQPSPttWZKBy9+nGzicF3iFlPLi5MmT9zmX++2BnC+GAKAXXthzQgj5jueaL5E5yL3/jzIFwAAQChkHdu3adcx7LRvy7g8ghOBwOPzbAlWuaPCOcmaGUvb7/l7ysQIrGNyoRzgc+T8ppQlnB7H+7s9r15kZ9fX1zwshfLcxVDa4MX0pZS9yF3rKBZegtIQQAk0NTc8NJIiVj6EKADZt2rRP1/WDTr18aQbSTqATz+/s7ERXVxe6urrQ2dmFlJnq82qXnzFEXaUAUCgU+tPGn23c47nWLwYiaFIIYY0bN+4HHR0d34L9mrhvh5JhGJg0aRIUKwiy07VJ2CnfH/zlA5Tb6uYgYQGQEydO/PnfOjrWmJZVuG3i5s2bd60QIuU80JcbRVUIStM0tXjx4iVe3hUCxMyypqbmZfh4qziXhBBZqdT1KiYR2Qd31NTUvM3MQZdvuZgKDNypE0IIa/z48VvJjqr4emLV3yJPMeCHV+IBwE7gImpsbHxSCNGNPN7/oMsCgI0bN8bC4fBxOMeVwAeSXyEwOWY5HA5/tGnTpgYASCQSBZ+xSSklJk9u+jenYF+bgVFGJgCe3ty8MVcCaDYM+MZEIsGWZdFXvnLPY6FQ6AwAURb7Bo58MAARCoUu3LZs2c9M0yR3s+xiQGiaxIwZM9YDPanHFSoduTy4ctq0x3VdB4oZrHPsCm3btq2xOhL5Gyq+QImZb9v+qkjV2fXr1zcDoGLY/kxIIQRaWlr+lYgqWqCkAmD3fWtr6w8Ha/uHDGYmAHT69Oma2ljte05FKlpg+JlvAVDjYuOOnzhxog7DNPoBAPF4XALAnXfeeUcgEGBUZgQlIDI1TePP3377l4gozZPhhAiFQpg1a9ZTQMUhHE5y+7q5uflZtk8JG9RJYQWB6xDu3bu3afz48X8FoFxTQD7opJFK7pmNY8eOPbNt27bpHl4MP+LxuCQirF69+gvBYJBRMQXDQaau6dze3v5lIURJVH8mpGEYmD9//mZCxRQUk9y+nTt37n+FQ2HAjveXdl3GmRUIZq6aOXPm71ARgqIyf8qUyb9n5hjsFVp/LMq5NuiVV16ZMWnSpA+BytSwkOT2ZSwW+3jLli1zvX3uG7i2aP369UtjsVg3bKewkjhy6cxXAKyqqmrr29/+9vJSTfkGhHg8LqWUWLdu3arq6moGYFaE4JKZb4ZDIf7Sii99TbPPAvQn8z3QdF3HmjVrvhWpqqoIwSUyPxgM8hfa2x8JhUJAGTAfsL1SaRgGVq9enaiyhcCqCMHgmR8IBHjZsmXrI5EIAEjfOH354FRUhkIhfPWrX/1ONBplAJYQFSHIR67ND4VCvHx5/IfOIZWibJjvwhUCwzDw4IMP3u85crUyO+if+RYAVV1dzStXrkw4I7/8mO/CFQJd17Fx48YVU6dOuQhU4gTZyO2TWCyWWrdu3T2GYQDlzHwX7rl1RITnnntuScucOcdhNzpV8QvAzh5MKQA8efLkjp//+8/bnD2Ky8fmDxASAJh5Wltb227nKHY1kk1CvkUxR+VbUkq+/vrrXj9w4IB7RF9ZePuDhhvAYObQN7/5zQ2NjY1uZ5jOSBgV5LTVBMBjx47h9vb2Tcxc7e2jEQs3hBkMBvHiiy/etmjRoqOapjGc5eSRLgiuoweAZ86ceXzDhg3/6Mzx/RfeLRZc59D5POHee+/dPHny5LQ2EGLkrSM4jHcdPV6+fPlWZnaPdCt/Z28ocNVdKBTCa6+99g+33HLLa7W1tWlBGAkLSm5QBwAbhsHXXnvtvs2bN3/Omd+PfJWfD+5ysvM5uHnz5jULFy48EolEeglCuZkG74jXdZ1nzpz5/v3337+OmcNO08WoUfkDgXckMHPs+9///gOtra3HnFAyA1BE/l5XICLlzOctOCN++vTpx+++++7vMPMEd7eyUT/q+wMzUxZBWLtgwYJ9biQRPVrBF8LgYXo6uBWNRrmlpWX/17/+9W8w8wTPwY0jbm5fFHidROf/4FNPPfW59i+0b29ubv44HA57mWChx0wUVSCoh+FWJtN1XefGxoZzN9544/88+uijn/eoeqDC+KEhUyOEw2Ew89REIvEvN99883NTp079pKoqkskoVyDSQjEUwXB/l8HsXk5pMBjk+vr6c/Pnz3/xnnvuWXf06F+anfi9iwrjCwGPIKR1aXV1NZj5ikceeWTFHXfc8cTs2bMP1NfXd4dCof6Y6r7HaOah9Dw9k0KGwbFYLNncfOV7N95443+uXbt29dtvv92ccYQ8xePxsmF8WVTSi0QiIQ4cOEDbt293mYRAIIDu7u7Qnj17pu3YseOao0ePzj5x4sSs06dPT+nsvFjf3Z2sSSWTsjuZhGVZzj6CvXcMSW8tJwQ0XYeu6yoYDH4SiUQ+jEajf6yrqzs4c+bMdxYvXvzusmXLDhuGcaG7u9v7CJlIJPjhhx/25S5q/aHsBMALjzC4IxyAfcSLYRi4cOGCcfHixdjzzz8//g9/+MP4999/v+78+fNju7q6qi3LMphZBwBmTum63hUOh89Fo9GPx4wZ89EVV1zR0dbW1lFbW/tRJBLp7O7uzjwyRsTjcZo1a1bZMX1EgpkpkUgIx1TkzZfPPDU8DwiAjMfjMpFIjKio3YhpSDYwMz300EMEAAcOHCAA2L59e87fxONxAMCsWbMYAB566CF38aaCCiqooIIKKqigggpGBv4f2LK8ia2pPm8AAAAASUVORK5CYII="

GROUP_UNCATEGORIZED = "__uncategorized__"


def make_logo_pixmap(size=64):
    pix = QPixmap()
    try:
        pix.loadFromData(QByteArray(base64.b64decode(LOGO_PNG_BASE64)), "PNG")
        if not pix.isNull():
            return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        pass
    fallback = QPixmap(size, size)
    fallback.fill(Qt.transparent)
    painter = QPainter(fallback)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#4361ee"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)
    painter.setPen(QColor("white"))
    font = QFont()
    font.setBold(True)
    font.setPointSize(max(8, size // 3))
    painter.setFont(font)
    painter.drawText(fallback.rect(), Qt.AlignCenter, "P")
    painter.end()
    return fallback


def _resolve_app_icon_path():
    """打包后的不透明 icon.ico，供任务栏使用。"""
    candidates = []
    if getattr(sys, 'frozen', False):
        mei = getattr(sys, '_MEIPASS', '')
        if mei:
            candidates.append(os.path.join(mei, 'icon.ico'))
        candidates.append(sys.executable)
        here = os.path.dirname(sys.executable)
    else:
        here = os.path.dirname(os.path.abspath(__file__))
    candidates.extend([
        os.path.join(here, 'icon.ico'),
        os.path.join(here, 'dist', 'icon.ico'),
    ])
    for p in candidates:
        p = os.path.normpath(p)
        if p and os.path.exists(p):
            return p
    return None


def apply_windows_taskbar_icon(widget, icon_path=None):
    """给无边框/透明窗口强制设置任务栏图标。"""
    if not IS_WINDOWS:
        return
    path = icon_path or _resolve_app_icon_path()
    try:
        import ctypes
        user32 = ctypes.windll.user32
        WM_SETICON = 0x0080
        ICON_SMALL, ICON_BIG = 0, 1
        hwnd = int(widget.winId())
        if path and path.lower().endswith('.ico') and os.path.exists(path):
            for size, which in ((32, ICON_BIG), (16, ICON_SMALL)):
                hicon = user32.LoadImageW(None, path, 1, size, size, 0x0010)
                if hicon:
                    user32.SendMessageW(hwnd, WM_SETICON, which, hicon)
            return
        if getattr(sys, 'frozen', False):
            large = ctypes.c_void_p(); small = ctypes.c_void_p()
            ctypes.windll.shell32.ExtractIconExW(sys.executable, 0, ctypes.byref(large), ctypes.byref(small), 1)
            if large.value:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, large.value)
            if small.value:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small.value)
    except Exception:
        pass


def load_app_icon():
    path = _resolve_app_icon_path()
    if path:
        if path.lower().endswith(('.ico', '.png')):
            ic = QIcon(path)
            if not ic.isNull():
                return ic
        if path.lower().endswith('.exe'):
            ic = QIcon(path)
            if not ic.isNull():
                return ic
    return QIcon(make_logo_pixmap(64))


def draw_titlebar_icon(kind, size=16, color="#ffffff", active=False):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)

    if kind == "pin":
        cx = size / 2
        head_r = size * 0.20
        head_cy = size * 0.32
        painter.setBrush(QColor(color) if active else Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, head_cy), head_r, head_r)
        painter.drawLine(QPointF(cx, head_cy + head_r), QPointF(cx, size * 0.86))
    elif kind == "minimize":
        y = size * 0.7
        painter.drawLine(QPointF(size * 0.22, y), QPointF(size * 0.78, y))
    elif kind == "close":
        m = size * 0.24
        painter.drawLine(QPointF(m, m), QPointF(size - m, size - m))
        painter.drawLine(QPointF(size - m, m), QPointF(m, size - m))
    elif kind == "cloud":
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(QPointF(size * 0.28, size * 0.72), QPointF(size * 0.75, size * 0.72))
        painter.drawArc(int(size * 0.16), int(size * 0.46), int(size * 0.32), int(size * 0.32), 90 * 16, 180 * 16)
        painter.drawArc(int(size * 0.30), int(size * 0.24), int(size * 0.42), int(size * 0.42), 0 * 16, 180 * 16)
        painter.drawArc(int(size * 0.56), int(size * 0.40), int(size * 0.34), int(size * 0.34), -60 * 16, 180 * 16)
    elif kind == "draft":
        rx = size * 0.22
        ry = size * 0.18
        rw = size * 0.56
        rh = size * 0.64
        if active:
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(int(rx), int(ry), int(rw), int(rh), 2, 2)
            bg_pen = QPen(QColor("#2b2d42"))
            bg_pen.setWidthF(1.4)
            painter.setPen(bg_pen)
            painter.drawLine(QPointF(rx + 2.5, ry + 3.5), QPointF(rx + rw - 2.5, ry + 3.5))
            painter.drawLine(QPointF(rx + 2.5, ry + 6.5), QPointF(rx + rw - 2.5, ry + 6.5))
        else:
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(int(rx), int(ry), int(rw), int(rh), 2, 2)
            painter.drawLine(QPointF(rx + 2.5, ry + 3.5), QPointF(rx + rw - 2.5, ry + 3.5))
            painter.drawLine(QPointF(rx + 2.5, ry + 6.5), QPointF(rx + rw - 2.5, ry + 6.5))
    elif kind == "clean":
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawLine(QPointF(size * 0.22, size * 0.78), QPointF(size * 0.62, size * 0.38))
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.drawLine(QPointF(size * 0.60, size * 0.20), QPointF(size * 0.80, size * 0.40))
        painter.drawLine(QPointF(size * 0.70, size * 0.15), QPointF(size * 0.70, size * 0.45))
        painter.drawLine(QPointF(size * 0.55, size * 0.30), QPointF(size * 0.85, size * 0.30))
    elif kind == "media":
        rx = size * 0.16
        ry = size * 0.20
        rw = size * 0.68
        rh = size * 0.60
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(int(rx), int(ry), int(rw), int(rh), 2, 2)
        poly = QPolygonF([
            QPointF(size * 0.42, size * 0.35),
            QPointF(size * 0.65, size * 0.50),
            QPointF(size * 0.42, size * 0.65),
        ])
        painter.setBrush(QColor(color))
        painter.drawPolygon(poly)
    elif kind == "schedule":
        rx = size * 0.18
        ry = size * 0.22
        rw = size * 0.64
        rh = size * 0.60
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(int(rx), int(ry), int(rw), int(rh), 2, 2)
        painter.drawLine(QPointF(rx, ry + rh * 0.30), QPointF(rx + rw, ry + rh * 0.30))
        painter.drawLine(QPointF(rx + rw * 0.28, ry - 1), QPointF(rx + rw * 0.28, ry + 2))
        painter.drawLine(QPointF(rx + rw * 0.72, ry - 1), QPointF(rx + rw * 0.72, ry + 2))
        painter.drawLine(QPointF(rx + rw * 0.25, ry + rh * 0.62), QPointF(rx + rw * 0.45, ry + rh * 0.62))
        painter.drawLine(QPointF(rx + rw * 0.55, ry + rh * 0.62), QPointF(rx + rw * 0.75, ry + rh * 0.62))

    painter.end()
    return pix


# ---------------------------------------------------------------------------
# 数据存储
# ---------------------------------------------------------------------------

def get_data_dir():
    if IS_WINDOWS:
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d


DATA_FILE = os.path.join(get_data_dir(), "prompts.json")
SETTINGS_FILE = os.path.join(get_data_dir(), "settings.json")

CARD_COLOR_DEFAULT = "#f5f6fa"
COLOR_PRESETS = [
    ("默认灰", "#f5f6fa"),
    ("暖蓝", "#e3edff"),
    ("清新绿", "#e3f9ec"),
    ("柔黄", "#fff8e1"),
    ("粉樱", "#ffe8f0"),
    ("薰衣紫", "#f1e8ff"),
]

THEME_PRESETS = [
    ("默认", "#2b2d42", "#4361ee"),
    ("石墨灰蓝", "#3a4750", "#6b8f96"),
    ("豆沙绿", "#3f4b3a", "#7a9471"),
    ("燕麦棕", "#4a3f35", "#9c8267"),
    ("雾霭蓝", "#35434a", "#6f93a3"),
    ("暖灰", "#454341", "#a39c8f"),
]
THEME_MAP = {name: (tb, ac) for name, tb, ac in THEME_PRESETS}

DEFAULT_SETTINGS = {
    "hotkey": "Shift+Z",
    "draft_hotkey": "Shift+X",
    "capture_hotkey": "Alt+C",
    "extractor_hotkey": "Shift+T",
    "schedule_hotkey": "Shift+A",
    "opacity": 1.0,
    "theme": "默认",
    "folders": [],
    "collapsed_groups": [],
    "edge_dock": True,
    "cloud_url": "",
    "cloud_token": "",
    "cloud_email": "",
    "cloud_nickname": "",
    "cloud_avatar": "",
    "last_sync_time": 0,
}


def _draft_file_path():
    return os.path.join(get_data_dir(), "draft.html")


def load_draft():
    path = _draft_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    # 兼容旧版本（纯文本）草稿文件
    legacy = os.path.join(get_data_dir(), "draft.txt")
    if os.path.exists(legacy):
        try:
            with open(legacy, "r", encoding="utf-8") as f:
                text = f.read()
            escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return "<p>{}</p>".format(escaped.replace("\n", "<br>"))
        except Exception:
            return ""
    return ""


def save_draft(html_content):
    try:
        tmp = _draft_file_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(html_content)
        os.replace(tmp, _draft_file_path())
    except Exception:
        pass



def _new_prompt(title, content, folder=""):
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "folder": folder,
        "pinned": False,
        "color": CARD_COLOR_DEFAULT,
        "segments": [{"id": str(uuid.uuid4()), "content": content}],
        "updated_at": int(time.time() * 1000),
        "is_deleted": False,
    }


DEFAULT_PROMPTS = [
    _new_prompt("写作开场白", "请用简洁有力的语言帮我写一段开场白，主题是："),
    _new_prompt("代码注释生成", "请为以下代码添加详细的中文注释，解释每一部分的作用："),
    _new_prompt("翻译提示词", "请将以下内容翻译成英文，保持语气自然、符合母语者表达习惯："),
]


def _migrate_prompt(p):
    p.setdefault("folder", "")
    if p.get("folder") == "默认":
        p["folder"] = ""
    p.setdefault("pinned", False)
    p.setdefault("color", CARD_COLOR_DEFAULT)
    p.setdefault("updated_at", 0)
    p.setdefault("is_deleted", False)
    if "segments" not in p or not p["segments"]:
        old_content = p.get("content", "")
        p["segments"] = [{"id": str(uuid.uuid4()), "content": old_content}]
    for seg in p["segments"]:
        seg.setdefault("id", str(uuid.uuid4()))
    return p


def load_prompts():
    if not os.path.exists(DATA_FILE):
        save_prompts(DEFAULT_PROMPTS)
        return [dict(p) for p in DEFAULT_PROMPTS]
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [_migrate_prompt(p) for p in data]
    except Exception:
        pass
    return [dict(p) for p in DEFAULT_PROMPTS]


def save_prompts(prompts):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return json.loads(json.dumps(DEFAULT_SETTINGS))
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            merged = json.loads(json.dumps(DEFAULT_SETTINGS))
            merged.update(data)
            merged["folders"] = [f for f in merged.get("folders", []) if f and f != "默认"]
            return merged
    except Exception:
        pass
    return json.loads(json.dumps(DEFAULT_SETTINGS))


def save_settings(settings):
    tmp = SETTINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SETTINGS_FILE)


def prompt_matches(prompt, keyword):
    if not keyword:
        return True
    keyword = keyword.lower()
    if keyword in prompt["title"].lower():
        return True
    for seg in prompt.get("segments", []):
        if keyword in seg["content"].lower():
            return True
    return False


# ---------------------------------------------------------------------------
# TXT 导入导出
# ---------------------------------------------------------------------------

def export_prompts_to_txt(prompts, path):
    parts = []
    for p in prompts:
        lines = ["标题: {}".format(p["title"]), "文件夹: {}".format(p.get("folder") or "未分类"), "内容:"]
        segs = p.get("segments", [])
        if len(segs) == 1:
            lines.append(segs[0]["content"])
        else:
            for idx, seg in enumerate(segs, 1):
                lines.append("[提示词{}]".format(idx))
                lines.append(seg["content"])
                lines.append("")
        parts.append("\n".join(lines).rstrip())
    content = "\n===\n".join(parts) + "\n"
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(content)


def parse_prompts_txt(text):
    blocks = re.split(r"\n\s*===\s*\n", text)
    results = []
    seg_pattern = re.compile(r"^\[(.+?)\]\s*$", re.M)
    for block in blocks:
        block = block.strip("\n")
        if not block.strip():
            continue
        title_match = re.search(r"标题[:：]\s*(.*)", block)
        folder_match = re.search(r"文件夹[:：]\s*(.*)", block)
        content_match = re.search(r"内容[:：]\s*\n(.*)", block, re.S)
        if not (title_match and content_match):
            continue
        title = title_match.group(1).strip()
        folder_text = folder_match.group(1).strip() if folder_match else ""
        folder = "" if folder_text in ("", "未分类", "默认") else folder_text
        body = content_match.group(1).strip("\n")
        if seg_pattern.search(body):
            segments = []
            pieces = seg_pattern.split(body)
            it = iter(pieces[1:])
            for _label, seg_content in zip(it, it):
                seg_content = seg_content.strip("\n").strip()
                if seg_content:
                    segments.append({"content": seg_content})
            if not segments:
                segments = [{"content": body}]
        else:
            segments = [{"content": body}]
        if title and segments:
            results.append({"title": title, "folder": folder, "segments": segments})
    return results


def import_prompts_from_txt(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        text = f.read()
    return parse_prompts_txt(text)


# ---------------------------------------------------------------------------
# 全局快捷键
# ---------------------------------------------------------------------------

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
HOTKEY_ID_MAIN = 1
HOTKEY_ID_DRAFT = 2
HOTKEY_ID_CAPTURE = 3
HOTKEY_ID_EXTRACTOR = 4
HOTKEY_ID_SCHEDULE = 5

SPECIAL_KEYS = {
    "SPACE": 0x20, "TAB": 0x09, "ESC": 0x1B, "ESCAPE": 0x1B,
    "ENTER": 0x0D, "RETURN": 0x0D, "BACKSPACE": 0x08,
    "UP": 0x26, "DOWN": 0x28, "LEFT": 0x25, "RIGHT": 0x27,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74,
    "F6": 0x75, "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79,
    "F11": 0x7A, "F12": 0x7B,
}


def parse_hotkey(text):
    if not text:
        return None, None
    parts = [p.strip() for p in text.split("+") if p.strip()]
    mods = 0
    vk = None
    for p in parts:
        low = p.lower()
        if low in ("ctrl", "control"):
            mods |= MOD_CONTROL
        elif low == "alt":
            mods |= MOD_ALT
        elif low == "shift":
            mods |= MOD_SHIFT
        elif low in ("win", "meta"):
            mods |= MOD_WIN
        else:
            key = p.upper()
            if key in SPECIAL_KEYS:
                vk = SPECIAL_KEYS[key]
            elif len(key) == 1:
                vk = ord(key)
    if vk is None or mods == 0:
        return None, None
    return mods, vk


if IS_WINDOWS:
    class _WinHotkeyFilter(QAbstractNativeEventFilter):
        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        def nativeEventFilter(self, eventType, message):
            try:
                ev = bytes(eventType) if hasattr(eventType, "data") or isinstance(eventType, (bytes, bytearray, QByteArray)) else str(eventType).encode()
                if b"MSG" in ev:
                    msg = wintypes.MSG.from_address(int(message))
                    if msg.message == WM_HOTKEY:
                        self.callback(msg.wParam)
            except Exception:
                pass
            return False, 0


RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "PromptDock"


def _startup_command():
    if getattr(sys, "frozen", False):
        return '"{}"'.format(sys.executable)
    return '"{}" "{}"'.format(sys.executable, os.path.abspath(__file__))


def is_startup_enabled():
    if not IS_WINDOWS:
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, RUN_VALUE_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def set_startup_enabled(enabled):
    if not IS_WINDOWS:
        return
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
    try:
        if enabled:
            winreg.SetValueEx(key, RUN_VALUE_NAME, 0, winreg.REG_SZ, _startup_command())
        else:
            try:
                winreg.DeleteValue(key, RUN_VALUE_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


class GlobalHotkeyManager:
    def __init__(self):
        self.callbacks = {}  # hotkey_id -> callable
        self.registered_ids = set()
        self._filter = None
        self._last_trigger_ms = {}  # hotkey_id -> timestamp
        if IS_WINDOWS:
            self._filter = _WinHotkeyFilter(self._on_hotkey)
            QApplication.instance().installNativeEventFilter(self._filter)

    def _on_hotkey(self, hotkey_id):
        callback = self.callbacks.get(hotkey_id)
        if callback is None:
            return
        import time
        now = time.monotonic() * 1000
        last = self._last_trigger_ms.get(hotkey_id, 0)
        if now - last < 400:
            return  # 400ms 内的重复触发直接忽略，防止同一次按键被处理两次
        self._last_trigger_ms[hotkey_id] = now
        QTimer.singleShot(0, callback)

    def register(self, hwnd, hotkey_id, combo_text, callback):
        self.callbacks[hotkey_id] = callback
        if not IS_WINDOWS:
            return True, ""
        self.unregister(hwnd, hotkey_id)
        mods, vk = parse_hotkey(combo_text)
        if mods is None:
            return False, "快捷键格式不对，至少需要一个修饰键（Ctrl/Alt/Shift）加一个普通键"
        ok = ctypes.windll.user32.RegisterHotKey(0, hotkey_id, mods | MOD_NOREPEAT, vk)
        if ok:
            self.registered_ids.add(hotkey_id)
            return True, ""
        err = ctypes.GetLastError()
        if err == 1409:
            return False, f"快捷键 [{combo_text}] 已被其他程序或后台占用，换一个试试"
        return False, f"快捷键 [{combo_text}] 注册失败 (错误代码: {err})"

    def unregister(self, hwnd, hotkey_id):
        if not IS_WINDOWS or hotkey_id not in self.registered_ids:
            return
        ctypes.windll.user32.UnregisterHotKey(0, hotkey_id)
        self.registered_ids.discard(hotkey_id)

    def unregister_all(self, hwnd):
        for hotkey_id in list(self.registered_ids):
            self.unregister(hwnd, hotkey_id)


# ---------------------------------------------------------------------------
# 样式表（跟随主题色动态生成）
# ---------------------------------------------------------------------------

def build_style(titlebar_color, accent_color):
    return """
#Wrapper {{ background-color: transparent; }}
#TitleBar {{
    background-color: {tb};
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
}}
#SearchBox {{
    background-color: rgba(255,255,255,0.92);
    border: none; border-radius: 8px; padding: 4px 8px; font-size: 12px;
}}
QToolButton#TitleBtn {{
    background: transparent; border: none; padding: 4px; border-radius: 6px;
}}
QToolButton#TitleBtn:hover {{ background-color: rgba(255,255,255,0.15); }}
#RootPanel {{ background-color: #ffffff; border-radius: 16px; }}
#FolderHeaderText {{ font-size: 12px; color: #6a6f7d; font-weight: 500; }}
#FolderArrow {{ font-size: 11px; color: #9a9fb0; }}
#Card {{
    background-color: #f5f6fa; border-radius: 12px; border: 1px solid transparent;
}}
#Card:hover {{ border: 1px solid #d8dcf5; }}
#CardTitle {{ font-size: 14px; font-weight: 600; color: #242424; }}
#SegTitle {{ font-size: 11px; font-weight: 600; color: #6a6f9c; }}
#CardPreview {{ font-size: 12px; color: #7a7a7a; }}
#PinBadge {{ font-size: 10px; color: {ac}; font-weight: 600; }}
#Watermark {{ color: #d3d4dc; font-size: 9px; }}
QPushButton#SegCopyBtn {{
    background-color: {ac}; color: white; border: none; border-radius: 6px;
    padding: 4px 10px; font-size: 11px;
}}
QPushButton#SegCopyBtn:hover {{ background-color: {ac}; }}
QDialog {{ background-color: #ffffff; }}
QListWidget {{ background: transparent; border: none; }}
QListWidget::item {{ border: none; }}
QListWidget::item:selected {{ background: transparent; }}
QMenu {{
    background-color: #ffffff; border: 1px solid #e3e3ec; border-radius: 8px; padding: 4px;
}}
QMenu::item {{ padding: 6px 18px; border-radius: 6px; font-size: 13px; }}
QMenu::item:selected {{ background-color: #eef0fb; color: {ac}; }}
QToolButton#ThemeSwatch {{ border: 2px solid transparent; border-radius: 8px; padding: 2px; }}
QToolButton#ThemeSwatch:checked {{ border: 2px solid {ac}; }}
""".format(tb=titlebar_color, ac=accent_color)


def _color_swatch_icon(hex_color, size=14):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(hex_color))
    painter.setPen(QColor("#cccccc"))
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.end()
    return QIcon(pix)


def _theme_swatch_icon(titlebar_color, accent_color, size=32):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    top_h = int(size * 0.55)
    painter.setBrush(QColor(titlebar_color))
    painter.drawRoundedRect(0, 0, size, top_h, 4, 4)
    painter.setBrush(QColor(accent_color))
    painter.drawRoundedRect(0, top_h, size, size - top_h, 4, 4)
    painter.end()
    return QIcon(pix)


# ---------------------------------------------------------------------------
# 文件夹分组标题（可点击折叠/展开）
# ---------------------------------------------------------------------------

def _find_prompt_list_widget(widget):
    w = widget.parent()
    while w is not None and not isinstance(w, PromptListWidget):
        w = w.parent()
    return w


def _accept_promptdock_drag(event):
    if event.mimeData().hasFormat("application/x-promptdock-id"):
        event.setDropAction(Qt.MoveAction)
        event.accept()
    else:
        event.ignore()


def _forward_drop_to_list(widget, event):
    mime = event.mimeData()
    if not mime.hasFormat("application/x-promptdock-id"):
        event.ignore()
        return
    lw = _find_prompt_list_widget(widget)
    if lw is None:
        event.ignore()
        return
    prompt_id = bytes(mime.data("application/x-promptdock-id")).decode("utf-8")
    pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
    list_pos = lw.viewport().mapFromGlobal(widget.mapToGlobal(pos))
    row = lw.indexAt(list_pos).row()
    if row == -1:
        row = lw.count()
    lw.card_dropped.emit(prompt_id, row)
    event.setDropAction(Qt.MoveAction)
    event.accept()


class FolderHeader(QWidget):
    toggled = Signal(str)
    delete_requested = Signal(str)
    rename_requested = Signal(str)

    def __init__(self, group_key, label, count, collapsed, is_folder=False):
        super().__init__()
        self.group_key = group_key
        self.label = label
        self.is_folder = is_folder
        self._press_pos = None
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptDrops(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(6)
        self.arrow = QLabel("▸" if collapsed else "▾")
        self.arrow.setObjectName("FolderArrow")
        layout.addWidget(self.arrow)
        self.text_label = QLabel("{} ({})".format(label, count))
        self.text_label.setObjectName("FolderHeaderText")
        layout.addWidget(self.text_label)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.pos()
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._press_pos is not None:
            moved = (event.pos() - self._press_pos).manhattanLength()
            if moved < 6:
                self.toggled.emit(self.group_key)
        self._press_pos = None
        event.accept()

    def dragEnterEvent(self, event):
        _accept_promptdock_drag(event)

    def dragMoveEvent(self, event):
        _accept_promptdock_drag(event)

    def dropEvent(self, event):
        _forward_drop_to_list(self, event)


# ---------------------------------------------------------------------------
# 单条提示词卡片（可直接拖动排序，不需要专门手柄）
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 自定义列表容器：接住卡片自己发起的拖拽（不使用 Qt 自带的 InternalMove，
# 那个机制在混有"分组标题行"的列表里，被拖动的那一项经常会跟自己的控件失联，
# 表现为"拖完东西凭空消失，点一下又出现"）。
# ---------------------------------------------------------------------------

class PromptListWidget(QListWidget):
    card_dropped = Signal(str, int)  # (prompt_id, drop_row)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-promptdock-id"):
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-promptdock-id"):
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime = event.mimeData()
        if not mime.hasFormat("application/x-promptdock-id"):
            event.ignore()
            return
        prompt_id = bytes(mime.data("application/x-promptdock-id")).decode("utf-8")
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        row = self.indexAt(pos).row()
        if row == -1:
            row = self.count()
        self.card_dropped.emit(prompt_id, row)
        event.setDropAction(Qt.MoveAction)
        event.accept()


class PromptCard(QFrame):
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    color_changed = Signal(str, str)
    pin_toggled = Signal(str)
    folder_changed = Signal(str, str)

    def __init__(self, prompt: dict, folders, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.folders = folders
        self.setObjectName("Card")
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptDrops(True)
        self._press_pos = None
        self._segment_areas = []  # [(widget, content, preview_label)]
        self._build_ui()
        self._apply_color()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        title = QLabel(self.prompt["title"])
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        header_row.addWidget(title, 1)
        if self.prompt.get("pinned"):
            badge = QLabel("置顶")
            badge.setObjectName("PinBadge")
            header_row.addWidget(badge, 0, Qt.AlignRight)
        layout.addLayout(header_row)

        segments = self.prompt.get("segments", [])
        multi = len(segments) > 1
        for idx, seg in enumerate(segments, start=1):
            seg_widget = QWidget()
            seg_layout = QVBoxLayout(seg_widget)
            seg_layout.setContentsMargins(0, 0, 0, 0)
            seg_layout.setSpacing(2)

            if multi:
                tag = QLabel("提示词{}".format(idx))
                tag.setObjectName("SegTitle")
                seg_layout.addWidget(tag)

            preview_text = seg["content"].replace("\n", " ")
            limit = 42 if multi else 50
            if len(preview_text) > limit:
                preview_text = preview_text[:limit] + "…"
            preview = QLabel(preview_text)
            preview.setObjectName("CardPreview")
            preview.setWordWrap(True)
            preview.setToolTip("点击即可复制")
            seg_layout.addWidget(preview)

            layout.addWidget(seg_widget)
            self._segment_areas.append((seg_widget, seg["content"], preview))

    def _apply_color(self):
        color = self.prompt.get("color", CARD_COLOR_DEFAULT)
        self.setStyleSheet(
            "QFrame#Card {{ background-color: {c}; border-radius:12px; border:1px solid transparent; }}"
            "QFrame#Card:hover {{ border:1px solid #d8dcf5; }}".format(c=color)
        )

    def _copy(self, text, preview_label):
        QApplication.clipboard().setText(text)
        original = preview_label.text()
        preview_label.setText("✅ 已复制")
        QTimer.singleShot(900, lambda: preview_label.setText(original))

    def matches(self, keyword: str) -> bool:
        return prompt_matches(self.prompt, keyword)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self._press_pos is not None:
            moved = (event.pos() - self._press_pos).manhattanLength()
            if moved >= 10:
                self._start_drag()
                return
        super().mouseMoveEvent(event)

    def _start_drag(self):
        prompt_id = self.prompt["id"]
        self._press_pos = None  # 防止拖拽结束后又被当成一次点击触发复制
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-promptdock-id", prompt_id.encode("utf-8"))
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(self.mapFromGlobal(self.cursor().pos()))
        drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event):
        _accept_promptdock_drag(event)

    def dragMoveEvent(self, event):
        _accept_promptdock_drag(event)

    def dropEvent(self, event):
        _forward_drop_to_list(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._press_pos is not None:
            moved = (event.pos() - self._press_pos).manhattanLength()
            if moved < 6:
                self._copy_at(event.pos())
        self._press_pos = None
        super().mouseReleaseEvent(event)

    def _copy_at(self, pos):
        for widget, content, preview_label in self._segment_areas:
            if widget.geometry().contains(pos):
                self._copy(content, preview_label)
                return
        if self._segment_areas:
            widget, content, preview_label = self._segment_areas[0]
            self._copy(content, preview_label)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        menu.addSeparator()
        pin_action = menu.addAction("取消置顶" if self.prompt.get("pinned") else "置顶")
        menu.addSeparator()

        color_menu = menu.addMenu("卡片颜色")
        color_actions = {}
        for name, hex_color in COLOR_PRESETS:
            act = color_menu.addAction(_color_swatch_icon(hex_color), name)
            color_actions[act] = hex_color

        folder_menu = menu.addMenu("移动到文件夹")
        folder_actions = {}
        current_folder = self.prompt.get("folder", "")
        uncat_act = folder_menu.addAction("未分类")
        uncat_act.setCheckable(True)
        uncat_act.setChecked(current_folder == "")
        folder_actions[uncat_act] = ""
        for f in self.folders:
            act = folder_menu.addAction(f)
            act.setCheckable(True)
            act.setChecked(f == current_folder)
            folder_actions[act] = f
        folder_menu.addSeparator()
        new_folder_action = folder_menu.addAction("新建文件夹...")

        action = menu.exec(event.globalPos())
        if action == edit_action:
            self.edit_requested.emit(self.prompt["id"])
        elif action == delete_action:
            self.delete_requested.emit(self.prompt["id"])
        elif action == pin_action:
            self.pin_toggled.emit(self.prompt["id"])
        elif action in color_actions:
            self.color_changed.emit(self.prompt["id"], color_actions[action])
        elif action in folder_actions:
            self.folder_changed.emit(self.prompt["id"], folder_actions[action])
        elif action == new_folder_action:
            self.folder_changed.emit(self.prompt["id"], "__new__")


# ---------------------------------------------------------------------------
# 新增 / 编辑 提示词的弹窗（支持多段，不再要求小标题）
# ---------------------------------------------------------------------------

class SegmentRow(QWidget):
    remove_requested = Signal(object)

    def __init__(self, content=""):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(3)

        top = QHBoxLayout()
        top.addStretch()
        self.remove_btn = QToolButton()
        self.remove_btn.setText("－ 删除本段")
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        top.addWidget(self.remove_btn)
        layout.addLayout(top)

        self.content_edit = QTextEdit()
        self.content_edit.setPlainText(content)
        self.content_edit.setFixedHeight(80)
        layout.addWidget(self.content_edit)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#eaeaf2;")
        layout.addWidget(line)

    def get_values(self):
        return self.content_edit.toPlainText().strip()


class PromptEditDialog(QDialog):
    def __init__(self, parent=None, prompt=None, style=""):
        super().__init__(parent)
        self.setWindowTitle("编辑提示词" if prompt else "新增提示词")
        self.resize(380, 480)
        self.setStyleSheet(style)
        self.segment_rows = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("标题："))
        self.title_edit = QLineEdit(prompt["title"] if prompt else "")
        layout.addWidget(self.title_edit)

        layout.addWidget(QLabel("提示词内容（可以添加多段，每段单独复制）："))

        self.segments_area = QScrollArea()
        self.segments_area.setWidgetResizable(True)
        self.segments_container = QWidget()
        self.segments_layout = QVBoxLayout(self.segments_container)
        self.segments_layout.addStretch()
        self.segments_area.setWidget(self.segments_container)
        layout.addWidget(self.segments_area, 1)

        segs = prompt.get("segments") if prompt else None
        if not segs:
            segs = [{"content": ""}]
        for seg in segs:
            self._add_segment_row(seg.get("content", ""))

        add_seg_btn = QPushButton("＋ 添加一段提示词")
        add_seg_btn.clicked.connect(lambda: self._add_segment_row())
        layout.addWidget(add_seg_btn)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _add_segment_row(self, content=""):
        row = SegmentRow(content)
        row.remove_requested.connect(self._remove_segment_row)
        self.segment_rows.append(row)
        self.segments_layout.insertWidget(self.segments_layout.count() - 1, row)
        self._update_remove_buttons()

    def _remove_segment_row(self, row):
        if len(self.segment_rows) <= 1:
            return
        self.segment_rows.remove(row)
        row.setParent(None)
        self._update_remove_buttons()

    def _update_remove_buttons(self):
        for row in self.segment_rows:
            row.remove_btn.setEnabled(len(self.segment_rows) > 1)

    def _on_save(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "提示", "标题不能为空")
            return
        if not any(r.get_values() for r in self.segment_rows):
            QMessageBox.warning(self, "提示", "至少填写一段提示词内容")
            return
        self.accept()

    def get_values(self):
        title = self.title_edit.text().strip()
        segments = []
        for r in self.segment_rows:
            c = r.get_values()
            if c:
                segments.append({"id": str(uuid.uuid4()), "content": c})
        return title, segments


# ---------------------------------------------------------------------------
# 快捷键设置
# ---------------------------------------------------------------------------

class HotkeyEdit(QLineEdit):
    def __init__(self, initial="", parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setPlaceholderText("点击后按下快捷键组合")
        self._value = initial
        self.setText(initial)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        mods = event.modifiers()
        parts = []
        if mods & Qt.ControlModifier:
            parts.append("Ctrl")
        if mods & Qt.AltModifier:
            parts.append("Alt")
        if mods & Qt.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.MetaModifier:
            parts.append("Win")
        if not parts:
            return
        key_name = QKeySequence(key).toString()
        if not key_name:
            return
        parts.append(key_name.upper())
        combo = "+".join(parts)
        self._value = combo
        self.setText(combo)

    def value(self):
        return self._value


# ---------------------------------------------------------------------------
# Cloudflare 云端同步客户端与弹窗
# ---------------------------------------------------------------------------

class CloudClient:
    @staticmethod
    def request(url, path, method="GET", data=None, token=None, timeout=10):
        full_url = url.rstrip("/") + path
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PromptDock/1.0",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(full_url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return True, res_data, ""
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                msg = err_body.get("error", str(e))
            except Exception:
                msg = str(e)
            return False, None, msg
        except Exception as e:
            return False, None, f"网络连接失败: {str(e)}"


class QuickCaptureDialog(QDialog):
    def __init__(self, initial_text="", folders=None, style="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("快速收录提示词")
        self.resize(360, 260)
        self.setStyleSheet(style)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.folders = folders or []
        self.result_title = ""
        self.result_content = ""
        self.result_folder = ""
        self._build_ui(initial_text)

    def _build_ui(self, initial_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        layout.addWidget(QLabel("标题："))
        first_line = initial_text.strip().split("\n")[0][:25] if initial_text else ""
        self.title_edit = QLineEdit(first_line)
        self.title_edit.setPlaceholderText("留空将自动提取首行")
        layout.addWidget(self.title_edit)

        layout.addWidget(QLabel("分类文件夹："))
        self.folder_combo = QComboBox()
        self.folder_combo.addItem("未分类", "")
        for f in self.folders:
            self.folder_combo.addItem(f, f)
        layout.addWidget(self.folder_combo)

        layout.addWidget(QLabel("收录内容："))
        self.content_edit = QTextEdit()
        self.content_edit.setPlainText(initial_text)
        layout.addWidget(self.content_edit, 1)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("取消 (Esc)")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("保存收录 (Enter)")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_save(self):
        content = self.content_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "提示", "收录内容不能为空")
            return
        title = self.title_edit.text().strip()
        if not title:
            title = content.split("\n")[0][:25].strip()
        self.result_title = title
        self.result_content = content
        self.result_folder = self.folder_combo.currentData()
        self.accept()


AVATAR_PRESETS = ["🤖", "🚀", "🌟", "🦊", "🐱", "🐼", "☕", "🎨", "🍀", "🎯"]


def make_circular_avatar(avatar_data=None, default_emoji="🤖", size=64, bg_color="#eef2ff", show_camera_badge=False):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    path = QPainterPath()
    path.addEllipse(1, 1, size - 2, size - 2)
    painter.setClipPath(path)
    painter.fillPath(path, QColor(bg_color))

    drawn = False
    if avatar_data:
        if isinstance(avatar_data, str) and (avatar_data.startswith("data:image") or len(avatar_data) > 60):
            try:
                b64_str = avatar_data.split(",", 1)[1] if "," in avatar_data else avatar_data
                raw = base64.b64decode(b64_str)
                img_pix = QPixmap()
                if img_pix.loadFromData(raw):
                    scaled = img_pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    sx = max(0, (scaled.width() - size) // 2)
                    sy = max(0, (scaled.height() - size) // 2)
                    painter.drawPixmap(0, 0, scaled.copy(sx, sy, size, size))
                    drawn = True
            except Exception:
                drawn = False
        elif isinstance(avatar_data, str) and os.path.exists(avatar_data):
            try:
                img_pix = QPixmap(avatar_data)
                if not img_pix.isNull():
                    scaled = img_pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    sx = max(0, (scaled.width() - size) // 2)
                    sy = max(0, (scaled.height() - size) // 2)
                    painter.drawPixmap(0, 0, scaled.copy(sx, sy, size, size))
                    drawn = True
            except Exception:
                drawn = False
        elif isinstance(avatar_data, str) and len(avatar_data) <= 4:
            font = QFont("Segoe UI Emoji", int(size * 0.44))
            painter.setFont(font)
            painter.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, avatar_data)
            drawn = True

    if not drawn:
        font = QFont("Segoe UI Emoji", int(size * 0.44))
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, default_emoji)

    painter.setClipping(False)
    pen = QPen(QColor("#cbd5e1"))
    pen.setWidthF(1.5)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(1, 1, size - 2, size - 2)

    if show_camera_badge:
        badge_r = int(size * 0.34)
        bx = size - badge_r - 1
        by = size - badge_r - 1

        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#cbd5e1"), 1.2))
        painter.drawEllipse(bx, by, badge_r, badge_r)

        painter.setBrush(QColor("#475569"))
        painter.setPen(Qt.NoPen)
        cw = badge_r * 0.54
        ch = badge_r * 0.40
        cx = bx + (badge_r - cw) / 2
        cy = by + (badge_r - ch) / 2 + 1
        painter.drawRoundedRect(QRectF(cx, cy, cw, ch), 1.5, 1.5)

        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QRectF(bx + badge_r * 0.36, by + badge_r * 0.38, badge_r * 0.28, badge_r * 0.28))

    painter.end()
    return pix


def image_file_to_base64_avatar(file_path, size=64):
    try:
        pix = QPixmap(file_path)
        if pix.isNull():
            return None
        scaled = pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        sx = max(0, (scaled.width() - size) // 2)
        sy = max(0, (scaled.height() - size) // 2)
        cropped = scaled.copy(sx, sy, size, size)
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        cropped.save(buf, "PNG")
        b64 = bytes(buf.data().toBase64()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


class AvatarSelectDialog(QDialog):
    def __init__(self, parent=None, current_avatar="🤖", style=""):
        super().__init__(parent)
        self.setWindowTitle("设置个性头像")
        self.setFixedSize(340, 310)
        self.setStyleSheet(style)
        self.selected_avatar = current_avatar or "🤖"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        preview_row = QHBoxLayout()
        preview_row.addStretch()
        self.preview_lbl = QLabel()
        self.preview_lbl.setFixedSize(68, 68)
        self._refresh_preview()
        preview_row.addWidget(self.preview_lbl)
        preview_row.addStretch()
        layout.addLayout(preview_row)

        hint = QLabel("点选精选预设，或从本地上传个性照片：")
        hint.setStyleSheet("font-size:11px; color:#6b7280;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        # 预设徽章 (两排)
        grid = QVBoxLayout()
        grid.setSpacing(6)
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        row1.setSpacing(6)
        row2.setSpacing(6)
        for i, em in enumerate(AVATAR_PRESETS):
            btn = QToolButton()
            btn.setText(em)
            btn.setFixedSize(34, 34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QToolButton { border:1px solid #e2e8f0; border-radius:8px; background:#fff; font-size:16px; }"
                "QToolButton:hover { background:#eef2ff; border-color:#818cf8; }"
            )
            btn.clicked.connect(lambda _c=False, e=em: self._set_emoji(e))
            if i < 5:
                row1.addWidget(btn)
            else:
                row2.addWidget(btn)
        grid.addLayout(row1)
        grid.addLayout(row2)
        layout.addLayout(grid)

        file_btn = QPushButton("📁 从本地电脑选择图片...")
        file_btn.setFixedHeight(34)
        file_btn.setCursor(Qt.PointingHandCursor)
        file_btn.setStyleSheet(
            "QPushButton { border:1px solid #cbd5e1; border-radius:8px; background:#fff; font-size:12px; color:#334155; font-weight:500; }"
            "QPushButton:hover { background:#f8fafc; border-color:#94a3b8; }"
        )
        file_btn.clicked.connect(self._pick_file)
        layout.addWidget(file_btn)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(64, 30)
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("保存头像")
        ok_btn.setFixedHeight(30)
        ok_btn.setStyleSheet("QPushButton { background:#4361ee; color:#fff; font-weight:600; border-radius:6px; padding:0 16px; border:none; }"
                             "QPushButton:hover { background:#3b52d4; }")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _refresh_preview(self):
        pix = make_circular_avatar(self.selected_avatar, size=68)
        self.preview_lbl.setPixmap(pix)

    def _set_emoji(self, emoji):
        self.selected_avatar = emoji
        self._refresh_preview()

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择头像图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp *.ico)"
        )
        if path:
            b64 = image_file_to_base64_avatar(path, size=64)
            if b64:
                self.selected_avatar = b64
                self._refresh_preview()


class ClickCopyLineEdit(QLineEdit):
    """点击即可一键通过默认浏览器进入该页面，同时自动复制全部文本并弹出提示"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("🌐 点击通过默认浏览器打开此页面 (并自动复制地址)")

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        text = self.text().strip()
        if text:
            import webbrowser
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.selectAll()
            try:
                webbrowser.open(text)
                QToolTip.showText(QCursor.pos(), "🌐 已在默认浏览器打开该页面 (并已复制地址)", self, QRect(), 2500)
            except Exception as e:
                QToolTip.showText(QCursor.pos(), f"✅ 已复制域名地址到剪贴板", self, QRect(), 2000)


class CloudSyncDialog(QDialog):
    def __init__(self, main_window, style=""):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Cloudflare 云端账号与同步")
        self.setFixedSize(450, 405)
        self.setStyleSheet(style)
        self._reg_avatar = "🤖"
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(10)

        # 1. 顶部 Header
        header_row = QHBoxLayout()
        header_icon = QLabel("☁️")
        header_icon.setStyleSheet("font-size:26px;")
        header_row.addWidget(header_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        dlg_title = QLabel("PromptDock 云端同步")
        dlg_title.setStyleSheet("font-size:16px; font-weight:700; color:#1e1b4b;")
        dlg_sub = QLabel("Cloudflare D1 驱动 · 多端实时备份与双向同步")
        dlg_sub.setStyleSheet("font-size:11px; color:#6b7280;")
        title_col.addWidget(dlg_title)
        title_col.addWidget(dlg_sub)
        header_row.addLayout(title_col)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        # 2. 未登录区域 (包含登录和注册的选项卡切换)
        self.auth_container = QWidget()
        auth_box_layout = QVBoxLayout(self.auth_container)
        auth_box_layout.setContentsMargins(0, 0, 0, 0)
        auth_box_layout.setSpacing(8)

        # 分段切换条 (Segmented Control)
        tab_row = QHBoxLayout()
        tab_row.setSpacing(4)
        self.tab_login_btn = QPushButton("账号登录")
        self.tab_reg_btn = QPushButton("注册新账号")
        for b in (self.tab_login_btn, self.tab_reg_btn):
            b.setCheckable(True)
            b.setFixedHeight(32)
            b.setCursor(Qt.PointingHandCursor)

        self.tab_login_btn.clicked.connect(lambda: self._switch_tab(0))
        self.tab_reg_btn.clicked.connect(lambda: self._switch_tab(1))
        tab_row.addWidget(self.tab_login_btn)
        tab_row.addWidget(self.tab_reg_btn)
        auth_box_layout.addLayout(tab_row)

        self.auth_stack = QStackedWidget()

        # Page 0: 登录页面
        login_page = QWidget()
        login_layout = QVBoxLayout(login_page)
        login_layout.setContentsMargins(0, 4, 0, 0)
        login_layout.setSpacing(8)

        login_tip = QLabel("登录已有云端账号，立刻同步您的所有提示词：")
        login_tip.setStyleSheet("font-size:12px; color:#6b7280;")
        login_layout.addWidget(login_tip)

        self.login_email_edit = QLineEdit()
        self.login_email_edit.setPlaceholderText("邮箱地址 (如: name@example.com)")
        self.login_email_edit.setFixedHeight(34)
        login_layout.addWidget(self.login_email_edit)

        self.login_pwd_edit = QLineEdit()
        self.login_pwd_edit.setEchoMode(QLineEdit.Password)
        self.login_pwd_edit.setPlaceholderText("输入密码")
        self.login_pwd_edit.setFixedHeight(34)
        self.login_pwd_edit.returnPressed.connect(self._on_login)
        login_layout.addWidget(self.login_pwd_edit)

        self.login_btn = QPushButton("🔑 登录并开启同步")
        self.login_btn.setFixedHeight(36)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(
            "QPushButton { background:#4361ee; color:#ffffff; font-weight:600; font-size:13px; border-radius:8px; border:none; }"
            "QPushButton:hover { background:#3b52d4; }"
        )
        self.login_btn.clicked.connect(self._on_login)
        login_layout.addWidget(self.login_btn)

        login_layout.addStretch()
        self.auth_stack.addWidget(login_page)

        # Page 1: 注册页面 (用心打造的注册界面与头像模块)
        reg_page = QWidget()
        reg_layout = QVBoxLayout(reg_page)
        reg_layout.setContentsMargins(0, 4, 0, 0)
        reg_layout.setSpacing(8)

        # 极简现代风头像区域 (居中 64px 精致圆形头像 + 悬浮相机角标)
        avatar_center_box = QVBoxLayout()
        avatar_center_box.setSpacing(4)
        avatar_center_box.setAlignment(Qt.AlignCenter)

        self.reg_avatar_btn = QToolButton()
        self.reg_avatar_btn.setFixedSize(64, 64)
        self.reg_avatar_btn.setCursor(Qt.PointingHandCursor)
        self.reg_avatar_btn.setIconSize(QSize(64, 64))
        self.reg_avatar_btn.setStyleSheet(
            "QToolButton { border:none; background:transparent; border-radius:32px; }"
            "QToolButton:hover { opacity:0.88; }"
        )
        self.reg_avatar_btn.setToolTip("点击设置个性头像（支持精选图标或本地照片）")
        self.reg_avatar_btn.clicked.connect(self._choose_local_avatar)
        self._refresh_reg_avatar_icon()
        avatar_center_box.addWidget(self.reg_avatar_btn, 0, Qt.AlignCenter)

        change_av_btn = QToolButton()
        change_av_btn.setText("设置头像 ▾")
        change_av_btn.setCursor(Qt.PointingHandCursor)
        change_av_btn.setStyleSheet(
            "QToolButton { border:none; background:transparent; color:#4361ee; font-size:11px; font-weight:600; padding:2px 6px; }"
            "QToolButton:hover { color:#3b52d4; text-decoration:underline; }"
        )
        change_av_btn.clicked.connect(self._choose_local_avatar)
        avatar_center_box.addWidget(change_av_btn, 0, Qt.AlignCenter)

        reg_layout.addLayout(avatar_center_box)

        # 注册表单输入框
        self.reg_nickname_edit = QLineEdit()
        self.reg_nickname_edit.setPlaceholderText("用户昵称 (选填，如: 小明)")
        self.reg_nickname_edit.setFixedHeight(34)
        reg_layout.addWidget(self.reg_nickname_edit)

        self.reg_email_edit = QLineEdit()
        self.reg_email_edit.setPlaceholderText("邮箱地址 (作为登录账号)")
        self.reg_email_edit.setFixedHeight(34)
        reg_layout.addWidget(self.reg_email_edit)

        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(6)
        self.reg_pwd_edit = QLineEdit()
        self.reg_pwd_edit.setEchoMode(QLineEdit.Password)
        self.reg_pwd_edit.setPlaceholderText("设置密码 (至少6位)")
        self.reg_pwd_edit.setFixedHeight(34)
        pwd_row.addWidget(self.reg_pwd_edit)

        self.reg_pwd2_edit = QLineEdit()
        self.reg_pwd2_edit.setEchoMode(QLineEdit.Password)
        self.reg_pwd2_edit.setPlaceholderText("确认密码")
        self.reg_pwd2_edit.setFixedHeight(34)
        self.reg_pwd2_edit.returnPressed.connect(self._on_register)
        pwd_row.addWidget(self.reg_pwd2_edit)
        reg_layout.addLayout(pwd_row)

        self.reg_btn = QPushButton("✨ 立即注册并开启云同步")
        self.reg_btn.setFixedHeight(38)
        self.reg_btn.setCursor(Qt.PointingHandCursor)
        self.reg_btn.setStyleSheet(
            "QPushButton { background:#4361ee; color:#ffffff; font-weight:600; font-size:13px; border-radius:8px; border:none; }"
            "QPushButton:hover { background:#3b52d4; }"
        )
        self.reg_btn.clicked.connect(self._on_register)
        reg_layout.addWidget(self.reg_btn)

        sec_tip = QLabel("🔒 密码经 PBKDF2/SHA-256 盐值哈希加密，云端绝不明文存储")
        sec_tip.setStyleSheet("font-size:10px; color:#9ca3af;")
        sec_tip.setAlignment(Qt.AlignCenter)
        reg_layout.addWidget(sec_tip)

        self.auth_stack.addWidget(reg_page)
        auth_box_layout.addWidget(self.auth_stack)
        main_layout.addWidget(self.auth_container)

        # 3. 已登录区域 (Logged-in User Area)
        self.logged_container = QWidget()
        logged_layout = QVBoxLayout(self.logged_container)
        logged_layout.setContentsMargins(0, 0, 0, 0)
        logged_layout.setSpacing(12)

        # 统一同步与账号状态卡片
        status_card = QFrame()
        status_card.setObjectName("StatusCard")
        status_card.setStyleSheet(
            "#StatusCard { background:#ffffff; border:1px solid #e5e7eb; border-radius:12px; }"
            "#StatusCard QLabel { border:none; background:transparent; }"
        )
        status_card.setMinimumHeight(138)
        scard_layout = QHBoxLayout(status_card)
        scard_layout.setContentsMargins(14, 12, 14, 12)
        scard_layout.setSpacing(12)

        # 左侧详细状态
        text_col = QVBoxLayout()
        text_col.setSpacing(5)

        self.account_label = QLabel("👤 当前账号: -")
        self.account_label.setStyleSheet("font-size:13px; color:#1f2937;")
        self.account_label.setFixedHeight(22)

        self.status_tag = QLabel("🟢 云端状态: Cloudflare D1 正常连接")
        self.status_tag.setStyleSheet("font-size:12px; color:#059669; font-weight:600;")
        self.status_tag.setFixedHeight(20)

        self.sync_time_label = QLabel("⏱️ 上次同步: 尚未同步")
        self.sync_time_label.setStyleSheet("font-size:12px; color:#4b5563;")
        self.sync_time_label.setFixedHeight(20)

        self.sync_count_label = QLabel("📦 本地提示词: 0 条")
        self.sync_count_label.setStyleSheet("font-size:12px; color:#4b5563;")
        self.sync_count_label.setFixedHeight(20)

        auto_tip = QLabel("💡 提示: 软件每 5 分钟在后台静默自动双向同步一次")
        auto_tip.setStyleSheet("font-size:11px; color:#9ca3af;")
        auto_tip.setFixedHeight(18)

        text_col.addWidget(self.account_label)
        text_col.addWidget(self.status_tag)
        text_col.addWidget(self.sync_time_label)
        text_col.addWidget(self.sync_count_label)
        text_col.addWidget(auto_tip)
        scard_layout.addLayout(text_col, 1)

        # 右侧头像展示与修改（图二位置）
        avatar_col = QVBoxLayout()
        avatar_col.setContentsMargins(0, 0, 0, 0)
        avatar_col.setSpacing(4)
        avatar_col.setAlignment(Qt.AlignCenter)

        self.logged_avatar_btn = QToolButton()
        self.logged_avatar_btn.setFixedSize(58, 58)
        self.logged_avatar_btn.setIconSize(QSize(58, 58))
        self.logged_avatar_btn.setCursor(Qt.PointingHandCursor)
        self.logged_avatar_btn.setStyleSheet("border:none; background:transparent; border-radius:29px;")
        self.logged_avatar_btn.setToolTip("点击更换头像")
        self.logged_avatar_btn.clicked.connect(self._change_logged_avatar)

        avatar_tip = QLabel("更换头像")
        avatar_tip.setAlignment(Qt.AlignCenter)
        avatar_tip.setStyleSheet("font-size:10px; color:#9ca3af;")

        avatar_col.addStretch()
        avatar_col.addWidget(self.logged_avatar_btn, 0, Qt.AlignCenter)
        avatar_col.addWidget(avatar_tip, 0, Qt.AlignCenter)
        avatar_col.addStretch()

        scard_layout.addLayout(avatar_col)
        logged_layout.addWidget(status_card)

        # 操作按钮
        self.sync_btn = QPushButton("☁️ 立即双向同步")
        self.sync_btn.setFixedHeight(38)
        self.sync_btn.setCursor(Qt.PointingHandCursor)
        self.sync_btn.setStyleSheet(
            "QPushButton { background:#4361ee; color:#ffffff; font-weight:600; font-size:13px; border-radius:8px; border:none; }"
            "QPushButton:hover { background:#3b52d4; }"
        )
        self.sync_btn.clicked.connect(self._on_sync_now)
        logged_layout.addWidget(self.sync_btn)

        self.logout_btn = QPushButton("退出当前账号")
        self.logout_btn.setFixedHeight(32)
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setStyleSheet(
            "QPushButton { background:#fff; color:#dc2626; border:1px solid #fecaca; border-radius:6px; font-size:12px; }"
            "QPushButton:hover { background:#fef2f2; border-color:#f87171; }"
        )
        self.logout_btn.clicked.connect(self._on_logout)
        logged_layout.addWidget(self.logout_btn)

        main_layout.addWidget(self.logged_container)

        main_layout.addStretch()

        # 4. 底部高级服务端设置（折叠面板）
        server_sec = QWidget()
        ssec_layout = QVBoxLayout(server_sec)
        ssec_layout.setContentsMargins(0, 0, 0, 0)
        ssec_layout.setSpacing(4)

        self.server_toggle_btn = QToolButton()
        self.server_toggle_btn.setText("⚙️ 高级配置：Cloudflare Worker 服务端地址 ▾")
        self.server_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.server_toggle_btn.setStyleSheet("border:none; color:#6b7280; font-size:11px; background:transparent;")
        self.server_toggle_btn.clicked.connect(self._toggle_server_box)
        ssec_layout.addWidget(self.server_toggle_btn)

        self.server_box = QWidget()
        sbox_layout = QHBoxLayout(self.server_box)
        sbox_layout.setContentsMargins(0, 0, 0, 0)
        sbox_layout.setSpacing(6)
        self.url_edit = ClickCopyLineEdit(self.main_window.settings.get("cloud_url", ""))
        self.url_edit.setPlaceholderText("https://promptdock-api.xxx.workers.dev")
        self.url_edit.setFixedHeight(30)
        self.url_edit.setStyleSheet(
            "QLineEdit { font-size:11px; padding: 0 8px; border: 1px solid #d1d5db; border-radius: 6px; background: #f9fafb; }"
            "QLineEdit:hover { border-color: #4361ee; background: #ffffff; }"
        )
        sbox_layout.addWidget(self.url_edit, 1)

        copy_url_btn = QPushButton("复制")
        copy_url_btn.setFixedSize(42, 30)
        copy_url_btn.setToolTip("复制当前服务域名地址")
        copy_url_btn.setCursor(Qt.PointingHandCursor)
        copy_url_btn.clicked.connect(self._copy_current_url)
        sbox_layout.addWidget(copy_url_btn)

        reset_url_btn = QPushButton("默认")
        reset_url_btn.setFixedSize(42, 30)
        reset_url_btn.setToolTip("恢复已部署的默认服务地址")
        reset_url_btn.setCursor(Qt.PointingHandCursor)
        reset_url_btn.clicked.connect(lambda: self.url_edit.setText("https://promptdock-api.wellshijian.workers.dev"))
        sbox_layout.addWidget(reset_url_btn)

        self.server_box.setVisible(False)
        ssec_layout.addWidget(self.server_box)
        main_layout.addWidget(server_sec)

        # 底部关闭按钮
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(70, 30)
        close_btn.clicked.connect(self.accept)
        bottom_row.addWidget(close_btn)
        main_layout.addLayout(bottom_row)

        self._switch_tab(0)
        self._refresh_ui()

    def _copy_current_url(self):
        url = self.url_edit.text().strip()
        if not url:
            url = "https://promptdock-api.wellshijian.workers.dev"
            self.url_edit.setText(url)
        QApplication.clipboard().setText(url)
        self.url_edit.selectAll()
        QToolTip.showText(QCursor.pos(), "✅ 已复制域名地址到剪贴板", self.url_edit, QRect(), 2000)

    def _update_dialog_size(self):
        email = self.main_window.settings.get("cloud_email", "").strip()
        token = self.main_window.settings.get("cloud_token", "").strip()
        is_logged = bool(email and token)

        width = 450
        if is_logged:
            # 保持固定高度，展开/折叠高级配置时卡片长度绝不发生改变与增长
            height = 405
        else:
            if self.auth_stack.currentIndex() == 1:
                height = 580
            else:
                height = 405
        self.setFixedSize(width, height)

    def _switch_tab(self, idx):
        self.auth_stack.setCurrentIndex(idx)
        ac = THEME_MAP.get(self.main_window.settings.get("theme", "默认"), THEME_MAP["默认"])[1]
        active_style = f"background:{ac}; color:#ffffff; font-weight:700; border-radius:6px; border:none;"
        inactive_style = "background:#f3f4f6; color:#4b5563; font-weight:500; border-radius:6px; border:none;"
        if idx == 0:
            self.tab_login_btn.setStyleSheet(active_style)
            self.tab_reg_btn.setStyleSheet(inactive_style)
        else:
            self.tab_login_btn.setStyleSheet(inactive_style)
            self.tab_reg_btn.setStyleSheet(active_style)
        self._update_dialog_size()

    def _toggle_server_box(self):
        to_show = self.server_box.isHidden()
        self.server_box.setVisible(to_show)
        arrow = "▴" if to_show else "▾"
        self.server_toggle_btn.setText(f"⚙️ 高级配置：Cloudflare Worker 服务端地址 {arrow}")
        self._update_dialog_size()

    def _refresh_reg_avatar_icon(self):
        pix = make_circular_avatar(self._reg_avatar, size=64, show_camera_badge=True)
        self.reg_avatar_btn.setIcon(QIcon(pix))

    def _set_reg_emoji(self, emoji):
        self._reg_avatar = emoji
        self._refresh_reg_avatar_icon()

    def _choose_local_avatar(self):
        dlg = AvatarSelectDialog(self, current_avatar=self._reg_avatar, style=self.styleSheet())
        if dlg.exec() == QDialog.Accepted and dlg.selected_avatar:
            self._reg_avatar = dlg.selected_avatar
            self._refresh_reg_avatar_icon()

    def _change_logged_avatar(self):
        current_av = self.main_window.settings.get("cloud_avatar", "") or "🤖"
        dlg = AvatarSelectDialog(self, current_avatar=current_av, style=self.styleSheet())
        if dlg.exec() == QDialog.Accepted and dlg.selected_avatar:
            self.main_window.settings["cloud_avatar"] = dlg.selected_avatar
            save_settings(self.main_window.settings)
            self._refresh_ui()
            self.main_window._run_cloud_sync(show_dialog_feedback=False)

    def _refresh_ui(self):
        email = self.main_window.settings.get("cloud_email", "").strip()
        token = self.main_window.settings.get("cloud_token", "").strip()
        nickname = self.main_window.settings.get("cloud_nickname", "").strip()
        avatar = self.main_window.settings.get("cloud_avatar", "").strip() or "🤖"
        last_sync = self.main_window.settings.get("last_sync_time", 0)

        if email and token:
            if nickname:
                self.account_label.setText(f"👤 当前账号: <b>{nickname}</b> <span style='color:#6b7280; font-size:11px;'>({email})</span>")
            else:
                self.account_label.setText(f"👤 当前账号: <b>{email}</b>")

            self.logged_avatar_btn.setIcon(QIcon(make_circular_avatar(avatar, size=58, show_camera_badge=True)))
            self.logged_avatar_btn.setIconSize(QSize(58, 58))

            active_prompts = [p for p in self.main_window.prompts if not p.get("is_deleted")]
            self.sync_count_label.setText(f"📦 本地提示词: {len(active_prompts)} 条")

            if last_sync > 0:
                dt = datetime.datetime.fromtimestamp(last_sync / 1000)
                self.sync_time_label.setText(f"⏱️ 上次同步: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                self.sync_time_label.setText("⏱️ 上次同步: 尚未同步")

            self.auth_container.setVisible(False)
            self.logged_container.setVisible(True)
        else:
            self.auth_container.setVisible(True)
            self.logged_container.setVisible(False)

        self._update_dialog_size()

        if hasattr(self.main_window, "title_bar"):
            self.main_window.title_bar.refresh_cloud_state()

    def _get_url(self):
        url = self.url_edit.text().strip()
        if not url:
            url = "https://promptdock-api.wellshijian.workers.dev"
            self.url_edit.setText(url)
        self.main_window.settings["cloud_url"] = url
        save_settings(self.main_window.settings)
        return url

    def _on_login(self):
        url = self._get_url()
        if not url:
            return
        email = self.login_email_edit.text().strip()
        pwd = self.login_pwd_edit.text().strip()
        if not email or not pwd:
            QMessageBox.warning(self, "提示", "请输入邮箱和密码")
            return
        ok, res, err = CloudClient.request(url, "/api/login", method="POST", data={"email": email, "password": pwd})
        if ok and res.get("token"):
            self.main_window.settings["cloud_token"] = res["token"]
            self.main_window.settings["cloud_email"] = res["email"]
            if res.get("nickname"):
                self.main_window.settings["cloud_nickname"] = res["nickname"]
            if res.get("avatar"):
                self.main_window.settings["cloud_avatar"] = res["avatar"]
            save_settings(self.main_window.settings)
            self._refresh_ui()
            display_name = self.main_window.settings.get("cloud_nickname") or res["email"]
            QMessageBox.information(self, "登录成功", f"欢迎回来，{display_name}！")
            self.main_window._run_cloud_sync(show_dialog_feedback=True)
        else:
            QMessageBox.warning(self, "登录失败", err or "账号或密码错误")

    def _on_register(self):
        url = self._get_url()
        if not url:
            return
        nickname = self.reg_nickname_edit.text().strip()
        email = self.reg_email_edit.text().strip()
        pwd = self.reg_pwd_edit.text().strip()
        pwd2 = self.reg_pwd2_edit.text().strip()

        if not email or "@" not in email:
            QMessageBox.warning(self, "提示", "请输入有效的邮箱地址")
            return
        if len(pwd) < 6:
            QMessageBox.warning(self, "提示", "密码长度不能少于 6 位")
            return
        if pwd != pwd2:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致，请核对")
            return

        ok, res, err = CloudClient.request(
            url, "/api/register", method="POST",
            data={
                "email": email,
                "password": pwd,
                "nickname": nickname,
                "avatar": self._reg_avatar
            }
        )
        if ok and res.get("token"):
            self.main_window.settings["cloud_token"] = res["token"]
            self.main_window.settings["cloud_email"] = res["email"]
            self.main_window.settings["cloud_nickname"] = nickname
            self.main_window.settings["cloud_avatar"] = self._reg_avatar
            save_settings(self.main_window.settings)
            self._refresh_ui()
            display_name = nickname or email
            QMessageBox.information(self, "注册成功", f"🎉 恭喜，{display_name}！\n账号注册成功并已自动登录，云端同步已就绪。")
            self.main_window._run_cloud_sync(show_dialog_feedback=True)
        else:
            QMessageBox.warning(self, "注册失败", err or "注册异常，请稍后重试")

    def _on_logout(self):
        if QMessageBox.question(self, "确认退出", "确定要退出当前云端账号吗？本地已有的提示词不会被删除。") == QMessageBox.Yes:
            self.main_window.settings["cloud_token"] = ""
            self.main_window.settings["cloud_email"] = ""
            self.main_window.settings["cloud_nickname"] = ""
            self.main_window.settings["cloud_avatar"] = ""
            self.main_window.settings["last_sync_time"] = 0
            save_settings(self.main_window.settings)
            self._refresh_ui()

    def _on_sync_now(self):
        url = self._get_url()
        if not url:
            return
        self.main_window._run_cloud_sync(show_dialog_feedback=True)
        self._refresh_ui()


# ---------------------------------------------------------------------------
# 应用内在线检查更新与同步升级引擎
# ---------------------------------------------------------------------------

class AppUpdateEngine:
    @staticmethod
    def parse_version(ver: str) -> tuple:
        parts = re.findall(r"\d+", str(ver or "0"))
        nums = [int(x) for x in parts[:4]]
        while len(nums) < 3:
            nums.append(0)
        return tuple(nums)

    @classmethod
    def is_newer(cls, remote_ver: str, local_ver: str = APP_VERSION) -> bool:
        return cls.parse_version(remote_ver) > cls.parse_version(local_ver)

    @staticmethod
    def _make_session(trust_env: bool = False) -> requests.Session:
        s = requests.Session()
        s.trust_env = trust_env
        try:
            s.verify = KuKuToolEngine.ensure_ca_bundle()
        except Exception:
            pass
        s.headers.update({
            "User-Agent": f"{APP_NAME}/{APP_VERSION}",
            "Accept": "application/json, */*",
        })
        return s

    @classmethod
    def check_update(cls) -> dict:
        """依次通过国内高速镜像节点与官方接口检查最新 Release 版本"""
        meta_urls = [
            f"https://github.com/{GITHUB_REPO}/releases/latest/download/version.json",
            f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json",
        ]
        last_err = None

        for trust_env in (False, True):
            s = cls._make_session(trust_env=trust_env)
            for node_name, prefix in GITHUB_MIRRORS:
                for raw_url in meta_urls:
                    target = f"{prefix}{raw_url}" if prefix else raw_url
                    try:
                        r = s.get(target, timeout=6)
                        if r.status_code == 200:
                            data = r.json()
                            remote_ver = str(data.get("version") or "").lstrip("vV").strip()
                            if remote_ver:
                                return {
                                    "has_update": cls.is_newer(remote_ver, APP_VERSION),
                                    "current_version": APP_VERSION,
                                    "latest_version": remote_ver,
                                    "notes": data.get("notes") or "包含功能优化与稳定性提升。",
                                    "sha256": str(data.get("sha256") or "").strip().lower(),
                                    "download_url": data.get("download_url") or f"https://github.com/{GITHUB_REPO}/releases/latest/download/PromptDock.exe",
                                    "published_at": data.get("published_at") or "",
                                    "node": node_name,
                                }
                    except Exception as e:
                        last_err = str(e)

        # 兜底：直接查询 GitHub Releases API
        try:
            s = cls._make_session(trust_env=True)
            r = s.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest", timeout=6)
            if r.status_code == 200:
                rel = r.json()
                tag = str(rel.get("tag_name") or "").lstrip("vV").strip()
                dl_url = f"https://github.com/{GITHUB_REPO}/releases/latest/download/PromptDock.exe"
                for asset in rel.get("assets") or []:
                    if str(asset.get("name", "")).lower() == "promptdock.exe":
                        dl_url = asset.get("browser_download_url") or dl_url
                        break
                if tag:
                    return {
                        "has_update": cls.is_newer(tag, APP_VERSION),
                        "current_version": APP_VERSION,
                        "latest_version": tag,
                        "notes": rel.get("body") or "包含功能优化与稳定性提升。",
                        "sha256": "",
                        "download_url": dl_url,
                        "published_at": rel.get("published_at") or "",
                        "node": "GitHub API",
                    }
        except Exception as e:
            last_err = str(e)

        raise RuntimeError(f"检查更新失败，请检查网络连接 ({last_err or '请求超时'})")

    @classmethod
    def download_update(cls, download_url: str, expected_sha256: str = "", progress_cb=None) -> str:
        """通过多条高速节点下载新版可执行文件，支持低速自动熔断切换与 SHA-256 完整性校验"""
        import tempfile
        tmp_dir = tempfile.gettempdir()
        target_file = os.path.join(tmp_dir, f"PromptDock_update_{int(time.time())}.exe")
        last_err = None

        # 优先尝试直连高速节点，若系统有代理随后兜底
        for trust_env in (False, True):
            s = cls._make_session(trust_env=trust_env)
            for node_name, prefix in GITHUB_MIRRORS:
                url = f"{prefix}{download_url}" if prefix else download_url
                env_tag = f"{node_name}(代理)" if trust_env else node_name
                try:
                    if progress_cb:
                        progress_cb(0, 0, f"正在连接 {env_tag}...")
                    r = s.get(url, stream=True, timeout=(5, 10))
                    if r.status_code not in (200, 206):
                        last_err = f"{env_tag} 返回 HTTP {r.status_code}"
                        r.close()
                        continue

                    total = int(r.headers.get("Content-Length", 0) or 0)
                    downloaded = 0
                    t_start = time.time()
                    t_last_ui = t_start
                    hasher = hashlib.sha256()
                    aborted_slow = False

                    with open(target_file, "wb") as f:
                        for chunk in r.iter_content(chunk_size=131072):
                            if not chunk:
                                continue
                            f.write(chunk)
                            hasher.update(chunk)
                            downloaded += len(chunk)
                            now = time.time()
                            elapsed = max(0.05, now - t_start)
                            speed_bps = downloaded / elapsed

                            # 若持续 5 秒以上且平均速度低于 120 KB/s，自动切换更快的节点
                            if elapsed > 5.0 and speed_bps < 120 * 1024 and downloaded < total:
                                aborted_slow = True
                                last_err = f"{env_tag} 速度过慢 ({speed_bps/1024:.0f} KB/s)"
                                break

                            if progress_cb and (now - t_last_ui >= 0.15 or (total and downloaded >= total)):
                                t_last_ui = now
                                sp_str = f"{speed_bps/(1024*1024):.1f} MB/s" if speed_bps >= 1024*1024 else f"{speed_bps/1024:.0f} KB/s"
                                progress_cb(downloaded, total, f"{env_tag} ({sp_str})")
                    r.close()

                    if aborted_slow:
                        try:
                            os.remove(target_file)
                        except Exception:
                            pass
                        continue

                    if downloaded < 1024 * 1024:
                        last_err = f"{env_tag} 下载文件体积异常"
                        try:
                            os.remove(target_file)
                        except Exception:
                            pass
                        continue

                    actual_sha = hasher.hexdigest().lower()
                    if expected_sha256 and actual_sha != expected_sha256.lower():
                        last_err = f"{env_tag} SHA-256 校验未通过"
                        try:
                            os.remove(target_file)
                        except Exception:
                            pass
                        continue

                    return target_file
                except Exception as e:
                    last_err = f"{env_tag}: {e}"
                    try:
                        if os.path.exists(target_file):
                            os.remove(target_file)
                    except Exception:
                        pass

        raise RuntimeError(f"所有下载节点均失败 ({last_err or '连接超时'})")

    @staticmethod
    def apply_update_and_restart(new_exe_path: str) -> bool:
        """在 Windows 下生成临时替换脚本：清除 PyInstaller 继承变量 -> 等待退出 -> 覆盖 exe -> 启动新版"""
        if not getattr(sys, "frozen", False):
            return False
        import subprocess
        import tempfile
        cur_exe = os.path.abspath(sys.executable)
        bat_path = os.path.join(tempfile.gettempdir(), f"promptdock_upgrade_{int(time.time())}.bat")
        script = (
            "@echo off\r\n"
            "chcp 65001 >nul\r\n"
            'set "_MEIPASS="\r\n'
            'set "_MEIPASS2="\r\n'
            'set "TCL_LIBRARY="\r\n'
            'set "TK_LIBRARY="\r\n'
            "timeout /t 2 /nobreak >nul\r\n"
            ":retry\r\n"
            f'move /y "{new_exe_path}" "{cur_exe}" >nul 2>&1\r\n'
            "if errorlevel 1 (\r\n"
            "    timeout /t 1 /nobreak >nul\r\n"
            "    goto retry\r\n"
            ")\r\n"
            f'start "" "{cur_exe}"\r\n'
            'del "%~f0"\r\n'
        )
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(script)

        clean_env = os.environ.copy()
        for k in ("_MEIPASS", "_MEIPASS2", "TCL_LIBRARY", "TK_LIBRARY", "_PYI_APPLICATION_HOME_DIR", "_PYI_PARENT_PROCESS_LEVEL"):
            clean_env.pop(k, None)

        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) | getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        subprocess.Popen(["cmd", "/c", bat_path], env=clean_env, creationflags=creation_flags, close_fds=True)
        return True


class UpdateCheckWorker(QThread):
    finished = Signal(dict)
    failed = Signal(str)

    def run(self):
        try:
            info = AppUpdateEngine.check_update()
            self.finished.emit(info)
        except Exception as e:
            self.failed.emit(str(e))


class UpdateDownloadWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, download_url: str, sha256: str = ""):
        super().__init__()
        self.download_url = download_url
        self.sha256 = sha256

    def run(self):
        try:
            path = AppUpdateEngine.download_update(
                self.download_url,
                self.sha256,
                progress_cb=lambda d, t, msg: self.progress.emit(d, t, msg),
            )
            self.finished.emit(path)
        except Exception as e:
            self.failed.emit(str(e))


class UpdateDialog(QDialog):
    def __init__(self, parent=None, initial_info: dict = None):
        super().__init__(parent)
        self.setWindowTitle(f"检查更新 - {APP_NAME}")
        self.setFixedSize(440, 330)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
            }
            QLabel { color: #cdd6f4; }
            QTextEdit {
                background-color: #2b2d42;
                border: 1px solid #3b3d54;
                border-radius: 8px;
                padding: 10px;
                color: #cdd6f4;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3b3d54;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4b4d66; }
            QPushButton#PrimaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a7cf8, stop:1 #6c5ce7);
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton#PrimaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #988bfb, stop:1 #7a6bf0);
            }
            QPushButton:disabled,
            QPushButton#PrimaryBtn:disabled {
                background: #2b2d42;
                background-color: #2b2d42;
                color: #6c7086;
                border: 1px solid #3b3d54;
                font-weight: normal;
            }
            QProgressBar {
                border: none;
                background-color: #2b2d42;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #6c5ce7;
                border-radius: 4px;
            }
        """)

        self.update_info = initial_info
        self.check_worker = None
        self.dl_worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        head = QHBoxLayout()
        title_lbl = QLabel(f"🚀 {APP_NAME} 在线更新")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        head.addWidget(title_lbl)
        head.addStretch(1)
        ver_lbl = QLabel(f"当前版本 v{APP_VERSION}")
        ver_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
        head.addWidget(ver_lbl)
        layout.addLayout(head)

        self.status_lbl = QLabel("正在连接国内高速节点检测最新版本...")
        self.status_lbl.setStyleSheet("color: #89b4fa; font-size: 13px; font-weight: bold;")
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)

        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setPlaceholderText("更新日志将在这里显示...")
        layout.addWidget(self.notes_edit, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        self.recheck_btn = QPushButton("🔄 重新检测")
        self.recheck_btn.setCursor(Qt.PointingHandCursor)
        self.recheck_btn.clicked.connect(self.start_check)
        btn_row.addWidget(self.recheck_btn)

        btn_row.addStretch(1)

        close_btn = QPushButton("关闭")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        self.sync_btn = QPushButton("⚡ 立即同步更新")
        self.sync_btn.setObjectName("PrimaryBtn")
        self.sync_btn.setCursor(Qt.PointingHandCursor)
        self.sync_btn.setEnabled(False)
        self.sync_btn.clicked.connect(self.start_download)
        btn_row.addWidget(self.sync_btn)

        layout.addLayout(btn_row)

        if initial_info:
            self._apply_info(initial_info)
        else:
            self.start_check()

    def start_check(self):
        self.recheck_btn.setEnabled(False)
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("检测中...")
        self.progress_bar.setVisible(False)
        self.status_lbl.setText("正在通过国内免梯子高速通道检测最新版本...")
        self.status_lbl.setStyleSheet("color: #89b4fa; font-size: 13px; font-weight: bold;")
        self.check_worker = UpdateCheckWorker()
        self.check_worker.finished.connect(self._on_check_finished)
        self.check_worker.failed.connect(self._on_check_failed)
        self.check_worker.start()

    def _on_check_finished(self, info: dict):
        self.recheck_btn.setEnabled(True)
        self._apply_info(info)

    def _on_check_failed(self, err: str):
        self.recheck_btn.setEnabled(True)
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("暂不可更新")
        self.status_lbl.setText(f"❌ {err}")
        self.status_lbl.setStyleSheet("color: #f38ba8; font-size: 13px; font-weight: bold;")

    def _apply_info(self, info: dict):
        self.update_info = info
        latest = info.get("latest_version", APP_VERSION)
        node = info.get("node", "")
        notes = info.get("notes") or "暂无更新说明"
        self.notes_edit.setPlainText(notes)
        if info.get("has_update"):
            self.status_lbl.setText(f"🎉 发现新版本 v{latest}！（当前 v{APP_VERSION} · {node}）")
            self.status_lbl.setStyleSheet("color: #a6e3a1; font-size: 13px; font-weight: bold;")
            self.sync_btn.setText("⚡ 立即同步更新")
            self.sync_btn.setEnabled(True)
        else:
            self.status_lbl.setText(f"✓ 当前已是最新版本 v{APP_VERSION}（检测通道：{node}）")
            self.status_lbl.setStyleSheet("color: #a6e3a1; font-size: 13px; font-weight: bold;")
            self.sync_btn.setText("✓ 已是最新版")
            self.sync_btn.setEnabled(False)

    def start_download(self):
        if not self.update_info:
            return
        self.sync_btn.setEnabled(False)
        self.recheck_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_lbl.setText("⏳ 正在连接国内高速镜像下载新版本...")
        self.status_lbl.setStyleSheet("color: #89b4fa; font-size: 13px; font-weight: bold;")

        self.dl_worker = UpdateDownloadWorker(
            self.update_info.get("download_url", ""),
            self.update_info.get("sha256", ""),
        )
        self.dl_worker.progress.connect(self._on_dl_progress)
        self.dl_worker.finished.connect(self._on_dl_finished)
        self.dl_worker.failed.connect(self._on_dl_failed)
        self.dl_worker.start()

    def _on_dl_progress(self, downloaded: int, total: int, label: str):
        if total > 0:
            self.progress_bar.setRange(0, 100)
            pct = min(100, int(downloaded * 100 / total))
            self.progress_bar.setValue(pct)
            mb_d = downloaded / (1024 * 1024)
            mb_t = total / (1024 * 1024)
            self.status_lbl.setText(f"📥 {label}：{mb_d:.1f} MB / {mb_t:.1f} MB ({pct}%)")
        else:
            self.progress_bar.setRange(0, 0)
            self.status_lbl.setText(f"📥 {label}...")

    def _on_dl_finished(self, new_exe_path: str):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.status_lbl.setText("✓ 下载与 SHA-256 安全校验通过，正在自动同步升级...")
        self.status_lbl.setStyleSheet("color: #a6e3a1; font-size: 13px; font-weight: bold;")

        if getattr(sys, "frozen", False):
            if AppUpdateEngine.apply_update_and_restart(new_exe_path):
                QTimer.singleShot(300, QApplication.instance().quit)
        else:
            self.recheck_btn.setEnabled(True)
            QMessageBox.information(
                self,
                "下载完成",
                f"当前为源码运行模式，新版程序已下载并校验通过：\n{new_exe_path}\n\n打包版 (.exe) 运行时将自动完成覆盖并重启。",
            )

    def _on_dl_failed(self, err: str):
        self.recheck_btn.setEnabled(True)
        self.sync_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_lbl.setText(f"❌ {err}")
        self.status_lbl.setStyleSheet("color: #f38ba8; font-size: 13px; font-weight: bold;")


class HotkeySettingsDialog(QDialog):
    def __init__(self, parent=None, current_main="", current_draft="", current_capture="", current_extractor="", current_schedule="", style=""):
        super().__init__(parent)
        self.setWindowTitle("设置快捷键")
        self.setFixedSize(340, 430)
        self.setStyleSheet(style)

        layout = QVBoxLayout(self)

        label1 = QLabel("呼出 / 隐藏悬浮窗：")
        layout.addWidget(label1)
        self.edit_main = HotkeyEdit(current_main)
        layout.addWidget(self.edit_main)

        label2 = QLabel("呼出全屏草稿纸：")
        layout.addWidget(label2)
        self.edit_draft = HotkeyEdit(current_draft)
        layout.addWidget(self.edit_draft)

        label3 = QLabel("全局划词快速收录：")
        layout.addWidget(label3)
        self.edit_capture = HotkeyEdit(current_capture)
        layout.addWidget(self.edit_capture)

        label4 = QLabel("视频无水印提取：")
        layout.addWidget(label4)
        self.edit_extractor = HotkeyEdit(current_extractor)
        layout.addWidget(self.edit_extractor)

        label5 = QLabel("任务排期表：")
        layout.addWidget(label5)
        self.edit_schedule = HotkeyEdit(current_schedule)
        layout.addWidget(self.edit_schedule)

        hint = QLabel("点击输入框，再按下想要的组合键（需包含 Ctrl / Alt / Shift 中至少一个）")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#999999; font-size:11px;")
        layout.addWidget(hint)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def main_value(self):
        return self.edit_main.value()

    def draft_value(self):
        return self.edit_draft.value()

    def capture_value(self):
        return self.edit_capture.value()

    def extractor_value(self):
        return self.edit_extractor.value()

    def schedule_value(self):
        return self.edit_schedule.value()


class AppearanceSettingsDialog(QDialog):
    def __init__(self, main_window, current_opacity, current_theme, style=""):
        super().__init__(main_window)
        self.main_window = main_window
        self._original_opacity = current_opacity
        self._original_theme = current_theme
        self._selected_theme = current_theme
        self.setWindowTitle("外观设置")
        self.setFixedSize(320, 280)
        self.setStyleSheet(style)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("窗口透明度："))
        row = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(30, 100)
        self.slider.setValue(int(current_opacity * 100))
        self.slider.valueChanged.connect(self._on_opacity_change)
        row.addWidget(self.slider)
        self.value_label = QLabel(f"{int(current_opacity * 100)}%")
        self.value_label.setFixedWidth(40)
        row.addWidget(self.value_label)
        layout.addLayout(row)

        layout.addWidget(QLabel("主题配色："))
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        self.theme_group = QButtonGroup(self)
        for name, tb, ac in THEME_PRESETS:
            btn = QToolButton()
            btn.setObjectName("ThemeSwatch")
            btn.setCheckable(True)
            btn.setChecked(name == current_theme)
            btn.setIcon(_theme_swatch_icon(tb, ac))
            btn.setIconSize(QSize(32, 32))
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked=False, n=name: self._on_theme_change(n))
            self.theme_group.addButton(btn)
            theme_row.addWidget(btn)
        theme_row.addStretch()
        layout.addLayout(theme_row)

        self.edge_dock_cb = QCheckBox("启用拖动贴边自动隐藏")
        self.edge_dock_cb.setChecked(self.main_window.settings.get("edge_dock", True))
        layout.addWidget(self.edge_dock_cb)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self._on_cancel)
        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_opacity_change(self, value):
        self.value_label.setText(f"{value}%")
        self.main_window.setWindowOpacity(value / 100)

    def _on_theme_change(self, name):
        self._selected_theme = name
        self.main_window.preview_theme(name)

    def _on_cancel(self):
        self.main_window.setWindowOpacity(self._original_opacity)
        self.main_window.preview_theme(self._original_theme)
        self.reject()

    def opacity_value(self):
        return self.slider.value() / 100

    def theme_value(self):
        return self._selected_theme

    def edge_dock_value(self):
        return self.edge_dock_cb.isChecked()


# ---------------------------------------------------------------------------
# 草稿纸：嵌在主窗口里的一个"内容页"（跟卡片列表共用同一个窗口/标题栏），
# 界面上没有常驻入口，只能通过快捷键切换进来/切回去。
# ---------------------------------------------------------------------------

class DraftTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        cursor = self.textCursor()
        if cursor.hasSelection():
            pairs = {
                "{": ("{", "}"),
                "}": ("{", "}"),
                "[": ("[", "]"),
                "]": ("[", "]"),
                "(": ("(", ")"),
                ")": ("(", ")"),
                '"': ('"', '"'),
                "'": ("'", "'"),
                "`": ("`", "`"),
                "《": ("《", "》"),
                "（": ("（", "）"),
                "【": ("【", "】"),
                "“": ("“", "”"),
            }
            char = event.text()
            if char in pairs:
                left, right = pairs[char]
                sel = cursor.selectedText()
                cursor.beginEditBlock()
                cursor.insertText(f"{left}{sel}{right}")
                cursor.endEditBlock()
                return
        super().keyPressEvent(event)


class DraftPadView(QWidget):
    def __init__(self, accent_color="#4361ee", on_exit_callback=None):
        super().__init__()
        self.on_exit_callback = on_exit_callback
        self._accent_color = accent_color
        self._current_font_size = 13
        self._search_matches = []
        self._search_index = -1
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_now)
        self._build_ui(accent_color)
        self._build_shortcuts()

    def _build_ui(self, accent_color):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        tool_style = (
            "QToolButton { border:1px solid #e3e3ec; border-radius:6px; padding:3px 5px; "
            "color:#444; background:#fff; font-size:12px; min-width:18px; }"
            "QToolButton:hover { background:#f5f5fa; }"
            "QToolButton:checked { background:#eef0fb; border-color:#c9cdf5; color:#4361ee; font-weight:700; }"
        )

        format_row = QHBoxLayout()
        format_row.setSpacing(4)

        self.bold_btn = QToolButton()
        self.bold_btn.setText("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setStyleSheet(tool_style + "QToolButton{font-weight:700; font-family:serif; min-width:18px;}")
        self.bold_btn.setToolTip("加粗 (Ctrl+B)")
        self.bold_btn.clicked.connect(self._toggle_bold)
        format_row.addWidget(self.bold_btn)

        size_down_btn = QToolButton()
        size_down_btn.setText("A-")
        size_down_btn.setStyleSheet(tool_style)
        size_down_btn.setToolTip("缩小字号 (Ctrl+-)")
        size_down_btn.clicked.connect(self._decrease_size)
        format_row.addWidget(size_down_btn)

        self.size_val_btn = QToolButton()
        self.size_val_btn.setText("13")
        self.size_val_btn.setStyleSheet(
            "QToolButton { border:1px solid #e3e3ec; border-radius:6px; padding:3px 2px; "
            "color:#6b7280; background:#f9fafb; font-size:11px; min-width:20px; }"
            "QToolButton:hover { background:#f3f4f6; color:#1f2937; }"
        )
        self.size_val_btn.setToolTip("当前字号（点击恢复默认 13pt / Ctrl+0）")
        self.size_val_btn.clicked.connect(self._reset_size)
        format_row.addWidget(self.size_val_btn)

        size_up_btn = QToolButton()
        size_up_btn.setText("A+")
        size_up_btn.setStyleSheet(tool_style)
        size_up_btn.setToolTip("放大字号 (Ctrl+=)")
        size_up_btn.clicked.connect(self._increase_size)
        format_row.addWidget(size_up_btn)

        self.heading_btn = QToolButton()
        self.heading_btn.setText("H")
        self.heading_btn.setStyleSheet(tool_style + "QToolButton{font-weight:700;}")
        self.heading_btn.setToolTip("切换标题 / 正文 (Ctrl+Shift+H)")
        self.heading_btn.clicked.connect(self._make_heading)
        format_row.addWidget(self.heading_btn)

        format_row.addStretch()

        self.back_btn = QToolButton()
        self.back_btn.setText("← 返回卡片")
        self.back_btn.setStyleSheet(
            f"QToolButton {{ border:1px solid #e3e3ec; border-radius:6px; padding:3px 8px; "
            f"color:{accent_color}; background:#fff; font-size:12px; font-weight:600; }}"
            f"QToolButton:hover {{ background:#f5f5fa; }}"
        )
        self.back_btn.setToolTip("返回提示词卡片列表 (Esc 或草稿快捷键)")
        self.back_btn.clicked.connect(self._on_back_clicked)
        format_row.addWidget(self.back_btn)

        layout.addLayout(format_row)

        # 查找/替换栏 (完全重构，支持黄色高亮与数量统计)
        self.find_bar = QFrame()
        self.find_bar.setStyleSheet(
            "QFrame { background:#ffffff; border:1px solid #d1d5db; border-radius:8px; padding:3px; }"
            "QLineEdit { border:1px solid #e5e7eb; border-radius:4px; padding:2px 5px; font-size:12px; }"
            "QLineEdit:focus { border-color:#6366f1; }"
        )
        find_layout = QVBoxLayout(self.find_bar)
        find_layout.setContentsMargins(4, 4, 4, 4)
        find_layout.setSpacing(4)

        find_row1 = QHBoxLayout()
        find_row1.setSpacing(3)

        find_icon = QLabel("🔍")
        find_icon.setStyleSheet("font-size:11px; color:#6b7280;")
        find_row1.addWidget(find_icon)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("查找关键词...")
        self.find_input.textChanged.connect(self._on_find_text_changed)
        self.find_input.returnPressed.connect(self._find_next)
        find_row1.addWidget(self.find_input, 1)

        self.find_count_label = QLabel("0/0")
        self.find_count_label.setStyleSheet("color:#6b7280; font-size:11px; padding:0 2px;")
        find_row1.addWidget(self.find_count_label)

        find_prev_btn = QToolButton()
        find_prev_btn.setText("↑")
        find_prev_btn.setToolTip("上一个 (Shift+Enter)")
        find_prev_btn.setStyleSheet(tool_style)
        find_prev_btn.clicked.connect(self._find_prev)
        find_row1.addWidget(find_prev_btn)

        find_next_btn = QToolButton()
        find_next_btn.setText("↓")
        find_next_btn.setToolTip("下一个 (Enter)")
        find_next_btn.setStyleSheet(tool_style)
        find_next_btn.clicked.connect(self._find_next)
        find_row1.addWidget(find_next_btn)

        self.replace_toggle_btn = QToolButton()
        self.replace_toggle_btn.setText("✏️")
        self.replace_toggle_btn.setCheckable(True)
        self.replace_toggle_btn.setStyleSheet(tool_style)
        self.replace_toggle_btn.setToolTip("展开/折叠替换栏 (Ctrl+H)")
        self.replace_toggle_btn.clicked.connect(self._toggle_replace_row)
        find_row1.addWidget(self.replace_toggle_btn)

        find_close_btn = QToolButton()
        find_close_btn.setText("✕")
        find_close_btn.setStyleSheet(tool_style)
        find_close_btn.setToolTip("关闭查找 (Esc)")
        find_close_btn.clicked.connect(self._hide_find_bar)
        find_row1.addWidget(find_close_btn)
        find_layout.addLayout(find_row1)

        # 替换行（按需展开）
        self.replace_row = QWidget()
        find_row2 = QHBoxLayout(self.replace_row)
        find_row2.setContentsMargins(0, 0, 0, 0)
        find_row2.setSpacing(3)

        replace_icon = QLabel("✏️")
        replace_icon.setStyleSheet("font-size:11px; color:#6b7280;")
        find_row2.addWidget(replace_icon)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("替换为...")
        self.replace_input.returnPressed.connect(self._replace_one)
        find_row2.addWidget(self.replace_input, 1)

        self.replace_btn = QToolButton()
        self.replace_btn.setText("替换")
        self.replace_btn.setStyleSheet(tool_style)
        self.replace_btn.clicked.connect(self._replace_one)
        find_row2.addWidget(self.replace_btn)

        self.replace_all_btn = QToolButton()
        self.replace_all_btn.setText("全换")
        self.replace_all_btn.setStyleSheet(tool_style)
        self.replace_all_btn.clicked.connect(self._replace_all)
        find_row2.addWidget(self.replace_all_btn)

        find_layout.addWidget(self.replace_row)
        self.replace_row.setVisible(False)

        self.find_bar.setVisible(False)
        layout.addWidget(self.find_bar)

        self.text_edit = DraftTextEdit()
        self.text_edit.setPlaceholderText("在这里随便写、随便改…")
        self.text_edit.setStyleSheet(
            "QTextEdit { background:#f5f6fa; border:1px solid #e3e3ec; border-radius:10px; "
            "padding:12px; font-size:13px; line-height:1.5; }"
        )
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.cursorPositionChanged.connect(self._sync_toolbar_state)
        layout.addWidget(self.text_edit, 1)

        btn_row = QHBoxLayout()
        self.word_count_label = QLabel("0 字")
        self.word_count_label.setStyleSheet("color:#999; font-size:11px;")
        btn_row.addWidget(self.word_count_label)
        btn_row.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet(
            "QPushButton { padding:6px 16px; border:1px solid #d8d8e0; border-radius:8px; color:#555; background:#fff; }"
            "QPushButton:hover { background:#f5f5fa; }"
        )
        clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(clear_btn)

        self.copy_btn = QPushButton("复制")
        self._set_copy_btn_style(accent_color)
        self.copy_btn.clicked.connect(self._on_copy)
        btn_row.addWidget(self.copy_btn)
        layout.addLayout(btn_row)

        self.find_input.installEventFilter(self)
        self.replace_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if self.find_bar.isVisible():
                self._hide_find_bar()
                return True
        return super().eventFilter(obj, event)

    def _build_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+B"), self.text_edit, self._toggle_bold)
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self._show_find_bar(replace_mode=False))
        QShortcut(QKeySequence("Ctrl+H"), self, lambda: self._show_find_bar(replace_mode=True))
        QShortcut(QKeySequence("Ctrl+="), self, self._increase_size)
        QShortcut(QKeySequence("Ctrl++"), self, self._increase_size)
        QShortcut(QKeySequence("Ctrl+-"), self, self._decrease_size)
        QShortcut(QKeySequence("Ctrl+0"), self, self._reset_size)
        QShortcut(QKeySequence("Ctrl+Shift+H"), self, self._make_heading)
        QShortcut(QKeySequence("Ctrl+Shift+K"), self, self._clean_text)

    def _set_copy_btn_style(self, accent_color):
        self._accent_color = accent_color
        self.copy_btn.setText("复制")
        self.copy_btn.setStyleSheet(
            "QPushButton {{ padding:6px 16px; border:none; border-radius:8px; color:white; background:{ac}; font-weight:600; }}"
            "QPushButton:hover {{ background:{ac}; }}".format(ac=accent_color)
        )

    def _on_back_clicked(self):
        if self.on_exit_callback:
            self.on_exit_callback()

    def apply_theme(self, accent_color):
        self._set_copy_btn_style(accent_color)
        if hasattr(self, "back_btn"):
            self.back_btn.setStyleSheet(
                f"QToolButton {{ border:1px solid #e3e3ec; border-radius:6px; padding:4px 10px; "
                f"color:{accent_color}; background:#fff; font-size:12px; font-weight:600; }}"
                f"QToolButton:hover {{ background:#f5f5fa; }}"
            )

    def load(self):
        self.text_edit.blockSignals(True)
        self.text_edit.setHtml(load_draft())
        self.text_edit.blockSignals(False)
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self._update_word_count()

    def flush_save(self):
        self._save_timer.stop()
        self._save_now()

    def _on_text_changed(self):
        self._save_timer.start(500)
        self._update_word_count()
        if self.find_bar.isVisible() and self.find_input.text():
            self._update_search_highlights()

    def _update_word_count(self):
        text = self.text_edit.toPlainText()
        count = len("".join(text.split()))
        self.word_count_label.setText(f"{count} 字")

    def _save_now(self):
        save_draft(self.text_edit.toHtml())

    def _on_clear(self):
        self.text_edit.clear()
        self._save_now()

    def _on_copy(self):
        text = self.text_edit.toPlainText()
        if not text:
            return
        QApplication.clipboard().setText(text)
        self.copy_btn.setText("✓ 已复制全部")
        self.copy_btn.setStyleSheet(
            "QPushButton { padding:6px 16px; border:none; border-radius:8px; color:white; background:#10b981; font-weight:600; }"
        )
        QTimer.singleShot(1500, lambda: self._set_copy_btn_style(self._accent_color))

    # -- 格式化工具栏 -----------------------------------------------------------
    def _sync_toolbar_state(self):
        self.bold_btn.setChecked(self.text_edit.fontWeight() == QFont.Bold)
        cur_size = int(self.text_edit.fontPointSize() or self._current_font_size)
        if cur_size > 0 and cur_size != self._current_font_size:
            self._current_font_size = cur_size
            self.size_val_btn.setText(str(cur_size))

    def _toggle_bold(self):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            current_weight = cursor.charFormat().fontWeight()
            new_weight = QFont.Normal if current_weight == QFont.Bold else QFont.Bold
            fmt = QTextCharFormat()
            fmt.setFontWeight(new_weight)
            cursor.mergeCharFormat(fmt)
            self.bold_btn.setChecked(new_weight == QFont.Bold)
        else:
            new_bold = not self.bold_btn.isChecked()
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Bold if new_bold else QFont.Normal)
            self.text_edit.mergeCurrentCharFormat(fmt)
            self.bold_btn.setChecked(new_bold)
        self.text_edit.setFocus()

    def _increase_size(self):
        self._adjust_size(1)

    def _decrease_size(self):
        self._adjust_size(-1)

    def _reset_size(self):
        self._set_font_size(13)

    def _adjust_size(self, delta):
        new_size = max(9, min(32, self._current_font_size + delta))
        self._set_font_size(new_size)

    def _set_font_size(self, size):
        self._current_font_size = size
        self.size_val_btn.setText(str(size))
        cursor = self.text_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.text_edit.mergeCurrentCharFormat(fmt)
        self.text_edit.setFocus()

    def _make_heading(self):
        cursor = self.text_edit.textCursor()
        is_heading = (cursor.charFormat().fontPointSize() >= 17 and cursor.charFormat().fontWeight() == QFont.Bold)
        fmt = QTextCharFormat()
        if is_heading:
            fmt.setFontPointSize(self._current_font_size)
            fmt.setFontWeight(QFont.Normal)
            fmt.setForeground(QColor("#242424"))
        else:
            fmt.setFontPointSize(18)
            fmt.setFontWeight(QFont.Bold)
            fmt.setForeground(QColor("#1e1b4b"))
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.mergeCharFormat(fmt)
        self.text_edit.setFocus()

    def _clean_text(self):
        text = self.text_edit.toPlainText()
        if not text:
            return
        cleaned = re.sub(r'\n{3,}', '\n\n', text)
        cleaned = '\n'.join([line.rstrip() for line in cleaned.splitlines()])
        if cleaned != text:
            cursor = self.text_edit.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.Document)
            cursor.insertText(cleaned)
            cursor.endEditBlock()
            self._save_now()
        if hasattr(self, "clean_btn"):
            self.clean_btn.setToolTip("✓ 文本已清洗")
            QTimer.singleShot(1500, lambda: self.clean_btn.setToolTip("一键清洗文本：清理空行与空格 (Ctrl+Shift+K)"))
        else:
            self.word_count_label.setText("✓ 文本已清洗")
            QTimer.singleShot(1500, self._update_word_count)

    # -- 查找 / 替换 -----------------------------------------------------------
    def _toggle_find_bar(self, replace_mode=False):
        if self.find_bar.isVisible():
            if replace_mode and not self.replace_row.isVisible():
                self.replace_row.setVisible(True)
                self.replace_toggle_btn.setChecked(True)
                self.replace_input.setFocus()
            else:
                self._hide_find_bar()
        else:
            self._show_find_bar(replace_mode)

    def _toggle_replace_row(self):
        show = not self.replace_row.isVisible()
        self.replace_row.setVisible(show)
        self.replace_toggle_btn.setChecked(show)
        if show:
            self.replace_input.setFocus()

    def _show_find_bar(self, replace_mode):
        self.find_bar.setVisible(True)
        self.replace_row.setVisible(replace_mode)
        self.replace_toggle_btn.setChecked(replace_mode)
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            self.find_input.setText(cursor.selectedText())
        self.find_input.setFocus()
        self.find_input.selectAll()
        self._update_search_highlights()

    def _hide_find_bar(self):
        self.find_bar.setVisible(False)
        self.text_edit.setExtraSelections([])
        self._search_matches = []
        self._search_index = -1
        self.text_edit.setFocus()

    def _on_find_text_changed(self):
        self._search_index = 0
        self._update_search_highlights()

    def _update_search_highlights(self):
        term = self.find_input.text()
        if not term:
            self._search_matches = []
            self._search_index = -1
            self.find_count_label.setText("0/0")
            self.text_edit.setExtraSelections([])
            return

        doc = self.text_edit.document()
        matches = []
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(term, cursor)
            if cursor.isNull():
                break
            matches.append(QTextCursor(cursor))

        self._search_matches = matches
        if not matches:
            self._search_index = -1
            self.find_count_label.setText("0/0")
            self.text_edit.setExtraSelections([])
            return

        if self._search_index < 0 or self._search_index >= len(matches):
            self._search_index = 0

        self._highlight_matches()

    def _highlight_matches(self):
        if not self._search_matches:
            self.text_edit.setExtraSelections([])
            return

        selections = []
        for idx, match_cursor in enumerate(self._search_matches):
            sel = QTextEdit.ExtraSelection()
            if idx == self._search_index:
                sel.format.setBackground(QColor("#facc15"))
                sel.format.setFontUnderline(True)
            else:
                sel.format.setBackground(QColor("#fef08a"))
            sel.cursor = match_cursor
            selections.append(sel)

        self.text_edit.setExtraSelections(selections)
        self.find_count_label.setText(f"{self._search_index + 1}/{len(self._search_matches)}")

        active_cursor = self._search_matches[self._search_index]
        self.text_edit.setTextCursor(active_cursor)
        self.text_edit.ensureCursorVisible()

    def _find_next(self):
        if not self._search_matches:
            self._update_search_highlights()
            return
        self._search_index = (self._search_index + 1) % len(self._search_matches)
        self._highlight_matches()

    def _find_prev(self):
        if not self._search_matches:
            self._update_search_highlights()
            return
        self._search_index = (self._search_index - 1) % len(self._search_matches)
        self._highlight_matches()

    def _replace_one(self):
        if not self._search_matches or self._search_index < 0:
            return
        replacement = self.replace_input.text()
        active_cursor = self._search_matches[self._search_index]
        active_cursor.beginEditBlock()
        active_cursor.insertText(replacement)
        active_cursor.endEditBlock()
        self._update_search_highlights()

    def _replace_all(self):
        term = self.find_input.text()
        if not term:
            return
        replacement = self.replace_input.text()
        doc = self.text_edit.document()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()
        search_cursor = QTextCursor(doc)
        cnt = 0
        while True:
            search_cursor = doc.find(term, search_cursor)
            if search_cursor.isNull():
                break
            search_cursor.insertText(replacement)
            cnt += 1
        cursor.endEditBlock()
        self._update_search_highlights()
        if cnt > 0:
            self.find_count_label.setText(f"已换{cnt}")


# ---------------------------------------------------------------------------
# 短视频 / 图集去水印提取 (KuKuTool 逆向引擎与内置面板)
# ---------------------------------------------------------------------------

try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass


class KuKuToolEngine:
    KEY = "12345678901234567890123456789013"
    STANDARD_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    CUSTOM_B64   = "ZYXABCDEFGHIJKLMNOPQRSTUVWzyxabcdefghijklmnopqrstuvw9876543210-_"
    CACHED_HASH  = "970b03"
    PREFERRED_TRUST_ENV = False
    _MEM_CACERT_PEM = None
    _ORIG_CERTIFI_PATH = None

    @classmethod
    def repair_tls_certificates(cls) -> str:
        """修复因 Windows 清理临时目录 (_MEIxxxxxx) 导致的 TLS CA 证书丢失问题"""
        import ssl
        persistent_ca = os.path.join(get_data_dir(), "cacert.pem")

        # 1. 记录并尝试读取原始 certifi 证书到内存缓存
        try:
            import certifi
            if cls._ORIG_CERTIFI_PATH is None:
                cls._ORIG_CERTIFI_PATH = certifi.where()
            if cls._MEM_CACERT_PEM is None:
                for candidate in (cls._ORIG_CERTIFI_PATH, persistent_ca):
                    if candidate and os.path.exists(candidate) and os.path.getsize(candidate) > 10240:
                        with open(candidate, "r", encoding="utf-8", errors="ignore") as f:
                            cls._MEM_CACERT_PEM = f.read()
                        break
        except Exception:
            pass

        # 2. 若内存和持久化目录都没有，直接从 Windows 系统根证书库导出 PEM 证书链
        if not cls._MEM_CACERT_PEM:
            pems = []
            try:
                for store_name in ("ROOT", "CA"):
                    for der, encoding, _ in ssl.enum_certificates(store_name):
                        if encoding == "x509_asn":
                            pems.append(ssl.DER_cert_to_PEM_cert(der))
            except Exception:
                pass
            if pems:
                cls._MEM_CACERT_PEM = "\n".join(pems)

        # 3. 写入持久化证书文件 (%APPDATA%\PromptDock\cacert.pem) 及恢复被删的 _MEI 临时证书
        if cls._MEM_CACERT_PEM:
            for target_path in (persistent_ca, cls._ORIG_CERTIFI_PATH):
                if not target_path:
                    continue
                try:
                    if not os.path.exists(target_path) or os.path.getsize(target_path) < 1024:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with open(target_path, "w", encoding="utf-8") as f:
                            f.write(cls._MEM_CACERT_PEM)
                except Exception:
                    pass

        # 4. 劫持环境变量与 requests / certifi 默认证书路径到持久化目录
        if os.path.exists(persistent_ca) and os.path.getsize(persistent_ca) > 1024:
            os.environ["REQUESTS_CA_BUNDLE"] = persistent_ca
            os.environ["SSL_CERT_FILE"] = persistent_ca
            os.environ["CURL_CA_BUNDLE"] = persistent_ca
            try:
                import certifi
                certifi.where = lambda: persistent_ca
            except Exception:
                pass
            try:
                import requests.utils
                import requests.adapters
                requests.utils.DEFAULT_CA_BUNDLE_PATH = persistent_ca
                requests.adapters.DEFAULT_CA_BUNDLE_PATH = persistent_ca
            except Exception:
                pass
            return persistent_ca
        return ""

    @classmethod
    def ensure_ca_bundle(cls):
        persistent_ca = os.path.join(get_data_dir(), "cacert.pem")
        if os.path.exists(persistent_ca) and os.path.getsize(persistent_ca) > 1024:
            return persistent_ca
        repaired = cls.repair_tls_certificates()
        if repaired and os.path.exists(repaired):
            return repaired
        return False

    @classmethod
    def extract_first_url(cls, text: str) -> str:
        if not text:
            return ""
        m = re.search(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&()*+,;=%]+", text)
        if m:
            return m.group(0).rstrip(".,!?;:)'\">]}")
        return text.strip()

    @classmethod
    def extract_all_urls(cls, text: str) -> list:
        if not text:
            return []
        matches = re.findall(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&()*+,;=%]+", text)
        urls = []
        seen = set()
        for raw in matches:
            u = raw.rstrip(".,!?;:)'\">]}")
            if u and u not in seen:
                seen.add(u)
                urls.append(u)
        return urls

    @classmethod
    def get_uwx_id(cls):
        return 'uwx_' + ''.join(random.choices('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=12))

    @classmethod
    def _make_session(cls, trust_env: bool = False) -> requests.Session:
        session = requests.Session()
        session.trust_env = trust_env
        session.verify = cls.ensure_ca_bundle()
        session.headers.update({
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "accept": "*/*",
            "referer": "https://dy.kukutool.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "content-type": "application/json",
            "accept-language": "zh-CN,zh;q=0.9",
            "origin": "https://dy.kukutool.com",
        })
        return session

    @classmethod
    def resolve_hash(cls, session: requests.Session) -> str:
        try:
            resp = session.get("https://dy.kukutool.com/", timeout=8)
            paths = re.findall(r'src="(/_next/static/chunks/[^"]+)"', resp.text)
            priority = [p for p in paths if any(k in p for k in ['7172', 'page', 'app', '7923', '7039'])]
            others = [p for p in paths if p not in priority]
            for path in (priority + others):
                try:
                    r = session.get(f"https://dy.kukutool.com{path}", timeout=6)
                    m = re.search(r'auth-([a-f0-9]{6})', r.text)
                    if m:
                        cls.CACHED_HASH = m.group(1)
                        return cls.CACHED_HASH
                except Exception:
                    continue
        except Exception:
            pass
        return cls.CACHED_HASH

    @classmethod
    def aes_gcm_encrypt(cls, params: dict, auth_key: str, auth_seed: str):
        key_bytes = hashlib.sha256(f'{auth_key}:{auth_seed}'.encode('utf-8')).digest()
        iv_bytes = os.urandom(12)
        plain_bytes = json.dumps(params, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=iv_bytes)
        cipher_bytes, tag_bytes = cipher.encrypt_and_digest(plain_bytes)
        return base64.b64encode(cipher_bytes + tag_bytes).decode('utf-8'), base64.b64encode(iv_bytes).decode('utf-8')

    @classmethod
    def decrypt_response(cls, data_str: str, iv_str: str) -> dict:
        data_x = "".join(chr(ord(ch) ^ 0x5A) for ch in data_str)
        iv_x = "".join(chr(ord(ch) ^ 0x5A) for ch in iv_str)

        def block_rev(s, b=8):
            return "".join(s[i:i+b][::-1] for i in range(0, len(s), b))

        data_r = block_rev(data_x)
        iv_r = block_rev(iv_x)

        data_m = "".join(cls.STANDARD_B64[idx] if (idx := cls.CUSTOM_B64.find(ch)) != -1 else ch for ch in data_r)
        iv_m = "".join(cls.STANDARD_B64[idx] if (idx := cls.CUSTOM_B64.find(ch)) != -1 else ch for ch in iv_r)

        key_bytes = hashlib.sha256(cls.KEY.encode("utf-8")).digest()
        cipher_bytes = base64.b64decode(data_m)
        iv_bytes = base64.b64decode(iv_m)

        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        dec = cipher.decrypt(cipher_bytes)
        plain = unpad(dec, AES.block_size)
        return json.loads(plain.decode("utf-8"))

    @classmethod
    def _parse_via_kuku(cls, url: str, trust_env: bool) -> dict:
        session = cls._make_session(trust_env=trust_env)
        uwx_id = cls.get_uwx_id()

        quote_token = None
        try:
            ent_resp = session.post(
                "https://dy.kukutool.com/api/parse-entitlement-status",
                json={"uwx_id": uwx_id, "page_path": "/", "request_url": url},
                timeout=6
            )
            if ent_resp.ok:
                quote_token = ent_resp.json().get("quoteToken")
        except Exception:
            pass

        current_hash = cls.CACHED_HASH
        auth_url = f"https://dy.kukutool.com/api/auth-{current_hash}"
        auth_resp = session.post(auth_url, json={"requestURL": url, "pagePath": "/", "mode": "single"}, timeout=10)

        if auth_resp.status_code in (404, 403) or f"k_{current_hash}" not in auth_resp.text:
            current_hash = cls.resolve_hash(session)
            auth_url = f"https://dy.kukutool.com/api/auth-{current_hash}"
            auth_resp = session.post(auth_url, json={"requestURL": url, "pagePath": "/", "mode": "single"}, timeout=10)

        auth_data = auth_resp.json()
        auth_key = auth_data.get(f"k_{current_hash}")
        auth_seed = auth_data.get(f"s_{current_hash}")

        if not auth_key or not auth_seed:
            err_msg = auth_data.get("message") or "授权校验未通过，请稍后重试"
            raise RuntimeError(f"KuKuTool: {err_msg}")

        params = {
            "requestURL": url,
            "captchaKey": "",
            "captchaInput": "",
            "totalSuccessCount": "0",
            "successCount": "0",
            "firstSuccessDate": "",
            "pagePath": "/",
            "uwx_id": uwx_id,
            "isMobile": "false",
            "geoipIp": "",
            "confirmPurchased": False,
            "qualityTier": "hd",
            "quoteToken": quote_token,
            "country_code": "CN",
        }
        payload, iv = cls.aes_gcm_encrypt(params, auth_key, auth_seed)

        parse_payload = {
            "version": 3,
            f"k_{current_hash}": auth_key,
            f"p_{current_hash}": payload,
            f"r_{current_hash}": 1,
            f"i_{current_hash}": iv
        }

        parse_resp = session.post("https://dy.kukutool.com/api/parse", json=parse_payload, timeout=15)
        res = parse_resp.json()

        if res.get("status") == 0 and res.get("encrypt") and res.get("data"):
            return cls.decrypt_response(res["data"], res["iv"])
        elif res.get("data") and isinstance(res.get("data"), dict):
            return res.get("data")
        else:
            msg = res.get("message") or res.get("error") or "视频解析失败，请检查链接是否有效或公开"
            raise RuntimeError(msg)

    @classmethod
    def _fallback_parse_douyin(cls, url: str) -> dict:
        s = requests.Session()
        s.trust_env = False
        s.verify = cls.ensure_ca_bundle()
        mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        s.headers.update({"User-Agent": mobile_ua})
        r = s.get(url, allow_redirects=True, timeout=10)
        final_url = r.url
        m_id = re.search(r'/(?:video|note|slides)/(\d+)', final_url) or re.search(r'modal_id=(\d+)', final_url) or re.search(r'(\d{19})', final_url)
        if m_id:
            vid = m_id.group(1)
            share_r = s.get(f"https://www.iesdouyin.com/share/video/{vid}/", timeout=10)
            m_router = re.search(r'window\._ROUTER_DATA\s*=\s*(\{.*?\})</script>', share_r.text, re.S)
            if m_router:
                router_data = json.loads(m_router.group(1))
                loader = router_data.get("loaderData", {})
                for k, v in loader.items():
                    if isinstance(v, dict) and "videoInfoRes" in v:
                        item_list = v["videoInfoRes"].get("item_list") or []
                        if item_list:
                            info = item_list[0]
                            desc = info.get("desc") or f"抖音视频_{vid}"
                            video_info = info.get("video") or {}
                            cover_urls = (video_info.get("cover") or {}).get("url_list") or []
                            cover = cover_urls[0] if cover_urls else ""
                            play_urls = (video_info.get("play_addr") or {}).get("url_list") or []
                            play_url = play_urls[0].replace("playwm", "play") if play_urls else ""
                            images_info = info.get("images") or []
                            pics = []
                            for img_item in images_info:
                                u_list = img_item.get("url_list") or []
                                if u_list:
                                    pics.append(u_list[-1])
                            if pics and not play_url:
                                return {"title": desc, "type": "images", "cover": cover or pics[0], "url": "", "pics": pics}
                            if play_url:
                                return {"title": desc, "type": "video", "cover": cover, "url": play_url, "videos": [{"url": play_url, "quality": "高清无水印"}], "pics": []}
        raise RuntimeError("抖音直连备用解析未获取到数据")

    @classmethod
    def _fallback_parse_bilibili(cls, url: str) -> dict:
        s = requests.Session()
        s.trust_env = False
        s.verify = cls.ensure_ca_bundle()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/"
        })
        if "b23.tv" in url:
            r_redir = s.get(url, allow_redirects=True, timeout=8)
            url = r_redir.url
        m_bv = re.search(r'(BV[0-9A-Za-z]{10})', url)
        if not m_bv:
            raise RuntimeError("未识别到有效的 B 站 BV 号")
        bvid = m_bv.group(1)
        r_view = s.get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", timeout=8).json()
        if r_view.get("code") != 0 or not r_view.get("data"):
            raise RuntimeError(r_view.get("message") or "B站视频信息获取失败")
        vdata = r_view["data"]
        cid = vdata.get("cid")
        title = vdata.get("title") or bvid
        cover = vdata.get("pic") or ""
        r_play = s.get(
            f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80&fnval=1&platform=html5&high_quality=1",
            timeout=8
        ).json()
        durl = (r_play.get("data") or {}).get("durl") or []
        if durl and durl[0].get("url"):
            vurl = durl[0]["url"]
            return {"title": title, "type": "video", "cover": cover, "url": vurl, "videos": [{"url": vurl, "quality": "高清 MP4"}], "pics": []}
        raise RuntimeError("B站直链获取失败")

    @classmethod
    def _fallback_parse_xiaohongshu(cls, url: str) -> dict:
        s = requests.Session()
        s.trust_env = False
        s.verify = cls.ensure_ca_bundle()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/"
        })
        r = s.get(url, allow_redirects=True, timeout=10)
        html = r.text
        m_state = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})</script>', html, re.S)
        if m_state:
            raw_json = m_state.group(1).replace(":undefined", ":null")
            state = json.loads(raw_json)
            note_map = (state.get("note") or {}).get("noteDetailMap") or {}
            for _, nd in note_map.items():
                note = (nd or {}).get("note") or {}
                if not note:
                    continue
                title = note.get("title") or note.get("desc") or "小红书笔记"
                video_obj = note.get("video") or {}
                streams = ((video_obj.get("media") or {}).get("stream") or {}).get("h264") or []
                if streams and isinstance(streams, list) and streams[0].get("masterUrl"):
                    vurl = streams[0]["masterUrl"]
                    img_list = note.get("imageList") or []
                    cover = (img_list[0].get("urlDefault") or img_list[0].get("urlPre") or "") if img_list else ""
                    return {"title": title, "type": "video", "cover": cover, "url": vurl, "videos": [{"url": vurl, "quality": "高清无水印"}], "pics": []}
                img_list = note.get("imageList") or []
                pics = [img.get("urlDefault") or img.get("urlPre") for img in img_list if isinstance(img, dict) and (img.get("urlDefault") or img.get("urlPre"))]
                if pics:
                    return {"title": title, "type": "images", "cover": pics[0], "url": "", "pics": pics}
        raise RuntimeError("小红书直连备用解析未获取到数据")

    @classmethod
    def diagnose_and_repair(cls) -> dict:
        """一键自检与修复：修复 TLS CA 证书链、测速直连/代理通道、拉取最新动态授权哈希、验证接口连通性"""
        ca_path = cls.repair_tls_certificates()
        best_trust = False
        best_latency_ms = None
        channel_results = {}

        for trust_env, label in ((False, "直连通道"), (True, "代理通道")):
            s = cls._make_session(trust_env=trust_env)
            t0 = time.time()
            try:
                r = s.get("https://dy.kukutool.com/api/maintenance-mode", timeout=5)
                ms = int((time.time() - t0) * 1000)
                if r.status_code == 200:
                    channel_results[label] = f"{ms}ms"
                    if best_latency_ms is None or ms < best_latency_ms:
                        best_latency_ms = ms
                        best_trust = trust_env
                else:
                    channel_results[label] = f"HTTP {r.status_code}"
            except Exception:
                channel_results[label] = "超时/不可用"

        cls.PREFERRED_TRUST_ENV = best_trust
        active_session = cls._make_session(trust_env=best_trust)
        new_hash = cls.resolve_hash(active_session)

        # 验证授权接口是否正常响应
        auth_ok = False
        try:
            test_auth = active_session.post(
                f"https://dy.kukutool.com/api/auth-{new_hash}",
                json={"requestURL": "https://www.bilibili.com/video/BV1GJ411x7h7", "pagePath": "/", "mode": "single"},
                timeout=6
            )
            if test_auth.ok and f"k_{new_hash}" in test_auth.text:
                auth_ok = True
        except Exception:
            pass

        return {
            "best_channel": "直连通道" if not best_trust else "代理通道",
            "latency_ms": best_latency_ms or 0,
            "hash": new_hash,
            "auth_ok": auth_ok,
            "tls_repaired": bool(ca_path),
            "details": channel_results,
        }

    @classmethod
    def parse(cls, input_text: str) -> dict:
        cls.ensure_ca_bundle()
        url = cls.extract_first_url(input_text)
        if not url:
            raise ValueError("未检测到有效网页链接，请粘贴完整的分享文字或网址！")

        overseas = any(d in url.lower() for d in ("youtube.com", "youtu.be", "tiktok.com", "instagram.com", "twitter.com", "x.com", "facebook.com"))
        if overseas:
            trust_order = [True, False]
        else:
            pref = cls.PREFERRED_TRUST_ENV
            trust_order = [pref, not pref]

        last_err = None
        for trust_env in trust_order:
            try:
                return cls._parse_via_kuku(url, trust_env=trust_env)
            except Exception as e:
                if "certificate" in str(e).lower() or "cacert.pem" in str(e).lower() or "tls" in str(e).lower():
                    cls.repair_tls_certificates()
                    try:
                        return cls._parse_via_kuku(url, trust_env=trust_env)
                    except Exception as e2:
                        last_err = e2
                else:
                    last_err = e

        # 若 KuKuTool 偶发上游故障，自动启用内置直连解析兜底
        low_url = url.lower()
        try:
            if "douyin.com" in low_url or "iesdouyin.com" in low_url:
                return cls._fallback_parse_douyin(url)
            elif "bilibili.com" in low_url or "b23.tv" in low_url:
                return cls._fallback_parse_bilibili(url)
            elif "xiaohongshu.com" in low_url or "xhslink.com" in low_url:
                return cls._fallback_parse_xiaohongshu(url)
        except Exception:
            pass

        raise RuntimeError(str(last_err) if last_err else "解析失败，请检查链接是否有效")


# 启动时立即初始化并持久化 TLS CA 证书链，防止临时目录被系统清理导致报错
KuKuToolEngine.repair_tls_certificates()


def _build_media_download_headers(url: str, custom_headers: dict = None) -> dict:
    if custom_headers:
        return dict(custom_headers)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
    }
    low = (url or "").lower()
    if any(k in low for k in ("bilivideo", "bilibili", "hdslb")):
        headers["Referer"] = "https://www.bilibili.com/"
    elif any(k in low for k in ("douyin", "byte", "snssdk", "amemv", "ixigua")):
        headers["Referer"] = "https://www.douyin.com/"
    elif any(k in low for k in ("xhscdn", "xiaohongshu")):
        headers["Referer"] = "https://www.xiaohongshu.com/"
    elif any(k in low for k in ("kwai", "kuaishou", "yximgs")):
        headers["Referer"] = "https://www.kuaishou.com/"
    elif "weibo" in low or "sinaimg" in low:
        headers["Referer"] = "https://weibo.com/"
    return headers


class MediaParseWorker(QThread):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, raw_input: str):
        super().__init__()
        self.raw_input = raw_input

    def run(self):
        try:
            data = KuKuToolEngine.parse(self.raw_input)
            self.finished.emit(data)
        except Exception as e:
            self.failed.emit(str(e))


class MediaRepairWorker(QThread):
    finished = Signal(dict)
    failed = Signal(str)

    def run(self):
        try:
            report = KuKuToolEngine.diagnose_and_repair()
            self.finished.emit(report)
        except Exception as e:
            self.failed.emit(str(e))


class MediaDownloadWorker(QThread):
    progress = Signal(int, int)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str, save_path: str, headers: dict = None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.headers = _build_media_download_headers(url, headers)

    def run(self):
        last_err = None
        for trust_env in (False, True):
            try:
                s = requests.Session()
                s.trust_env = trust_env
                s.verify = KuKuToolEngine.ensure_ca_bundle()
                r = s.get(self.url, headers=self.headers, stream=True, timeout=25)
                if r.status_code == 403 and "Referer" in self.headers:
                    hdr_no_ref = {k: v for k, v in self.headers.items() if k.lower() != "referer"}
                    r.close()
                    r = s.get(self.url, headers=hdr_no_ref, stream=True, timeout=25)
                if r.status_code not in (200, 206):
                    last_err = f"下载失败: HTTP {r.status_code}"
                    r.close()
                    continue
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                with open(self.save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            self.progress.emit(downloaded, total)
                r.close()
                self.finished.emit(self.save_path)
                return
            except Exception as e:
                last_err = str(e)
        self.failed.emit(last_err or "下载失败")


class MediaBatchDownloadWorker(QThread):
    progress = Signal(int, int)
    finished = Signal(int)
    failed = Signal(str)

    def __init__(self, urls: list, folder_path: str):
        super().__init__()
        self.urls = urls
        self.folder_path = folder_path

    def run(self):
        try:
            total = len(self.urls)
            success_count = 0
            s = requests.Session()
            s.trust_env = False
            s.verify = KuKuToolEngine.ensure_ca_bundle()
            for i, u in enumerate(self.urls):
                try:
                    headers = _build_media_download_headers(u)
                    r = s.get(u, headers=headers, timeout=15)
                    if r.status_code != 200:
                        s_proxy = requests.Session()
                        s_proxy.trust_env = True
                        s_proxy.verify = KuKuToolEngine.ensure_ca_bundle()
                        r = s_proxy.get(u, headers=headers, timeout=15)
                    if r.status_code == 200:
                        ext = ".jpg"
                        if ".png" in u.lower(): ext = ".png"
                        elif ".webp" in u.lower(): ext = ".webp"
                        filepath = os.path.join(self.folder_path, f"image_{i+1:02d}{ext}")
                        with open(filepath, "wb") as f:
                            f.write(r.content)
                        success_count += 1
                except Exception:
                    pass
                self.progress.emit(i + 1, total)
            self.finished.emit(success_count)
        except Exception as e:
            self.failed.emit(str(e))


class MediaBatchParseWorker(QThread):
    item_started = Signal(int, str)
    item_finished = Signal(int, dict)
    item_failed = Signal(int, str)
    all_finished = Signal(int, int)

    def __init__(self, urls: list):
        super().__init__()
        self.urls = urls
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        success_count = 0
        total = len(self.urls)
        for idx, u in enumerate(self.urls):
            if self._stop:
                break
            self.item_started.emit(idx, u)
            try:
                data = KuKuToolEngine.parse(u)
                success_count += 1
                self.item_finished.emit(idx, data)
            except Exception as e:
                self.item_failed.emit(idx, str(e))
        self.all_finished.emit(success_count, total)


class MediaMultiVideoDownloadWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(int, int, str)

    def __init__(self, items: list, folder_path: str):
        super().__init__()
        self.items = items  # list of (idx, data_dict)
        self.folder_path = folder_path

    def run(self):
        total = len(self.items)
        success_count = 0
        for step, (idx, data) in enumerate(self.items, 1):
            title = data.get("title") or f"media_{idx+1}"
            safe_title = sanitize_filename(title, 35)
            video_url = data.get("url") or ""
            pics = data.get("pics") or data.get("images") or []
            is_gallery = bool(pics and len(pics) > 0 and (not video_url or len(pics) > 1))

            self.progress.emit(step, total, f"正在下载 ({step}/{total}): {safe_title}")

            if video_url and not is_gallery:
                save_path = os.path.join(self.folder_path, f"{idx+1:02d}_{safe_title}.mp4")
                headers = _build_media_download_headers(video_url)
                ok = False
                for trust_env in (False, True):
                    try:
                        s = requests.Session()
                        s.trust_env = trust_env
                        s.verify = KuKuToolEngine.ensure_ca_bundle()
                        r = s.get(video_url, headers=headers, stream=True, timeout=25)
                        if r.status_code == 403 and "Referer" in headers:
                            hdr_no_ref = {k: v for k, v in headers.items() if k.lower() != "referer"}
                            r.close()
                            r = s.get(video_url, headers=hdr_no_ref, stream=True, timeout=25)
                        if r.status_code in (200, 206):
                            with open(save_path, "wb") as f:
                                for chunk in r.iter_content(chunk_size=65536):
                                    if chunk:
                                        f.write(chunk)
                            r.close()
                            ok = True
                            break
                        r.close()
                    except Exception:
                        pass
                if ok:
                    success_count += 1
            elif pics:
                sub_dir = os.path.join(self.folder_path, f"{idx+1:02d}_{safe_title}")
                os.makedirs(sub_dir, exist_ok=True)
                s = requests.Session()
                s.trust_env = False
                s.verify = KuKuToolEngine.ensure_ca_bundle()
                got_any = False
                for p_i, p_url in enumerate(pics, 1):
                    try:
                        headers = _build_media_download_headers(p_url)
                        r = s.get(p_url, headers=headers, timeout=15)
                        if r.status_code == 200:
                            ext = ".png" if ".png" in p_url.lower() else (".webp" if ".webp" in p_url.lower() else ".jpg")
                            with open(os.path.join(sub_dir, f"img_{p_i:02d}{ext}"), "wb") as f:
                                f.write(r.content)
                            got_any = True
                    except Exception:
                        pass
                if got_any:
                    success_count += 1

        self.finished.emit(success_count, total, self.folder_path)


def sanitize_filename(name: str, max_len: int = 40) -> str:
    if not name:
        return "media"
    clean = re.sub(r'[\r\n\t]+', ' ', name)
    clean = re.sub(r'[\\/:*?"<>|]', '', clean)
    clean = re.sub(r'[^\w\s\u4e00-\u9fa5\-_()（）\[\]【】]', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip('. ')
    clean = clean[:max_len].strip('. ')
    return clean or "media"


class MediaExtractorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("视频无水印提取")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
        self.resize(640, 540)
        self.setMinimumSize(540, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit {
                background-color: #2b2d42;
                border: 1px solid #3b3d54;
                border-radius: 8px;
                padding: 10px 12px;
                color: #ffffff;
                font-size: 13px;
                selection-background-color: #6c5ce7;
            }
            QLineEdit:focus {
                border: 1px solid #8075e8;
                background-color: #31334d;
            }
            QPushButton {
                background-color: #3b3d54;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
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
                padding: 9px 20px;
            }
            QPushButton#PrimaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #988bfb, stop:1 #7a6bf0);
            }
            QPushButton#PrimaryBtn:pressed {
                background: #5b4bd6;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QProgressBar {
                border: none;
                background-color: #2b2d42;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6c5ce7;
                border-radius: 4px;
            }
        """)

        self.current_data = None
        self.parse_worker = None
        self.dl_worker = None
        self.batch_worker = None
        self.repair_worker = None
        self.batch_parse_worker = None
        self.multi_dl_worker = None
        self.batch_mode = False
        self.batch_results = {}  # idx -> data dict
        self.batch_row_widgets = {}  # idx -> dict of UI refs
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 16)
        main_layout.setSpacing(12)

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
        back_btn.clicked.connect(self.close_and_return_to_main)
        header_layout.addWidget(back_btn)

        header_title = QLabel("🎬 视频无水印提取")
        header_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; margin-left: 6px;")
        header_layout.addWidget(header_title)

        header_layout.addStretch(1)

        self.repair_btn = QPushButton("🛠️ 一键修复")
        self.repair_btn.setCursor(Qt.PointingHandCursor)
        self.repair_btn.setToolTip("自动测速并切换直连/代理通道、更新最新解析密钥、重绑全局快捷键")
        self.repair_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2d42;
                border: 1px solid #f9e2af;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                color: #f9e2af;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b3d54;
                color: #ffffff;
                border-color: #fab387;
            }
        """)
        self.repair_btn.clicked.connect(self.run_self_repair)
        header_layout.addWidget(self.repair_btn)

        hotkey_tip = QLabel("快捷键: Shift+T / Esc 关闭")
        hotkey_tip.setStyleSheet("color: #6c7086; font-size: 12px; margin-left: 6px;")
        header_layout.addWidget(hotkey_tip)

        main_layout.addLayout(header_layout)

        # 模式切换栏：单条解析 vs 批量解析
        mode_bar = QHBoxLayout()
        mode_bar.setSpacing(8)

        self.btn_mode_single = QPushButton("⚡ 单条解析")
        self.btn_mode_single.setCursor(Qt.PointingHandCursor)
        self.btn_mode_single.clicked.connect(lambda: self.switch_mode(False))
        mode_bar.addWidget(self.btn_mode_single)

        self.btn_mode_batch = QPushButton("📦 批量解析")
        self.btn_mode_batch.setCursor(Qt.PointingHandCursor)
        self.btn_mode_batch.clicked.connect(lambda: self.switch_mode(True))
        mode_bar.addWidget(self.btn_mode_batch)

        sub_desc = QLabel("支持抖音、小红书、快手、B站等主流平台（粘贴多条链接将自动识别）")
        sub_desc.setStyleSheet("color: #a6adc8; font-size: 12px; margin-left: 8px;")
        mode_bar.addWidget(sub_desc, 1)

        main_layout.addLayout(mode_bar)

        # 单条输入容器
        self.single_input_widget = QWidget()
        input_row = QHBoxLayout(self.single_input_widget)
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setClearButtonEnabled(True)
        self.url_input.setPlaceholderText("粘贴含有短视频或图文的分享文字 / 网页链接...")
        self.url_input.returnPressed.connect(self.start_parse)
        input_row.addWidget(self.url_input, 1)

        clear_btn = QPushButton("✕ 清空")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b3d54;
                color: #f38ba8;
                border: none;
                border-radius: 8px;
                padding: 9px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #4b4d66;
                color: #ff99b0;
            }
        """)
        clear_btn.clicked.connect(self.clear_all)
        input_row.addWidget(clear_btn)

        paste_btn = QPushButton("📋 粘贴")
        paste_btn.setCursor(Qt.PointingHandCursor)
        paste_btn.clicked.connect(self.paste_from_clipboard)
        input_row.addWidget(paste_btn)

        self.parse_btn = QPushButton("⚡ 一键解析")
        self.parse_btn.setObjectName("PrimaryBtn")
        self.parse_btn.setCursor(Qt.PointingHandCursor)
        self.parse_btn.clicked.connect(self.start_parse)
        input_row.addWidget(self.parse_btn)

        main_layout.addWidget(self.single_input_widget)

        # 批量输入容器
        self.batch_input_widget = QWidget()
        batch_vbox = QVBoxLayout(self.batch_input_widget)
        batch_vbox.setContentsMargins(0, 0, 0, 0)
        batch_vbox.setSpacing(8)

        self.batch_text_edit = QTextEdit()
        self.batch_text_edit.setFixedHeight(96)
        self.batch_text_edit.setPlaceholderText("在此一次性粘贴多条分享口令或链接（每行一条，或直接粘贴多段混杂文字，系统会自动提取所有网址并去重）...")
        self.batch_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2b2d42;
                border: 1px solid #3b3d54;
                border-radius: 8px;
                padding: 8px 10px;
                color: #ffffff;
                font-size: 12px;
                selection-background-color: #6c5ce7;
            }
            QTextEdit:focus {
                border: 1px solid #8075e8;
                background-color: #31334d;
            }
        """)
        self.batch_text_edit.textChanged.connect(self._update_batch_link_count)
        batch_vbox.addWidget(self.batch_text_edit)

        batch_action_row = QHBoxLayout()
        batch_action_row.setSpacing(8)

        self.batch_count_lbl = QLabel("已识别 0 条链接")
        self.batch_count_lbl.setStyleSheet("color: #89b4fa; font-size: 12px; font-weight: bold;")
        batch_action_row.addWidget(self.batch_count_lbl)

        batch_action_row.addStretch(1)

        append_paste_btn = QPushButton("📋 追加粘贴")
        append_paste_btn.setCursor(Qt.PointingHandCursor)
        append_paste_btn.setToolTip("将剪贴板内容追加到下方新的一行，方便连续复制多条后一起解析")
        append_paste_btn.setStyleSheet("padding: 7px 12px; font-size: 12px;")
        append_paste_btn.clicked.connect(self.append_paste_to_batch)
        batch_action_row.addWidget(append_paste_btn)

        batch_clear_btn = QPushButton("✕ 清空")
        batch_clear_btn.setCursor(Qt.PointingHandCursor)
        batch_clear_btn.setStyleSheet("background-color: #3b3d54; color: #f38ba8; padding: 7px 12px; font-size: 12px; border-radius: 8px;")
        batch_clear_btn.clicked.connect(self.clear_all)
        batch_action_row.addWidget(batch_clear_btn)

        self.batch_copy_links_btn = QPushButton("🔗 复制全部直链")
        self.batch_copy_links_btn.setCursor(Qt.PointingHandCursor)
        self.batch_copy_links_btn.setStyleSheet("padding: 7px 12px; font-size: 12px;")
        self.batch_copy_links_btn.clicked.connect(self.batch_copy_all_direct_urls)
        self.batch_copy_links_btn.setEnabled(False)
        batch_action_row.addWidget(self.batch_copy_links_btn)

        self.batch_dl_all_btn = QPushButton("📥 一键下载全部")
        self.batch_dl_all_btn.setCursor(Qt.PointingHandCursor)
        self.batch_dl_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
            QPushButton:disabled {
                background-color: #2b2d42;
                color: #6c7086;
            }
        """)
        self.batch_dl_all_btn.clicked.connect(self.batch_download_all_parsed)
        self.batch_dl_all_btn.setEnabled(False)
        batch_action_row.addWidget(self.batch_dl_all_btn)

        self.batch_parse_btn = QPushButton("⚡ 开始批量解析")
        self.batch_parse_btn.setObjectName("PrimaryBtn")
        self.batch_parse_btn.setCursor(Qt.PointingHandCursor)
        self.batch_parse_btn.setStyleSheet("padding: 7px 16px; font-size: 12px;")
        self.batch_parse_btn.clicked.connect(self.start_batch_parse)
        batch_action_row.addWidget(self.batch_parse_btn)

        batch_vbox.addLayout(batch_action_row)
        main_layout.addWidget(self.batch_input_widget)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #fab387; font-size: 12px; min-height: 16px;")
        main_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.single_input_widget.setStyleSheet("background: transparent;")
        self.batch_input_widget.setStyleSheet("background: transparent;")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #1e1e2e; border: none;")
        self.scroll_area.viewport().setStyleSheet("background-color: #1e1e2e;")
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: #1e1e2e;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 4, 4, 4)
        self.scroll_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll_area, 1)

        self.empty_tip = QLabel("复制短视频或小红书链接后，点击【一键解析】即可获取无水印资源。")
        self.empty_tip.setAlignment(Qt.AlignCenter)
        self.empty_tip.setStyleSheet("color: #6c7086; font-size: 13px; margin-top: 40px;")
        self.scroll_layout.addWidget(self.empty_tip)

        self._refresh_mode_styles()

    def _save_my_pos(self):
        if self.parent() and hasattr(self.parent(), "settings"):
            _save_window_pos(self, self.parent().settings, "extractor_x", "extractor_y")

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.isVisible() and not self.isMinimized():
            self._save_my_pos()

    def close_cleanly(self):
        """仅关闭视频提取器本身，不影响主卡片原有显示/隐藏状态（与任务排期表一致）"""
        self._save_my_pos()
        self.hide()

    def close_and_return_to_main(self):
        """仅在用户主动点击左上角「← 返回卡片」时原位回到主窗口"""
        self._save_my_pos()
        cur_pos = self.pos()
        ext_w = self.width()
        self.hide()
        if self.parent():
            p = self.parent()
            if hasattr(p, "_cancel_edge_dock"):
                p._cancel_edge_dock()
            screen_obj = QGuiApplication.screenAt(cur_pos) or QApplication.primaryScreen()
            sg = screen_obj.availableGeometry()
            mw, mh = p.width(), p.height()
            tx = max(sg.x() - 16, min(cur_pos.x() + (ext_w - mw) // 2, sg.x() + sg.width() - mw + 16))
            ty = max(sg.y() - 16, min(cur_pos.y() - 16, sg.y() + sg.height() - mh + 16))
            p.move(tx, ty)
            p._normal_pos = QPoint(tx, ty)
            if hasattr(p, "settings"):
                _save_window_pos(p, p.settings, "window_x", "window_y")
            p.show()
            p.raise_()
            p.activateWindow()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                # 用户点击了窗口右上角最小化按钮 '_'
                # 立即缩到右下角托盘并隐藏窗口，彻底消除 Windows 弹出的浮动 MDI 缩略框
                self.hide()
                self.setWindowState(Qt.WindowNoState)
                if self.parent() and hasattr(self.parent(), "tray"):
                    self.parent().tray.showMessage(
                        "PromptDock",
                        "🎬 视频无水印提取已缩至右下角托盘 (按 Shift+T 再次呼出)",
                        QSystemTrayIcon.Information,
                        1500
                    )
                event.ignore()
                return
        super().changeEvent(event)

    def closeEvent(self, event):
        self.close_cleanly()
        event.accept()

    def reject(self):
        self.close_cleanly()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_cleanly()
        else:
            super().keyPressEvent(event)

    def switch_mode(self, batch: bool):
        self.batch_mode = bool(batch)
        self._refresh_mode_styles()

    def _refresh_mode_styles(self):
        active_css = "background-color: #6c5ce7; color: #ffffff; font-weight: bold; border-radius: 6px; padding: 6px 14px; font-size: 12px;"
        inactive_css = "background-color: #2b2d42; color: #a6adc8; border: 1px solid #3b3d54; border-radius: 6px; padding: 6px 14px; font-size: 12px;"
        if self.batch_mode:
            self.btn_mode_single.setStyleSheet(inactive_css)
            self.btn_mode_batch.setStyleSheet(active_css)
            self.single_input_widget.setVisible(False)
            self.batch_input_widget.setVisible(True)
        else:
            self.btn_mode_single.setStyleSheet(active_css)
            self.btn_mode_batch.setStyleSheet(inactive_css)
            self.single_input_widget.setVisible(True)
            self.batch_input_widget.setVisible(False)

    def _update_batch_link_count(self):
        urls = KuKuToolEngine.extract_all_urls(self.batch_text_edit.toPlainText())
        self.batch_count_lbl.setText(f"已识别 {len(urls)} 条链接")

    def append_paste_to_batch(self):
        cb = QApplication.clipboard()
        text = (cb.text() or "").strip()
        if not text:
            self.status_label.setText("⚠️ 剪贴板为空！")
            self.status_label.setStyleSheet("color: #fab387; font-size: 12px;")
            return
        cur = self.batch_text_edit.toPlainText().strip()
        new_text = f"{cur}\n{text}" if cur else text
        self.batch_text_edit.setPlainText(new_text)
        urls = KuKuToolEngine.extract_all_urls(new_text)
        self.status_label.setText(f"✓ 已追加粘贴，当前共识别 {len(urls)} 条有效链接")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")

    def clear_all(self):
        if self.batch_parse_worker and self.batch_parse_worker.isRunning():
            self.batch_parse_worker.stop()
        self.url_input.clear()
        self.batch_text_edit.clear()
        if self.batch_mode:
            self.batch_text_edit.setFocus()
        else:
            self.url_input.setFocus()
        self.status_label.setText("")
        self.progress_bar.setVisible(False)
        self.current_data = None
        self.batch_results.clear()
        self.batch_row_widgets.clear()
        self.batch_dl_all_btn.setEnabled(False)
        self.batch_copy_links_btn.setEnabled(False)
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        tip_text = "支持粘贴多条链接批量解析并一键下载全部视频。" if self.batch_mode else "复制短视频或小红书链接后，点击【一键解析】即可获取无水印资源。"
        self.empty_tip = QLabel(tip_text)
        self.empty_tip.setAlignment(Qt.AlignCenter)
        self.empty_tip.setStyleSheet("color: #6c7086; font-size: 13px; margin-top: 40px;")
        self.scroll_layout.addWidget(self.empty_tip)

    def _check_clipboard(self):
        pass  # 禁用自动从剪贴板填入内容，保持打开界面清爽空白

    def paste_from_clipboard(self):
        cb = QApplication.clipboard()
        text = (cb.text() or "").strip()
        if text:
            urls = KuKuToolEngine.extract_all_urls(text)
            if len(urls) > 1:
                self.switch_mode(True)
                self.batch_text_edit.setPlainText(text)
                self.start_batch_parse()
                return
            self.clear_all()
            self.url_input.setText(text)
            self.start_parse()

    def start_parse(self):
        text = self.url_input.text().strip()
        if not text:
            self.status_label.setText("⚠️ 请先输入或粘贴链接！")
            self.status_label.setStyleSheet("color: #fab387; font-size: 12px;")
            return

        urls = KuKuToolEngine.extract_all_urls(text)
        if len(urls) > 1:
            self.switch_mode(True)
            self.batch_text_edit.setPlainText(text)
            self.start_batch_parse()
            return

        self.status_label.setText("🔄 正在解析视频/图文数据，请稍候...")
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 12px;")
        self.parse_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.parse_worker = MediaParseWorker(text)
        self.parse_worker.finished.connect(self.on_parse_success)
        self.parse_worker.failed.connect(self.on_parse_failed)
        self.parse_worker.start()

    def on_parse_success(self, data: dict):
        self.parse_btn.setEnabled(True)
        self.current_data = data
        self.status_label.setText("✓ 解析成功！")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        self.render_result(data)

    def on_parse_failed(self, err_msg: str):
        self.parse_btn.setEnabled(True)
        self.status_label.setText(f"❌ {err_msg}")
        self.status_label.setStyleSheet("color: #f38ba8; font-size: 12px;")
        
        err_box = QFrame()
        err_box.setStyleSheet("background-color: #2b2d42; border: 1px solid #45475a; border-radius: 10px; padding: 16px;")
        err_vbox = QVBoxLayout(err_box)
        err_vbox.setSpacing(12)

        err_lbl = QLabel(f"解析出现问题：\n{err_msg}\n\n你可以点击下方【🛠️ 一键修复并重试】，自动检测最快网络通道并同步最新解析协议密钥。")
        err_lbl.setStyleSheet("color: #f38ba8; font-size: 13px; line-height: 1.5; border: none;")
        err_lbl.setWordWrap(True)
        err_vbox.addWidget(err_lbl)

        fix_retry_btn = QPushButton("🛠️ 一键修复解析通道并重试")
        fix_retry_btn.setCursor(Qt.PointingHandCursor)
        fix_retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #fab387;
                color: #1e1e2e;
                font-weight: bold;
                font-size: 13px;
                border-radius: 8px;
                padding: 9px 18px;
            }
            QPushButton:hover {
                background-color: #f9e2af;
            }
        """)
        fix_retry_btn.clicked.connect(self.run_self_repair)
        err_vbox.addWidget(fix_retry_btn, 0, Qt.AlignLeft)

        self.scroll_layout.addWidget(err_box)
        self.scroll_layout.addStretch(1)

    def run_self_repair(self):
        if self.repair_worker and self.repair_worker.isRunning():
            return
        self.repair_btn.setEnabled(False)
        self.repair_btn.setText("🔄 修复中...")
        self.parse_btn.setEnabled(False)
        self.status_label.setText("🛠️ 正在重建 TLS 证书链、检测直连/代理通道、更新解析密钥、重绑快捷键...")
        self.status_label.setStyleSheet("color: #f9e2af; font-size: 12px;")

        # 0. 立即重建并持久化 TLS CA 证书链（修复临时目录被系统清理导致的 cacert.pem 丢失）
        try:
            KuKuToolEngine.repair_tls_certificates()
        except Exception:
            pass

        # 1. 重新绑定主窗口全局快捷键
        if self.parent() and hasattr(self.parent(), "_register_hotkeys"):
            try:
                self.parent()._register_hotkeys()
            except Exception:
                pass

        # 2. 启动后台网络测速与协议哈希更新
        self.repair_worker = MediaRepairWorker()
        self.repair_worker.finished.connect(self.on_repair_finished)
        self.repair_worker.failed.connect(self.on_repair_failed)
        self.repair_worker.start()

    def on_repair_finished(self, report: dict):
        self.repair_btn.setEnabled(True)
        self.repair_btn.setText("🛠️ 一键修复")
        self.parse_btn.setEnabled(True)
        if hasattr(self, "batch_parse_btn"):
            self.batch_parse_btn.setEnabled(True)

        channel = report.get("best_channel", "直连通道")
        ms = report.get("latency_ms", 0)
        h = report.get("hash", "")
        msg = f"✓ 修复完成：TLS 证书已恢复 · 已切换【{channel} ({ms}ms)】· 密钥 auth-{h} · 快捷键已激活"
        self.status_label.setText(msg)
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")

        # 若输入框内已有链接，自动重新触发解析
        if getattr(self, "batch_mode", False):
            if hasattr(self, "batch_text_edit") and self.batch_text_edit.toPlainText().strip():
                QTimer.singleShot(400, self.start_batch_parse)
        else:
            if self.url_input.text().strip():
                QTimer.singleShot(400, self.start_parse)

    def on_repair_failed(self, err: str):
        self.repair_btn.setEnabled(True)
        self.repair_btn.setText("🛠️ 一键修复")
        self.parse_btn.setEnabled(True)
        if hasattr(self, "batch_parse_btn"):
            self.batch_parse_btn.setEnabled(True)
        self.status_label.setText(f"⚠️ 修复检测完成 (已重绑快捷键，网络提示: {err})")
        self.status_label.setStyleSheet("color: #fab387; font-size: 12px;")

    @staticmethod
    def _extract_video_qualities(data: dict) -> list:
        qualities = []
        # 1. 检查 KuKuTool 的 video_fullinfo 结构
        vf = data.get("video_fullinfo")
        if isinstance(vf, list) and vf:
            for item in vf:
                if isinstance(item, dict) and item.get("url"):
                    q_label = item.get("type") or item.get("quality") or item.get("name") or "清晰度"
                    size = item.get("size")
                    size_str = ""
                    if size:
                        if isinstance(size, (int, float)):
                            if size > 1024 * 1024:
                                size_str = f"({size / (1024*1024):.1f}MB)"
                            elif size > 1024:
                                size_str = f"({size / 1024:.1f}KB)"
                            else:
                                size_str = f"({size}B)"
                        else:
                            size_str = f"({size})"
                    qualities.append({
                        "url": item.get("url"),
                        "label": str(q_label),
                        "size_str": size_str
                    })
        # 2. 检查 videos 列表 (若每项有不同清晰度/链接)
        if not qualities:
            v_list = data.get("videos")
            if isinstance(v_list, list) and len(v_list) > 1:
                for idx, item in enumerate(v_list):
                    if isinstance(item, dict) and item.get("url"):
                        q_label = item.get("type") or item.get("quality") or item.get("definition") or f"清晰度 {idx+1}"
                        size = item.get("size")
                        size_str = f"({size})" if size else ""
                        qualities.append({
                            "url": item.get("url"),
                            "label": str(q_label),
                            "size_str": size_str
                        })
                    elif isinstance(item, str) and item.startswith("http"):
                        qualities.append({
                            "url": item,
                            "label": f"清晰度 {idx+1}",
                            "size_str": ""
                        })
        return qualities

    def render_result(self, data: dict):
        title = data.get("title") or "无标题媒体"
        video_url = data.get("url") or ""
        cover_url = data.get("cover") or ""
        pics = data.get("pics") or data.get("images") or []
        music_url = data.get("music") or data.get("audio") or ""
        is_gallery = bool(pics and len(pics) > 0 and (not video_url or len(pics) > 1))

        card = QFrame()
        card.setStyleSheet("background-color: #2b2d42; border-radius: 12px; padding: 14px;")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        title_row = QHBoxLayout()
        type_badge = QLabel("🖼️ 图集" if is_gallery else "🎬 视频")
        type_badge.setStyleSheet("background-color: #6c5ce7; color: #ffffff; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold;")
        title_row.addWidget(type_badge)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        title_lbl.setWordWrap(True)
        title_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title_row.addWidget(title_lbl, 1)

        copy_title_btn = QPushButton("📋 复制文案")
        copy_title_btn.setCursor(Qt.PointingHandCursor)
        copy_title_btn.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        copy_title_btn.clicked.connect(lambda: self.copy_text(title, "文案已复制！"))
        title_row.addWidget(copy_title_btn)

        card_layout.addLayout(title_row)

        if cover_url:
            preview_layout = QHBoxLayout()
            cover_lbl = QLabel()
            cover_lbl.setFixedSize(180, 110)
            cover_lbl.setStyleSheet("background-color: #1e1e2e; border-radius: 8px;")
            cover_lbl.setAlignment(Qt.AlignCenter)
            cover_lbl.setText("加载预览中...")
            preview_layout.addWidget(cover_lbl)

            def load_cover(url=cover_url, lbl=cover_lbl):
                try:
                    s = requests.Session()
                    s.trust_env = False
                    r = s.get(url, headers=_build_media_download_headers(url), timeout=8)
                    if r.status_code == 200:
                        img = QImage.fromData(r.content)
                        if not img.isNull():
                            pix = QPixmap.fromImage(img).scaled(180, 110, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                            lbl.setPixmap(pix)
                            return
                except Exception:
                    pass
                lbl.setText("暂无预览")

            threading.Thread(target=load_cover, daemon=True).start()

            action_vbox = QVBoxLayout()
            action_vbox.setSpacing(8)

            if video_url:
                dl_vid_btn = QPushButton("📥 下载无水印视频 (默认/最佳)")
                dl_vid_btn.setObjectName("PrimaryBtn")
                dl_vid_btn.setCursor(Qt.PointingHandCursor)
                dl_vid_btn.clicked.connect(lambda: self.download_video(video_url, title))
                action_vbox.addWidget(dl_vid_btn)

            if music_url:
                dl_music_btn = QPushButton("🎵 提取音频 (MP3)")
                dl_music_btn.setCursor(Qt.PointingHandCursor)
                dl_music_btn.setStyleSheet("padding: 7px 12px; font-size: 12px; background-color: #8b5cf6; color: #ffffff; font-weight: bold; border-radius: 6px; border: none;")
                dl_music_btn.clicked.connect(lambda: self.download_file(music_url, f"{title}_audio.mp3"))
                action_vbox.addWidget(dl_music_btn)

            if video_url:
                copy_link_btn = QPushButton("🔗 复制无水印视频直链")
                copy_link_btn.setCursor(Qt.PointingHandCursor)
                copy_link_btn.clicked.connect(lambda: self.copy_text(video_url, "视频直链已复制！"))
                action_vbox.addWidget(copy_link_btn)

            dl_cover_btn = QPushButton("🖼️ 下载高清封面")
            dl_cover_btn.setCursor(Qt.PointingHandCursor)
            dl_cover_btn.clicked.connect(lambda: self.download_file(cover_url, f"{title}_cover.jpg"))
            action_vbox.addWidget(dl_cover_btn)

            action_vbox.addStretch(1)
            preview_layout.addLayout(action_vbox, 1)
            card_layout.addLayout(preview_layout)

        # 多个清晰度选择区域（当检测到有多个分辨率时自动展示）
        qualities = self._extract_video_qualities(data)
        if qualities and len(qualities) > 1:
            q_box = QFrame()
            q_box.setStyleSheet("background-color: #1e1e2e; border: 1px solid #3b3d54; border-radius: 10px; padding: 12px; margin-top: 4px;")
            q_layout = QVBoxLayout(q_box)
            q_layout.setSpacing(10)

            q_title = QLabel("🎬 选择清晰度下载：")
            q_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #a6e3a1;")
            q_layout.addWidget(q_title)

            q_grid = QGridLayout()
            q_grid.setSpacing(8)
            for idx, q_info in enumerate(qualities):
                row = idx // 2
                col_base = (idx % 2) * 2

                q_url = q_info["url"]
                q_lbl = q_info["label"]
                q_size = q_info["size_str"]

                btn_text = f"下载  {q_lbl} {q_size}".strip()
                dl_q_btn = QPushButton(btn_text)
                dl_q_btn.setCursor(Qt.PointingHandCursor)
                dl_q_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #22c55e;
                        color: #ffffff;
                        font-weight: bold;
                        font-size: 12px;
                        padding: 8px 12px;
                        border-radius: 6px;
                        border: none;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #16a34a;
                    }
                """)
                dl_q_btn.clicked.connect(lambda checked, u=q_url, q=q_lbl: self.download_video(u, f"{title}_{q}"))
                q_grid.addWidget(dl_q_btn, row, col_base)

                copy_q_btn = QPushButton("复制")
                copy_q_btn.setCursor(Qt.PointingHandCursor)
                copy_q_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b82f6;
                        color: #ffffff;
                        font-weight: bold;
                        font-size: 12px;
                        padding: 8px 10px;
                        border-radius: 6px;
                        border: none;
                        min-width: 44px;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                """)
                copy_q_btn.clicked.connect(lambda checked, u=q_url, q=q_lbl: self.copy_text(u, f"{q_lbl} 视频直链已复制！"))
                q_grid.addWidget(copy_q_btn, row, col_base + 1)

            q_layout.addLayout(q_grid)
            card_layout.addWidget(q_box)

        if is_gallery:
            pics_count = len(pics)
            pics_hdr = QHBoxLayout()
            pics_title = QLabel(f"📸 图集原图 (共 {pics_count} 张无水印图片)")
            pics_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #a6adc8; margin-top: 6px;")
            pics_hdr.addWidget(pics_title)

            pics_hdr.addStretch(1)

            dl_all_btn = QPushButton("📥 批量下载全部原图")
            dl_all_btn.setObjectName("PrimaryBtn")
            dl_all_btn.setCursor(Qt.PointingHandCursor)
            dl_all_btn.setStyleSheet("padding: 6px 14px; font-size: 12px;")
            dl_all_btn.clicked.connect(lambda: self.batch_download_images(pics))
            pics_hdr.addWidget(dl_all_btn)

            copy_all_btn = QPushButton("🔗 复制所有图片链接")
            copy_all_btn.setCursor(Qt.PointingHandCursor)
            copy_all_btn.setStyleSheet("padding: 6px 14px; font-size: 12px;")
            copy_all_btn.clicked.connect(lambda: self.copy_text("\n".join(pics), "所有图片链接已复制！"))
            pics_hdr.addWidget(copy_all_btn)

            card_layout.addLayout(pics_hdr)

            thumb_scroll = QScrollArea()
            thumb_scroll.setFixedHeight(110)
            thumb_scroll.setWidgetResizable(True)
            thumb_scroll.setStyleSheet("background: transparent; border: none;")
            thumb_widget = QWidget()
            thumb_layout = QHBoxLayout(thumb_widget)
            thumb_layout.setContentsMargins(0, 4, 0, 4)
            thumb_layout.setSpacing(8)

            for idx, p_url in enumerate(pics[:12]):
                t_lbl = QLabel()
                t_lbl.setFixedSize(90, 90)
                t_lbl.setStyleSheet("background-color: #1e1e2e; border-radius: 6px;")
                t_lbl.setAlignment(Qt.AlignCenter)
                t_lbl.setText(f"图{idx+1}")
                thumb_layout.addWidget(t_lbl)

                def load_thumb(url=p_url, lbl=t_lbl):
                    try:
                        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
                        if r.status_code == 200:
                            img = QImage.fromData(r.content)
                            if not img.isNull():
                                pix = QPixmap.fromImage(img).scaled(90, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                                lbl.setPixmap(pix)
                    except Exception:
                        pass

                threading.Thread(target=load_thumb, daemon=True).start()

            thumb_layout.addStretch(1)
            thumb_scroll.setWidget(thumb_widget)
            card_layout.addWidget(thumb_scroll)

        self.scroll_layout.addWidget(card)
        self.scroll_layout.addStretch(1)

    def copy_text(self, text: str, tip: str = "已复制！"):
        QApplication.clipboard().setText(text)
        self.status_label.setText(f"✓ {tip}")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")

    def download_video(self, url: str, title: str):
        safe_title = sanitize_filename(title, 35)
        default_name = f"{safe_title}.mp4"
        save_path, _ = QFileDialog.getSaveFileName(self, "保存无水印视频", default_name, "MP4 视频 (*.mp4)")
        if not save_path:
            return

        self.status_label.setText(f"📥 正在下载视频: {os.path.basename(save_path)}...")
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 12px;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.dl_worker = MediaDownloadWorker(url, save_path)
        self.dl_worker.progress.connect(self.on_download_progress)
        self.dl_worker.finished.connect(self.on_download_finished)
        self.dl_worker.failed.connect(self.on_download_failed)
        self.dl_worker.start()

    def download_file(self, url: str, default_name: str):
        ext = ".jpg"
        if "." in default_name:
            base, ext = os.path.splitext(default_name)
        else:
            base = default_name
        safe_base = sanitize_filename(base, 35)
        safe_name = f"{safe_base}{ext}"
        save_path, _ = QFileDialog.getSaveFileName(self, "保存文件", safe_name, "所有文件 (*.*)")
        if not save_path:
            return

        self.status_label.setText(f"📥 正在保存: {os.path.basename(save_path)}...")
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 12px;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.dl_worker = MediaDownloadWorker(url, save_path)
        self.dl_worker.progress.connect(self.on_download_progress)
        self.dl_worker.finished.connect(self.on_download_finished)
        self.dl_worker.failed.connect(self.on_download_failed)
        self.dl_worker.start()

    def batch_download_images(self, urls: list):
        folder = QFileDialog.getExistingDirectory(self, "选择保存所有图片的文件夹")
        if not folder:
            return

        self.status_label.setText(f"📥 正在批量下载 {len(urls)} 张原图到所选文件夹...")
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 12px;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(urls))
        self.progress_bar.setValue(0)

        self.batch_worker = MediaBatchDownloadWorker(urls, folder)
        self.batch_worker.progress.connect(lambda cur, tot: self.progress_bar.setValue(cur))
        self.batch_worker.finished.connect(lambda cnt: self.on_batch_finished(cnt, folder))
        self.batch_worker.failed.connect(self.on_download_failed)
        self.batch_worker.start()

    def on_download_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int((downloaded / total) * 100)
            self.progress_bar.setValue(pct)
            mb_down = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self.status_label.setText(f"📥 下载中: {mb_down:.1f}MB / {mb_tot:.1f}MB ({pct}%)")

    def on_download_finished(self, save_path: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✓ 下载完成: {os.path.basename(save_path)}")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        QMessageBox.information(self, "下载完成", f"文件已成功保存至：\n{save_path}")

    def on_batch_finished(self, count: int, folder: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✓ 批量保存完成: 共保存 {count} 张图片！")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        QMessageBox.information(self, "批量下载完成", f"已成功保存 {count} 张无水印原图至：\n{folder}")

    def on_download_failed(self, err: str):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ 下载失败: {err}")
        self.status_label.setStyleSheet("color: #f38ba8; font-size: 12px;")

    # -- 批量解析与一键批量下载 -------------------------------------------------
    def start_batch_parse(self):
        raw_text = self.batch_text_edit.toPlainText().strip()
        urls = KuKuToolEngine.extract_all_urls(raw_text)
        if not urls:
            self.status_label.setText("⚠️ 未检测到有效链接，请在上方输入框粘贴一条或多条视频/图文分享链接！")
            self.status_label.setStyleSheet("color: #fab387; font-size: 12px;")
            return

        if self.batch_parse_worker and self.batch_parse_worker.isRunning():
            self.batch_parse_worker.stop()
            self.batch_parse_worker.wait(500)

        self.batch_results.clear()
        self.batch_row_widgets.clear()
        self.batch_dl_all_btn.setEnabled(False)
        self.batch_copy_links_btn.setEnabled(False)
        self.batch_parse_btn.setEnabled(False)

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(urls))
        self.progress_bar.setValue(0)
        self.status_label.setText(f"🔄 正在批量解析 {len(urls)} 条链接，请稍候...")
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 12px;")

        for idx, u in enumerate(urls):
            row_card, refs = self._create_batch_row_card(idx, u)
            self.batch_row_widgets[idx] = refs
            self.scroll_layout.addWidget(row_card)
        self.scroll_layout.addStretch(1)

        self.batch_parse_worker = MediaBatchParseWorker(urls)
        self.batch_parse_worker.item_started.connect(self._on_batch_item_started)
        self.batch_parse_worker.item_finished.connect(self._on_batch_item_finished)
        self.batch_parse_worker.item_failed.connect(self._on_batch_item_failed)
        self.batch_parse_worker.all_finished.connect(self._on_batch_all_finished)
        self.batch_parse_worker.start()

    def _create_batch_row_card(self, idx: int, url: str):
        card = QFrame()
        card.setStyleSheet("background-color: #2b2d42; border: 1px solid #3b3d54; border-radius: 10px; padding: 10px 12px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        idx_lbl = QLabel(f"#{idx + 1:02d}")
        idx_lbl.setStyleSheet("color: #7f849c; font-size: 12px; font-weight: bold; border: none;")
        idx_lbl.setFixedWidth(30)
        layout.addWidget(idx_lbl)

        badge = QLabel("⏳ 等待解析")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedWidth(78)
        badge.setStyleSheet("background-color: rgba(147,153,178,0.18); color: #a6adc8; border-radius: 5px; padding: 3px 6px; font-size: 11px; font-weight: bold; border: none;")
        layout.addWidget(badge)

        title_lbl = QLabel(url)
        title_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; border: none;")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl, 1)

        btn_box = QWidget()
        btn_box.setStyleSheet("border: none; background: transparent;")
        btn_layout = QHBoxLayout(btn_box)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)
        layout.addWidget(btn_box)

        refs = {
            "card": card,
            "badge": badge,
            "title_lbl": title_lbl,
            "btn_layout": btn_layout,
            "url": url,
        }
        return card, refs

    def _clear_layout_widgets(self, layout):
        while layout.count():
            it = layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def _on_batch_item_started(self, idx: int, url: str):
        refs = self.batch_row_widgets.get(idx)
        if not refs:
            return
        refs["badge"].setText("🔄 解析中")
        refs["badge"].setStyleSheet("background-color: rgba(137,180,250,0.2); color: #89b4fa; border-radius: 5px; padding: 3px 6px; font-size: 11px; font-weight: bold; border: none;")

    def _on_batch_item_finished(self, idx: int, data: dict):
        self.batch_results[idx] = data
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.batch_dl_all_btn.setEnabled(True)
        self.batch_copy_links_btn.setEnabled(True)

        refs = self.batch_row_widgets.get(idx)
        if not refs:
            return

        title = data.get("title") or "无标题媒体"
        video_url = data.get("url") or ""
        pics = data.get("pics") or data.get("images") or []
        is_gallery = bool(pics and len(pics) > 0 and (not video_url or len(pics) > 1))

        refs["badge"].setText("🖼️ 图集成功" if is_gallery else "✓ 视频成功")
        refs["badge"].setStyleSheet("background-color: rgba(166,227,161,0.2); color: #a6e3a1; border-radius: 5px; padding: 3px 6px; font-size: 11px; font-weight: bold; border: none;")
        refs["title_lbl"].setText(title)
        refs["title_lbl"].setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold; border: none;")

        btn_layout = refs["btn_layout"]
        self._clear_layout_widgets(btn_layout)

        if video_url and not is_gallery:
            dl_btn = QPushButton("📥 下载")
            dl_btn.setCursor(Qt.PointingHandCursor)
            dl_btn.setStyleSheet("background-color: #22c55e; color: #fff; font-size: 11px; font-weight: bold; padding: 5px 10px; border-radius: 5px;")
            dl_btn.clicked.connect(lambda _, u=video_url, t=title: self.download_video(u, t))
            btn_layout.addWidget(dl_btn)

            cp_url_btn = QPushButton("🔗 直链")
            cp_url_btn.setCursor(Qt.PointingHandCursor)
            cp_url_btn.setStyleSheet("background-color: #3b82f6; color: #fff; font-size: 11px; font-weight: bold; padding: 5px 10px; border-radius: 5px;")
            cp_url_btn.clicked.connect(lambda _, u=video_url: self.copy_text(u, "无水印视频直链已复制！"))
            btn_layout.addWidget(cp_url_btn)
        elif pics:
            dl_pics_btn = QPushButton(f"📥 下载图集({len(pics)})")
            dl_pics_btn.setCursor(Qt.PointingHandCursor)
            dl_pics_btn.setStyleSheet("background-color: #6c5ce7; color: #fff; font-size: 11px; font-weight: bold; padding: 5px 10px; border-radius: 5px;")
            dl_pics_btn.clicked.connect(lambda _, p=pics: self.batch_download_images(p))
            btn_layout.addWidget(dl_pics_btn)

        cp_title_btn = QPushButton("📋 文案")
        cp_title_btn.setCursor(Qt.PointingHandCursor)
        cp_title_btn.setStyleSheet("background-color: #3b3d54; color: #cdd6f4; font-size: 11px; padding: 5px 8px; border-radius: 5px;")
        cp_title_btn.clicked.connect(lambda _, t=title: self.copy_text(t, "文案已复制！"))
        btn_layout.addWidget(cp_title_btn)

    def _on_batch_item_failed(self, idx: int, err_msg: str):
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        refs = self.batch_row_widgets.get(idx)
        if not refs:
            return
        refs["badge"].setText("❌ 失败")
        refs["badge"].setStyleSheet("background-color: rgba(243,139,168,0.2); color: #f38ba8; border-radius: 5px; padding: 3px 6px; font-size: 11px; font-weight: bold; border: none;")
        refs["title_lbl"].setText(f"{refs['url']}  ({err_msg})")
        refs["title_lbl"].setStyleSheet("color: #f38ba8; font-size: 12px; border: none;")

        btn_layout = refs["btn_layout"]
        self._clear_layout_widgets(btn_layout)

        retry_btn = QPushButton("🔄 重试")
        retry_btn.setCursor(Qt.PointingHandCursor)
        retry_btn.setStyleSheet("background-color: #fab387; color: #1e1e2e; font-size: 11px; font-weight: bold; padding: 5px 10px; border-radius: 5px;")
        retry_btn.clicked.connect(lambda _, i=idx: self._retry_batch_single_item(i))
        btn_layout.addWidget(retry_btn)

    def _retry_batch_single_item(self, idx: int):
        refs = self.batch_row_widgets.get(idx)
        if not refs:
            return
        url = refs["url"]
        self._on_batch_item_started(idx, url)

        def _worker():
            try:
                data = KuKuToolEngine.parse(url)
                QTimer.singleShot(0, lambda: self._on_batch_item_finished(idx, data))
            except Exception as e:
                err = str(e)
                QTimer.singleShot(0, lambda: self._on_batch_item_failed(idx, err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_batch_all_finished(self, success_count: int, total: int):
        self.batch_parse_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        fail_count = total - success_count
        if fail_count == 0:
            self.status_label.setText(f"✓ 批量解析全部完成！共成功 {success_count}/{total} 条，可点击【📥 一键下载全部】保存")
            self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        else:
            self.status_label.setText(f"✓ 批量解析结束：成功 {success_count} 条 · 失败 {fail_count} 条（失败项可单独点击重试或点右上角一键修复）")
            self.status_label.setStyleSheet("color: #fab387; font-size: 12px;")

    def batch_copy_all_direct_urls(self):
        if not self.batch_results:
            return
        links = []
        for idx in sorted(self.batch_results.keys()):
            d = self.batch_results[idx]
            u = d.get("url")
            if u:
                links.append(u)
            else:
                pics = d.get("pics") or d.get("images") or []
                links.extend(pics)
        if not links:
            self.status_label.setText("⚠️ 暂无可复制的直链")
            return
        QApplication.clipboard().setText("\n".join(links))
        self.status_label.setText(f"✓ 已复制全部 {len(links)} 条无水印直链到剪贴板！")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")

    def batch_download_all_parsed(self):
        if not self.batch_results:
            return
        folder = QFileDialog.getExistingDirectory(self, "选择批量保存无水印视频/图集的文件夹")
        if not folder:
            return

        items = [(idx, self.batch_results[idx]) for idx in sorted(self.batch_results.keys())]
        self.batch_dl_all_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(items))
        self.progress_bar.setValue(0)
        self.status_label.setText(f"📥 正在批量下载 {len(items)} 项无水印资源到所选文件夹...")
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 12px;")

        self.multi_dl_worker = MediaMultiVideoDownloadWorker(items, folder)
        self.multi_dl_worker.progress.connect(self._on_multi_dl_progress)
        self.multi_dl_worker.finished.connect(self._on_multi_dl_finished)
        self.multi_dl_worker.start()

    def _on_multi_dl_progress(self, step: int, total: int, msg: str):
        self.progress_bar.setValue(step - 1)
        self.status_label.setText(f"📥 {msg}")

    def _on_multi_dl_finished(self, success_count: int, total: int, folder: str):
        self.progress_bar.setVisible(False)
        self.batch_dl_all_btn.setEnabled(True)
        self.status_label.setText(f"✓ 批量下载完成：成功保存 {success_count}/{total} 项至 {folder}")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        QMessageBox.information(self, "批量下载完成", f"已成功批量下载 {success_count}/{total} 项无水印视频/图集至：\n{folder}")


# ---------------------------------------------------------------------------
# 标题栏
# ---------------------------------------------------------------------------

class TitleBar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("TitleBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(46)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 8, 6)
        layout.setSpacing(6)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText("搜索")
        self.search_box.setFixedWidth(120)
        self.search_box.textChanged.connect(lambda _t: self.main_window.render_cards())
        layout.addWidget(self.search_box)

        layout.addStretch(1)

        self.draft_btn = QToolButton()
        self.draft_btn.setObjectName("TitleBtn")
        self.draft_btn.setIcon(QIcon(draw_titlebar_icon("draft")))
        self.draft_btn.setIconSize(QSize(16, 16))
        self.draft_btn.setToolTip("快速草稿纸 (Shift+X)")
        self.draft_btn.clicked.connect(self.main_window.open_draft_pad)
        layout.addWidget(self.draft_btn)

        self.media_btn = QToolButton()
        self.media_btn.setObjectName("TitleBtn")
        self.media_btn.setIcon(QIcon(draw_titlebar_icon("media")))
        self.media_btn.setIconSize(QSize(16, 16))
        self.media_btn.setToolTip("视频无水印提取 (Shift+T)")
        self.media_btn.clicked.connect(self.main_window.open_media_extractor)
        layout.addWidget(self.media_btn)

        self.schedule_btn = QToolButton()
        self.schedule_btn.setObjectName("TitleBtn")
        self.schedule_btn.setIcon(QIcon(draw_titlebar_icon("schedule")))
        self.schedule_btn.setIconSize(QSize(16, 16))
        self.schedule_btn.setToolTip("任务排期表 (Shift+A)")
        self.schedule_btn.clicked.connect(self.main_window.toggle_schedule_pad)
        layout.addWidget(self.schedule_btn)

        self.cloud_btn = QToolButton()
        self.cloud_btn.setObjectName("TitleBtn")
        self.cloud_btn.setIcon(QIcon(draw_titlebar_icon("cloud")))
        self.cloud_btn.setIconSize(QSize(16, 16))
        self.cloud_btn.setToolTip("Cloudflare 云端同步与账号")
        self.cloud_btn.clicked.connect(self.main_window.open_cloud_sync_dialog)
        layout.addWidget(self.cloud_btn)

        self.pin_btn = QToolButton()
        self.pin_btn.setObjectName("TitleBtn")
        self.pin_btn.setIconSize(QSize(16, 16))
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(True)
        self.pin_btn.setToolTip("窗口置顶开关")
        self.pin_btn.clicked.connect(self.main_window.toggle_pin)
        layout.addWidget(self.pin_btn)

        self.min_btn = QToolButton()
        self.min_btn.setObjectName("TitleBtn")
        self.min_btn.setIcon(QIcon(draw_titlebar_icon("minimize")))
        self.min_btn.setIconSize(QSize(16, 16))
        self.min_btn.setToolTip("最小化到系统托盘")
        self.min_btn.clicked.connect(self.main_window.hide_to_tray)
        layout.addWidget(self.min_btn)

        self.close_btn = QToolButton()
        self.close_btn.setObjectName("TitleBtn")
        self.close_btn.setIcon(QIcon(draw_titlebar_icon("close")))
        self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setToolTip("关闭（隐藏到托盘，不会退出）")
        self.close_btn.clicked.connect(self.main_window.hide_to_tray)
        layout.addWidget(self.close_btn)

        self._refresh_pin_icon()
        self.refresh_cloud_state()

    def _refresh_pin_icon(self):
        active = self.pin_btn.isChecked()
        self.pin_btn.setIcon(QIcon(draw_titlebar_icon("pin", active=active)))

    def refresh_cloud_state(self):
        email = self.main_window.settings.get("cloud_email", "").strip()
        nickname = self.main_window.settings.get("cloud_nickname", "").strip()
        if email:
            name = nickname if nickname else email.split("@")[0]
            self.cloud_btn.setToolTip(f"Cloudflare 云端已连接: {name} ({email})\n点击管理账号与同步")
        else:
            self.cloud_btn.setToolTip("Cloudflare 云端同步与账号 (点击登录/注册)")

    def update_draft_state(self, is_in_draft):
        hk = self.main_window.settings.get("draft_hotkey", "Shift+X")
        if is_in_draft:
            self.draft_btn.setIcon(QIcon(draw_titlebar_icon("draft", active=True)))
            self.draft_btn.setToolTip(f"退出草稿纸，返回卡片列表 (Esc / {hk})")
        else:
            self.draft_btn.setIcon(QIcon(draw_titlebar_icon("draft", active=False)))
            self.draft_btn.setToolTip(f"快速草稿纸 ({hk})")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.main_window.pos()
            if self.main_window._is_edge_hidden:
                self.main_window._slide_out_from_edge()
            self.main_window._cancel_edge_dock()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.main_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self.main_window._check_edge_dock()
        if not self.main_window._is_edge_hidden:
            pos = self.main_window.pos()
            self.main_window._normal_pos = pos
            self.main_window.settings["window_x"] = pos.x()
            self.main_window.settings["window_y"] = pos.y()
            save_settings(self.main_window.settings)


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------

def _center_window_on_screen(win):
    screen_obj = QGuiApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
    if screen_obj:
        sg = screen_obj.availableGeometry()
        x = sg.x() + (sg.width() - win.width()) // 2
        y = sg.y() + (sg.height() - win.height()) // 2
        win.move(x, y)


def _restore_or_center_window(win, settings, key_x, key_y):
    screen_obj = QGuiApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
    sg = screen_obj.availableGeometry() if screen_obj else QApplication.primaryScreen().availableGeometry()
    sx = settings.get(key_x) if isinstance(settings, dict) else None
    sy = settings.get(key_y) if isinstance(settings, dict) else None
    if (sx is None or sy is None) and isinstance(settings, dict) and key_x != "window_x":
        sx = settings.get("window_x")
        sy = settings.get("window_y")
    w, h = win.width(), win.height()
    win.setAttribute(Qt.WA_Moved, True)
    if sx is not None and sy is not None:
        try:
            tx = max(sg.x() - 16, min(int(sx), sg.x() + sg.width() - w + 16))
            ty = max(sg.y() - 16, min(int(sy), sg.y() + sg.height() - h + 16))
            win.move(tx, ty)
            return QPoint(tx, ty)
        except Exception:
            pass
    cx = sg.x() + (sg.width() - w) // 2
    cy = sg.y() + (sg.height() - h) // 2
    win.move(cx, cy)
    return QPoint(cx, cy)


def _save_window_pos(win, settings, key_x, key_y):
    if isinstance(settings, dict):
        pos = win.pos()
        settings[key_x] = pos.x()
        settings[key_y] = pos.y()
        save_settings(settings)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.prompts = load_prompts()
        self.settings = load_settings()
        self.collapsed_groups = set(self.settings.get("collapsed_groups", []))
        self._hotkey_ready = False

        # Qt.Tool：不进 Windows 任务栏，只用托盘
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(WINDOW_W, WINDOW_H)
        self.setWindowIcon(load_app_icon())
        self.setWindowOpacity(self.settings.get("opacity", 1.0))

        # 贴边自动隐藏属性与动画
        self._edge_dock_enabled = self.settings.get("edge_dock", True)
        self._docked_edge = None
        self._is_edge_hidden = False

        # 初始窗口位置：默认屏幕正中显示，若用户已拖放过则恢复上次拖放位置
        self._normal_pos = _restore_or_center_window(self, self.settings, "window_x", "window_y")

        self._edge_hover_timer = QTimer(self)
        self._edge_hover_timer.setInterval(80)
        self._edge_hover_timer.timeout.connect(self._on_edge_hover_check)
        # 启动时锁定 8 秒不自动隐藏，让用户清晰看到卡片已启动在桌面
        self._leave_countdown = -100

        self._edge_anim = QPropertyAnimation(self, b"pos")
        self._edge_anim.setDuration(220)
        self._edge_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.hotkey_manager = GlobalHotkeyManager()
        theme_colors = THEME_MAP.get(self.settings.get("theme", "默认"), THEME_MAP["默认"])
        self.draft_pad = DraftPadView(theme_colors[1], on_exit_callback=self.exit_draft_pad)
        self.in_draft_mode = False

        self._build_ui()
        self._build_tray()
        self.apply_theme(self.settings.get("theme", "默认"))
        self.render_cards()

        self.escape_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.escape_shortcut.setContext(Qt.WindowShortcut)
        self.escape_shortcut.activated.connect(self._on_escape_shortcut)

        # 云端自动同步定时器（每 5 分钟静默同步一次）
        self._cloud_sync_timer = QTimer(self)
        self._cloud_sync_timer.setInterval(5 * 60 * 1000)
        self._cloud_sync_timer.timeout.connect(self.sync_cloud_silently)
        self._cloud_sync_timer.start()
        QTimer.singleShot(2500, self.sync_cloud_silently)
        QTimer.singleShot(4500, self.check_update_silently)

        # 启动后若停留在边缘则自动吸附
        QTimer.singleShot(600, self._check_edge_dock)

        QApplication.instance().aboutToQuit.connect(self._on_about_to_quit)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self._edge_dock_enabled and self._docked_edge and self._is_edge_hidden:
            self._slide_out_from_edge()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self._edge_dock_enabled and self._docked_edge and not self._is_edge_hidden and not self.in_draft_mode:
            self._leave_countdown = 1

    def _get_current_screen_geometry(self):
        center = self.geometry().center()
        screen = QGuiApplication.screenAt(center)
        if not screen:
            screen = self.screen() or QApplication.primaryScreen()
        return screen.availableGeometry() if screen else QApplication.primaryScreen().availableGeometry()

    def _on_edge_hover_check(self):
        if not self._edge_dock_enabled or not self._docked_edge or self.in_draft_mode:
            return

        if getattr(self.title_bar, "_drag_pos", None) is not None:
            return
        if self._edge_anim.state() == QPropertyAnimation.Running:
            return
        if QApplication.activeModalWidget():
            return

        cursor = QCursor.pos()
        geom = self.geometry()
        screen = self._get_current_screen_geometry()

        # 给予边缘吸附微小余量，确保光标滑到屏幕物理边缘时 100% 灵敏触发
        trigger_rect = QRect(geom)
        if self._docked_edge == "left":
            trigger_rect.setLeft(screen.x())
            trigger_rect.setWidth(geom.width() + 6)
        elif self._docked_edge == "right":
            trigger_rect.setRight(screen.x() + screen.width())
            trigger_rect.setLeft(geom.left() - 6)
        elif self._docked_edge == "top":
            trigger_rect.setTop(screen.y())
            trigger_rect.setHeight(geom.height() + 6)

        is_hover = trigger_rect.contains(cursor)

        if self._is_edge_hidden:
            # 隐藏状态：极致纯净不留边。当鼠标贴近屏幕物理边缘（0~4px）时极速响应滑出唤醒
            TRIGGER_MARGIN = 4
            edge_hit = False
            if self._docked_edge == "left":
                edge_hit = (cursor.x() <= screen.x() + TRIGGER_MARGIN) and (geom.top() - 30 <= cursor.y() <= geom.bottom() + 30)
            elif self._docked_edge == "right":
                edge_hit = (cursor.x() >= screen.x() + screen.width() - TRIGGER_MARGIN) and (geom.top() - 30 <= cursor.y() <= geom.bottom() + 30)
            elif self._docked_edge == "top":
                edge_hit = (cursor.y() <= screen.y() + TRIGGER_MARGIN) and (geom.left() - 30 <= cursor.x() <= geom.right() + 30)

            if edge_hit:
                self._slide_out_from_edge()
        else:
            if is_hover:
                self._leave_countdown = 0
            else:
                self._leave_countdown += 1
                # 80ms * 4 = 320ms 离开缓冲期，平滑滑入隐藏
                if self._leave_countdown >= 4:
                    self._slide_into_edge()

    def _slide_into_edge(self):
        if not self._edge_dock_enabled or not self._docked_edge or self._is_edge_hidden or self.in_draft_mode:
            return
        if QApplication.activeModalWidget() or self.geometry().contains(QCursor.pos()):
            return

        screen = self._get_current_screen_geometry()
        cur = self.pos()
        w = self.width()
        h = self.height()

        target_x = cur.x()
        target_y = cur.y()

        # 完全贴边不留边（0px 实体露边，桌面极简无痕）
        if self._docked_edge == "left":
            target_x = screen.x() - w + 16
        elif self._docked_edge == "right":
            target_x = screen.x() + screen.width() - 16
        elif self._docked_edge == "top":
            target_y = screen.y() - h + 22

        self._is_edge_hidden = True
        self._edge_anim.stop()
        self._edge_anim.setDuration(220)
        self._edge_anim.setStartValue(cur)
        self._edge_anim.setEndValue(QPoint(target_x, target_y))
        self._edge_anim.start()

    def _slide_out_from_edge(self, lock_seconds=5.0):
        self._is_edge_hidden = False
        # 唤醒滑出时锁定指定秒数不自动缩回隐藏
        self._leave_countdown = -int(lock_seconds * 12.5)
        self._edge_anim.stop()
        self._edge_anim.setDuration(220)
        self._edge_anim.setStartValue(self.pos())

        # 确保 normal_pos 在当前屏幕可见范围内
        screen = self._get_current_screen_geometry()
        nx = max(screen.x() + 20, min(self._normal_pos.x(), screen.x() + screen.width() - self.width() - 20))
        ny = max(screen.y() + 20, min(self._normal_pos.y(), screen.y() + screen.height() - self.height() - 20))
        self._normal_pos = QPoint(nx, ny)

        self._edge_anim.setEndValue(self._normal_pos)
        self._edge_anim.start()

    def _check_edge_dock(self):
        if not self._edge_dock_enabled:
            self._cancel_edge_dock()
            return

        screen = self._get_current_screen_geometry()
        x = self.x()
        y = self.y()
        w = self.width()
        h = self.height()

        card_left = x + 16
        card_right = x + w - 16
        card_top = y + 16

        SNAP_THRESH = 45

        candidates = []
        if card_left <= screen.x() + SNAP_THRESH:
            candidates.append(("left", abs(card_left - screen.x())))
        if card_right >= screen.x() + screen.width() - SNAP_THRESH:
            candidates.append(("right", abs((screen.x() + screen.width()) - card_right)))
        if card_top <= screen.y() + SNAP_THRESH:
            candidates.append(("top", abs(card_top - screen.y())))

        if candidates:
            candidates.sort(key=lambda item: item[1])
            edge = candidates[0][0]
            self._docked_edge = edge

            if edge == "left":
                clamped_y = max(screen.y() - 16, min(y, screen.y() + screen.height() - h + 22))
                self.move(screen.x() - 16, clamped_y)
            elif edge == "right":
                clamped_y = max(screen.y() - 16, min(y, screen.y() + screen.height() - h + 22))
                self.move(screen.x() + screen.width() - w + 16, clamped_y)
            elif edge == "top":
                clamped_x = max(screen.x() - 16, min(x, screen.x() + screen.width() - w + 16))
                self.move(clamped_x, screen.y() - 16)

            self._normal_pos = self.pos()
            self._is_edge_hidden = False
            self._leave_countdown = 0

            if not self._edge_hover_timer.isActive():
                self._edge_hover_timer.start(80)
        else:
            self._cancel_edge_dock()
            self._normal_pos = self.pos()

    def _cancel_edge_dock(self):
        self._docked_edge = None
        self._is_edge_hidden = False
        if hasattr(self, "_edge_hover_timer"):
            self._edge_hover_timer.stop()
        self._edge_anim.stop()

    def _on_escape_shortcut(self):
        if self.in_draft_mode:
            if hasattr(self, "draft_pad") and self.draft_pad.find_bar.isVisible():
                self.draft_pad._hide_find_bar()
                return
            self.exit_draft_pad()

    def current_style(self):
        tb, ac = THEME_MAP.get(self.settings.get("theme", "默认"), THEME_MAP["默认"])
        return build_style(tb, ac)

    def apply_theme(self, name):
        self.settings["theme"] = name
        self.setStyleSheet(self.current_style())
        tb, ac = THEME_MAP.get(name, THEME_MAP["默认"])
        self.draft_pad.apply_theme(ac)

    def preview_theme(self, name):
        tb, ac = THEME_MAP.get(name, THEME_MAP["默认"])
        self.setStyleSheet(build_style(tb, ac))

    def _build_ui(self):
        wrapper = QWidget()
        wrapper.setObjectName("Wrapper")
        self.setCentralWidget(wrapper)

        wrapper_layout = QVBoxLayout(wrapper)
        margin = 16
        wrapper_layout.setContentsMargins(margin, margin, margin, margin + 6)

        root = QWidget()
        root.setObjectName("RootPanel")
        shadow = QGraphicsDropShadowEffect(root)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 90))
        root.setGraphicsEffect(shadow)
        wrapper_layout.addWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.title_bar = TitleBar(self)
        outer.addWidget(self.title_bar)

        body = QVBoxLayout()
        body.setContentsMargins(10, 6, 10, 2)
        body.setSpacing(4)

        self.list_widget = PromptListWidget()
        self.list_widget.setFrameShape(QFrame.NoFrame)
        self.list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setSpacing(8)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_list_context_menu)
        self.list_widget.card_dropped.connect(self._on_card_dropped)

        self.body_stack = QStackedWidget()
        self.body_stack.addWidget(self.list_widget)
        self.body_stack.addWidget(self.draft_pad)
        body.addWidget(self.body_stack, 1)

        outer.addLayout(body)

        footer = QLabel("WELLSHIJIAN")
        footer.setObjectName("Watermark")
        footer.setAlignment(Qt.AlignCenter)
        f = footer.font()
        f.setLetterSpacing(QFont.AbsoluteSpacing, 3)
        f.setPointSize(8)
        footer.setFont(f)
        outer.addWidget(footer)

    def _on_list_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item is None:
            menu = QMenu(self)
            add_action = menu.addAction("＋  添加新提示词")
            new_folder_action = menu.addAction("＋  新建文件夹")
            menu.addSeparator()
            update_action = menu.addAction(f"🔄 检查更新 (v{APP_VERSION})...")
            action = menu.exec(self.list_widget.viewport().mapToGlobal(pos))
            if action == add_action:
                self.add_prompt()
            elif action == new_folder_action:
                name = self._prompt_new_folder_name()
                if name:
                    self._ensure_folder(name)
                    self.render_cards()
            elif action == update_action:
                self.open_update_dialog()
            return

        widget = self.list_widget.itemWidget(item)
        if isinstance(widget, FolderHeader) and widget.is_folder:
            menu = QMenu(self)
            rename_action = menu.addAction("重命名文件夹")
            delete_action = menu.addAction("删除文件夹")
            action = menu.exec(self.list_widget.viewport().mapToGlobal(pos))
            if action == rename_action:
                self.rename_folder(widget.label)
            elif action == delete_action:
                self.delete_folder(widget.label)

    def _resolve_folder_name(self, text):
        text = (text or "").strip()
        if not text:
            return ""
        for f in self.get_all_folders():
            if f.strip().lower() == text.lower():
                return f
        return text

    def _prompt_new_folder_name(self, title="新建文件夹", initial=""):
        name, ok = QInputDialog.getText(self, title, "文件夹名称：", text=initial)
        if not ok:
            return None
        name = name.strip()
        if not name:
            return None
        if name in self.get_all_folders():
            QMessageBox.warning(self, "文件夹已存在", "已经有一个叫「{}」的文件夹了，换个名字吧。".format(name))
            return None
        return name

    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon(make_logo_pixmap(64)))
        self.tray.setToolTip(APP_NAME)

        menu = QMenu()
        show_action = QAction("显示 / 隐藏 PromptDock", self)
        show_action.triggered.connect(self.toggle_visibility)
        draft_action = QAction("📝 快速草稿纸...", self)
        draft_action.triggered.connect(self.open_draft_pad)
        media_action = QAction("🎬 视频无水印提取 (Shift+T)...", self)
        media_action.triggered.connect(self.open_media_extractor)
        schedule_action = QAction("📅 任务排期表 (Shift+A)...", self)
        schedule_action.triggered.connect(self.open_schedule_pad)
        capture_action = QAction("✂️ 划词快速收录...", self)
        capture_action.triggered.connect(self.trigger_quick_capture)
        cloud_action = QAction("☁️ 账号与云端同步...", self)
        cloud_action.triggered.connect(self.open_cloud_sync_dialog)
        self.update_action = QAction(f"🔄 检查更新 (v{APP_VERSION})...", self)
        self.update_action.triggered.connect(lambda: self.open_update_dialog())

        menu.addAction(show_action)
        menu.addAction(draft_action)
        menu.addAction(media_action)
        menu.addAction(schedule_action)
        menu.addAction(capture_action)
        menu.addSeparator()
        menu.addAction(cloud_action)
        menu.addAction(self.update_action)
        menu.addSeparator()
        export_action = QAction("导出提示词...", self)
        export_action.triggered.connect(self.export_prompts)
        import_action = QAction("导入提示词...", self)
        import_action.triggered.connect(self.import_prompts)
        open_data_action = QAction("打开数据文件夹", self)
        open_data_action.triggered.connect(self.open_data_folder)
        appearance_action = QAction("外观设置...", self)
        appearance_action.triggered.connect(self.open_appearance_settings)
        hotkey_action = QAction("设置快捷键...", self)
        hotkey_action.triggered.connect(self.open_hotkey_settings)
        self.startup_action = QAction("开机自动启动", self)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(is_startup_enabled())
        self.startup_action.toggled.connect(self.toggle_startup)
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        menu.addAction(export_action)
        menu.addAction(import_action)
        menu.addAction(open_data_action)
        menu.addSeparator()
        menu.addAction(appearance_action)
        menu.addAction(hotkey_action)
        menu.addAction(self.startup_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.toggle_visibility()

    # -- 文件夹 ---------------------------------------------------------------
    def get_all_folders(self):
        ordered = list(self.settings.get("folders", []))
        known = set(ordered)
        for p in self.prompts:
            if p.get("is_deleted", False):
                continue
            f = p.get("folder")
            if f and f not in known:
                ordered.append(f)
                known.add(f)
        return ordered

    def _ensure_folder(self, name):
        if not name:
            return
        folders = list(self.settings.get("folders", []))
        if name in folders:
            folders.remove(name)
        folders.insert(0, name)
        self.settings["folders"] = folders
        save_settings(self.settings)

    def delete_folder(self, name):
        ret = QMessageBox.question(
            self, "删除文件夹",
            "确定要删除文件夹「{}」吗？\n里面的提示词会移动到「未分类」，不会被删除。".format(name)
        )
        if ret != QMessageBox.Yes:
            return
        for p in self.prompts:
            if p.get("folder") == name:
                p["folder"] = ""
        self.settings["folders"] = [f for f in self.settings.get("folders", []) if f != name]
        self.collapsed_groups.discard("folder:{}".format(name))
        self.settings["collapsed_groups"] = list(self.collapsed_groups)
        save_settings(self.settings)
        save_prompts(self.prompts)
        self.render_cards()

    def rename_folder(self, old_name):
        new_name, ok = QInputDialog.getText(self, "重命名文件夹", "新名称：", text=old_name)
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name or new_name == old_name:
            return
        other_folders = [f for f in self.get_all_folders() if f != old_name]
        if new_name in other_folders:
            QMessageBox.warning(self, "文件夹已存在", "已经有一个叫「{}」的文件夹了，换个名字吧。".format(new_name))
            return
        for p in self.prompts:
            if p.get("folder") == old_name:
                p["folder"] = new_name
        folders = list(self.settings.get("folders", []))
        if old_name in folders:
            folders[folders.index(old_name)] = new_name
        else:
            folders.insert(0, new_name)
        self.settings["folders"] = folders
        save_settings(self.settings)
        save_prompts(self.prompts)
        self.render_cards()

    def _toggle_group(self, group_key):
        if group_key in self.collapsed_groups:
            self.collapsed_groups.discard(group_key)
        else:
            self.collapsed_groups.add(group_key)
        self.settings["collapsed_groups"] = list(self.collapsed_groups)
        save_settings(self.settings)
        self.render_cards()

    # -- 卡片渲染（分组 + 折叠 + 搜索） -----------------------------------------
    def render_cards(self):
        self.list_widget.clear()
        keyword = self.title_bar.search_box.text().strip()
        search_active = bool(keyword)

        known_folders = self.get_all_folders()

        def sorted_by_pin(items):
            pinned_items = [p for p in items if p.get("pinned")]
            other_items = [p for p in items if not p.get("pinned")]
            return pinned_items + other_items

        active_prompts = [p for p in self.prompts if not p.get("is_deleted", False)]
        groups = []
        for name in known_folders:
            folder_items = [p for p in active_prompts if p.get("folder") == name]
            groups.append(("folder:{}".format(name), name, sorted_by_pin(folder_items)))
        uncategorized = [p for p in active_prompts if not p.get("folder")]
        groups.append((GROUP_UNCATEGORIZED, None, sorted_by_pin(uncategorized)))

        for group_key, label, items in groups:
            if search_active:
                visible_items = [p for p in items if prompt_matches(p, keyword)]
                if not visible_items:
                    continue
            else:
                visible_items = items
                if not items and group_key == GROUP_UNCATEGORIZED:
                    continue

            if label is not None:
                collapsed = group_key in self.collapsed_groups
                is_folder = group_key.startswith("folder:")
                header_item = QListWidgetItem()
                header_item.setFlags(Qt.ItemIsEnabled)
                header_item.setData(Qt.UserRole, self._group_meta(group_key, label))
                header_widget = FolderHeader(group_key, label, len(items), collapsed, is_folder=is_folder)
                header_widget.toggled.connect(self._toggle_group)
                self.list_widget.addItem(header_item)
                header_item.setSizeHint(header_widget.sizeHint())
                self.list_widget.setItemWidget(header_item, header_widget)

                if collapsed and not search_active:
                    continue

            group_meta = self._group_meta(group_key, label)
            for p in visible_items:
                card = PromptCard(p, known_folders)
                card.edit_requested.connect(self.edit_prompt)
                card.delete_requested.connect(self.delete_prompt)
                card.color_changed.connect(self.change_prompt_color)
                card.pin_toggled.connect(self.toggle_pin_prompt)
                card.folder_changed.connect(self.change_prompt_folder)
                item = QListWidgetItem()
                item.setFlags(Qt.ItemIsEnabled)
                item.setData(Qt.UserRole, {"type": "card", "group": group_meta})
                item.setSizeHint(card.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, card)

        self.list_widget.viewport().update()
        self.list_widget.update()

    @staticmethod
    def _group_meta(group_key, label):
        if group_key == GROUP_UNCATEGORIZED:
            return {"type": "header", "kind": "uncategorized"}
        return {"type": "header", "kind": "folder", "name": label}

    def _group_kind_at_row(self, row):
        """根据拖放落点所在的行号，判断这个位置属于哪个分组（文件夹/未分类）。"""
        count = self.list_widget.count()
        if count == 0:
            return {"kind": "uncategorized"}
        if row < 0 or row >= count:
            row = count - 1  # 拖到列表末尾之后，就参照最后一行所属的分组
        item = self.list_widget.item(row)
        data = item.data(Qt.UserRole)
        if isinstance(data, dict):
            if data.get("type") == "header":
                return data
            if data.get("type") == "card":
                return data.get("group", {"kind": "uncategorized"})
        return {"kind": "uncategorized"}

    def _on_card_dropped(self, prompt_id, row):
        target = next((p for p in self.prompts if p["id"] == prompt_id), None)
        if not target:
            return
        group = self._group_kind_at_row(row)
        if group.get("kind") == "folder":
            target["folder"] = group.get("name", "")
        else:
            target["folder"] = ""
        target["updated_at"] = int(time.time() * 1000)
        # 挪到目标分组的末尾（按 self.prompts 里的相对顺序过滤显示，这样它会显示在该分组最后一条）
        self.prompts.remove(target)
        self.prompts.append(target)
        save_prompts(self.prompts)
        self.render_cards()
        self.sync_cloud_silently()

    # -- 增删改 ---------------------------------------------------------------
    def add_prompt(self):
        dlg = PromptEditDialog(self, style=self.current_style())
        if dlg.exec() == QDialog.Accepted:
            title, segments = dlg.get_values()
            self.prompts.append({
                "id": str(uuid.uuid4()), "title": title, "folder": "",
                "pinned": False, "color": CARD_COLOR_DEFAULT, "segments": segments,
                "updated_at": int(time.time() * 1000), "is_deleted": False,
            })
            save_prompts(self.prompts)
            self.render_cards()
            self.sync_cloud_silently()

    def edit_prompt(self, prompt_id):
        target = next((p for p in self.prompts if p["id"] == prompt_id), None)
        if not target:
            return
        dlg = PromptEditDialog(self, prompt=target, style=self.current_style())
        if dlg.exec() == QDialog.Accepted:
            title, segments = dlg.get_values()
            target["title"] = title
            target["segments"] = segments
            target["updated_at"] = int(time.time() * 1000)
            save_prompts(self.prompts)
            self.render_cards()
            self.sync_cloud_silently()

    def delete_prompt(self, prompt_id):
        ret = QMessageBox.question(self, "确认删除", "确定要删除这条提示词吗？")
        if ret == QMessageBox.Yes:
            target = next((p for p in self.prompts if p["id"] == prompt_id), None)
            if target:
                target["is_deleted"] = True
                target["updated_at"] = int(time.time() * 1000)
                save_prompts(self.prompts)
                self.render_cards()
                self.sync_cloud_silently()

    def change_prompt_color(self, prompt_id, hex_color):
        target = next((p for p in self.prompts if p["id"] == prompt_id), None)
        if not target:
            return
        target["color"] = hex_color
        target["updated_at"] = int(time.time() * 1000)
        save_prompts(self.prompts)
        self.render_cards()
        self.sync_cloud_silently()

    def change_prompt_folder(self, prompt_id, folder_name):
        if folder_name == "__new__":
            name = self._prompt_new_folder_name()
            if not name:
                return
            folder_name = name
            self._ensure_folder(folder_name)
        target = next((p for p in self.prompts if p["id"] == prompt_id), None)
        if not target:
            return
        target["folder"] = folder_name
        target["updated_at"] = int(time.time() * 1000)
        save_prompts(self.prompts)
        self.render_cards()
        self.sync_cloud_silently()

    def toggle_pin_prompt(self, prompt_id):
        target = next((p for p in self.prompts if p["id"] == prompt_id), None)
        if not target:
            return
        target["pinned"] = not target.get("pinned", False)
        target["updated_at"] = int(time.time() * 1000)
        if target["pinned"]:
            self.prompts.remove(target)
            self.prompts.insert(0, target)
        save_prompts(self.prompts)
        self.render_cards()
        self.sync_cloud_silently()

    # -- 导入导出 -------------------------------------------------------------
    def export_prompts(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出提示词", "我的提示词.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            active = [p for p in self.prompts if not p.get("is_deleted", False)]
            export_prompts_to_txt(active, path)
            self.tray.showMessage(APP_NAME, f"已导出 {len(active)} 条提示词", QSystemTrayIcon.Information, 2000)
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))

    def import_prompts(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入提示词", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if not path:
            return
        try:
            new_items = import_prompts_from_txt(path)
        except Exception as e:
            QMessageBox.warning(self, "导入失败", str(e))
            return
        if not new_items:
            QMessageBox.information(self, "没有导入任何内容", "没有在文件里找到符合格式的提示词，请检查文件格式。")
            return
        now = int(time.time() * 1000)
        for item in new_items:
            folder = self._resolve_folder_name(item.get("folder", ""))
            self._ensure_folder(folder)
            self.prompts.append({
                "id": str(uuid.uuid4()), "title": item["title"], "folder": folder,
                "pinned": False, "color": CARD_COLOR_DEFAULT,
                "segments": [{"id": str(uuid.uuid4()), "content": s["content"]} for s in item["segments"]],
                "updated_at": now, "is_deleted": False,
            })
        save_prompts(self.prompts)
        self.render_cards()
        self.sync_cloud_silently()
        QMessageBox.information(self, "导入完成", f"成功导入 {len(new_items)} 条提示词（追加在原有列表后面）。")

    def open_data_folder(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(get_data_dir()))

    def toggle_startup(self, checked):
        try:
            set_startup_enabled(checked)
            msg = "已开启开机自动启动" if checked else "已关闭开机自动启动"
            self.tray.showMessage(APP_NAME, msg, QSystemTrayIcon.Information, 2000)
        except Exception as e:
            QMessageBox.warning(self, "设置失败", str(e))
            self.startup_action.blockSignals(True)
            self.startup_action.setChecked(not checked)
            self.startup_action.blockSignals(False)

    # -- 设置 -----------------------------------------------------------------
    def open_cloud_sync_dialog(self):
        dlg = CloudSyncDialog(self, style=self.current_style())
        dlg.exec()

    def open_update_dialog(self, initial_info=None):
        dlg = UpdateDialog(self, initial_info=initial_info)
        _center_window_on_screen(dlg)
        dlg.exec()

    def check_update_silently(self):
        self._bg_update_worker = UpdateCheckWorker()
        self._bg_update_worker.finished.connect(self._on_bg_update_checked)
        self._bg_update_worker.start()

    def _on_bg_update_checked(self, info: dict):
        if info.get("has_update"):
            latest = info.get("latest_version", "")
            if hasattr(self, "update_action"):
                self.update_action.setText(f"🆕 发现新版本 v{latest} (点击更新)...")
            if hasattr(self, "tray"):
                self.tray.showMessage(
                    f"{APP_NAME} 发现新版本 v{latest}",
                    "右键托盘图标点击「发现新版本」，即可国内免梯子一键同步更新！",
                    QSystemTrayIcon.Information,
                    4000,
                )

    def trigger_quick_capture(self):
        if IS_WINDOWS:
            # 释放并模拟 Ctrl+C 抓取当前窗口选中的文字
            ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x43, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x43, 0, 2, 0)
            ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)
        QTimer.singleShot(120, self._show_quick_capture_dialog)

    def _show_quick_capture_dialog(self):
        text = QApplication.clipboard().text().strip()
        dlg = QuickCaptureDialog(initial_text=text, folders=self.get_all_folders(), style=self.current_style(), parent=self)
        _center_window_on_screen(dlg)
        if dlg.exec() == QDialog.Accepted:
            title, folder, content = dlg.result_title, dlg.result_folder, dlg.result_content
            item = _new_prompt(title, content, folder)
            self.prompts.append(item)
            save_prompts(self.prompts)
            self.render_cards()
            self.tray.showMessage(APP_NAME, f"✅ 已收录：「{title}」", QSystemTrayIcon.Information, 2000)
            self.sync_cloud_silently()

    def sync_cloud_silently(self):
        cloud_url = self.settings.get("cloud_url", "").strip()
        cloud_token = self.settings.get("cloud_token", "").strip()
        if not cloud_url or not cloud_token:
            return
        threading.Thread(target=self._run_cloud_sync, args=(False,), daemon=True).start()

    def _run_cloud_sync(self, show_dialog_feedback=False):
        cloud_url = self.settings.get("cloud_url", "").strip()
        cloud_token = self.settings.get("cloud_token", "").strip()
        if not cloud_url or not cloud_token:
            return
        last_sync = self.settings.get("last_sync_time", 0)

        # 1. 搜集需要推送到服务端的本地增量
        need_push = [p for p in self.prompts if p.get("updated_at", 0) >= last_sync]
        push_data = {
            "prompts": need_push,
            "settings": self.settings,
            "timestamp": int(time.time() * 1000)
        }
        ok, res, err = CloudClient.request(
            cloud_url, "/api/sync/push", method="POST",
            data=push_data,
            token=cloud_token
        )
        if not ok:
            if show_dialog_feedback:
                QTimer.singleShot(0, lambda: QMessageBox.warning(self, "同步失败", f"上传数据失败: {err}"))
            return

        # 2. 从服务端拉取云端增量
        ok, res, err = CloudClient.request(
            cloud_url, f"/api/sync/pull?since={last_sync}", method="GET",
            token=cloud_token
        )
        if not ok:
            if show_dialog_feedback:
                QTimer.singleShot(0, lambda: QMessageBox.warning(self, "同步失败", f"拉取云端数据失败: {err}"))
            return

        cloud_prompts = res.get("prompts", [])
        cloud_settings = res.get("settings")
        if cloud_settings and isinstance(cloud_settings, dict):
            if cloud_settings.get("cloud_avatar") and not self.settings.get("cloud_avatar"):
                self.settings["cloud_avatar"] = cloud_settings["cloud_avatar"]
            if cloud_settings.get("cloud_nickname") and not self.settings.get("cloud_nickname"):
                self.settings["cloud_nickname"] = cloud_settings["cloud_nickname"]
        server_time = res.get("server_time", int(time.time() * 1000))

        local_map = {p["id"]: p for p in self.prompts}
        changed = False
        for cp in cloud_prompts:
            pid = cp["id"]
            if pid in local_map:
                lp = local_map[pid]
                if cp.get("updated_at", 0) >= lp.get("updated_at", 0):
                    lp.update(cp)
                    changed = True
            else:
                self.prompts.append(cp)
                changed = True

        # 清理已同步完成的本地软删除墓碑记录
        self.prompts = [p for p in self.prompts if not (p.get("is_deleted") and p.get("updated_at", 0) <= server_time)]

        self.settings["last_sync_time"] = server_time
        save_settings(self.settings)
        save_prompts(self.prompts)

        if changed:
            QTimer.singleShot(0, self.render_cards)

        if show_dialog_feedback:
            QTimer.singleShot(0, lambda: QMessageBox.information(self, "同步成功", f"云端数据已同步完毕 (获取更新: {len(cloud_prompts)} 条)"))

    def open_appearance_settings(self):
        current_opacity = self.settings.get("opacity", 1.0)
        current_theme = self.settings.get("theme", "默认")
        dlg = AppearanceSettingsDialog(self, current_opacity, current_theme, style=self.current_style())
        if dlg.exec() == QDialog.Accepted:
            self.settings["opacity"] = dlg.opacity_value()
            self.settings["edge_dock"] = dlg.edge_dock_value()
            self._edge_dock_enabled = dlg.edge_dock_value()
            if not self._edge_dock_enabled:
                if self._is_edge_hidden:
                    self._slide_out_from_edge()
                self._cancel_edge_dock()
            else:
                self._check_edge_dock()
            self.apply_theme(dlg.theme_value())
            save_settings(self.settings)
        else:
            self.setWindowOpacity(current_opacity)
            self.apply_theme(current_theme)

    def open_hotkey_settings(self):
        dlg = HotkeySettingsDialog(
            self,
            current_main=self.settings.get("hotkey", "Shift+Z"),
            current_draft=self.settings.get("draft_hotkey", "Shift+X"),
            current_capture=self.settings.get("capture_hotkey", "Alt+C"),
            current_extractor=self.settings.get("extractor_hotkey", "Shift+T"),
            current_schedule=self.settings.get("schedule_hotkey", "Shift+A"),
            style=self.current_style(),
        )
        if dlg.exec() == QDialog.Accepted:
            combo_main = dlg.main_value()
            combo_draft = dlg.draft_value()
            combo_capture = dlg.capture_value()
            combo_extractor = dlg.extractor_value()
            combo_schedule = dlg.schedule_value()
            hwnd = int(self.winId())
            errors = []
            if combo_main:
                ok, msg = self.hotkey_manager.register(hwnd, HOTKEY_ID_MAIN, combo_main, self.toggle_visibility)
                if ok:
                    self.settings["hotkey"] = combo_main
                else:
                    errors.append("悬浮窗快捷键：{}".format(msg))
            if combo_draft:
                ok2, msg2 = self.hotkey_manager.register(hwnd, HOTKEY_ID_DRAFT, combo_draft, self.open_draft_pad)
                if ok2:
                    self.settings["draft_hotkey"] = combo_draft
                else:
                    errors.append("草稿纸快捷键：{}".format(msg2))
            if combo_capture:
                ok3, msg3 = self.hotkey_manager.register(hwnd, HOTKEY_ID_CAPTURE, combo_capture, self.trigger_quick_capture)
                if ok3:
                    self.settings["capture_hotkey"] = combo_capture
                else:
                    errors.append("划词收录快捷键：{}".format(msg3))
            if combo_extractor:
                ok4, msg4 = self.hotkey_manager.register(hwnd, HOTKEY_ID_EXTRACTOR, combo_extractor, self.toggle_media_extractor)
                if ok4:
                    self.settings["extractor_hotkey"] = combo_extractor
                else:
                    errors.append("无水印提取快捷键：{}".format(msg4))
            if combo_schedule:
                ok5, msg5 = self.hotkey_manager.register(hwnd, HOTKEY_ID_SCHEDULE, combo_schedule, self.toggle_schedule_pad)
                if ok5:
                    self.settings["schedule_hotkey"] = combo_schedule
                else:
                    errors.append("任务排期表快捷键：{}".format(msg5))
            save_settings(self.settings)
            self.title_bar.update_draft_state(self.in_draft_mode)
            if errors:
                QMessageBox.warning(self, "部分设置失败", "\n".join(errors))
            else:
                self.tray.showMessage(APP_NAME, "快捷键已更新", QSystemTrayIcon.Information, 2000)

    def open_draft_pad(self):
        if self.in_draft_mode and self.isVisible() and not self._is_edge_hidden:
            self.exit_draft_pad()
            return
        if self._is_edge_hidden:
            self._slide_out_from_edge()
        elif not self.isVisible():
            self._normal_pos = _restore_or_center_window(self, self.settings, "window_x", "window_y")
        self.draft_pad.load()
        self.body_stack.setCurrentWidget(self.draft_pad)
        self.in_draft_mode = True
        self.title_bar.update_draft_state(True)
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()
        self.draft_pad.text_edit.setFocus()

    def exit_draft_pad(self):
        self.draft_pad.flush_save()
        self.body_stack.setCurrentWidget(self.list_widget)
        self.in_draft_mode = False
        self.title_bar.update_draft_state(False)

    def toggle_media_extractor(self):
        if not hasattr(self, "_media_extractor") or self._media_extractor is None:
            self._media_extractor = MediaExtractorDialog(self)
        if self._media_extractor.isVisible() and self._media_extractor.isActiveWindow() and not self._media_extractor.isMinimized():
            self._media_extractor.close_cleanly()
        else:
            was_main_visible = self.isVisible() and not getattr(self, "_is_edge_hidden", False)
            main_pos = self.pos()
            main_w = self.width()
            if not self._media_extractor.isVisible():
                self._media_extractor.clear_all()
            if was_main_visible:
                screen_obj = QGuiApplication.screenAt(main_pos) or QApplication.primaryScreen()
                sg = screen_obj.availableGeometry()
                ew, eh = self._media_extractor.width(), self._media_extractor.height()
                tx = max(sg.x() + 8, min(main_pos.x() + (main_w - ew) // 2, sg.x() + sg.width() - ew - 8))
                ty = max(sg.y() + 8, min(main_pos.y() + 16, sg.y() + sg.height() - eh - 8))
                target_pt = QPoint(tx, ty)
                self.settings["extractor_x"] = tx
                self.settings["extractor_y"] = ty
                save_settings(self.settings)
            else:
                target_pt = _restore_or_center_window(self._media_extractor, self.settings, "extractor_x", "extractor_y")
            self._media_extractor.setAttribute(Qt.WA_Moved, True)
            self._media_extractor.move(target_pt)
            self._media_extractor.setWindowState(Qt.WindowNoState)
            self._media_extractor.show()
            self._media_extractor.move(target_pt)
            self._media_extractor.raise_()
            self._media_extractor.activateWindow()
            if IS_WINDOWS:
                try:
                    hwnd = int(self._media_extractor.winId())
                    ctypes.windll.user32.ShowWindow(hwnd, 9)
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                except Exception:
                    pass

    def open_media_extractor(self):
        self.toggle_media_extractor()

    def toggle_schedule_pad(self):
        if not hasattr(self, "_schedule_pad") or self._schedule_pad is None:
            self._schedule_pad = SchedulePadDialog(self)
        if self._schedule_pad.isVisible():
            _save_window_pos(self._schedule_pad, self.settings, "schedule_x", "schedule_y")
            self._schedule_pad.close()
        else:
            target_pt = _restore_or_center_window(self._schedule_pad, self.settings, "schedule_x", "schedule_y")
            self._schedule_pad.setAttribute(Qt.WA_Moved, True)
            self._schedule_pad.move(target_pt)
            self._schedule_pad.show()
            self._schedule_pad.move(target_pt)
            self._schedule_pad.raise_()
            self._schedule_pad.activateWindow()

    def open_schedule_pad(self):
        self.toggle_schedule_pad()

    def _register_hotkeys(self):
        hwnd = int(self.winId())
        combo_main = self.settings.get("hotkey", "Shift+Z")
        combo_draft = self.settings.get("draft_hotkey", "Shift+X")
        combo_capture = self.settings.get("capture_hotkey", "Alt+C")
        combo_extractor = self.settings.get("extractor_hotkey", "Shift+T")
        combo_schedule = self.settings.get("schedule_hotkey", "Shift+A")
        ok1, msg1 = self.hotkey_manager.register(hwnd, HOTKEY_ID_MAIN, combo_main, self.toggle_visibility)
        ok2, msg2 = self.hotkey_manager.register(hwnd, HOTKEY_ID_DRAFT, combo_draft, self.open_draft_pad)
        ok3, msg3 = self.hotkey_manager.register(hwnd, HOTKEY_ID_CAPTURE, combo_capture, self.trigger_quick_capture)
        ok4, msg4 = self.hotkey_manager.register(hwnd, HOTKEY_ID_EXTRACTOR, combo_extractor, self.toggle_media_extractor)
        ok5, msg5 = self.hotkey_manager.register(hwnd, HOTKEY_ID_SCHEDULE, combo_schedule, self.toggle_schedule_pad)
        if not IS_WINDOWS:
            return
        if ok1 and ok2 and ok3 and ok4 and ok5:
            self.tray.showMessage(
                APP_NAME,
                "后台运行中\n悬浮窗: {}\n草稿纸: {}\n去水印: {}\n排期表: {}".format(combo_main, combo_draft, combo_extractor, combo_schedule),
                QSystemTrayIcon.Information, 3500,
            )
        else:
            problems = []
            if not ok1:
                problems.append("悬浮窗快捷键 ({}) 注册失败：{}".format(combo_main, msg1))
            if not ok2:
                problems.append("草稿纸快捷键 ({}) 注册失败：{}".format(combo_draft, msg2))
            if not ok3:
                problems.append("划词收录快捷键 ({}) 注册失败：{}".format(combo_capture, msg3))
            if not ok4:
                problems.append("无水印提取快捷键 ({}) 注册失败：{}".format(combo_extractor, msg4))
            if not ok5:
                problems.append("排期表快捷键 ({}) 注册失败：{}".format(combo_schedule, msg5))
            self.tray.showMessage(APP_NAME, "\n".join(problems), QSystemTrayIcon.Warning, 4000)

    def _on_about_to_quit(self):
        try:
            self.hotkey_manager.unregister_all(int(self.winId()))
        except Exception:
            pass

    # -- 窗口行为 -------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        if not self._hotkey_ready:
            self._hotkey_ready = True
            self._register_hotkeys()

    def toggle_pin(self):
        pinned = self.title_bar.pin_btn.isChecked()
        self.title_bar._refresh_pin_icon()
        # 保持 Qt.Tool，避免重新出现在任务栏
        flags = Qt.Tool | Qt.FramelessWindowHint
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self._hide_from_taskbar()

    def _hide_from_taskbar(self):
        """Windows：强制不显示任务栏按钮，只留托盘。"""
        if not IS_WINDOWS:
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass

    def hide_to_tray(self):
        if not self._is_edge_hidden:
            _save_window_pos(self, self.settings, "window_x", "window_y")
        self.hide()

    def toggle_visibility(self):
        if self.isVisible() and not self._is_edge_hidden:
            _save_window_pos(self, self.settings, "window_x", "window_y")
            self.hide()
        else:
            if self._edge_dock_enabled and self._docked_edge:
                self.show()
                self._hide_from_taskbar()
                self._slide_out_from_edge(lock_seconds=6.0)
            else:
                self._normal_pos = _restore_or_center_window(self, self.settings, "window_x", "window_y")
                self._leave_countdown = -75
                self.show()
                self._hide_from_taskbar()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide_to_tray()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.in_draft_mode:
            if hasattr(self, "draft_pad") and self.draft_pad.find_bar.isVisible():
                self.draft_pad._hide_find_bar()
                return
            self.exit_draft_pad()
        else:
            super().keyPressEvent(event)


LOCAL_SERVER_NAME = "PromptDock_SingleInstance_App_2026"


def main():
    if IS_WINDOWS:
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('PromptDock.App.1')
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    try:
        app.setWindowIcon(load_app_icon())
    except Exception:
        pass

    # 1. 检查是否已有实例运行
    socket = QLocalSocket()
    socket.connectToServer(LOCAL_SERVER_NAME)
    if socket.waitForConnected(400):
        # 已经有实例在运行，授予其前台激活权限，向它发送唤醒指令并退出
        if IS_WINDOWS:
            try:
                ctypes.windll.user32.AllowSetForegroundWindow(0xFFFFFFFF)
            except Exception:
                pass
        socket.write(b"WAKEUP\n")
        if socket.waitForBytesWritten(800):
            socket.disconnectFromServer()
            sys.exit(0)
        # 如果旧实例无响应（假死或僵尸进程），则放弃并作为主实例启动
        socket.disconnectFromServer()

    # 2. 我们是主实例，清理旧服务并创建新服务监听唤醒
    QLocalServer.removeServer(LOCAL_SERVER_NAME)
    local_server = QLocalServer(app)
    local_server.listen(LOCAL_SERVER_NAME)

    window = MainWindow()

    def handle_wakeup():
        client = local_server.nextPendingConnection()
        if client:
            client.disconnectFromServer()

        # 只要用户再次运行程序，立刻取消最小化并居中展示在屏幕正前方，绝对不消失
        window.setWindowState(Qt.WindowNoState)
        screen = QApplication.primaryScreen().availableGeometry()
        cx = screen.x() + (screen.width() - window.width()) // 2
        cy = screen.y() + (screen.height() - window.height()) // 2
        window.move(cx, cy)
        window._normal_pos = QPoint(cx, cy)
        window._docked_edge = None
        window._is_edge_hidden = False
        window._leave_countdown = -100
        window.show()
        window.raise_()
        window.activateWindow()
        if IS_WINDOWS:
            try:
                hwnd = int(window.winId())
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
        if hasattr(window, "tray"):
            window.tray.showMessage("PromptDock", "💡 提示词卡片已在屏幕中央激活展示", QSystemTrayIcon.Information, 1500)

    local_server.newConnection.connect(handle_wakeup)

    window.show()
    window.raise_()
    window.activateWindow()
    if IS_WINDOWS:
        try:
            hwnd = int(window.winId())
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        apply_windows_taskbar_icon(window)
        window._hide_from_taskbar()
        QTimer.singleShot(200, lambda: (apply_windows_taskbar_icon(window), window._hide_from_taskbar()))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
