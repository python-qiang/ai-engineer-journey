# 跨周次分流决策记录（Cross-Week Deferrals）

> **这个文件是什么：** 当我们在某一节做内容边界划分时，会把一些内容"分流"到后续周次。
> 这里记录每一次分流的**前因后果**，供将来规划对应周次时参考。
>
> **怎么用这个文件（重要）：**
> - 开新周/新节前，先查这里有没有"分流到本周"的欠账，确保衔接（承接前面埋的伏笔、不重复、不遗漏）。
> - 但这是**参考，不是照搬清单**。必须结合开课时的最新工业实践重新 review。
>   我们过往的思考很有价值，但也可能过时——不能因为"之前规划过"就跳过独立思考。
> - 分流内容一旦在目标周真正落地，就在这里标记"✅ 已落地"并简述实际怎么做的。

---

## 分流记录

### D1. Week 2 Section 4 → 多个后续周次

**分流时间/地点：** 规划 Week 2 Section 4「Prompt Behavior Control」时。

**背景：** 咨询了 Gemini + ChatGPT 关于 2026 年 Prompt 工程现状。两家都指出：现代 Prompt 相关内容（Reasoning Control、结构化输出、评估、优化、注入防御、Context Engineering）加起来远超一节课的容量。核心原则——**Section 4 只做"纯语言/排版控制模型行为 + 建立实验对比思维"，其余分流**，以保持"先手写理解、再引入框架"的学习理念。

**Section 4 保留：** Zero/Few-shot 对照、Reasoning Control（重点）、传统 CoT 对照实验、纯 prompt 约束、Prompt Cache 排版、Mini Experiment Runner。

**分流出去的内容：**

| 内容 | 分流到 | 为什么在 S4 不做 | 目标周要怎么做 / 达到什么效果 |
|------|--------|----------------|--------------------------|
| Pydantic / JSON Schema / Structured Outputs API / 校验重试 | **第3周** | S4 只让学生**体验**"纯 prompt 控制 JSON 的不确定性"(04c)，故意不给确定性方案 | 第3周开头呼应"还记得 04c 纯 prompt 控制不稳定吗"，用 Pydantic + Structured Outputs API + ValidationError 重试**彻底解决**。形成"S4 尽量让模型听话 → 第3周即使模型不听话系统也不崩"的边界 |
| Tool-use prompting（何时调工具/工具描述） | **第4周** | 工具调用是 Function Calling 的核心，独立成周 | 确认第4周覆盖 tool 描述质量、tool_choice、何时调用等 prompt 层技巧 |
| DSPy / GEPA / MIPRO / Meta-prompting | **第9周+ / 第16周** | 这些是"程序优化"层，必须先有手写 prompt + 手写实验 + 评估基础才有意义。现在直接上会让学生失去"为什么需要框架"的理解 | 第9周框架阶段可引入 DSPy 的 Signature→Module→Metric→Optimizer 思想；GEPA/自动优化留第16周评估之后。用户公司有内部 prompt 优化网站，届时可对照理解其底层 |
| 完整 Evaluation 框架 / LLM-as-Judge / Ragas / 回归测试 / golden dataset | **第16周** | S4 只建立"实验对比意识"(04e Mini Runner，50-100行，非框架)；S5 做"Micro-Eval"(固定用例跑分对比) | 第16周承接 04e 的手写 runner 和 S5 的 micro-eval，引入 Ragas/LLM-as-Judge/CI/回归测试/版本管理。让学生经历过"手写实验的局限"后，才理解自动化评估框架的价值 |
| Prompt Injection 深入 / instruction hierarchy / untrusted content 隔离 | **第12周 / 第15周** | S4 只做"纯 prompt 末尾加防御句"体验基础概念 | 第12周 Agent+MCP 做 instruction hierarchy、trust boundary；第15周 Harness 做输入/输出护栏、注入检测的工程实现 |
| Verification / self-check 深化 | **第15周** | S4 (04b) 只做 verification 的**基础概念**(prompt 里加"回答前先验证") | 第15周 Harness 承接，做成完整的 self-correction 循环(生成→执行→报错→反馈→重试) |
| Context Engineering 系统化 | **第13周** | Section 3 已手写(滑动窗口/摘要/动态prompt/token预算/memory)，属于 context engineering 雏形 | 第13周 LangGraph State 把手写的 context 管理系统化(State/Node/持久化)，呼应 Section 3 |
| KV-Cache 内部原理(K/V tensor / PagedAttention / cache eviction) | **不进入应用主线** | S4 只做应用层的"cache-friendly 排版"(观测 cached_tokens)，不碰 Transformer 内部 | 如未来想深入，属于 LLM Serving/Infra 方向，不在 AI 应用工程主线 |

**衔接检查清单（到对应周开始前逐一确认）：**
- [ ] 第3周：是否呼应 04c、用 API+Pydantic 解决纯 prompt 的不确定性
- [ ] 第4周：是否覆盖 tool prompting
- [ ] 第9周：是否引入 DSPy 思想
- [ ] 第12周：是否做 instruction hierarchy / 注入防御
- [ ] 第13周：是否呼应 Section 3 的 context 管理
- [ ] 第15周：是否承接 04b 的 verification 做 self-correction
- [ ] 第16周：是否承接 04e/S5 的 runner，引入完整评估 + 回收 DSPy/GEPA

---

<!-- 后续每次分流，在下面追加 D2、D3... 保持同样的结构：背景/保留/分流表/衔接清单 -->
