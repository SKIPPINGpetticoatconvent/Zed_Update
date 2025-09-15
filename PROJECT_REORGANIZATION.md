# Zed Update Manager - 项目重组说明

本文档详细说明了 Zed Update Manager 项目的重组过程和新的文件夹结构。

## 🔄 重组目标

将项目从单一实现重组为支持两种架构的多实现项目：
1. **Legacy 实现** - 原有的 PyQt5 单体应用
2. **Modern 实现** - 新的 Go 后端 + PyQt5 前端微服务架构

## 📁 新的项目结构

### 完整目录树
```
Zed_Update/
├── 📂 legacy/                        # 经典实现目录
│   ├── main.py                       # 主程序入口
│   ├── gui_launcher.pyw              # GUI 启动器
│   ├── install.py                    # 安装脚本
│   ├── uninstall.py                  # 卸载脚本
│   ├── setup.py                      # 打包配置
│   ├── requirements.txt              # Python 依赖
│   └── 📂 updater/                   # 核心模块
│       ├── __init__.py               # 包初始化
│       ├── gui.py                    # GUI 界面模块
│       ├── updater.py                # 更新逻辑模块
│       ├── config.py                 # 配置管理模块
│       ├── scheduler.py              # 定时任务模块
│       └── encoding_utils.py         # 编码工具模块
│
├── 📂 modern/                        # 现代实现目录
│   ├── 📂 backend/                   # Go 后端服务
│   │   ├── main.go                   # HTTP API 服务器
│   │   ├── go.mod                    # Go 模块定义
│   │   └── go.sum                    # 依赖版本锁定
│   └── 📂 frontend/                  # PyQt5 前端
│       ├── main.py                   # GUI 应用程序
│       └── requirements.txt          # Python 依赖
│
├── 📂 scripts/                       # 构建和启动脚本
│   ├── start-legacy.bat             # Windows Legacy 启动脚本
│   ├── start-legacy.sh              # Linux/macOS Legacy 启动脚本
│   ├── start-modern.bat             # Windows Modern 启动脚本
│   ├── start-modern.sh              # Linux/macOS Modern 启动脚本
│   └── Makefile                      # 构建配置文件
│
├── 📂 .github/                       # GitHub 配置
│   └── 📂 workflows/                 # GitHub Actions 工作流
│       ├── build.yml                 # 原有构建工作流
│       ├── build-windows.yml         # Windows 专用构建
│       └── build-multi-arch.yml      # 多架构构建工作流
│
├── 📂 docs/                          # 文档目录
├── 📂 examples/                      # 示例文件
├── 📂 resources/                     # 资源文件
├── 📂 tests/                         # 测试文件
├── 📂 .conda/                        # Conda 环境配置
│
├── start.bat                         # Windows 统一启动脚本
├── start.sh                          # Linux/macOS 统一启动脚本
├── config.json                       # 主配置文件
├── config.example.json              # 配置示例文件
├── requirements.txt                  # 项目级 Python 依赖
├── ZedUpdater.spec                   # PyInstaller 规格文件
│
├── README.md                         # 项目主说明文档
├── PROJECT_STRUCTURE.md             # 项目结构说明
├── PROJECT_REORGANIZATION.md        # 本文档
├── INTEGRATION_README.md            # 集成说明文档
├── GUI_MIGRATION_README.md          # GUI 移植说明
├── QUICK_START.md                   # 快速开始指南
├── CHANGELOG.md                     # 更新日志
├── VERSION_CHECK_INFO.md            # 版本检查信息
└── LICENSE                          # 开源许可证
```

## 📦 文件移动映射

### Legacy 实现文件移动
```
原位置                    →  新位置
main.py                  →  legacy/main.py
gui_launcher.pyw          →  legacy/gui_launcher.pyw
install.py               →  legacy/install.py
uninstall.py             →  legacy/uninstall.py
setup.py                 →  legacy/setup.py
requirements.txt         →  legacy/requirements.txt
updater/                 →  legacy/updater/
```

### Modern 实现文件移动
```
原位置                    →  新位置
backend/                 →  modern/backend/
frontend/                →  modern/frontend/
```

### 脚本文件移动
```
原位置                    →  新位置
start.bat                →  scripts/start-modern.bat
start.sh                 →  scripts/start-modern.sh
Makefile                 →  scripts/Makefile
(新创建)                  →  scripts/start-legacy.bat
(新创建)                  →  scripts/start-legacy.sh
```

## 🚀 新的启动方式

### 1. 统一启动入口
```bash
# Windows
start.bat

# Linux/macOS
./start.sh
```
提供交互式选择界面，用户可以选择启动哪种实现。

### 2. 直接启动特定实现
```bash
# Legacy 实现
scripts/start-legacy.bat    # Windows
scripts/start-legacy.sh     # Linux/macOS

# Modern 实现
scripts/start-modern.bat    # Windows
scripts/start-modern.sh     # Linux/macOS
```

## 🔧 GitHub Actions 工作流更新

### 新增工作流文件
- `build-multi-arch.yml` - 支持两种架构的综合构建工作流

### 工作流特性
1. **变更检测**: 只在相关文件变化时构建对应的实现
2. **多平台构建**: 支持 Windows、Linux、macOS
3. **多版本支持**: 支持多个 Python 和 Go 版本
4. **安全扫描**: 集成安全漏洞扫描
5. **自动发布**: 根据 Release 自动构建和发布

### 构建矩阵
```yaml
Legacy 实现:
  - OS: ubuntu-latest, windows-latest, macos-latest
  - Python: 3.9, 3.10, 3.11, 3.12

Modern 实现:
  - Backend: Go 1.21 (跨平台编译)
  - Frontend: 同 Legacy 实现的构建矩阵
```

## 🎯 重组优势

### 1. 清晰的代码组织
- **职责分离**: Legacy 和 Modern 实现完全分离
- **代码复用**: 公共脚本和配置统一管理
- **维护便利**: 每种实现独立维护，互不影响

### 2. 灵活的部署选择
- **按需部署**: 用户可以选择只部署需要的实现
- **渐进升级**: 可以从 Legacy 平滑升级到 Modern
- **环境适配**: 不同环境选择最适合的实现

### 3. 强化的构建流程
- **智能构建**: 只构建有变更的部分
- **多平台支持**: 一次构建，多平台可用
- **质量保证**: 集成测试和安全扫描

## 📚 相关文档

### 使用文档
- `README.md` - 项目总览和快速开始
- `QUICK_START.md` - 详细的快速开始指南
- `INTEGRATION_README.md` - 集成架构说明
- `GUI_MIGRATION_README.md` - GUI 移植详情

### 开发文档
- `PROJECT_STRUCTURE.md` - 详细的项目结构说明
- `docs/ARCHITECTURE.md` - 架构设计文档
- `docs/DEVELOPER.md` - 开发者指南
- `docs/API.md` - Modern 实现的 API 文档

## 🔄 迁移指南

### 从旧版本迁移
1. **备份配置**: 保存现有的 `config.json` 文件
2. **更新代码**: 拉取最新的项目代码
3. **选择实现**: 决定使用 Legacy 还是Modern 实现
4. **重新安装**: 根据选择的实现重新安装依赖
5. **恢复配置**: 将备份的配置文件复制到对应位置

### 配置文件兼容性
- Legacy 实现完全兼容原有的 `config.json` 格式
- Modern 实现支持大部分原有配置，新增了一些现代化选项

## ⚠️ 注意事项

### 破坏性变更
- 直接启动脚本路径发生变化
- 某些内部 API 可能不兼容

### 兼容性保证
- Legacy 实现保持 100% 向后兼容
- 配置文件格式保持兼容
- 用户数据和日志位置不变

### 升级建议
1. **测试环境先行**: 在测试环境中验证新版本
2. **备份重要数据**: 升级前备份配置和日志
3. **渐进式升级**: 可以先使用 Legacy 实现，再考虑 Modern

## 🎉 重组成果

通过这次重组，Zed Update Manager 项目实现了：

1. **架构现代化**: 从单体应用演进到微服务架构
2. **用户选择权**: 用户可以根据需求选择最适合的实现
3. **开发效率**: 清晰的代码结构提高了开发和维护效率
4. **部署灵活性**: 支持多种部署方式和环境
5. **未来扩展性**: 为后续功能扩展奠定了良好基础

---

**更新日期**: 2024-12-19  
**文档版本**: 1.0.0  
**适用版本**: Zed Update Manager v2.0.0+