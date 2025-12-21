# Agent Trace Logger - Framework Analysis Guide

## 概述

Agent Trace Logger 是一个专门用于**分析和改进multi-agent框架**的工具。它记录完整的agent工作轨迹，帮助你：

- 🔍 **理解决策过程**：看到orchestrator如何决策、为什么调用某个agent
- 📊 **分析工作模式**：识别agent的工作模式、发现低效的地方
- 🐛 **调试框架问题**：追踪整个执行流程，定位问题
- 📈 **优化性能**：查看资源使用、识别瓶颈
- 💡 **改进prompt**：通过观察agent行为来优化system prompt

## 启用方式

只需在运行时添加 `--debug` 或 `-d` 标志：

```bash
# 启用trace logging
uv run researcher research "AI trends" --llm openai --debug

# 或使用短标志
uv run researcher research "AI trends" --llm openai -d
```

## 输出文件

Trace logger会在workspace中生成两个文件：

### 1. `agent_trace.jsonl` - 机器可读格式

JSONL格式（每行一个JSON对象），方便程序化分析：

```jsonl
{"timestamp":"2024-12-21T10:58:00.123","event_type":"agent_start","agent_type":"orchestrator","task":"AI trends","parent_agent":null}
{"timestamp":"2024-12-21T10:58:05.456","event_type":"tool_call","agent_type":"orchestrator","tool_name":"execute_shell","arguments":{"command":"ls -la"}}
{"timestamp":"2024-12-21T10:58:05.789","event_type":"tool_result","agent_type":"orchestrator","tool_name":"execute_shell","success":true,"content":"total 8..."}
{"timestamp":"2024-12-21T10:58:10.012","event_type":"agent_start","agent_type":"searcher","task":"Search for comprehensive information on AI trends","parent_agent":"orchestrator"}
```

**用途**：
- 使用Python/jq等工具分析
- 统计分析（工具调用频率、成功率等）
- 可视化工作流

### 2. `agent_trace.md` - 人类可读格式

Markdown格式，包含统计摘要和时间线：

```markdown
# Agent Trace Log

Session started: 2024-12-21T10:58:00.000000

---

## Session Summary

- **Duration**: 245.67 seconds
- **Total Agent Calls**: 7
- **Total Tool Calls**: 42
- **Total LLM Calls**: 0

### Agent Statistics

| Agent | Calls | Tools | Success | Failure |
|-------|-------|-------|---------|----------|
| orchestrator | 1 | 15 | 1 | 0 |
| searcher | 3 | 12 | 3 | 0 |
| analyzer | 2 | 10 | 2 | 0 |
| writer | 1 | 5 | 1 | 0 |

### Tool Statistics

| Tool | Calls | Success | Failure | Success Rate |
|------|-------|---------|---------|--------------|
| execute_shell | 5 | 5 | 0 | 100.0% |
| read_file | 8 | 8 | 0 | 100.0% |
| write_file | 12 | 12 | 0 | 100.0% |
| web_search | 4 | 4 | 0 | 100.0% |
| call_agent | 6 | 6 | 0 | 100.0% |
| complete_task | 4 | 4 | 0 | 100.0% |

### Event Timeline

- **10:58:00** - 🚀 `orchestrator` started: AI trends...
  - **10:58:05** - 🔧 `orchestrator` → `execute_shell`
  - **10:58:05** - ✓ `execute_shell`: total 8...
  - **10:58:07** - 🔧 `orchestrator` → `read_file`
  - **10:58:07** - ✓ `read_file`: 1→AI trends
  - **10:58:10** - 🔧 `orchestrator` → `call_agent`
- **10:58:10** - 🚀 `searcher` started: Search for comprehensive information on AI trends...
  - **10:58:15** - 🔧 `searcher` → `web_search`
  - **10:58:20** - ✓ `web_search`: Found 15 sources...
  - **10:58:25** - 🔧 `searcher` → `write_file`
  - **10:58:25** - ✓ `write_file`: Created search_results.md (250 lines)
- **10:58:30** - ✅ `searcher` completed (15 steps)
  - **10:58:30** - ✓ `call_agent`: Searcher completed successfully
...
```

**用途**：
- 快速理解研究流程
- 查看agent调用关系
- 分析成功率和性能

## 使用场景

### 场景1：分析Agent决策

**问题**：orchestrator为什么调用了3次searcher？

**方法**：
1. 查看 `agent_trace.md` 的 Event Timeline
2. 找到每次 `call_agent(searcher)` 的时间点
3. 查看之前的工具调用，理解上下文
4. 分析：第一次搜索 → analyzer发现gaps → 第二次搜索填补 → 第三次搜索细化

**改进**：可能需要优化searcher的prompt，让它一次搜索更全面

### 场景2：识别低效模式

**问题**：研究耗时过长

**方法**：
1. 查看Session Summary的Duration
2. 查看Tool Statistics的调用次数
3. 发现某个工具被调用了过多次（如read_file被调用50次）
4. 在timeline中查找重复读取相同文件的情况

**改进**：优化prompt，让agent记住已读内容，避免重复读取

### 场景3：调试框架Bug

**问题**：某次运行失败了，不知道哪里出错

**方法**：
1. 查看 `agent_trace.md` 找到失败的agent/tool
2. 查看 `agent_trace.jsonl` 获取完整错误信息
3. 追踪失败之前的操作序列
4. 定位问题（如：文件路径错误、API调用失败）

**改进**：修复bug或改进错误处理

### 场景4：优化Agent Prompt

**问题**：想优化searcher的prompt

**方法**：
1. 运行几次研究，都开启debug模式
2. 对比不同研究的searcher调用模式：
   - 调用了几次？
   - 每次搜索了什么？
   - 哪些搜索是重复的？
   - 哪些gaps是后续才发现的？
3. 识别模式，调整prompt

**改进**：让searcher更主动地预测可能的gaps，一次搜索更全面

## 分析工具示例

### Python脚本分析JSONL

```python
import json
from collections import Counter

# 分析工具调用频率
tool_calls = []
with open("agent_trace.jsonl") as f:
    for line in f:
        event = json.loads(line)
        if event["event_type"] == "tool_call":
            tool_calls.append(event["tool_name"])

print("Tool call frequency:")
for tool, count in Counter(tool_calls).most_common():
    print(f"  {tool}: {count}")
```

### jq查询示例

```bash
# 查找所有失败的tool调用
cat agent_trace.jsonl | jq 'select(.event_type == "tool_result" and .success == false)'

# 统计每个agent的调用次数
cat agent_trace.jsonl | jq 'select(.event_type == "agent_start") | .agent_type' | sort | uniq -c

# 查找特定agent的所有工具调用
cat agent_trace.jsonl | jq 'select(.agent_type == "searcher" and .event_type == "tool_call")'
```

## 最佳实践

### 1. 对比分析

运行同一个topic多次，对比trace文件，找出：
- 稳定的模式（应该保留）
- 不稳定的行为（需要改进）
- 效率差异（优化机会）

### 2. 建立基准

保存几个"好的"研究的trace文件作为基准，用于：
- 评估新改动的影响
- 检测性能回归
- 指导新prompt设计

### 3. 定期审查

每次框架改动后：
1. 运行相同的测试case
2. 对比trace文件
3. 确认改进效果

### 4. 文档化发现

将trace分析的发现记录下来：
- 哪些模式是好的
- 哪些问题已识别
- 改进措施和效果

## 示例分析流程

```bash
# 1. 运行研究（debug模式）
uv run researcher research "AI trends" --llm openai -d

# 2. 查看摘要
cat workspace/xxx/agent_trace.md

# 3. 分析关键问题
# - orchestrator调用了几次searcher？为什么？
# - 有重复的工具调用吗？
# - 成功率如何？

# 4. 深入分析（如果需要）
cat workspace/xxx/agent_trace.jsonl | jq '...'

# 5. 识别改进点
# - prompt优化
# - 框架改进
# - 新工具需求

# 6. 实施改进并重新测试
```

## 总结

Agent Trace Logger 是框架迭代改进的关键工具。通过它，你可以：

✅ **看到**：完整的agent工作过程
✅ **理解**：为什么做某个决策
✅ **发现**：低效和问题
✅ **改进**：prompt和框架设计
✅ **验证**：改进效果

在debug模式下运行，让每次研究都成为框架改进的学习机会！
