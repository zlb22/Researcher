# Researcher Repository Overview

## Project Status

**当前进度**: Phase 1 ✅ 已完成 | Phase 2 🚧 进行中

| Phase | 状态 | 完成度 | 说明 |
|-------|------|--------|------|
| Phase 1: 核心基础设施 | ✅ 完成 | 100% | Tool 基类、文件工具、Workspace 管理 |
| Phase 2: Agent 系统 | 🚧 进行中 | 40% | LLM 客户端 ✅，BaseAgent ✅，PromptLoader ✅，Orchestrator 待实现 |
| Phase 3: 助理 Agent | ⬜ 待开始 | 0% | Searcher、Analyzer、Writer、CallAgentTool |
| Phase 4: Shell 工具 | ⬜ 待开始 | 0% | BashTool、进程管理 |
| Phase 5: 完善和优化 | ⬜ 待开始 | 0% | 配置系统、CLI（OpenAI 客户端 ✅） |

**整体统计**：
- 源代码：970 行
- 测试覆盖：26 个测试（100% 通过）
- 代码质量：✅ Ruff format + check 通过
- Git Commits: 1 个

---

## Project Description

### Motivation

现有的 deep research 系统，大多遵循「并发收集信息 → 汇总写作」的流水线式脚手架。
随着模型能力的提升，这种流程被设计得越精细，反而越容易限制模型自身的思考与规划能力。
本项目的目标，是探索一种「脚手架尽量少、自由度尽量高」的 deep research 形态。

核心思路是：围绕一个主 Agent，为它提供一组以工具形式存在的助理 Agent（agent-as-tool），例如搜索 Agent、分析 Agent 等。主 Agent 不再被固定在某个预设流程里，而是根据研究目标自主调用这些工具，决定何时搜索、何时分析、何时写作。

为了解决「多个助理 Agent 产生大量内容，主 Agent 无法全部读完」的问题，本项目引入了一个分层记忆与阅读机制：
- 助理 Agent 不直接把长篇内容塞回上下文，而是持久化到文件系统，**由 Agent 自己决定如何组织信息结构**
- 返回给主 Agent 的只是「简要摘要 + 文件索引」，主 Agent 如有需要，可以通过文件操作工具按需读取细节
- 主 Agent 通过「概览 → 选点下钻 → 再行动」的节奏组织研究

通过这种方式，主 Agent 可以在有限上下文内进行高层规划和决策；助理 Agent 则负责扩展记忆与信息深度。最终形成一个**脚手架极简、以工具化多 Agent 和文件系统为基础、支持分层阅读和长期积累**的 deep research 系统。

---

## Design Philosophy

### 核心原则

1. **最小化预设结构**：不强制 Agent 按照固定流程或目录结构工作
2. **Agent 自主决策**：让 Agent 自己决定如何组织信息、如何分解任务
3. **工具化协作**：Agent 之间通过标准化的工具接口协作
4. **分层信息管理**：大量信息持久化到文件，通过摘要 + 索引机制访问
5. **渐进式深入**：支持从概览到细节的多层次探索

---

## Design-存储结构

### 基本原则

**不预设目录结构**，只提供最小化的入口文件，Agent 完全自由组织信息。

### 初始结构

```
./workspace/<research_id>/
├── question.txt           # 研究问题（唯一预设文件）
├── workspace/            # Agent 自由组织的工作区
└── report.md             # 最终报告（orchestrator 决定何时创建）
```

### Agent 自由组织示例

不同的研究可能形成完全不同的结构，由 Agent 根据需要自主创建：

```
# 示例 A：按主题分类
workspace/
├── topic_ai_history/
│   ├── search_results.md
│   └── analysis.md
├── topic_current_trends/
│   └── data.json
└── index.md              # Agent 自建的索引

# 示例 B：按时间线组织
workspace/
├── phase1_exploration/
├── phase2_deep_dive/
└── timeline.md

# 示例 C：按来源分类
workspace/
├── academic_papers/
├── industry_reports/
└── expert_interviews/
```

**关键点**：
- 没有强制的 `search/`、`analyze/` 目录
- 没有强制的 `summary.md + detail.md` 模式
- Agent 根据研究特点和需要自主决定结构
- 唯一要求：返回给 orchestrator 的必须包含简要摘要 + 文件路径

---

## Design-工具系统

### 设计原则（参考 Mini-Agent）

所有工具继承统一的 `Tool` 基类，返回标准化的 `ToolResult`。

### Tool 基类定义

```python
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

class ToolResult(BaseModel):
    """工具执行结果的标准返回值"""
    success: bool                    # 执行是否成功
    content: str = ""               # 结果内容（简要）
    error: str | None = None        # 错误信息
    metadata: dict[str, Any] = {}   # 额外元数据（如文件路径、统计信息等）

class Tool(ABC):
    """工具抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """参数 schema（JSON Schema 格式）"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具（异步）"""
        pass
```

### 核心工具列表

#### 1. 文件操作工具

```python
# ReadTool
read_file(
    filepath: str,           # 文件路径（支持相对于 workspace 的路径）
    start_line: int = None,  # 起始行（可选）
    end_line: int = None,    # 结束行（可选）
) -> ToolResult

# WriteTool
write_file(
    filepath: str,           # 文件路径
    content: str,            # 文件内容
    mode: str = 'create'     # 'create' | 'overwrite' | 'append'
) -> ToolResult

# EditTool
edit_file(
    filepath: str,           # 文件路径
    old_string: str,         # 要替换的字符串（必须唯一）
    new_string: str          # 新字符串
) -> ToolResult
```

#### 2. Shell 工具

```python
# BashTool
execute_shell(
    command: str,                    # Shell 命令
    timeout: int = 120,              # 超时时间（秒）
    run_in_background: bool = False  # 是否后台运行
) -> ToolResult

# BashOutputTool（获取后台进程输出）
get_shell_output(
    bash_id: str,            # 后台进程 ID
    block: bool = True       # 是否阻塞等待
) -> ToolResult

# BashKillTool（终止后台进程）
kill_shell(
    bash_id: str             # 后台进程 ID
) -> ToolResult
```

#### 3. Agent 调用工具

```python
# CallAgentTool
call_agent(
    agent_type: str,                # Agent 类型：'searcher' | 'analyzer' | 'writer'
    task_description: str,          # 任务描述
    context_files: list[str] = [],  # 需要读取的上下文文件
    output_dir: str = "",           # 输出目录（相对于 workspace）
    max_steps: int = 50,            # 最大步数
    return_full_output: bool = False # 是否返回完整输出
) -> ToolResult

# ToolResult.metadata 包含：
# {
#   "output_files": ["workspace/topic_ai/search.md", ...],  # 产出的文件列表
#   "full_output": "...",        # 完整输出（如果 return_full_output=True）
#   "steps_used": 15,            # 使用的步数
#   "agent_id": "searcher_001"   # Agent 实例 ID
# }
```

#### 4. 网络搜索工具（仅 searcher 可用）

```python
# TavilySearchTool
web_search(
    query: str,                  # 搜索查询
    max_results: int = 10,       # 最大结果数
    search_depth: str = "advanced"  # 'basic' | 'advanced'
) -> ToolResult

# ToolResult.content: 搜索结果摘要
# ToolResult.metadata: 完整的搜索结果 JSON
```

---

## Design-Agents

### Agent 架构

每个 Agent 都是一个独立的执行单元，拥有：
- 专属的 system prompt
- 特定的工具集合
- 独立的 workspace 目录
- 标准化的输入输出接口

### Orchestrator（编排者）

**职责**：
- 理解研究问题，制定高层研究计划
- 决定何时调用哪个助理 Agent（searcher/analyzer/writer）
- 管理研究进度，维护全局视图
- 通过"概览 → 选点下钻"的方式阅读助理 Agent 的产出
- 决定何时结束研究，触发报告生成

**可用工具**：
```python
[
    ReadTool,           # 读取文件
    WriteTool,          # 写入文件
    EditTool,           # 编辑文件
    CallAgentTool,      # 调用助理 Agent
    ExecuteShellTool,   # 执行 Shell 命令
]
```

**System Prompt 关键点**：
```
你是一个研究编排者，负责组织和管理深度研究项目。

核心职责：
1. 分解研究问题，制定研究计划
2. 调用助理 Agent（searcher/analyzer/writer）执行具体任务
3. 管理文件系统中的研究信息
4. 采用"概览 → 选点下钻"的方式阅读助理 Agent 的产出

工作原则：
- 不要预设固定流程，根据研究问题灵活规划
- 助理 Agent 会返回简要摘要 + 文件路径，你可以按需读取细节
- 自主决定何时搜索、何时分析、何时写作
- 信息组织方式完全由你决定

可用工具：read_file, write_file, edit_file, call_agent, execute_shell
```

### Searcher（搜索者）

**职责**：
- 执行网络搜索，收集原始信息
- **自主决定信息的组织方式**（不受预设结构限制）
- 将搜索结果持久化到文件系统
- 返回简要摘要 + 文件索引给 orchestrator
- 支持 orchestrator 的进一步查询和细化搜索

**可用工具**：
```python
[
    WebSearchTool,      # Tavily 搜索
    ReadTool,           # 读取文件（可能需要读取上下文）
    WriteTool,          # 写入文件
    EditTool,           # 编辑文件
    ExecuteShellTool,   # Shell 命令（如 curl、wget）
]
```

**System Prompt 关键点**：
```
你是一个网络搜索专家，负责收集和组织研究信息。

核心职责：
1. 根据任务描述执行网络搜索
2. 评估搜索结果质量，决定是否需要细化查询
3. 将搜索结果持久化到文件系统
4. 自主决定信息的组织方式（按主题/时间/来源等）

工作原则：
- 返回结果时，content 字段只包含简要摘要（< 500 tokens）
- metadata 中必须包含 output_files 列表
- 信息组织方式由你自由决定，但要易于后续检索
- 如果搜索结果不足，主动进行多轮搜索

示例返回格式：
{
  "success": true,
  "content": "完成搜索，找到 15 篇相关资料，已按主题分为 3 类...",
  "metadata": {
    "output_files": ["workspace/ai_history/search_1.md", "workspace/ai_history/search_2.md"],
    "search_queries": ["AI history", "deep learning evolution"],
    "total_results": 15
  }
}

可用工具：web_search, read_file, write_file, edit_file, execute_shell
```

### Analyzer（分析者）

**职责**：
- 对搜索结果或其他数据进行深度分析
- 提取关键洞察、发现模式、建立联系
- **自主决定分析结果的存储方式**
- 返回分析摘要 + 详细文件路径
- 支持多轮迭代分析

**可用工具**：
```python
[
    ReadTool,           # 读取文件（分析对象）
    WriteTool,          # 写入分析结果
    EditTool,           # 编辑文件
    ExecuteShellTool,   # Shell 命令（如数据处理脚本）
]
```

**System Prompt 关键点**：
```
你是一个数据分析专家，负责深度分析研究材料。

核心职责：
1. 读取并分析指定的文件或数据
2. 提取关键信息、发现模式、建立关联
3. 将分析结果持久化到文件系统
4. 生成结构化的分析报告

工作原则：
- 返回结果时，content 字段只包含核心发现摘要（< 500 tokens）
- metadata 中必须包含 output_files 列表
- 分析深度和广度根据任务描述自主判断
- 可以创建图表、表格等辅助材料

示例返回格式：
{
  "success": true,
  "content": "分析完成。核心发现：1) AI 发展呈现三波浪潮... 2) 关键转折点...  3) 未来趋势...",
  "metadata": {
    "output_files": ["workspace/analysis_report.md", "workspace/timeline_chart.json"],
    "key_insights": ["insight1", "insight2"],
    "data_points": 45
  }
}

可用工具：read_file, write_file, edit_file, execute_shell
```

### Writer（写作者）

**职责**：
- 根据搜索和分析结果撰写研究报告
- 支持多种报告格式（markdown、结构化文档）
- 与 orchestrator 协作，迭代改进报告质量
- 确保报告的逻辑性、完整性和可读性

**可用工具**：
```python
[
    ReadTool,           # 读取素材
    WriteTool,          # 写入报告
    EditTool,           # 编辑报告
    ExecuteShellTool,   # Shell 命令（如生成 PDF）
]
```

**System Prompt 关键点**：
```
你是一个专业的研究报告撰写专家。

核心职责：
1. 阅读搜索和分析结果
2. 组织逻辑结构，撰写高质量研究报告
3. 确保报告的完整性、准确性和可读性
4. 支持迭代修改和优化

工作原则：
- 报告结构由你根据内容自主决定
- 引用来源时注明文件路径和关键信息
- 可以多次迭代，逐步完善报告
- 返回时，content 字段包含报告摘要，metadata 包含报告文件路径

示例返回格式：
{
  "success": true,
  "content": "研究报告已完成，共 5000 字，包含 3 个主要章节...",
  "metadata": {
    "output_files": ["report.md"],
    "word_count": 5000,
    "sections": ["背景", "现状", "趋势"]
  }
}

可用工具：read_file, write_file, edit_file, execute_shell
```

---

## Design-技术实现

### 核心架构（参考 Mini-Agent）

**不使用高度封装的框架**（如 OpenAI Agents SDK），而是基于原生 SDK 构建：

```python
# 1. Tool 基类系统
from abc import ABC, abstractmethod

class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]: ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult: ...

# 2. Agent 基类
class BaseAgent:
    def __init__(
        self,
        agent_type: str,
        system_prompt: str,
        tools: list[Tool],
        workspace_dir: str,
        max_steps: int = 50
    ):
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.tools = {tool.name: tool for tool in tools}
        self.workspace_dir = Path(workspace_dir)
        self.max_steps = max_steps
        self.messages = []

    async def run(self, task_description: str) -> ToolResult:
        """执行 Agent 任务"""
        # 添加任务到消息历史
        # 循环：LLM 生成 → 执行工具 → 收集结果
        # 返回标准化的 ToolResult
        ...

# 3. LLM 客户端（支持多提供商）
class LLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: list[Tool]
    ) -> LLMResponse: ...

class AnthropicClient(LLMClient): ...
class OpenAIClient(LLMClient): ...
```

### 目录结构

```
src/researcher/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── tool.py              # Tool 基类和 ToolResult
│   ├── agent.py             # BaseAgent 实现
│   └── workspace.py         # Workspace 管理
├── tools/
│   ├── __init__.py
│   ├── file_tools.py        # ReadTool, WriteTool, EditTool
│   ├── bash_tool.py         # BashTool, BashOutputTool, BashKillTool
│   ├── agent_tool.py        # CallAgentTool
│   └── search_tool.py       # TavilySearchTool
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py      # Orchestrator Agent
│   ├── searcher.py          # Searcher Agent
│   ├── analyzer.py          # Analyzer Agent
│   └── writer.py            # Writer Agent
├── llm/
│   ├── __init__.py
│   ├── base.py              # LLMClient 抽象基类
│   ├── anthropic_client.py  # Anthropic 实现
│   └── openai_client.py     # OpenAI 实现
├── prompts/
│   ├── __init__.py
│   ├── orchestrator.txt     # Orchestrator system prompt
│   ├── searcher.txt         # Searcher system prompt
│   ├── analyzer.txt         # Analyzer system prompt
│   └── writer.txt           # Writer system prompt
└── utils/
    ├── __init__.py
    ├── logger.py            # 日志配置（loguru）
    └── config.py            # 配置管理
```

---

## Coding Rules

### 代码规范

1. **命名规范**：
   - 变量：`snake_case`，按功能命名，尽可能详细
   - 类：`PascalCase`
   - 常量：`UPPER_SNAKE_CASE`
   - 私有成员：前缀 `_`

2. **类型注解**：
   - 所有函数必须有类型注解
   - 使用 `from typing import` 导入类型
   - 示例：`def read_file(filepath: str, start_line: int | None = None) -> ToolResult:`

3. **异步优先**：
   - 所有 Tool 的 `execute` 方法必须是异步的
   - Agent 的 `run` 方法必须是异步的
   - 使用 `async/await` 语法

4. **错误处理**：
   - 工具执行异常统一捕获，转换为 `ToolResult(success=False, error=...)`
   - 使用 loguru 记录错误日志
   - 不要让异常传播到 Agent 循环外

5. **日志规范**：
   - 使用 loguru 记录所有关键操作
   - 日志级别：
     - `DEBUG`: 详细的调试信息
     - `INFO`: Agent 执行步骤、工具调用
     - `WARNING`: 工具执行失败（但可恢复）
     - `ERROR`: Agent 执行失败、系统错误
   - 示例：
     ```python
     from loguru import logger

     logger.info(f"Orchestrator calling searcher agent: {task_description}")
     logger.debug(f"Tool arguments: {arguments}")
     ```

6. **Prompt 管理**：
   - 所有 system prompt 放在 `src/researcher/prompts/` 目录
   - 使用 `.txt` 文件存储，加载时读取
   - 不要硬编码在代码里

7. **依赖管理**：
   - 使用 `uv` 管理环境
   - `pyproject.toml` 定义依赖
   - 依赖版本明确指定（避免兼容性问题）

8. **代码质量**：
   - 完成小功能后执行：`ruff format . && ruff check --fix .`
   - 通过后再提交代码

9. **文档更新**：
   - 完成小功能后及时更新 `CLAUDE.md` 的 Repository Structure 部分
   - 保持文档与代码同步

10. **测试规范**：
    - 为每个 Tool 编写单元测试
    - 使用 pytest + pytest-asyncio
    - 测试文件命名：`test_<module_name>.py`

### 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| Agent 框架 | 自建（基于原生 SDK） | 参考 Mini-Agent，完全自主控制 |
| LLM | Anthropic Claude / OpenAI GPT | 通过抽象客户端支持多提供商 |
| 网络搜索 | Tavily Search API | 高质量搜索结果 |
| 日志 | loguru | 简洁强大的日志库 |
| 数据验证 | Pydantic v2 | ToolResult、配置等数据模型 |
| 异步 | asyncio | 原生异步支持 |
| 环境管理 | uv | 快速的 Python 包管理器 |
| 代码格式化 | ruff | 快速的 linter + formatter |
| 测试 | pytest + pytest-asyncio | 标准测试框架 |

---

## Implementation Roadmap

### Phase 1: 核心基础设施（优先级 P0）✅ **已完成**

1. ✅ 设计文档完成
2. ✅ Tool 基类系统
   - ✅ `ToolResult` 数据模型
   - ✅ `Tool` 抽象基类
   - ✅ Schema 转换方法（Anthropic/OpenAI）
3. ✅ 文件操作工具
   - ✅ `ReadTool` - 读取文件，支持行范围，带行号输出
   - ✅ `WriteTool` - 写入文件，支持 create/overwrite/append 模式
   - ✅ `EditTool` - 精确文本替换（要求 old_string 唯一）
4. ✅ Workspace 管理
   - ✅ 目录创建和管理
   - ✅ 相对路径解析
   - ✅ 安全检查（防止访问 workspace 外文件）
   - ✅ 文件列表和元数据查询
5. ✅ 测试和示例
   - ✅ 26 个单元测试（100% 通过）
   - ✅ 2 个示例程序（basic_tool_usage.py, file_tools_usage.py）
   - ✅ 代码质量检查（Ruff format + check）

**Phase 1 完成统计**：
- 源代码：970 行
- 测试覆盖：26 个测试用例，100% 通过
- 核心模块：5 个（tool.py, workspace.py, file_tools.py）
- Git Commits: 1 个

### Phase 2: Agent 系统（优先级 P0）

1. ✅ LLM 客户端抽象
   - ✅ `LLMClient` 基类
   - ✅ `AnthropicClient` 实现
   - ✅ Message 格式转换 + OpenAI 兼容客户端
2. ✅ `BaseAgent` 实现
   - ✅ Agent 循环逻辑
   - ✅ Tool 调用和结果处理
   - ✅ 消息历史管理（`src/researcher/core/agent.py`）
3. ✅ System Prompt 加载器（`PromptLoader`）
4. ⬜ 简单的 Orchestrator（测试用）

### Phase 3: 助理 Agent（优先级 P1）

1. ⬜ `TavilySearchTool` 实现
2. ⬜ `Searcher` Agent
3. ⬜ `Analyzer` Agent
4. ⬜ `Writer` Agent
5. ⬜ `CallAgentTool` 实现

### Phase 4: Shell 工具（优先级 P1）

1. ⬜ `BashTool` 实现
2. ⬜ 后台进程管理器
3. ⬜ `BashOutputTool` 和 `BashKillTool`

### Phase 5: 完善和优化（优先级 P2）

1. ✅ OpenAI 客户端实现（支持 OPENAI_BASE_URL/OPENAI_MODEL 环境变量）
2. ⬜ 配置文件系统
3. ⬜ CLI 入口
4. ⬜ 单元测试
5. ⬜ 示例和文档

---

## Key Differences from Original Design

| 维度 | 原设计 | 新设计 | 理由 |
|------|--------|--------|------|
| 目录结构 | 预设 `search/`, `analyze/` 等目录 | 只有 `workspace/`，Agent 自由组织 | 贯彻"最小化脚手架"理念 |
| 信息组织 | 强制 `summary.md + detail.md` | Agent 自主决定 | 给予 Agent 完全自由度 |
| Tool 返回值 | 未定义 | 标准化 `ToolResult` | 统一接口，易于扩展 |
| Tool 参数 | 不一致 | 统一的 JSON Schema | 规范化，支持多 LLM |
| Agent 调用 | 参数简陋 | 完整的参数和返回值设计 | 支持上下文传递、结果追踪 |
| 技术栈 | OpenAI Agents SDK（高封装） | 基于原生 SDK 自建（低封装） | 完全控制，易于定制 |
| Agent 职责 | 未明确 | 详细的职责和 prompt 设计 | 清晰的分工和协作 |
| Agent 数量 | 3 个（缺 writer） | 4 个（增加 writer） | 职责分离，orchestrator 不负责写作 |




## Repository Structure

### Root Directory

```
.
├── src/researcher/          # Main package source code
├── tests/                   # Test files
├── examples/                # Example scripts
├── .env.example             # Sample environment configuration
├── pyproject.toml           # Project configuration and dependencies
├── CLAUDE.md                # Design documentation and implementation guide
└── uv.lock                  # Dependency lockfile (managed by uv)
```

### Core Implementation (`src/researcher/`)

**Phase 1: ✅ 已完成**

```
src/researcher/
├── __init__.py             # ✅ Package initialization, exports Tool and ToolResult
├── core/
│   ├── __init__.py         # ✅ Core module exports
│   ├── tool.py             # ✅ Tool base class and ToolResult data model (210 lines)
│   ├── workspace.py        # ✅ Workspace management (260 lines)
│   └── agent.py            # ⬜ BaseAgent implementation (TODO - Phase 2)
├── tools/
│   ├── __init__.py         # ✅ Tools module exports
│   ├── file_tools.py       # ✅ ReadTool, WriteTool, EditTool (480 lines)
│   ├── bash_tool.py        # ⬜ BashTool and related tools (TODO - Phase 4)
│   ├── agent_tool.py       # ⬜ CallAgentTool (TODO - Phase 3)
│   └── search_tool.py      # ⬜ TavilySearchTool (TODO - Phase 3)
├── agents/
│   ├── __init__.py         # ⬜ Agents module exports
│   ├── orchestrator.py     # ⬜ Orchestrator Agent (TODO - Phase 2)
│   ├── searcher.py         # ⬜ Searcher Agent (TODO - Phase 3)
│   ├── analyzer.py         # ⬜ Analyzer Agent (TODO - Phase 3)
│   └── writer.py           # ⬜ Writer Agent (TODO - Phase 3)
├── llm/
│   ├── __init__.py         # ✅ LLM module exports
│   ├── base.py             # ✅ LLMClient abstract base class
│   ├── anthropic_client.py # ✅ Anthropic implementation
│   └── openai_client.py    # ✅ OpenAI implementation (OpenAI-compatible)
├── prompts/
│   ├── __init__.py         # ⬜ Prompts module exports
│   ├── orchestrator.txt    # ⬜ Orchestrator system prompt (TODO - Phase 2)
│   ├── searcher.txt        # ⬜ Searcher system prompt (TODO - Phase 3)
│   ├── analyzer.txt        # ⬜ Analyzer system prompt (TODO - Phase 3)
│   └── writer.txt          # ⬜ Writer system prompt (TODO - Phase 3)
└── utils/
    ├── __init__.py         # ⬜ Utils module exports
    ├── logger.py           # ⬜ Loguru configuration (TODO - Phase 2)
    └── config.py           # ⬜ Configuration management (TODO - Phase 5)
```

**Phase 1 已实现的核心功能**：

1. **Tool 抽象基类** (tool.py:1)
   - 统一的工具接口（name, description, parameters, execute）
   - 标准化 ToolResult 返回值
   - 支持 Anthropic 和 OpenAI 两种 schema 格式
   - 完全异步 + 类型安全（Pydantic v2）

2. **WorkspaceManager** (workspace.py:1)
   - 工作区创建和路径解析
   - 安全检查（防止访问 workspace 外文件）
   - 文件列表、子目录管理
   - 元数据查询

3. **文件操作工具** (file_tools.py:1)
   - **ReadTool**: 读取文件（支持行范围、带行号输出）
   - **WriteTool**: 写入文件（create/overwrite/append 模式）
   - **EditTool**: 精确文本替换（old_string 必须唯一）

### Testing (`tests/`)

**Phase 1: ✅ 已完成 - 26 个测试，100% 通过**

```
tests/
├── test_tool_base.py       # ✅ Tests for Tool and ToolResult (7 tests)
│                           # - ToolResult data model tests
│                           # - Tool properties and execution
│                           # - Schema conversion (Anthropic/OpenAI)
├── test_file_tools.py      # ✅ Tests for file tools (19 tests)
│                           # - ReadTool: 5 tests (simple read, line range, errors)
│                           # - WriteTool: 6 tests (create/overwrite/append, errors)
│                           # - EditTool: 6 tests (replacement, uniqueness, errors)
│                           # - Integration: 2 tests (workflow, path resolution)
├── test_bash_tool.py       # ⬜ Tests for bash tools (TODO - Phase 4)
└── test_agents.py          # ⬜ Tests for agents (TODO - Phase 2)
```

**测试统计**：
- 总计：26 个测试用例
- 通过率：100%
- 执行时间：0.12 秒
- 覆盖范围：Tool 基类、Workspace 管理、所有文件工具

### Examples (`examples/`)

**Phase 1: ✅ 已完成 - 2 个示例程序**

```
examples/
├── basic_tool_usage.py     # ✅ Basic tool usage example
│                           # - Creating custom tools (Calculator demo)
│                           # - Tool execution and error handling
│                           # - Schema conversion for different LLM providers
├── file_tools_usage.py     # ✅ File tools comprehensive demo
│                           # - ReadTool: full read, line range
│                           # - WriteTool: create, overwrite, append
│                           # - EditTool: text replacement
│                           # - Workspace organization
│                           # - Error handling and security checks
├── simple_agent.py         # ⬜ Simple agent example (TODO - Phase 2)
└── full_research.py        # ⬜ Full research workflow example (TODO - Phase 3)
```

**示例特点**：
- 可直接运行（`uv run python examples/xxx.py`）
- 包含详细的输出和说明
- 展示最佳实践和常见用法
- 覆盖错误处理和边界情况

## Configuration

### Dependencies (pyproject.toml)

**Core Dependencies:**
- `pydantic>=2.0.0` - Data validation and modeling
- `loguru>=0.7.0` - Logging
- `anthropic>=0.40.0` - Anthropic Claude API
- `openai>=1.50.0` - OpenAI GPT API
- `tavily-python>=0.5.0` - Tavily search API

**Development Dependencies:**
- `ruff>=0.8.0` - Linting and formatting
- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.24.0` - Async test support

### Environment Setup

```bash
# Install dependencies using uv
uv sync --dev

# Run tests
uv run pytest

# Run linting and formatting
uv run ruff format .
uv run ruff check --fix .
```

### Environment Variables

- `.env.example` 提供了完整的环境变量模板（ANTHROPIC_API_KEY、OPENAI_API_KEY、OPENAI_BASE_URL、OPENAI_MODEL 等）
- 复制为 `.env` 或直接导出到 shell，即可在示例与客户端中自动读取配置
