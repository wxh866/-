"""
截图工具 v4.0 - 全新 UI
- 深色/浅色双主题一键切换
- 4种截图模式：全屏、区域、窗口、滚动
- 标注工具：画笔、直线、矩形、圆形、箭头、文字、马赛克、高亮、橡皮、水印
- 工具栏悬浮/固定双模式
- 历史记录面板
- 一键保存/分享
快捷键: Ctrl+Shift+S  截图
"""
import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import subprocess
import os
import ctypes
import ctypes.wintypes
import json
import datetime
import math
from PIL import Image, ImageGrab, ImageDraw, ImageFont, ImageTk


# ==================== 主题系统（双主题） ====================
class _DarkTheme:
    BG0       = "#0f0f1a"
    BG1       = "#181828"
    BG2       = "#1e1e32"
    BG3       = "#282844"
    BG4       = "#333358"
    ACCENT    = "#4a8cff"
    ACCENT2   = "#5c9cff"
    ACCENT_BG = "#1a2848"
    TXT0      = "#f0f0f8"
    TXT1      = "#b0b0c8"
    TXT2      = "#707088"
    TXT3      = "#505068"
    BD        = "#2a2a44"
    BD2       = "#3a3a58"
    RED       = "#e05555"
    RED2      = "#f06060"
    GREEN     = "#4caf84"
    ORANGE    = "#e09050"
    CANVAS    = "#10101c"
    SELECTOR  = "#4a8cff"


class _LightTheme:
    BG0       = "#eef0f4"
    BG1       = "#f5f7fa"
    BG2       = "#ffffff"
    BG3       = "#f4f6f9"
    BG4       = "#eef1f6"
    ACCENT    = "#2e6fe0"
    ACCENT2   = "#4a8cff"
    ACCENT_BG = "#eaf1fe"
    TXT0      = "#1a2233"
    TXT1      = "#4a5568"
    TXT2      = "#8a94a6"
    TXT3      = "#b0b8c4"
    BD        = "#e4e7ec"
    BD2       = "#d3d8df"
    RED       = "#e05555"
    RED2      = "#f06060"
    GREEN     = "#2fa86c"
    ORANGE    = "#e09050"
    CANVAS    = "#eef0f4"
    SELECTOR  = "#2e6fe0"


class _ThemeMeta(type):
    """元类：让 T.BG0 这种类属性访问动态委托到当前主题"""
    def __getattr__(cls, name):
        return getattr(T._themes[T._theme], name)


class T(metaclass=_ThemeMeta):
    """统一主题色板（动态切换深色/浅色）

    用法不变：T.BG0 / T.ACCENT 等。切换主题调用 T.set_theme('light'/'dark')。
    所有已创建组件需自行实现刷新逻辑（_apply_theme）。
    """
    _theme = "dark"
    _themes = {"dark": _DarkTheme, "light": _LightTheme}

    COLORS = [
        "#FF3B30", "#FF6B35", "#FF9500", "#FFCC02",
        "#34C759", "#30B0C7", "#007AFF", "#5856D6",
        "#AF52DE", "#FF2D55", "#8E8E93", "#FFFFFF",
    ]
    FONT      = "Microsoft YaHei"
    FONT_MONO = "Consolas"

    @classmethod
    def set_theme(cls, name):
        if name in cls._themes:
            cls._theme = name

    @classmethod
    def get_theme(cls):
        return cls._theme

    @classmethod
    def toggle_theme(cls):
        cls._theme = "light" if cls._theme == "dark" else "dark"
        return cls._theme


# ==================== 全局配置 ====================
APP_NAME = "截图工具"
APP_VERSION = "4.0"
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
FONT_PATH_CN = "C:/Windows/Fonts/msyh.ttc"
HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

DEFAULT_SETTINGS = {
    "save_path": os.path.expanduser("~/Desktop"),
    "hotkey": "ctrl+shift+s",
    "default_watermark_text": "机密文件",
    "default_watermark_opacity": 25,
    "default_watermark_size": 52,
    "default_watermark_rotation": 28,
    "default_watermark_color": "#888888",
    "file_format": "PNG",
    "last_color": "#FF3B30",
    "last_line_width": 3,
    "theme": "dark",
}

try:
    import keyboard as kb
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


# ==================== 工具函数 ====================

def get_font(size=20):
    if os.path.exists(FONT_PATH_CN):
        try:
            return ImageFont.truetype(FONT_PATH_CN, size)
        except Exception:
            pass
    for path in ["arial.ttf", "C:/Windows/Fonts/arial.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            import traceback; traceback.print_exc(); pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        import traceback; traceback.print_exc(); pass


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def lighten(hex_color, factor=0.2):
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)


def darken(hex_color, factor=0.2):
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(int(r * (1 - factor)), int(g * (1 - factor)), int(b * (1 - factor)))


# ==================== 历史记录管理 ====================

def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            import traceback; traceback.print_exc()
    return []


def save_history(history):
    try:
        with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        import traceback; traceback.print_exc(); pass


def add_history(path, width, height):
    """添加一条历史记录，返回缩略图 PhotoImage（供 UI 显示）"""
    if not os.path.exists(path):
        return None
    history = load_history()
    # 去重
    history = [h for h in history if h.get("path") != path]
    history.insert(0, {
        "path": path,
        "name": os.path.basename(path),
        "time": datetime.datetime.now().strftime("%H:%M"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "size": f"{width}×{height}",
    })
    history = history[:20]  # 最多 20 条
    save_history(history)
    return make_thumbnail(path)


def make_thumbnail(path, size=(80, 50)):
    """生成缩略图 PhotoImage"""
    try:
        img = Image.open(path)
        img.thumbnail(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


# ==================== 自定义按钮 ====================

class StyledButton(tk.Canvas):
    """现代风格按钮"""

    def __init__(self, parent, text="", icon="", width=80, height=32,
                 bg=T.BG3, fg=T.TXT1, accent=False, danger=False,
                 command=None, font_size=9, **kw):
        parent_bg = parent.cget("bg") if hasattr(parent, "cget") else T.BG2
        super().__init__(parent, width=width, height=height,
                         bg=parent_bg, highlightthickness=0,
                         cursor="hand2", bd=0, **kw)

        self.cmd = command
        self.text = text
        self.icon = icon
        self.w = width
        self.h = height
        self._bg = bg
        self._fg = fg
        self._accent = accent
        self._danger = danger
        self._hover = False
        self._pressed = False
        self.font_size = font_size

        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.delete("all")
        r = 6
        w, h = self.w, self.h

        if self._pressed:
            bg = darken(self._bg, 0.15)
        elif self._hover:
            bg = lighten(self._bg, 0.12)
        else:
            bg = self._bg

        fg = self._fg
        if self._accent:
            bg = T.ACCENT if not self._hover else T.ACCENT2
            fg = "#ffffff"
        if self._danger and self._hover:
            bg = T.RED2
            fg = "#ffffff"

        self._round_rect(0, 0, w, h, r, bg, bg)
        display = f"{self.icon} {self.text}".strip()
        self.create_text(w // 2, h // 2, text=display, fill=fg,
                         font=(T.FONT, self.font_size), anchor="center")

    def _round_rect(self, x1, y1, x2, y2, r, fill, outline):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1,
            x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2,
            x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        self.create_polygon(points, fill=fill, outline=outline,
                            smooth=True, width=1)

    def _on_enter(self, e):
        self._hover = True; self._draw()

    def _on_leave(self, e):
        self._hover = False; self._pressed = False; self._draw()

    def _on_press(self, e):
        self._pressed = True; self._draw()

    def _on_release(self, e):
        self._pressed = False
        if self._hover and self.cmd:
            self.cmd()
        self._draw()


# ==================== 多显示器辅助 ====================

def get_virtual_screen_rect():
    """获取所有显示器组成的虚拟屏幕矩形 (Windows API)。
    返回 (left, top, width, height) —— left/top 在副屏在左侧/上方时可能为负。"""
    try:
        user32 = ctypes.windll.user32
        left   = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
        top    = user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
        width  = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
        height = user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
        return left, top, width, height
    except Exception:
        # 回退：使用 Tkinter 获取单屏尺寸
        root = tk.Tk()
        root.withdraw()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        return 0, 0, w, h


def capture_screen_with_dpi():
    """捕获全屏截图并处理 DPI 缩放。
    返回 (vs_left, vs_top, screenshot_pil, dpi_scale)。"""
    vs_left, vs_top, vs_w, vs_h = get_virtual_screen_rect()
    raw = ImageGrab.grab()
    if raw.width != vs_w or raw.height != vs_h:
        screenshot = raw.resize((vs_w, vs_h), Image.LANCZOS)
        dpi_scale = raw.width / vs_w
    else:
        screenshot = raw
        dpi_scale = 1.0
    return vs_left, vs_top, screenshot, dpi_scale


# ==================== 区域截图选择器 ====================

class RegionSelector:
    """全屏覆盖层，拖拽选择截图区域（支持多显示器）
    
    交互模式：
      - IDLE：无选区或鼠标未按下
      - NEW：在选区内/无选区时拖拽，创建新选区
      - MOVE：在选区内按住拖拽，移动整个选区
      - RESIZE：在选区边缘8px范围内拖拽，调整选区边界
    """

    EDGE_WIDTH = 8  # 边缘检测宽度（像素）

    def __init__(self, settings, callback):
        """
        settings: 配置字典
        callback: 选中区域后回调 callback(region_tuple) 其中 region_tuple = (x1,y1,x2,y2)
                  如果用户取消（ESC），callback(None)
        """
        self.settings = settings
        self.callback = callback
        self.region = None  # (x1, y1, x2, y2)  —— 屏幕绝对坐标

        # 捕获全屏截图（自动处理 DPI 缩放）
        self.vs_left, self.vs_top, self.vs_w, self.vs_h = get_virtual_screen_rect()
        _, _, self.screenshot, self.dpi_scale = capture_screen_with_dpi()

        self.sw = self.screenshot.width   # 逻辑像素宽度
        self.sh = self.screenshot.height  # 逻辑像素高度

        # 创建覆盖所有显示器的无边框窗口（逻辑像素）
        self.win = tk.Toplevel()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="black")
        self.win.config(cursor="crosshair")
        # 使用虚拟屏幕尺寸（逻辑像素），确保窗口完整覆盖屏幕
        self.win.geometry(f"{self.vs_w}x{self.vs_h}+{self.vs_left}+{self.vs_top}")
        # 强制获取键盘焦点（overrideredirect 窗口需要）
        self.win.after(50, self.win.focus_force)

        # Canvas 使用逻辑像素尺寸
        self.canvas = tk.Canvas(self.win, width=self.sw, height=self.sh,
                                bg="black", highlightthickness=0)
        self.canvas.pack()

        # 显示截图作为背景（已缩放到逻辑像素）
        self._photo = ImageTk.PhotoImage(self.screenshot)
        self._bg_id = self.canvas.create_image(0, 0, image=self._photo, anchor="nw")

        # 半透明遮罩（初始全屏）
        self._mask_ids = []
        self._draw_full_mask()

        # 交互状态
        self._mode = "IDLE"           # IDLE | NEW | MOVE | RESIZE
        self._resize_dir = ""         # N S E W NE NW SE SW
        self._drag_start_x = 0        # 拖拽起始鼠标 X
        self._drag_start_y = 0        # 拖拽起始鼠标 Y
        self._region_snapshot = None  # 拖拽前的选区快照 (x1,y1,x2,y2)
        self._dragging = False        # 是否正在拖拽
        self._prev_region = None      # 在 NEW 模式下保存的旧选区（用于 _on_up 判断）

        # 框选框 + 文字
        self._sel_rect = None
        self._info_text = None
        self._info_bgs = []  # 信息背景矩形 id 列表，用于清理

        # 双击检测（手动实现，避免 Tkinter Double-Button 事件时序冲突）
        self._last_click_time = 0         # 上次点击时间戳 (ms)
        self._last_click_pos = (0, 0)     # 上次点击位置
        self.DOUBLE_CLICK_INTERVAL = 400  # 双击间隔 (ms)
        self.DOUBLE_CLICK_RADIUS = 10     # 双击位置容差 (px)

        # 绑定事件
        self.canvas.bind("<ButtonPress-1>", self._on_down)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_up)
        self.canvas.bind("<Motion>", self._on_motion)
        self.win.bind("<Escape>", lambda e: self._cancel())
        self.win.bind("<Return>", lambda e: self._confirm())

        # 提示文字
        self._hint_id = self.canvas.create_text(
            self.sw // 2, 40,
            text="拖拽选择截图区域  |  选中后可拖拽移动/调整  |  双击全屏  |  Enter 确认  |  Esc 取消",
            fill="#ffffff", font=(T.FONT, 13, "bold"),
            anchor="center")
        # 提示背景
        bbox = self.canvas.bbox(self._hint_id)
        if bbox:
            self._hint_bg = self.canvas.create_rectangle(
                bbox[0] - 14, bbox[1] - 6, bbox[2] + 14, bbox[3] + 6,
                fill="#000000", outline="")
            self.canvas.tag_lower(self._hint_bg, self._hint_id)

    # ---------- 边缘检测 ----------

    def _hit_edge(self, mx, my):
        """检测鼠标是否在选区边缘上。返回方向字符串，若不在边缘返回 ''。"""
        if self.region is None:
            return ''
        x1, y1, x2, y2 = self.region
        ew = self.EDGE_WIDTH
        # 检查四个角优先（角有更高优先级）
        on_left   = x1 - ew <= mx <= x1 + ew
        on_right  = x2 - ew <= mx <= x2 + ew
        on_top    = y1 - ew <= my <= y1 + ew
        on_bottom = y2 - ew <= my <= y2 + ew
        in_x      = x1 + ew < mx < x2 - ew
        in_y      = y1 + ew < my < y2 - ew

        if on_left and on_top:
            return "NW"
        if on_right and on_top:
            return "NE"
        if on_left and on_bottom:
            return "SW"
        if on_right and on_bottom:
            return "SE"
        if on_left and in_y:
            return "W"
        if on_right and in_y:
            return "E"
        if on_top and in_x:
            return "N"
        if on_bottom and in_x:
            return "S"
        return ''

    def _inside_region(self, mx, my):
        """鼠标是否在选区内部（不含边缘）"""
        if self.region is None:
            return False
        x1, y1, x2, y2 = self.region
        ew = self.EDGE_WIDTH
        return x1 + ew < mx < x2 - ew and y1 + ew < my < y2 - ew

    # ---------- 光标样式 ----------

    def _set_cursor_for_pos(self, mx, my):
        """根据鼠标位置设置光标"""
        edge = self._hit_edge(mx, my)
        if edge:
            cursors = {
                "N":  "sb_v_double_arrow",
                "S":  "sb_v_double_arrow",
                "E":  "sb_h_double_arrow",
                "W":  "sb_h_double_arrow",
                "NE": "top_right_corner",
                "NW": "top_left_corner",
                "SE": "bottom_right_corner",
                "SW": "bottom_left_corner",
            }
            self.canvas.config(cursor=cursors.get(edge, "crosshair"))
        elif self._inside_region(mx, my):
            self.canvas.config(cursor="fleur")  # 移动光标
        else:
            self.canvas.config(cursor="crosshair")

    def _on_motion(self, event):
        """鼠标移动时更新光标样式"""
        self._set_cursor_for_pos(event.x, event.y)

    # ---------- 遮罩 ----------

    def _draw_full_mask(self):
        """初始全屏半透明遮罩"""
        self._mask_ids.append(
            self.canvas.create_rectangle(
                0, 0, self.sw, self.sh,
                fill="#000000", outline="", stipple="gray50"))

    def _reset_full_mask(self):
        """清除旧遮罩并重新绘制全屏遮罩"""
        for mid in self._mask_ids:
            self.canvas.delete(mid)
        self._mask_ids.clear()
        self._draw_full_mask()

    def _snap(self, x1, y1, x2, y2):
        """边缘吸附：距离屏幕边缘 ≤ SNAP_DIST 像素时自动吸附到边缘"""
        SNAP_DIST = 25
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        if x1 <= SNAP_DIST:
            x1 = 0
        if y1 <= SNAP_DIST:
            y1 = 0
        if x2 >= self.sw - SNAP_DIST:
            x2 = self.sw
        if y2 >= self.sh - SNAP_DIST:
            y2 = self.sh
        return x1, y1, x2, y2

    def _update_mask(self, x1, y1, x2, y2):
        """更新遮罩：选中区域透明，外围半透明（NEW 模式，含边缘吸附）"""
        x1, y1, x2, y2 = self._snap(x1, y1, x2, y2)
        self._rebuild_mask(x1, y1, x2, y2)
        self.region = (x1, y1, x2, y2)

    # ---------- 鼠标事件 ----------

    def _on_down(self, event):
        mx, my = event.x, event.y
        self._drag_start_x = mx
        self._drag_start_y = my

        # 保存旧选区（在 NEW 模式覆盖 region 之前）
        self._prev_region = self.region

        # 判断交互模式
        edge = self._hit_edge(mx, my)
        if edge and self.region is not None:
            # 在边缘 → 调整大小
            self._mode = "RESIZE"
            self._resize_dir = edge
            self._region_snapshot = self.region
        elif self._inside_region(mx, my) and self.region is not None:
            # 在选区内部 → 移动
            self._mode = "MOVE"
            self._region_snapshot = self.region
        else:
            # 新建选区（先在旧选区外部点击，之后可能是拖拽新选区或单击清除）
            self._mode = "NEW"
            self._region_snapshot = None

        self._dragging = True

        if self._mode == "NEW":
            # 注意：这里会覆盖 self.region，旧值已保存在 self._prev_region 中
            self._update_mask(mx, my, mx, my)
            self._draw_selection()

    def _on_drag(self, event):
        if not self._dragging:
            return
        mx, my = event.x, event.y
        dx = mx - self._drag_start_x
        dy = my - self._drag_start_y

        if self._mode == "NEW":
            self._update_mask(self._drag_start_x, self._drag_start_y, mx, my)
        elif self._mode == "MOVE":
            self._apply_move(dx, dy)
        elif self._mode == "RESIZE":
            self._apply_resize(mx, my)

        self._draw_selection()

    def _apply_move(self, dx, dy):
        """移动选区"""
        if self._region_snapshot is None:
            return
        x1, y1, x2, y2 = self._region_snapshot
        nw = x2 - x1
        nh = y2 - y1
        nx1 = x1 + dx
        ny1 = y1 + dy
        nx2 = nx1 + nw
        ny2 = ny1 + nh
        # 限制在屏幕范围内
        if nx1 < 0:
            nx1 = 0
            nx2 = nw
        if ny1 < 0:
            ny1 = 0
            ny2 = nh
        if nx2 > self.sw:
            nx2 = self.sw
            nx1 = self.sw - nw
        if ny2 > self.sh:
            ny2 = self.sh
            ny1 = self.sh - nh
        # 直接设置 region 并重建遮罩（跳过 _snap 避免排序和吸附干扰移动操作）
        self._rebuild_mask(int(nx1), int(ny1), int(nx2), int(ny2))

    def _rebuild_mask(self, x1, y1, x2, y2):
        """重建遮罩矩形（上/下/左/右四个方向）"""
        # 清理旧遮罩
        for mid in self._mask_ids:
            self.canvas.delete(mid)
        self._mask_ids.clear()

        # 边界 clamp
        x1 = max(0, min(x1, self.sw))
        y1 = max(0, min(y1, self.sh))
        x2 = max(0, min(x2, self.sw))
        y2 = max(0, min(y2, self.sh))

        fill, stipple = "#000000", "gray50"
        rects = [
            (0, 0, self.sw, y1),           # 上
            (0, y2, self.sw, self.sh),     # 下
            (0, y1, x1, y2),               # 左
            (x2, y1, self.sw, y2),         # 右
        ]
        for rx1, ry1, rx2, ry2 in rects:
            if rx2 > rx1 and ry2 > ry1:
                self._mask_ids.append(
                    self.canvas.create_rectangle(rx1, ry1, rx2, ry2,
                                                  fill=fill, outline="", stipple=stipple))

        # 确保遮罩层级在背景图之上但在选框/文字之下
        bg_id = getattr(self, '_bg_id', None)
        hint_id = getattr(self, '_hint_id', None)
        for mid in self._mask_ids:
            if bg_id:
                self.canvas.tag_raise(mid, bg_id)
            if hint_id:
                self.canvas.tag_lower(mid, hint_id)

        self.region = (x1, y1, x2, y2)

    def _apply_resize(self, mx, my):
        """根据边缘方向调整选区大小"""
        if self._region_snapshot is None:
            return
        x1, y1, x2, y2 = self._region_snapshot
        d = self._resize_dir
        if "W" in d:
            x1 = mx
        if "E" in d:
            x2 = mx
        if "N" in d:
            y1 = my
        if "S" in d:
            y2 = my
        # 保证最小尺寸
        MIN_SIZE = 10
        if x2 - x1 < MIN_SIZE:
            if "W" in d:
                x1 = x2 - MIN_SIZE
            else:
                x2 = x1 + MIN_SIZE
        if y2 - y1 < MIN_SIZE:
            if "N" in d:
                y1 = y2 - MIN_SIZE
            else:
                y2 = y1 + MIN_SIZE
        # 使用 _rebuild_mask 避免移动/缩放时 _snap 排序干扰坐标
        self._rebuild_mask(x1, y1, x2, y2)

    def _on_up(self, event):
        if not self._dragging:
            return
        self._dragging = False

        mx, my = event.x, event.y

        if self._mode == "NEW":
            dx = abs(mx - self._drag_start_x)
            dy = abs(my - self._drag_start_y)

            if dx < 5 and dy < 5:
                # 点击范围太小（< 5px）→ 可能是单击或双击
                now = event.time
                # 使用 _prev_region 判断之前是否有有效选区
                # （因为 _on_down 的 NEW 模式已经用零尺寸选区覆盖了 self.region）
                has_valid_region = (self._prev_region is not None and
                                    self._prev_region[2] - self._prev_region[0] >= 5 and
                                    self._prev_region[3] - self._prev_region[1] >= 5)

                if has_valid_region:
                    # 已有有效选区时点击空白 → 检查双击
                    if (now - self._last_click_time < self.DOUBLE_CLICK_INTERVAL and
                            abs(mx - self._last_click_pos[0]) < self.DOUBLE_CLICK_RADIUS and
                            abs(my - self._last_click_pos[1]) < self.DOUBLE_CLICK_RADIUS):
                        # 双击空白 → 全屏截图
                        self._update_mask(0, 0, self.sw, self.sh)
                        self._draw_selection()
                        self.win.after(50, self._confirm)
                        self._mode = "IDLE"
                        return
                    else:
                        # 单击空白 → 清除选区
                        self._last_click_time = now
                        self._last_click_pos = (mx, my)
                        self._reset_full_mask()
                        self.region = None
                        self._prev_region = None
                        self._draw_selection()
                        self._mode = "IDLE"
                        return
                else:
                    # 无有效选区时点击 → 检查双击全屏
                    if (now - self._last_click_time < self.DOUBLE_CLICK_INTERVAL and
                            abs(mx - self._last_click_pos[0]) < self.DOUBLE_CLICK_RADIUS and
                            abs(my - self._last_click_pos[1]) < self.DOUBLE_CLICK_RADIUS):
                        # 双击 → 全屏截图
                        self._update_mask(0, 0, self.sw, self.sh)
                        self._draw_selection()
                        self.win.after(50, self._confirm)
                        self._mode = "IDLE"
                        return
                    else:
                        self._last_click_time = now
                        self._last_click_pos = (mx, my)
                        # 清除 _on_down 创建的临时 0 尺寸选区
                        self._reset_full_mask()
                        self.region = None
                        self._prev_region = None
                        self._draw_selection()
                        self._mode = "IDLE"
                        return

            # 有效拖拽（dx >= 5 或 dy >= 5）→ 完成新选区
            self._last_click_time = 0
            self._update_mask(self._drag_start_x, self._drag_start_y, mx, my)
            self._draw_selection()

        # 所有模式结束时都刷新状态
        self._mode = "IDLE"
        self._prev_region = None

    # ---------- 绘制 ----------

    def _draw_selection(self):
        if self._sel_rect:
            self.canvas.delete(self._sel_rect)
        if self._info_text:
            self.canvas.delete(self._info_text)
        # 清理旧的信息背景矩形
        for bg_id in self._info_bgs:
            self.canvas.delete(bg_id)
        self._info_bgs.clear()

        if self.region is None:
            return

        x1, y1, x2, y2 = self.region
        w = x2 - x1
        h = y2 - y1

        # 选框（确保在遮罩之上）
        self._sel_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2, outline=T.SELECTOR, width=2, dash=(6, 3))

        # 尺寸信息
        info = f"{w} × {h} px"
        # 放在选框右上角外侧或内侧
        tx = x2 + 6
        ty = y1 - 6
        if tx + 120 > self.sw:
            tx = x2 - 6
        if ty < 20:
            ty = y1 + 18

        self._info_text = self.canvas.create_text(
            tx, ty, text=info, fill="#ffffff",
            font=(T.FONT_MONO, 10), anchor="ne")
        # 信息背景
        bbox = self.canvas.bbox(self._info_text)
        if bbox:
            bg_id = self.canvas.create_rectangle(
                bbox[0] - 6, bbox[1] - 2, bbox[2] + 6, bbox[3] + 2,
                fill=T.BG0, outline="")
            self.canvas.tag_lower(bg_id, self._info_text)
            self._info_bgs.append(bg_id)

        # 确保选框和文字在所有遮罩矩形之上
        for mid in self._mask_ids:
            self.canvas.tag_raise(self._sel_rect, mid)
        for bg_id in self._info_bgs:
            for mid in self._mask_ids:
                self.canvas.tag_raise(bg_id, mid)
        for mid in self._mask_ids:
            self.canvas.tag_raise(self._info_text, mid)

    def _confirm(self):
        if self.region is None:
            return
        x1, y1, x2, y2 = self.region
        w = x2 - x1
        h = y2 - y1
        if w < 5 or h < 5:
            self._cancel()
            return
        self.win.destroy()
        if self.callback:
            # Canvas 坐标是逻辑像素，需要转换回物理像素坐标给 ImageGrab
            ds = self.dpi_scale
            self.callback((
                int(x1 * ds), int(y1 * ds),
                int(x2 * ds), int(y2 * ds)
            ))

    def _cancel(self):
        self._photo = None
        self.region = None
        self.win.destroy()
        if self.callback:
            self.callback(None)


# ==================== 截图编辑器 ====================


class ScreenshotEditor:
    """截图编辑器"""

    def __init__(self, pil_image, settings, on_save_callback=None, on_theme_callback=None):
        self.settings = settings
        self.original_image = pil_image.copy()
        self.display_image = pil_image.copy()
        self.on_theme_callback = on_theme_callback
        self.result_image = None

        # 窗口尺寸计算
        self.win.config(cursor="crosshair")
        self.win.geometry(f"{self.vs_w}x{self.vs_h}+{self.vs_left}+{self.vs_top}")
        self.win.after(50, self.win.focus_force)

        self.canvas = tk.Canvas(self.win, width=self.sw, height=self.sh,
                                bg="black", highlightthickness=0)
        self.canvas.pack()
        self._photo = ImageTk.PhotoImage(self.screenshot)
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")

        # 全屏半透明遮罩
        self._mask_id = self.canvas.create_rectangle(
            0, 0, self.sw, self.sh, fill="#000000", outline="", stipple="gray50")

        # 提示文字
        hint = self.canvas.create_text(
            self.sw // 2, 40,
            text="移动鼠标选择窗口  |  点击捕获  |  Esc 取消",
            fill="#ffffff", font=(T.FONT, 13, "bold"), anchor="center")
        bbox = self.canvas.bbox(hint)
        if bbox:
            self._hint_bg = self.canvas.create_rectangle(
                bbox[0] - 14, bbox[1] - 6, bbox[2] + 14, bbox[3] + 6,
                fill="#000000", outline="")
            self.canvas.tag_lower(self._hint_bg, hint)

        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Button-1>", self._on_click)
        self.win.bind("<Escape>", lambda e: self._cancel())

        self._user32 = ctypes.windll.user32

    def _get_window_at(self, x, y):
        """获取鼠标位置所在的窗口矩形（屏幕逻辑坐标）"""
        try:
            # 将 Tkinter 逻辑坐标转换为物理坐标供 win32 使用
            px = int(x * self.dpi_scale)
            py = int(y * self.dpi_scale)
            hwnd = self._user32.WindowFromPoint(
                ctypes.wintypes.POINT(px, py))
            if not hwnd:
                return None
            # 获取顶层窗口
            root_hwnd = self._user32.GetAncestor(hwnd, 2)  # GA_ROOT = 2
            if root_hwnd:
                hwnd = root_hwnd
            rect = ctypes.wintypes.RECT()
            if self._user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                # 物理坐标转回逻辑坐标
                lx1 = int((rect.left - self.vs_left * self.dpi_scale) / self.dpi_scale) if self.vs_left < 0 else int(rect.left / self.dpi_scale)
                ly1 = int(rect.top / self.dpi_scale)
                lx2 = int(rect.right / self.dpi_scale)
                ly2 = int(rect.bottom / self.dpi_scale)
                # clamp 到屏幕范围
                lx1 = max(0, min(lx1, self.sw))
                ly1 = max(0, min(ly1, self.sh))
                lx2 = max(0, min(lx2, self.sw))
                ly2 = max(0, min(ly2, self.sh))
                if lx2 - lx1 > 10 and ly2 - ly1 > 10:
                    return (lx1, ly1, lx2, ly2)
        except Exception:
            pass
        return None

    def _on_motion(self, event):
        rect = self._get_window_at(event.x, event.y)
        # 清理上次绘制的高亮、标签和背景矩形
        for attr in ('_highlight_id', '_info_id', '_info_bg_id'):
            to_del = getattr(self, attr, None)
            if to_del:
                self.canvas.delete(to_del)
                setattr(self, attr, None)
        if rect:
            x1, y1, x2, y2 = rect
            self._highlight_id = self.canvas.create_rectangle(
                x1, y1, x2, y2, outline=T.SELECTOR, width=3)
            # 尺寸标签
            w, h = x2 - x1, y2 - y1
            info = f"{w}  {h}"
            self._info_id = self.canvas.create_text(
                x2 - 6, y1 + 18, text=info, fill=T.TXT0,
                font=(T.FONT_MONO, 10), anchor="ne")
            self._info_bg_id = self.canvas.create_rectangle(
                self.canvas.bbox(self._info_id),
                fill=T.BG0, outline="")
            self.canvas.tag_lower(self._info_bg_id, self._info_id)
            self.region = rect

    def _on_click(self, event):
        if self.region:
            self._confirm()

    def _confirm(self):
        if self.region is None:
            return
        x1, y1, x2, y2 = self.region
        if (x2 - x1) < 5 or (y2 - y1) < 5:
            self._cancel()
            return
        self.win.destroy()
        if self.callback:
            ds = self.dpi_scale
            self.callback((
                int(x1 * ds), int(y1 * ds),
                int(x2 * ds), int(y2 * ds)
            ))

    def _cancel(self):
        self._photo = None
        self.region = None
        self.win.destroy()
        if self.callback:
            self.callback(None)


# ==================== 截图编辑器 ====================

class ScreenshotEditor:
    """截图编辑器"""

    def __init__(self, pil_image, settings, on_save_callback=None, on_theme_callback=None):
        self.settings = settings
        self.original_image = pil_image.copy()
        self.display_image = pil_image.copy()
        self.on_save_callback = on_save_callback
        self.on_theme_callback = on_theme_callback
        self.result_image = None

        # 窗口尺寸计算
        self.window = tk.Toplevel()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()

        self.toolbar_w = 80
        self.top_h = 48
        self.bottom_h = 28

        # 编辑器窗口最大占屏幕 85%，给桌面留空间
        max_cw = int(sw * 0.85) - self.toolbar_w - 40
        max_ch = int(sh * 0.85) - self.top_h - self.bottom_h - 60

        # 最小画布尺寸
        MIN_CANVAS_W = 520
        MIN_CANVAS_H = 280

        self.scale = min(max_cw / pil_image.width, max_ch / pil_image.height, 1.0)
        self.canvas_w = int(pil_image.width * self.scale)
        self.canvas_h = int(pil_image.height * self.scale)

        if self.canvas_w < MIN_CANVAS_W or self.canvas_h < MIN_CANVAS_H:
            scale_up = min(MIN_CANVAS_W / pil_image.width, MIN_CANVAS_H / pil_image.height)
            if pil_image.width * scale_up <= max_cw and pil_image.height * scale_up <= max_ch:
                self.scale = scale_up
            else:
                self.scale = min(max_cw / pil_image.width, max_ch / pil_image.height)
            self.canvas_w = int(pil_image.width * self.scale)
            self.canvas_h = int(pil_image.height * self.scale)

        self.win_w = self.canvas_w + self.toolbar_w + 6
        self.win_h = self.canvas_h + self.top_h + self.bottom_h + 6

        # 绘图状态
        self.tool = "pen"
        self.color = settings.get("last_color", "#FF3B30")
        self.line_width = settings.get("last_line_width", 3)
        self.drawing = False
        self.start_x = self.start_y = None
        self.current_overlay = None

        # 图层（必须在 _make_snapshot 之前初始化）
        self.text_layer = Image.new("RGBA", pil_image.size, (0, 0, 0, 0))
        self.watermark_layer = Image.new("RGBA", pil_image.size, (0, 0, 0, 0))

        # 历史（保存完整的合成图层）
        self.history = [self._make_snapshot()]
        self.history_pos = 0
        self.max_history = 30

        # === 主题追踪：记录所有需要随主题切换的 widget 引用 ===
        self._themed_widgets = []   # (widget, 'bg'|'fg', role_hint)
        self._themed_canvases = []  # 需要重绘的 Canvas 组件 (redraw_method_name, widget)

        # 构建窗口
        self.window.title(f"{APP_NAME} - 编辑器")
        self.window.configure(bg=T.BG1)
        self.window.minsize(360, 280)
        self.window.protocol("WM_DELETE_WINDOW", self.discard)

        x = max(0, (sw - self.win_w) // 2)
        y = max(0, (sh - self.win_h) // 2)
        self.window.geometry(f"{self.win_w}x{self.win_h}+{x}+{y}")

        self._build_ui()
        self._apply_theme_to_tracked()  # 初始注册所有 widget
        self.update_display()

        # 快捷键
        self.window.bind("<Control-z>", lambda e: self.undo())
        self.window.bind("<Control-y>", lambda e: self.redo())
        self.window.bind("<Control-s>", lambda e: self.save_image())
        self.window.bind("<Control-c>", lambda e: self.copy_to_clipboard())
        self.window.bind("<Escape>", lambda e: self.discard())
        self.window.bind("<Delete>", lambda e: self.clear_all())
        self.window.bind("<Control-0>", lambda e: self._zoom_fit())

    def _make_snapshot(self):
        """创建完整状态快照用于撤销"""
        return (
            self.display_image.copy(),
            self.text_layer.copy(),
            self.watermark_layer.copy(),
        )

    def _restore_snapshot(self, snapshot):
        """从快照恢复状态"""
        self.display_image, self.text_layer, self.watermark_layer = snapshot
        self.display_image = self.display_image.copy()
        self.text_layer = self.text_layer.copy()
        self.watermark_layer = self.watermark_layer.copy()

    # ========== 主题追踪系统 ==========

    def _track(self, widget, attr='bg', role=''):
        """注册一个需要跟随主题切换的 widget 属性"""
        self._themed_widgets.append((widget, attr, role))

    def _track_canvas(self, canvas, method_name):
        """注册一个主题切换时需调用重绘方法的 Canvas"""
        self._themed_canvases.append((canvas, method_name))

    def _apply_theme_to_tracked(self):
        """根据当前 T.* 值更新所有已追踪的 widget — 核心主题刷新方法"""
        # 1) 更新普通 widget 的 bg/fg
        for widget, attr, role in self._themed_widgets:
            try:
                if not widget.winfo_exists():
                    continue
                val = self._resolve_theme_color(attr, role)
                if val is not None:
                    try:
                        widget.configure(**{attr: val})
                    except Exception:
                        pass
            except Exception:
                continue

        # 2) 重绘 Canvas 组件（颜色按钮、粗细预览、自定义颜色、+/-按钮等）
        for canvas, method_name in self._themed_canvases:
            try:
                if hasattr(canvas, 'winfo_exists') and not canvas.winfo_exists():
                    continue
                method = getattr(self, method_name, None)
                if callable(method):
                    method()
            except Exception:
                continue

        # 3) 重绘所有 StyledButton（必须逐个调用 _draw()）
        self._redraw_all_styled_buttons()

        # 4) 重绘颜色选择器圆点（边框色 T.BD 随主题变化）
        self._update_color_indicators()

        # 5) 刷新工具按钮高亮状态（当前选中工具需用 accent 色）
        if hasattr(self, 'tool_btns') and self.tool_btns:
            current = self.tool
            for tid, btn in self.tool_btns.items():
                if btn.winfo_exists():
                    if tid == current:
                        btn.configure(bg=T.ACCENT_BG, fg=T.ACCENT,
                                      activebackground=T.ACCENT_BG)
                    else:
                        btn.configure(bg=T.BG2, fg=T.TXT1,
                                      activebackground=T.BG3)

        # 6) 刷新画布背景 + 状态栏 + 坐标标签
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.configure(bg=T.CANVAS)
        if hasattr(self, '_status_lbl') and self._status_lbl.winfo_exists():
            self._status_lbl.configure(bg=T.BG2, fg=T.TXT2)
        if hasattr(self, '_coord_lbl') and self._coord_lbl.winfo_exists():
            self._coord_lbl.configure(bg=T.BG2, fg=T.TXT3)

        # 7) 刷新窗口自身背景
        try:
            self.window.configure(bg=T.BG1)
        except Exception:
            pass

        self.update_status()
        self.update_display()
        try:
            self.window.update_idletasks()
        except Exception:
            pass

    @staticmethod
    def _resolve_theme_color(attr, role):
        """根据角色返回当前主题对应的颜色值"""
        bg_roles = {
            'window': T.BG1, 'topbar': T.BG2, 'sidebar': T.BG2,
            'panel': T.BG2, 'canvas_shell': T.CANVAS,
            'bottombar': T.BG2, 'card': T.BG3, 'elev': T.BG3,
            'hover': T.BG4, 'input': T.BG3, 'accent_bg': T.ACCENT_BG,
            'dialog': T.BG2,
        }
        fg_roles = {
            'title': T.TXT0, 'text': T.TXT1, 'text2': T.TXT2,
            'text3': T.TXT3, 'accent': T.ACCENT, 'status': T.TXT2,
            'coord': T.TXT3,
        }
        if attr == 'bg':
            return bg_roles.get(role, T.BG2)
        elif attr == 'fg':
            return fg_roles.get(role, T.TXT1)
        return None

    # ========== UI 构建 ==========

    def _build_ui(self):
        self._themed_widgets.clear()
        self._themed_canvases.clear()

        self._build_topbar()
        self._build_sidebar()
        self._build_canvas()
        self._build_bottombar()

    def _build_topbar(self):
        bar = tk.Frame(self.window, bg=T.BG2, height=self.top_h)
        bar.pack(side=tk.TOP, fill=tk.X)
        bar.pack_propagate(False)
        self._track(bar, 'bg', 'topbar')

        inner = tk.Frame(bar, bg=T.BG2)
        inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=3)
        self._track(inner, 'bg', 'topbar')

        left = tk.Frame(inner, bg=T.BG2)
        left.pack(side=tk.LEFT)
        self._track(left, 'bg', 'topbar')

        # ---- 左侧：撤销/重做 ----
        self.btn_undo = StyledButton(left, icon="↩", text="撤销", width=58, height=28,
                                      command=self.undo, font_size=8)
        self.btn_undo.pack(side=tk.LEFT, padx=(0, 1))
        self.btn_redo = StyledButton(left, icon="↪", text="重做", width=58, height=28,
                                      command=self.redo, font_size=8)
        self.btn_redo.pack(side=tk.LEFT, padx=(1, 2))

        sep1 = tk.Frame(left, bg=T.BD, height=1)
        sep1.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=3)
        self._track(sep1, 'bg', 'card')

        # ---- 颜色选择器 ----
        self._color_btns = []
        color_frame = tk.Frame(left, bg=T.BG2)
        color_frame.pack(side=tk.LEFT)
        self._track(color_frame, 'bg', 'topbar')
        for c in T.COLORS[:10]:
            cb = tk.Canvas(color_frame, width=18, height=18, bg=T.BG2,
                           highlightthickness=0, cursor="hand2", bd=0)
            cb.pack(side=tk.LEFT, padx=1)
            outline = "#ffffff" if c == self.color else T.BD
            ow = 2 if c == self.color else 1
            cb.create_oval(2, 2, 16, 16, fill=c, outline=outline, width=ow)
            cb.bind("<Button-1>", lambda e, clr=c: self._set_color(clr))
            cb.bind("<Enter>", lambda e, c=cb: c.configure(bg=T.BG3))
            cb.bind("<Leave>", lambda e, c=cb: c.configure(bg=T.BG2))
            self._color_btns.append((cb, c))

        # 自定义颜色
        sep2 = tk.Frame(left, bg=T.BD, height=1)
        sep2.pack(side=tk.LEFT, fill=tk.Y, padx=3, pady=3)
        self._track(sep2, 'bg', 'card')
        self._custom_color_btn = tk.Canvas(left, width=24, height=24, bg=T.BG2,
                                            highlightthickness=0, cursor="hand2", bd=0)
        self._custom_color_btn.pack(side=tk.LEFT, padx=1)
        self._draw_custom_color_btn()
        self._custom_color_btn.bind("<Button-1>", lambda e: self.pick_color())
        self._custom_color_btn.bind("<Enter>",
                                    lambda e: self._custom_color_btn.configure(bg=T.BG3))
        self._custom_color_btn.bind("<Leave>",
                                    lambda e: self._custom_color_btn.configure(bg=T.BG2))

        # ---- 中间：线宽 ----
        mid = tk.Frame(inner, bg=T.BG2)
        mid.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=12)
        self._track(mid, 'bg', 'topbar')

        lbl_thickness = tk.Label(mid, text="粗细", bg=T.BG2, fg=T.TXT2,
                                 font=(T.FONT, 8))
        lbl_thickness.pack(anchor="center")
        self._track(lbl_thickness, 'fg', 'text2')

        width_shell = tk.Frame(mid, bg=T.BG2)
        width_shell.pack(anchor="center")

        self._btn_minus = tk.Canvas(width_shell, width=18, height=20, bg=T.BG3,
                                     highlightthickness=0, cursor="hand2")
        self._btn_minus.pack(side=tk.LEFT)
        self._btn_minus.create_text(9, 10, text="−", fill=T.TXT1, font=(T.FONT, 11, "bold"))
        self._btn_minus.bind("<Button-1>", lambda e: self._adjust_width(-1))
        self._btn_minus.bind("<Enter>", lambda e: self._btn_minus.configure(bg=T.BG4))
        self._btn_minus.bind("<Leave>", lambda e: self._btn_minus.configure(bg=T.BG3))

        self._width_preview = tk.Canvas(width_shell, width=44, height=20,
                                         bg=T.BG3, highlightthickness=0)
        self._width_preview.pack(side=tk.LEFT, padx=1)
        self._draw_width_preview()

        self._btn_plus = tk.Canvas(width_shell, width=18, height=20, bg=T.BG3,
                                   highlightthickness=0, cursor="hand2")
        self._btn_plus.pack(side=tk.LEFT, padx=(0, 1))
        self._btn_plus.create_text(9, 10, text="+", fill=T.TXT1, font=(T.FONT, 11, "bold"))
        self._btn_plus.bind("<Button-1>", lambda e: self._adjust_width(1))
        self._btn_plus.bind("<Enter>", lambda e: self._btn_plus.configure(bg=T.BG4))
        self._btn_plus.bind("<Leave>", lambda e: self._btn_plus.configure(bg=T.BG3))

        self._width_label = tk.Label(width_shell, text=str(self.line_width),
                                     bg=T.BG2, fg=T.TXT1, font=(T.FONT_MONO, 9), width=2)
        self._width_label.pack(side=tk.LEFT, padx=3)
        self._track(self._width_label, 'fg', 'text')
        lbl_px = tk.Label(width_shell, text="px", bg=T.BG2, fg=T.TXT2,
                          font=(T.FONT, 7))
        lbl_px.pack(side=tk.LEFT)

        # ---- 右侧：操作按钮 ----
        right = tk.Frame(inner, bg=T.BG2)
        right.pack(side=tk.RIGHT)
        self._track(right, 'bg', 'topbar')

        self.btn_save = StyledButton(right, icon="💾", text="保存", width=58, height=28,
                                      command=self.save_image, accent=True, font_size=8)
        self.btn_save.pack(side=tk.LEFT, padx=1)
        self.btn_copy = StyledButton(right, icon="📋", text="复制", width=58, height=28,
                                      command=self.copy_to_clipboard, font_size=8)
        self.btn_copy.pack(side=tk.LEFT, padx=1)

        sep3 = tk.Frame(right, bg=T.BD, height=1)
        sep3.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=3)
        self._track(sep3, 'bg', 'card')

        # 主题切换按钮
        self.btn_theme = StyledButton(right, icon="◐", text="", width=30, height=28,
                                      command=self.toggle_theme, font_size=8)
        self.btn_theme.pack(side=tk.LEFT, padx=1)

        sep4 = tk.Frame(right, bg=T.BD, height=1)
        sep4.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=3)
        self._track(sep4, 'bg', 'card')

        self.btn_discard = StyledButton(right, text="✕", width=30, height=28,
                                         command=self.discard, danger=True, font_size=8)
        self.btn_discard.pack(side=tk.LEFT, padx=1)

        # === 注册所有需要主题切换时重绘的 Canvas 组件 ===
        self._styled_buttons = [
            self.btn_undo, self.btn_redo,
            self.btn_save, self.btn_copy, self.btn_theme, self.btn_discard,
        ]
        self._track_canvas(self._custom_color_btn, '_draw_custom_color_btn')
        self._track_canvas(self._width_preview, '_draw_width_preview')
        self._track_canvas(self._btn_minus, '_redraw_minus_btn')
        self._track_canvas(self._btn_plus, '_redraw_plus_btn')

    def _draw_custom_color_btn(self):
        self._custom_color_btn.delete("all")
        self._custom_color_btn.create_oval(5, 2, 23, 20, fill=self.color,
                                           outline=T.BD2, width=1)
        self._custom_color_btn.create_text(14, 25, text="···", fill=T.TXT2,
                                           font=(T.FONT, 6))

    def _draw_width_preview(self):
        self._width_preview.delete("all")
        r = max(min(self.line_width, 8), 2)
        cx, cy = 25, 11
        self._width_preview.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        fill=self.color, outline="")

    def _adjust_width(self, delta):
        self.line_width = max(1, min(30, self.line_width + delta))
        self._width_label.configure(text=str(self.line_width))
        self._draw_width_preview()
        self.update_status()
        self.settings["last_line_width"] = self.line_width
        save_settings(self.settings)

    def _set_color(self, color):
        self.color = color
        self._draw_custom_color_btn()
        self._draw_width_preview()
        self._update_color_indicators()
        self.settings["last_color"] = self.color
        save_settings(self.settings)
        self.update_status()

    def _update_color_indicators(self):
        """重绘所有颜色选择按钮（主题切换时需重新绘制边框颜色）"""
        for cb, c in self._color_btns:
            cb.delete("all")
            outline = "#ffffff" if c == self.color else T.BD
            ow = 2 if c == self.color else 1
            cb.create_oval(2, 2, 18, 18, fill=c, outline=outline, width=ow)

    # ========== Canvas 重绘方法 ==========

    def _redraw_all_styled_buttons(self):
        """重绘所有 StyledButton 组件 — 先更新内部缓存的色值再 _draw()"""
        if not hasattr(self, '_styled_buttons'):
            return
        for sb in self._styled_buttons:
            try:
                if not sb.winfo_exists():
                    continue
                # 判断按钮类型并更新内部缓存色值为当前主题
                if sb._accent:
                    sb._fg = "#ffffff"
                    # accent 按钮不需要改 _bg，_draw 会用 T.ACCENT
                elif sb._danger and sb.text == "✕":
                    sb._bg = T.BG3
                    sb._fg = T.TXT2
                else:
                    # 普通按钮：背景随父容器
                    sb._bg = T.BG3
                    sb._fg = T.TXT1
                sb._draw()
            except Exception:
                pass

    def _redraw_minus_btn(self):
        """重绘粗细减号按钮"""
        if hasattr(self, '_btn_minus') and self._btn_minus.winfo_exists():
            self._btn_minus.delete("all")
            self._btn_minus.configure(bg=T.BG3)
            self._btn_minus.create_text(9, 10, text="−", fill=T.TXT1,
                                        font=(T.FONT, 11, "bold"))

    def _redraw_plus_btn(self):
        """重绘粗细加号按钮"""
        if hasattr(self, '_btn_plus') and self._btn_plus.winfo_exists():
            self._btn_plus.delete("all")
            self._btn_plus.configure(bg=T.BG3)
            self._btn_plus.create_text(9, 10, text="+", fill=T.TXT1,
                                       font=(T.FONT, 11, "bold"))

    def _build_sidebar(self):
        sidebar = tk.Frame(self.window, bg=T.BG2, width=self.toolbar_w)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        self._track(sidebar, 'bg', 'sidebar')

        tools_area = tk.Frame(sidebar, bg=T.BG2)
        tools_area.pack(fill=tk.X, padx=3, pady=(4, 0))
        self._track(tools_area, 'bg', 'sidebar')

        TOOLS = [
            ("✏ 画笔", "pen"),
            ("📏 直线", "line"),
            ("▭ 矩形", "rect"),
            ("◯ 圆形", "circle"),
            ("➤ 箭头", "arrow"),
            ("T 文字", "text"),
            ("▦ 马赛克", "mosaic"),
            ("🖍 高亮", "highlight"),
            ("◌ 橡皮", "eraser"),
            (". 水印", "watermark"),
        ]

        self.tool_btns = {}
        for display, tool_id in TOOLS:
            frame = tk.Frame(tools_area, bg=T.BG2)
            frame.pack(fill=tk.X, pady=0)

            btn = tk.Button(frame, text=display,
                            bg=T.BG2, fg=T.TXT1,
                            activebackground=T.BG3, activeforeground=T.TXT0,
                            relief="flat", bd=0, cursor="hand2",
                            font=(T.FONT, 8), anchor="w",
                            padx=8, pady=4, width=9,
                            command=lambda t=tool_id: self.select_tool(t))
            btn.pack(fill=tk.X)
            self.tool_btns[tool_id] = btn
            self._track(btn, 'bg', 'sidebar')
            self._track(btn, 'fg', 'text')

            # 悬停效果
            btn.bind("<Enter>",
                     lambda e, b=btn: b.configure(bg=T.BG3))
            btn.bind("<Leave>",
                     lambda e, b=btn, t_id=tool_id:
                     self._restore_tool_btn_bg(b, t_id))

        # 默认选中画笔
        if "pen" in self.tool_btns:
            self.tool_btns["pen"].configure(bg=T.ACCENT_BG, fg=T.ACCENT,
                                            activebackground=T.ACCENT_BG)

        # 底部缩放信息 — 更紧凑
        tk.Frame(sidebar, bg=T.BG2).pack(fill=tk.BOTH, expand=True)
        sep_sidebar = tk.Frame(sidebar, bg=T.BD, height=1)
        sep_sidebar.pack(fill=tk.X, padx=6)
        self._track(sep_sidebar, 'bg', 'card')

        zoom_frame = tk.Frame(sidebar, bg=T.BG2)
        zoom_frame.pack(fill=tk.X, padx=6, pady=4)
        self._zoom_label = tk.Label(zoom_frame, text=f"{int(self.scale * 100)}%",
                                    bg=T.BG2, fg=T.TXT2, font=(T.FONT_MONO, 7))
        self._zoom_label.pack()
        self._track(self._zoom_label, 'fg', 'text2')
        tk.Label(zoom_frame, text=f"{self.original_image.width}×{self.original_image.height}",
                 bg=T.BG2, fg=T.TXT3, font=(T.FONT_MONO, 6)).pack()
        self._track(zoom_frame.winfo_children()[-1], 'fg', 'text3')

    def _restore_tool_btn_bg(self, btn, tool_id):
        """恢复按钮背景色"""
        if tool_id == self.tool:
            btn.configure(bg=T.ACCENT_BG)
        else:
            btn.configure(bg=T.BG2)

    def _build_canvas(self):
        canvas_shell = tk.Frame(self.window, bg=T.CANVAS)
        canvas_shell.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.canvas = tk.Canvas(canvas_shell, bg=T.CANVAS,
                                 width=self.canvas_w, height=self.canvas_h,
                                 highlightthickness=0, cursor="cross")
        self.canvas.pack(expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

    def _build_bottombar(self):
        bar = tk.Frame(self.window, bg=T.BG2, height=self.bottom_h)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        bar.pack_propagate(False)
        self._track(bar, 'bg', 'bottombar')

        self._status_lbl = tk.Label(bar, text="", bg=T.BG2, fg=T.TXT2,
                                    font=(T.FONT, 8), anchor="w")
        self._status_lbl.pack(side=tk.LEFT, padx=8, fill=tk.Y)
        self._track(self._status_lbl, 'bg', 'bottombar')
        self._track(self._status_lbl, 'fg', 'status')

        self._coord_lbl = tk.Label(bar, text="",
                                   bg=T.BG2, fg=T.TXT3, font=(T.FONT_MONO, 7))
        self._coord_lbl.pack(side=tk.RIGHT, padx=8)
        self._track(self._coord_lbl, 'bg', 'bottombar')
        self._track(self._coord_lbl, 'fg', 'coord')

        self.update_status()

    def _zoom_fit(self):
        """缩放图片以适应画布（Ctrl+0）—— 恢复初始显示比例"""
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        max_cw = int(sw * 0.85) - self.toolbar_w - 40
        max_ch = int(sh * 0.85) - self.top_h - self.bottom_h - 80
        MIN_CANVAS_W = 580
        MIN_CANVAS_H = 300

        # 先按屏幕可用空间计算（上限 1.0）
        self.scale = min(max_cw / self.original_image.width,
                         max_ch / self.original_image.height, 1.0)
        canvas_w = int(self.original_image.width * self.scale)
        canvas_h = int(self.original_image.height * self.scale)

        # 如果太小则放大到最小画布尺寸（和初始化逻辑一致）
        if canvas_w < MIN_CANVAS_W or canvas_h < MIN_CANVAS_H:
            scale_up = min(MIN_CANVAS_W / self.original_image.width,
                           MIN_CANVAS_H / self.original_image.height)
            if (self.original_image.width * scale_up <= max_cw and
                    self.original_image.height * scale_up <= max_ch):
                self.scale = scale_up
            else:
                self.scale = min(max_cw / self.original_image.width,
                                 max_ch / self.original_image.height)

        self.canvas_w = int(self.original_image.width * self.scale)
        self.canvas_h = int(self.original_image.height * self.scale)
        self.canvas.configure(width=self.canvas_w, height=self.canvas_h)
        self.win_w = self.canvas_w + self.toolbar_w + 8
        self.win_h = self.canvas_h + self.top_h + self.bottom_h + 8
        x = max(0, (sw - self.win_w) // 2)
        y = max(0, (sh - self.win_h) // 2)
        self.window.geometry(f"{self.win_w}x{self.win_h}+{x}+{y}")
        self._zoom_label.configure(text=f"{int(self.scale * 100)}%")
        self.update_display()

    # ========== 工具选择 ==========

    def select_tool(self, tool_name):
        self.tool = tool_name
        for name, btn in self.tool_btns.items():
            if name == tool_name:
                btn.configure(bg=T.ACCENT_BG, fg=T.ACCENT, activebackground=T.ACCENT_BG)
            else:
                btn.configure(bg=T.BG2, fg=T.TXT1, activebackground=T.BG3)

        cursors = {
            "pen": "crosshair", "line": "crosshair", "rect": "crosshair",
            "circle": "crosshair", "arrow": "crosshair",
            "mosaic": "crosshair", "highlight": "crosshair",
            "text": "xterm", "eraser": "dotbox", "watermark": "arrow"
        }
        self.canvas.configure(cursor=cursors.get(tool_name, "crosshair"))
        self.update_status()

    def pick_color(self):
        result = colorchooser.askcolor(color=self.color, title="选择颜色")
        if result[1]:
            self._set_color(result[1])

    # ========== 画布事件 ==========

    def canvas_to_image(self, cx, cy):
        return int(cx / self.scale), int(cy / self.scale)

    def _pil_line_width(self):
        """将 canvas 线宽转换为 PIL 图像线宽（考虑缩放）"""
        return max(1, int(self.line_width / self.scale))

    def on_mouse_down(self, event):
        if self.tool == "text":
            ix, iy = self.canvas_to_image(event.x, event.y)
            self.add_text_at(ix, iy)
            return
        if self.tool == "watermark":
            self.add_watermark_dialog()
            return

        self.drawing = True
        self.start_x, self.start_y = event.x, event.y

        if self.tool in ("pen", "eraser"):
            self._last_x = event.x
            self._last_y = event.y
            ix, iy = self.canvas_to_image(event.x, event.y)
            draw = ImageDraw.Draw(self.display_image)
            pil_w = self._pil_line_width()
            if self.tool == "pen":
                r = max(pil_w // 2, 1)
                draw.ellipse([ix - r, iy - r, ix + r, iy + r], fill=self.color)
            elif self.tool == "eraser":
                r = max(pil_w * 3 // 2, 2)
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if dx * dx + dy * dy <= r * r:
                            px, py = ix + dx, iy + dy
                            if 0 <= px < self.display_image.width and \
                               0 <= py < self.display_image.height:
                                self.display_image.putpixel(
                                    (px, py), self.original_image.getpixel((px, py)))

        if self.tool in ("line", "rect", "circle", "arrow", "mosaic", "highlight"):
            self.current_overlay = None

    def on_mouse_move(self, event):
        if not self.drawing:
            ix, iy = self.canvas_to_image(event.x, event.y)
            self._coord_lbl.configure(
                text=f"{ix}, {iy}  |  {self.original_image.width}×{self.original_image.height}")
            return

        if self.tool in ("line", "rect", "circle", "arrow"):
            if self.current_overlay:
                self.canvas.delete(self.current_overlay)

            if self.tool in ("line", "arrow"):
                self.current_overlay = self.canvas.create_line(
                    self.start_x, self.start_y, event.x, event.y,
                    fill=self.color, width=self.line_width,
                    arrow="last" if self.tool == "arrow" else "none",
                    capstyle="round", joinstyle="round")
            elif self.tool == "rect":
                self.current_overlay = self.canvas.create_rectangle(
                    self.start_x, self.start_y, event.x, event.y,
                    outline=self.color, width=self.line_width)
            elif self.tool == "circle":
                self.current_overlay = self.canvas.create_oval(
                    self.start_x, self.start_y, event.x, event.y,
                    outline=self.color, width=self.line_width)

        elif self.tool in ("mosaic", "highlight"):
            if self.current_overlay:
                self.canvas.delete(self.current_overlay)
            if self.tool == "mosaic":
                self.current_overlay = self.canvas.create_rectangle(
                    self.start_x, self.start_y, event.x, event.y,
                    outline=self.color, width=2, dash=(4, 3))
            else:  # highlight
                r, g, b = hex_to_rgb(self.color)
                stipple = "gray50"
                self.current_overlay = self.canvas.create_rectangle(
                    self.start_x, self.start_y, event.x, event.y,
                    fill=self.color, outline="", stipple=stipple)

        elif self.tool == "pen":
            self.canvas.create_line(self._last_x, self._last_y,
                                    event.x, event.y,
                                    fill=self.color, width=self.line_width,
                                    capstyle="round", joinstyle="round")
            ix1, iy1 = self.canvas_to_image(self._last_x, self._last_y)
            ix2, iy2 = self.canvas_to_image(event.x, event.y)
            draw = ImageDraw.Draw(self.display_image)
            draw.line([ix1, iy1, ix2, iy2], fill=self.color, width=self._pil_line_width())
            self._last_x, self._last_y = event.x, event.y

        elif self.tool == "eraser":
            eraser_w = self.line_width * 3
            self.canvas.create_line(self._last_x, self._last_y,
                                    event.x, event.y,
                                    fill=T.CANVAS, width=eraser_w, capstyle="round")
            ix1, iy1 = self.canvas_to_image(self._last_x, self._last_y)
            ix2, iy2 = self.canvas_to_image(event.x, event.y)
            self.erase_on_pil(ix1, iy1, ix2, iy2, self._pil_line_width() * 3 // 2)
            self._last_x, self._last_y = event.x, event.y

        ix, iy = self.canvas_to_image(event.x, event.y)
        self._coord_lbl.configure(
            text=f"{ix}, {iy}  |  {self.original_image.width}×{self.original_image.height}")

    def on_mouse_up(self, event):
        if not self.drawing:
            return
        self.drawing = False

        if self.current_overlay:
            self.canvas.delete(self.current_overlay)
            self.current_overlay = None

        if self.tool in ("line", "rect", "circle", "arrow"):
            x1, y1 = self.canvas_to_image(self.start_x, self.start_y)
            x2, y2 = self.canvas_to_image(event.x, event.y)
            draw = ImageDraw.Draw(self.display_image)
            pil_w = self._pil_line_width()

            if self.tool == "line":
                draw.line([x1, y1, x2, y2], fill=self.color, width=pil_w)
            elif self.tool == "rect":
                draw.rectangle([x1, y1, x2, y2], outline=self.color, width=pil_w)
            elif self.tool == "circle":
                draw.ellipse([x1, y1, x2, y2], outline=self.color, width=pil_w)
            elif self.tool == "arrow":
                self.draw_arrow_pil(draw, x1, y1, x2, y2, self.color, pil_w)

            # 统一通过 update_display 刷新（包含所有图层合成）
            self.update_display()

        elif self.tool in ("mosaic", "highlight"):
            x1, y1 = self.canvas_to_image(self.start_x, self.start_y)
            x2, y2 = self.canvas_to_image(event.x, event.y)
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])
            if x2 - x1 > 2 and y2 - y1 > 2:
                if self.tool == "mosaic":
                    self.apply_mosaic(x1, y1, x2, y2, max(self.line_width * 2, 6))
                else:
                    self.apply_highlight(x1, y1, x2, y2)
            self.update_display()

        elif self.tool in ("pen", "eraser"):
            if hasattr(self, "_last_x"):
                del self._last_x, self._last_y
            self.update_display()

        self.save_state()

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.line_width = min(30, self.line_width + 1)
        else:
            self.line_width = max(1, self.line_width - 1)
        self._width_label.configure(text=str(self.line_width))
        self._draw_width_preview()
        self.update_status()
        self.settings["last_line_width"] = self.line_width
        save_settings(self.settings)

    # ========== 橡皮擦 ==========

    def erase_on_pil(self, x1, y1, x2, y2, radius):
        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        steps = max(int(dist), 1)
        pts = [(int(x1 + (x2 - x1) * i / steps), int(y1 + (y2 - y1) * i / steps))
               for i in range(steps + 1)]
        w, h = self.display_image.width, self.display_image.height
        for px, py in pts:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            self.display_image.putpixel(
                                (nx, ny), self.original_image.getpixel((nx, ny)))

    # ========== 箭头 ==========

    def draw_arrow_pil(self, draw, x1, y1, x2, y2, color, width):
        draw.line([x1, y1, x2, y2], fill=color, width=width)
        angle = math.atan2(y2 - y1, x2 - x1)
        alen = max(15, width * 5)
        aa = math.pi / 6
        px1 = x2 - alen * math.cos(angle - aa)
        py1 = y2 - alen * math.sin(angle - aa)
        px2 = x2 - alen * math.cos(angle + aa)
        py2 = y2 - alen * math.sin(angle + aa)
        draw.polygon([x2, y2, px1, py1, px2, py2], fill=color)

    # ========== 马赛克与高亮 ==========

    def apply_mosaic(self, x1, y1, x2, y2, block=8):
        """对矩形区域做像素化处理"""
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(self.display_image.width, x2)
        y2 = min(self.display_image.height, y2)
        if x2 <= x1 or y2 <= y1:
            return
        region = self.display_image.crop((x1, y1, x2, y2))
        # 缩小再放大实现像素化
        small_w = max(1, region.width // block)
        small_h = max(1, region.height // block)
        small = region.resize((small_w, small_h), Image.LANCZOS)
        pixelated = small.resize((region.width, region.height), Image.NEAREST)
        self.display_image.paste(pixelated, (x1, y1))

    def apply_highlight(self, x1, y1, x2, y2):
        """半透明高亮覆盖"""
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(self.display_image.width, x2)
        y2 = min(self.display_image.height, y2)
        if x2 <= x1 or y2 <= y1:
            return
        r, g, b = hex_to_rgb(self.color)
        # 创建半透明覆盖层
        overlay = Image.new("RGBA", (x2 - x1, y2 - y1), (r, g, b, 100))
        base = self.display_image.convert("RGBA")
        # 在指定区域合成
        region = base.crop((x1, y1, x2, y2))
        merged = Image.alpha_composite(region, overlay)
        self.display_image.paste(merged.convert("RGB"), (x1, y1))

    # ========== 文字 ==========

    def add_text_at(self, ix, iy):
        dlg = tk.Toplevel(self.window)
        dlg.title("添加文字")
        dlg.configure(bg=T.BG2)
        dlg.transient(self.window)
        dlg.grab_set()
        dlg.resizable(False, False)

        w, h = 380, 180
        x = self.window.winfo_x() + (self.window.winfo_width() - w) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        frame = tk.Frame(dlg, bg=T.BG2)
        frame.pack(expand=True, fill=tk.BOTH, padx=16, pady=14)

        tk.Label(frame, text="输入文字内容", bg=T.BG2, fg=T.TXT1,
                 font=(T.FONT, 10, "bold")).pack(anchor="w")

        entry = tk.Entry(frame, bg=T.BG3, fg=T.TXT0,
                         insertbackground=T.TXT0, font=(T.FONT, 13),
                         relief="flat", bd=8)
        entry.pack(fill=tk.X, pady=(8, 10))
        entry.focus_set()

        row = tk.Frame(frame, bg=T.BG2)
        row.pack(fill=tk.X)
        tk.Label(row, text="字号:", bg=T.BG2, fg=T.TXT2,
                 font=(T.FONT, 9)).pack(side=tk.LEFT)
        size_var = tk.IntVar(value=28)
        tk.Spinbox(row, from_=8, to=180, textvariable=size_var, width=4,
                   bg=T.BG3, fg=T.TXT0, bd=0, relief="flat",
                   font=(T.FONT, 9)).pack(side=tk.LEFT, padx=6)

        def ok():
            txt = entry.get().strip()
            if txt:
                self.place_text(ix, iy, txt, size_var.get())
                self.save_state()
                self.update_display()
            dlg.destroy()

        btn_row = tk.Frame(frame, bg=T.BG2)
        btn_row.pack(fill=tk.X, pady=(14, 0))
        StyledButton(btn_row, text="取消", width=72, height=30,
                     command=dlg.destroy, font_size=9).pack(side=tk.RIGHT, padx=4)
        StyledButton(btn_row, text="确定", width=72, height=30,
                     command=ok, accent=True, font_size=9).pack(side=tk.RIGHT)

        entry.bind("<Return>", lambda e: ok())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def place_text(self, x, y, text, font_size):
        draw = ImageDraw.Draw(self.text_layer)
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x - tw // 2, y - th // 2), text, fill=self.color, font=font)

    # ========== 水印 ==========

    def add_watermark_dialog(self):
        dlg = tk.Toplevel(self.window)
        dlg.title("添加水印")
        dlg.configure(bg=T.BG2)
        dlg.transient(self.window)
        dlg.grab_set()
        dlg.resizable(False, False)

        w, h = 460, 420
        x = self.window.winfo_x() + (self.window.winfo_width() - w) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        frame = tk.Frame(dlg, bg=T.BG2)
        frame.pack(expand=True, fill=tk.BOTH, padx=18, pady=16)

        label_kw = {"bg": T.BG2, "fg": T.TXT2, "font": (T.FONT, 9)}

        tk.Label(frame, text="水印文字", bg=T.BG2, fg=T.TXT1,
                 font=(T.FONT, 10, "bold")).pack(anchor="w")
        txt_entry = tk.Entry(frame, bg=T.BG3, fg=T.TXT0,
                             insertbackground=T.TXT0, font=(T.FONT, 12),
                             relief="flat", bd=8)
        txt_entry.insert(0, self.settings.get("default_watermark_text", "机密文件"))
        txt_entry.pack(fill=tk.X, pady=(6, 12))
        txt_entry.focus_set()
        txt_entry.select_range(0, tk.END)

        # 字号
        r1 = tk.Frame(frame, bg=T.BG2)
        r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="字体大小", **label_kw).pack(side=tk.LEFT)
        size_var = tk.IntVar(value=self.settings.get("default_watermark_size", 52))
        tk.Spinbox(r1, from_=12, to=200, textvariable=size_var, width=4,
                   bg=T.BG3, fg=T.TXT0, bd=0, relief="flat",
                   font=(T.FONT, 9)).pack(side=tk.LEFT, padx=6)

        # 透明度
        r2 = tk.Frame(frame, bg=T.BG2)
        r2.pack(fill=tk.X, pady=3)
        tk.Label(r2, text="透明度", **label_kw).pack(side=tk.LEFT)
        opacity_var = tk.IntVar(value=self.settings.get("default_watermark_opacity", 25))
        scale = tk.Scale(r2, from_=5, to=90, orient=tk.HORIZONTAL,
                         variable=opacity_var, bg=T.BG2, fg=T.TXT0,
                         highlightbackground=T.BG2, troughcolor=T.BG3,
                         activebackground=T.ACCENT, length=180,
                         bd=0, sliderrelief="flat")
        scale.pack(side=tk.LEFT, padx=10)
        tk.Label(r2, textvariable=opacity_var, bg=T.BG2, fg=T.TXT1,
                 font=(T.FONT_MONO, 9), width=3).pack(side=tk.LEFT)
        tk.Label(r2, text="%", bg=T.BG2, fg=T.TXT2, font=(T.FONT, 9)).pack(side=tk.LEFT)

        # 旋转
        r3 = tk.Frame(frame, bg=T.BG2)
        r3.pack(fill=tk.X, pady=3)
        tk.Label(r3, text="旋转角度", **label_kw).pack(side=tk.LEFT)
        rot_var = tk.IntVar(value=self.settings.get("default_watermark_rotation", 28))
        scale2 = tk.Scale(r3, from_=0, to=90, orient=tk.HORIZONTAL,
                          variable=rot_var, bg=T.BG2, fg=T.TXT0,
                          highlightbackground=T.BG2, troughcolor=T.BG3,
                          activebackground=T.ACCENT, length=180,
                          bd=0, sliderrelief="flat")
        scale2.pack(side=tk.LEFT, padx=10)
        tk.Label(r3, textvariable=rot_var, bg=T.BG2, fg=T.TXT1,
                 font=(T.FONT_MONO, 9), width=3).pack(side=tk.LEFT)
        tk.Label(r3, text="°", bg=T.BG2, fg=T.TXT2, font=(T.FONT, 9)).pack(side=tk.LEFT)

        # 水印颜色 — 使用预设颜色网格 + 自定义选择
        r4 = tk.Frame(frame, bg=T.BG2)
        r4.pack(fill=tk.X, pady=3)
        tk.Label(r4, text="水印颜色", **label_kw).pack(side=tk.LEFT)

        default_wm_color = self.settings.get("default_watermark_color", "#888888")
        wm_color = tk.StringVar(value=default_wm_color)

        # 颜色圆点预览
        self._wm_color_dot = tk.Canvas(r4, width=24, height=24, bg=T.BG2,
                                       highlightthickness=0, cursor="hand2")
        self._wm_color_dot.pack(side=tk.LEFT, padx=4)

        def _draw_wm_dot(clr):
            self._wm_color_dot.delete("all")
            self._wm_color_dot.create_oval(2, 2, 22, 22, fill=clr, outline=T.BD2, width=1)
        _draw_wm_dot(default_wm_color)

        # 颜色网格行
        wm_palette = [
            "#FFFFFF", "#CCCCCC", "#999999", "#666666", "#333333", "#000000",
            "#FF3B30", "#FF6B35", "#FF9500", "#FFCC02", "#FF2D55", "#FF1493",
            "#34C759", "#30B0C7", "#007AFF", "#5856D6", "#AF52DE", "#8B4513",
        ]

        color_grid = tk.Frame(frame, bg=T.BG2)
        color_grid.pack(fill=tk.X, pady=(4, 0))

        for idx, clr in enumerate(wm_palette):
            row_idx = idx // 6
            col_idx = idx % 6
            # 确保行存在
            if col_idx == 0:
                row_frame = tk.Frame(color_grid, bg=T.BG2)
                row_frame.pack(fill=tk.X, pady=1)

            cell = tk.Canvas(row_frame, width=26, height=26, bg=T.BG2,
                             highlightthickness=0, cursor="hand2")
            cell.pack(side=tk.LEFT, padx=2)
            border = "#ffffff" if clr == default_wm_color else T.BD
            cell.create_rectangle(1, 1, 25, 25, fill=clr, outline=border, width=2)

            def make_callback(c=clr, cv=cell, row_f=row_frame):
                def cb(event=None):
                    wm_color.set(c)
                    _draw_wm_dot(c)
                    # 更新所有颜色格子的边框
                    _update_wm_grid_borders()
                return cb

            cell.bind("<Button-1>", make_callback())

        # 更新所有颜色格子边框的方法
        def _update_wm_grid_borders():
            current = wm_color.get().upper()
            for child in color_grid.winfo_children():
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Canvas) and sub is not self._wm_color_dot:
                        items = sub.find_all()
                        if items:
                            fill_color = sub.itemcget(items[0], "fill")
                            is_current = (fill_color.upper() == current)
                            sub.itemconfig(items[0], outline=("#ffffff" if is_current else T.BD))

        # 自定义颜色按钮
        custom_row = tk.Frame(frame, bg=T.BG2)
        custom_row.pack(fill=tk.X, pady=(4, 0))

        def pick_wm_clr():
            # 临时释放 grab 以避免 colorchooser 冲突
            dlg.grab_release()
            dlg.after(100, lambda: _do_pick_color())

        def _do_pick_color():
            try:
                result = colorchooser.askcolor(color=wm_color.get(), title="水印颜色")
                dlg.grab_set()
                if result and result[1]:
                    wm_color.set(result[1])
                    _draw_wm_dot(result[1])
                    _update_wm_grid_borders()
            except Exception:
                dlg.grab_set()

        StyledButton(custom_row, text="自定义颜色...", width=120, height=26,
                     command=pick_wm_clr, font_size=8).pack(side=tk.LEFT)
        tk.Label(custom_row, textvariable=wm_color, bg=T.BG2, fg=T.TXT3,
                 font=(T.FONT_MONO, 8)).pack(side=tk.LEFT, padx=10)

        # 模式
        r5 = tk.Frame(frame, bg=T.BG2)
        r5.pack(fill=tk.X, pady=(8, 3))
        tk.Label(r5, text="排列方式", **label_kw).pack(side=tk.LEFT)
        mode_var = tk.StringVar(value="tile")
        tk.Radiobutton(r5, text="平铺", variable=mode_var, value="tile",
                       bg=T.BG2, fg=T.TXT1, selectcolor=T.BG3,
                       activebackground=T.BG2, activeforeground=T.TXT0,
                       font=(T.FONT, 9)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(r5, text="居中", variable=mode_var, value="center",
                       bg=T.BG2, fg=T.TXT1, selectcolor=T.BG3,
                       activebackground=T.BG2, activeforeground=T.TXT0,
                       font=(T.FONT, 9)).pack(side=tk.LEFT, padx=10)

        def apply_and_remember():
            if remember_var.get():
                self.settings["default_watermark_text"] = txt_entry.get().strip()
                self.settings["default_watermark_size"] = size_var.get()
                self.settings["default_watermark_opacity"] = opacity_var.get()
                self.settings["default_watermark_rotation"] = rot_var.get()
                self.settings["default_watermark_color"] = wm_color.get()
                save_settings(self.settings)
            txt = txt_entry.get().strip()
            if txt:
                self.apply_watermark(
                    text=txt, font_size=size_var.get(),
                    opacity=opacity_var.get(), rotation=rot_var.get(),
                    color=wm_color.get(), mode=mode_var.get())
                self.save_state()
                self.update_display()
            dlg.destroy()

        btn_row = tk.Frame(frame, bg=T.BG2)
        btn_row.pack(fill=tk.X, pady=(14, 0))
        remember_var = tk.BooleanVar(value=False)
        tk.Checkbutton(btn_row, text="设为默认", variable=remember_var,
                       bg=T.BG2, fg=T.TXT3, selectcolor=T.BG3,
                       activebackground=T.BG2, activeforeground=T.TXT1,
                       font=(T.FONT, 8)).pack(side=tk.LEFT)
        StyledButton(btn_row, text="取消", width=72, height=30,
                     command=dlg.destroy, font_size=9).pack(side=tk.RIGHT, padx=4)
        StyledButton(btn_row, text="应用水印", width=88, height=30,
                     command=apply_and_remember, accent=True, font_size=9).pack(side=tk.RIGHT)

        txt_entry.bind("<Return>", lambda e: apply_and_remember())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def apply_watermark(self, text, font_size, opacity, rotation, color, mode):
        self.watermark_layer = Image.new("RGBA", self.original_image.size, (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(self.watermark_layer)
        r, g, b = hex_to_rgb(color)
        alpha = int(255 * opacity / 100)
        wm_color = (r, g, b, alpha)
        font = get_font(font_size)
        bbox = wm_draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        iw, ih = self.original_image.size

        if mode == "center":
            temp = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
            ImageDraw.Draw(temp).text((20, 20), text, fill=wm_color, font=font)
            temp = temp.rotate(rotation, expand=True, resample=Image.BICUBIC,
                               fillcolor=(0, 0, 0, 0))
            tw2, th2 = temp.size
            self.watermark_layer.paste(temp, ((iw - tw2) // 2, (ih - th2) // 2), temp)
        else:
            spacing_x = int(tw * 3.5)
            spacing_y = int(th * 3.5)
            for sy in range(-th, ih + th, spacing_y):
                for sx in range(-tw, iw + tw, spacing_x):
                    temp = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
                    ImageDraw.Draw(temp).text((20, 20), text, fill=wm_color, font=font)
                    temp = temp.rotate(rotation, expand=True, resample=Image.BICUBIC,
                                       fillcolor=(0, 0, 0, 0))
                    self.watermark_layer.paste(temp, (sx, sy), temp)

    # ========== 撤销/重做（保存/恢复完整快照）==========

    def save_state(self):
        self.history = self.history[:self.history_pos + 1]
        self.history.append(self._make_snapshot())
        self.history_pos += 1
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.history_pos = len(self.history) - 1

    def composite_all_layers(self):
        base = self.display_image.convert("RGBA")
        base = Image.alpha_composite(base, self.text_layer)
        base = Image.alpha_composite(base, self.watermark_layer)
        return base

    def undo(self):
        if self.history_pos > 0:
            self.history_pos -= 1
            self._restore_snapshot(self.history[self.history_pos])
            self.update_display()
            self._status_lbl.configure(text="  已撤销")

    def redo(self):
        if self.history_pos < len(self.history) - 1:
            self.history_pos += 1
            self._restore_snapshot(self.history[self.history_pos])
            self.update_display()
            self._status_lbl.configure(text="  已重做")

    def clear_all(self):
        if messagebox.askyesno("确认", "确定清除所有标注？"):
            self.display_image = self.original_image.copy()
            self.text_layer = Image.new("RGBA", self.original_image.size, (0, 0, 0, 0))
            self.watermark_layer = Image.new("RGBA", self.original_image.size, (0, 0, 0, 0))
            self.canvas.delete("all")
            self.save_state()
            self.update_display()

    # ========== 显示更新 ==========

    def update_display(self):
        merged = self.composite_all_layers()
        if self.scale != 1.0:
            display = merged.resize((self.canvas_w, self.canvas_h), Image.LANCZOS)
        else:
            display = merged
        self._photo = ImageTk.PhotoImage(display)
        self.canvas.delete("all")
        self.canvas.create_image(self.canvas_w // 2, self.canvas_h // 2,
                                 image=self._photo, anchor="center")

    def update_status(self):
        names = {
            "pen": "画笔 - 自由绘制",  "line": "直线 - 拖拽绘制",
            "rect": "矩形 - 拖拽绘制", "circle": "圆形 - 拖拽绘制",
            "arrow": "箭头 - 拖拽绘制", "text": "文字 - 点击添加文字",
            "mosaic": "马赛克 - 拖拽马赛克", "highlight": "高亮 - 半透明高亮",
            "eraser": "橡皮擦 - 擦除标注", "watermark": "水印 - 添加水印",
        }
        info = f"  {names.get(self.tool, '')}  |  {self.color}  |  {self.line_width}px"
        self._status_lbl.configure(text=info)

    # ========== 保存与复制 ==========

    def save_image(self):
        merged = self.composite_all_layers()
        fmt = self.settings.get("file_format", "PNG")
        ext = {"PNG": ".png", "JPEG": ".jpg", "BMP": ".bmp"}.get(fmt, ".png")

        default_name = f"截图_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        initial_dir = self.settings.get("save_path", os.path.expanduser("~/Desktop"))

        path = filedialog.asksaveasfilename(
            title="保存截图",
            initialdir=initial_dir,
            initialfile=default_name,
            defaultextension=ext,
            filetypes=[
                ("PNG 图片", "*.png"),
                ("JPEG 图片", "*.jpg"),
                ("BMP 图片", "*.bmp"),
                ("所有文件", "*.*"),
            ])

        if path:
            try:
                save_dir = os.path.dirname(path)
                self.settings["save_path"] = save_dir
                save_settings(self.settings)

                _, save_ext = os.path.splitext(path)
                if save_ext.lower() in (".jpg", ".jpeg"):
                    merged.convert("RGB").save(path, "JPEG", quality=95)
                else:
                    merged.save(path)

                self.result_image = path
                self._status_lbl.configure(text=f"  已保存: {os.path.basename(path)}")

                # 记录历史
                try:
                    add_history(path, merged.width, merged.height)
                except Exception:
                    pass

                if self.on_save_callback:
                    self.on_save_callback(path)

                messagebox.showinfo("保存成功", f"截图已保存到:\n{path}")
            except Exception as e:
                messagebox.showerror("保存失败", str(e))

    def copy_to_clipboard(self):
        try:
            merged = self.composite_all_layers()
            temp_path = os.path.join(os.environ.get("TEMP", "."),
                                     f"_screenshot_{datetime.datetime.now():%Y%m%d%H%M%S}.png")
            merged.save(temp_path, "PNG")
            ps_cmd = (
                'Add-Type -AssemblyName System.Windows.Forms;'
                f'$img=[System.Drawing.Image]::FromFile("{temp_path}");'
                '[System.Windows.Forms.Clipboard]::SetImage($img);'
                '$img.Dispose();'
            )
            subprocess.run(["powershell", "-Command", ps_cmd],
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                os.remove(temp_path)
            except Exception:
                pass
            self._status_lbl.configure(text="  已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("复制失败", str(e))

    def toggle_theme(self, _toggle=True):
        """切换或同步主题。
        _toggle=True:  翻转主题并刷新（编辑器自身的主题按钮）
        _toggle=False: 只刷新到当前主题（被 FloatingToolbar 通知时）"""
        if _toggle:
            new_theme = T.toggle_theme()
            self.settings["theme"] = new_theme
            save_settings(self.settings)
            # 通知 FloatingToolbar 同步跟新（不重复翻转）
            if self.on_theme_callback:
                self.on_theme_callback()
        # 无论是否翻转，都要用当前主题刷新所有组件
        self._apply_theme_to_tracked()

    def discard(self):
        if self.history_pos > 0:
            if not messagebox.askyesno("确认", "确定丢弃当前截图？"):
                return
        self._photo = None
        self.window.destroy()


# ==================== 浮动工具栏 ====================

class FloatingToolbar:
    """现代浮动主界面（4 模式 + 双主题 + 历史记录）"""

    def __init__(self, settings):
        self.settings = settings
        self.running = True
        self.editors = []
        self._thumbs = []  # 历史缩略图 PhotoImage 引用（防 GC）

        # 应用保存的主题
        T.set_theme(settings.get("theme", "dark"))

        # 创建无边框窗口
        self.window = tk.Tk()
        self.window.title(APP_NAME)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # 窗口尺寸（紧凑版）
        self.w = 280
        self.h = 420

        sw = self.window.winfo_screenwidth()
        self.window.geometry(f"{self.w}x{self.h}+{sw - self.w - 20}+20")

        # 外层 Canvas（绘制圆角边框 + 阴影），内层 Frame 承载内容
        self._cv = tk.Canvas(self.window, width=self.w, height=self.h,
                             bg=T.BG0, highlightthickness=0)
        self._cv.pack(fill=tk.BOTH, expand=True)

        self._content = tk.Frame(self._cv, bg=T.BG1)
        self._content_window_id = self._cv.create_window(
            self.w // 2, self.h // 2, window=self._content,
            width=self.w - 4, height=self.h - 4)

        self._build_ui()
        self._bind_drag()
        self._refresh_history()

        # 热键
        if HAS_KEYBOARD:
            try:
                kb.add_hotkey(self.settings.get("hotkey", "ctrl+shift+s"),
                              self.do_fullscreen_capture)
            except Exception:
                pass

    # ========== UI 构建 ==========

    def _build_ui(self):
        for w in self._content.winfo_children():
            w.destroy()
        self._thumbs = []

        # 标题栏
        title_bar = tk.Frame(self._content, bg=T.BG2, height=32)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text=APP_NAME, bg=T.BG2, fg=T.TXT0,
                 font=(T.FONT, 9, "bold")).pack(side=tk.LEFT, padx=10)

        # 右侧按钮组
        right_btns = tk.Frame(title_bar, bg=T.BG2)
        right_btns.pack(side=tk.RIGHT, padx=4)

        # 主题切换按钮
        self._theme_btn_cv = tk.Canvas(right_btns, width=26, height=26, bg=T.BG2,
                                       highlightthickness=0, cursor="hand2")
        self._theme_btn_cv.pack(side=tk.RIGHT, padx=1)
        self._draw_theme_icon(self._theme_btn_cv)
        self._theme_btn_cv.bind("<Button-1>", lambda e: self._toggle_theme())
        self._theme_btn_cv.bind("<Enter>", lambda e: self._theme_btn_cv.configure(bg=T.BG3))
        self._theme_btn_cv.bind("<Leave>", lambda e: self._theme_btn_cv.configure(bg=T.BG2))

        # 关闭按钮
        close_btn = tk.Canvas(right_btns, width=26, height=26, bg=T.BG2,
                               highlightthickness=0, cursor="hand2")
        close_btn.pack(side=tk.RIGHT)
        close_btn.create_text(13, 13, text="✕", fill=T.TXT2,
                               font=(T.FONT, 10))
        close_btn.bind("<Button-1>", lambda e: self.on_exit())
        close_btn.bind("<Enter>", lambda e: (close_btn.configure(bg=T.RED),
                                              close_btn.itemconfig("all", fill=T.TXT0)))
        close_btn.bind("<Leave>", lambda e: (close_btn.configure(bg=T.BG2),
                                              close_btn.itemconfig("all", fill=T.TXT2)))

        # 截图模式区
        mode_frame = tk.Frame(self._content, bg=T.BG1)
        mode_frame.pack(fill=tk.X, padx=12, pady=(8, 4))

        tk.Label(mode_frame, text="截图模式", bg=T.BG1, fg=T.TXT2,
                 font=(T.FONT, 7)).pack(anchor="w")

        grid = tk.Frame(mode_frame, bg=T.BG1)
        grid.pack(fill=tk.X, pady=(3, 0))

        modes = [
            ("全屏", "fullscreen", T.ACCENT),
            ("区域", "region", darken(T.ACCENT, 0.15)),
        ]
        for i, (text, mode_id, color) in enumerate(modes):
            cell = tk.Frame(grid, bg=T.BG1)
            cell.pack(side=tk.LEFT, fill=tk.X, expand=True,
                      padx=(0 if i == 0 else 5, 0))
            cv = tk.Canvas(cell, width=122, height=42, bg=T.BG1,
                           highlightthickness=0, cursor="hand2")
            cv.pack()
            cmd = getattr(self, f"do_{mode_id}_capture")
            cv.bind("<Button-1>", lambda e, c=cmd: c())
            cv.bind("<Enter>", lambda e, c=cv, t=text, cl=color: self._draw_mode_btn(c, t, cl, hover=True))
            cv.bind("<Leave>", lambda e, c=cv, t=text, cl=color: self._draw_mode_btn(c, t, cl, hover=False))
            self._draw_mode_btn(cv, text, color)

        # 历史记录区
        hist_frame = tk.Frame(self._content, bg=T.BG1)
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 4))

        hist_header = tk.Frame(hist_frame, bg=T.BG1)
        hist_header.pack(fill=tk.X)
        tk.Label(hist_header, text="历史记录", bg=T.BG1, fg=T.TXT2,
                 font=(T.FONT, 7)).pack(side=tk.LEFT)
        self._hist_count_lbl = tk.Label(hist_header, text="", bg=T.BG1, fg=T.TXT3,
                                        font=(T.FONT, 7))
        self._hist_count_lbl.pack(side=tk.RIGHT)

        # 历史列表容器
        hist_shell = tk.Frame(hist_frame, bg=T.BG2, highlightthickness=0)
        hist_shell.pack(fill=tk.BOTH, expand=True, pady=(3, 0))

        self._hist_canvas = tk.Canvas(hist_shell, bg=T.BG2, highlightthickness=0,
                                      width=0, height=0)
        hist_scroll = tk.Scrollbar(hist_shell, orient="vertical",
                                   command=self._hist_canvas.yview)
        self._hist_inner = tk.Frame(self._hist_canvas, bg=T.BG2)
        self._hist_inner.bind("<Configure>",
                              lambda e: self._hist_canvas.configure(
                                  scrollregion=self._hist_canvas.bbox("all")))
        self._hist_canvas.create_window((0, 0), window=self._hist_inner, anchor="nw")
        self._hist_canvas.configure(yscrollcommand=hist_scroll.set)
        self._hist_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._hist_canvas.bind("<MouseWheel>",
                               lambda e: self._hist_canvas.yview_scroll(
                                   int(-1 * (e.delta / 120)), "units"))

        # 底部操作栏
        bottom = tk.Frame(self._content, bg=T.BG2, height=38)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)

        left_btns = tk.Frame(bottom, bg=T.BG2)
        left_btns.pack(side=tk.LEFT, padx=6, pady=5)
        StyledButton(left_btns, text="设置", width=56, height=24,
                     command=self.open_settings, font_size=7).pack(side=tk.LEFT, padx=1)

        status_text = "热键就绪" if HAS_KEYBOARD else "热键不可用"
        self._status_lbl = tk.Label(bottom, text=status_text, bg=T.BG2,
                                    fg=T.GREEN if HAS_KEYBOARD else T.ORANGE,
                                    font=(T.FONT, 7))
        self._status_lbl.pack(side=tk.RIGHT, padx=8)

    def _draw_mode_btn(self, cv, text, color, hover=False):
        cv.delete("all")
        w, h = 122, 38
        r = 6
        fill = lighten(color, 0.12) if hover else color
        points = [
            r, 0, w - r, 0, w, 0, w, r, w, h - r,
            w, h, w - r, h, r, h, 0, h, 0, h - r, 0, r, 0, 0,
        ]
        cv.create_polygon(points, fill=fill, outline=fill, smooth=True, width=1)
        cv.create_text(w // 2, h // 2, text=text, fill="#ffffff",
                       font=(T.FONT, 9, "bold"))

    def _draw_theme_icon(self, cv):
        """根据当前主题绘制太阳/月亮图标"""
        cv.delete("all")
        theme = T.get_theme()
        if theme == "dark":
            # 月亮
            cv.create_arc(6, 6, 22, 22, start=30, extent=200, style="arc",
                          outline=T.TXT1, width=1.5)
        else:
            # 太阳
            cv.create_oval(10, 10, 18, 18, outline=T.TXT1, width=1.5)
            for ang in range(0, 360, 45):
                x1 = 14 + 5 * math.cos(math.radians(ang))
                y1 = 14 + 5 * math.sin(math.radians(ang))
                x2 = 14 + 8 * math.cos(math.radians(ang))
                y2 = 14 + 8 * math.sin(math.radians(ang))
                cv.create_line(x1, y1, x2, y2, fill=T.TXT1, width=1.5)

    def _toggle_theme(self):
        """切换深色/浅色主题 — 销毁内容容器完整重建 + 通知编辑器"""
        new_theme = T.toggle_theme()
        self.settings["theme"] = new_theme
        save_settings(self.settings)

        # 1) 更新外层 Canvas 背景
        try:
            self._cv.configure(bg=T.BG0)
        except Exception:
            pass

        # 2) 销毁旧的内容容器，创建全新的（确保无残留状态）
        self._content.destroy()
        self._content = tk.Frame(self._cv, bg=T.BG1)
        self._cv.create_window(
            self.w // 2, self.h // 2, window=self._content,
            width=self.w - 4, height=self.h - 4)

        # 3) 重建浮动工具栏 UI（全新子组件用新的 T.* 值）
        self._build_ui()

        # 4) 刷新历史记录
        self._refresh_history()

        # 5) 强制 Tkinter 处理所有待处理事件，确保渲染完成
        self.window.update_idletasks()

        # 6) 通知所有打开的编辑器窗口同步切换主题（仅刷新，不重复翻转）
        for ed in self.editors[:]:
            try:
                if ed.window.winfo_exists():
                    ed.toggle_theme(_toggle=False)
            except Exception:
                pass

    def _refresh_history(self):
        """刷新历史记录列表"""
        for w in self._hist_inner.winfo_children():
            w.destroy()
        self._thumbs = []

        history = load_history()
        self._hist_count_lbl.configure(text=f"共 {len(history)} 张")

        if not history:
            tk.Label(self._hist_inner, text="暂无历史记录", bg=T.BG2, fg=T.TXT3,
                     font=(T.FONT, 8)).pack(pady=20, padx=10)
            return

        for item in history[:20]:
            row = tk.Frame(self._hist_inner, bg=T.BG2)
            row.pack(fill=tk.X, padx=4, pady=2)

            thumb = make_thumbnail(item.get("path", ""), size=(60, 38))
            if thumb:
                self._thumbs.append(thumb)
                thumb_lbl = tk.Label(row, image=thumb, bg=T.BG2)
                thumb_lbl.pack(side=tk.LEFT, padx=4, pady=3)
            else:
                tk.Label(row, text="🖼", bg=T.BG2, fg=T.TXT3,
                         font=(T.FONT, 12), width=8).pack(side=tk.LEFT, padx=4)

            info = tk.Frame(row, bg=T.BG2)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Label(info, text=item.get("name", "")[:18], bg=T.BG2, fg=T.TXT0,
                     font=(T.FONT, 8), anchor="w").pack(fill=tk.X)
            tk.Label(info, text=f"{item.get('time', '')}  {item.get('size', '')}",
                     bg=T.BG2, fg=T.TXT2, font=(T.FONT_MONO, 7), anchor="w").pack(fill=tk.X)

            # 悬停效果
            row.bind("<Enter>", lambda e, r=row: r.configure(bg=T.BG3))
            row.bind("<Leave>", lambda e, r=row: r.configure(bg=T.BG2))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, p=item.get("path", ""): self._open_history(p))

    def _open_history(self, path):
        """打开历史截图"""
        if not os.path.exists(path):
            messagebox.showwarning("提示", "文件不存在，可能已被移动或删除")
            return
        try:
            img = Image.open(path)
            self._open_editor(img)
        except Exception as e:
            messagebox.showerror("打开失败", str(e))

    def _bind_drag(self):
        self._drag_x = None
        self._drag_y = None
        self._cv.bind("<Button-1>", self._drag_start)
        self._cv.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        if event.y < 36:
            self._drag_x = event.x
            self._drag_y = event.y

    def _drag_move(self, event):
        if self._drag_x is not None and event.y < 50:
            dx = event.x - self._drag_x
            dy = event.y - self._drag_y
            x = self.window.winfo_x() + dx
            y = self.window.winfo_y() + dy
            self.window.geometry(f"+{x}+{y}")

    # ========== 截图模式 ==========

    def do_fullscreen_capture(self):
        """全屏截图"""
        self.window.withdraw()
        self.window.after(300, self._capture_fullscreen)

    def _capture_fullscreen(self):
        try:
            img = ImageGrab.grab()
            self.window.deiconify()
            self._open_editor(img)
        except Exception as e:
            self.window.deiconify()
            messagebox.showerror("截图失败", str(e))

    def do_region_capture(self):
        """区域截图"""
        self.window.withdraw()
        self.window.after(200, self._start_region_select)

    def _start_region_select(self):
        """启动区域选择器"""
        try:
            def on_region_selected(region):
                if region is None:
                    # 用户取消
                    self.window.deiconify()
                    return
                x1, y1, x2, y2 = region
                self.window.deiconify()
                # 截取区域
                img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                self._open_editor(img)

            selector = RegionSelector(self.settings, on_region_selected)
            self.window.wait_window(selector.win)
        except Exception as e:
            self.window.deiconify()
            messagebox.showerror("区域截图失败", str(e))

    def _open_editor(self, img):
        """打开截图编辑器（同时只允许一个）"""
        # 关闭已打开的编辑器窗口
        for ed in self.editors[:]:
            try:
                if ed.window.winfo_exists():
                    ed.window.destroy()
            except Exception:
                pass
        self.editors.clear()

        editor = ScreenshotEditor(img, self.settings,
                                   on_save_callback=self._on_saved,
                                   on_theme_callback=self._on_editor_theme_changed)
        self.editors.append(editor)
        self.window.wait_window(editor.window)
        if editor in self.editors:
            self.editors.remove(editor)

    def _on_saved(self, path):
        self._status_lbl.configure(text=f"已保存: {os.path.basename(path)}")
        self._refresh_history()
        self.window.after(3000, lambda: self._status_lbl.configure(
            text="热键就绪" if HAS_KEYBOARD else "热键不可用"))

    def _on_editor_theme_changed(self):
        """编辑器主题按钮被点击时，同步刷新浮动工具栏。"""
        self._cv.configure(bg=T.BG0)
        self._content.destroy()
        self._content = tk.Frame(self._cv, bg=T.BG1)
        self._cv.create_window(
            self.w // 2, self.h // 2, window=self._content,
            width=self.w - 4, height=self.h - 4)
        self._build_ui()
        self._refresh_history()
        self.window.update_idletasks()

    # ========== 设置 ==========

    def open_settings(self):
        dlg = tk.Toplevel(self.window)
        dlg.title("设置")
        dlg.configure(bg=T.BG2)
        dlg.transient(self.window)
        dlg.grab_set()
        dlg.resizable(False, False)

        w, h = 420, 280
        x = self.window.winfo_x() + (self.w - w) // 2
        y = self.window.winfo_y() + (self.h - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        frame = tk.Frame(dlg, bg=T.BG2)
        frame.pack(expand=True, fill=tk.BOTH, padx=18, pady=16)

        label_kw = {"bg": T.BG2, "fg": T.TXT1, "font": (T.FONT, 9)}

        # 保存路径
        tk.Label(frame, text="默认保存路径", bg=T.BG2, fg=T.TXT1,
                 font=(T.FONT, 10, "bold")).pack(anchor="w", pady=(0, 4))

        pf = tk.Frame(frame, bg=T.BG2)
        pf.pack(fill=tk.X, pady=(0, 14))
        path_var = tk.StringVar(value=self.settings.get("save_path", ""))

        def browse_path():
            p = filedialog.askdirectory(title="保存目录", initialdir=path_var.get())
            if p:
                path_var.set(p)

        tk.Entry(pf, textvariable=path_var, bg=T.BG3, fg=T.TXT0,
                 font=(T.FONT, 9), relief="flat", bd=6).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        StyledButton(pf, text="浏览", width=60, height=28,
                     command=browse_path, font_size=8).pack(side=tk.LEFT, padx=6)

        # 快捷键
        tk.Label(frame, text="截图快捷键", **label_kw).pack(anchor="w")
        hk_var = tk.StringVar(value=self.settings.get("hotkey", "ctrl+shift+s"))
        hk_entry = tk.Entry(frame, textvariable=hk_var, bg=T.BG3, fg=T.TXT0,
                            font=(T.FONT, 9), relief="flat", bd=6,
                            state="readonly" if not HAS_KEYBOARD else "normal")
        hk_entry.pack(fill=tk.X, pady=(2, 14))

        # 格式
        tk.Label(frame, text="默认文件格式", **label_kw).pack(anchor="w")
        ff = tk.Frame(frame, bg=T.BG2)
        ff.pack(fill=tk.X, pady=(2, 14))
        fmt_var = tk.StringVar(value=self.settings.get("file_format", "PNG"))
        for t, v in [("PNG", "PNG"), ("JPEG", "JPEG"), ("BMP", "BMP")]:
            tk.Radiobutton(ff, text=t, variable=fmt_var, value=v,
                           bg=T.BG2, fg=T.TXT1, selectcolor=T.BG3,
                           activebackground=T.BG2, activeforeground=T.TXT0,
                           font=(T.FONT, 9)).pack(side=tk.LEFT, padx=8)

        def save():
            self.settings["save_path"] = path_var.get()
            self.settings["hotkey"] = hk_var.get()
            self.settings["file_format"] = fmt_var.get()
            save_settings(self.settings)
            dlg.destroy()
            messagebox.showinfo("设置", "设置已保存")

        bf = tk.Frame(frame, bg=T.BG2)
        bf.pack(fill=tk.X, pady=(8, 0))
        StyledButton(bf, text="关闭", width=68, height=28,
                     command=dlg.destroy, font_size=8).pack(side=tk.RIGHT, padx=4)
        StyledButton(bf, text="保存设置", width=80, height=28,
                     command=save, accent=True, font_size=8).pack(side=tk.RIGHT)

    def on_exit(self):
        if messagebox.askyesno("退出", f"确定退出{APP_NAME}？"):
            self.running = False
            if HAS_KEYBOARD:
                try:
                    kb.unhook_all()
                except Exception:
                    pass
            self.window.destroy()

    def run(self):
        self.window.mainloop()


# ==================== 入口 ====================

def main():
    settings = load_settings()
    save_path = settings.get("save_path", os.path.expanduser("~/Desktop"))
    if not os.path.exists(save_path):
        try:
            os.makedirs(save_path, exist_ok=True)
        except Exception:
            settings["save_path"] = os.path.expanduser("~/Desktop")

    app = FloatingToolbar(settings)
    app.run()


if __name__ == "__main__":
    main()
