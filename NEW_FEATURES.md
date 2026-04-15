# B站音频提取器 - 新功能说明

## 🎯 优化概述

本项目已优化，实现了用户输入B站视频链接后，先判断该视频可下载的音频格式，再由用户选择所下载格式的功能。

## ✨ 新增功能

### 1. 自动格式检测
- 自动检测视频可下载的音频格式
- 显示可用格式列表供用户选择
- 支持多种格式：1080p、720p、FLV、360p等

### 2. 多种音频质量选择
- **原始质量 (FLAC无损)**：保持源文件最佳质量
- **Hi-Res音质**：FLAC格式，96kHz采样率，24bit位深
- **CD音质**：FLAC格式，44.1kHz采样率，16bit位深
- **高音质MP3**：MP3格式，320kbps比特率
- **标准MP3音质**：MP3格式，128kbps比特率

### 3. 交互式用户界面
- 清晰的格式选择菜单
- 直观的音频质量选项
- 实时显示选择结果

### 4. 命令行参数支持
- `--format, -f`：指定下载格式
- `--quality, -q`：指定输出质量
- `--auto, -a`：自动模式，跳过交互
- `--output, -o`：指定输出目录

## 🚀 使用示例

### 交互模式（新功能）
```bash
python bilibili_audio_extractor.py https://www.bilibili.com/video/BVxxxxx
```

程序会显示：
1. 可下载格式列表，用户选择
2. 音频质量选项，用户选择
3. 开始下载和转换

### 快速指定格式和质量
```bash
python bilibili_audio_extractor.py <URL> --format hd2 --quality hires
```

### 全自动模式
```bash
python bilibili_audio_extractor.py <URL> --auto --format hd2 --quality cd
```

### 指定输出目录
```bash
python bilibili_audio_extractor.py <URL> --output ./my_music
```

## 📝 参数说明

| 参数 | 缩写 | 说明 |
|------|------|------|
| `--format` | `-f` | 指定下载格式 (hd2, hd1, flv, 360p) |
| `--quality` | `-q` | 指定输出质量 (original, hires, cd, mp3_high, mp3_standard) |
| `--auto` | `-a` | 自动模式，跳过用户交互 |
| `--output` | `-o` | 指定输出目录 |
| `--cleanup` | 无 | 清理临时文件 |

## 🔧 技术实现

### 新增方法
- `get_available_audio_formats(url)`：检测可用格式
- `extract_audio_to_flac(video_path, title, quality_choice)`：支持多种质量输出
- `_get_quality_suffix(quality_choice)`：生成文件名后缀

### 改进方法
- `process_url(url, format_choice, quality_choice)`：添加用户交互
- `download_video(url, format_choice)`：支持格式选择
- `main()`：添加命令行参数解析

## 🎨 用户体验改进

1. **智能默认值**：自动选择最佳格式和质量
2. **错误处理**：友好的错误提示和恢复机制
3. **进度反馈**：实时显示处理状态
4. **文件命名**：根据质量自动添加后缀，便于区分

## 📊 测试结果

- ✅ URL验证功能正常
- ✅ 格式检测功能正常
- ✅ 质量选择功能正常
- ✅ 依赖检查功能正常
- ✅ 命令行参数解析正常

## 🔄 向后兼容性

- 保持原有API兼容性
- 支持原有的命令行用法
- 默认行为保持不变

## 🎉 总结

此次优化显著提升了用户体验：
- 用户可以根据需要选择最适合的格式
- 支持多种音频质量输出，满足不同场景需求
- 既保持了交互式的便利性，又提供了自动化的效率
- 完整的命令行参数支持，便于脚本调用和批量处理