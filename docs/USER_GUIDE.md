# Zed Editor Auto Updater - 用户指南

## 目录
- [快速开始](#快速开始)
- [图形界面使用](#图形界面使用)
- [命令行使用](#命令行使用)
- [配置说明](#配置说明)
- [高级功能](#高级功能)
- [故障排除](#故障排除)

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

### 首次运行
```bash
# 启动图形界面
zed-updater-gui
```

首次运行时，程序会：
1. 检查 Zed 是否已安装
2. 创建默认配置文件
3. 检查是否有可用更新

## 图形界面使用

### 主界面

主界面包含以下区域：

#### 版本信息面板
- **当前版本**: 显示已安装的 Zed 版本
- **最新版本**: 显示 GitHub 上的最新版本
- **状态**: 显示当前操作状态

#### 操作按钮
- **检查更新**: 检查是否有新版本可用
- **下载更新**: 下载可用更新
- **安装更新**: 安装已下载的更新
- **启动 Zed**: 启动 Zed 编辑器

#### 进度显示
- **进度条**: 显示下载/安装进度
- **状态标签**: 显示详细操作信息

#### 系统信息
- 显示系统状态和 Zed 进程信息

### 设置界面

#### 基本设置
- **Zed 安装路径**: Zed 可执行文件的位置
- **GitHub 仓库**: 用于检查更新的仓库地址

#### 更新设置
- **自动检查**: 是否启用自动检查更新
- **检查间隔**: 自动检查的时间间隔（小时）
- **检查时间**: 每日检查的具体时间
- **启动时检查**: 程序启动时自动检查更新

#### 下载和安装设置
- **自动下载**: 发现更新时自动下载
- **自动安装**: 下载完成后自动安装
- **自动启动**: 安装完成后自动启动 Zed
- **下载超时**: 下载超时时间（秒）
- **重试次数**: 下载失败时的重试次数

#### 备份设置
- **启用备份**: 更新前创建备份
- **保留备份数**: 保留的备份文件数量

#### 网络设置
- **启用代理**: 使用代理服务器
- **代理 URL**: 代理服务器地址

#### 界面设置
- **最小化到托盘**: 关闭窗口时最小化到托盘
- **启动时最小化**: 程序启动时直接最小化
- **启用通知**: 显示系统通知
- **语言**: 界面语言选择

### 定时任务界面

#### 定时设置
- **检查时间**: 设置每日检查时间
- **启用定时检查**: 启用/禁用定时检查功能

#### 运行状态
- **当前状态**: 定时任务的运行状态
- **下次运行**: 下次检查的时间

#### 控制按钮
- **启动定时任务**: 启动定时检查
- **立即运行检查**: 立即执行一次检查

### 日志界面

显示程序运行日志，包括：
- 操作记录
- 错误信息
- 调试信息

### 关于界面

显示程序信息和系统状态。

## 命令行使用

### 基本命令

```bash
# 显示帮助信息
zed-updater --help

# 显示版本信息
zed-updater --version

# 检查当前 Zed 版本
zed-updater --current-version

# 检查是否有更新
zed-updater --check

# 下载并安装更新
zed-updater --update

# 启动图形界面
zed-updater --gui
```

### 高级选项

```bash
# 指定配置文件
zed-updater --config /path/to/config.json --check

# 设置日志级别
zed-updater --log-level DEBUG --check

# 指定日志文件
zed-updater --log-file /path/to/log.txt --update
```

### 组合使用

```bash
# 检查更新并记录详细日志
zed-updater --check --log-level DEBUG --log-file debug.log

# 使用自定义配置更新
zed-updater --config custom_config.json --update --log-level INFO
```

## 配置说明

### 配置文件位置

默认配置文件位置：
- Windows: `%APPDATA%\zed_updater\config.json`
- Linux/macOS: `~/.config/zed_updater/config.json`

### 配置项说明

#### 基本配置
```json
{
  "zed_install_path": "D:\\Zed.exe",
  "github_repo": "TC999/zed-loc"
}
```

#### 更新配置
```json
{
  "auto_check_enabled": true,
  "check_interval_hours": 24,
  "check_on_startup": true,
  "force_download_latest": true
}
```

#### 备份配置
```json
{
  "backup_enabled": true,
  "backup_count": 3
}
```

#### 网络配置
```json
{
  "proxy_enabled": false,
  "proxy_url": "http://proxy.example.com:8080",
  "download_timeout": 300,
  "retry_count": 3
}
```

#### 界面配置
```json
{
  "minimize_to_tray": true,
  "start_minimized": false,
  "notification_enabled": true,
  "language": "zh_CN",
  "log_level": "INFO"
}
```

## 高级功能

### 代理支持

程序支持 HTTP 和 SOCKS5 代理：

```json
{
  "proxy_enabled": true,
  "proxy_url": "http://user:pass@proxy.example.com:8080"
}
```

### 定时任务

定时任务使用系统调度器，支持：
- 每日固定时间检查
- 可配置检查间隔
- 后台运行不干扰工作

### 备份管理

自动备份功能：
- 更新前自动创建备份
- 支持多版本备份
- 自动清理旧备份

### 系统集成

#### Windows
- 系统托盘图标
- 开机自启动（可选）
- 桌面快捷方式

#### Linux/macOS
- 系统托盘图标
- 启动脚本支持

## 故障排除

### 常见问题

#### 无法检测 Zed 版本
- 检查 Zed 安装路径是否正确
- 确认 Zed 可执行文件存在
- 检查文件权限

#### 下载失败
- 检查网络连接
- 确认代理设置（如果使用代理）
- 检查防火墙设置
- 查看日志中的详细错误信息

#### 安装失败
- 确保有足够的磁盘空间
- 检查 Zed 进程是否正在运行
- 确认文件权限
- 以管理员身份运行（Windows）

#### 代理问题
- 检查代理 URL 格式
- 确认代理服务器可访问
- 检查代理认证信息

### 日志分析

程序会在以下位置生成日志：
- 默认日志: `zed_updater.log`
- 自定义日志: 通过 `--log-file` 指定

查看日志：
```bash
# 显示最后 50 行日志
tail -50 zed_updater.log

# 搜索错误信息
grep ERROR zed_updater.log
```

### 调试模式

启用详细日志：
```bash
zed-updater --log-level DEBUG --check
```

### 重置配置

删除配置文件可重置为默认设置：
```bash
rm config.json
# 重新运行程序将创建默认配置
```

## 性能优化

### 内存使用
- 程序空闲时内存占用约 50MB
- 下载时内存使用与文件大小相关
- 建议系统内存 256MB 以上

### 磁盘空间
- 程序本体约 20MB
- 备份文件大小等于 Zed 安装大小
- 临时文件在下载完成后自动清理

### 网络使用
- 版本检查请求很小（< 1KB）
- 下载流量等于更新文件大小
- 支持断点续传节省流量

## 安全考虑

### 文件验证
- SHA256 校验下载文件完整性
- 验证 GitHub 发布来源
- 检查文件签名（计划中）

### 权限管理
- 遵循最小权限原则
- 只访问必要的文件和网络资源
- 支持用户级和系统级安装

### 数据保护
- 敏感配置加密存储（计划中）
- 备份文件安全保存
- 日志不记录敏感信息