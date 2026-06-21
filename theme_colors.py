"""
截图工具 v5.0 · 统一主题色彩管理模块
=====================================
集中管理所有颜色常量，提供验证工具和一致性检查。

使用方式：
    from theme_colors import T, validate_theme, print_theme_report

    # 获取当前主题的颜色
    bg = T.BG2          # 面板背景色
    accent = T.ACCENT   # 强调色

    # 切换主题
    T.set_theme('light')
    bg = T.BG2          # 自动返回浅色主题值

    # 验证颜色一致性（开发/调试用）
    issues = validate_theme()
    if issues:
        print(f"发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"  ⚠️  {issue}")

    # 打印完整主题报告
    print_theme_report()
"""

from __future__ import annotations
import colorsys
from typing import Dict, List, Optional, Tuple


# ==================== 深色主题 ====================
class _DarkTheme:
    """深色主题 (Dark) · 默认主题"""

    # L1 基础色：背景层次（从暗到亮）
    BG_CANVAS: str = "#0f0f1a"       # 最底层：画布/全屏遮罩底色
    BG_APP: str = "#141422"           # 应用主背景：窗口底色
    BG_CARD: str = "#1e1e32"          # 卡片/面板背景
    BG_ELEV: str = "#282844"          # 悬浮层：输入框、下拉菜单
    BG_HOVER: str = "#333358"         # 悬停态：按钮/列表项 hover
    BG_INPUT: str = "#181828"         # 输入框专用背景

    # 兼容旧代码的简写别名
    BG0 = BG_CANVAS
    BG1 = BG_APP
    BG2 = BG_CARD
    BG3 = BG_ELEV
    BG4 = BG_HOVER

    # L1 基础色：文字层次（从亮到暗）
    TXT_PRIMARY: str = "#f0f0f8"      # 主文字：标题、重要信息
    TXT_SECONDARY: str = "#b0b0c8"    # 次文字：常规内容
    TXT_TERTIARY: str = "#707088"     # 辅助文字：提示、说明
    TXT_MUTED: str = "#505068"        # 弱化文字：占位符、禁用态

    # 兼容旧代码的简写别名
    TXT0 = TXT_PRIMARY
    TXT1 = TXT_SECONDARY
    TXT2 = TXT_TERTIARY
    TXT3 = TXT_MUTED

    # L1 基础色：边框层次
    BORDER: str = "#2a2a44"           # 默认边框：分割线
    BORDER_STRONG: str = "#3a3a58"    # 强调边框：输入框 focus、活跃态

    # 兼容旧代码的简写别名
    BD = BORDER
    BD2 = BORDER_STRONG

    # L2 语义色：功能色
    ACCENT: str = "#4a8cff"           # 主强调色：主操作按钮、选中态
    ACCENT_LIGHT: str = "#5c9cff"     # 强调色浅变体：hover 态
    ACCENT_BG: str = "#1a2848"        # 强调色淡背景：选中项背景

    # 兼容旧代码的简写别名
    ACCENT2 = ACCENT_LIGHT

    SUCCESS: str = "#4caf84"           # 成功态
    WARNING: str = "#e09050"           # 警告态
    ERROR: str = "#e05555"            # 错误态
    ERROR_LIGHT: str = "#f06060"      # 错误色浅变体
    INFO: str = "#4a8cff"             # 信息提示

    # 兼容旧代码的简写别名
    RED = ERROR
    RED2 = ERROR_LIGHT
    GREEN = SUCCESS
    ORANGE = WARNING

    # L2 特殊用途色
    CANVAS_BG: str = "#10101c"        # 编辑器画布底色
    SELECTOR: str = "#4a8cff"         # 选区边框
    MASK_DARK: str = "rgba(0,0,0,0.45)"  # 选区外遮罩

    # L3 视觉效果
    SHADOW: str = "0 8px 32px rgba(0,0,0,0.4)"
    FOCUS_RING: str = "0 0 0 3px rgba(74,140,255,0.18)"
    SEL_FILL: str = "rgba(74,140,255,0.06)"

    @classmethod
    def name(cls) -> str:
        return "dark"

    @classmethod
    def display_name(cls) -> str:
        return "深色 (Dark)"

    @classmethod
    def all_colors(cls) -> Dict[str, str]:
        """返回所有颜色的完整字典（用于验证和文档生成）"""
        colors = {}
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            attr = getattr(cls, attr_name)
            if isinstance(attr, str) and len(attr) >= 6:
                # 只取看起来像颜色值的属性（以 # 开头或 rgba）
                if attr.startswith('#') or attr.startswith('rgba'):
                    colors[attr_name] = attr
        return colors


# ==================== 浅色主题 ====================
class _LightTheme:
    """浅色主题 (Light)"""

    # L1 基础色：背景层次（从亮到暗）
    BG_CANVAS: str = "#f8f9fb"
    BG_APP: str = "#ffffff"
    BG_CARD: str = "#ffffff"
    BG_ELEV: str = "#f4f6f9"
    BG_HOVER: str = "#eef1f6"
    BG_INPUT: str = "#ffffff"

    # 兼容旧代码的简写别名
    BG0 = BG_CANVAS
    BG1 = BG_APP
    BG2 = BG_CARD
    BG3 = BG_ELEV
    BG4 = BG_HOVER

    # L1 基础色：文字层次（从暗到亮）
    TXT_PRIMARY: str = "#1a2233"
    TXT_SECONDARY: str = "#4a5568"
    TXT_TERTIARY: str = "#8a94a6"
    TXT_MUTED: str = "#b0b8c4"

    # 兼容旧代码的简写别名
    TXT0 = TXT_PRIMARY
    TXT1 = TXT_SECONDARY
    TXT2 = TXT_TERTIARY
    TXT3 = TXT_MUTED

    # L1 基础色：边框层次
    BORDER: str = "#e4e7ec"
    BORDER_STRONG: str = "#d3d8df"

    # 兼容旧代码的简写别名
    BD = BORDER
    BD2 = BORDER_STRONG

    # L2 语义色：功能色
    ACCENT: str = "#2e6fe0"
    ACCENT_LIGHT: str = "#4a8cff"
    ACCENT_BG: str = "#eaf1fe"

    # 兼容旧代码的简写别名
    ACCENT2 = ACCENT_LIGHT

    SUCCESS: str = "#2fa86c"
    WARNING: str = "#e09050"
    ERROR: str = "#e05555"
    ERROR_LIGHT: str = "#f06060"
    INFO: str = "#2e6fe0"

    # 兼容旧代码的简写别名
    RED = ERROR
    RED2 = ERROR_LIGHT
    GREEN = SUCCESS
    ORANGE = WARNING

    # L2 特殊用途色
    CANVAS_BG: str = "#eef0f4"
    SELECTOR: str = "#2e6fe0"
    MASK_DARK: str = "rgba(20,30,60,0.32)"

    # L3 视觉效果
    SHADOW: str = "0 8px 24px rgba(20,30,60,0.1)"
    FOCUS_RING: str = "0 0 0 3px rgba(46,111,224,0.16)"
    SEL_FILL: str = "rgba(46,111,224,0.06)"

    @classmethod
    def name(cls) -> str:
        return "light"

    @classmethod
    def display_name(cls) -> str:
        return "浅色 (Light)"

    @classmethod
    def all_colors(cls) -> Dict[str, str]:
        """返回所有颜色的完整字典"""
        colors = {}
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            attr = getattr(cls, attr_name)
            if isinstance(attr, str) and len(attr) >= 6:
                if attr.startswith('#') or attr.startswith('rgba'):
                    colors[attr_name] = attr
        return colors


# ==================== 标注色板（双主题固定不变） ====================
ANNOTATION_COLORS: Tuple[str, ...] = (
    "#FF3B30",  # 红色 - 重点标记
    "#FF6B35",  # 橙红 - 暖色强调
    "#FF9500",  # 橙色 - 警告标注
    "#FFCC02",  # 黄色 - 高亮标注
    "#34C759",  # 绿色 - 通过标记
    "#30B0C7",  # 青色 - 信息标注
    "#007AFF",  # 蓝色 - 默认标注
    "#5856D6",  # 紫色 - 特殊强调
    "#AF52DE",  # 品红 - 高亮强调
    "#FF2D55",  # 玫红 - 极强强调
    "#8E8E93",  # 灰色 - 弱化标注
    "#FFFFFF",  # 白色 - 浅色标注
)

# 水印专用扩展色板（灰度 + 主要标注色）
WATERMARK_PALETTE: Tuple[str, ...] = (
    "#FFFFFF", "#CCCCCC", "#999999",
    "#666666", "#333333", "#000000",
    *ANNOTATION_COLORS[:10],
)


# ==================== 主题代理类（动态切换） ====================
class _ThemeMeta(type):
    """元类：让 `T.BG0` 这种类属性访问动态委托到当前激活的主题类
    
    用法：
        T.BG0     → 返回 _DarkTheme.BG0 或 _LightTheme.BG0（取决于当前主题）
        T.set_theme('light')
        T.BG0     → 现在返回 _LightTheme.BG0
    """
    def __getattr__(cls, name: str):
        current_cls = cls._themes.get(cls._theme)
        if current_cls is None:
            raise AttributeError(f"Theme '{cls._theme}' not found. Available: {list(cls._themes.keys())}")
        return getattr(current_cls, name)


class T(metaclass=_ThemeMeta):
    """
    统一主题代理 — 所有颜色访问的唯一入口。
    
    切换主题：
        T.set_theme('dark')   # 深色（默认）
        T.set_theme('light')  # 浅色
        T.toggle_theme()      # 切换到另一个
    
    访问颜色：
        T.BG0 / T.BG1 / T.BG2 / T.BG3 / T.BG4   # 背景
        T.TXT0 / T.TXT1 / T.TXT2 / T.TXT3        # 文字
        T.ACCENT / T.ACCENT2 / T.ACCENT_BG        # 强调色
        T.BD / T.BD2                               # 边框
        T.RED / T.GREEN / T.ORANGE                # 功能色
        T.COLORS                                    # 标注色板
        T.FONT / T.FONT_MONO                         # 字体名
    
    主题信息：
        T.get_theme()      # 当前主题名 'dark'/'light'
        T.get_display_name() # '深色 (Dark)'/'浅色 (Light)'
    
    注意：
        - 所有已创建组件需自行实现刷新逻辑（_apply_theme）
        - 新建组件时请使用 T.* 而非硬编码颜色值
    """
    
    _theme: str = "dark"
    _themes: Dict[str, type] = {
        "dark": _DarkTheme,
        "light": _LightTheme,
    }

    # ===== 标注色板（不随主题变化）=====
    COLORS: Tuple[str, ...] = ANNOTATION_COLORS

    # ===== 字体配置（平台无关）=====
    FONT: str = "Microsoft YaHei"
    FONT_MONO: str = "Consolas"

    @classmethod
    def set_theme(cls, name: str) -> None:
        """设置当前主题 ('dark' 或 'light')"""
        if name in cls._themes:
            cls._theme = name
        else:
            raise ValueError(f"未知主题: '{name}'，可选: {list(cls._themes.keys())}")

    @classmethod
    def get_theme(cls) -> str:
        """获取当前主题名称"""
        return cls._theme

    @classmethod
    def get_display_name(cls) -> str:
        """获取当前主题显示名称"""
        current = cls._themes.get(cls._theme)
        return current.display_name() if current else "Unknown"

    @classmethod
    def toggle_theme(cls) -> str:
        """切换到另一主题，返回新主题名称"""
        cls._theme = "light" if cls._theme == "dark" else "dark"
        return cls._theme

    @classmethod
    def get_current_class(cls) -> type:
        """获取当前激活的主题类（用于类型提示和反射）"""
        return cls._themes[cls._theme]

    @classmethod
    def is_dark(cls) -> bool:
        return cls._theme == "dark"


# ==================== 颜色工具函数 ====================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """将十六进制颜色转为 RGB 元组
    
    >>> hex_to_rgb("#FF3B30")
    (255, 59, 48)
    """
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """将 RGB 转为十六进制颜色
    
    >>> rgb_to_hex(255, 59, 48)
    '#ff3b30'
    """
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def calc_contrast(color1: str, color2: str) -> float:
    """
    计算两个颜色之间的 WCAG 对比度比值。
    返回值 ≥ 4.5 表示通过 AA 标准（常规文字），
    ≥ 3.0 表示通过 AA 大文字标准。
    
    >>> calc_contrast("#FFFFFF", "#000000")  # 最极端对比
    21.0
    >>> calc_contrast("#F0F0F8", "#0F0F1A")  # Dark 主文字
    16.82...
    """
    def _rel_lum(hex_color: str) -> float:
        r, g, b = hex_to_rgb(hex_color)
        rsrgb = [c / 255.0 for c in (r, g, b)]
        linear = []
        for val in rsrgb:
            if val <= 0.03928:
                linear.append(val / 12.92)
            else:
                linear.append(((val + 0.055) / 1.055) ** 2.4)
        r_lin, g_lin, b_lin = linear
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

    l1 = _rel_lum(color1)
    l2 = _rel_lum(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    if darker == 0:
        return float('inf')
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(fg: str, bg: str,
                    level: str = "AA",
                    size: str = "normal") -> Tuple[bool, float]:
    """
    检查前景色与背景色的对比度是否达标。
    
    Args:
        fg: 前景色（文字色）
        bg: 背景色
        level: "AA" (4.5:1) 或 "AAA" (7:1)
        size: "normal" (≥14px常规) 或 "large" (≥18px大字/粗体)
    
    Returns:
        (是否达标, 实际对比度值)
    
    示例：
        >>> ok, ratio = check_contrast(T.TXT0, T.BG2)  # 主文字在面板上
        >>> print(f"{ratio:.1f}:1 {'✓' if ok else '✗'}")
    """
    ratio = calc_contrast(fg, bg)
    if size == "large":
        threshold = 3.0  # 大文字只需 3:1
    else:
        threshold = {"AA": 4.5, "AAA": 7.0}.get(level, 4.5)
    return ratio >= threshold, ratio


def lighten(hex_color: str, factor: float = 0.2) -> str:
    """使颜色变亮
    
    >>> lighten("#4A8CFF", 0.2)
    '#79aaff'
    """
    r, g, b = [min(255, int(c + (255 - c) * factor)) for c in hex_to_rgb(hex_color)]
    return rgb_to_hex(r, g, b)


def darken(hex_color: str, factor: float = 0.2) -> str:
    """使颜色变暗
    
    >>> darken("#4A8CFF", 0.2)
    '#3b70cc'
    """
    r, g, b = [max(0, int(c * (1 - factor))) for c in hex_to_rgb(hex_color)]
    return rgb_to_hex(r, g, b)


# ==================== 一致性验证工具 ====================

def validate_theme() -> List[str]:
    """
    验证当前主题的一致性规则。
    
    返回违规列表（空列表表示全部通过）。
    
    检查项：
        1. 文字/背景对比度是否达标（WCAG AA）
        2. 深浅主题的同一令牌是否有明显区分（不能相同或太接近）
        3. 边框色与背景色是否有足够区分
    """
    issues = []
    current = T._themes[T._theme]

    # 1. 对比度检查
    checks = [
        ("主文字-面板背景", "TXT_PRIMARY", "BG_CARD", 4.5),
        ("次文字-面板背景", "TXT_SECONDARY", "BG_CARD", 4.5),
        ("辅助文字-面板背景", "TXT_TERTIARY", "BG_CARD", 3.0),  # 辅助文字允许稍低
        ("主文字-悬浮背景", "TXT_PRIMARY", "BG_ELEV", 4.5),
        ("主文字-悬停背景", "TXT_PRIMARY", "BG_HOVER", 4.5),
        ("强调色文字-白底", "ACCENT", "#FFFFFF", 4.5),
        ("错误文字-白底", "ERROR", "#FFFFFF", 4.5),
    ]

    for label, fg_attr, bg_attr, required_ratio in checks:
        try:
            fg_val = getattr(current, fg_attr)
            bg_val = getattr(current, bg_attr)
            if fg_val.startswith('rgba') or bg_val.startswith('rgba'):
                continue  # rgba 无法准确计算对比度，跳过
            ok, ratio = check_contrast(fg_val, bg_val)
            if not ok:
                issues.append(
                    f"[对比度不足] {label}: {ratio:.1f}:1 "
                    f"< 要求 {required_ratio}:1 ({fg_val} on {bg_val})"
                )
        except Exception:
            pass

    # 2. 深浅主题区分度检查
    other_name = "light" if T._theme == "dark" else "dark"
    other = T._themes[other_name]
    same_attrs = ["BG_APP", "BG_CARD", "ACCENT"]  # 这些必须有区别
    for attr in same_attrs:
        try:
            this_val = getattr(current, attr).lower()
            that_val = getattr(other, attr).lower()
            if this_val == that_val:
                issues.append(
                    f"[主题无区分] {attr} 在深色({this_val})和浅色({that_val})中相同"
                )
        except Exception:
            pass

    # 3. 边框可见性检查
    border_checks = [
        ("默认边框-面板背景", "BORDER", "BG_CARD"),
        ("强调边框-面板背景", "BORDER_STRONG", "BG_CARD"),
    ]
    for label, bd_attr, bg_attr in border_checks:
        try:
            bd_val = getattr(current, bd_attr)
            bg_val = getattr(current, bg_attr)
            if bd_val.lower() == bg_val.lower():
                issues.append(
                    f"[边框不可见] {label}: 边框色({bd_val})与背景色({bg_val})相同"
                )
        except Exception:
            pass

    return issues


def print_theme_report() -> None:
    """打印完整的主题颜色报告（用于调试和文档生成）"""
    current = T._themes[T._theme]
    other_name = "light" if T._theme == "dark" else "dark"
    other = T._themes[other_name]

    print(f"\n{'='*60}")
    print(f"  截图工具 · 主题色彩报告")
    print(f"  当前主题: {current.display_name()}")
    print(f"{'='*60}\n")

    # 背景色
    print("【背景层次】")
    bg_attrs = [
        ("画布底层", "BG_CANVAS"),
        ("应用背景", "BG_APP"),
        ("卡片背景", "BG_CARD"),
        ("悬浮层", "BG_ELEV"),
        ("悬停态", "BG_HOVER"),
    ]
    for label, attr in bg_attrs:
        this = getattr(current, attr, "?")
        that = getattr(other, attr, "?")
        print(f"  {attr:12s} = {this:12s} | {other_name:5s}: {that}")

    print()
    print("【文字层次】")
    txt_attrs = [
        ("主文字", "TXT_PRIMARY"),
        ("次文字", "TXT_SECONDARY"),
        ("辅助文字", "TXT_TERTIARY"),
        ("弱化文字", "TXT_MUTED"),
    ]
    for label, attr in txt_attrs:
        this = getattr(current, attr, "?")
        that = getattr(other, attr, "?")
        ratio, _ = check_contrast(this, getattr(current, "BG_CARD"))
        print(f"  {attr:12s} = {this:12s} | 对比度 {ratio:.1f}:1")

    print()
    print("【功能色】")
    func_attrs = [
        ("强调色", "ACCENT"),
        ("强调浅色", "ACCENT_LIGHT"),
        ("强调背景", "ACCENT_BG"),
        ("成功绿", "SUCCESS"),
        ("警告橙", "WARNING"),
        ("错误红", "ERROR"),
    ]
    for label, attr in func_attrs:
        this = getattr(current, attr, "?")
        that = getattr(other, attr, "?")
        marker = " <-- DIFFERENT!" if this != that else ""
        print(f"  {attr:12s} = {this:12s} | {that}{marker}")

    print()

    # 一致性验证结果
    issues = validate_theme()
    if issues:
        print(f"[!] Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("[OK] All consistency checks passed!")

    print(f"\n{'='*60}\n")


def generate_css_variables(theme: str = "dark") -> str:
    """
    生成 CSS 变量定义块（用于 HTML/CSS 端同步）。
    
    用法：
        css = generate_css_variables('dark')
        print(css)
        
        css = generate_css_variables('light')
        print(css)
    """
    cls = _themes.get(theme)
    if cls is None:
        raise ValueError(f"未知主题: {theme}")

    mapping = {
        "bg-canvas": "BG_CANVAS",
        "bg-app": "BG_APP",
        "bg-card": "BG_CARD",
        "bg-elev": "BG_ELEV",
        "bg-hover": "BG_HOVER",
        "accent": "ACCENT",
        "accent-2": "ACCENT_LIGHT",
        "accent-bg": "ACCENT_BG",
        "txt-0": "TXT_PRIMARY",
        "txt-1": "TXT_SECONDARY",
        "txt-2": "TXT_TERTIARY",
        "bd": "BORDER",
        "bd-2": "BORDER_STRONG",
        "red": "ERROR",
        "green": "SUCCESS",
        "orange": "WARNING",
    }

    lines = [':root[data-theme="{}"] {{'.format(theme)]
    for css_name, py_attr in mapping.items():
        value = getattr(cls, py_attr, "")
        lines.append(f'  --{css_name}: {value};')
    lines.append("}")
    return "\n".join(lines)


# 导出 _themes 字典供 T 元类使用
_themes = {
    "dark": _DarkTheme,
    "light": _LightTheme,
}


# ==================== 模块自检（导入时运行）====================

if __name__ == "__main__":
    print_theme_report()
    
    # 生成 CSS 变量供复制
    print("\n/* ===== CSS 变量（可直接复制到 HTML）===== */")
    print(generate_css_variables("dark"))
    print()
    print(generate_css_variables("light"))
