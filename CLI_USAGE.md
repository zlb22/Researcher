# CLI Usage Guide

The Researcher CLI provides a command-line interface with real-time visualization for deep research projects.

## Installation

```bash
# Install dependencies
uv sync

# The CLI is automatically available as `researcher`
uv run researcher --help
```

## Commands

### 1. Start New Research

Start a new research project on any topic:

```bash
# Basic usage
uv run researcher research "quantum computing applications in finance"

# With custom workspace
uv run researcher research "AI safety trends" -w ./my-research

# With OpenAI (or compatible) provider
uv run researcher research "climate change solutions" --llm openai

# With custom model
uv run researcher research "blockchain scalability" --llm anthropic -m claude-3-opus-20240229

# With more steps for complex research
uv run researcher research "comprehensive analysis of renewable energy" -s 200

# Without UI (simple text output)
uv run researcher research "quick topic overview" --no-ui

# Export final report to a specific path
uv run researcher research "AI agents in production" -r ./report.md

# Print final report to stdout (useful for piping)
uv run researcher research "RAG best practices" -r -
```

### 2. Continue Existing Research

Continue and refine an existing research project:

```bash
# Continue from workspace
uv run researcher continue-research -w ./workspace/abc12345

# With additional task
uv run researcher continue-research -w ./workspace/abc12345 -t "Add more details on implementation challenges"

# With different provider
uv run researcher continue-research -w ./workspace/abc12345 --llm openai

# Export the latest final report after continuation
uv run researcher continue-research -w ./workspace/abc12345 -t "Polish the executive summary" -r ./final.md
```

### 3. List Research Projects

List all research projects in the workspace:

```bash
# List all projects
uv run researcher list-research

# List from custom workspace root
uv run researcher list-research -w ./my-workspace
```

## Real-Time Visualization

The CLI features a live UI similar to Claude Code that shows:

- **Agent Activity**: Real-time view of which agent is running (Orchestrator, Searcher, Analyzer, Writer)
- **Tool Calls**: Each tool call with arguments and results
- **File Operations**: Files being created, modified, or read
- **Progress**: Current step and overall progress
- **Status**: Live statistics on file operations and activity

### Color Coding

- 🔵 **Orchestrator** (Blue): Main coordinator making high-level decisions
- 🟢 **Searcher** (Green): Web search and information gathering
- 🟡 **Analyzer** (Yellow): Deep analysis of collected data
- 🟣 **Writer** (Purple): Report and document creation

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ Activity Log                                            │
│ 12:34:56 ▶ ORCHESTRATOR: Research quantum computing... │
│ 12:34:57 orchestrator → call_agent: searcher           │
│ 12:34:58   searcher → web_search: quantum computing    │
│ 12:34:59   searcher ✓ web_search: Found 15 sources     │
│ 12:35:00 📄 CREATE: workspace/search_results.md         │
│ ...                                                     │
├─────────────────────────────────────────────────────────┤
│ Status                                                  │
│ Current Agent:  ORCHESTRATOR                            │
│ Step:           5                                       │
│                                                         │
│ Files Created:  3                                       │
│ Files Modified: 1                                       │
└─────────────────────────────────────────────────────────┘
```

## Environment Variables

Configure LLM providers using environment variables:

```bash
# Anthropic Claude (default)
export ANTHROPIC_API_KEY="your-api-key"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"  # Optional

# OpenAI (or compatible: DeepSeek, Ollama, etc.)
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional
export OPENAI_MODEL="gpt-4"  # Optional

# Tavily Search (required for web search)
export TAVILY_API_KEY="your-tavily-key"
```

## Examples

### Example 1: Quick Research with Visualization

```bash
uv run researcher research "Python async/await best practices"
```

This will:
1. Create a workspace in `./workspace/<random-id>/`
2. Show live visualization of agent activity
3. Save research results to the workspace
4. Display final summary with output files

### Example 2: Deep Research with Custom Settings

```bash
uv run researcher research \
  "Comprehensive analysis of large language model architectures" \
  -w ./llm-research \
  -s 200 \
  --llm anthropic \
  -m claude-3-opus-20240229
```

This will:
1. Use custom workspace `./llm-research/`
2. Allow up to 200 orchestrator steps for thorough research
3. Use Claude Opus for maximum capability
4. Show live visualization throughout

### Example 3: Continue and Refine

```bash
# Initial research
uv run researcher research "blockchain scalability solutions" -w ./blockchain

# Later, add more detail
uv run researcher continue-research \
  -w ./blockchain \
  -t "Add section on zero-knowledge rollups"
```

### Example 4: Batch Research Without UI

```bash
# For scripting/automation
uv run researcher research "topic overview" --no-ui > results.txt 2>&1
```

### Example 5: Export Final Report

```bash
# Save the final report markdown to a chosen path
uv run researcher research "Prompt engineering techniques" -r ./out/FINAL.md

# Stream the final report to stdout (combine with tools like tee)
uv run researcher research "LLM evaluation methods" -r - | tee report.md
```

## Workflow Structure

The CLI supports the dynamic, non-linear research workflow:

1. **Orchestrator** analyzes the research question
2. Dynamically decides which agent to call:
   - **Searcher** for gathering information
   - **Analyzer** for deep analysis
   - **Writer** for documentation
3. Iterates based on findings:
   - Search → Analyze → Search again (if gaps found)
   - Analyze → Write → Analyze (if more detail needed)
   - Complete flexibility in workflow order

## Output Structure

Each research project creates:

```
workspace/<research-id>/
├── question.txt              # Original research question
├── workspace/               # Agent-organized work area
│   ├── search_results/      # (example - agent decides structure)
│   ├── analysis/            # (example - agent decides structure)
│   └── ...
└── report.md                # Final report (if generated)
```

Note on reports:
- By default, the Writer agent saves the single comprehensive report as `./FINAL_REPORT.md` at the workspace root.
- Use `-r/--report-out <PATH>` to export a copy to any path or `-` to print it to stdout.

The structure is **not predetermined** - agents organize information as they see fit.

## Tips

1. **Use descriptive topics**: Clear, specific research questions yield better results
2. **Adjust max-steps**: Complex research may need more steps (150-200)
3. **Review workspace**: Check intermediate files to understand agent thinking
4. **Continue research**: Iteratively refine by using `continue-research`
5. **Watch the UI**: The live visualization shows agent decision-making in real-time

## Troubleshooting

### API Key Errors

```bash
# Make sure environment variables are set
echo $ANTHROPIC_API_KEY
echo $TAVILY_API_KEY
```

### Workspace Issues

```bash
# Check workspace permissions
ls -la ./workspace/

# Manually inspect workspace
cd ./workspace/<research-id>/
ls -la
cat question.txt
```

### UI Not Showing

```bash
# Make sure rich is installed
uv sync

# Try with --no-ui to see text output
uv run researcher research "test topic" --no-ui
```

## Advanced Usage

### Custom LLM Providers

Use any OpenAI-compatible API:

```bash
# DeepSeek
export OPENAI_BASE_URL="https://api.deepseek.com"
export OPENAI_API_KEY="your-deepseek-key"
export OPENAI_MODEL="deepseek-chat"

uv run researcher research "topic" --llm openai

# Local Ollama
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="dummy"  # Ollama doesn't need a real key
export OPENAI_MODEL="llama2"

uv run researcher research "topic" --llm openai
```

### Programmatic Usage

The CLI can be imported and used programmatically:

```python
from researcher.cli.ui import ResearchUIDisplay
from researcher.agents.orchestrator import create_orchestrator
from researcher.llm.anthropic_client import AnthropicClient

# Create components
workspace = "./my-research"
llm_client = AnthropicClient()
orchestrator = create_orchestrator(llm_client, workspace)
ui = ResearchUIDisplay(workspace)

# Run with UI
ui.start("Research topic")
result = await orchestrator.run("Research quantum computing")
ui.stop()
ui.print_final_summary(result.success, result.content, result.metadata.get("output_files", []))
```
