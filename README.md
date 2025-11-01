# Zed Editor Auto Updater v2.0

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**简化的 Zed Editor 自动更新程序**

[🚀 快速开始](#快速开始) • [✨ 特性](#特性) • [📦 安装](#安装) • [💻 使用](#使用) • [🔧 配置](#配置)

</div>

## 项目概述

Zed Editor Auto Updater v2.0 是一个完全重构的简化版本，采用统一的单体架构，提供图形界面和命令行操作。该版本移除了复杂的微服务架构，专注于核心更新功能的稳定性和易用性。

## 主要特性

### 🔄 智能更新
- **自动版本检测**: 实时检查 GitHub 最新版本
- **增量下载**: 只下载必要的更新文件
- **断点续传**: 网络中断后可继续下载
- **安全备份**: 自动备份旧版本，支持回滚

### 🎨 简洁界面
- **响应式设计**: 自适应不同屏幕分辨率
- **中文界面**: 完全中文化的用户界面
- **进度显示**: 实时显示下载和安装进度
- **操作日志**: 详细的操作记录

### 🛡️ 安全可靠
- **权限检查**: 确保必要的文件权限
- **备份机制**: 自动备份旧版本
- **回滚支持**: 更新失败时自动恢复
- **进程管理**: 安全停止和启动 Zed 进程

### ⚙️ 灵活配置
- **定时检查**: 可配置自动检查间隔
- **代理支持**: 支持 HTTP/HTTPS 代理
- **网络重试**: 自动重试失败的下载
- **自定义路径**: 支持自定义安装和备份路径

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/TC999/zed-update.git
cd zed-update

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

### 使用

#### 图形界面
```bash
# 启动图形界面
zed-updater-gui

# 或者
python -m zed_updater.gui_main
```

#### 命令行
```bash
# 检查更新
zed-updater --check

# 更新到最新版本
zed-updater --update

# 查看当前版本
zed-updater --current-version

# 显示版本信息
zed-updater --version
```

## 安装选项

### 从 PyPI 安装 (即将推出)
```bash
pip install zed-updater
```

### 从源码安装
```bash
git clone https://github.com/TC999/zed-update.git
cd zed-update
pip install -e .
```

### 便携版
下载发布版中的 `ZedUpdater.exe` 即可直接使用，无需安装。

## 配置

配置文件位置: `config.json`

```json
{
  "zed_install_path": "D:\\Zed.exe",
  "github_repo": "TC999/zed-loc",
  "auto_check_enabled": true,
  "check_interval_hours": 24,
  "backup_enabled": true,
  "backup_count": 3,
  "download_timeout": 300,
  "retry_count": 3,
  "proxy_enabled": false,
  "proxy_url": ""
}
```

### 主要配置项

- `zed_install_path`: Zed.exe 的完整路径
- `github_repo`: GitHub 仓库名称 (默认: TC999/zed-loc)
- `auto_check_enabled`: 是否启用自动检查更新
- `check_interval_hours`: 自动检查间隔 (小时)
- `backup_enabled`: 是否启用自动备份
- `backup_count`: 保留的备份文件数量

## 架构说明

### 简化架构
```
src/zed_updater/
├── core/              # 核心业务逻辑
│   ├── config.py      # 配置管理
│   └── updater.py     # 统一更新器
├── utils/             # 工具函数
│   └── logger.py      # 日志系统
├── cli.py            # 命令行入口
└── gui_main.py       # 图形界面入口
```

### 设计原则
1. **单体内核**: 所有核心功能集成在一个统一模块中
2. **模块化设计**: 清晰的功能分离，便于维护
3. **向后兼容**: 保持与旧版本的配置兼容
4. **简化依赖**: 减少不必要的第三方依赖

## 开发

### 构建可执行文件
```bash
# 使用 PyInstaller 构建
pyinstaller ZedUpdater.spec

# 构建产物
# dist/ZedUpdater.exe
```

### 运行测试
```bash
# 安装测试依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

## 文档

- [用户指南](docs/USER_GUIDE.md)
- [开发者文档](docs/DEVELOPER.md)
- [API 参考](docs/API.md)

## 变更日志

### v2.0.0 (2025-11-01)
- **完全重构**: 从多架构简化为单体架构
- **移除复杂度**: 删除微服务和Go后端
- **统一接口**: 单一更新器类处理所有操作
- **简化配置**: 移除不必要的配置选项
- **改进GUI**: 更简洁的用户界面
- **优化依赖**: 大幅减少第三方依赖

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 致谢

- [Zed Editor](https://zed.dev/) - 优秀的代码编辑器
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的 GUI 框架

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个 Star！⭐**

Made with ❤️ by [Zed Update Team](https://github.com/TC999/zed-update)

</div>