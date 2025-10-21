# Zed Editor Auto Updater - API 参考

本文档描述 Zed Editor Auto Updater 的各种 API 接口。

## 目录
- [命令行 API](#命令行-api)
- [Python API](#python-api)
- [GUI API](#gui-api)
- [内部 API](#内部-api)

## 命令行 API

### 基本命令

#### `zed-updater --version`
显示程序版本信息。

```bash
$ zed-updater --version
Zed Editor Auto Updater v2.1.0
```

#### `zed-updater --help`
显示帮助信息。

```bash
$ zed-updater --help
usage: zed-updater [-h] [--version] [--check] [--update] [--current-version]
                   [--config CONFIG] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   [--log-file LOG_FILE] [--gui] [--quiet]

Zed Editor Auto Updater

options:
  -h, --help            show this help message and exit
  --version             Show Zed Updater version
  --check, -c           Check for Zed updates
  --update, -u          Download and install Zed updates
  --current-version     Show current Zed version
  --config CONFIG       Path to configuration file
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set logging level
  --log-file LOG_FILE   Path to log file
  --gui, -g             Start GUI mode
  --quiet, -q           Quiet mode (less output)
```

#### `zed-updater --current-version`
显示当前安装的 Zed 版本。

```bash
$ zed-updater --current-version
Current Zed version: 1.2.3
```

#### `zed-updater --check`
检查是否有可用更新。

```bash
$ zed-updater --check
Update available: 2.0.0
Release date: 2024-01-15T10:30:00Z
Download size: 10485760 bytes
Description: New features and improvements...
```

#### `zed-updater --update`
下载并安装可用更新。

```bash
$ zed-updater --update
Starting update process...
Download completed: zed_update_2.0.0.exe
Update installation completed
Successfully updated to version 2.0.0
```

#### `zed-updater --gui`
启动图形界面。

### 高级选项

#### 日志控制
```bash
# 设置日志级别
zed-updater --log-level DEBUG --check

# 指定日志文件
zed-updater --log-file /path/to/log.txt --update
```

#### 配置文件
```bash
# 使用自定义配置文件
zed-updater --config /path/to/custom_config.json --check
```

## Python API

### 核心类

#### ConfigManager

配置管理器，负责处理应用程序配置。

```python
from zed_updater.core.config import ConfigManager

# 创建配置管理器
config = ConfigManager()

# 获取配置值
install_path = config.get('zed_install_path')

# 设置配置值
config.set('backup_count', 5)

# 保存配置
config.save_config()

# 验证配置
errors = config.validate()
if errors:
    print("Configuration errors:", errors)
```

##### 方法

- `get(key, default=None)`: 获取配置值
- `set(key, value)`: 设置配置值
- `update(updates)`: 批量更新配置
- `save_config()`: 保存配置到文件
- `reset_to_defaults()`: 重置为默认配置
- `validate()`: 验证配置有效性

#### ZedUpdater

核心更新器，负责处理 Zed 的更新逻辑。

```python
from zed_updater.core.updater import ZedUpdater

# 创建更新器
updater = ZedUpdater(config)

# 获取当前版本
current_version = updater.get_current_version()
print(f"Current version: {current_version}")

# 检查更新
release_info = updater.check_for_updates()
if release_info:
    print(f"Update available: {release_info.version}")

    # 下载更新
    download_path = updater.download_update(release_info)

    # 安装更新
    result = updater.install_update(download_path)
    print(f"Update result: {result.message}")

# 启动 Zed
updater.start_zed()
```

##### 方法

- `get_current_version()`: 获取当前 Zed 版本
- `get_latest_version_info()`: 获取最新版本信息
- `check_for_updates()`: 检查是否有可用更新
- `download_update(release_info, progress_callback=None)`: 下载更新
- `install_update(download_path)`: 安装更新
- `create_backup()`: 创建备份
- `check_and_update(progress_callback=None)`: 检查并执行更新
- `start_zed()`: 启动 Zed 应用
- `cleanup_temp_files()`: 清理临时文件

#### UpdateScheduler

定时任务调度器。

```python
from zed_updater.core.scheduler import UpdateScheduler

# 创建调度器
scheduler = UpdateScheduler(updater, config)

# 添加更新回调
def on_update_available(update_available, result):
    if update_available:
        print(f"Update available: {result.version}")

scheduler.add_update_callback(on_update_available)

# 启动调度器
scheduler.start()

# 手动触发检查
result = scheduler.force_check_now()

# 停止调度器
scheduler.stop()
```

##### 方法

- `start()`: 启动定时任务
- `stop()`: 停止定时任务
- `restart()`: 重启定时任务
- `is_running()`: 检查是否正在运行
- `force_check_now()`: 立即执行检查
- `add_update_callback(callback)`: 添加回调函数
- `remove_update_callback(callback)`: 移除回调函数

### 服务类

#### GitHubAPI

GitHub API 客户端。

```python
from zed_updater.services.github_api import GitHubAPI

# 创建 API 客户端
api = GitHubAPI(repo="TC999/zed-loc")

# 获取最新发布
latest_release = api.get_latest_release()
print(f"Latest version: {latest_release.version}")

# 获取特定标签的发布
release = api.get_release_by_tag("v1.0.0")

# 获取发布列表
releases = api.get_releases(count=5)

# 设置代理
api.set_proxy("http://proxy.example.com:8080")
```

##### 方法

- `get_latest_release()`: 获取最新发布
- `get_release_by_tag(tag)`: 获取指定标签的发布
- `get_releases(count=10)`: 获取发布列表
- `set_proxy(proxy_url)`: 设置代理

#### SystemService

系统服务，提供系统信息和操作。

```python
from zed_updater.services.system_service import SystemService

# 创建系统服务
system = SystemService()

# 获取系统信息
info = system.get_system_info()
print(f"OS: {info.get('system')}")
print(f"Memory: {info.get('memory_total')} bytes")

# 获取系统状态
status = system.get_system_status()
print(f"CPU usage: {status.get('cpu_percent')}%")

# 查找进程
zed_processes = system.find_processes_by_name('zed')
for proc in zed_processes:
    print(f"PID: {proc['pid']}, CPU: {proc['cpu_percent']}%")

# 终止进程
success = system.terminate_process(pid=1234)
```

##### 方法

- `get_system_info()`: 获取系统信息
- `get_system_status()`: 获取系统状态
- `find_processes_by_name(name)`: 按名称查找进程
- `terminate_process(pid, timeout=10)`: 终止进程
- `get_process_info(pid)`: 获取进程信息
- `get_available_space(path=".")`: 获取可用磁盘空间
- `ensure_directory(path)`: 确保目录存在
- `get_file_info(file_path)`: 获取文件信息

### 工具类

#### EncodingUtils

编码工具类。

```python
from zed_updater.utils.encoding import EncodingUtils

# 设置 UTF-8 环境
EncodingUtils.setup_utf8_environment()

# 检测文件编码
encoding = EncodingUtils.detect_file_encoding('file.txt')
print(f"Detected encoding: {encoding}")

# 读取文本文件
content = EncodingUtils.read_text_file('file.txt', encoding)
if content:
    print(f"Content length: {len(content)}")

# 写入文本文件
success = EncodingUtils.write_text_file('output.txt', content)

# 规范化文本
normalized = EncodingUtils.normalize_text(raw_text)

# 转换文件编码
success = EncodingUtils.convert_file_encoding(
    'input.txt', 'output.txt', 'utf-8'
)
```

##### 方法

- `setup_utf8_environment()`: 设置 UTF-8 环境
- `get_system_encoding()`: 获取系统编码
- `detect_file_encoding(file_path, sample_size=8192)`: 检测文件编码
- `read_text_file(file_path, encoding=None)`: 读取文本文件
- `write_text_file(file_path, content, encoding='utf-8-sig')`: 写入文本文件
- `normalize_text(text)`: 规范化文本
- `safe_encode(text, target_encoding='utf-8')`: 安全编码
- `safe_decode(data, source_encoding=None)`: 安全解码
- `convert_file_encoding(source_path, target_path, target_encoding='utf-8-sig')`: 转换文件编码

#### 日志工具

```python
from zed_updater.utils.logger import setup_logging, get_logger

# 设置日志
setup_logging(
    level='INFO',
    log_file='zed_updater.log',
    use_colors=True
)

# 获取日志器
logger = get_logger(__name__)

# 记录日志
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

## GUI API

### 主窗口

```python
from zed_updater.gui.main_window import MainWindow

# 创建主窗口
window = MainWindow(config, updater, scheduler)
window.show()
```

### 更新 GUI 组件

```python
from zed_updater.gui.updater_gui import UpdaterGUI

# 创建更新组件
updater_gui = UpdaterGUI(config, updater, scheduler)

# 设置当前版本显示
updater_gui.set_current_version("1.0.0")

# 检查更新
updater_gui.check_for_updates()

# 连接信号
updater_gui.update_progress.connect(on_progress)
updater_gui.update_completed.connect(on_completed)
```

### 设置对话框

```python
from zed_updater.gui.settings_dialog import SettingsDialog

# 创建设置对话框
settings = SettingsDialog(config)
result = settings.exec_()  # 显示模态对话框

if result == QDialog.Accepted:
    print("Settings saved")
```

### 系统托盘

```python
from zed_updater.gui.system_tray import SystemTrayIcon

# 创建托盘图标
tray = SystemTrayIcon()

# 显示通知
tray.show_update_available("2.0.0")
tray.show_update_completed("2.0.0")
tray.show_update_failed("Network error")
```

## 内部 API

### 异常类

```python
from zed_updater.core.exceptions import (
    ZedUpdaterError,
    ConfigurationError,
    NetworkError,
    DownloadError,
    InstallationError,
    ValidationError,
    GitHubAPIError,
    ChecksumError,
    ProcessError,
    PermissionError,
    TimeoutError,
    FileOperationError,
    SchedulerError
)

try:
    # 可能出错的操作
    pass
except NetworkError as e:
    print(f"Network error: {e}")
except InstallationError as e:
    print(f"Installation failed: {e}")
```

### 错误处理装饰器

```python
from zed_updater.utils.error_handler import error_handler, safe_call, retry_on_failure

@error_handler("文件下载")
def download_file(self, url):
    # 下载逻辑
    pass

# 安全调用（出错时返回默认值）
result = safe_call(some_function, arg1, arg2, default=None)

# 重试调用
@retry_on_failure(max_attempts=3, delay=1.0)
def unreliable_operation(self):
    # 可能失败的操作
    pass
```

### 自定义数据类

```python
from zed_updater.services.github_api import ReleaseInfo, ReleaseAsset

# 创建发布信息
release = ReleaseInfo(
    version="2.0.0",
    release_date=datetime.now(),
    download_url="https://example.com/download.zip",
    description="New features",
    size=10485760,
    sha256="abc123",
    assets=[]
)

# 创建资源信息
asset = ReleaseAsset(
    name="zed-windows.exe",
    download_url="https://example.com/zed.exe",
    size=10485760,
    content_type="application/octet-stream"
)
```

### 配置数据类

```python
from zed_updater.core.config import ConfigData

# 创建配置
config = ConfigData()
config.zed_install_path = "/custom/path/zed.exe"
config.backup_enabled = False

# 转换为字典
config_dict = asdict(config)
```

## 扩展 API

### 添加新配置项

```python
# 在 ConfigData 中添加字段
@dataclass
class ConfigData:
    custom_setting: str = "default_value"

# 更新迁移逻辑
def _migrate_config(self, old_config):
    # 处理新配置项
    pass
```

### 添加新服务

```python
# 创建新服务类
class CustomService:
    def __init__(self):
        pass

    def custom_method(self):
        pass

# 在 services/__init__.py 中注册
from .custom_service import CustomService
__all__ = ['CustomService']
```

### 添加新 GUI 组件

```python
# 创建新组件
class CustomWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化界面

# 在主窗口中集成
def create_custom_tab(self):
    custom_tab = CustomWidget()
    self.tab_widget.addTab(custom_tab, "自定义")
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| DOWNLOAD_FAILED | 下载失败 |
| INSTALL_FAILED | 安装失败 |
| NETWORK_ERROR | 网络错误 |
| CONFIG_ERROR | 配置错误 |
| VALIDATION_ERROR | 验证错误 |
| PERMISSION_DENIED | 权限不足 |
| TIMEOUT | 操作超时 |
| CHECKSUM_MISMATCH | 校验和不匹配 |

## 响应格式

### 成功响应

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {
    "version": "2.0.0",
    "size": 10485760
  }
}
```

### 错误响应

```json
{
  "success": false,
  "message": "Operation failed: Network error",
  "error_code": "NETWORK_ERROR"
}