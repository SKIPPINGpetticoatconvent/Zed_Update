# Zed Editor 自动更新程序 - 项目结构说明

## 项目概述

这是一个用于自动更新 Zed Editor 的 Python 程序，支持图形界面和命令行操作。

## 目录结构

```
D:\Vs\Zed_Update/
├── .github/
│   └── workflows/
│       └── build-windows.yml      # GitHub Actions 构建工作流
├── docs/                          # 项目文档目录
├── examples/                      # 使用示例
├── resources/                     # 资源文件（图标等）
├── scripts/                       # 辅助脚本
├── tests/                         # 测试文件
├── updater/                       # 核心更新模块
│   ├── __init__.py               # 包初始化文件
│   ├── config.py                 # 配置管理模块
│   ├── encoding_utils.py         # 编码处理工具
│   ├── gui.py                    # GUI 界面模块
│   ├── scheduler.py              # 任务调度模块
│   └── updater.py                # 核心更新逻辑
├── .gitattributes                 # Git 属性配置
├── .gitignore                     # Git 忽略文件配置
├── CHANGELOG.md                   # 版本更新记录
├── LICENSE                        # 许可证文件
├── PROJECT_STRUCTURE.md           # 项目结构说明（本文件）
├── QUICK_START.md                 # 快速开始指南
├── README.md                      # 项目说明文档
├── VERSION_CHECK_INFO.md          # 版本检查信息
├── ZedUpdater.spec                # PyInstaller 打包配置
├── config.example.json            # 配置文件模板
├── gui_launcher.pyw               # GUI 启动器（无控制台窗口）
├── install.py                     # 安装脚本
├── main.py                        # 主程序入口
├── requirements.txt               # Python 依赖列表
├── setup.py                       # Python 包安装配置
└── uninstall.py                   # 卸载脚本
```

## 核心文件说明

### 主要入口文件
- **main.py**: 主程序入口，支持 GUI 和命令行模式
- **gui_launcher.pyw**: GUI 专用启动器，无控制台窗口

### 核心模块 (updater/)
- **updater.py**: 核心更新逻辑，处理版本检查和文件下载
- **gui.py**: PyQt5 图形用户界面
- **config.py**: 配置文件管理
- **scheduler.py**: 定时任务调度
- **encoding_utils.py**: 字符编码处理工具

### 配置文件
- **config.example.json**: 配置文件模板
- **ZedUpdater.spec**: PyInstaller 打包规格文件
- **requirements.txt**: Python 依赖包列表

### 文档文件
- **README.md**: 项目主要说明文档
- **QUICK_START.md**: 快速开始指南
- **CHANGELOG.md**: 版本更新日志
- **VERSION_CHECK_INFO.md**: 版本检查机制说明

### 构建配置
- **.github/workflows/build-windows.yml**: GitHub Actions 自动构建配置

## 使用方式

### 开发环境运行
```bash
# 安装依赖
pip install -r requirements.txt

# 运行 GUI 模式
python main.py

# 运行命令行更新
python main.py --update

# 显示帮助
python main.py --help
```

### 打包构建
```bash
# 使用 PyInstaller 构建
pyinstaller --clean ZedUpdater.spec
```

### 构建产物
- **dist/ZedUpdater.exe**: GUI 版本（无控制台窗口）
- **dist/ZedUpdater-Console.exe**: 控制台版本（显示控制台）

## 项目特点

### 已移除的文件/目录
在重构过程中，以下不必要的文件已被删除：
- `build/`, `dist/`, `.venv/`: 构建产物和虚拟环境
- `temp_downloads/`: 临时下载目录
- `zed_updater/`: 重复的包结构
- 各种重复的批处理启动脚本
- 临时和调试文件

### 优化改进
1. **简化项目结构**: 移除重复和不必要的文件
2. **统一构建配置**: 使用单一的 PyInstaller spec 文件
3. **优化 GitHub 工作流**: 简化构建流程，减少复杂性
4. **标准化依赖管理**: 清理 requirements.txt，移除注释
5. **完善 .gitignore**: 确保不跟踪构建产物和临时文件

## 开发规范

### 代码风格
- 使用 UTF-8 编码
- 遵循 PEP 8 代码规范
- 函数和类添加适当的文档字符串

### 版本管理
- 使用语义化版本号 (Semantic Versioning)
- 在 CHANGELOG.md 中记录版本更新

### 构建发布
- 通过 GitHub Actions 自动构建
- 支持手动触发版本发布
- 生成多种分发格式（单文件、便携包等）

## 依赖说明

### 主要依赖
- **PyQt5**: GUI 框架
- **requests**: HTTP 请求库
- **schedule**: 任务调度
- **psutil**: 系统进程管理
- **pywin32**: Windows 系统 API
- **python-dateutil**: 日期时间处理
- **chardet**: 编码检测
- **pyinstaller**: 打包工具

### 系统要求
- Python 3.7+
- Windows 10/11 (主要目标平台)
- 网络连接用于下载更新

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

请确保在提交前：
- 运行测试
- 更新相关文档
- 遵循代码规范