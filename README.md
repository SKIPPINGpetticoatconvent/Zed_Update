# Zed Editor Auto Updater v2.1.0

<div align="center">

[![Build Status](https://github.com/TC999/zed-update/workflows/Build/badge.svg)](https://github.com/TC999/zed-update/actions)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/TC999/zed-update/branch/main/graph/badge.svg)](https://codecov.io/gh/TC999/zed-update)

**现代化 Zed Editor 自动更新程序**

[🚀 快速开始](#-快速开始) • [⚡ 特性](#-特性) • [📦 安装](#-安装) • [📚 文档](#-文档) • [🤝 贡献](#-贡献)

</div>

## 🎯 项目概述

Zed Editor Auto Updater 是一个现代化的自动更新程序，专为 Zed Editor 设计，支持图形界面和命令行操作。该项目采用模块化架构，既保持了 Legacy 实现的兼容性，又提供了 Modern 微服务实现的新功能。

## 🏗️ 架构设计

### 双架构实现
- **Legacy 实现**: 经典的单体 PyQt5 应用，部署简单
- **Modern 实现**: Go 后端 + PyQt5 前端的微服务架构，性能更佳

### 模块化设计
```
src/zed_updater/
├── core/           # 核心业务逻辑
├── gui/            # 图形界面组件
├── services/       # 外部服务集成
├── utils/          # 工具函数
└── cli.py         # 命令行接口
```

## ⚡ 主要特性

### 🔄 智能更新
- **自动版本检测**: 实时检查 GitHub 最新版本
- **增量下载**: 只下载必要的更新文件
- **断点续传**: 网络中断后可继续下载
- **完整性校验**: SHA256 校验确保文件安全

### 🎨 现代界面
- **响应式设计**: 自适应不同屏幕分辨率
- **深色主题**: 护眼的深色界面
- **多语言支持**: 中英文界面切换
- **系统托盘**: 最小化到托盘继续运行

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

## 🚀 快速开始

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
```bash
# 启动图形界面
zed-updater-gui

# 命令行检查更新
zed-updater --check

# 命令行更新
zed-updater --update

# 显示版本信息
zed-updater --version
```

## 📦 安装选项

### 从 PyPI 安装
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
下载发布版中的 `zed-updater.exe` 即可直接使用，无需安装。

## 🔧 配置

配置文件位置: `config.json`

```json
{
  "zed_install_path": "D:\\Zed.exe",
  "github_repo": "TC999/zed-loc",
  "auto_check_enabled": true,
  "check_interval_hours": 24,
  "backup_enabled": true,
  "backup_count": 3,
  "proxy_enabled": false,
  "proxy_url": "",
  "language": "zh_CN",
  "log_level": "INFO"
}
```

## 📚 文档

- [详细使用指南](docs/USER_GUIDE.md)
- [开发者文档](docs/DEVELOPER.md)
- [API 参考](docs/API.md)
- [故障排除](docs/TROUBLESHOOTING.md)
- [贡献指南](CONTRIBUTING.md)

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov=zed_updater --cov-report=html

# 运行特定测试
pytest tests/unit/test_config.py
```

## 🤝 贡献

我们欢迎各种形式的贡献！

### 开发流程
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范
- 使用 `black` 格式化代码
- 使用 `flake8` 检查代码质量
- 添加适当的类型注解
- 为新功能编写测试

## 🐛 问题报告

如果您遇到问题，请：

1. 查看[故障排除指南](docs/TROUBLESHOOTING.md)
2. 在 [Issues](https://github.com/TC999/zed-update/issues) 中搜索相似问题
3. 创建详细的问题报告，包括：
   - 操作系统版本
   - Python 版本
   - 错误信息和日志
   - 重现步骤

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Zed Editor](https://zed.dev/) - 优秀的代码编辑器
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的 GUI 框架
- [所有贡献者](https://github.com/TC999/zed-update/contributors)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个 Star！⭐**

Made with ❤️ by [Zed Update Team](https://github.com/TC999/zed-update)

</div>