# Citation Management - 完整URL引用技术方案

## 目标
在最终报告中添加标准的学术引用格式，包含：
- 内联引用：`[1]`, `[2]` 等
- References部分：完整的URL链接

## 当前问题分析

### 1. 数据流现状
```
TavilySearchTool.execute()
  ↓ 返回 ToolResult
  ├── content: 摘要（只有前3个source的title+snippet）
  └── metadata:
      └── response: 完整的Tavily API响应
          └── results: [ {title, url, content, score}, ... ]
              ↑ URL在这里！但没被使用
```

### 2. Searcher当前行为
- 调用web_search获取结果
- 从ToolResult.content读取摘要（没有URL）
- 将摘要信息写入markdown文件
- **问题**：URL在metadata.response.results里，但没被提取和保存

### 3. Writer当前行为
- 读取searcher保存的markdown文件
- 整理信息生成报告
- **问题**：markdown文件里没有URL，所以无法生成引用

---

## 技术方案设计

### 方案概览

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: TavilySearchTool                                   │
│ ✓ 已有完整数据，无需修改                                      │
│   metadata.response.results = [{title, url, content}, ...]  │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Searcher Agent (需要修改)                           │
│ 1. 从ToolResult.metadata.response.results提取URL            │
│ 2. 保存格式化的引用信息到markdown                             │
│ 3. 维护一个citations.json（可选，用于writer aggregation）    │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Writer Agent (需要修改)                             │
│ 1. 收集所有markdown文件中的引用信息                           │
│ 2. 去重和编号                                                │
│ 3. 在报告中插入内联引用[1]                                    │
│ 4. 在报告末尾生成References部分                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 详细实现方案

### Phase 1: TavilySearchTool (无需修改)

**现状**：✅ 已完美
```python
metadata = {
    "response": {
        "results": [
            {
                "title": "CDC Adult Obesity Maps",
                "url": "https://www.cdc.gov/obesity/data/...",
                "content": "...",
                "score": 0.95
            },
            # ... more results
        ]
    }
}
```

---

### Phase 2: Searcher Agent (关键修改点)

#### 选项A：在Prompt中指导（推荐）⭐

**优势**：
- 不改代码，只改prompt
- 灵活，agent自己决定如何组织
- 30分钟即可完成

**Searcher Prompt 修改**：
```markdown
# 添加到 searcher.txt

CITATION MANAGEMENT (IMPORTANT):
When saving search results from web_search tool, you MUST preserve citation information:

1. After each web_search call, extract URLs from the tool result metadata:
   - The metadata.response.results contains full citation data
   - Each result has: title, url, content, score

2. Save citations in your markdown files using this format:
   ```markdown
   ## Finding Title

   [Content summary here...]

   **Source**: Title (Year if available)
   **URL**: https://example.com/full-url
   ```

3. Example:
   ```markdown
   ## Student Debt and Obesity Relationship

   Research shows that student debt >$50,000 increases obesity risk by 35%.

   **Source**: American Journal of Preventive Medicine (2023)
   **URL**: https://ajpm.org/article/...
   ```

4. Keep a running list of all sources at the end of your summary files:
   ```markdown
   ## References
   1. CDC Adult Obesity Maps (2024) - https://cdc.gov/...
   2. NHANES Data Brief (2023) - https://cdc.gov/nchs/...
   ```

WHY THIS MATTERS:
- Writer agent will use these URLs to create proper academic citations
- Ensures research is verifiable and credible
- Follows academic integrity standards
```

**预期效果**：
Searcher会在markdown文件中保存URL，例如：
```markdown
# 学生债务与肥胖关系

研究发现学生债务>$50,000增加35%肥胖风险。

**Source**: American Journal of Preventive Medicine (2023)
**URL**: https://www.ajpmonline.org/article/S0749-3797(23)00123-4

## References
1. CDC Adult Obesity Maps (2024) - https://www.cdc.gov/obesity/data/prevalence-maps.html
2. Student Debt and Health Study (2020) - https://example.com/study
```

#### 选项B：添加专用CitationTool（完整方案，不推荐）

**优势**：
- 引用管理标准化
- 可以自动去重、格式化

**劣势**：
- 需要开发新tool
- 增加复杂度
- overkill for current needs

**暂不推荐实施**

---

### Phase 3: Writer Agent (关键修改点)

#### Writer Prompt 修改

```markdown
# 添加到 writer.txt

CITATION AND REFERENCES MANAGEMENT (CRITICAL):

1. COLLECTING CITATIONS:
   When reading research files, look for citation information in these formats:
   - **Source**: ... **URL**: ...
   - ## References sections
   - Any markdown files with URLs

2. CREATING INLINE CITATIONS:
   - Assign sequential numbers [1], [2], [3]... to each unique source
   - Use consistent numbering throughout the report
   - Example: "Young adult obesity rate is 34-36% [1]"

3. BUILDING REFERENCES SECTION:
   At the END of your report, create a References section:

   ```markdown
   ## References

   [1] CDC Adult Obesity Maps (2024). *CDC Obesity Data & Statistics*.
       https://www.cdc.gov/obesity/data/prevalence-maps.html

   [2] Smith, J. et al. (2023). Student Debt and Health Outcomes. *American Journal of Preventive Medicine*.
       https://www.ajpmonline.org/article/S0749-3797(23)00123-4

   [3] Trust for America's Health (2024). *State of Obesity Report*.
       https://www.tfah.org/report-details/state-of-obesity-2024/
   ```

4. CITATION WORKFLOW:
   Step 1: Read all research/analysis files
   Step 2: Extract unique sources with URLs
   Step 3: Assign sequential numbers
   Step 4: Write report with inline citations [1], [2]
   Step 5: Add References section at end

5. CITATION FORMAT GUIDELINES:
   - Author/Organization (Year). Title. Publication (if applicable).
   - URL on new line (full, clickable link)
   - Use markdown formatting for readability
   - Sort by citation number (order of first appearance)

6. HANDLING MISSING INFORMATION:
   - If no URL available: Use "Source: [Description from file]" format
   - If no year: Use "n.d." (no date)
   - If no author: Use organization or website name

7. QUALITY CHECKS:
   - All data claims should have a citation
   - All citations in text must have corresponding References entry
   - All References entries should be cited in text
   - URLs should be complete and properly formatted

EXAMPLE INTEGRATION:

## Executive Summary

Young adult obesity affects 34-36% of Americans aged 18-35 [1]. Research shows that
student debt exceeding $50,000 increases obesity risk by 35% [2]. Food deserts
impact approximately 19% of the US population [3].

...

## References

[1] CDC Adult Obesity Maps (2024). *CDC Obesity Data & Statistics*.
    https://www.cdc.gov/obesity/data/prevalence-maps.html

[2] Johnson, A. & Smith, B. (2023). Financial Stress and Health Outcomes in Young Adults.
    *American Journal of Preventive Medicine*, 45(2), 123-145.
    https://www.ajpmonline.org/article/S0749-3797(23)00123-4

[3] USDA Economic Research Service (2023). *Food Access Research Atlas*.
    https://www.ers.usda.gov/data-products/food-access-research-atlas/
```

---

## 实施步骤

### Step 1: 修改 Searcher Prompt (15分钟)
```bash
编辑: src/researcher/prompts/searcher.txt
添加: CITATION MANAGEMENT section
```

### Step 2: 修改 Writer Prompt (15分钟)
```bash
编辑: src/researcher/prompts/writer.txt
添加: CITATION AND REFERENCES MANAGEMENT section
```

### Step 3: 测试 (30分钟)
```bash
# 运行一个小型测试研究
uv run researcher research "COVID-19 vaccine effectiveness 2024" --llm openai -d

# 检查：
# 1. searcher保存的文件是否包含URL
# 2. writer生成的报告是否有内联引用[1]
# 3. 报告末尾是否有References部分
# 4. URL是否完整且可点击
```

### Step 4: 迭代优化 (可选)
- 如果引用格式不理想，调整prompt
- 如果URL丢失，检查searcher是否正确提取
- 如果引用编号混乱，优化writer的citation tracking逻辑

---

## 预期效果

### Before (当前)
```markdown
# 美国年轻成年人肥胖问题

年轻成年人肥胖率约34-36%。学生债务>$50,000增加35%肥胖风险。
```

### After (改进后)
```markdown
# 美国年轻成年人肥胖问题

## Executive Summary

年轻成年人肥胖率约34-36% [1]。学生债务>$50,000增加35%肥胖风险 [2]。
食品荒漠影响约19%的美国人口 [3]。

## 主要发现

...detailed content with citations [4], [5]...

## References

[1] CDC Adult Obesity Maps (2024). *CDC Obesity Data & Statistics*.
    https://www.cdc.gov/obesity/data/prevalence-maps.html

[2] Johnson, A. & Smith, B. (2023). Financial Stress and Health Outcomes in Young Adults.
    *American Journal of Preventive Medicine*, 45(2), 123-145.
    https://www.ajpmonline.org/article/S0749-3797(23)00123-4

[3] USDA Economic Research Service (2023). *Food Access Research Atlas*.
    https://www.ers.usda.gov/data-products/food-access-research-atlas/

[4] Trust for America's Health (2024). *State of Obesity 2024 Report*.
    https://www.tfah.org/report-details/state-of-obesity-2024/

[5] NHANES (2023). National Health and Nutrition Examination Survey Data.
    https://www.cdc.gov/nchs/nhanes/index.htm
```

---

## 风险与应对

### 风险1: Searcher不提取URL
**概率**: 低 (prompt很明确)
**应对**: 在prompt中加强 "MUST preserve URLs" 的指令

### 风险2: Writer引用格式不一致
**概率**: 中 (LLM可能有创造性)
**应对**: 在prompt中提供详细的格式示例

### 风险3: URL链接断开/失效
**概率**: 高 (互联网常见问题)
**应对**:
- 在References中同时包含标题和URL
- 即使URL失效，标题仍可用于手动查找

### 风险4: 引用编号混乱
**概率**: 低-中 (取决于writer的实现)
**应对**: 在prompt中明确说明 "sequential numbering [1], [2], [3]"

---

## 替代方案对比

| 方案 | 优势 | 劣势 | 实施时间 |
|------|------|------|---------|
| **方案A: Prompt优化** (推荐) | 简单、灵活、无代码改动 | 依赖LLM理解和执行 | 30分钟 |
| 方案B: 添加CitationTool | 标准化、可靠 | 复杂、overkill | 3-4小时 |
| 方案C: 后处理脚本 | 可以批量处理历史报告 | 需要维护额外脚本 | 2小时 |

---

## 下一步行动

如果同意此方案，执行顺序：
1. ✅ 审阅方案，确认技术可行性
2. ⬜ 修改 searcher.txt prompt
3. ⬜ 修改 writer.txt prompt
4. ⬜ 运行测试研究
5. ⬜ 检查引用质量
6. ⬜ 必要时迭代优化
7. ⬜ Commit changes

---

## 问题讨论

1. **引用格式偏好**：APA? MLA? 还是简化版？
2. **Searcher中间文件格式**：当前设计够用吗？还是需要单独的citations.json？
3. **Writer的智能程度**：相信LLM能正确分配引用编号吗？还是需要额外验证逻辑？
