# GitHub Workflows 更新说明

本文档详细说明了 Zed Update Manager 项目 GitHub Actions 工作流的更新和优化。

## 🔄 更新概览

### 更新背景
- **问题**: GitHub Actions 中使用的 `actions/upload-artifact@v3` 已被弃用
- **影响**: 构建流程失败，无法正常上传构建产物
- **解决方案**: 升级所有 GitHub Actions 到最新版本并优化工作流

### 更新时间
- **更新日期**: 2024-12-19
- **适用版本**: v2.0.0+
- **更新范围**: 所有 GitHub Actions 工作流文件

## 📁 更新的工作流文件

### 1. 主要工作流文件

| 文件名 | 状态 | 描述 |
|--------|------|------|
| `build-multi-arch.yml` | ✅ 新增 | 多架构综合构建工作流 |
| `build.yml` | ✅ 更新 | 原有构建工作流（升级版本） |
| `build-windows.yml` | ⚡ 存在 | Windows 专用构建（未修改） |

### 2. 工作流功能对比

| 功能 | build.yml | build-multi-arch.yml | 说明 |
|------|-----------|----------------------|------|
| **变更检测** | ❌ | ✅ | 智能检测文件变更 |
| **Legacy构建** | ❌ | ✅ | 支持传统实现构建 |
| **Modern构建** | ✅ | ✅ | 现代架构构建 |
| **安全扫描** | ❌ | ✅ | Trivy + gosec 扫描 |
| **多Python版本** | 3.9-3.11 | 3.9-3.12 | 扩展版本支持 |
| **智能发布** | 基础发布 | ✅ | 分离式发布包 |

## 🔧 Action 版本更新

### 核心 Actions 升级

```yaml
# 更新前 → 更新后
actions/checkout@v3 → actions/checkout@v4
actions/setup-go@v3 → actions/setup-go@v4  
actions/setup-python@v3 → actions/setup-python@v4
actions/cache@v3 → actions/cache@v4
actions/upload-artifact@v3 → actions/upload-artifact@v4  # 🔥 关键更新
actions/download-artifact@v3 → actions/download-artifact@v4
dorny/paths-filter@v2 → dorny/paths-filter@v3
geekyeggo/delete-artifact@v2 → geekyeggo/delete-artifact@v5
```

### 新增 Actions

```yaml
# 安全扫描
aquasecurity/trivy-action@master  # 漏洞扫描
github/codeql-action/upload-sarif@v2  # SARIF 结果上传
securecodewarrior/github-action-gosec@v1  # Go 安全扫描
```

## 🚀 新工作流特性

### 1. 智能构建触发 (`build-multi-arch.yml`)

```yaml
detect-changes:
  outputs:
    legacy-changed: ${{ steps.changes.outputs.legacy }}
    modern-changed: ${{ steps.changes.outputs.modern }}
```

**优势**:
- 只在相关文件变更时构建对应实现
- 节省 CI/CD 资源和时间
- 避免不必要的构建

### 2. 多实现支持

#### Legacy 实现构建
```yaml
build-legacy:
  if: needs.detect-changes.outputs.legacy-changed == 'true'
  strategy:
    matrix:
      os: [ubuntu-latest, windows-latest, macos-latest]
      python-version: ["3.9", "3.10", "3.11", "3.12"]
```

#### Modern 实现构建
```yaml
build-modern-backend:  # Go 后端
build-modern-frontend: # PyQt5 前端
```

### 3. 安全扫描集成

```yaml
security-scan:
  steps:
    - name: Run Trivy vulnerability scanner
    - name: Run gosec Security Scanner  
    - name: Upload scan results to GitHub Security tab
```

**扫描范围**:
- 文件系统漏洞扫描
- Go 代码安全审计
- 依赖包安全检查
- SARIF 格式结果上传

### 4. 智能发布系统

```yaml
package-release:
  steps:
    - name: Create separate archives for each implementation
      run: |
        # 完整版本
        tar -czf zed-updater-complete.tar.gz .
        # Legacy 版本
        tar -czf zed-updater-legacy-only.tar.gz legacy/ scripts/start-legacy.*
        # Modern 版本  
        tar -czf zed-updater-modern-only.tar.gz modern/ scripts/start-modern.*
```

**发布包类型**:
- **Complete Package**: 包含两种实现的完整版本
- **Legacy Only**: 仅传统实现
- **Modern Only**: 仅现代实现

## 📊 构建矩阵详情

### Legacy 实现构建矩阵
```yaml
Strategy:
  OS: [ubuntu-latest, windows-latest, macos-latest]
  Python: [3.9, 3.10, 3.11, 3.12]
Total Jobs: 12 (3 OS × 4 Python版本)
```

### Modern 实现构建矩阵
```yaml
Backend (Go):
  OS: ubuntu-latest (交叉编译到所有平台)
  Targets: linux-amd64, linux-arm64, windows-amd64, windows-arm64, darwin-amd64, darwin-arm64

Frontend (PyQt5):
  OS: [ubuntu-latest, windows-latest, macos-latest] 
  Python: [3.9, 3.10, 3.11, 3.12]
Total Jobs: 12 + 1 = 13
```

## 🎯 工作流触发条件

### 触发事件
```yaml
on:
  push:
    branches: [main, develop]  # 推送到主要分支
  pull_request:
    branches: [main]           # PR 到主分支
  release:
    types: [created]           # 创建 Release
  workflow_dispatch:           # 手动触发
```

### 条件执行
- **Legacy构建**: Legacy文件变更时
- **Modern构建**: Modern文件变更时  
- **安全扫描**: Push 或 PR 事件
- **集成测试**: Modern构建完成后
- **发布打包**: Release 事件时

## 🔍 工作流监控

### 构建状态徽章
```markdown
[![Build Status](https://github.com/TC999/zed-update/workflows/Build%20Multi-Architecture%20Zed%20Updater/badge.svg)](https://github.com/TC999/zed-update/actions)
```

### 监控指标
- **构建成功率**: 目标 > 95%
- **构建时间**: Legacy < 10min, Modern < 15min
- **失败恢复时间**: < 24小时
- **安全扫描**: 0 严重漏洞

## 🛠️ 故障排除

### 常见问题及解决方案

#### 1. Artifact 上传失败
```yaml
# 问题: upload-artifact@v3 已弃用
- uses: actions/upload-artifact@v3  ❌

# 解决: 升级到 v4
- uses: actions/upload-artifact@v4  ✅
```

#### 2. Python 版本兼容性
```yaml
# 确保使用正确的 Python 版本
- name: Set up Python ${{ matrix.python-version }}
  uses: actions/setup-python@v4
  with:
    python-version: ${{ matrix.python-version }}
```

#### 3. Go 模块缓存问题
```yaml
- name: Cache Go modules
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache/go-build
      ~/go/pkg/mod
    key: ${{ runner.os }}-go-${{ hashFiles('*/go.sum') }}
```

#### 4. 跨平台编译失败
```bash
# 确保环境变量设置正确
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build
```

## 📈 性能优化

### 缓存策略
- **Go模块缓存**: 减少依赖下载时间
- **Python包缓存**: 加速 pip 安装
- **Docker层缓存**: 优化容器构建

### 并行执行
- **矩阵构建**: 多OS/版本并行构建
- **作业依赖**: 合理的依赖关系避免不必要等待
- **条件执行**: 只运行必要的作业

### 资源使用
- **智能触发**: 避免无关变更触发构建
- **失败快速**: 早期失败检测和报告
- **清理机制**: 自动清理旧的构建产物

## 📋 维护检查清单

### 定期检查项目
- [ ] GitHub Actions 版本更新通知
- [ ] 依赖安全漏洞扫描结果
- [ ] 构建性能指标监控
- [ ] 工作流执行时间趋势
- [ ] 失败率统计和分析

### 月度维护任务
- [ ] 更新 Action 版本到最新稳定版
- [ ] 清理过期的构建产物和缓存
- [ ] 审查安全扫描报告
- [ ] 优化构建矩阵配置
- [ ] 更新文档和徽章状态

## 🔮 未来规划

### 短期目标 (1-3个月)
- [ ] 添加代码质量检查 (SonarQube)
- [ ] 集成自动化测试覆盖率报告
- [ ] 优化构建缓存策略
- [ ] 添加性能基准测试

### 中期目标 (3-6个月)
- [ ] 实现蓝绿部署工作流
- [ ] 添加多环境部署支持
- [ ] 集成容器安全扫描
- [ ] 自动化依赖更新工作流

### 长期目标 (6个月+)
- [ ] 实现 GitOps 工作流
- [ ] 多云部署支持
- [ ] 高级监控和告警
- [ ] AI 辅助的构建优化

## 📞 支持和反馈

### 获取帮助
- **GitHub Issues**: 报告工作流问题
- **GitHub Discussions**: 讨论改进建议  
- **Wiki**: 查看详细的使用说明

### 贡献指南
1. Fork 仓库
2. 创建工作流分支
3. 测试工作流变更
4. 提交 Pull Request
5. 等待代码审查

---

**文档版本**: 1.0.0  
**最后更新**: 2024-12-19  
**维护者**: Zed Update Team  
**状态**: ✅ 生产就绪