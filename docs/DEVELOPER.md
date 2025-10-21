# Zed Editor Auto Updater - 开发者文档

## 项目结构

```
src/zed_updater/
├── __init__.py          # 包初始化
├── cli.py               # 命令行接口
├── gui_main.py          # GUI 主入口
├── core/                # 核心模块
│   ├── __init__.py
│   ├── config.py        # 配置管理
│   ├── updater.py       # 更新逻辑
│   ├── scheduler.py     # 定时任务
│   └── exceptions.py    # 自定义异常
├── gui/                 # GUI 组件
│   ├── __init__.py
│   ├── main_window.py   # 主窗口
│   ├── updater_gui.py   # 更新界面
│   ├── settings_dialog.py # 设置对话框
│   └── system_tray.py   # 系统托盘
├── services/            # 外部服务
│   ├── __init__.py
│   ├── github_api.py    # GitHub API 客户端
│   ├── system_service.py # 系统服务
│   └── notification_service.py # 通知服务
└── utils/               # 工具模块
    ├── __init__.py
    ├── logger.py        # 日志工具
    ├── encoding.py      # 编码工具
    └── error_handler.py # 错误处理
```

## 开发环境设置

### 环境要求

- Python 3.9+
- pip
- git

### 安装开发依赖

```bash
# 克隆项目
git clone https://github.com/TC999/zed-update.git
cd zed-update

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e .[dev]
```

### 代码质量工具

项目使用以下工具确保代码质量：

```bash
# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/

# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=zed_updater --cov-report=html
```

## 核心组件详解

### 配置管理 (ConfigManager)

配置管理器负责处理应用程序的所有配置项：

```python
from zed_updater.core.config import ConfigManager

config = ConfigManager()
config.set('zed_install_path', '/path/to/zed')
config.save_config()
```

#### 配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| zed_install_path | str | "D:\\Zed.exe" | Zed 可执行文件路径 |
| github_repo | str | "TC999/zed-loc" | GitHub 仓库 |
| auto_check_enabled | bool | true | 启用自动检查 |
| check_interval_hours | int | 24 | 检查间隔（小时） |
| backup_enabled | bool | true | 启用备份 |
| backup_count | int | 3 | 保留备份数 |

### 更新器核心 (ZedUpdater)

更新器负责处理 Zed 的下载、安装和版本管理：

```python
from zed_updater.core.updater import ZedUpdater

updater = ZedUpdater(config)
version = updater.get_current_version()
latest = updater.check_for_updates()
if latest:
    updater.download_update(latest)
    updater.install_update(download_path)
```

#### 主要方法

- `get_current_version()`: 获取当前版本
- `check_for_updates()`: 检查更新
- `download_update()`: 下载更新
- `install_update()`: 安装更新
- `create_backup()`: 创建备份

### 定时任务 (UpdateScheduler)

调度器管理自动更新任务：

```python
from zed_updater.core.scheduler import UpdateScheduler

scheduler = UpdateScheduler(updater, config)
scheduler.start()

# 添加回调
scheduler.add_update_callback(my_callback)
```

### GitHub API 客户端

处理与 GitHub API 的通信：

```python
from zed_updater.services.github_api import GitHubAPI

api = GitHubAPI(repo="TC999/zed-loc")
release = api.get_latest_release()
```

## GUI 架构

### 主窗口 (MainWindow)

主窗口是应用程序的核心界面：

```python
from zed_updater.gui.main_window import MainWindow

window = MainWindow(config, updater, scheduler)
window.show()
```

### 组件通信

GUI 组件通过信号槽机制通信：

```python
# 在 UpdaterGUI 中
self.update_progress.emit(progress, message)

# 在 MainWindow 中连接信号
self.updater_gui.update_progress.connect(self.on_update_progress)
```

## 错误处理

### 自定义异常

项目定义了多种特定异常：

```python
from zed_updater.core.exceptions import (
    ZedUpdaterError,
    NetworkError,
    DownloadError,
    InstallationError
)

try:
    # 操作
    pass
except NetworkError as e:
    # 处理网络错误
    pass
```

### 错误处理器

使用装饰器进行统一错误处理：

```python
from zed_updater.utils.error_handler import error_handler

@error_handler("配置保存")
def save_config(self):
    # 保存逻辑
    pass
```

## 测试

### 单元测试

测试使用 pytest 框架：

```python
import pytest
from zed_updater.core.config import ConfigManager

def test_config_save(temp_dir):
    config = ConfigManager()
    config.set('test_key', 'test_value')
    assert config.save_config() is True
```

### 测试结构

```
tests/
├── conftest.py           # 测试配置和 fixtures
├── unit/                # 单元测试
│   ├── test_config.py   # 配置测试
│   ├── test_updater.py  # 更新器测试
│   └── ...
└── integration/         # 集成测试
    └── ...
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_config.py

# 运行带覆盖率的测试
pytest --cov=zed_updater

# 生成 HTML 覆盖率报告
pytest --cov=zed_updater --cov-report=html
```

## 构建和发布

### PyInstaller 构建

```bash
# 安装构建依赖
pip install pyinstaller

# 构建单文件可执行程序
pyinstaller --clean --onefile --name zed-updater src/zed_updater/cli.py

# 构建 GUI 版本
pyinstaller --clean --onefile --name zed-updater-gui --windowed src/zed_updater/gui_main.py
```

### 构建配置

`pyproject.toml` 包含构建配置：

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
zip-safe = false
include-package-data = true
```

## 代码规范

### 命名约定

- 类名: `PascalCase`
- 函数名: `snake_case`
- 常量: `UPPER_CASE`
- 私有成员: 前缀 `_`

### 文档字符串

所有公共函数和类都需要文档字符串：

```python
def get_current_version(self) -> Optional[str]:
    """
    Get currently installed Zed version.

    Returns:
        Version string or None if not found.
    """
    pass
```

### 类型注解

使用类型注解提高代码可读性：

```python
from typing import Optional, Dict, Any

def process_data(self, data: Dict[str, Any]) -> Optional[str]:
    pass
```

## 调试技巧

### 日志调试

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 在代码中使用
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### 断点调试

```python
# 添加断点
import pdb; pdb.set_trace()

# 或使用 IDE 断点
```

### 性能分析

```python
import cProfile
cProfile.run('main()')
```

## 贡献指南

### 分支策略

- `main`: 主分支
- `develop`: 开发分支
- `feature/*`: 功能分支
- `bugfix/*`: 错误修复分支

### 提交规范

使用 Conventional Commits:

```
feat: add new feature
fix: fix bug
docs: update documentation
style: format code
refactor: refactor code
test: add tests
chore: update build scripts
```

### Pull Request

1. 从 develop 分支创建功能分支
2. 实现功能并添加测试
3. 确保所有测试通过
4. 更新文档
5. 提交 PR 到 develop 分支

## 性能优化

### 内存优化

- 使用生成器处理大文件
- 及时释放资源
- 避免循环引用

### 网络优化

- 使用连接池
- 实现重试机制
- 支持断点续传

### UI 优化

- 使用异步操作避免界面冻结
- 实现虚拟滚动处理大数据
- 缓存频繁使用的资源

## 安全考虑

### 输入验证

```python
def validate_path(path: str) -> bool:
    """验证路径安全性"""
    # 检查路径遍历攻击
    if ".." in path:
        return False
    # 检查绝对路径
    if not os.path.isabs(path):
        return False
    return True
```

### 敏感数据处理

- 不记录密码或敏感信息
- 使用环境变量存储密钥
- 加密存储敏感配置

### 权限检查

```python
def check_permissions(self, path: str) -> bool:
    """检查文件权限"""
    try:
        with open(path, 'r'):
            pass
        return os.access(path, os.W_OK)
    except:
        return False
```

## 扩展开发

### 添加新功能

1. 在相应模块中实现功能
2. 添加单元测试
3. 更新配置（如需要）
4. 更新文档
5. 添加 CLI 选项（如适用）

### 插件系统 (未来计划)

```python
class PluginInterface:
    def initialize(self, app):
        pass

    def on_update_check(self, version_info):
        pass

    def on_update_complete(self, result):
        pass
```

### API 扩展

为 Modern 实现添加新 API：

```python
# 在 backend 中添加路由
api.HandleFunc("/api/v1/custom", s.handleCustom).Methods("GET")

# 在 frontend 中调用
response = requests.get(f"{backend_url}/api/v1/custom")