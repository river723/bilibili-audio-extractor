#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站音频提取器 - 增强版本
自动处理B站登录限制，支持多种下载策略
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import os
import sys
import re
import json
from pathlib import Path

class BilibiliAudioExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("B站音频提取器 v2.0 (增强版)")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)

        # 配置文件路径
        self.config_file = Path.home() / ".bilibili_audio_extractor_config.json"

        # 初始化变量
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="就绪")
        self.is_processing = False
        self.download_strategies = [
            {'format': 'flv', 'desc': 'FLV格式 (高质量)'},
            {'format': 'mp4', 'desc': 'MP4格式 (标准质量)'},
            {'format': '360p', 'desc': '360p (低质量，免登录)'},
            {'format': '', 'desc': '自动选择 (推荐)'}
        ]
        self.selected_strategy = tk.StringVar(value='')

        # 文件保留选项
        self.keep_video_var = tk.BooleanVar(value=False)  # 默认不保留视频文件

        # 大会员登录相关
        self.use_login_var = tk.BooleanVar(value=False)
        self.cookie_file_var = tk.StringVar()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self.setup_ui()

        # 加载配置 (需要在UI设置完成后进行)
        self.load_config()

        self.check_dependencies()

    def setup_ui(self):
        """设置用户界面"""
        # 创建主容器
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = tk.Label(
            main_container,
            text="B站音频提取器 v2.0 (增强版)",
            font=('微软雅黑', 16, 'bold'),
            pady=10
        )
        title_label.pack(fill=tk.X)

        # 创建带滚动条的画布
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # URL输入区域
        url_frame = tk.LabelFrame(scrollable_frame, text="B站视频链接", padx=10, pady=10)
        url_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(url_frame, text="视频URL:", anchor="w").pack(fill=tk.X, pady=(0, 5))
        url_entry = tk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 10))
        url_entry.pack(fill=tk.X, pady=(0, 5))

        # 示例链接
        example_url = "https://www.bilibili.com/video/BV1Hs4y1B7T2"
        tk.Label(url_frame, text=f"示例: {example_url}", fg="gray", anchor="w").pack(fill=tk.X)

        # 格式检测按钮
        format_detect_frame = tk.LabelFrame(scrollable_frame, text="格式检测", padx=10, pady=10)
        format_detect_frame.pack(fill=tk.X, pady=(0, 10))

        detect_btn_frame = tk.Frame(format_detect_frame)
        detect_btn_frame.pack(fill=tk.X, pady=(0, 5))

        self.detect_format_btn = tk.Button(
            detect_btn_frame,
            text="检测可用格式",
            command=self.detect_available_formats,
            bg='#4CAF50',
            fg='white',
            width=15
        )
        self.detect_format_btn.pack(side=tk.LEFT)

        # 可用格式显示
        self.available_formats_var = tk.StringVar(value="点击按钮检测该视频可用的下载格式")
        self.available_formats_label = tk.Label(
            format_detect_frame,
            textvariable=self.available_formats_var,
            anchor="w",
            fg="blue",
            wraplength=600
        )
        self.available_formats_label.pack(fill=tk.X, pady=(5, 0))

        # 下载策略选择
        strategy_frame = tk.LabelFrame(scrollable_frame, text="下载策略 (解决登录限制)", padx=10, pady=10)
        strategy_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(strategy_frame, text="选择下载策略:", anchor="w").pack(fill=tk.X, pady=(0, 5))

        for i, strategy in enumerate(self.download_strategies):
            rb = tk.Radiobutton(
                strategy_frame,
                text=strategy['desc'],
                variable=self.selected_strategy,
                value=strategy['format'],
                anchor="w"
            )
            rb.pack(fill=tk.X, pady=(0, 2))

        # 输出目录选择
        dir_frame = tk.LabelFrame(scrollable_frame, text="输出设置", padx=10, pady=10)
        dir_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(dir_frame, text="保存目录:", anchor="w").pack(fill=tk.X, pady=(0, 5))

        dir_entry_frame = tk.Frame(dir_frame)
        dir_entry_frame.pack(fill=tk.X, pady=(0, 5))

        dir_entry = tk.Entry(dir_entry_frame, textvariable=self.output_dir_var, font=('Arial', 10))
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = tk.Button(
            dir_entry_frame,
            text="浏览",
            command=self.browse_directory,
            width=8,
            bg='#2196F3',
            fg='white'
        )
        browse_btn.pack(side=tk.RIGHT)

        # 设置默认目录
        default_dir = str(Path.home() / "B站音频提取")
        # 优先使用保存的配置，否则使用默认目录
        saved_dir = self.get_config('output_dir', default_dir)
        self.output_dir_var.set(saved_dir)

        # 音频质量信息
        quality_frame = tk.LabelFrame(scrollable_frame, text="音频质量", padx=10, pady=10)
        quality_frame.pack(fill=tk.X, pady=(0, 10))

        # 原始音频信息显示
        self.original_quality_var = tk.StringVar(value="原始音频信息: 待检测...")
        self.original_quality_label = tk.Label(
            quality_frame,
            textvariable=self.original_quality_var,
            fg="blue",
            anchor="w",
            font=('Arial', 9)
        )
        self.original_quality_label.pack(fill=tk.X, pady=(0, 5))

        # 转换质量选择
        tk.Label(quality_frame, text="选择转换质量:", anchor="w").pack(fill=tk.X, pady=(5, 2))

        self.quality_var = tk.StringVar(value="original")
        quality_options = [
            ("原始质量 (FLAC无损，保持源音频参数)", "original"),
            ("高质量FLAC (FLAC, 96kHz升频, 32bit)", "hires"),
            ("CD音质 (FLAC, 44.1kHz, 16bit)", "cd"),
            ("高音质MP3 (MP3, 320kbps)", "mp3_high"),
            ("标准MP3 (MP3, 128kbps)", "mp3")
        ]

        for text, value in quality_options:
            rb = tk.Radiobutton(
                quality_frame,
                text=text,
                variable=self.quality_var,
                value=value,
                anchor="w",
                command=self.save_quality_settings  # 选择改变时保存
            )
            rb.pack(fill=tk.X, pady=(0, 2))

        # 文件保留选项
        options_frame = tk.LabelFrame(scrollable_frame, text="处理选项", padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        keep_video_cb = tk.Checkbutton(
            options_frame,
            text="保留下载的视频文件 (方便后续使用)",
            variable=self.keep_video_var,
            anchor="w",
            command=self.save_checkbox_settings  # 状态改变时保存
        )
        keep_video_cb.pack(fill=tk.X, pady=(0, 5))

        tk.Label(
            options_frame,
            text="提示: 保留视频文件会占用更多磁盘空间，但可以用于其他用途",
            fg="gray",
            anchor="w",
            font=('Arial', 9)
        ).pack(fill=tk.X)

        # 大会员登录设置
        login_frame = tk.LabelFrame(scrollable_frame, text="大会员登录 (获取更高音质)", padx=10, pady=10)
        login_frame.pack(fill=tk.X, pady=(0, 10))

        use_login_cb = tk.Checkbutton(
            login_frame,
            text="启用大会员登录 (获取最高音质)",
            variable=self.use_login_var,
            anchor="w",
            command=self.toggle_login_fields
        )
        use_login_cb.pack(fill=tk.X, pady=(0, 10))

        # Cookie文件选择
        cookie_frame = tk.Frame(login_frame)
        cookie_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(cookie_frame, text="Cookie文件:", anchor="w").pack(fill=tk.X, pady=(0, 2))
        cookie_entry_frame = tk.Frame(cookie_frame)
        cookie_entry_frame.pack(fill=tk.X)

        self.cookie_entry = tk.Entry(cookie_entry_frame, textvariable=self.cookie_file_var, font=('Arial', 10))
        self.cookie_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.cookie_entry.config(state=tk.DISABLED)  # 初始禁用

        cookie_browse_btn = tk.Button(
            cookie_entry_frame,
            text="浏览",
            command=self.browse_cookie_file,
            width=8,
            bg='#2196F3',
            fg='white'
        )
        cookie_browse_btn.pack(side=tk.RIGHT)

        tk.Label(
            login_frame,
            text="提示: Cookie文件已验证有效，大会员音质功能正常。选择Cookie文件: E:\\music\\www.bilibili.com_cookies.txt",
            fg="gray",
            anchor="w",
            font=('Arial', 9),
            wraplength=600
        ).pack(fill=tk.X)

        # 进度条
        progress_frame = tk.LabelFrame(scrollable_frame, text="处理进度", padx=10, pady=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.status_label = tk.Label(progress_frame, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill=tk.X)

        # 按钮区域
        button_frame = tk.Frame(scrollable_frame, pady=10)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # 创建按钮
        self.extract_btn = tk.Button(
            button_frame,
            text="开始提取音频",
            command=self.start_extraction,
            bg='#4CAF50',
            fg='white',
            font=('微软雅黑', 10, 'bold'),
            width=15,
            height=2
        )
        self.extract_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.test_btn = tk.Button(
            button_frame,
            text="测试依赖",
            command=self.test_dependencies,
            bg='#2196F3',
            fg='white',
            font=('微软雅黑', 10),
            width=10,
            height=2
        )
        self.test_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.cleanup_btn = tk.Button(
            button_frame,
            text="清理临时文件",
            command=self.cleanup_temp,
            bg='#FF9800',
            fg='white',
            font=('微软雅黑', 10),
            width=12,
            height=2
        )
        self.cleanup_btn.pack(side=tk.LEFT)

        # 日志区域
        log_frame = tk.LabelFrame(scrollable_frame, text="处理日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 使用ScrolledText替代Text+Scrollbar组合
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            width=80,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 绑定回车键
        self.root.bind('<Return>', lambda e: self.start_extraction())

        # 绑定鼠标滚轮
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

    def check_dependencies(self):
        """检查必要的依赖"""
        self.log_message("检查系统依赖...")

        # 检查you-get
        try:
            subprocess.run(['you-get', '--version'], capture_output=True, check=True)
            self.log_message("you-get 已安装")
        except:
            self.log_message("you-get 未安装，请运行: pip install you-get")

        # 检查FFmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            self.log_message("FFmpeg 已安装")
        except:
            self.log_message("FFmpeg 未安装，请从 https://ffmpeg.org 下载安装")

        self.log_message("依赖检查完成")

    def browse_directory(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(
            title="选择保存目录",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
            # 保存配置
            self.save_config('output_dir', directory)

    def browse_cookie_file(self):
        """选择Cookie文件"""
        cookie_file = filedialog.askopenfilename(
            title="选择Cookie文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialdir=str(Path.home())
        )
        if cookie_file:
            self.cookie_file_var.set(cookie_file)
            self.save_config('cookie_file', cookie_file)

    def toggle_login_fields(self):
        """切换登录相关控件的启用状态"""
        if self.use_login_var.get():
            self.cookie_entry.config(state=tk.NORMAL)
        else:
            self.cookie_entry.config(state=tk.DISABLED)
        # 保存登录设置
        self.save_login_settings()

    def validate_url(self, url):
        """验证B站URL格式"""
        patterns = [
            r'https?://www\.bilibili\.com/video/[AaBb][Vv]\w+',
            r'https?://b23\.tv/[AaBb][Vv]\w+',
            r'https?://www\.bilibili\.com/video/[Bb][Vv]\w+',
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_progress(self, progress, status):
        """更新进度条和状态"""
        self.progress_var.set(progress)
        self.status_var.set(status)
        self.root.update_idletasks()

    def test_dependencies(self):
        """测试依赖功能"""
        self.log_message("\n=== 依赖功能测试 ===")
        self.check_dependencies()

    def cleanup_temp(self):
        """清理临时文件"""
        try:
            # 清理输出目录中的临时文件夹
            output_dir = self.output_dir_var.get()
            if output_dir:
                temp_dir = Path(output_dir) / ".temp_bilibili_extractor"
                if temp_dir.exists():
                    for file in temp_dir.glob('*'):
                        if file.is_file():
                            file.unlink()
                    temp_dir.rmdir()  # 删除临时目录本身
                    self.log_message(f"临时文件已清理: {temp_dir}")
                    return

            # 也清理系统临时目录（向后兼容）
            system_temp_dir = Path(os.getenv('TEMP', '/tmp')) / "bilibili_audio_extractor"
            if system_temp_dir.exists():
                for file in system_temp_dir.glob('*'):
                    if file.is_file():
                        file.unlink()
                system_temp_dir.rmdir()
                self.log_message(f"系统临时文件已清理: {system_temp_dir}")
            else:
                self.log_message("没有找到临时文件")
        except Exception as e:
            self.log_message(f"清理失败: {e}")

    def get_available_formats(self, url):
        """获取视频可用的下载格式"""
        try:
            import subprocess
            import json

            cmd = ['you-get', '--json', url]
            result = subprocess.run(cmd, capture_output=True, text=False)

            formats = []
            seen_descriptions = set()  # 用于去重
            if result.returncode == 0 and result.stdout:
                try:
                    # 尝试解码输出
                    try:
                        stdout_text = result.stdout.decode('utf-8')
                    except UnicodeDecodeError:
                        stdout_text = result.stdout.decode('gbk', errors='ignore')

                    video_info = json.loads(stdout_text)

                    if 'streams' in video_info:
                        streams = video_info['streams']

                        if isinstance(streams, dict):
                            # streams是字典结构，键是格式名称，值是流信息
                            for stream_key, stream_info in streams.items():
                                if isinstance(stream_info, dict):
                                    quality = stream_info.get('quality', '')
                                    container = stream_info.get('container', '')
                                    size = stream_info.get('size', 'unknown')

                                    if quality and container:
                                        # 解析质量信息，提取分辨率
                                        resolution = ''

                                        # 从quality字段提取分辨率
                                        if '1080' in quality or '1080' in stream_key:
                                            resolution = '1080p'
                                        elif '720' in quality or '720' in stream_key:
                                            resolution = '720p'
                                        elif '480' in quality or '480' in stream_key:
                                            resolution = '480p'
                                        elif '360' in quality or '360' in stream_key:
                                            resolution = '360p'
                                        elif 'hd' in stream_key.lower():
                                            resolution = '高清'

                                        # 创建描述（只显示分辨率，不显示编码）
                                        if resolution:
                                            description = f"{resolution} ({container})"
                                        else:
                                            description = f"{quality} ({container})"

                                        # 生成对应的you-get格式参数
                                        # 优先使用分辨率作为参数
                                        if 'flv' in stream_key.lower():
                                            format_param = 'flv'
                                        elif resolution == '1080p':
                                            format_param = 'hd2'
                                        elif resolution == '720p':
                                            format_param = 'hd1'
                                        elif resolution == '360p':
                                            format_param = '360p'
                                        elif resolution == '480p':
                                            format_param = '480p'
                                        else:
                                            format_param = resolution or 'mp4'

                                        # 去重：如果已经有相同描述的格式，跳过
                                        if description not in seen_descriptions:
                                            seen_descriptions.add(description)
                                            formats.append({
                                                'quality': format_param,
                                                'container': container,
                                                'size': size,
                                                'description': description,
                                                'original_key': stream_key
                                            })
                        elif isinstance(streams, list):
                            # streams是列表结构（旧版本格式）
                            for stream in streams:
                                if isinstance(stream, dict) and stream.get('quality') and stream.get('container'):
                                    description = f"{stream['quality']} ({stream['container']})"

                                    # 去重：如果已经有相同描述的格式，跳过
                                    if description not in seen_descriptions:
                                        seen_descriptions.add(description)
                                        formats.append({
                                            'quality': stream['quality'],
                                            'container': stream['container'],
                                            'size': stream.get('size', 'unknown'),
                                            'description': description,
                                            'original_key': stream.get('quality', '')
                                        })
                except Exception as e:
                    print(f"解析视频信息失败: {e}")

            # 如果没有找到具体格式信息，提供默认选项
            if not formats:
                formats = [
                    {'quality': 'hd2', 'container': 'mp4', 'description': '1080p (MP4, 高质量)', 'original_key': 'hd2'},
                    {'quality': 'hd1', 'container': 'mp4', 'description': '720p (MP4, 标准质量)', 'original_key': 'hd1'},
                    {'quality': 'flv', 'container': 'flv', 'description': 'FLV格式 (高质量)', 'original_key': 'flv'},
                    {'quality': '360p', 'container': 'mp4', 'description': '360p (低质量，免登录)', 'original_key': '360p'}
                ]

            return formats
        except Exception as e:
            # 如果无法获取详细信息，提供默认选项
            print(f"获取格式信息失败: {e}")
            return [
                {'quality': 'hd2', 'container': 'mp4', 'description': '1080p (MP4, 高质量)', 'original_key': 'hd2'},
                {'quality': 'hd1', 'container': 'mp4', 'description': '720p (MP4, 标准质量)', 'original_key': 'hd1'},
                {'quality': 'flv', 'container': 'flv', 'description': 'FLV格式 (高质量)', 'original_key': 'flv'},
                {'quality': '360p', 'container': 'mp4', 'description': '360p (低质量，免登录)', 'original_key': '360p'}
            ]

    def detect_available_formats(self):
        """检测并显示可用格式"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请先输入B站视频链接")
            return

        if not self.validate_url(url):
            messagebox.showerror("错误", "无效的B站视频链接")
            return

        # 在后台线程中执行格式检测
        self.detect_format_btn.config(state='disabled', text="检测中...")
        self.available_formats_var.set("正在检测可用格式，请稍候...")

        thread = threading.Thread(target=self._detect_formats_thread, args=(url,), daemon=True)
        thread.start()

    def _detect_formats_thread(self, url):
        """在后台线程中检测格式"""
        try:
            formats = self.get_available_formats(url)

            # 更新UI
            self.root.after(0, lambda: self._update_formats_display(formats))

        except Exception as e:
            self.root.after(0, lambda: self._show_format_error(str(e)))

    def _update_formats_display(self, formats):
        """更新格式显示"""
        self.detect_format_btn.config(state='normal', text="检测可用格式")

        format_text = f"检测到 {len(formats)} 种可下载格式:\n"
        for i, fmt in enumerate(formats, 1):
            format_text += f"{i}. {fmt['description']}\n"

        self.available_formats_var.set(format_text)
        self.log_message(f"格式检测完成，找到 {len(formats)} 个可用格式")

    def _show_format_error(self, error):
        """显示格式检测错误"""
        self.detect_format_btn.config(state='normal', text="检测可用格式")
        self.available_formats_var.set("格式检测失败，使用默认选项")
        messagebox.showerror("错误", f"格式检测失败: {error}")

    def download_with_strategy(self, url, temp_dir, strategy):
        """使用指定策略下载视频"""
        cmd = ['you-get', '--output-dir', str(temp_dir)]

        if strategy:
            cmd.extend(['--format', strategy])

        # 如果启用了大会员登录，添加cookie文件
        if self.use_login_var.get() and self.cookie_file_var.get():
            cookie_file = self.cookie_file_var.get()
            if Path(cookie_file).exists():
                cmd.extend(['--cookies', cookie_file])
                self.log_message("✓ 使用Cookie文件进行下载 (大会员音质)")
            else:
                self.log_message("⚠ Cookie文件不存在，跳过登录")
                self.log_message("  请确保Cookie文件路径正确，否则无法获取大会员音质")
        else:
            self.log_message("ℹ 未使用Cookie，将下载普通音质")
            self.log_message("  如需大会员音质，请启用登录并设置有效的Cookie文件")

        cmd.append(url)

        self.log_message(f"尝试下载策略: {strategy if strategy else '自动选择'}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr

    def find_video_file(self, temp_dir):
        """在临时目录中查找视频文件"""
        video_extensions = ['*.mp4', '*.flv', '*.mkv', '*.avi', '*.mov']

        for ext in video_extensions:
            files = list(temp_dir.glob(ext))
            if files:
                return files[0]
        return None

    def get_audio_info(self, video_path):
        """获取视频中的音频信息"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-show_streams', '-select_streams', 'a:0', '-of', 'json', str(video_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                if 'streams' in info and len(info['streams']) > 0:
                    audio_stream = info['streams'][0]

                    sample_rate = audio_stream.get('sample_rate', '未知')
                    channels = audio_stream.get('channels', '未知')
                    codec_name = audio_stream.get('codec_name', '未知')

                    # 尝试获取位深度信息
                    bits_per_sample = audio_stream.get('bits_per_sample', '未知')
                    if bits_per_sample == 'unknown' or bits_per_sample == 0:
                        bits_per_sample = '自动检测'

                    return {
                        'sample_rate': sample_rate,
                        'channels': channels,
                        'codec': codec_name,
                        'bits_per_sample': bits_per_sample
                    }
            return None
        except Exception as e:
            print(f"获取音频信息失败: {e}")
            return None

    def extract_audio_thread(self):
        """在后台线程中执行音频提取"""
        url = self.url_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        strategy = self.selected_strategy.get()

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

            # 3. 创建临时目录 (使用输出目录的子目录)
            self.update_progress(30, "准备临时目录...")
            temp_dir = output_path / ".temp_bilibili_extractor"

            # 如果临时目录已存在，先清理它
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)

            temp_dir.mkdir(parents=True, exist_ok=True)

            # 4. 尝试多种下载策略
            self.update_progress(40, "下载视频...")
            self.log_message("开始尝试下载视频...")

            strategies_to_try = []

            # 如果用户选择了特定策略，先尝试该策略
            if strategy:
                strategies_to_try.append(strategy)

            # 然后尝试其他策略作为备选
            # 注意：you-get的格式名称需要准确，这里使用空字符串让you-get自动选择最佳格式
            fallback_strategies = ['']  # 只使用自动选择，避免格式名称错误
            for s in fallback_strategies:
                if s not in strategies_to_try:
                    strategies_to_try.append(s)

            video_path = None
            last_error = ""

            for current_strategy in strategies_to_try:
                try:
                    success, output = self.download_with_strategy(url, temp_dir, current_strategy)

                    if success:
                        # 查找下载的文件
                        video_path = self.find_video_file(temp_dir)
                        if video_path:
                            strategy_desc = current_strategy if current_strategy else "自动选择"
                            self.log_message(f"✓ 下载成功 (策略: {strategy_desc}): {video_path.name}")

                            # 获取原始音频信息
                            self.update_progress(50, "分析音频信息...")
                            audio_info = self.get_audio_info(video_path)
                            if audio_info:
                                sample_rate = audio_info['sample_rate']
                                channels = audio_info['channels']
                                codec = audio_info['codec']
                                bits = audio_info['bits_per_sample']

                                original_info = f"原始音频: {sample_rate}Hz, {bits}bit, {channels}声道, {codec}"
                                self.original_quality_var.set(original_info)
                                self.log_message(f"✓ 音频信息: {original_info}")
                            else:
                                self.original_quality_var.set("原始音频信息: 检测失败")
                                self.log_message("⚠ 无法获取详细音频信息")
                            break
                        else:
                            self.log_message(f"⚠ 下载完成但找不到视频文件 (策略: {current_strategy})")
                    else:
                        last_error = output
                        strategy_desc = current_strategy if current_strategy else "自动选择"
                        self.log_message(f"✗ 下载失败 (策略: {strategy_desc}): {output[:100]}...")

                except Exception as e:
                    last_error = str(e)
                    self.log_message(f"✗ 下载异常: {e}")

            if not video_path:
                raise Exception(f"所有下载策略都失败。最后的错误: {last_error}")

            # 5. 提取音频
            self.update_progress(70, "提取音频...")
            self.log_message("开始提取音频...")

            file_stem = video_path.stem
            quality_choice = self.quality_var.get()

            # 根据用户选择设置音频参数
            if quality_choice == "original":
                # 保持原始质量 (FLAC无损)
                output_file = output_path / f"{file_stem}_原始质量.flac"
                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-vn',
                    '-c:a', 'flac',
                    '-compression_level', '12',
                    '-y',
                    str(output_file)
                ]
                quality_desc = "原始质量 (FLAC无损)"
            elif quality_choice == "hires":
                # 高质量FLAC (升频到96kHz, 32bit)
                output_file = output_path / f"{file_stem}_高质量FLAC.flac"
                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-vn',
                    '-c:a', 'flac',
                    '-compression_level', '12',
                    '-ar', '96000',
                    '-sample_fmt', 's32',
                    '-b:a', '1536k',
                    '-y',
                    str(output_file)
                ]
                quality_desc = "高质量FLAC (96kHz升频, 32bit)"
            elif quality_choice == "cd":
                # CD音质 (FLAC, 44.1kHz, 16bit)
                output_file = output_path / f"{file_stem}_CD音质.flac"
                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-vn',
                    '-c:a', 'flac',
                    '-compression_level', '12',
                    '-ar', '44100',
                    '-sample_fmt', 's16',
                    '-y',
                    str(output_file)
                ]
                quality_desc = "CD音质 (FLAC, 44.1kHz, 16bit)"
            elif quality_choice == "mp3_high":
                # 高音质MP3 (MP3, 320kbps)
                output_file = output_path / f"{file_stem}_高音质MP3.mp3"
                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-vn',
                    '-c:a', 'libmp3lame',
                    '-b:a', '320k',  # 320kbps，高音质
                    '-ar', '48000',
                    '-y',
                    str(output_file)
                ]
                quality_desc = "高音质MP3 (MP3, 320kbps)"
            else:  # mp3
                # MP3音质 (MP3, 128kbps)
                output_file = output_path / f"{file_stem}_MP3音质.mp3"
                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-vn',
                    '-c:a', 'libmp3lame',
                    '-b:a', '128k',  # 128kbps
                    '-ar', '44100',
                    '-y',
                    str(output_file)
                ]
                quality_desc = "MP3音质 (MP3, 128kbps)"

            self.log_message(f"转换质量: {quality_desc}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"音频提取失败: {result.stderr}")

            if not output_file.exists():
                raise Exception("FLAC文件未生成")

            file_size = output_file.stat().st_size / (1024 * 1024)  # MB
            self.log_message(f"✓ 音频提取完成: {output_file.name} ({file_size:.2f} MB)")

            # 6. 处理视频文件
            self.update_progress(90, "处理视频文件...")

            if self.keep_video_var.get():
                # 用户选择保留视频文件
                video_output_path = output_path / f"{file_stem}_原始视频{video_path.suffix}"

                # 重命名并移动视频文件到输出目录
                video_path.rename(video_output_path)
                self.log_message(f"✓ 视频文件已保留: {video_output_path.name}")

                # 清理临时目录中的所有文件，然后删除目录
                if temp_dir.exists():
                    for file in temp_dir.glob('*'):
                        if file.is_file():
                            file.unlink()
                    try:
                        temp_dir.rmdir()
                    except OSError as e:
                        self.log_message(f"⚠ 临时目录删除失败，但文件已清理: {temp_dir} (错误: {e})")
            else:
                # 用户选择不保留，清理临时文件
                video_path.unlink()

                # 删除临时目录
                if temp_dir.exists():
                    try:
                        temp_dir.rmdir()
                    except OSError:
                        # 如果目录不为空，使用shutil.rmtree
                        import shutil
                        shutil.rmtree(temp_dir)

                self.log_message("✓ 临时文件已清理")

            # 7. 完成
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

        # 开始处理
        self.is_processing = True
        self.extract_btn.config(state=tk.DISABLED)
        self.log_message(f"\n=== 开始处理 ===")
        self.log_message(f"URL: {url}")
        self.log_message(f"输出目录: {output_dir}")
        self.log_message(f"下载策略: {self.selected_strategy.get() if self.selected_strategy.get() else '自动选择'}")

        # 在后台线程中执行
        thread = threading.Thread(target=self.extract_audio_thread, daemon=True)
        thread.start()

    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 恢复上次的输出目录
                    if 'output_dir' in config:
                        saved_dir = config['output_dir']
                        # 检查目录是否仍然存在
                        if Path(saved_dir).exists():
                            self.output_dir_var.set(saved_dir)
                        else:
                            # 如果目录不存在，使用默认目录
                            default_dir = str(Path.home() / "B站音频提取")
                            self.output_dir_var.set(default_dir)

                    # 恢复下载策略
                    if 'download_strategy' in config:
                        self.selected_strategy.set(config['download_strategy'])

                    # 恢复文件保留选项
                    if 'keep_video' in config:
                        self.keep_video_var.set(config['keep_video'])

                    # 恢复音频质量选择
                    if 'audio_quality' in config:
                        self.quality_var.set(config['audio_quality'])

                    # 恢复登录设置
                    if 'use_login' in config:
                        self.use_login_var.set(config['use_login'])
                    if 'cookie_file' in config:
                        self.cookie_file_var.set(config['cookie_file'])
        except Exception as e:
            print(f"加载配置失败: {e}")

    def save_config(self, key, value):
        """保存配置项"""
        try:
            config = {}
            # 如果配置文件存在，先读取现有配置
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # 更新配置项
            config[key] = value

            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def save_checkbox_settings(self):
        """保存复选框设置"""
        self.save_config('keep_video', self.keep_video_var.get())

    def save_quality_settings(self):
        """保存音频质量选择"""
        self.save_config('audio_quality', self.quality_var.get())

    def save_login_settings(self):
        """保存登录设置"""
        self.save_config('use_login', self.use_login_var.get())
        self.save_config('cookie_file', self.cookie_file_var.get())

    def get_config(self, key, default=None):
        """获取配置项"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get(key, default)
        except Exception as e:
            print(f"读取配置失败: {e}")
        return default

    def save_current_settings(self):
        """保存当前设置 (在程序退出时调用)"""
        try:
            # 保存当前的输出目录
            current_dir = self.output_dir_var.get()
            if current_dir and Path(current_dir).exists():
                self.save_config('output_dir', current_dir)

            # 保存当前的下载策略
            current_strategy = self.selected_strategy.get()
            if current_strategy:
                self.save_config('download_strategy', current_strategy)
        except Exception as e:
            print(f"保存设置失败: {e}")

def main():
    root = tk.Tk()
    app = BilibiliAudioExtractorGUI(root)

    # 绑定窗口关闭事件
    def on_closing():
        app.save_current_settings()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()