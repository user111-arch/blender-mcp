# Blender MCP

[English](readme.md)

Blender 的轻量级 MCP（Model Context Protocol）服务器。它面向 Blender 的
Python API 提供自然语言接口，改善对官方文档的检索体验，并让用户能够探索
和理解复杂场景。

本仓库是官方 [Blender Lab MCP server](https://projects.blender.org/lab/blender_mcp)
的 fork，在上游功能之上扩展了一套建模工具与访问控制机制。详见
[本 fork 新增内容](#本-fork-新增内容)。

上游文档请参阅 [blender.org/lab/mcp-server](https://www.blender.org/lab/mcp-server/)。

----

## 概述

项目刻意保持精简与可维护，只做必要的事。它由两个组件组成，通过 TCP socket
通信：

- **Blender 插件** —— 在 Blender 内部运行，负责执行请求。
- **MCP 服务器** —— 作为独立进程运行，由 MCP 客户端启动
  （例如 [Llama.cpp](https://projects.blender.org/lab/blender_mcp/wiki/Llama.cpp)）。

数据流如下：

```
MCP 客户端  ⇐ MCP/stdio ⇒  blender-mcp  ⇐ TCP socket ⇒  Blender 插件
```

任何支持 MCP 的客户端都可以驱动它：Claude Desktop、Cursor、Cline、Continue、
本地 Llama.cpp Web UI，或任何遵守该协议的其他 agent。每个客户端各自启动一个
`blender-mcp` 进程；插件端允许若干个并发连接，因此多个客户端可以共用同一
Blender 实例。注意它们会同时共用同一个场景，所以最好避免同时使用。

## 本 fork 新增内容

**十个新工具**，覆盖上游留给 `execute_blender_code` 处理的建模环节：

| 工具 | 用途 |
|---|---|
| `create_primitive` | 添加立方体 / 球体 / 圆柱 / 平面 / 锥体 / 圆环 |
| `transform_object` | 平移 / 旋转 / 缩放，支持绝对值或相对值 |
| `duplicate_object` | 复制对象 N 次，可设累积偏移 |
| `delete_objects` | 删除对象，并可选择清理孤立数据块 |
| `create_material` | 创建或更新材质，并将其指派给对象 |
| `join_objects` | 安全合并网格，保留材质槽位 |
| `add_light` | 添加或更新灯光，可瞄准目标点 |
| `setup_camera` | 摆放相机并对准主体 |
| `render_to_image` | 渲染后直接返回图像本体，而非文件路径 |
| `export_scene` | 将场景导出为 glb / gltf / obj / fbx / stl |

这些工具分别取代了一段手写的 `bpy` 代码，那些代码容易踩到细微的坑。举两个
例子：`join_objects` 走 `bmesh` 路径，因为当操作符上下文不全时，
`bpy.ops.object.join()` 会直接让 Blender 中止；`create_material` 按类型查找
shader 节点，因为节点的 *名字* 是跟着 UI 语言走的，按名字查找在非英文环境
下会静默失败。

**两个访问控制特性**，均默认关闭、按需启用：

- 工具可见性列表（`BLENDER_MCP_ALLOW_TOOLS`、`BLENDER_MCP_DENY_TOOLS`、
  `BLENDER_MCP_READ_ONLY`），用于向客户端暴露受限的工具子集。
- 桥接 socket 上的共享密钥握手（`BLENDER_MCP_TOKEN` 加插件的 *Auth Token*
  偏好项），防止其他本地进程通过该端口驱动 Blender。

详见 [安全](#安全)。

## 环境要求

- Blender 5.1 或更高版本（插件侧），多数工具需要在 GUI 下运行。
- Python 3.10 或更高版本（MCP 服务器侧），配合 `uv` 或 `pip` 使用。
- Blender 侧：`Preferences → System → Network → Allow Online Access` 必须
  启用，否则插件会拒绝启动 server。

## 安装

### 1. Blender 插件

在本仓库的 checkout 中，将 `addon/blender_mcp_addon/` 目录打包成 zip，然后在
Blender 中安装：

```
Edit → Preferences → Get Extensions → （下拉 v）→ Install from Disk…
```

启用 *MCP* 扩展。其偏好面板位于
`Preferences → Add-ons → MCP`（不是 3D 视图侧边栏），提供 host、port、
auto-start、日志等设置，并显示 server 是否在运行。

### 2. MCP 服务器

进入 checkout 的 `mcp/` 目录：

```
uv sync            # 创建虚拟环境并安装依赖
```

或使用纯 pip：

```
pip install .
```

入口命令为 `blender-mcp`；不需要额外步骤，因为 MCP 客户端会自行启动该进程。

## 客户端配置

对于支持 stdio 的客户端（Claude Desktop、Cursor、Cline，以及大多数其他客户端），
将 server 指向 checkout 即可：

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["--directory", "/path/to/blender-mcp/mcp", "run", "blender-mcp"]
    }
  }
}
```

Windows 上请使用 Windows 风格的路径。`uv` 接受正斜杠，在 JSON 里也更易读：

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["--directory", "C:/path/to/blender-mcp/mcp", "run", "blender-mcp"]
    }
  }
}
```

对于偏好 URL 的客户端（Continue、某些 Web UI，以及任何需要走代理的客户端），
server 也支持 streamable HTTP。每个会话启动一次即可：

```
blender-mcp --transport http --host 127.0.0.1 --port 8000
```

端点为 `http://127.0.0.1:8000/`。大多数 URL 模式的客户端接受如下 JSON 条目，
而不需要 stdio 的 command：

```json
{
  "mcpServers": {
    "blender": {
      "url": "http://127.0.0.1:8000/"
    }
  }
}
```

请将 HTTP 仅绑定到回环接口。server 在设计上会执行任意代码，绑定到其他地址
就等于把这种能力开放给整个网络。

**先启动 Blender，再连客户端。** auto-start 默认开启，桥接 socket 会在
Blender 启动约一秒后开始监听；如果客户端先连，第一次调用会撞上冷启动窗口
并以连接错误失败。重试一次后再开始排查。

## 安全

### 工具可见性

可通过环境变量限制暴露给客户端的工具集。当 server 要交给一个你不完全信任的
客户端时很有用，因为工具之间的能力差距相当大。

``BLENDER_MCP_DENY_TOOLS``
   逗号分隔的工具名列表，这些工具永远不被暴露。
``BLENDER_MCP_ALLOW_TOOLS``
   设置后，仅暴露与列表项匹配的工具。
``BLENDER_MCP_READ_ONLY``
   设为 ``1``，则只暴露声明了 ``readOnlyHint`` 的工具。

条目接受 shell 风格的通配符，例如 ``execute_blender_code*`` 同时匹配
``execute_blender_code`` 和 ``execute_blender_code_for_cli``。
``DENY`` 在 ``ALLOW`` 之后生效，因此可以先开一个宽口径的 allow 列表，再
针对个别条目挖洞。这三个变量都不设置时，所有工具都暴露，行为与原先一致。

例如，向某个 agent 只授予只读权限：

   BLENDER_MCP_READ_ONLY=1 blender-mcp

或保留全部能力、仅屏蔽任意代码执行工具：

   BLENDER_MCP_DENY_TOOLS='execute_blender_code*' blender-mcp

启动时会在 stderr 报告当前生效的策略，并列出每个被扣留的工具及原因，因此
某个工具意外缺失时很容易追踪。

两点需要知道的取舍。

这是工具 *可见性* 的控制，不是沙箱。被暴露的工具会以 Blender 进程本身的
全部权限运行 —— 隐藏 ``execute_blender_code`` 并不会让桥接本身变安全，因为
任何能访问插件 socket 的代码仍然可以执行代码。

``readOnlyHint`` 表示工具是否修改 Blender 数据，并不代表它没有副作用。
``render_viewport_to_path`` 在这个意义上是只读的，但它仍会写一张图片到磁盘。

### 认证

默认情况下，插件接受任何能连上 socket 的客户端。socket 本身绑定在回环接口
上，所以网络不是真正的威胁面：任何 *本地* 进程（包括一个沙箱化的应用）都
可以连上来执行 Blender 内的任意 Python，因为每条请求都以 Blender 自身的权限
被 ``exec()``。

要关掉这条路，请在插件偏好中设置 token，并将同一个值通过
``BLENDER_MCP_TOKEN`` 环境变量交给 MCP 服务器：

   Edit -> Preferences -> Add-ons -> MCP -> Auth Token: <your secret>

MCP 服务器由 MCP 客户端启动，所以这个变量应该放在客户端的 server 配置中，
例如：

   "env": {"BLENDER_MCP_TOKEN": "<your secret>"}

将偏好项留空即关闭校验，这是默认行为，现有配置可以保持不变。当 token 被设置
后，携带缺失或不正确 token 的请求会在任何代码执行前被拒绝，且比较是常量
时间的，攻击者无法通过响应耗时反推 token。

请注意，这只保护桥接 socket 本身。它不能让 ``execute_blender_code`` 变安全
—— 详见上文工具可见性部分，以及插件中 ``weak_sandbox`` 模块对“按内容过滤
代码不可行”的说明。

## 工具

服务器共暴露 36 个工具。

### 参考与检查

上游的工具集：场景与 blend 文件摘要、对象详情、内置 API 文档与手册检索、
截图、视图导航、代码执行。完整列表与说明见
[readme_tools.rst](readme_tools.rst)。

### 建模与渲染

[本 fork 新增内容](#本-fork-新增内容) 一节列出的十个扩展。需要知道的几条约定：

- 写文件的工具（``render_to_image``、``export_scene``）将输出限制在 Blender
  的临时目录，沿用上游渲染工具的做法。这避免了它们退化为“任意文件写入”
  的原始操作。
- 创建或重配场景元素的工具采用 upsert 语义：用同样的名字再次调用
  ``create_material`` 或 ``add_light``，会更新既有项而非堆叠一个副本。

## 开发

### 新增一个工具

一个工具对应 `mcp/blmcp/tools/` 下的两个模块：

- ``<name>.py`` —— MCP 侧。调用 ``toolcode_format_call`` 与 ``send_code``，
  并通过 ``@mcp.tool()`` 注册。
- ``<name>_toolcode.py`` —— Blender 侧。定义 ``Params`` / ``Result``
  NamedTuple 与 ``main(params)`` 入口；``bpy`` 在 ``main`` 内部 import，绝不
  在模块级 import。

工具在启动时自动发现；``*_toolcode`` 模块会被跳过。共享逻辑放在
``tools_helpers/`` 下，工具之间不互相 import。

新增工具后，重新生成清单快照并运行测试：

```
python tests/test_tool_listing.py --update
python tests/test_tool_listing.py
python tests/test_mcp_server.py
```

### 测试

``make test``（或上面两条脚本）运行不需要 Blender 实例的测试套件。需要真实
Blender 与 LLM 的集成测试位于 ``tests/integration/``；环境变量说明见
``make help``。

### 部署插件改动

Blender 实际运行的是位于
``%APPDATA%\Blender Foundation\Blender\<version>\extensions\user_default\mcp\``
下的副本，而非 checkout 中的源码，因此插件源码改动必须重新安装才能生效。
直接修改已安装副本时，请统一换行符（checkout 是 CRLF，已安装文件是 LF），
保留备份，并对每个文件做语法检查。重新加载需要在 disable 与 enable 之间
清掉 ``sys.modules`` 中的 ``bl_ext.user_default.mcp*`` 条目 —— 单纯的勾选
切换会复用缓存的子模块。

## 许可证

GPL-3.0-or-later，与上游一致。每个源文件均带有 SPDX 头；第三方贡献者署名
就地保留。