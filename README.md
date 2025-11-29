# qsync

qsync 是一个用于文件同步和服务器部署的工具。

## 功能特点

- 支持文件批量同步到远程服务器
- 支持预处理和后处理脚本
- 支持嵌套包含配置文件（自动去重）
- 支持自动更新sitemap文件

## 安装

由于本项目未上传到 PyPI，您需要通过以下方式安装：

### 方法一：从 wheel 文件安装（推荐）
从 [Releases](https://github.com/nexeora/QSync/releases) 页面下载最新版本的 wheel 文件（例如 `qsync-1.0.0-py3-none-any.whl`），然后执行安装命令：
```bash
pip install qsync-1.0.0-py3-none-any.whl
```

### 方法二：从源码安装（在本项目根目录下执行）（使用-e参数可以以开发模式安装）
```bash
pip install .
```


## 使用方法

```bash
qsync <config_path>
```

## 配置文件说明

qsync 使用 YAML 格式的配置文件来定义同步任务。配置文件支持丰富的功能，包括但不限于：

### 基本配置结构

```yaml
# 项目根目录
project_root: "/path/to/project"

# 远程主机信息（用户名@主机地址）
remote_host: "user@example.com"

# 临时目录（远程服务器上的临时目录位置，默认为/tmp）
temp_dir: "/tmp"

# 要同步的资源
resources:
  # 单个文件（本地路径（相对于项目根目录）: 远程路径（绝对路径））
  files:
    "local/path/file.txt": "remote/path/file.txt"
  
  # 目录（本地路径（相对于项目根目录）: 远程路径（绝对路径））
  dirs:
    "local/dir": "remote/dir"

# 部署后在远程服务器执行的命令（可选）
post_commands:
  - "nginx -s reload"
```
### 嵌套配置文件

qsync 支持通过 `include` 字段包含其他配置文件，便于管理复杂的项目结构：

```yaml
# 包含子配置
include:
  - sync_module1.yaml
  - sync_module2.yaml
```

### 预处理和后处理命令

qsync 支持在同步过程的不同阶段执行命令：


- `local_pre_commands`: 在打包文件之前在本地执行的命令
- `pre_commands`: 在打包文件之前在远程服务器上执行的命令
- `post_commands`: 在文件同步完成后在远程服务器上执行的命令
- `local_post_commands`: 在文件同步完成后在本地执行的命令

示例：
```yaml
# 同步前在本地构建项目
local_pre_commands:
  - "npm run build"

# 同步前停止服务
pre_commands:
  - "systemctl stop nginx"

# 同步后重启服务
post_commands:
  - "systemctl start nginx"

# 同步后在本地生成部署报告
local_post_commands:
  - "echo 'Deploy completed at $(date)' >> deploy.log"
```
嵌套配置文件时会自动去重预处理命令和后处理命令，避免重复执行。


### Sitemap 更新
qsync 可以自动更新 sitemap 文件：

```yaml
sitemaps:
  - path: "/local/path/sitemap.xml" # 本地sitemap文件路径(相对于项目根目录或绝对路径)
    loc:
      - "https://example.com/base/" # 站点URL
    target: "/remote/path/sitemap.xml" # 远程sitemap文件路径
```
在嵌套配置文件时，sitemap文件的更新任务会自动去重。

## 许可证

本项目采用 GNU 较宽松通用公共许可证 v2.1 (LGPLv2.1)。

您可以自由地：
- 在源代码形式下重新分发和修改软件
- 在二进制形式下重新分发修改后的作品
- 在满足一定条件下将本库与其他作品结合

有关更多信息，请参阅 [LICENSE](LICENSE) 文件。