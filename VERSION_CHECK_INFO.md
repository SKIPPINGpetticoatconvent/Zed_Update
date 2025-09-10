# Zed Editor 版本检查机制说明

## 概述

本程序已正确配置为检查 `https://github.com/TC999/zed-loc/releases` 的标签来获取程序版本信息，而非使用其他版本检查方式。

## 版本检查工作原理

### 1. GitHub Releases API

程序使用 GitHub Releases API 来获取最新版本信息：
- **API 端点**: `https://api.github.com/repos/TC999/zed-loc/releases/latest`
- **数据来源**: 直接从 GitHub releases 的 `tag_name` 字段获取版本标签
- **支持格式**: 
  - 日期格式标签（如：`20250907`）
  - 传统版本格式（如：`v1.0.0`）

### 2. 版本检查流程

```
1. 发送 HTTP 请求到 GitHub API
   ↓
2. 解析 JSON 响应，提取 tag_name
   ↓
3. 处理版本格式（移除 'v' 前缀等）
   ↓
4. 查找对应的下载资源（Assets）
   ↓
5. 与本地版本进行比较
```

### 3. 核心实现

版本检查的核心逻辑位于 `updater/updater.py` 文件的 `get_latest_version_info()` 方法中：

```python
def get_latest_version_info(self) -> Optional[Dict[str, Any]]:
    """从GitHub获取最新版本信息 - 支持日期发行版"""
    
    # 1. 请求 GitHub API
    url = self.config.get_setting('github_api_url')
    response = self.session.get(url, timeout=timeout, proxies=proxies)
    
    # 2. 解析响应
    release_info = response.json()
    tag_name = release_info.get('tag_name', '')
    
    # 3. 处理版本格式
    if tag_name.startswith('v'):
        version = tag_name[1:]  # 移除'v'前缀
    else:
        version = tag_name      # 直接使用标签名
    
    # 4. 查找下载链接
    assets = release_info.get('assets', [])
    # ... 资源查找逻辑
    
    return version_info
```

## 配置文件

### 当前配置
程序默认配置已更新为使用 TC999/zed-loc 仓库：

```json
{
    "github_repo": "TC999/zed-loc",
    "github_api_url": "https://api.github.com/repos/TC999/zed-loc/releases/latest"
}
```

### 相关文件
以下文件已更新为使用正确的仓库配置：

- `updater/config.py` - 默认配置
- `install.py` - 安装程序默认配置
- `config.example.json` - 示例配置文件
- `updater/gui.py` - GUI 默认设置
- `README.md` - 文档示例
- `run.bat` - 批处理脚本

## 版本比较机制

### 日期格式版本
- 格式：`YYYYMMDD`（如：`20250907`）
- 比较方式：字符串比较转数值比较
- 适用于 TC999/zed-loc 仓库的发行版

### 传统版本格式
- 格式：`major.minor.patch`（如：`1.2.3`）
- 比较方式：语义化版本比较
- 向下兼容其他项目

## 优势

1. **直接性**: 直接从 GitHub releases 获取官方标签信息
2. **准确性**: 避免了第三方数据源的延迟或不准确问题
3. **实时性**: 获取最新的发行版信息
4. **兼容性**: 支持多种版本标签格式
5. **可靠性**: 使用 GitHub 官方 API，稳定可靠

## 网络和代理支持

程序支持以下网络配置：
- HTTP/HTTPS 代理
- 自定义超时设置
- 请求重试机制
- 网络错误处理

## 错误处理

程序包含完善的错误处理机制：
- 网络连接错误
- API 响应解析错误
- 版本格式识别错误
- 下载资源缺失处理

## 验证方法

要验证版本检查是否正常工作：

1. 运行程序的 GUI 界面
2. 点击"检查更新"按钮
3. 查看日志文件 `zed_updater.log`
4. 观察是否正确获取了 TC999/zed-loc 的最新 release 标签

## 总结

本程序已完全配置为使用 GitHub releases 标签进行版本检查，确保了版本信息的准确性和实时性。所有相关配置文件都已更新为指向正确的 `TC999/zed-loc` 仓库。