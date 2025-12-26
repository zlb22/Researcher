# Researcher

[English](/README.md) | [简体中文](/README.zh-CN.md)

A minimal‑scaffold deep research system powered by multi‑agent collaboration (Orchestrator, Searcher, Analyzer, Writer) with a real‑time terminal UI.

<!-- Hero Demo: GIF auto-plays and loops on GitHub -->
<p align="center">
  <img
    src="docs/demo.gif"
    alt="Researcher CLI Demo"
    width="100%"
    style="max-width: 960px; border-radius: 8px;"
  />
</p>
<p align="center">
  <a href="resaercher-demo.mp4">Download MP4</a>
</p>

## Motivation

Most “deep research” systems follow a pipeline of “gather in parallel → aggregate → write”.  
As models get stronger, overly rigid scaffolding can become a constraint on the model’s own planning and reasoning.

This project explores a “minimal scaffolding, maximal freedom” approach to deep research.  
At the core is a main Agent, assisted by specialized Agents exposed as tools (agent‑as‑tool), such as Searcher and Analyzer.  
The main Agent is not forced into a fixed flow; it autonomously decides when to search, analyze, or write.

To avoid the “too much assistant output to read” problem, we use layered memory and reading:
- Assistants persist long content to the filesystem and decide how to organize it.
- They return “short summaries + file index” to the main Agent. The main Agent reads details on demand via file tools.
- The main Agent operates with a rhythm of “overview → selective drill‑down → next action”.

This enables high‑level planning within limited context while assistants extend memory and depth.  
The result is a minimal‑scaffold, tool‑based multi‑agent system that leverages the filesystem for layered reading and long‑term accumulation.

## Quick Start

- Requirements
  - Python >= 3.11
  - uv (recommended) or pip
  - LLM API keys: Anthropic (default) or OpenAI; optional Tavily for search

- Install
  - In repo root:
    - Using uv (recommended): `uv sync`
    - Or pip: `python -m venv .venv && source .venv/bin/activate && pip install -e .`

- Configure
  - Copy `.env.example` to `.env` and fill your keys, or export env vars:
    - Anthropic (default)
      - `export ANTHROPIC_API_KEY="your-key"`
      - Optional: `export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"`
    - OpenAI (or compatible)
      - `export OPENAI_API_KEY="your-key"`
      - Optional: `export OPENAI_BASE_URL="https://api.openai.com/v1"`
      - Optional: `export OPENAI_MODEL="gpt-4o"`
    - Tavily Search
      - `export TAVILY_API_KEY="your-key"`

- Run
  - Minimal example (with live UI):
    - `uv run researcher research "Python async/await best practices"`
  - Use OpenAI or custom model:
    - `uv run researcher research "RAG best practices" --llm openai -m gpt-4o`
  - No UI (good for scripts/CI):
    - `uv run researcher research "topic overview" --no-ui`
  - Continue an existing workspace:
    - `uv run researcher continue-research -w ./workspace/<id> -t "Add more details"`
  - List projects:
    - `uv run researcher list-research`

## Examples

- Minimal run with UI:
  - `uv run researcher research "Python async/await best practices"`
- Custom workspace and more steps:
  - `uv run researcher research "RAG best practices" -w ./workspace/rag-demo -s 50`
- Export report to stdout (pipe to file):
  - `uv run researcher research "topic overview" -r - | tee report.md`
- Continue an existing project with a refinement task:
  - `uv run researcher continue-research -w ./workspace/<id> -t "Add more details"`

## What You Get

Each run creates a workspace under `./workspace/<auto-id>/`:
- `question.txt`: original research question
- If writing completes: `FINAL_REPORT.md` at workspace root (single, comprehensive report)
- Other intermediate files are organized by agents as needed


## TODO_LIST

- running DeepResearch Bench
