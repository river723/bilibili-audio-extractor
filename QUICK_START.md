# 快速开始指南

## 🎯 核心功能
用户输入B站视频链接后，程序会：
1. 自动检测可下载的音频格式
2. 显示格式选项供用户选择
3. 显示音频质量选项供用户选择
4. 下载并转换为用户指定的格式

## 🚀 快速使用

### 方式1：交互式（推荐）
```bash
python bilibili_audio_extractor.py <视频URL>
```

程序会引导你完成选择过程。

### 方式2：快速指定
```bash
# 下载最高质量，输出Hi-Res音质
python bilibili_audio_extractor.py <URL> --format hd2 --quality hires

# 下载标准质量，输出CD音质
python bilibili_audio_extractor.py <URL> --format hd1 --quality cd

# 下载并输出高音质MP3
python bilibili_audio_extractor.py <URL> --quality mp3_high
```

### 方式3：全自动
```bash
# 完全自动处理，无需交互
python bilibili_audio_extractor.py <URL> --auto --format hd2 --quality original
```

## 📋 格式选项

| 格式 | 说明 |
|------|------|
| `hd2` | 1080p (MP4, 高质量) |
| `hd1` | 720p (MP4, 标准质量) |
| `flv` | FLV格式 (高质量) |
| `360p` | 360p (低质量，免登录) |

## 🎵 音质选项

| 质量 | 说明 | 文件格式 |
|------|------|----------|
| `original` | 原始质量 (无损) | FLAC |
| `hires` | Hi-Res音质 | FLAC (96kHz, 24bit) |
| `cd` | CD音质 | FLAC (44.1kHz, 16bit) |
| `mp3_high` | 高音质MP3 | MP3 (320kbps) |
| `mp3_standard` | 标准MP3 | MP3 (128kbps) |

## 💡 实用技巧

### 获取帮助
```bash
python bilibili_audio_extractor.py --help
```

### 清理临时文件
```bash
python bilibili_audio_extractor.py --cleanup
```

### 指定输出目录
```bash
python bilibili_audio_extractor.py <URL> --output ./音乐
```

### 常用组合
```bash
# 最高质量无损音频
python bilibili_audio_extractor.py <URL> -f hd2 -q original

# 高质量MP3（适合播放）
python bilibili_audio_extractor.py <URL> -q mp3_high

# CD音质（平衡质量与大小）
python bilibili_audio_extractor.py <URL> -q cd
```

## 🔍 故障排除

### 依赖问题
如果出现依赖错误，请确保已安装：
- FFmpeg
- you-get

### 网络问题
- 某些高质量格式可能需要登录
- 尝试使用`360p`格式避免登录限制

### 编码问题
- 确保系统支持UTF-8编码
- 如遇乱码，可尝试在英文环境下运行

## 🎓 示例

```bash
# 示例1：交互式使用
python bilibili_audio_extractor.py https://www.bilibili.com/video/BV1Hs4y1B7T2

# 示例2：快速获取Hi-Res音质
python bilibili_audio_extractor.py https://www.bilibili.com/video/BV1Hs4y1B7T2 -f hd2 -q hires -o ./HiRes音乐

# 示例3：批量处理（在脚本中使用）
python bilibili_audio_extractor.py <URL> --auto --format hd1 --quality mp3_high
```

## 📞 获取帮助

运行以下命令查看更多选项：
```bash
python bilibili_audio_extractor.py --help
```

查看新功能详情：
```bash
python demo_new_features.py
```