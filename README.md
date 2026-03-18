# AIMoeMaker

AI 驱动的 MMD 建模 Blender 插件 —— 通过自然语言对话创建 MMD (PMX) 角色模型。

零建模基础的用户只需用中文描述角色外观，AI 即可自动生成 3D 模型、配置骨骼、设置物理和表情，最终导出可直接在 MikuMikuDance 中使用的 PMX 文件。

## 功能特性

### 三种交互模式

- **聊天面板** —— 在 Blender 侧边栏与 AI 对话，用自然语言描述角色（"创建一个银发红瞳的哥特萝莉"）
- **快捷面板** —— 滑块、下拉菜单、颜色选择器，直接调整模型参数
- **节点视图** —— 可视化节点编辑器，连接节点组合建模流程

### 20 个 MMD 建模命令

| 分类 | 命令 |
|------|------|
| 身体 | 创建体型、设置身高、调整比例 |
| 头发 | 添加头发（10 种发型）、修改发型、设置发色 |
| 面部 | 设置眼型（6 种）、设置瞳色、调整脸型 |
| 服装 | 添加服装（11 种）、修改服装、设置面料 |
| 配饰 | 添加配饰、按类型/索引移除 |
| 骨骼 | 配置 MMD 标准骨骼（29 根 + IK）、自动权重绘制 |
| 物理 | 头发刚体链、服装布料物理 |
| 表情 | 创建单个表情、添加 MMD 标准表情集（20 个） |
| 导出 | PMX 验证、6 阶段管线导出 |

### 3D 网格生成

- **身体** —— Skin 修改器参数化人体，无缝有机拓扑
- **头发** —— 四层曲线发丝（刘海/侧发/后发/束发），根粗尖细渐变
- **面部** —— 三层眼球（巩膜/虹膜/瞳孔）+ 发光材质
- **服装** —— 参数化服装网格，腰线收紧 + 裙摆展开
- **骨骼** —— 完整 MMD 标准骨骼树 + IK 约束

### PMX 导出管线

```
网格验证 → 骨骼验证 → 权重检查 → 物理验证 → 表情验证 → PMX 导出
```

- 安装了 mmd_tools 时直接导出 `.pmx`
- 未安装时降级保存为 `.blend` 并显示安装指南

### 其他

- **AI 后端可配置** —— 支持 OpenAI、Claude、Ollama、国产大模型等任何 OpenAI 兼容 API
- **代码沙箱** —— AST 安全检查 + 模块白名单 + 超时保护，安全执行 AI 生成的代码
- **资产管理器** —— 本地资产库 + GitHub 开源仓库搜索
- **会话管理** —— 对话历史、上下文压缩、项目持久化、撤销/重做

## 环境要求

- **Blender 4.2+**
- **Python 3.11+**（Blender 内置）
- **mmd_tools**（可选，用于 PMX 导出）—— [下载地址](https://github.com/UuuNyaa/blender_mmd_tools/releases)

## 安装

### 方式一：Extensions Platform（推荐）

Blender 4.2+ 的扩展平台（开发中）。

### 方式二：手动安装

1. 下载本仓库为 `.zip`
2. Blender → 编辑 → 偏好设置 → 插件 → 安装
3. 选择下载的 `.zip` 文件
4. 勾选启用 "AIMoeMaker"

## 配置

安装后进入偏好设置 → 插件 → AIMoeMaker：

| 设置 | 说明 | 示例 |
|------|------|------|
| API 端点 | OpenAI 兼容的 API URL | `https://api.openai.com/v1/chat/completions` |
| API Key | 你的 API 密钥 | `sk-...` |
| 模型名称 | 使用的模型 | `gpt-4o`、`claude-sonnet-4-20250514`、`deepseek-chat` |

**Ollama 本地模型：** 端点设为 `http://localhost:11434/v1/chat/completions`，API Key 填任意值，模型名填 Ollama 中的模型名。

## 使用方式

### 聊天模式

1. 3D 视口 → 侧边栏（N 键）→ AIMoeMaker 标签
2. 在输入框描述你想要的角色
3. AI 自动解析意图并生成模型

```
你: 创建一个145cm的萝莉角色，银色双马尾，红色瞳孔，穿哥特萝莉裙

AI: 好的，我来创建这个角色...
    → create_base_body(body_type="loli", height=145)
    → add_hair(style="twintail", colors=["#C0C0C0"])
    → set_eye_color(color="#FF0000")
    → add_clothing(type="gothic_dress", color="#000000")
```

### 快捷面板模式

侧边栏 → 快捷面板 → 直接拖动滑块调整参数。

### 节点模式

1. 打开节点编辑器
2. 树类型选择 "AIMoeMaker 节点编辑器"
3. 添加节点 → 连接 → 执行

## 项目结构

```
AIMoeMaker/
  ai/                  # AI 提供层（OpenAI 兼容适配器）
  asset_mgr/           # 资产管理器（本地库 + GitHub 搜索）
  blender_ops/         # Blender 3D 操作（网格/骨骼/物理生成）
  commands/            # 20 个 MMD 命令模块
  core/                # 核心引擎（会话、路由、沙箱、状态）
  pipeline/            # 6 阶段 PMX 导出管线
  prompts/             # AI 系统提示词和意图 Schema
  ui/                  # 三种 UI 模式（聊天/快捷/节点）
  utils/               # 工具函数
  tests/               # 108 个单元/集成测试
```

## 开发

### 运行测试

```bash
cd AIMoeMaker
python -m pytest tests/ -v
```

所有测试不依赖 Blender 环境即可运行（Blender 操作通过 `bpy_available` 标志隔离）。

### 架构

```
用户输入（自然语言 / 滑块 / 节点）
    ↓
Session Manager（对话历史 + 模型状态）
    ↓
AI Provider（OpenAI 兼容 API）
    ↓
Intent Router
    ├─ command → Command Engine（20 个命令）→ Blender Ops
    ├─ code    → Code Sandbox（AST 安全检查）
    └─ asset   → Asset Manager（搜索/下载）
    ↓
PMX Export Pipeline（6 阶段）
```

## 许可证

MIT

## 致谢

- [blender_mmd_tools](https://github.com/UuuNyaa/blender_mmd_tools) —— MMD/PMX Blender 支持
- [Blender](https://www.blender.org/) —— 开源 3D 创作套件
