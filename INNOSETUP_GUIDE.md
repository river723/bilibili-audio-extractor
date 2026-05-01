# Inno Setup 安装程序指南

## 📦 概述

从 v2.3.0 开始，本项目支持创建 Inno Setup 安装程序。这比单独的 EXE 文件更具有以下优势：

- ✅ **获得 Windows 信任** - 安装程序通常不会触发 SmartScreen 警告
- ✅ **自动卸载** - 提供完整的卸载程序
- ✅ **开始菜单集成** - 自动创建快捷方式
- ✅ **专业外观** - 标准的 Windows 安装向导
- ✅ **版本管理** - 支持自动版本检测和升级

## 🚀 如何使用

### 不安装 Inno Setup（默认行为）

如果不安装 Inno Setup，打包流程会：
1. ✅ 正常生成 EXE 文件
2. ✅ 创建便携版 ZIP 包
3. ⏭️ 跳过 Inno Setup 安装程序编译

运行命令：
```bash
cd bilibili-audio-extractor
python build_package.py
```

### 安装 Inno Setup 来生成安装程序

#### 方式1：官网下载（推荐）

1. 访问 [Inno Setup 官网](https://jrsoftware.org/isinfo.php)
2. 下载最新版本（推荐 6.x）
3. 运行安装程序，选择默认安装位置
4. 重新运行打包命令

#### 方式2：使用 Chocolatey（快速）

```bash
choco install innosetup
```

#### 方式3：使用 Windows Package Manager

```bash
winget install --id InnoSetup.InnoSetup
```

### 验证安装

安装完成后，验证 ISCC 编译器：

```bash
# Windows CMD
where iscc.exe

# PowerShell
Get-Command iscc.exe
```

应该看到类似输出：
```
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
```

## 📊 打包流程

安装 Inno Setup 后，完整打包命令生成的输出：

```
output/
├─ B站音频提取器_Setup.exe          # 安装程序（~17MB）
├─ Bilibili_Audio_Extractor_v2.3.0_Portable.zip  # 便携版（~16MB）
└─ setup.iss                        # Inno Setup 配置脚本（可用于自定义）
```

## 🔧 自定义安装程序

如果想自定义安装程序的外观和功能，可以编辑生成的 `setup.iss` 文件：

```bash
# 编辑配置
notepad output/setup.iss

# 手动编译
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" output/setup.iss
```

### 常见自定义选项

**改变安装目录**
```ini
DefaultDirName={autopf}\My Audio Extractor
```

**添加许可协议**
```ini
LicenseFile=LICENSE
```

**改变开始菜单名称**
```ini
DefaultGroupName=My Audio Tools
```

## 🎯 用户体验对比

### 方式1：单独 EXE（当前）
- ❌ 首次运行显示 SmartScreen 警告
- ✅ 用户需点击"更多信息" → "仍要运行"
- ✅ 无需安装，直接运行

### 方式2：Inno Setup 安装程序（推荐）
- ✅ 不显示 SmartScreen 警告
- ✅ 专业的安装向导
- ✅ 自动创建卸载程序
- ✅ 集成到系统

## ⚙️ 打包脚本细节

`build_package.py` 中的 Inno Setup 支持是**可选的**，具体工作流程：

1. **检查 ISCC.exe**
   - 尝试多个可能的安装位置
   - 如果未找到，只提示用户，不中断流程

2. **生成 .iss 脚本**
   - 从版本号和应用名动态生成
   - 自动包含 EXE、依赖库和文档

3. **编译安装程序**
   - 调用 ISCC.exe 编译
   - 输出 Setup.exe

4. **生成两种格式**
   - ZIP 便携版（总是生成）
   - Inno Setup 安装程序（ISCC 可用时）

## 📝 常见问题

**Q: 必须安装 Inno Setup 吗？**  
A: 不需要。不安装也能正常打包，只是无法生成 Setup.exe。

**Q: Setup.exe 的大小为什么和 EXE 差不多？**  
A: Setup.exe 包含了完整的程序和依赖库，大小相近是正常的。

**Q: 如何在 CI/CD 中使用？**  
A: 在 GitHub Actions 或 GitLab CI 中安装 Inno Setup，流程会自动生成 Setup.exe。

**Q: 能否创建便携版本（无需安装）？**  
A: 可以，项目仍然生成 ZIP 便携版，用户可选择直接运行或安装。

## 📦 依赖

- **Inno Setup 5.x 或 6.x**
  - 可选（自动检测）
  - 不影响基本打包功能

## 🔗 相关资源

- [Inno Setup 官网](https://jrsoftware.org/)
- [Inno Setup 文档](https://jrsoftware.org/isdocs/)
- [ISS 脚本参考](https://jrsoftware.org/isdocs/index.php?topic=scriptreference)

## 💡 建议

- 对普通用户推荐使用 Setup.exe
- 对高级用户推荐便携版 ZIP
- 可同时提供两种版本供用户选择
