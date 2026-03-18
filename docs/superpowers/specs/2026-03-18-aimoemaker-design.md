# AIMoeMaker - AI 驱动的 MMD 建模 Blender 插件设计文档

## 概述

AIMoeMaker 是一个 Blender 插件，让零建模基础的用户通过自然语言对话创建开箱即用的 MMD（PMX）模型。首攻方向为 MMD 角色制作，后续扩展至游戏场景和角色。

## 核心决策

| 维度 | 决策 |
|------|------|
| 产品形态 | Blender 插件（.zip 安装） |
| 目标用户 | 零建模基础的人 |
| 首攻方向 | MMD 制作（PMX 模型） |
| 工作流 | 对话式逐步构建为主，可选模板起点 |
| AI 后端 | 可配置（Claude / OpenAI / Ollama / 自定义端点） |
| 生成方式 | 混合架构（指令引擎为主 + 代码沙箱为补充） |
| 输出标准 | 开箱即用的 PMX（骨骼、权重、物理、表情全配好） |
| UI 形式 | 聊天 + 快捷面板为主，可切换节点式 |
| 语言 | 仅中文 |
| 资产库 | 社区驱动，AI 可联网检索/下载/安装部件包 |
| 部署 | 单插件 + API 远程调用 AI |

## 整体架构

```
┌─────────────────────────────────────────────────┐
│                 Blender Plugin                   │
│                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Chat UI  │  │ Quick Panel  │  │ Node View │  │
│  │ (侧边栏) │  │ (滑块/按钮)  │  │ (高级模式)│  │
│  └────┬─────┘  └──────┬───────┘  └─────┬─────┘  │
│       └───────────┬───┘────────────────┘         │
│                   ↓                              │
│  ┌────────────────────────────────┐              │
│  │      Session Manager          │              │
│  │  (对话历史、项目状态、撤销栈)   │              │
│  └───────────────┬────────────────┘              │
│                  ↓                               │
│  ┌────────────────────────────────┐              │
│  │      AI Provider Layer        │              │
│  │  (统一接口，可切换后端)         │              │
│  │  Claude / OpenAI / Ollama / …  │              │
│  └───────────────┬────────────────┘              │
│                  ↓                               │
│  ┌────────────────────────────────┐              │
│  │      Intent Router            │              │
│  │  AI 返回结构化意图              │              │
│  │  ├─ 匹配指令 → Command Engine │              │
│  │  └─ 无匹配  → Code Sandbox    │              │
│  └──────┬──────────────┬──────────┘              │
│         ↓              ↓                         │
│  ┌────────────┐ ┌──────────────┐                 │
│  │  Command   │ │   Code       │                 │
│  │  Engine    │ │   Sandbox    │                 │
│  │ (指令执行)  │ │ (沙箱执行)   │                 │
│  └─────┬──────┘ └──────┬───────┘                 │
│        └───────┬───────┘                         │
│                ↓                                 │
│  ┌────────────────────────────────┐              │
│  │      Asset Manager            │              │
│  │  (部件库管理、联网检索/下载)    │              │
│  └────────────────────────────────┘              │
│                ↓                                 │
│  ┌────────────────────────────────┐              │
│  │      PMX Export Pipeline      │              │
│  │  (骨骼/权重/物理/表情/导出)     │              │
│  └────────────────────────────────┘              │
└─────────────────────────────────────────────────┘
```

### 7 个核心模块

| 模块 | 职责 |
|------|------|
| **UI Layer** | 聊天面板 + 快捷面板 + 节点视图，三种交互模式 |
| **Session Manager** | 管理对话历史、当前模型状态快照、操作撤销栈 |
| **AI Provider Layer** | 统一的 LLM 调用接口，适配不同 API |
| **Intent Router** | 解析 AI 返回的意图，路由到指令引擎或代码沙箱 |
| **Command Engine** | 执行预定义指令（安全、可预测的常见操作） |
| **Code Sandbox** | 沙箱环境执行 AI 生成的 Python 代码（受限 API、超时保护） |
| **Asset Manager** | 部件库的本地管理 + 联网搜索/下载/安装 |
| **PMX Export Pipeline** | 最终导出为开箱即用的 PMX 文件 |

## 模块详细设计

### 1. AI Provider Layer

统一接口抽象：

```python
class AIProvider:
    def chat(messages, system_prompt, tools) -> AIResponse
    def stream_chat(messages, system_prompt, tools) -> Iterator[AIResponse]
```

适配器模式，每个 AI 后端一个适配器：

| 适配器 | 对接方式 |
|--------|---------|
| `ClaudeAdapter` | Anthropic API，支持 tool use |
| `OpenAIAdapter` | OpenAI API，支持 function calling |
| `OllamaAdapter` | 本地 HTTP，Ollama REST API |
| `CustomAdapter` | 用户自定义 OpenAI 兼容端点（覆盖大部分国产模型） |

**System Prompt 策略：**
- 内置 MMD 建模领域的 system prompt，教会 AI 输出结构化意图
- AI 被要求返回 JSON 格式的意图，同时返回自然语言解释

**AI 返回格式：**

指令型：
```json
{
  "reply": "好的，我来给角色加上粉色渐变的双马尾。",
  "intents": [
    {
      "type": "command",
      "action": "add_hair",
      "params": { "style": "twintail", "colors": ["#FFB6C1", "#FF69B4"], "gradient": true }
    }
  ]
}
```

代码型（无匹配指令时）：
```json
{
  "reply": "这个效果需要自定义脚本来实现，我来生成代码。",
  "intents": [
    {
      "type": "code",
      "description": "在裙摆边缘添加荷叶边装饰",
      "code": "import bpy\nimport bmesh\n..."
    }
  ]
}
```

### 2. Intent Router + Command Engine + Code Sandbox

**Intent Router：**

接收 AI 返回的 intents 数组，按顺序执行：

```
intents 数组
  ↓ 逐条处理
  ├─ type: "command" → Command Engine
  ├─ type: "code"    → Code Sandbox
  └─ type: "asset"   → Asset Manager
```

每条 intent 执行前自动创建状态快照，失败时可回滚。

**Command Engine 指令集（按 MMD 工序分类）：**

| 分类 | 指令示例 |
|------|---------|
| 身体 | `create_base_body`, `adjust_proportions`, `set_height` |
| 头发 | `add_hair`, `modify_hair_style`, `set_hair_color` |
| 面部 | `set_eye_shape`, `set_eye_color`, `adjust_face_shape` |
| 服装 | `add_clothing`, `modify_clothing`, `set_fabric_material` |
| 配饰 | `add_accessory`, `remove_accessory` |
| 骨骼 | `setup_skeleton`, `add_bone`, `auto_weight_paint` |
| 物理 | `add_physics_body`, `setup_hair_physics`, `setup_cloth_physics` |
| 表情 | `create_morph`, `add_expression_set` |
| 导出 | `export_pmx`, `validate_pmx` |

每个指令是独立的 Python 模块，接收参数字典，操作 Blender 对象，返回执行结果。

**Code Sandbox 安全措施：**

| 保护层 | 机制 |
|--------|------|
| API 白名单 | 只允许访问 `bpy`, `bmesh`, `mathutils`, `math` 等安全模块 |
| 禁止列表 | 屏蔽 `os`, `sys`, `subprocess`, `shutil`, 文件 I/O 等 |
| 超时保护 | 单次执行上限 30 秒，防止死循环 |
| 作用域隔离 | 在独立命名空间中 exec()，不污染全局 |
| 用户确认 | 首次执行代码时弹出确认，可设置为"总是允许" |

### 3. Asset Manager

**本地资产库结构：**

```
user_data/asset_library/
  index.json          ← 资产索引
  hair/
    twintail_01/
      model.blend     ← Blender 源文件
      meta.json       ← 元数据（作者、许可证、标签、适配参数）
      thumbnail.png
  clothing/
  accessory/
  body/
  eyes/
```

资产库存放于 Blender 用户数据路径下，与插件代码分离。

**搜索源与合规方案：** 详见下方"资产检索合规方案"章节。

**版权合规：**
- 每个资产的 `meta.json` 记录来源 URL 和许可证类型
- 下载前展示许可证信息，用户确认后才执行
- 标记为"禁止再分发"的资产不纳入分享功能

### 4. PMX Export Pipeline

6 个阶段顺序执行：

**① Mesh Validation（网格验证）**
- 检查非流形面、重叠顶点、法线方向
- 自动修复常见问题

**② Skeleton Setup（骨骼配置）**
- 按 MMD 标准骨骼树配置（全親→センター→上半身→...）
- 标准骨骼命名（日文名 + 英文名）
- IK 骨骼自动配置（足IK、つま先IK）

**③ Weight Paint（权重绘制）**
- 自动权重分配（Blender automatic weights 为基底）
- MMD 特有的权重修正（肩、膝盖的权重过渡）
- SDEF 权重支持（可选）

**④ Physics Setup（物理设置）**
- 头发刚体链自动生成
- 裙子/披风的布料物理刚体
- Joint 弹簧参数预设（可通过对话微调）

**⑤ Morph Setup（表情设置）**

标准表情集自动生成：
- 眉：真面目、困る、にこり、怒り …
- 目：まばたき、笑い、ウィンク …
- 口：あ、い、う、え、お、△、∧ …
- 其他：照れ（脸红）等

基于 Shape Key 驱动。

**⑥ PMX Export（导出）**
- 调用 mmd_tools 或自研导出器
- 写入 PMX 2.0 格式
- 自动生成 toon 贴图引用、sphere map 配置
- 显示枠（表示枠）自动分组

**依赖：** 需要 `mmd_tools`（Blender MMD Tools 插件）作为基础依赖。首次使用时检测是否已安装，未安装则引导或自动安装。

**导出前验证检查：**

| 检查项 | 说明 |
|--------|------|
| 骨骼完整性 | 是否包含所有必需的标准骨骼 |
| 权重覆盖 | 是否所有顶点都有权重分配 |
| 物理合法性 | 刚体/Joint 参数是否在合理范围内 |
| 表情完整性 | 是否包含基础表情集 |
| 材质有效性 | 贴图路径是否有效 |

验证失败时不阻止导出，向用户报告问题并建议修复。

### 5. UI Layer

**三种模式，统一入口（N 面板，标签 `AIMoeMaker`）：**

**模式 A：聊天面板（默认）**
- 对话气泡式布局，AI 回复附带操作进度条
- 底部固定操作栏：撤销、重做、导出
- 支持发送文字 + 拖入参考图片

**模式 B：快捷面板**
- 分类折叠面板（身体、头发、面部、服装、配饰、骨骼/物理、表情）
- 每个属性有滑块/下拉/颜色选择器
- 修改参数时实时调用 Command Engine
- 与聊天联动——快捷面板改参数，聊天记录也会体现

**模式 C：节点视图（v2 计划，首版不实现）**
- 利用 Blender 节点编辑器框架，自定义节点类型
- 每个节点对应一个 Command 或一组 Commands
- AI 可自动生成节点图，用户也可手动编排

**模式 A 和 B 共享同一个 Session Manager 和指令系统，** 任一模式的操作同步反映到另一模式。

### 6. Session Manager

**对话管理：**
- 完整对话历史保存
- 发送给 AI 时做上下文压缩：保留最近 N 轮 + 当前模型状态摘要 + 关键决策点

**模型状态追踪：**

```python
ModelState:
  body:        { height, proportions, body_type }
  hair:        { style, colors, length, physics_enabled }
  face:        { eye_shape, eye_color, face_shape }
  clothing:    [{ type, material, color, physics_enabled }]
  accessories: [{ type, position, scale }]
  skeleton:    { bones[], ik_setup, is_configured }
  physics:     { rigid_bodies[], joints[] }
  morphs:      { expressions[] }
```

每次 intent 执行后更新，摘要注入 AI 上下文。

**项目持久化：**

```
projects/
  my_gothic_lolita/
    project.json      ← 项目元数据
    session.json      ← 对话历史 + 状态快照
    scene.blend       ← Blender 场景文件
    exports/
      model.pmx
      textures/
```

支持多项目管理，保存/加载项目继续对话。

**撤销栈：**
- 每个操作有语义标签（中文），支持精确回滚（"撤销到添加双马尾之前"）
- 与 Blender undo 系统同步

## 错误处理策略

### 错误分类与处理

| 错误类型 | 处理方式 |
|----------|----------|
| AI API 调用失败（网络/限流/无效 key） | 在聊天面板显示友好提示，自动重试 1 次，失败后引导用户检查设置 |
| AI 返回格式异常（非法 JSON） | 解析失败时要求 AI 重新生成（最多 2 次），仍失败则提示用户换个说法 |
| Command 执行失败 | 自动回滚到执行前快照，在聊天中报告具体原因 |
| Code Sandbox 超时/异常 | 终止执行，回滚状态，向用户解释失败原因 |
| 资产下载失败/损坏 | 重试 1 次，失败后提示用户手动下载并导入 |

### 多 Intent 序列的部分失败

当一个回复包含多条 intents 时，按顺序执行。任一条失败：
1. 停止后续 intent 执行
2. 回滚到该回复执行前的快照（整体回滚，非逐条回滚）
3. 将失败信息反馈给 AI，由 AI 提出修复建议

### 离线降级

当 AI 后端不可用时，快捷面板仍可独立使用（直接操作 Command Engine），仅聊天功能不可用。

## Code Sandbox 安全模型

### 威胁模型

沙箱保护的主要场景是 **AI 生成错误或危险代码**（非恶意攻击），包括：意外删除场景对象、无限循环、调用破坏性 Blender 操作。

### 多层防护

**第一层：AST 预检查（执行前）**
- 解析代码为 AST，遍历检查：
  - 禁止访问 `__builtins__`、`__subclasses__`、`__import__`、`__globals__`
  - 禁止 `eval()`、`exec()`、`compile()` 调用
  - 禁止 `open()`、文件 I/O 相关调用
- AST 检查不通过则直接拒绝执行

**第二层：bpy 操作白名单**
- 允许的 `bpy.ops` 类别：`mesh.*`、`object.*`（部分）、`material.*`
- 禁止的高危操作：`bpy.ops.wm.*`（文件操作）、`bpy.ops.export_scene.*`、`bpy.data.libraries.load()`
- 白名单而非黑名单——未列入白名单的操作默认禁止

**第三层：运行时隔离**
- 构造受限的 `__builtins__` 字典（仅保留 `range`、`len`、`list`、`dict`、`print` 等安全内置函数）
- 独立命名空间 exec()
- 30 秒超时保护（通过 threading.Timer 实现）

**第四层：执行前快照**
- 每次沙箱执行前 `bpy.ops.ed.undo_push()`
- 异常或超时自动 `bpy.ops.ed.undo()`

## 上下文管理策略

### Token 预算分配

| 区域 | 预算比例 | 说明 |
|------|---------|------|
| System Prompt | 固定 ~2000 tokens | MMD 领域知识 + 意图输出格式定义 |
| 模型状态摘要 | 固定 ~500 tokens | 当前 ModelState 的 JSON 摘要 |
| 对话历史 | 剩余空间 | 滑动窗口，最近 N 轮完整保留 |

### 不同 Provider 的适配

| Provider | 典型上下文窗口 | 策略 |
|----------|--------------|------|
| Claude | 200K tokens | 保留最近 20 轮 + 完整历史摘要 |
| OpenAI GPT-4 | 128K tokens | 保留最近 15 轮 + 关键决策点 |
| Ollama 本地模型 | 4K-8K tokens | 仅保留最近 3 轮 + 精简状态摘要 |

对于小上下文窗口的本地模型，System Prompt 内部使用英文以提升解析可靠性，用户回复翻译为英文后发送，AI 回复翻译为中文后展示（可选，默认关闭）。

### 关键决策点标记

以下操作会被标记为"关键决策点"，在上下文压缩时优先保留：
- 角色整体设定描述（首次描述）
- 重大风格变更
- 用户明确拒绝/纠正 AI 的操作

## Blender 兼容性

### 目标版本

**最低支持：Blender 4.2+**

选择 4.2 而非 3.6 的原因：
- 4.2 引入了 Extensions Platform，是未来的标准分发方式
- 4.0+ 的 API 变更较大，同时维护 3.x 和 4.x 成本过高
- mmd_tools 社区 fork 已支持 4.x

### 分发方式

- 主要：Blender Extensions Platform（`blender_manifest.toml`）
- 备选：.zip 手动安装（兼容不便访问 Extensions Platform 的用户）

### mmd_tools 依赖

- 指定依赖：`mmd_tools` 社区 fork（UuuNyaa/blender_mmd_tools 或其后继）
- 安装策略：在插件首次激活时检测，未安装则在 UI 中显示安装引导（附下载链接和步骤），不尝试自动安装（避免权限问题）
- 长期计划：将核心 PMX 导出功能逐步内化，减少对 mmd_tools 的依赖

## 资产检索合规方案

### 搜索源策略调整

取消直接爬取 Bowlroll / DeviantArt（违反 ToS），改为：

| 来源 | 方式 | 说明 |
|------|------|------|
| GitHub | API 搜索 | 搜索带有开源许可的 MMD 资产仓库 |
| 用户本地 | 本地索引 | 用户手动下载的资产导入并索引 |
| 社区仓库（未来） | 自建 API | 未来可建立 AIMoeMaker 社区资产仓库 |

### 联网检索流程（修订）

```
用户："我想要初音未来风格的头发部件"
    ↓
AI 生成 asset intent → Asset Manager 执行：
  1. 搜索本地已安装资产
  2. 搜索 GitHub 开源仓库
  3. 若无结果，向用户推荐手动搜索的关键词和网站链接
    ↓
用户确认 → 下载/导入 → 注册到本地索引
```

## 测试策略

| 测试类型 | 范围 | 工具 |
|----------|------|------|
| 单元测试 | Command Engine 各指令、ModelState、Intent Router | Blender headless mode (`blender --background --python`) |
| 集成测试 | PMX Export Pipeline 全流程 | 导出 PMX 后用 pymeshio 验证格式正确性 |
| AI 集成测试 | Intent 解析、Provider 适配 | Mock AI 响应，验证 Intent Router 路由正确 |
| 沙箱安全测试 | Code Sandbox 防护 | 构造恶意代码样本，验证全部被拦截 |
| 手动验收 | 导出的 PMX 在 MMD 中加载和播放 | MikuMikuDance 手动测试 |

## 数据版本化

所有持久化 JSON 文件（`project.json`、`session.json`、`index.json`）包含 `schema_version` 字段。插件升级时：
- 读取文件 → 检查 schema_version → 版本低于当前则执行迁移函数 → 写回
- 迁移函数链式调用：v1→v2→v3，每个版本增量迁移

## 性能考虑

- **AI 调用异步化：** 通过 `threading.Thread` 在后台调用 AI API，避免阻塞 Blender UI 主线程。使用 `bpy.app.timers` 将结果回调到主线程执行 Blender 操作。
- **撤销快照：** 依赖 Blender 内置 undo 系统（增量存储），不额外做全场景拷贝。
- **快捷面板实时更新：** 使用 debounce（200ms 延迟），避免滑块拖动时每帧触发 Command Engine。

## 范围声明

以下功能明确标记为 **v2 / 未来版本**，不在首个版本实现：
- 节点视图（模式 C）——首版仅实现聊天面板 + 快捷面板
- 社区资产仓库（自建）——首版仅支持 GitHub 搜索 + 本地导入
- 参考图片识别——首版仅支持文字输入
- 多语言支持——首版仅中文

## 技术依赖

| 依赖 | 用途 |
|------|------|
| Blender 4.2+ | 宿主环境 |
| mmd_tools (社区 fork) | PMX 导入/导出、MMD 骨骼和物理支持 |
| httpx / urllib | AI API 调用、联网资产检索 |

## 项目目录结构

```
AIMoeMaker/
  __init__.py              ← Blender 插件入口
  ai/
    provider.py            ← AIProvider 基类
    adapters/
      claude.py
      openai_adapter.py
      ollama.py
      custom.py
  core/
    session.py             ← Session Manager
    intent_router.py       ← Intent Router
    command_engine.py       ← Command Engine 调度器
    code_sandbox.py        ← Code Sandbox
    model_state.py         ← ModelState 追踪
  commands/
    body.py
    hair.py
    face.py
    clothing.py
    accessory.py
    skeleton.py
    physics.py
    morph.py
    export.py
  asset_mgr/
    manager.py             ← Asset Manager
    sources/
      github_source.py
      local.py
  pipeline/
    mesh_validation.py
    skeleton_setup.py
    weight_paint.py
    physics_setup.py
    morph_setup.py
    pmx_export.py
  ui/
    chat_panel.py
    quick_panel.py
    node_view.py           ← v2 预留，首版不实现
    operators.py           ← Blender operators
    preferences.py         ← 插件设置面板（API key 配置等）
  prompts/
    system_prompt.py       ← MMD 建模领域 system prompt
    intent_schema.py       ← AI 返回格式定义
  utils/
    undo.py
    context_compression.py
  user_data/               ← 用户数据（运行时生成，存于 Blender 用户路径下）
    asset_library/         ← 本地资产库
      index.json
    projects/              ← 用户项目
```
