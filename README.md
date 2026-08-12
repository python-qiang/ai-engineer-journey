# AI Engineer Journey

20 周从软件开发工程师转型 AI 应用工程师的实战学习项目。

## 学习路线

| 阶段 | 周数 | 主题 | 状态 |
|------|------|------|------|
| 一 | 1-4 | 底层原语、成本与本地化 | 🚧 进行中 |
| 二 | 5-8 | 手搓 RAG 与 Embedding 选型 | ⏳ |
| 三 | 9-12 | 框架、进阶 RAG、多模态与 MCP | ⏳ |
| 四 | 13-16 | 编排、可观测性与 Harness | ⏳ |
| 五 | 17-20 | 全栈整合与业务交付 | ⏳ |

## 技术栈

- **语言**: Python / JavaScript
- **本地模型**: Ollama (qwen3:4b, qwen2.5:1.5b)
- **云端 API**: 阿里云百炼 (OpenAI 兼容格式, qwen3.7-plus)
- **后续**: LangChain, LangGraph, FastAPI, Next.js, ChromaDB, MCP

## 项目结构

```
ai-engineer-journey/
├── docs/                          # 学习大纲与参考文档
│   └── AI_Engineer_20周实战大纲.md
├── src/
│   ├── framework/                 # 共享配置 (API URLs 等)
│   ├── week01_api_basics/         # HTTP调用、Token计算、SSE流式、Ollama、参数调优
│   │   └── docs/                  # Week 1 学习笔记
│   ├── week02_prompt/             # Prompt工程与对话管理
│   │   └── docs/                  # Week 2 学习笔记
│   ├── week03_structured_output/  # Pydantic + JSON Schema
│   ├── week04_function_calling/   # 手写 Function Calling
│   ├── week05_embedding/          # 向量与语义搜索
│   ├── ...
│   └── week20_career/             # 简历与面试
├── .envrc                         # direnv 自动加载环境
└── .nvmrc                         # Node.js 版本锁定
```

## 快速开始

```bash
# 环境要求: Python 3.13+, Node.js 22+, Ollama

# 1. 克隆
git clone https://github.com/python-qiang/ai-engineer-journey.git
cd ai-engineer-journey

# 2. Python 环境
python -m venv .venv
source .venv/bin/activate
pip install httpx tiktoken

# 3. 配置环境变量 (创建 .env.dev, direnv 自动加载)
export PYTHONPATH=$(expand_path ./src)
export BEIJING_API_KEY=你的阿里云百炼API_KEY

# 4. Ollama (本地免费模型)
ollama pull qwen3:4b
ollama pull qwen2.5:1.5b

# 5. 运行第一个脚本
python src/week01_api_basics/01a_http_call.py
```

## 学习理念

- **先手写底层，再用框架** — 理解本质后才引入 LangChain (第9周)
- **痛点驱动** — 先体验问题，再学解决方案
- **每个文件都有学习边界** — 明确"需要掌握"和"暂不关心"
- **大纲是活的** — 随学习深入持续更新优化

## 当前进度

- [x] Week 1 Section 1: HTTP API 调用 (Python + JS)
- [x] Week 1 Section 2: Token 计算与成本估算
- [x] Week 1 Section 3: SSE 流式传输
- [x] Week 1 Section 4: Ollama 本地部署
- [x] Week 1 Section 5: 参数调优实验 (temperature, top_p, penalty, stop)
- [x] Week 2 Section 1: 消息角色体系 (system prompt, few-shot, 越狱测试)
- [x] Week 2 Section 2: 多轮对话实现 (CLI, token追踪, session管理)
- [ ] Week 2 Section 3: 上下文窗口管理策略
- [ ] Week 2 Section 4: Prompt 核心技巧
- [ ] Week 2 Section 5: Prompt 模板化工程
