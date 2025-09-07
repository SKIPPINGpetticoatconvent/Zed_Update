# Zed Editor 自动更新程序 - 快速使用指南

## 🚀 5分钟快速上手

### 1. 首次安装
```bash
# 方法一：使用安装脚本（推荐）
python install.py

# 方法二：手动安装
pip install -r requirements.txt
python main.py --gui
```

### 2. 配置 Zed 路径
首次运行时需要设置 Zed.exe 的安装路径：
- 打开程序后，在"基本设置"选项卡中点击"浏览"
- 选择你的 Zed.exe 文件（通常在 `D:\Zed.exe` 或类似位置）
- 点击"保存设置"

### 3. 立即体验
- 点击"检查更新"按钮
- 如果有新版本，点击"立即更新"
- 程序会自动备份、下载并安装新版本

## 📋 常用操作

### 启动程序
```bash
# GUI界面
python main.py --gui
# 或双击 run.bat 选择选项1

# 仅更新（命令行）
python main.py --update
# 或双击 run.bat 选择选项2
```

### 设置定时更新
1. 打开"定时设置"选项卡
2. 勾选"启用定时更新"
3. 设置执行时间（如：02:00）
4. 选择执行天数（默认工作日）
5. 点击"保存定时设置"
6. 点击"启动调度器"

### 开机自启动
1. 在"基本设置"中勾选"开机自启动"
2. 点击"保存设置"
3. 程序将在下次开机时自动启动

## ⚙️ 推荐配置

### 新手配置
```json
{
    "auto_check_enabled": true,
    "check_interval_hours": 24,
    "auto_download": true,
    "auto_install": false,  // 建议手动确认
    "backup_enabled": true,
    "show_notifications": true
}
```

### 高级用户配置
```json
{
    "scheduled_update_enabled": true,
    "scheduled_time": "02:00",
    "scheduled_days": [0, 1, 2, 3, 4],  // 工作日
    "auto_install": true,  // 如果你信任自动安装
    "minimize_to_tray": true
}
```

## 🔧 故障排除

### 问题：无法检查更新
**解决方案：**
1. 检查网络连接
2. 确认防火墙设置
3. 如果使用代理，在"高级设置"中配置代理

### 问题：更新失败
**解决方案：**
1. 关闭正在运行的 Zed 进程
2. 以管理员身份运行程序
3. 检查磁盘空间是否充足
4. 查看日志文件了解详细错误信息

### 问题：找不到 Zed.exe
**解决方案：**
1. 确认 Zed 已正确安装
2. 在"基本设置"中重新选择正确的路径
3. 如果 Zed 安装在非标准位置，手动指定路径

## 📱 系统托盘使用

程序运行时会在系统托盘显示图标：
- **单击**: 无操作
- **双击**: 显示/隐藏主窗口
- **右键**: 显示菜单（显示窗口、检查更新、退出）

## 📁 重要文件位置

```
程序目录/
├── config.json          # 配置文件
├── zed_updater.log      # 日志文件
├── ZedUpdater.bat       # GUI启动脚本
├── ZedUpdate.bat        # 命令行更新脚本
└── run.bat              # 交互式启动脚本
```

## 🛡️ 安全提示

### ⚠️ 重要警告
- **自动安装功能**：建议在生产环境中保持关闭，仅在测试环境使用
- **备份重要性**：虽然程序会自动备份，但建议定期手动备份重要文件
- **网络安全**：程序仅从官方 GitHub 仓库下载，通过 HTTPS 确保安全

### 🔒 最佳实践
1. 首次使用时先手动测试更新流程
2. 定期检查日志文件
3. 根据使用频率调整检查间隔
4. 保持程序本身的更新

## 🆘 需要帮助？

1. **查看日志**: 程序目录下的 `zed_updater.log` 文件
2. **重置配置**: 运行程序，在"高级设置"中点击"重置配置"
3. **完全重装**: 运行 `python uninstall.py` 后重新安装
4. **联系支持**: 在项目 GitHub 页面提交 Issue

## 🎯 使用技巧

### 快捷操作
- **F5**: 刷新版本信息（在主界面中）
- **Ctrl+Q**: 退出程序
- **最小化**: 程序会自动最小化到托盘（可设置）

### 批量操作
```bash
# 静默更新（用于脚本）
python main.py --update > update.log 2>&1

# 检查配置有效性
python -c "from updater.config import Config; c=Config(); print('配置正常' if not c.validate_config() else '配置有误')"
```

### 自定义计划任务
如果需要更复杂的调度，可以使用 Windows 任务计划程序：
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器（时间、频率）
4. 操作：运行 `ZedUpdateSilent.bat`

---

**🎉 恭喜！你已经掌握了 Zed Editor 自动更新程序的基本使用方法。享受自动化带来的便利吧！**