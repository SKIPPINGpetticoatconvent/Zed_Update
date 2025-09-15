# Zed Editor 自动更新程序

<div align="center">

[![Build Status](https://github.com/TC999/zed-update/workflows/Build%20Multi-Architecture%20Zed%20Updater/badge.svg)](https://github.com/TC999/zed-update/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

**自动检查、下载和安装 Zed Editor 最新版本的强大工具**

[功能特色](#-功能特色) • [快速开始](#-快速开始) • [架构对比](#-架构对比) • [安装指南](#-安装指南) • [文档](#-文档)

</div>

## 🚀 双架构设计

本项目提供两种实现方案，满足不同需求：

### 🏛️ Legacy 实现（经典版）
- **单体应用架构**：一个可执行文件包含所有功能
- **最小依赖**：只需要 Python + PyQt5
- **兼容性强**：支持较老的系统环境
- **部署简单**：开箱即用

### 🚀 Modern 实现（现代版）
- **微服务架构**：Go 后端 + PyQt5 前端
- **高性能**：Go 提供快速的 API 响应
- **可扩展**：松耦合设计，易于功能扩展
- **现代化**：RESTful API，实时通信

## 📁 项目结构

```
Zed_Update/
├── 📂 legacy/                    # 经典实现
│   ├── main.py                   # 主程序入口
│   ├── gui_launcher.pyw          # GUI 启动器
│   ├── requirements.txt          # Python 依赖
│   ├── install.py                # 安装脚本
│   ├── uninstall.py             # 卸载脚本
│   └── 📂 updater/              # 核心模块
│       ├── gui.py               # GUI 界面
│       ├── updater.py           # 更新逻辑
│       ├── config.py            # 配置管理
│       └── scheduler.py         # 定时任务
│
├── 📂 modern/                   # 现代实现
│   ├── 📂 backend/              # Go 后端服务
│   │   ├── main.go              # HTTP API 服务器
│   │   ├── go.mod               # Go 模块定义
│   │   └── go.sum               # 依赖锁定
│   └── 📂 frontend/             # PyQt5 前端
│       ├── main.py              # GUI 应用程序
│       └── requirements.txt     # Python 依赖
│
├── 📂 scripts/                  # 构建和启动脚本
│   ├── start-legacy.bat/sh      # 启动经典版
│   ├── start-modern.bat/sh      # 启动现代版
│   └── Makefile                 # 构建配置
│
├── 📂 .github/workflows/        # CI/CD 配置
├── 📂 docs/                     # 详细文档
├── start.bat/sh                 # 统一启动入口
└── README.md                    # 本文件
```

## ⚡ 快速开始

### 一键启动

```bash
# Windows
start.bat

# Linux/macOS
chmod +x start.sh
./start.sh
```

启动脚本会自动检测系统环境，提供交互式选择界面：
1. **Legacy 实现** - 经典单体应用
2. **Modern 实现** - 现代微服务架构
3. **自动选择** - 基于系统环境智能选择

### 直接启动特定实现

```bash
# 启动 Legacy 实现
scripts/start-legacy.bat    # Windows
./scripts/start-legacy.sh   # Linux/macOS

# 启动 Modern 实现
scripts/start-modern.bat    # Windows  
./scripts/start-modern.sh   # Linux/macOS
```

## 🎯 功能特色

### 🔄 智能更新
- **自动版本检测**：实时检查 GitHub 最新版本
- **增量下载**：只下载必要的更新文件
- **断点续传**：网络中断后可继续下载
- **校验完整性**：SHA256 校验确保文件安全

### 🎨 现代界面
- **响应式设计**：适配不同屏幕分辨率
- **暗黑主题**：护眼的深色界面
- **多语言支持**：中英文界面切换
- **系统托盘**：最小化到托盘继续运行

### ⚙️ 灵活配置
- **定时检查**：可配置自动检查间隔
- **备份策略**：自动备份旧版本
- **代理支持**：支持 HTTP/HTTPS 代理
- **启动选项**：多种启动和安装模式

### 🛡️ 安全可靠
- **数字签名验证**：验证下载文件的完整性
- **沙箱运行**：隔离的更新环境
- **回滚机制**：更新失败时自动恢复
- **日志审计**：详细的操作日志记录

## 🏗️ 架构对比

| 特性 | Legacy 实现 | Modern 实现 | 说明 |
|------|-------------|-------------|------|
| **架构设计** | 单体应用 | 微服务 | Modern 更易扩展和维护 |
| **性能** | 中等 | 高 | Go 后端提供更快响应 |
| **部署复杂度** | 简单 | 中等 | Legacy 一键部署，Modern 需要两个组件 |
| **系统资源** | 80MB | 120MB | Modern 占用略多内存 |
| **扩展性** | 有限 | 优秀 | Modern 可轻松添加新功能 |
| **兼容性** | 优秀 | 良好 | Legacy 支持更多老系统 |
| **技术栈** | Python + PyQt5 | Go + Python + PyQt5 | Modern 使用更多现代技术 |

## 📋 系统要求

### Legacy 实现
- **操作系统**: Windows 7+, macOS 10.12+, Ubuntu 16.04+
- **Python**: 3.9 或更高版本
- **内存**: 最少 256MB 可用内存
- **存储**: 50MB 可用磁盘空间
- **网络**: 互联网连接（用于检查更新）

### Modern 实现
- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.9 或更高版本
- **Go**: 1.21 或更高版本
- **内存**: 最少 512MB 可用内存
- **存储**: 100MB 可用磁盘空间
- **网络**: 互联网连接（用于检查更新）

## 🔧 安装指南

### 自动安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/TC999/zed-update.git
cd zed-update

# 运行安装脚本
python legacy/install.py
```

### 手动安装

#### Legacy 实现
```bash
cd legacy
pip install -r requirements.txt
python main.py --gui
```

#### Modern 实现
```bash
# 安装后端依赖
cd modern/backend
go mod tidy

# 安装前端依赖
cd ../frontend
pip install -r requirements.txt

# 启动后端（新终端）
cd ../backend
go run main.go

# 启动前端
cd ../frontend
python main.py
```

## 🔌 API 文档（Modern 实现）

Modern 实现提供完整的 RESTful API：

### 健康检查
```http
GET /api/v1/health
```

### 系统信息
```http
GET /api/v1/system/info
GET /api/v1/system/status
```

### 更新管理
```http
GET  /api/v1/updates/check
POST /api/v1/updates/download
POST /api/v1/updates/install
```

### Zed 管理
```http
GET  /api/v1/zed/version
POST /api/v1/zed/start
POST /api/v1/zed/backup
```

### 配置管理
```http
GET  /api/v1/config
POST /api/v1/config
```

详细 API 文档请参考 [docs/API.md](docs/API.md)

## 🔨 开发指南

### 构建项目

```bash
# 使用 Makefile（推荐）
make help                    # 查看所有可用命令
make all                     # 构建所有组件
make legacy                  # 构建 Legacy 实现
make modern                  # 构建 Modern 实现
make cross-compile          # 跨平台编译

# 或使用构建脚本
scripts/build-all.sh        # 构建所有平台版本
```

### 运行测试

```bash
# 单元测试
make test                   # 运行所有测试
make test-legacy           # 测试 Legacy 实现
make test-modern           # 测试 Modern 实现

# 集成测试
python test_integration.py

# 性能测试
make benchmark
```

### 代码规范

- **Go**: 遵循 `gofmt` 和 `go vet` 标准
- **Python**: 遵循 PEP 8 编码规范
- **提交**: 使用 [Conventional Commits](https://conventionalcommits.org/) 格式

## 📚 文档

- [📖 详细使用说明](docs/USER_GUIDE.md)
- [🏗️ 架构设计文档](docs/ARCHITECTURE.md)
- [🔧 开发者指南](docs/DEVELOPER.md)
- [🚀 部署指南](docs/DEPLOYMENT.md)
- [🔌 API 参考](docs/API.md)
- [❓ 常见问题](docs/FAQ.md)
- [🐛 故障排除](docs/TROUBLESHOOTING.md)

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 贡献方式
1. **Bug 报告**: 在 [Issues](https://github.com/TC999/zed-update/issues) 中报告问题
2. **功能请求**: 提出新功能建议
3. **代码贡献**: 提交 Pull Request
4. **文档改进**: 完善项目文档
5. **测试**: 帮助测试新版本

### 开发流程
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📊 项目状态

### 版本历史
- **v2.0.0** - 添加 Modern 微服务架构
- **v1.5.0** - 增强 Legacy 实现功能
- **v1.0.0** - 初始 Legacy 实现发布

### 开发计划
- [ ] Web 管理界面
- [ ] Docker 容器化部署
- [ ] 移动端应用支持
- [ ] 插件系统
- [ ] 多仓库源支持

## 🆘 获取帮助

### 社区支持
- 💬 [GitHub Discussions](https://github.com/TC999/zed-update/discussions) - 社区讨论
- 🐛 [GitHub Issues](https://github.com/TC999/zed-update/issues) - Bug 报告和功能请求
- 📧 [Email](mailto:support@zed-update.com) - 直接联系

### 紧急支持
如果遇到紧急问题，请：
1. 查看 [故障排除指南](docs/TROUBLESHOOTING.md)
2. 搜索 [已知问题](https://github.com/TC999/zed-update/issues)
3. 在 Issues 中创建详细的错误报告

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🏆 致谢

感谢以下项目和贡献者：

- [Zed Editor](https://zed.dev/) - 优秀的代码编辑器
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的 GUI 框架
- [Go](https://golang.org/) - 高效的后端语言
- [所有贡献者](https://github.com/TC999/zed-update/contributors) - 感谢每一位贡献者

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个 Star！⭐**

Made with ❤️ by [Zed Update Team](https://github.com/TC999/zed-update)

</div>