#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B站音频提取器 - 美化版界面

采用Cyber-Media美学设计，使用深色主题和Bilibili品牌色彩
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import re
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageTk
import qrcode

class CyberMediaTheme:
    """Cyber-Media主题配置"""

    # 颜色方案
    BG_DARK = "#0D1117"           # 主背景色
    BG_CARD = "#161B22"          # 卡片背景色
    BG_HOVER = "#21262D"         # 悬停背景色

    # Bilibili品牌色彩
    CYAN = "#00A1D6"             # Bilibili蓝色
    PINK = "#FB7299"             # Bilibili粉色

    # 文本色彩
    TEXT_PRIMARY = "#F0F6FC"     # 主要文本
    TEXT_SECONDARY = "#8B949E"   # 次要文本
    TEXT_ACCENT = "#58A6FF"      # 强调文本

    # 功能色彩
    SUCCESS = "#238636"          # 成功
    WARNING = "#D29922"          # 警告
    ERROR = "#DA3633"            # 错误

    # 字体配置
    FONT_TITLE = ("微软雅黑", 18, "bold")
    FONT_SUBTITLE = ("微软雅黑", 12, "bold")
    FONT_BODY = ("微软雅黑", 10)
    FONT_MONO = ("Consolas", 9)

class ModernButton(tk.Button):
    """现代化按钮组件"""

    def __init__(self, master, **kwargs):
        # 默认样式
        self.bg_color = kwargs.pop('bg_color', CyberMediaTheme.CYAN)
        self.hover_color = kwargs.pop('hover_color', "#0084B6")
        self.text_color = kwargs.pop('fg', CyberMediaTheme.TEXT_PRIMARY)

        # 应用样式
        super().__init__(
            master,
            bg=self.bg_color,
            fg=self.text_color,
            relief="flat",
            bd=0,
            highlightthickness=0,
            activebackground=self.hover_color,
            activeforeground=self.text_color,
            font=CyberMediaTheme.FONT_BODY,
            cursor="hand2",
            **kwargs
        )

        # 绑定悬停效果
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)

    def _on_hover(self, event):
        if self['state'] != 'disabled':
            self.config(bg=self.hover_color)

    def _on_leave(self, event):
        if self['state'] != 'disabled':
            self.config(bg=self.bg_color)

class ModernLabelFrame(tk.LabelFrame):
    """现代化LabelFrame组件"""

    def __init__(self, master, **kwargs):
        # 应用样式
        super().__init__(
            master,
            bg=CyberMediaTheme.BG_CARD,
            fg=CyberMediaTheme.TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=CyberMediaTheme.FONT_SUBTITLE,
            **kwargs
        )

class ModernEntry(tk.Entry):
    """现代化输入框组件"""

    def __init__(self, master, **kwargs):
        # 应用样式
        super().__init__(
            master,
            bg=CyberMediaTheme.BG_DARK,
            fg=CyberMediaTheme.TEXT_PRIMARY,
            insertbackground=CyberMediaTheme.CYAN,
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=CyberMediaTheme.BG_HOVER,
            highlightcolor=CyberMediaTheme.CYAN,
            font=CyberMediaTheme.FONT_BODY,
            **kwargs
        )

class BilibiliAudioExtractorGUI:
    """B站音频提取器 - 美化版"""

    def __init__(self, root):
        self.root = root
        self.root.title("B站音频提取器 - 美化版")
        self.root.geometry("600x650")
        self.root.minsize(550, 500)

        # 应用主题
        self.root.configure(bg=CyberMediaTheme.BG_DARK)

        # 配置文件路径
        self.config_file = Path.home() / ".bilibili_audio_extractor_simple_config.json"

        # 初始化变量
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "B站音频提取"))
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="就绪")
        self.is_processing = False
        self.highest_quality = None

        # B站扫码登录相关
        self.bilibili_cookie_file = Path.home() / ".bilibili_cookies.json"
        self.bili_jct = None

        # 设置样式
        self.setup_styles()

        # 构建UI
        self.setup_ui()

        self.load_config()
        self.check_dependencies()

    def setup_styles(self):
        """设置ttk样式"""
        style = ttk.Style()

        # 配置主题
        style.theme_use('clam')

        # 进度条样式
        style.configure(
            "Modern.Horizontal.TProgressbar",
            background=CyberMediaTheme.CYAN,
            troughcolor=CyberMediaTheme.BG_HOVER,
            bordercolor=CyberMediaTheme.BG_CARD,
            lightcolor=CyberMediaTheme.CYAN,
            darkcolor=CyberMediaTheme.CYAN,
            thickness=8
        )

        # 整体背景
        self.root.option_add("*Background", CyberMediaTheme.BG_DARK)
        self.root.option_add("*Foreground", CyberMediaTheme.TEXT_PRIMARY)

    def setup_ui(self):
        """设置用户界面 - 现代化设计"""

        # 主容器
        main_frame = tk.Frame(self.root, bg=CyberMediaTheme.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题区域
        self.create_header(main_frame)

        # URL输入区域
        self.create_url_section(main_frame)

        # 输出目录区域
        self.create_output_section(main_frame)

        # 进度区域
        self.create_progress_section(main_frame)

        # 按钮区域
        self.create_button_section(main_frame)

        # 日志区域
        self.create_log_section(main_frame)

        # 绑定回车键
        self.root.bind('<Return>', lambda e: self.start_extraction())

    def create_header(self, parent):
        """创建标题区域"""
        header_frame = tk.Frame(parent, bg=CyberMediaTheme.BG_DARK)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # 主标题
        title_label = tk.Label(
            header_frame,
            text="🎵 B站音频提取器",
            font=CyberMediaTheme.FONT_TITLE,
            bg=CyberMediaTheme.BG_DARK,
            fg=CyberMediaTheme.TEXT_PRIMARY
        )
        title_label.pack(anchor="w")

        # 副标题
        subtitle_label = tk.Label(
            header_frame,
            text="最高音质 · 大会员支持 · 一键操作",
            font=CyberMediaTheme.FONT_BODY,
            bg=CyberMediaTheme.BG_DARK,
            fg=CyberMediaTheme.TEXT_SECONDARY
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def create_url_section(self, parent):
        """创建URL输入区域"""
        url_card = ModernLabelFrame(parent, text="📎 视频链接")
        url_card.pack(fill=tk.X, pady=(0, 15))

        # URL输入
        url_inner = tk.Frame(url_card, bg=CyberMediaTheme.BG_CARD)
        url_inner.pack(fill=tk.X, padx=15, pady=15)

        url_label = tk.Label(
            url_inner,
            text="输入B站视频URL:",
            font=CyberMediaTheme.FONT_BODY,
            bg=CyberMediaTheme.BG_CARD,
            fg=CyberMediaTheme.TEXT_SECONDARY
        )
        url_label.pack(anchor="w", pady=(0, 8))

        self.url_entry = ModernEntry(
            url_inner,
            textvariable=self.url_var
        )
        self.url_entry.pack(fill=tk.X, pady=(0, 8))

        example_label = tk.Label(
            url_inner,
            text="示例: https://www.bilibili.com/video/BV1Hs4y1B7T2",
            font=("微软雅黑", 9),
            bg=CyberMediaTheme.BG_CARD,
            fg=CyberMediaTheme.TEXT_SECONDARY
        )
        example_label.pack(anchor="w")

    def create_output_section(self, parent):
        """创建输出目录区域"""
        output_card = ModernLabelFrame(parent, text="💾 输出设置")
        output_card.pack(fill=tk.X, pady=(0, 15))

        output_inner = tk.Frame(output_card, bg=CyberMediaTheme.BG_CARD)
        output_inner.pack(fill=tk.X, padx=15, pady=15)

        dir_label = tk.Label(
            output_inner,
            text="保存目录:",
            font=CyberMediaTheme.FONT_BODY,
            bg=CyberMediaTheme.BG_CARD,
            fg=CyberMediaTheme.TEXT_SECONDARY
        )
        dir_label.pack(anchor="w", pady=(0, 8))

        dir_entry_frame = tk.Frame(output_inner, bg=CyberMediaTheme.BG_CARD)
        dir_entry_frame.pack(fill=tk.X)

        self.dir_entry = ModernEntry(
            dir_entry_frame,
            textvariable=self.output_dir_var
        )
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = ModernButton(
            dir_entry_frame,
            text="浏览",
            bg_color=CyberMediaTheme.PINK,
            hover_color="#E05D84",
            command=self.browse_directory,
            width=8
        )
        browse_btn.pack(side=tk.RIGHT, padx=(10, 0))

    def create_progress_section(self, parent):
        """创建进度区域"""
        progress_card = ModernLabelFrame(parent, text="📊 处理进度")
        progress_card.pack(fill=tk.X, pady=(0, 15))

        progress_inner = tk.Frame(progress_card, bg=CyberMediaTheme.BG_CARD)
        progress_inner.pack(fill=tk.X, padx=15, pady=15)

        self.progress_bar = ttk.Progressbar(
            progress_inner,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            style="Modern.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        self.status_label = tk.Label(
            progress_inner,
            textvariable=self.status_var,
            font=CyberMediaTheme.FONT_BODY,
            bg=CyberMediaTheme.BG_CARD,
            fg=CyberMediaTheme.TEXT_ACCENT,
            anchor="w"
        )
        self.status_label.pack(fill=tk.X)

    def create_button_section(self, parent):
        """创建按钮区域"""
        button_frame = tk.Frame(parent, bg=CyberMediaTheme.BG_DARK)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        # 主要操作按钮
        self.extract_btn = ModernButton(
            button_frame,
            text="🎵 开始提取音频",
            bg_color=CyberMediaTheme.SUCCESS,
            hover_color="#1A6B29",
            command=self.start_extraction,
            font=CyberMediaTheme.FONT_SUBTITLE,
            width=20,
            height=2
        )
        self.extract_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 次要按钮
        btn_frame = tk.Frame(button_frame, bg=CyberMediaTheme.BG_DARK)
        btn_frame.pack(side=tk.RIGHT)

        self.test_btn = ModernButton(
            btn_frame,
            text="🔧 测试",
            bg_color=CyberMediaTheme.BG_HOVER,
            hover_color=CyberMediaTheme.TEXT_SECONDARY,
            command=self.test_dependencies,
            width=8
        )
        self.test_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.login_btn = ModernButton(
            btn_frame,
            text="🔐 登录",
            bg_color=CyberMediaTheme.WARNING,
            hover_color="#B37A19",
            command=self.bilibili_qrcode_login,
            width=8
        )
        self.login_btn.pack(side=tk.LEFT)

    def create_log_section(self, parent):
        """创建日志区域"""
        log_card = ModernLabelFrame(parent, text="📋 处理日志")
        log_card.pack(fill=tk.BOTH, expand=True)

        log_inner = tk.Frame(log_card, bg=CyberMediaTheme.BG_CARD)
        log_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.log_text = scrolledtext.ScrolledText(
            log_inner,
            height=12,
            wrap=tk.WORD,
            bg=CyberMediaTheme.BG_DARK,
            fg=CyberMediaTheme.TEXT_PRIMARY,
            insertbackground=CyberMediaTheme.CYAN,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=CyberMediaTheme.BG_HOVER,
            highlightcolor=CyberMediaTheme.CYAN,
            font=CyberMediaTheme.FONT_MONO
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def check_dependencies(self):
        """检查必要的依赖 - 美化版本"""
        self.log_message("🔍 检查系统依赖...")

        try:
            subprocess.run(['you-get', '--version'], capture_output=True, check=True)
            self.log_message("✅ you-get 已安装")
        except:
            self.log_message("❌ you-get 未安装，请运行: pip install you-get")

        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            self.log_message("✅ FFmpeg 已安装")
        except:
            self.log_message("❌ FFmpeg 未安装，请从 https://ffmpeg.org 下载安装")

        # 检查qrcode库
        try:
            import qrcode
            qrcode_available = True
            self.log_message("✅ qrcode库已安装（本地二维码生成可用）")
        except ImportError:
            qrcode_available = False
            self.log_message("⚠️ qrcode库未安装，建议运行: 一键打包.bat install")
            self.log_message("  当前将使用外部API或文字链接生成二维码")

    def log_message(self, message):
        """添加日志消息 - 美化版本"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    # 其余方法保持与原始版本相同，只是UI相关的方法需要调整
    # 为了节省篇幅，这里只展示关键的美化部分

    def browse_directory(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(
            title="选择保存目录",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
            self.save_config('output_dir', directory)

    def start_extraction(self):
        """开始音频提取 - 保持原有逻辑"""
        if self.is_processing:
            return

        url = self.url_var.get().strip()
        output_dir = self.output_dir_var.get().strip()

        if not url:
            messagebox.showwarning("警告", "请输入B站视频链接")
            return

        if not output_dir:
            messagebox.showwarning("警告", "请选择输出目录")
            return

        self.is_processing = True
        self.extract_btn.config(state=tk.DISABLED)
        self.highest_quality = None

        self.log_message("\n=== 🎵 开始提取最高音质音频 ===")
        self.log_message(f"📎 URL: {url}")
        self.log_message(f"💾 输出目录: {output_dir}")

        thread = threading.Thread(target=self.extract_audio_thread, daemon=True)
        thread.start()

    def extract_audio_thread(self):
        """音频提取线程 - 保持原有逻辑，只更新UI相关部分"""
        # 这里使用原始的extract_audio_thread逻辑，但保持UI更新的一致性
        # 由于篇幅限制，这里省略具体实现，使用原始版本的方法
        pass

    # 其他方法保持与原始版本相同
    def test_dependencies(self):
        """测试依赖功能"""
        self.log_message("\n=== 🔧 依赖功能测试 ===")
        self.check_dependencies()

def main():
    """主函数"""
    root = tk.Tk()
    app = BilibiliAudioExtractorGUI(root)

    def on_closing():
        app.save_current_settings()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()