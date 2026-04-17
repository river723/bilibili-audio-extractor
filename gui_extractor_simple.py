#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

B站音频提取器 - 精简版

只下载所输入URL的最高音质音频（支持扫码登录大会员）

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



class BilibiliAudioExtractorGUI:

    def __init__(self, root):

        self.root = root

        self.root.title("B站音频提取器 - 精简版")

        self.root.geometry("550x600")

        self.root.minsize(500, 450)


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


    def setup_ui(self):

        """设置用户界面"""

        # 标题

        title_label = tk.Label(

            self.root,

            text="B站音频提取器 - 精简版",

            font=('微软雅黑', 16, 'bold'),

            pady=15

        )

        title_label.pack()


        # URL输入区域

        url_frame = tk.LabelFrame(self.root, text="B站视频链接", padx=15, pady=10)

        url_frame.pack(fill=tk.X, padx=15, pady=(0, 10))


        tk.Label(url_frame, text="视频URL:", anchor="w").pack(fill=tk.X, pady=(0, 5))

        url_entry = tk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 10))

        url_entry.pack(fill=tk.X, pady=(0, 5))


        example_url = "https://www.bilibili.com/video/BV1Hs4y1B7T2"

        tk.Label(url_frame, text=f"示例: {example_url}", fg="gray", anchor="w").pack(fill=tk.X)


        # 输出目录选择

        dir_frame = tk.LabelFrame(self.root, text="输出设置", padx=15, pady=10)

        dir_frame.pack(fill=tk.X, padx=15, pady=(0, 10))


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




        # 进度条

        progress_frame = tk.LabelFrame(self.root, text="处理进度", padx=15, pady=10)

        progress_frame.pack(fill=tk.X, padx=15, pady=(0, 10))


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

        button_frame = tk.Frame(self.root, pady=10)

        button_frame.pack()


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


        # B站登录状态按钮

        self.login_btn = tk.Button(

            button_frame,

            text="B站登录",

            command=self.bilibili_qrcode_login,  # 直接调用二维码登录

            bg='#FF9800',

            fg='white',

            font=('微软雅黑', 10),

            width=12,

            height=2

        )

        self.login_btn.pack(side=tk.LEFT, padx=(0, 10))


        # 日志区域

        log_frame = tk.LabelFrame(self.root, text="处理日志", padx=10, pady=10)

        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))


        self.log_text = scrolledtext.ScrolledText(

            log_frame,

            height=10,

            wrap=tk.WORD,

            font=('Consolas', 9)

        )

        self.log_text.pack(fill=tk.BOTH, expand=True)


        # 绑定回车键

        self.root.bind('<Return>', lambda e: self.start_extraction())


    def check_dependencies(self):

        """检查必要的依赖"""

        self.log_message("检查系统依赖...")


        try:

            subprocess.run(['you-get', '--version'], capture_output=True, check=True)

            self.log_message("✓ you-get 已安装")

        except:

            self.log_message("✗ you-get 未安装，请运行: pip install you-get")


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

        self.log_text.insert(tk.END, f"{message}\n")

        self.log_text.see(tk.END)

        self.root.update_idletasks()


    def update_progress(self, progress, status):

        """更新进度条和状态"""

        self.progress_var.set(progress)

        self.status_var.set(status)

        self.root.update_idletasks()


    def get_highest_quality_url(self, url):

        """获取视频的最高音质URL"""

        self.log_message("正在获取最高音质音频信息...")


        try:

            # 使用 you-get 的 JSON 输出获取视频信息

            cmd = ['you-get', '--json', url]

            result = subprocess.run(cmd, capture_output=True, text=False)


            if result.returncode != 0:

                # 如果失败，直接返回原URL，you-get会自动选择最高质量

                self.log_message("无法获取详细信息，将下载最高质量音频")

                return url, "自动选择最高质量"


            # 解码输出

            try:

                stdout_text = result.stdout.decode('utf-8')

            except UnicodeDecodeError:

                stdout_text = result.stdout.decode('gbk', errors='ignore')


            import json

            video_info = json.loads(stdout_text)


            if 'streams' in video_info:

                streams = video_info['streams']


                # 查找最高音质的音频流

                highest_stream = None

                highest_score = -1


                for stream_key, stream_info in streams.items():

                    if isinstance(stream_info, dict):

                        # 给不同音质打分

                        score = 0

                        container = stream_info.get('container', '').lower()

                        quality = stream_info.get('quality', '').lower()


                        # 优先选择音频流（不含视频或纯音频）

                        # flac, aiff, wav, m4a 是无损格式

                        if 'flac' in container or 'aiff' in container or 'wav' in container:

                            score += 1000

                        elif 'm4a' in container or 'mp3' in container:

                            score += 500


                        # 检查是否是音频流（没有 vid 或 video 相关字段）

                        if 'vid' not in stream_key.lower() and 'video' not in stream_key.lower():

                            score += 100


                        # 根据质量描述打分

                        if 'hi-res' in quality or 'hirez' in quality:

                            score += 50

                        if 'lossless' in quality or '无损' in quality:

                            score += 40

                        if '320k' in quality:

                            score += 30

                        if '128k' in quality:

                            score += 10


                        if score > highest_score:

                            highest_score = score

                            highest_stream = {

                                'stream_key': stream_key,

                                'container': stream_info.get('container', 'auto'),

                                'quality': stream_info.get('quality', '自动'),

                                'url': url  # 使用原始URL，you-get会自动选择流

                            }


                if highest_stream:

                    quality_desc = f"{highest_stream['quality']} ({highest_stream['container']})"

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


            # 5. 使用 you-get 下载视频（包含最高音质音频）

            temp_dir = output_path / ".temp_audio_extract"

            temp_dir.mkdir(parents=True, exist_ok=True)


            self.update_progress(50, "下载视频中...")

            self.log_message("开始下载视频（包含最高音质音频）...")


            # 构建you-get命令

            cmd = ['you-get', '--output-dir', str(temp_dir)]


            # 使用Cookie

            if cookie_str:

                cookie_file = temp_dir / "bilibili_cookie.txt"

                with open(cookie_file, 'w', encoding='utf-8') as f:

                    f.write(f"Cookie: {cookie_str}\n")

                cmd.extend(['--cookies', str(cookie_file)])

                self.log_message("✓ 使用B站Cookie进行下载")


            cmd.append(url)


            result = subprocess.run(cmd, capture_output=True, text=True)


            if result.returncode != 0:

                self.log_message("下载失败，尝试不使用Cookie...")

                cmd_no_cookie = ['you-get', '--output-dir', str(temp_dir), url]

                result = subprocess.run(cmd_no_cookie, capture_output=True, text=True)


            if result.returncode != 0:

                raise Exception(f"下载失败: {result.stderr[:200] if result.stderr else '未知错误'}")


            self.log_message("✓ 视频下载完成")


            # 6. 查找下载的文件

            video_path = None

            for ext in ['*.mp4', '*.flv', '*.mkv', '*.avi', '*.m4a']:

                files = list(temp_dir.glob(ext))

                if files:

                    video_path = files[0]

                    break


            if not video_path:

                raise Exception("未找到下载的视频文件")


            self.log_message(f"✓ 找到视频文件: {video_path.name}")


            # 7. 提取音频（最高音质 - 保持原始质量）

            self.update_progress(70, "提取音频...")

            self.log_message("开始提取音频（保持原始最高音质）...")


            file_stem = video_path.stem

            output_file = output_path / f"{file_stem}_最高音质.flac"


            cmd = [

                'ffmpeg',

                '-i', str(video_path),

                '-vn',

                '-c:a', 'flac',

                '-compression_level', '12',

                '-y',

                str(output_file)

            ]


            result = subprocess.run(cmd, capture_output=True, text=True)


            if result.returncode != 0:

                # 如果FLAC提取失败，尝试其他格式

                output_file = output_path / f"{file_stem}_最高音质.mp3"

                cmd = [

                    'ffmpeg',

                    '-i', str(video_path),

                    '-vn',

                    '-c:a', 'libmp3lame',

                    '-b:a', '320k',

                    '-y',

                    str(output_file)

                ]

                result = subprocess.run(cmd, capture_output=True, text=True)


            if result.returncode != 0:

                raise Exception(f"音频提取失败: {result.stderr[:200] if result.stderr else '未知错误'}")


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


        thread = threading.Thread(target=self.extract_audio_thread, daemon=True)

        thread.start()


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