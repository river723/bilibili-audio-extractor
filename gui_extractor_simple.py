#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

B站音频提取器 - 精简版

只下载所输入URL的最高音质音频（支持扫码登录大会员）

依赖: yt-dlp + ffmpeg

更新: 已从 you-get 迁移到 yt-dlp，支持更高质量的音频提取
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


# 玻璃态主题样式系统
class GlassTheme:
    """高端大气玻璃态主题"""

    # 色彩系统 (使用十六进制格式，因为Tkinter不支持rgba字符串)
    COLORS = {
        'bg_primary': '#f8f9fa',      # 主背景
        'bg_secondary': '#eef2f7',    # 次背景
        'card_bg': '#ffffff',         # 卡片背景 (纯白，通过Frame透明度模拟玻璃效果)
        'primary': '#ff6699',         # 主色 - B站粉
        'primary_light': '#ff8fab',   # 浅色主色
        'primary_dark': '#ff3388',    # 深色主色
        'accent_blue': '#4a90e2',     # 科技蓝
        'accent_green': '#52c41a',    # 成功绿
        'accent_red': '#ff4d4f',      # 错误红
        'text_primary': '#1a1a1a',    # 主文本
        'text_secondary': '#595959',  # 次文本
        'text_hint': '#8c8c8c',       # 提示文本
        'border': '#e0e0e0',          # 边框 (浅灰色)
        'shadow': '#e8e8e8',          # 阴影 (浅灰色)
        'glass_highlight': '#ffffff',  # 玻璃高光
    }

    # 字体系统
    FONTS = {
        'title': ('微软雅黑', 18, 'bold'),
        'subtitle': ('微软雅黑', 12, 'normal'),
        'heading': ('微软雅黑', 11, 'bold'),
        'body': ('微软雅黑', 9, 'normal'),
        'caption': ('微软雅黑', 8, 'normal'),
        'code': ('Consolas', 8, 'normal'),
    }

    # 阴影系统
    SHADOWS = {
        'card': '0 4px 20px rgba(0, 0, 0, 0.08)',
        'button': '0 2px 8px rgba(0, 0, 0, 0.12)',
        'button_hover': '0 4px 16px rgba(0, 0, 0, 0.16)',
        'input': '0 2px 6px rgba(0, 0, 0, 0.06)',
    }

    # 圆角半径
    RADIUS = {
        'card': 16,
        'button': 8,
        'input': 6,
        'progress': 4,
    }

    @classmethod
    def get_color(cls, key):
        """获取颜色值"""
        return cls.COLORS.get(key, '#000000')

    @classmethod
    def get_font(cls, key):
        """获取字体配置"""
        return cls.FONTS.get(key, ('Arial', 10))

    @classmethod
    def get_shadow(cls, key):
        """获取阴影配置"""
        return cls.SHADOWS.get(key, '0 0 0 rgba(0, 0, 0, 0)')

    @classmethod
    def get_radius(cls, key):
        """获取圆角半径"""
        return cls.RADIUS.get(key, 0)


def create_glass_card(parent, **kwargs):
    """创建玻璃态卡片容器"""
    card = tk.Frame(
        parent,
        bg=GlassTheme.get_color('card_bg'),
        highlightbackground=GlassTheme.get_color('border'),
        highlightthickness=1,
        bd=0,
        **kwargs
    )

    # 添加阴影效果（通过place实现）
    def add_shadow():
        try:
            x = card.winfo_x()
            y = card.winfo_y()
            width = card.winfo_width()
            height = card.winfo_height()

            if width > 0 and height > 0:
                # 创建阴影画布
                shadow = tk.Canvas(
                    parent,
                    width=width + 20,
                    height=height + 20,
                    bg=GlassTheme.get_color('bg_primary'),
                    highlightthickness=0,
                    bd=0
                )
                shadow.place(x=x - 10, y=y - 10)

                # 绘制渐变阴影
                shadow_color = GlassTheme.get_color('shadow')
                for i in range(10):
                    alpha = int(255 * (1 - i / 10) * 0.3)
                    color = f'#{alpha:02x}{alpha:02x}{alpha:02x}'
                    shadow.create_oval(
                        10 - i, 10 - i, width + 10 + i, height + 10 + i,
                        fill=color, outline=color
                    )

                # 将卡片移到最上层
                card.lift()
        except:
            pass

    card.bind('<Configure>', lambda e: add_shadow())
    return card



class BilibiliAudioExtractorGUI:

    def __init__(self, root):

        self.root = root

        self.root.title("B站音频提取器")

        self.root.geometry("600x720")

        self.root.minsize(500, 500)

        # 设置窗口背景
        self.root.configure(bg=GlassTheme.get_color('bg_primary'))

        # 添加窗口动画效果
        self.root.attributes('-alpha', 0.0)  # 初始透明
        self._fade_in_animation()


        # 配置文件路径

        self.config_file = Path.home() / ".bilibili_audio_extractor_simple_config.json"


        # 初始化变量

        self.url_var = tk.StringVar()

        self.output_dir_var = tk.StringVar(value=str(Path.home() / "B站音频提取"))

        self.progress_var = tk.DoubleVar()

        self.status_var = tk.StringVar(value="就绪")

        self.is_processing = False


        # 最高音质标识

        self.highest_quality = None


        # B站扫码登录相关

        self.bilibili_cookie_file = Path.home() / ".bilibili_cookies.json"

        self.bili_jct = None


        self.setup_ui()

        self.load_config()

        self.check_dependencies()


    def _fade_in_animation(self):
        """窗口淡入动画"""
        current_alpha = self.root.attributes('-alpha')
        if current_alpha < 1.0:
            new_alpha = min(current_alpha + 0.1, 1.0)
            self.root.attributes('-alpha', new_alpha)
            self.root.after(50, self._fade_in_animation)

    def _create_glass_card(self, parent, **kwargs):
        """创建玻璃态卡片，返回(外容器, 内容容器)"""
        # 创建外容器用于阴影效果
        outer_frame = tk.Frame(parent, bg=GlassTheme.get_color('bg_primary'))

        # 创建卡片主体
        card = tk.Frame(
            outer_frame,
            bg=GlassTheme.get_color('card_bg'),
            highlightbackground='#e0e0e0',
            highlightthickness=1,
            bd=0,
            relief='flat',
            **kwargs
        )

        # 使用pack布局
        card.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        return outer_frame, card

    def _on_button_hover(self, button, hovering):
        """按钮悬停效果"""
        if hovering:
            button.configure(bg=GlassTheme.get_color('primary_light'))
        else:
            button.configure(bg=GlassTheme.get_color('accent_blue'))

    def _animate_button_press(self, button, pressing):
        """按钮按压缩放动画"""
        if pressing:
            button.configure(relief='sunken')
        else:
            button.configure(relief='flat')

    def setup_ui(self):

        """设置用户界面"""

        # 主容器
        main_container = tk.Frame(
            self.root,
            bg=GlassTheme.get_color('bg_primary')
        )
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题区域容器
        title_container = tk.Frame(
            main_container,
            bg=GlassTheme.get_color('bg_primary')
        )
        title_container.pack(fill=tk.X, pady=(0, 10))

        # 主标题 - 居左下
        title_label = tk.Label(
            title_container,
            text="B站音频提取器",
            font=GlassTheme.get_font('title'),
            fg=GlassTheme.get_color('text_primary'),
            bg=GlassTheme.get_color('bg_primary')
        )
        title_label.pack(side=tk.LEFT, anchor='s')

        # 副标题 - 居右下
        subtitle_label = tk.Label(
            title_container,
            text="最高音质提取",
            font=GlassTheme.get_font('caption'),
            fg=GlassTheme.get_color('text_hint'),
            bg=GlassTheme.get_color('bg_primary')
        )
        subtitle_label.pack(side=tk.RIGHT, anchor='s')

        # URL输入区域 - 玻璃态卡片
        url_card_outer, url_card = self._create_glass_card(main_container)
        url_card_outer.pack(fill=tk.X, pady=(0, 20))
        url_card.pack_propagate(True)  # 自动调整大小
       

        url_frame = tk.Frame(url_card, bg=GlassTheme.get_color('card_bg'))
        url_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(url_frame, text="视频URL:", font=GlassTheme.get_font('body'),
                fg=GlassTheme.get_color('text_primary'), bg=GlassTheme.get_color('card_bg'),
                anchor="w").pack(fill=tk.X, pady=(0, 8))

        url_entry = tk.Entry(url_frame, textvariable=self.url_var, font=GlassTheme.get_font('body'),
                           bg='white', fg=GlassTheme.get_color('text_primary'),
                           relief='flat', bd=1, highlightbackground=GlassTheme.get_color('border'),
                           highlightthickness=1)
        url_entry.pack(fill=tk.X, pady=(0, 8))

        example_url = "https://www.bilibili.com/video/BV1Hs4y1B7T2"
        tk.Label(url_frame, text=f"示例: {example_url}", font=GlassTheme.get_font('caption'),
                fg=GlassTheme.get_color('text_hint'), bg=GlassTheme.get_color('card_bg'),
                anchor="w").pack(fill=tk.X)


        # 输出目录选择 - 玻璃态卡片
        dir_card_outer, dir_card = self._create_glass_card(main_container)
        dir_card_outer.pack(fill=tk.X, pady=(0, 20))
        dir_card.pack_propagate(True)

        dir_frame = tk.Frame(dir_card, bg=GlassTheme.get_color('card_bg'))
        dir_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(dir_frame, text="保存目录:", font=GlassTheme.get_font('body'),
                fg=GlassTheme.get_color('text_primary'), bg=GlassTheme.get_color('card_bg'),
                anchor="w").pack(fill=tk.X, pady=(0, 8))

        dir_entry_frame = tk.Frame(dir_frame, bg=GlassTheme.get_color('card_bg'))
        dir_entry_frame.pack(fill=tk.X, pady=(0, 8))

        dir_entry = tk.Entry(dir_entry_frame, textvariable=self.output_dir_var,
                           font=GlassTheme.get_font('body'), bg='white',
                           fg=GlassTheme.get_color('text_primary'), relief='flat',
                           bd=1, highlightbackground=GlassTheme.get_color('border'),
                           highlightthickness=1)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = tk.Button(dir_entry_frame, text="浏览",
                             command=self.browse_directory, width=10,
                             font=GlassTheme.get_font('body'),
                             bg=GlassTheme.get_color('accent_blue'),
                             fg='white', relief='flat', bd=0,
                             activebackground=GlassTheme.get_color('primary'),
                             activeforeground='white',
                             cursor='hand2')
        browse_btn.pack(side=tk.RIGHT)

        # 添加按钮悬停效果
        browse_btn.bind('<Enter>', lambda e: self._on_button_hover(browse_btn, True))
        browse_btn.bind('<Leave>', lambda e: self._on_button_hover(browse_btn, False))


        # 按钮区域 - 玻璃态卡片
        button_card_outer, button_card = self._create_glass_card(main_container)
        button_card_outer.pack(fill=tk.X, pady=(0, 20))
        button_card.pack_propagate(True)

        button_frame = tk.Frame(button_card, bg=GlassTheme.get_color('card_bg'))
        button_frame.pack(fill=tk.X, padx=20, pady=15)

        # 按钮样式函数
        def create_glass_button(parent, text, command, color_key, width=12):
            btn = tk.Button(parent, text=text, command=command,
                           font=GlassTheme.get_font('body'),
                           bg=GlassTheme.get_color(color_key),
                           fg='white', relief='flat', bd=0,
                           activebackground=GlassTheme.get_color('primary_dark'),
                           activeforeground='white',
                           width=width, height=2,
                           cursor='hand2')
            btn.bind('<Enter>', lambda e: self._on_button_hover(btn, True))
            btn.bind('<Leave>', lambda e: self._on_button_hover(btn, False))
            btn.bind('<Button-1>', lambda e: self._animate_button_press(btn, True))
            btn.bind('<ButtonRelease-1>', lambda e: self._animate_button_press(btn, False))
            return btn

        self.extract_btn = create_glass_button(button_frame, "开始提取",
                                              self.start_extraction, 'primary', 12)
        self.extract_btn.pack(side=tk.LEFT, padx=(0, 12))

        self.test_btn = create_glass_button(button_frame, "测试依赖",
                                           self.test_dependencies, 'accent_blue', 12)
        self.test_btn.pack(side=tk.LEFT, padx=(0, 12))

        # B站登录状态按钮
        self.login_btn = create_glass_button(button_frame, "B站登录",
                                            self.bilibili_qrcode_login, 'accent_green', 12)
        self.login_btn.pack(side=tk.LEFT)


        # 进度和日志合并区域 - 玻璃态卡片
        log_card_outer, log_card = self._create_glass_card(main_container)
        log_card_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        log_card.pack_propagate(False)

        # 进度条区域（在按钮下方）
        progress_frame = tk.Frame(log_card, bg=GlassTheme.get_color('card_bg'))
        progress_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        tk.Label(progress_frame, text="处理进度:", font=GlassTheme.get_font('body'),
                fg=GlassTheme.get_color('text_primary'), bg=GlassTheme.get_color('card_bg'),
                anchor="w").pack(fill=tk.X, pady=(0, 8))

        # 进度条容器
        progress_container = tk.Frame(progress_frame, bg=GlassTheme.get_color('card_bg'))
        progress_container.pack(fill=tk.X, pady=(0, 8))

        self.progress_bar = ttk.Progressbar(
            progress_container,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)

        # 美化进度条样式
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Thin.Horizontal.TProgressbar',
                       background=GlassTheme.get_color('primary'),
                       troughcolor='white',
                       borderwidth=0,
                       thickness=1,
                       relief='flat')
        style.configure('ThinPulse.Horizontal.TProgressbar',
                       background=GlassTheme.get_color('primary_light'),
                       troughcolor='white',
                       borderwidth=0,
                       thickness=2,
                       relief='flat')
        self.progress_bar.configure(style='Thin.Horizontal.TProgressbar')

        # 添加进度百分比标签
        self.progress_label = tk.Label(progress_container, text="0%",
                                     font=GlassTheme.get_font('caption'),
                                     fg=GlassTheme.get_color('primary'),
                                     bg=GlassTheme.get_color('card_bg'),
                                     width=6)
        self.progress_label.pack(side=tk.RIGHT, padx=(10, 0))

        # 日志区域
        log_frame = tk.Frame(log_card, bg=GlassTheme.get_color('card_bg'))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # tk.Label(log_frame, text="处理日志:", font=GlassTheme.get_font('body'),
        #         fg=GlassTheme.get_color('text_primary'), bg=GlassTheme.get_color('card_bg'),
        #         anchor="w").pack(fill=tk.X, pady=(0, 8))

        # 日志文本区域容器
        log_container = tk.Frame(log_frame, bg=GlassTheme.get_color('card_bg'))
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=10,
            wrap=tk.WORD,
            font=GlassTheme.get_font('code'),
            bg='#f8f9fa',
            fg=GlassTheme.get_color('text_primary'),
            relief='flat',
            bd=1,
            highlightbackground=GlassTheme.get_color('border'),
            highlightthickness=1
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # 滚动条美化需要特殊处理，暂时注释掉
        # log_scrollbar = self.log_text.master.nametowidget(self.log_text.cget('yscrollcommand').split()[0])
        # log_scrollbar.configure(bg=GlassTheme.get_color('card_bg'),
        #                        troughcolor=GlassTheme.get_color('card_bg'),
        #                        relief='flat')

        # 绑定回车键
        self.root.bind('<Return>', lambda event: self.start_extraction())


    def check_dependencies(self):

        """检查必要的依赖"""

        self.log_message("检查系统依赖...")


        try:

            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)

            self.log_message("✓ yt-dlp 已安装")

        except:

            self.log_message("✗ yt-dlp 未安装，请运行: pip install yt-dlp")


        try:

            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)

            self.log_message("✓ FFmpeg 已安装")

        except:

            self.log_message("✗ FFmpeg 未安装，请从 https://ffmpeg.org 下载安装")


        # 检查qrcode库

        try:

            import qrcode

            qrcode_available = True

            self.log_message("✓ qrcode库已安装（本地二维码生成可用）")

        except ImportError:

            qrcode_available = False

            self.log_message("⚠ qrcode库未安装，建议运行: 一键打包.bat install")

            self.log_message("  当前将使用外部API或文字链接生成二维码")


    def show_bilibili_login_menu(self):
        """显示B站登录菜单"""
        menu = tk.Menu(self.root, tearoff=0)
        if self.bilibili_cookie_file.exists():
            menu.add_command(label="✓ 已登录B站大会员", state='disabled')
            menu.add_command(label="退出登录", command=self.bilibili_logout)
            menu.add_separator()
            menu.add_command(label="扫码登录B站", command=self.bilibili_qrcode_login)
        else:
            menu.add_command(label="扫码登录B站", command=self.bilibili_qrcode_login)

        # 获取按钮位置并显示菜单
        try:
            x = self.login_btn.winfo_rootx()
            y = self.login_btn.winfo_rooty() + self.login_btn.winfo_height()
            menu.tk_popup(x, y)
        except Exception:
            # 如果获取位置失败，使用默认位置
            menu.tk_popup(100, 100)


    def _copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()  # 确保剪贴板更新

            # 显示复制成功的提示
            if hasattr(self, '_qrcode_copy_btn'):
                original_text = self._qrcode_copy_btn.cget('text')
                self._qrcode_copy_btn.config(text='已复制!')

                # 2秒后恢复按钮文本
                def restore_button():
                    import time
                    time.sleep(2)
                    self._qrcode_copy_btn.config(text=original_text)

                import threading
                threading.Thread(target=restore_button, daemon=True).start()

        except Exception as e:
            print(f"复制到剪贴板失败: {e}")


    def bilibili_qrcode_login(self):

        # 如果已经登录，显示退出登录选项
        if self.bilibili_cookie_file.exists():
            result = messagebox.askyesno("B站登录状态", "您已经登录了B站大会员\n是否要退出当前登录？")
            if result:
                self.bilibili_logout()
            return

        # 否则显示二维码登录窗口
        login_window = tk.Toplevel(self.root)

        login_window.title("B站扫码登录")

        login_window.geometry("350x450")

        login_window.resizable(False, False)

        login_window.transient(self.root)  # 设置为root的临时窗口
        login_window.grab_set()  # 模态窗口


        # 窗口居中

        login_window.update_idletasks()

        x = (login_window.winfo_screenwidth() - 350) // 2

        y = (login_window.winfo_screenheight() - 450) // 2

        login_window.geometry(f"350x450+{x}+{y}")


        tk.Label(login_window, text="使用B站APP扫码登录", font=('微软雅黑', 12, 'bold')).pack(pady=20)


        # 二维码显示区域

        qrcode_frame = tk.Frame(login_window, bg='white', relief=tk.RIDGE, bd=2)

        qrcode_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)


        qrcode_label = tk.Label(qrcode_frame, text="获取二维码中...", bg='white', font=('Arial', 9))

        qrcode_label.pack(pady=20, padx=20, anchor='center', fill='both', expand=True)


        status_label = tk.Label(login_window, text="打开B站APP → 扫一扫 → 摄像头", fg='gray', font=('Arial', 8))

        status_label.pack(pady=5)


        # 进度条

        progress = ttk.Progressbar(login_window, mode='indeterminate', length=200)

        progress.pack(pady=10)

        progress.start()


        # 取消按钮

        cancel_frame = tk.Frame(login_window)

        cancel_frame.pack(pady=15)


        cancel_btn = tk.Button(cancel_frame, text="取消", command=lambda: login_window.destroy(), width=10)

        cancel_btn.pack()


        # 在后台线程中获取二维码

        def get_qrcode():

            try:

                # 获取二维码

                auth_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"

                req = urllib.request.Request(auth_url, headers={

                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

                })

                # 增加重试机制
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        with urllib.request.urlopen(req, timeout=15) as response:
                            data = json.loads(response.read().decode('utf-8'))
                        break
                    except Exception as e:
                        if retry == max_retries - 1:
                            raise e
                        time.sleep(1)  # 等待1秒后重试


                if data.get('code') != 0:

                    raise Exception(data.get('message', '获取二维码失败'))


                qrcode_data = data['data']['url']

                qrcode_key = data['data']['qrcode_key']


                # 先生成二维码文字链接作为备选显示
                # 创建可选择的文本，方便用户复制
                qrcode_text = f"请使用B站APP扫码登录\n\n二维码链接:\n{qrcode_data}"
                qrcode_label.config(text=qrcode_text, justify='center')

                # 添加一个可复制的文本框作为备选
                if not hasattr(self, '_qrcode_text_widget'):
                    # 创建可复制的文本显示区域
                    from tkinter import scrolledtext

                    # 在二维码区域添加一个隐藏的文本框
                    text_frame = tk.Frame(login_window)
                    text_frame.pack(pady=5, padx=20, fill=tk.X)

                    # 添加说明标签
                    tk.Label(text_frame, text="如二维码无法显示，可复制下方链接到浏览器:",
                            font=('Arial', 8), fg='gray').pack(anchor='w')

                    # 创建可选择的文本框
                    link_text = scrolledtext.ScrolledText(text_frame, height=2, width=40,
                                                        font=('Consolas', 8), wrap=tk.WORD)
                    link_text.pack(fill=tk.X, pady=(0, 5))
                    link_text.insert(tk.END, qrcode_data)
                    link_text.config(state='normal')  # 允许选择和复制

                    # 添加复制按钮
                    copy_btn = tk.Button(text_frame, text="复制链接",
                                       command=lambda: self._copy_to_clipboard(qrcode_data),
                                       font=('Arial', 8), width=8)
                    copy_btn.pack(anchor='e', pady=(0, 5))

                    # 保存引用
                    self._qrcode_text_widget = link_text
                    self._qrcode_copy_btn = copy_btn
                    self._qrcode_text_frame = text_frame

                # 尝试下载二维码图片（带重试）
                def load_qrcode_image():
                    try:
                        # 优先使用本地qrcode库生成
                        if qrcode is not None:
                            try:
                                # 使用本地qrcode库生成二维码
                                qr = qrcode.QRCode(
                                    version=None,  # 自动选择版本
                                    error_correction=qrcode.constants.ERROR_CORRECT_M,  # 中等容错
                                    box_size=15,   # 增大像素大小
                                    border=8,      # 增大边距确保静区
                                )
                                qr.add_data(qrcode_data)
                                qr.make(fit=True)

                                # 生成二维码图片
                                qr_image = qr.make_image(fill_color="black", back_color="white")

                                # 调整二维码大小确保清晰显示
                                qr_image = qr_image.resize((300, 300), Image.LANCZOS)

                                # 转换为PhotoImage
                                photo = ImageTk.PhotoImage(qr_image)

                                # 显示二维码图片，隐藏文字链接
                                qrcode_label.config(image=photo, text="")
                                qrcode_label.image = photo  # 保持引用避免被垃圾回收

                                # 隐藏文本链接区域
                                if hasattr(self, '_qrcode_text_frame'):
                                    self._qrcode_text_frame.pack_forget()

                                print("✓ 使用本地qrcode库生成二维码成功")
                                return

                            except Exception as local_error:
                                print(f"本地qrcode生成失败，尝试外部API: {local_error}")

                        # 如果本地qrcode不可用或失败，尝试外部API
                        qrcode_url = f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&data={urllib.parse.quote(qrcode_data)}"
                        img_req = urllib.request.Request(qrcode_url, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        })

                        # 二维码图片下载也加重试
                        for img_retry in range(2):
                            try:
                                with urllib.request.urlopen(img_req, timeout=10) as response:
                                    qrcode_image_data = response.read()
                                break
                            except Exception as img_e:
                                if img_retry == 1:
                                    raise img_e
                                time.sleep(0.5)

                        # 使用PIL处理图片
                        image = Image.open(BytesIO(qrcode_image_data))
                        photo = ImageTk.PhotoImage(image)

                        # 显示二维码图片，隐藏文字链接
                        qrcode_label.config(image=photo, text="")
                        qrcode_label.image = photo  # 保持引用避免被垃圾回收

                        # 隐藏文本链接区域
                        if hasattr(self, '_qrcode_text_frame'):
                            self._qrcode_text_frame.pack_forget()

                        print("✓ 使用外部API生成二维码成功")

                    except Exception as img_error:
                        # 如果所有方法都失败，显示文字和链接
                        print(f"二维码图片生成失败，使用文字显示: {img_error}")
                        qrcode_label.config(text=qrcode_text, justify='center')
                        # 确保文本区域可见
                        if hasattr(self, '_qrcode_text_frame'):
                            self._qrcode_text_frame.pack(pady=5, padx=20, fill='x')

                # 延迟加载图片，避免阻塞主线程
                def delayed_image_load():
                    time.sleep(1)  # 给用户看到文字提示的时间
                    load_qrcode_image()

                threading.Thread(target=delayed_image_load, daemon=True).start()


                # 检查登录状态

                self.check_login_status(qrcode_key, login_window, qrcode_label, progress, status_label)


            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    error_msg = "网络连接超时，请检查网络连接后重试"
                elif "connection" in error_msg.lower():
                    error_msg = "网络连接失败，请检查网络设置"
                else:
                    error_msg = f"获取二维码失败: {error_msg}"

                login_window.after(0, lambda: messagebox.showerror("错误", error_msg))
                login_window.after(0, lambda: progress.stop())


        threading.Thread(target=get_qrcode, daemon=True).start()


    def check_login_status(self, qrcode_key, window, qrcode_label, progress, status_label):
        """检查扫码登录状态"""

        def poll():
            for i in range(60):
                time.sleep(2)

                try:
                    params = {'qrcode_key': qrcode_key, 'source': 'main-fe-header'}
                    url = f"https://passport.bilibili.com/x/passport-login/web/qrcode/poll?{urllib.parse.urlencode(params)}"
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': 'https://passport.bilibili.com/',
                        'Origin': 'https://passport.bilibili.com'
                    })

                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode('utf-8'))

                    if data.get('code') != 0:
                        window.after(0, lambda: messagebox.showerror("错误", data.get('message', '登录失败')))
                        window.after(0, lambda: progress.stop())
                        return

                    login_data = data.get('data', {})
                    cid = login_data.get('code', 0)

                    if cid == 0:
                        url_redirect = login_data.get('url', '')
                        refresh_token = login_data.get('refresh_token', '')
                        window.after(0, lambda: status_label.config(text="登录成功，获取Cookie中..."))
                        if url_redirect:
                            self.parse_and_save_cookie(url_redirect, refresh_token)
                        window.after(0, lambda: self.show_login_success(window, progress))
                        return
                    elif cid == 86038:
                        window.after(0, lambda: messagebox.showwarning("超时", "二维码已过期，请重新获取"))
                        window.after(0, lambda: progress.stop())
                        return
                    elif cid == 86090:
                        window.after(0, lambda: status_label.config(text="已扫码，请在APP中确认..."))

                except Exception as e:
                    # 网络错误时继续尝试，不要立即退出
                    if i > 3:  # 30次尝试（约1分钟）后才显示错误
                        window.after(0, lambda: status_label.config(text="网络连接异常，正在重试..."))
                    continue

            window.after(0, lambda: messagebox.showwarning("超时", "登录已超时，请重新获取二维码"))
            window.after(0, lambda: progress.stop())

        threading.Thread(target=poll, daemon=True).start()


    def parse_and_save_cookie(self, url_redirect, refresh_token):
        """从跳转URL解析并保存Cookie"""
        try:
            parsed = urllib.parse.urlparse(url_redirect)
            query_params = urllib.parse.parse_qs(parsed.query)

            cookie_data = {
                'refresh_token': refresh_token,
                'expires_at': time.time() + 7 * 24 * 3600,
                'mid': query_params.get('mid', [None])[0],
                'bili_jct': query_params.get('bili_jct', [None])[0],
                'SESSDATA': query_params.get('SESSDATA', [None])[0],
                'DEDEUserID': query_params.get('DEDEUserID', [None])[0],
                'DEDEUserID__ckMd5': query_params.get('DEDEUserID__ckMd5', [None])[0],
                'sid': query_params.get('sid', [None])[0],
            }

            with open(self.bilibili_cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, ensure_ascii=False, indent=2)

            self.log_message("✓ B站大会员登录成功")
            self.bili_jct = cookie_data.get('bili_jct')
        except Exception as e:
            self.log_message(f"保存Cookie失败: {e}")


    def save_bilibili_cookie(self, login_data):

        """保存B站Cookie"""

        try:

            # 保存cookie到文件

            cookie_data = {

                'access_token': login_data.get('access_token'),

                'refresh_token': login_data.get('refresh_token'),

                'expires_at': time.time() + 7 * 24 * 3600,  # 7天后过期

                'mid': login_data.get('mid'),

                'timeline': login_data.get('timeline', {})

            }

            with open(self.bilibili_cookie_file, 'w', encoding='utf-8') as f:

                json.dump(cookie_data, f, ensure_ascii=False, indent=2)

            self.log_message("✓ B站大会员登录成功")

            self.bili_jct = login_data.get('bili_jct')

        except Exception as e:

            self.log_message(f"保存Cookie失败: {e}")


    def bilibili_logout(self):
        """退出B站登录"""
        try:
            if self.bilibili_cookie_file.exists():
                self.bilibili_cookie_file.unlink()
                self.log_message("✓ 已退出B站登录")
                self.bili_jct = None
            else:
                self.log_message("✓ 未检测到B站登录状态")
        except Exception as e:
            self.log_message(f"退出登录失败: {e}")

    def show_login_success(self, window, progress):

        """显示登录成功"""

        progress.stop()

        window.destroy()

        messagebox.showinfo("成功", "✓ B站大会员登录成功！\n\n现在可以下载更高音质的音频了")


    def get_bilibili_cookies(self):

        """获取B站Cookie字符串"""

        if self.bilibili_cookie_file.exists():

            try:

                with open(self.bilibili_cookie_file, 'r', encoding='utf-8') as f:

                    data = json.load(f)

                # 生成cookie字符串 - 匹配parse_and_save_cookie保存的格式
                cookies = []

                # 检查是否有SESSDATA（主要的登录凭证）
                if 'SESSDATA' in data and data['SESSDATA']:
                    cookies.append(f"SESSDATA={data['SESSDATA']}")

                if 'bili_jct' in data and data['bili_jct']:
                    cookies.append(f"bili_jct={data['bili_jct']}")

                if 'DEDEUserID' in data and data['DEDEUserID']:
                    cookies.append(f"DEDEUserID={data['DEDEUserID']}")

                if 'DEDEUserID__ckMd5' in data and data['DEDEUserID__ckMd5']:
                    cookies.append(f"DEDEUserID__ckMd5={data['DEDEUserID__ckMd5']}")

                if 'sid' in data and data['sid']:
                    cookies.append(f"sid={data['sid']}")

                if cookies:
                    self.log_message(f"✓ 读取到B站登录信息，Cookie项数: {len(cookies)}")
                    return '; '.join(cookies)

            except Exception as e:
                self.log_message(f"读取Cookie失败: {e}")

        return None


    def test_dependencies(self):

        """测试依赖功能"""

        self.log_message("\n=== 依赖功能测试 ===")

        self.check_dependencies()


    def browse_directory(self):

        """选择输出目录"""

        directory = filedialog.askdirectory(

            title="选择保存目录",

            initialdir=self.output_dir_var.get()

        )

        if directory:

            self.output_dir_var.set(directory)

            self.save_config('output_dir', directory)


    def validate_url(self, url):

        """验证B站URL格式"""

        patterns = [

            r'https?://www\.bilibili\.com/video/[AaBb][Vv]\w+',

            r'https?://b23\.tv/[AaBb][Vv]\w+',

        ]

        return any(re.match(pattern, url) for pattern in patterns)


    def log_message(self, message):

        """添加日志消息"""

        # 根据消息类型添加颜色
        if message.startswith('✓'):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.tag_configure('success', foreground=GlassTheme.get_color('accent_green'))
            self.log_text.tag_add('success', 'end-2c linestart', 'end-2c lineend')
        elif message.startswith('❌') or message.startswith('✗'):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.tag_configure('error', foreground=GlassTheme.get_color('accent_red'))
            self.log_text.tag_add('error', 'end-2c linestart', 'end-2c lineend')
        elif message.startswith('⚠'):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.tag_configure('warning', foreground=GlassTheme.get_color('primary'))
            self.log_text.tag_add('warning', 'end-2c linestart', 'end-2c lineend')
        else:
            self.log_text.insert(tk.END, f"{message}\n")

        self.log_text.see(tk.END)

        self.root.update_idletasks()

    def _animate_progress(self):
        """进度条动画效果"""
        current_value = self.progress_var.get()
        if current_value > 0 and self.is_processing:
            # 添加脉冲效果
            pulse = 1 + 0.02 * (1 + (time.time() * 10) % 1)
            self.progress_bar.configure(style='Pulse.Horizontal.TProgressbar')
        else:
            self.progress_bar.configure(style='Glass.Horizontal.TProgressbar')


    def update_progress(self, progress, status):

        """更新进度条和状态"""

        self.progress_var.set(progress)

        self.status_var.set(status)

        self.progress_label.config(text=f"{int(progress)}%")


        # 根据进度更新颜色
        if progress == 100:
            self.progress_label.config(fg=GlassTheme.get_color('accent_green'))
        elif progress > 0:
            self.progress_label.config(fg=GlassTheme.get_color('primary'))
        else:
            self.progress_label.config(fg=GlassTheme.get_color('text_secondary'))

        self.root.update_idletasks()

    def _on_button_hover(self, button, hovering):

        """按钮悬停效果"""

        if hovering:

            button.configure(bg=GlassTheme.get_color('primary_light'))

        else:

            # 恢复原始颜色，根据按钮类型
            if button == self.extract_btn:
                button.configure(bg=GlassTheme.get_color('primary'))
            elif button == self.test_btn:
                button.configure(bg=GlassTheme.get_color('accent_blue'))
            elif button == self.login_btn:
                button.configure(bg=GlassTheme.get_color('accent_green'))
            else:
                button.configure(bg=GlassTheme.get_color('accent_blue'))


    def get_highest_quality_url(self, url):

        """获取视频的最高音质URL"""

        self.log_message("正在获取最高音质音频信息...")


        try:

            # 使用 yt-dlp 获取视频信息

            cmd = ['yt-dlp', '--dump-json', '--no-playlist', url]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')


            if result.returncode != 0:

                # 如果失败，直接返回原URL，yt-dlp会自动选择最高质量

                self.log_message("无法获取详细信息，将下载最高质量音频")

                return url, "自动选择最高质量"


            import json

            video_info = json.loads(result.stdout)


            # yt-dlp 格式信息在 formats 字段中

            if 'formats' in video_info:

                formats = video_info['formats']


                # 查找最高音质的音频流

                highest_audio_format = None

                highest_score = -1


                for fmt in formats:

                    if isinstance(fmt, dict):

                        # 只考虑纯音频格式

                        if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':

                            score = 0

                            # 根据音频编码格式打分

                            acodec = fmt.get('acodec', '').lower()

                            # flac, aiff, wav 是无损格式

                            if 'flac' in acodec or 'pcm' in acodec:

                                score += 2000  # 最高优先级给FLAC

                            elif 'aac' in acodec:

                                score += 500

                            elif 'opus' in acodec or 'vorbis' in acodec:

                                score += 300

                            elif 'mp3' in acodec:

                                score += 100


                            # 根据比特率打分

                            abr = fmt.get('abr', 0) or 0

                            score += int(abr) if abr else 0


                            # 根据采样率打分

                            asr = fmt.get('asr', 0) or 0

                            score += int(asr) // 100 if asr else 0


                            if score > highest_score:

                                highest_score = score

                                highest_audio_format = {

                                    'format_id': fmt.get('format_id', 'unknown'),

                                    'acodec': acodec,

                                    'abr': abr,

                                    'asr': asr,

                                    'format_note': fmt.get('format_note', ''),

                                    'url': fmt.get('url', url)

                                }


                if highest_audio_format:

                    quality_parts = []

                    if highest_audio_format['abr']:

                        quality_parts.append(f"{int(highest_audio_format['abr'])}kbps")

                    if highest_audio_format['asr']:

                        quality_parts.append(f"{int(highest_audio_format['asr'])}Hz")

                    if highest_audio_format['acodec']:

                        quality_parts.append(highest_audio_format['acodec'].upper())


                    quality_desc = " ".join(quality_parts) if quality_parts else "最高音质"

                    self.log_message(f"✓ 最高音质: {quality_desc}")

                    self.highest_quality = quality_desc

                    return url, quality_desc


        except Exception as e:

            self.log_message(f"获取音质信息时出错: {e}")


        # 如果无法获取详细信息，返回原URL

        return url, "自动选择最高质量"


    def extract_audio_thread(self):

        """在后台线程中执行音频提取"""

        url = self.url_var.get().strip()

        output_dir = self.output_dir_var.get().strip()


        try:

            # 1. 验证URL

            self.update_progress(10, "验证URL...")

            if not self.validate_url(url):

                raise Exception("无效的B站视频链接")

            self.log_message(f"URL验证通过: {url}")


            # 2. 创建输出目录

            self.update_progress(20, "创建输出目录...")

            output_path = Path(output_dir)

            output_path.mkdir(parents=True, exist_ok=True)

            self.log_message(f"输出目录: {output_path}")


            # 3. B站登录检查

            self.update_progress(25, "检查登录状态...")

            cookie_str = self.get_bilibili_cookies()

            if cookie_str:

                self.log_message("✓ 使用B站大会员Cookie")

            else:

                self.log_message("⚠ 未检测到B站登录，使用普通账号下载")

                cookie_str = None


            # 4. 获取最高音质音频

            self.update_progress(30, "获取音频信息...")

            download_url, quality_desc = self.get_highest_quality_url(url)

            self.log_message(f"将下载: {quality_desc}")


            # 5. 使用 yt-dlp 直接下载最高音质音频

            temp_dir = output_path / ".temp_audio_extract"

            temp_dir.mkdir(parents=True, exist_ok=True)


            self.update_progress(50, "下载最高音质音频...")

            self.log_message("开始下载最高音质音频...")


            # 构建yt-dlp命令 - 下载最佳质量音频

            cmd = [

                'yt-dlp',

                '--extract-audio',  # 提取音频

                '--audio-format', 'best',  # 使用最佳可用格式

                '--audio-quality', '0',  # 最高质量

                '--output', str(temp_dir / '%(title)s.%(ext)s'),

                '--no-playlist',  # 不下载播放列表

                '--retries', '3',  # 重试次数

                '--fragment-retries', '3',  # 片段重试次数

            ]


            # 使用Cookie
            cookie_file = None
            if cookie_str:

                cookie_file = temp_dir / "bilibili_cookie.txt"

                with open(cookie_file, 'w', encoding='utf-8') as f:
                    # yt-dlp 需要 Netscape 格式的 cookie 文件
                    f.write("# Netscape HTTP Cookie File\n")
                    f.write("# https://curl.haxx.se/docs/http-cookies.html\n")
                    f.write("# This file was generated by B站音频提取器\n\n")

                    for part in cookie_str.split('; '):
                        if '=' in part:
                            key, value = part.split("=", 1)
                            # Netscape cookie format: domain flag path secure expires name value
                            # .bilibili.com  domain
                            # TRUE              flag (all domains under .bilibili.com)
                            # /                 path
                            # FALSE             secure (not HTTPS only)
                            # 0                 expires (session cookie)
                            f.write(f".bilibili.com\tTRUE\t/\tFALSE\t0\t{key.strip()}\t{value.strip()}\n")

                cmd.extend(['--cookies', str(cookie_file)])

                self.log_message("✓ 使用B站Cookie进行下载")
            else:
                self.log_message("⚠ 未检测到B站登录，使用普通账号下载")

            cmd.append(url)


            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

            if result.returncode != 0:
                stderr_output = result.stderr if result.stderr else ''
                error_msg = stderr_output[:200] if stderr_output else '未知错误'

                # 如果使用了Cookie且出现412错误，尝试移除Cookie重试
                if cookie_str and cookie_file and ('412' in stderr_output or 'Precondition Failed' in stderr_output):
                    self.log_message("检测到Cookie失效(412错误)，自动切换到非会员下载模式...")

                    cmd_no_cookie = [arg for arg in cmd if '--cookies' not in arg and str(cookie_file) not in arg]
                    result = subprocess.run(cmd_no_cookie, capture_output=True, text=True, encoding='utf-8', errors='replace')

                    if result.returncode == 0:
                        self.log_message("✓ 非会员下载成功（最高可用音质）")
                    else:
                        raise Exception(f"下载失败: {result.stderr[:200] if result.stderr else '未知错误'}")
                else:
                    # 没有使用Cookie或非412错误，直接报错
                    raise Exception(f"下载失败: {error_msg}")

            # 6. 查找下载的音频文件

            audio_path = None

            for ext in ['*.flac', '*.m4a', '*.mp3', '*.opus', '*.aac', '*.wav']:

                files = list(temp_dir.glob(ext))

                if files:

                    audio_path = files[0]

                    break


            if not audio_path:

                raise Exception("未找到下载的音频文件")


            self.log_message(f"✓ 找到音频文件: {audio_path.name}")


            # 7. 提取音频（最高音质 - 保持原始质量）

            self.update_progress(70, "提取音频...")

            self.log_message("开始提取音频（保持原始最高音质）...")


            # yt-dlp 已经下载了音频文件

            import shutil


            file_stem = audio_path.stem


            # 检查是否需要转换为FLAC

            if audio_path.suffix.lower() == '.flac':

                # 已经是FLAC格式，直接复制

                output_file = output_path / f"{file_stem}_最高音质.flac"

                shutil.copy2(audio_path, output_file)

                self.log_message("✓ 已下载FLAC无损音频")

            else:

                # 转换为FLAC格式

                output_file = output_path / f"{file_stem}_最高音质.flac"

                self.log_message(f"正在将 {audio_path.suffix} 转换为FLAC无损格式...")


                cmd = [

                    'ffmpeg',

                    '-i', str(audio_path),

                    '-c:a', 'flac',

                    '-compression_level', '12',

                    '-y',

                    str(output_file)

                ]


                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')


                if result.returncode != 0:

                    # 转换失败，使用原文件

                    self.log_message(f"FLAC转换失败，使用原格式: {result.stderr[:100] if result.stderr else '未知错误'}")

                    output_file = output_path / f"{file_stem}_最高音质{audio_path.suffix}"

                    shutil.copy2(audio_path, output_file)

                else:

                    self.log_message("✓ 已转换为FLAC无损格式")


            if not output_file.exists():

                raise Exception("音频文件未生成")


            file_size = output_file.stat().st_size / (1024 * 1024)

            self.log_message(f"✓ 音频提取完成: {output_file.name} ({file_size:.2f} MB)")

            self.log_message(f"  音质: {self.highest_quality or '最高音质'}")


            # 7. 清理临时文件

            self.update_progress(90, "清理临时文件...")

            try:

                for item in temp_dir.glob('*'):

                    if item.is_file():

                        item.unlink()

                temp_dir.rmdir()

                self.log_message("✓ 临时文件已清理")

            except Exception as e:

                self.log_message(f"临时清理完成: {e}")


            # 8. 完成

            self.update_progress(100, "完成！")

            self.log_message(f"🎉 音频提取成功！文件保存在: {output_file}")


            messagebox.showinfo(

                "完成",

                f"音频提取成功！\n\n文件: {output_file.name}\n大小: {file_size:.2f} MB\n位置: {output_path}"

            )


        except Exception as e:

            self.log_message(f"❌ 错误: {e}")

            messagebox.showerror("错误", str(e))

            self.update_progress(0, "错误")


        finally:

            self.is_processing = False

            self.extract_btn.config(state=tk.NORMAL)


    def start_extraction(self):

        """开始音频提取"""

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

        self.log_message(f"\n=== 开始提取最高音质音频 ===")

        self.log_message(f"URL: {url}")

        self.log_message(f"输出目录: {output_dir}")


        # 启动动画效果
        self._start_processing_animation()

        thread = threading.Thread(target=self.extract_audio_thread, daemon=True)

        thread.start()

    def _start_processing_animation(self):
        """启动处理中的动画效果"""
        self._animate_pulse()

    def _animate_pulse(self):
        """脉冲动画效果"""
        if self.is_processing:
            # 让进度条轻微脉冲
            current_value = self.progress_var.get()
            pulse_value = current_value + 0.5
            if pulse_value > 100:
                pulse_value = current_value
            self.progress_var.set(pulse_value)

            self.root.after(200, self._animate_pulse)

    def _animate_button_press(self, button, pressing):
        """按钮按压缩放动画"""
        if pressing:
            button.configure(relief='sunken')
        else:
            button.configure(relief='flat')


    def load_config(self):

        """加载配置文件"""

        try:

            if self.config_file.exists():

                with open(self.config_file, 'r', encoding='utf-8') as f:

                    config = json.load(f)

                    if 'output_dir' in config:

                        saved_dir = config['output_dir']

                        if Path(saved_dir).exists():

                            self.output_dir_var.set(saved_dir)

        except:

            pass


    def save_config(self, key, value):

        """保存配置项"""

        try:

            config = {}

            if self.config_file.exists():

                with open(self.config_file, 'r', encoding='utf-8') as f:

                    config = json.load(f)

            config[key] = value

            with open(self.config_file, 'w', encoding='utf-8') as f:

                json.dump(config, f, ensure_ascii=False, indent=2)

        except:

            pass


    def save_current_settings(self):

        """保存当前设置 (在程序退出时调用)"""

        try:

            # 保存当前的输出目录

            current_dir = self.output_dir_var.get()

            if current_dir and Path(current_dir).exists():

                self.save_config('output_dir', current_dir)

        except Exception as e:

            print(f"保存设置失败: {e}")


def main():

    root = tk.Tk()

    app = BilibiliAudioExtractorGUI(root)


    def on_closing():

        app.save_current_settings()

        root.destroy()


    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()




if __name__ == "__main__":

    main()