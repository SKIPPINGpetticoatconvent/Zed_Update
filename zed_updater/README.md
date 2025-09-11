# Zed Updater

## 项目概述

Zed Updater 是一个全面的自动更新解决方案，专为 Zed 编辑器设计。本项目通过定期检查、自动下载和安装最新版本，确保您始终使用最新版本的 Zed 编辑器。

## 重构说明

这个项目是对原有 Zed 自动更新工具的完整重构，采用了更加模块化和可维护的设计：

- **模块化架构**：将功能拆分为核心、UI、工具三大模块
- **改进的错误处理**：更加健壮的异常捕获和日志机制
- **增强的用户界面**：更友好的图形界面和系统托盘集成
- **更好的代码组织**：遵循 Python 最佳实践的项目结构

## 项目结构

```
zed_updater/
├── zed_updater/                # 主源代码包
│   ├── core/                   # 核心功能模块
│   │   ├── updater.py          # 更新核心逻辑
│   │   ├── config.py           # 配置管理
│   │   └── scheduler.py        # 定时调度
│   ├── ui/                     # 用户界面相关
│   │   ├── gui.py              # 主GUI窗口
│   │   ├── dialogs.py          # 对话框
│   │   └── tray.py             # 系统托盘
│   ├── utils/                  # 工具函数
│   │   ├── encoding.py         # 编码处理
│   │   ├── version.py          # 版本比较
│   │   ├── platform.py         # 平台检测
│   │   └── network.py          # 网络请求
│   └── constants.py            # 常量定义
├── scripts/                    # 辅助脚本
│   ├── install.py              # 安装脚本
│   └── run.py                  # 运行脚本
├── resources/                  # 资源文件
│   └── icons/                  # 图标文件
├── docs/                       # 文档
```

## 核心模块

### updater.py

负责版本检查、下载和安装的核心逻辑。

### config.py

处理配置文件的读取、写入和验证，支持导入/导出配置。

### scheduler.py

管理定时检查任务，支持按小时间隔和指定时间点执行。

## 工具模块

### encoding.py

处理文本编码相关的功能，确保跨平台兼容性。

### version.py

提供版本号解析和比较功能，支持多种版本格式。

### platform.py

提供平台特定的功能，如进程管理和开机自启动。

### network.py

处理网络请求、下载和代理设置。

## UI 模块

### gui.py

主界面实现，包含版本信息显示、手动更新等功能。

### dialogs.py

各种对话框，如设置、更新进度、日志查看器等。

### tray.py

系统托盘集成，支持后台运行和快速访问常用功能。

## 安装与使用

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 运行安装向导：

```bash
python scripts/install.py
```

3. 启动程序：

```bash
python scripts/run.py
```

或使用GUI模式：

```bash
python scripts/run.py --gui
```

## 开发与贡献

欢迎提交问题报告和功能请求！

## 许可证

本项目采用 MIT 许可证