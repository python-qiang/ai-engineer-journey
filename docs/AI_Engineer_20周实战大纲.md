# AI Engineer（应用工程师）20周实战演进大纲

> 适用对象：有 Python + JavaScript 基础的软件开发工程师，零 AI 基础
> 学习方式：自学 + 实战项目驱动
> 核心理念：先手写底层 → 发现痛点 → 引入框架 → 拥抱标准协议 → 全栈交付
> 预计总时长：20周（每周投入 15-20 小时）

---

## 总览


| 阶段 | 周数  | 主题                         | 核心产出                           |
| ---- | ----- | ---------------------------- | ---------------------------------- |
| 一   | 1-4   | 底层原语、成本与本地化       | 能手写 Function Calling 的完整流程 |
| 二   | 5-8   | 手搓 RAG 与 Embedding 选型   | 从零搭建一个朴素 RAG 系统          |
| 三   | 9-12  | 框架、进阶 RAG、多模态与 MCP | 掌握 LangChain + MCP 协议开发      |
| 四   | 13-16 | 编排、可观测性与 Harness     | 能构建可调试、可评估的复杂 Agent   |
| 五   | 17-20 | 全栈整合与业务交付           | 完成一个商业级 AI 应用作品集       |

---

## 阶段一：底层原语、成本与本地化（第 1-4 周）

> 目标：脱离 Web 聊天框的思维，以纯程序员视角理解 LLM API 的本质。不用任何 AI 框架，全部手写。

---

### 第 1 周：API 原语与 Ollama 本地部署

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_理解大模型 API 的 HTTP 通信本质（不是魔法，就是发 POST 请求）
- 02_掌握 Token 的分词原理，能手动计算一段文本的 Token 数
- 03_掌握 SSE（Server-Sent Events）流式传输协议，用 Python 和 JS 分别实现流式接收
- 04_在本地安装 Ollama 并跑通开源模型，建立免费无限测试环境
- 05_理解 Temperature、Top-p、Max Tokens 等参数对输出的实际影响

#### 主讲内容

##### 1. 大模型 API 的 HTTP 本质

**要做什么：** 不使用任何 SDK（不用 openai 库），纯用 Python 的 `httpx` 或 `requests` 库，手动构造 HTTP POST 请求调用大模型 API。

**要达到的效果：** 看到大模型 API 就是一个普通的 REST 接口，消除对 AI 的神秘感。

**技术点：**

- 01_HTTP POST 请求结构（headers、body、authentication）
- 02_API Key 的管理（环境变量、.env 文件，绝不硬编码）
- 03_请求体 JSON 结构：model、messages 数组、temperature 等参数
- 04_响应体解析：choices[0].message.content 的提取
- 05_错误处理：429 限流、401 认证失败、500 服务端错误的重试策略

**练习任务：**

```
任务1：用 httpx 直接调用 DeepSeek API，发送 "你好" 并打印回复
任务2：用 JavaScript fetch 调用同一个 API，在 Node.js 中打印回复
任务3：故意传错 API Key，观察并处理错误响应
任务4：封装一个 chat(message) 函数，支持传入不同参数
```

##### 2. Token 分词原理与成本计算

**要做什么：** 理解大模型不是按"字"或"词"处理文本的，而是按 Token（子词单元）。学会精确计算 Token 数量和对应费用。

**要达到的效果：** 看到任何一段文本，能估算它消耗多少 Token、花多少钱。养成"每次调用都在烧钱"的工程意识。

**技术点：**

- 06_BPE（Byte Pair Encoding）分词算法的基本原理
- 07_tiktoken 库的使用（OpenAI 系列模型的分词器）
- 08_中文 vs 英文的 Token 效率差异（中文通常 1 字 = 1.5-2 Token）
- 09_Input Token vs Output Token 的计价差异
- 10_Context Window（上下文窗口）的硬限制：4K、8K、32K、128K 的含义

**练习任务：**

```
任务1：安装 tiktoken，对同一段话分别用中文和英文计算 Token 数，对比差异
任务2：写一个 cost_calculator(text, model) 函数，输入文本和模型名，输出预估费用（元）
任务3：找一篇 5000 字的文章，计算如果全部作为 Prompt 发送，消耗多少 Token、花多少钱
任务4：实验 Context Window 与输出限制：观察输入越长响应越慢的关系，用 max_tokens 截断输出并观察 finish_reason 的变化
```

##### 3. SSE 流式传输（打字机效果的底层原理）

**要做什么：** 理解为什么 ChatGPT 的回复是一个字一个字蹦出来的。手动实现 SSE 流式接收。

**要达到的效果：** 能用 Python 和 JS 分别实现逐字输出的效果，理解 `stream=True` 背后的网络协议。

**技术点：**

- 11_SSE（Server-Sent Events）协议规范：`data:` 前缀、`[DONE]` 终止信号
- 12_Python httpx 的流式响应处理（`async for line in response.aiter_lines()`）
- 13_JavaScript EventSource API 与 fetch + ReadableStream
- 14_流式响应中每个 chunk 的 JSON 结构（delta.content）
- 15_流式 vs 非流式的延迟对比（首字延迟 TTFT）

**练习任务：**

```
任务1：用 Python httpx 实现流式调用，在终端逐字打印大模型回复
任务2：用 Node.js fetch 实现同样的流式接收
任务3：写一个计时器，测量"首个 Token 到达时间"（TTFT）和"总完成时间"
任务4：对比 stream=True 和 stream=False 的用户体验差异
```

##### 4. Ollama 本地部署与开源模型

**要做什么：** 在本地电脑安装 Ollama，下载并运行开源大模型（Qwen2、Llama3、DeepSeek 等），建立免费的本地测试环境。

**要达到的效果：** 后续所有实验都可以先在本地免费跑，验证逻辑后再切换到云端 API。

**技术点：**

- 16_Ollama 的安装与基本命令（ollama pull、ollama run、ollama serve）
- 17_Ollama 的 REST API（与 OpenAI API 格式兼容）
- 18_模型选择：Qwen2:7b（中文好）、Llama3:8b（英文好）、DeepSeek-R1:8b（推理强）
- 19_模型大小与显存/内存的关系（7B 约需 8GB RAM）
- 20_Ollama 的 Modelfile 自定义（修改系统提示词、温度等默认参数）

**练习任务：**

```
任务1：安装 Ollama，拉取 qwen2:7b 模型，在终端对话
任务2：用 Python httpx 调用 Ollama 的本地 API（http://localhost:11434），验证与云端 API 格式一致
任务3：对比同一个问题在 Qwen2:7b（本地免费）和 DeepSeek API（云端付费）的回答质量
任务4：写一个 Modelfile，创建一个"只说中文、性格幽默"的自定义模型
```

##### 5. 参数调优实验

**要做什么：** 通过对比实验，直观理解 Temperature、Top-p、Max Tokens 等参数的实际效果。

**要达到的效果：** 面对不同业务场景，能快速判断该用什么参数组合。

**技术点：**

- 21_Temperature（0-2）：越低越确定，越高越随机
- 22_Top-p（核采样）：与 Temperature 的配合关系
- 23_Max Tokens：控制输出长度上限
- 24_Frequency Penalty / Presence Penalty：控制重复度
- 25_Stop Sequences：自定义停止生成的标记

**练习任务：**

```
任务1：同一个问题，分别用 temperature=0、0.7、1.5 调用 10 次，观察输出稳定性
任务2：写一个"生成产品名"的场景，调整 temperature 找到创意与可控的平衡点
任务3：用 max_tokens=50 限制输出，观察模型如何在限制内组织语言
任务4：总结一份"参数速查表"：什么场景用什么参数
```

#### 本周验收标准

- [X]  能不用任何 SDK，纯 HTTP 调用大模型 API 并获取回复
- [X]  能准确计算任意文本的 Token 数和费用
- [ ]  能用 Python 和 JS 分别实现流式输出
- [ ]  本地 Ollama 环境搭建完成，能通过 API 调用本地模型
- [ ]  完成参数对比实验，产出参数速查表

---

### 第 2 周：Prompt 工程与对话管理

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_理解 System/User/Assistant 三种角色的严格区分和各自用途
- 02_掌握多轮对话的实现原理（大模型本身无记忆，全靠你拼接历史）
- 03_能编写高质量的 System Prompt 控制模型行为
- 04_掌握 Few-shot、Chain-of-Thought 等核心 Prompt 技巧
- 05_理解上下文窗口管理：当对话太长时如何截断/压缩

#### 主讲内容

##### 1. 消息角色体系（Messages Array）

**要做什么：** 深入理解 API 中 messages 数组的结构，明白每种角色的作用边界。

**要达到的效果：** 能精确控制大模型的"人设"和行为边界。

**技术点：**

- 01_system 角色：设定模型的身份、能力边界、输出格式要求
- 02_user 角色：用户的输入
- 03_assistant 角色：模型的历史回复（用于多轮对话）
- 04_messages 数组的顺序对输出的影响
- 05_System Prompt 的最佳实践：角色定义 + 约束条件 + 输出格式

**练习任务：**

```
任务1：写一个 System Prompt，让模型扮演"严格的代码审查员"，只指出问题不写代码
任务2：对比有 System Prompt 和没有 System Prompt 时，模型对同一问题的回答差异
任务3：写一个 System Prompt，严格限制模型只能用中文回答，测试它是否遵守
任务4：尝试用 User 消息"越狱"你的 System Prompt，观察模型的抗干扰能力
```

##### 2. 多轮对话的实现原理

**要做什么：** 理解大模型 API 是无状态的——它不记得上一轮说了什么。多轮对话完全靠你在每次请求中把历史消息全部带上。

**要达到的效果：** 能手写一个支持多轮对话的命令行聊天程序。

**技术点：**

- 06_无状态 API 的本质：每次请求都是独立的
- 07_对话历史的维护：用 Python list 存储 messages
- 08_每轮对话的 Token 消耗是累加的（历史越长越贵）
- 09_对话历史的序列化与持久化（存到文件/数据库）
- 10_会话 ID（session_id）的设计

**练习任务：**

```
任务1：写一个命令行多轮对话程序，用 while 循环 + messages 列表实现
任务2：在每轮对话后打印当前总 Token 数，观察它如何增长
任务3：聊 20 轮后，观察是否触发 Context Window 限制
任务4：实现"新建对话"功能（清空 messages 列表）
```

##### 3. 上下文窗口管理策略

**要做什么：** 当对话历史超过模型的 Context Window 时，学习各种截断和压缩策略。

**要达到的效果：** 能在长对话场景中保持模型的回答质量，同时控制成本。

**技术点：**

- 11_滑动窗口策略：只保留最近 N 轮对话
- 12_摘要压缩策略：用大模型把旧对话总结成一段摘要
- 13_重要消息标记：某些关键信息永远保留
- 14_Token 预算分配：为系统提示词、历史、用户输入、模型输出分别预留空间
- 15_实现一个 context_manager 类，自动管理对话长度

**练习任务：**

```
任务1：实现滑动窗口策略，只保留最近 10 轮对话
任务2：实现摘要压缩：当历史超过 2000 Token 时，调用模型生成摘要替代原文
任务3：对比两种策略在 30 轮对话后的回答质量
任务4：实现 Token 预算分配器，确保每次请求不超过模型限制
```

##### 4. Prompt 核心技巧

**要做什么：** 掌握让大模型输出更准确、更可控的关键 Prompt 技术。

**要达到的效果：** 面对任何业务需求，能快速设计出高质量的 Prompt。

**技术点：**

- 16_Zero-shot：直接提问，不给示例
- 17_Few-shot：给 2-3 个输入输出示例，让模型模仿
- 18_Chain-of-Thought (CoT)：让模型"一步步思考"再给答案
- 19_角色扮演（Role Playing）：赋予模型专家身份
- 20_约束与格式控制：明确告诉模型"不要做什么"

**练习任务：**

```
任务1：用 Zero-shot 让模型做情感分析，记录准确率
任务2：用 Few-shot（给 3 个示例）做同样的情感分析，对比准确率提升
任务3：用 CoT 让模型解一道数学题，对比直接回答 vs 分步思考的正确率
任务4：设计一个"客服机器人"的完整 System Prompt，包含角色、约束、格式要求
```

##### 5. Prompt 模板化工程

**要做什么：** 将 Prompt 从硬编码字符串变成可维护的模板系统。

**要达到的效果：** Prompt 可以像代码一样版本管理、参数化、复用。

**技术点：**

- 21_Python f-string / Jinja2 模板引擎做 Prompt 模板
- 22_变量注入：将业务数据动态插入 Prompt
- 23_Prompt 版本管理：用 Git 管理 Prompt 的迭代
- 24_Prompt 测试：同一个 Prompt 跑 10 次看稳定性
- 25_Prompt Library：建立自己的 Prompt 模板库

**练习任务：**

```
任务1：用 Jinja2 写一个"文本分类"的 Prompt 模板，支持动态传入类别列表和待分类文本
任务2：用 Git 管理你的 Prompt 文件夹，每次修改都 commit
任务3：写一个 prompt_test.py 脚本，对同一个 Prompt 跑 20 次，统计输出一致性
任务4：建立一个 prompts/ 目录，按场景分类存放你的所有 Prompt 模板
```

#### 本周验收标准

- [ ]  能手写一个支持多轮对话的命令行聊天程序
- [ ]  实现了至少两种上下文窗口管理策略
- [ ]  掌握 Few-shot、CoT 等技巧并有对比实验数据
- [ ]  建立了自己的 Prompt 模板库（至少 5 个模板）
- [ ]  每次 API 调用都能看到 Token 消耗和费用

---

### 第 3 周：结构化输出与数据校验

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_掌握 Pydantic 数据模型定义与校验
- 02_理解 JSON Schema 规范，能手写 Schema
- 03_掌握大模型 JSON Mode 和 Structured Outputs 的使用
- 04_能强制大模型输出 100% 符合预定义结构的数据
- 05_建立"大模型输出不可信，必须校验"的工程意识

#### 主讲内容

##### 1. Pydantic 数据模型（AI 工程的基石）

**要做什么：** 学习 Python 的 Pydantic 库，它是 AI 应用中定义数据结构、校验输入输出的核心工具。LangChain、FastAPI 都深度依赖它。

**要达到的效果：** 能用 Pydantic 定义任意复杂的数据结构，并自动校验大模型的输出是否合规。

**技术点：**

- 01_Pydantic BaseModel 的定义与使用
- 02_字段类型：str、int、float、List、Optional、Enum
- 03_字段校验器（validator）：自定义校验规则
- 04_嵌套模型：模型中包含模型
- 05_model_json_schema() 方法：自动生成 JSON Schema

**练习任务：**

```
任务1：定义一个 MovieReview 模型（title: str, rating: int 1-5, sentiment: Enum, summary: str）
任务2：用 validator 确保 rating 只能是 1-5 之间的整数
任务3：故意传入错误数据（rating=10），观察 Pydantic 的报错信息
任务4：调用 model_json_schema()，观察生成的 JSON Schema 长什么样
```

##### 2. JSON Schema 规范

**要做什么：** 理解 JSON Schema 是一种描述 JSON 数据结构的标准语言。大模型的 Function Calling 和 Structured Outputs 都依赖它。

**要达到的效果：** 能手写 JSON Schema，也能从 Pydantic 模型自动生成。

**技术点：**

- 06_JSON Schema 基本语法：type、properties、required
- 07_类型约束：string、number、integer、boolean、array、object
- 08_枚举约束：enum 字段限定可选值
- 09_嵌套对象与数组的 Schema 定义
- 10_description 字段：给大模型的"说明书"

**练习任务：**

```
任务1：手写一个"天气查询结果"的 JSON Schema（city, temperature, condition, humidity）
任务2：对比手写的 Schema 和 Pydantic 自动生成的 Schema，理解两者的对应关系
任务3：写一个包含数组的 Schema（如：一个订单包含多个商品）
任务4：在 Schema 的每个字段加上 description，解释该字段的含义
```

##### 3. 大模型 JSON Mode

**要做什么：** 使用 API 的 `response_format={"type": "json_object"}` 参数，强制大模型只输出合法 JSON。

**要达到的效果：** 解决大模型经常在 JSON 外面包裹 ```json``` 标记导致解析失败的问题。

**技术点：**

- 11_response_format 参数的使用
- 12_JSON Mode 的限制：只保证语法合法，不保证结构正确
- 13_在 Prompt 中明确描述期望的 JSON 结构
- 14_json.loads() 解析与异常处理
- 15_JSON Mode vs Structured Outputs 的区别

**练习任务：**

```
任务1：不用 JSON Mode，让模型返回 JSON，观察它经常带 ```json``` 标记
任务2：开启 JSON Mode，验证输出一定是合法 JSON
任务3：开启 JSON Mode 但不在 Prompt 中描述结构，观察模型返回的随机 JSON 结构
任务4：在 Prompt 中精确描述结构 + 开启 JSON Mode，验证输出的可控性
```

##### 4. Structured Outputs（结构化输出 API）

**要做什么：** 使用最新的 Structured Outputs API，传入 JSON Schema，让大模型 100% 按照你的 Schema 输出。

**要达到的效果：** 大模型的输出可以直接被 Pydantic 模型解析，零容错。

**技术点：**

- 16_Structured Outputs API 的调用方式（传入 json_schema）
- 17_将 Pydantic 模型转为 JSON Schema 传给 API
- 18_解析响应并用 Pydantic 模型实例化
- 19_处理模型拒绝输出的情况（refusal）
- 20_Structured Outputs 的模型兼容性（哪些模型支持）

**练习任务：**

```
任务1：定义一个"商品信息提取"的 Pydantic 模型，用 Structured Outputs 从商品描述中提取结构化数据
任务2：定义一个"会议纪要"模型（participants, decisions, action_items），从一段会议文本中提取
任务3：测试边界情况：输入完全无关的文本，观察模型如何处理
任务4：封装一个 extract(text, model_class) 通用函数，传入文本和 Pydantic 类，返回结构化对象
```

##### 5. 输出校验与重试机制

**要做什么：** 即使用了 Structured Outputs，工程上仍需要校验和重试机制作为兜底。

**要达到的效果：** 建立"永远不信任大模型输出"的防御性编程习惯。

**技术点：**

- 21_Pydantic ValidationError 的捕获与处理
- 22_重试策略：校验失败时，把错误信息反馈给模型让它修正
- 23_最大重试次数限制（防止无限循环）
- 24_降级策略：重试 N 次仍失败时的兜底方案
- 25_日志记录：记录每次校验失败的输入输出，用于后续优化 Prompt

**练习任务：**

```
任务1：故意用一个很弱的本地模型（Ollama 小模型）调用 Structured Outputs，触发校验失败
任务2：实现自动重试：校验失败 → 把错误信息加入 Prompt → 重新调用 → 再校验
任务3：设置最大重试 3 次，超过后返回默认值并记录日志
任务4：统计不同模型的"一次通过率"（第一次就校验通过的比例）
```

#### 本周验收标准

- [ ]  能熟练使用 Pydantic 定义复杂数据模型
- [ ]  能手写 JSON Schema 并理解其与 Pydantic 的对应关系
- [ ]  掌握 JSON Mode 和 Structured Outputs 的区别与使用场景
- [ ]  实现了带重试机制的结构化输出提取函数
- [ ]  建立了"校验 → 重试 → 降级"的完整防御链

---

### 第 4 周：函数调用（Function Calling）纯手写

**课时：5天 | 技术点：30项 | 学习方式：动手实操**

#### 学习目标

- 01_理解 Function Calling 的完整通信流程（模型不执行函数，只告诉你该调哪个）
- 02_能用 JSON Schema 向模型描述本地函数的签名
- 03_能手写代码解析模型返回的 tool_calls，执行对应函数，并回传结果
- 04_掌握多工具并行调用的处理
- 05_理解这是所有 Agent 和 MCP 的最底层基石

#### 主讲内容

##### 1. Function Calling 的通信流程

**要做什么：** 彻底理解 Function Calling 不是"大模型执行了你的函数"，而是一个三步握手协议：

1. 你告诉模型有哪些函数可用（tools 参数）
2. 模型决定要调用哪个函数、传什么参数（返回 tool_calls）
3. 你执行函数，把结果以 tool 角色发回给模型

**要达到的效果：** 能画出 Function Calling 的完整时序图，理解每一步的数据流。

**技术点：**

- 01_tools 参数的结构：type="function"、function.name、function.description、function.parameters
- 02_模型响应中的 tool_calls 字段：id、function.name、function.arguments
- 03_tool 角色消息的构造：tool_call_id、content（函数执行结果）
- 04_完整的消息流：user → assistant(tool_calls) → tool(result) → assistant(final answer)
- 05_tool_choice 参数：auto（模型自己决定）、required（强制调用）、none（禁止调用）

**练习任务：**

```
任务1：画出 Function Calling 的完整时序图（手画或用 Mermaid）
任务2：构造一个 tools 数组，描述 get_weather(city: str) 函数
任务3：发送请求，打印模型返回的原始 JSON，找到 tool_calls 字段
任务4：手动构造 tool 角色的消息，把"晴天 25度"作为结果发回，观察模型的最终回答
```

##### 2. 工具描述的 JSON Schema 编写

**要做什么：** 学习如何用 JSON Schema 精确描述函数的参数，让模型知道该传什么。

**要达到的效果：** description 写得越好，模型调用的准确率越高。

**技术点：**

- 06_function.parameters 的 JSON Schema 结构
- 07_参数的 type、description、enum 约束
- 08_required 字段：哪些参数是必填的
- 09_复杂参数：对象类型、数组类型的参数描述
- 10_description 的撰写技巧：告诉模型"什么时候该调用这个函数"

**练习任务：**

```
任务1：描述一个 search_database(query: str, limit: int, category: enum) 函数
任务2：描述一个 send_email(to: str, subject: str, body: str, cc: list[str]) 函数
任务3：对比 description 写得好 vs 写得差时，模型调用的准确率
任务4：用 Pydantic 模型自动生成函数参数的 JSON Schema（结合第3周知识）
```

##### 3. 手写工具调度器（Tool Dispatcher）

**要做什么：** 写一个调度器，根据模型返回的 tool_calls，自动找到对应的 Python 函数并执行。

**要达到的效果：** 这就是所有 Agent 框架的核心——你在手写一个微型 Agent 运行时。

**技术点：**

- 11_工具注册表：用 dict 映射 function_name → callable
- 12_参数解析：json.loads(tool_call.function.arguments)
- 13_函数执行与结果序列化
- 14_错误处理：函数执行报错时，把错误信息作为 tool 结果返回给模型
- 15_异步执行：多个 tool_calls 的并行处理

**练习任务：**

```
任务1：实现一个 tool_registry = {"get_weather": get_weather, "calculate": calculate} 注册表
任务2：写一个 dispatch(tool_calls) 函数，自动解析并执行所有工具调用
任务3：模拟函数执行报错（如查询不存在的城市），观察把错误返回给模型后它如何应对
任务4：实现并行调用：模型同时请求查天气和查股价，两个函数并行执行
```

##### 4. 多轮工具调用与对话循环

**要做什么：** 实现完整的 Agent 循环：模型可能需要调用多次工具才能回答一个问题。

**要达到的效果：** 写出一个 while 循环，让模型持续思考和调用工具，直到它给出最终答案。

**技术点：**

- 16_循环判断：如果响应包含 tool_calls，继续循环；否则输出 content 并退出
- 17_多步推理：模型先查天气，再根据天气推荐穿搭
- 18_最大循环次数限制（防止死循环）
- 19_对话历史的完整维护（包含所有 tool 消息）
- 20_Token 消耗的累计计算

**练习任务：**

```
任务1：实现完整的 Agent 循环（while True → 调用模型 → 检查 tool_calls → 执行 → 回传 → 重复）
任务2：测试多步场景："帮我查北京天气，如果下雨就提醒我带伞"（需要先查天气再判断）
任务3：设置 max_iterations=5，超过后强制退出并告知用户
任务4：在每次循环中打印当前步骤、调用的工具、累计 Token 数
```

##### 5. 从 Function Calling 到 Agent 的认知跃迁

**要做什么：** 回顾本周所写的代码，认识到你已经手写了一个最简 Agent。理解框架（LangChain、LangGraph）本质上就是在封装这些逻辑。

**要达到的效果：** 建立"Agent = LLM + 工具 + 循环"的核心认知。后续学框架时不再迷茫。

**技术点：**

- 21_Agent 的本质：ReAct 循环（Reasoning + Acting）
- 22_你手写的代码 vs LangChain Agent 的对应关系
- 23_工具描述的质量决定 Agent 的智能程度
- 24_当前方案的局限：没有状态管理、没有错误恢复、没有可观测性
- 25_预告：这些局限就是后续引入 LangGraph 和 Harness 的动机

**练习任务：**

```
任务1：给你的 Agent 加入 5 个工具（查天气、计算器、查时间、翻译、搜索模拟），测试它的多工具选择能力
任务2：记录 Agent 在 10 个不同问题上的表现，找出它"选错工具"的案例
任务3：尝试优化工具的 description，看能否提高选择准确率
任务4：写一份总结文档：Function Calling 的完整流程图 + 你遇到的坑 + 解决方案
```

#### 本周验收标准

- [ ]  能完整画出 Function Calling 的时序图并解释每一步
- [ ]  实现了工具注册表 + 调度器 + Agent 循环的完整代码
- [ ]  Agent 能处理多步推理场景（需要多次工具调用）
- [ ]  实现了错误处理和最大循环次数限制
- [ ]  产出一份 Function Calling 学习总结文档

---

## 阶段二：手搓 RAG 与 Embedding 选型（第 5-8 周）

> 目标：理解 RAG 不是魔法，只是"先搜索再回答"。全手动实现，不用 LangChain。

---

### 第 5 周：Embedding 与向量检索基础

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_理解 Embedding（向量嵌入）的本质：把文本变成数字数组，语义相近的文本数组也相近
- 02_掌握 Embedding API 的调用（云端 + 本地）
- 03_理解余弦相似度的计算原理（半天即可，不深入数学）
- 04_掌握 Embedding 模型的选型：不同模型在中英文、长短文本上的表现差异
- 05_能实现一个纯内存的语义搜索 Demo

#### 主讲内容

##### 1. Embedding 的本质与 API 调用

**要做什么：** 调用 Embedding API，把一段文本变成一个浮点数数组（向量）。理解"语义相近的文本，向量也相近"这个核心概念。

**要达到的效果：** 能把任意文本转为向量，并直观感受到语义相似的文本向量确实"靠近"。

**技术点：**

- 01_Embedding 的概念：文本 → 高维空间中的一个点
- 02_调用 OpenAI/DeepSeek 的 Embedding API
- 03_调用本地 Ollama 的 Embedding 模型（如 nomic-embed-text）
- 04_向量的维度：384维、768维、1536维、3072维的含义
- 05_Embedding 的输入限制：最大 Token 数

**练习任务：**

```
任务1：把 "我喜欢吃苹果" 和 "我爱吃水果" 分别转为向量，打印前 10 个维度的值
任务2：把 "我喜欢吃苹果" 和 "苹果公司股价上涨" 转为向量，准备后续对比
任务3：用 Ollama 本地 Embedding 模型做同样的事，对比速度和维度
任务4：测试超长文本（超过模型限制）时 API 的报错行为
```

##### 2. 余弦相似度（半天搞定）

**要做什么：** 用 Numpy 实现余弦相似度计算，理解"两个向量越相似，余弦值越接近 1"。

**要达到的效果：** 能计算任意两个向量的相似度分数，验证语义相似的文本确实得分高。

**技术点：**

- 06_余弦相似度公式：cos(A,B) = (A·B) / (|A| × |B|)
- 07_用 Numpy 实现：np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
- 08_相似度分数的含义：1=完全相同，0=无关，-1=完全相反
- 09_欧氏距离 vs 余弦相似度的区别与适用场景
- 10_归一化向量的简化计算

**练习任务：**

```
任务1：计算 "我喜欢吃苹果" vs "我爱吃水果" 的相似度（应该很高）
任务2：计算 "我喜欢吃苹果" vs "苹果公司股价上涨" 的相似度（应该较低）
任务3：计算 "我喜欢吃苹果" vs "量子力学的基本原理" 的相似度（应该很低）
任务4：把结果排序，验证语义越相近分数越高
```

##### 3. Embedding 模型选型实验

**要做什么：** 对比不同 Embedding 模型在中文、英文、长文本、短文本上的表现差异。这比数学重要 100 倍。

**要达到的效果：** 面对实际项目，能快速选择最适合的 Embedding 模型。

**技术点：**

- 11_主流 Embedding 模型：text-embedding-3-small/large、BGE-M3、Jina-embeddings-v3
- 12_中文 Embedding 的特殊性：BGE 系列在中文上的优势
- 13_维度与性能的权衡：维度越高越准但越慢越贵
- 14_MTEB 排行榜：如何查看模型的公开评测分数
- 15_多语言 Embedding vs 单语言 Embedding

**练习任务：**

```
任务1：准备 10 组中文语义相似/不相似的句子对
任务2：分别用 text-embedding-3-small 和 BGE（本地 Ollama）计算相似度，对比哪个更准
任务3：测试长文本（500字以上）的 Embedding 质量
任务4：制作一份"Embedding 模型选型对比表"（模型名、维度、中文表现、速度、价格）
```

##### 4. 纯内存语义搜索 Demo

**要做什么：** 不用任何数据库，用 Python list 存储向量，实现一个最简单的语义搜索。

**要达到的效果：** 输入一个问题，从 20 条预存文本中找出最相关的 3 条。

**技术点：**

- 16_文档集合的向量化：批量调用 Embedding API
- 17_暴力搜索（Brute Force）：遍历所有向量计算相似度
- 18_Top-K 检索：返回相似度最高的 K 条结果
- 19_相似度阈值：低于某个分数的结果不返回
- 20_搜索结果的格式化输出（分数 + 原文）

**练习任务：**

```
任务1：准备 20 条关于 Python 编程的 FAQ（问题+答案）
任务2：把所有问题转为向量存入 Python list
任务3：实现 search(query, top_k=3) 函数，返回最相关的 3 条
任务4：测试各种问法（同义词、口语化表达），观察搜索质量
```

##### 5. Embedding 的局限性认知

**要做什么：** 通过实验发现 Embedding 搜索的局限，为后续引入混合检索做铺垫。

**技术点：**

- 21_关键词精确匹配的失败案例（如搜索特定错误码）
- 22_长文本 vs 短文本的 Embedding 质量差异
- 23_领域专业术语的 Embedding 表现
- 24_Embedding 不理解否定（"不喜欢" vs "喜欢" 可能很相似）
- 25_预告：这些问题将在第 10 周通过混合检索解决

**练习任务：**

```
任务1：搜索一个特定的错误码（如 "ERR_CONNECTION_REFUSED"），观察语义搜索是否能找到
任务2：搜索 "不喜欢 Python" 和 "喜欢 Python"，对比它们与同一文档的相似度
任务3：记录 5 个语义搜索失败的案例，分析原因
任务4：思考：什么情况下应该用关键词搜索而非语义搜索？
```

#### 本周验收标准

- [ ]  能调用云端和本地 Embedding API 将文本转为向量
- [ ]  理解余弦相似度并能手写计算
- [ ]  完成 Embedding 模型选型对比实验
- [ ]  实现了纯内存的语义搜索 Demo
- [ ]  记录了 Embedding 搜索的局限性案例

---

### 第 6 周：文档解析与分块策略

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_掌握 PDF、Markdown、HTML、Word 等常见文档格式的文本提取
- 02_理解为什么要分块（Chunking）：大模型有上下文限制，长文档必须切片
- 03_掌握多种分块策略及其适用场景
- 04_理解 Overlap（重叠）的作用：防止关键信息被切断
- 05_能根据文档类型选择最优的分块方案

#### 主讲内容

##### 1. 文档格式解析

**要做什么：** 学习从各种格式的文件中提取纯文本。

**技术点：**

- 01_PDF 解析：PyPDF2（简单）、pdfplumber（表格友好）、PyMuPDF（速度快）
- 02_Markdown 解析：保留结构信息（标题层级）
- 03_HTML 解析：BeautifulSoup 提取正文，去除导航/广告
- 04_Word (.docx) 解析：python-docx 库
- 05_OCR 场景：扫描件 PDF 需要 OCR（了解即可，如 Tesseract）

**练习任务：**

```
任务1：用 PyMuPDF 解析一个 PDF，提取全部文本并保留页码信息
任务2：解析一个 Markdown 文件，按标题层级拆分为段落
任务3：解析一个网页 HTML，只提取正文内容
任务4：对比不同 PDF 库在同一文件上的提取质量
```

##### 2. 分块策略详解

**要做什么：** 学习将长文档切成适合 Embedding 和检索的小块。

**技术点：**

- 06_为什么要分块：Embedding 模型有输入限制（通常 512-8192 Token）
- 07_固定大小分块：按字符数/Token 数切割
- 08_按分隔符分块：按段落（\n\n）、按句子（。！？）切割
- 09_递归分块：先按大分隔符切，太长再按小分隔符切
- 10_语义分块：用 Embedding 检测语义断点（进阶）

**练习任务：**

```
任务1：实现固定大小分块（chunk_size=500字符），观察切割效果
任务2：实现按段落分块，观察段落长短不一的问题
任务3：实现递归分块：先按 \n\n 切，超过 500 字的再按 。切
任务4：对比三种策略在同一文档上的分块数量和质量
```

##### 3. Overlap（重叠）策略

**要做什么：** 理解为什么相邻块之间需要重叠一部分内容。

**技术点：**

- 11_Overlap 的作用：防止一句话被切成两半，导致两个块都不完整
- 12_Overlap 大小的选择：通常为 chunk_size 的 10%-20%
- 13_Overlap 过大的问题：冗余增加、存储浪费、检索时重复
- 14_Overlap 过小的问题：信息断裂、检索质量下降
- 15_实现带 Overlap 的分块函数

**练习任务：**

```
任务1：实现 chunk_text(text, chunk_size=500, overlap=100) 函数
任务2：用 overlap=0 和 overlap=100 分别分块，找出信息被切断的案例
任务3：验证 overlap 确实解决了信息切断问题
任务4：实验不同 overlap 比例（10%、20%、30%），找到最佳平衡点
```

##### 4. 元数据保留

**要做什么：** 分块时保留每个块的来源信息（文件名、页码、章节标题），检索时能告诉用户"答案来自哪里"。

**技术点：**

- 16_每个 chunk 附带 metadata：source_file、page_number、section_title
- 17_按文档结构分块：利用标题层级作为分块边界
- 18_chunk_id 的生成策略
- 19_metadata 在后续检索中的过滤作用
- 20_数据结构设计：{"text": "...", "metadata": {...}, "embedding": [...]}

**练习任务：**

```
任务1：修改分块函数，为每个 chunk 添加 metadata（来源文件、块序号）
任务2：解析一个有标题结构的文档，按标题分块并记录章节信息
任务3：设计 Chunk 的 Pydantic 模型（结合第3周知识）
任务4：实现一个 document_processor(file_path) 函数，输入文件路径，输出 List[Chunk]
```

##### 5. 分块质量评估

**要做什么：** 如何判断分块效果好不好？建立评估意识。

**技术点：**

- 21_好的分块标准：语义完整、长度适中、信息不丢失
- 22_人工抽检：随机抽 10 个块，看是否能独立理解
- 23_检索测试：用已知问题搜索，看能否命中正确的块
- 24_块大小的影响：太小信息不全，太大噪音太多
- 25_不同文档类型的最佳分块策略总结

**练习任务：**

```
任务1：准备 5 个测试问题，验证分块后能否通过语义搜索找到正确答案
任务2：对比 chunk_size=200 vs 500 vs 1000 的检索效果
任务3：总结一份"分块策略速查表"：什么文档用什么策略
任务4：处理一个真实的技术文档（如 Python 官方文档的某一章），完成完整的解析+分块流程
```

#### 本周验收标准

- [ ]  能解析 PDF、Markdown、HTML 三种格式的文档
- [ ]  实现了至少 3 种分块策略并能对比优劣
- [ ]  理解 Overlap 的作用并实现了带重叠的分块
- [ ]  每个 chunk 都带有完整的 metadata
- [ ]  产出分块策略速查表

---

### 第 7 周：向量数据库集成

**课时：5天 | 技术点：20项 | 学习方式：动手实操**

#### 学习目标

- 01_理解为什么需要向量数据库（内存存储不持久、不可扩展）
- 02_掌握 ChromaDB 的安装、存储、检索全流程
- 03_理解向量索引的基本原理（ANN 近似最近邻）
- 04_掌握 metadata 过滤检索
- 05_能将第 6 周的分块结果存入向量数据库并检索

#### 主讲内容

##### 1. 向量数据库选型

**技术点：**

- 01_为什么不能用 Python list 存向量：数据量大时暴力搜索太慢、不持久化
- 02_主流向量数据库对比：ChromaDB（轻量本地）、Milvus（生产级）、Qdrant（Rust 高性能）、Pinecone（云托管）
- 03_选型建议：学习阶段用 ChromaDB，生产环境用 Milvus/Qdrant
- 04_ANN（近似最近邻）索引原理：HNSW、IVF 的基本概念
- 05_向量数据库 vs 传统数据库的区别

##### 2. ChromaDB 实战

**技术点：**

- 06_ChromaDB 安装与初始化
- 07_Collection 的创建与管理
- 08_文档的添加：documents + embeddings + metadatas + ids
- 09_查询：query_texts / query_embeddings + n_results
- 10_metadata 过滤：where 条件（如只搜某个文件的内容）

**练习任务：**

```
任务1：安装 ChromaDB，创建一个 collection
任务2：把第 6 周处理好的 chunks 全部存入 ChromaDB
任务3：实现语义搜索：输入问题，返回最相关的 5 个 chunk
任务4：实现 metadata 过滤：只搜索某个特定文件的内容
任务5：测试持久化：关闭程序后重新打开，验证数据还在
```

##### 3. 检索质量优化

**技术点：**

- 11_n_results 的选择：返回太多噪音大，太少可能漏掉答案
- 12_相似度分数阈值过滤
- 13_去重：相邻的重叠块可能都被召回，需要去重
- 14_多 collection 管理：不同类型的文档存不同 collection
- 15_索引重建：文档更新后如何增量更新向量库

**练习任务：**

```
任务1：对比 n_results=3 vs 5 vs 10 的检索质量
任务2：实现相似度阈值过滤（分数低于 0.7 的不返回）
任务3：实现增量更新：新增一个文档时，只处理新文档的 chunks
任务4：设计一个 VectorStore 类，封装所有向量数据库操作
```

#### 本周验收标准

- [ ]  ChromaDB 环境搭建完成，能正常存取数据
- [ ]  第 6 周的所有 chunks 已存入向量数据库
- [ ]  实现了带 metadata 过滤的语义搜索
- [ ]  封装了 VectorStore 类，接口清晰
- [ ]  理解 ANN 索引的基本原理

---

### 第 8 周：组装 Naive RAG 并直面缺陷

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_将前几周的所有组件串联，搭建完整的 RAG 系统
- 02_理解 RAG 的完整流程：Query → Retrieve → Augment → Generate
- 03_体验 Naive RAG 的实际效果和明显缺陷
- 04_记录所有失败案例，为后续优化做准备
- 05_建立"RAG 不是银弹"的认知

#### 主讲内容

##### 1. RAG 完整流程组装

**要做什么：** 把文档解析、分块、Embedding、向量存储、检索、Prompt 拼接、大模型生成全部串起来。

**技术点：**

- 01_完整流程：用户提问 → 问题转向量 → 查向量库 → 召回 Top-K 块 → 拼接到 Prompt → 大模型回答
- 02_RAG Prompt 模板设计："根据以下参考资料回答问题，如果资料中没有答案请说不知道"
- 03_上下文拼接策略：多个 chunk 如何组织（编号、分隔符）
- 04_来源引用：在回答中标注"答案来自第X页"
- 05_完整的 rag_query(question) 函数实现

**练习任务：**

```
任务1：实现完整的 rag_query(question) 函数
任务2：准备 10 个测试问题，记录 RAG 的回答质量（1-5分打分）
任务3：实现来源引用：回答末尾附上参考来源
任务4：对比有 RAG vs 无 RAG（直接问大模型）的回答质量
```

##### 2. Naive RAG 的典型缺陷

**要做什么：** 通过大量测试，发现 Naive RAG 的各种问题。

**技术点：**

- 06_检索失败：用户问法与文档表述不一致，搜不到正确内容
- 07_噪音干扰：召回的内容不相关，误导大模型
- 08_信息分散：答案分布在多个 chunk 中，单个 chunk 不完整
- 09_幻觉问题：大模型无视参考资料，自己编造答案
- 10_多跳问题：需要综合多个文档才能回答的问题

**练习任务：**

```
任务1：找出 3 个"搜不到正确答案"的案例，分析原因
任务2：找出 3 个"搜到了但大模型回答错误"的案例
任务3：测试一个需要综合多个文档的问题，观察 RAG 的表现
任务4：整理一份"Naive RAG 失败案例集"，每个案例记录：问题、召回内容、错误回答、原因分析
```

##### 3. 简单优化尝试

**技术点：**

- 11_Prompt 优化：更严格地要求模型"只根据资料回答"
- 12_Top-K 调整：增加或减少召回数量
- 13_chunk_size 调整：更大的块包含更多上下文
- 14_问题改写：手动改写用户问题再搜索
- 15_预告：这些手动优化将在第 10 周被系统化的 Advanced RAG 技术替代

**练习任务：**

```
任务1：优化 RAG Prompt，加入更严格的约束，对比效果
任务2：调整 Top-K 从 3 到 10，观察对回答质量的影响
任务3：手动改写一个搜索失败的问题，验证改写后能否搜到
任务4：写一份"第一版 RAG 系统评估报告"：成功率、失败模式、优化方向
```

#### 本周验收标准

- [ ]  完整的 RAG 系统跑通（从文档到回答的全流程）
- [ ]  在 10+ 个测试问题上评估了系统表现
- [ ]  整理了 Naive RAG 的失败案例集（至少 10 个）
- [ ]  尝试了基本优化并记录效果
- [ ]  产出第一版 RAG 系统评估报告

---

## 阶段三：框架、进阶 RAG、多模态与 MCP（第 9-12 周）

> 目标：你已经知道了底层的痛点，现在引入框架提效，并掌握 2026 年最核心的工具协议。

---

### 第 9 周：LangChain 核心抽象与 LCEL

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_理解 LangChain 的设计哲学：为什么需要这个框架（对应你前 8 周的痛点）
- 02_掌握 LangChain 的核心抽象：Models、Prompts、Output Parsers、Retrievers
- 03_掌握 LCEL（LangChain Expression Language）管道语法
- 04_能用 LangChain 快速重构你前 8 周手写的代码
- 05_理解框架的边界：什么时候该用框架，什么时候该手写

#### 主讲内容

##### 1. LangChain 架构总览

**技术点：**

- 01_LangChain 的模块划分：langchain-core、langchain-community、langchain-openai 等
- 02_核心接口：BaseChatModel、BaseRetriever、BaseOutputParser
- 03_Runnable 协议：所有组件都实现 invoke/stream/batch 接口
- 04_LCEL 管道语法：用 | 符号串联组件（prompt | model | parser）
- 05_与你手写代码的对应关系

**练习任务：**

```
任务1：安装 langchain 全家桶，跑通官方 quickstart
任务2：用 LCEL 实现：prompt_template | chat_model | str_output_parser
任务3：对比你第 2 周手写的对话代码 vs LangChain 版本的代码量
任务4：用 LangChain 的 ChatModel 接口同时对接 OpenAI 和 Ollama，验证接口统一性
```

##### 2. Prompt Templates 与 Output Parsers

**技术点：**

- 06_ChatPromptTemplate：系统化管理 Prompt 模板
- 07_MessagesPlaceholder：动态插入对话历史
- 08_PydanticOutputParser：结合 Pydantic 模型解析输出（对应你第 3 周的知识）
- 09_JsonOutputParser：直接解析 JSON 输出
- 10_StrOutputParser：最简单的字符串输出

**练习任务：**

```
任务1：用 ChatPromptTemplate 重写你第 2 周的 Prompt 模板
任务2：用 PydanticOutputParser 重写你第 3 周的结构化输出逻辑
任务3：实现一个带对话历史的 Chain（用 MessagesPlaceholder）
任务4：对比手写版 vs LangChain 版的代码可维护性
```

##### 3. Retrievers 与 RAG Chain

**技术点：**

- 11_VectorStoreRetriever：将你第 7 周的 ChromaDB 包装为 LangChain Retriever
- 12_create_retrieval_chain：一行代码搭建 RAG
- 13_create_stuff_documents_chain：文档拼接策略
- 14_自定义 Retriever：继承 BaseRetriever 实现自己的检索逻辑
- 15_RunnablePassthrough：在 LCEL 中传递原始输入

**练习任务：**

```
任务1：用 LangChain 重构你第 8 周的 RAG 系统（应该只需要 20 行代码）
任务2：对比手写 RAG vs LangChain RAG 的代码量和可读性
任务3：自定义一个 Retriever，在检索前先打印日志
任务4：用 LCEL 实现完整的 RAG Chain：input → retriever → prompt → model → parser
```

##### 4. Memory 与对话链

**技术点：**

- 16_ConversationBufferMemory：存储完整对话历史
- 17_ConversationSummaryMemory：自动摘要压缩（对应你第 2 周的手写逻辑）
- 18_ConversationBufferWindowMemory：滑动窗口
- 19_在 LCEL 中集成 Memory
- 20_Memory 的持久化（存到 Redis/文件）

**练习任务：**

```
任务1：用 ConversationBufferMemory 实现多轮对话
任务2：用 ConversationSummaryMemory 实现自动压缩
任务3：对比你第 2 周手写的上下文管理 vs LangChain Memory 的效果
任务4：实现 Memory 持久化到本地文件
```

##### 5. 框架的边界认知

**技术点：**

- 21_什么时候该用 LangChain：快速原型、标准流程、团队协作
- 22_什么时候不该用：极致性能要求、非标准流程、框架 bug 难调试
- 23_LangChain 的常见坑：版本更新快、文档滞后、抽象泄漏
- 24_替代方案：LlamaIndex（RAG 专精）、Haystack、纯手写
- 25_最佳实践：核心逻辑用框架，边缘逻辑手写

**练习任务：**

```
任务1：找一个 LangChain 文档中的示例，尝试运行，记录遇到的版本兼容问题
任务2：用纯手写和 LangChain 分别实现同一个功能，对比调试难度
任务3：阅读 LangChain 某个组件的源码（如 StrOutputParser），理解它做了什么
任务4：总结一份"LangChain 使用决策表"：什么场景用什么方案
```

#### 本周验收标准

- [ ]  掌握 LCEL 管道语法，能流畅地串联组件
- [ ]  用 LangChain 重构了前 8 周的 RAG 系统
- [ ]  理解 LangChain 各核心抽象与你手写代码的对应关系
- [ ]  产出 LangChain 使用决策表
- [ ]  能在 LangChain 和手写之间做出合理选择

---

### 第 10 周：Advanced RAG（进阶检索策略）

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_掌握 Query Rewrite（查询重写）：让搜索更精准
- 02_掌握 Hybrid Search（混合检索）：语义 + 关键词双管齐下
- 03_掌握 Reranking（重排序）：用专门模型对结果二次排序
- 04_掌握 Multi-Query（多查询）：一个问题生成多个搜索角度
- 05_系统性解决第 8 周发现的 Naive RAG 缺陷

#### 主讲内容

##### 1. Query Rewrite（查询重写）

**要做什么：** 用户的原始问题往往不适合直接搜索。用大模型先改写问题，再去检索。

**技术点：**

- 01_为什么需要重写：用户说"它怎么用"，搜索引擎不知道"它"是什么
- 02_HyDE（Hypothetical Document Embeddings）：让模型先生成一个"假答案"，用假答案去搜索
- 03_Step-back Prompting：把具体问题抽象化再搜索
- 04_Multi-Query：一个问题生成 3-5 个不同角度的搜索查询
- 05_Query Decomposition：复杂问题拆解为多个子问题

**练习任务：**

```
任务1：实现 HyDE：用户问 "LangChain 怎么用"，先让模型生成一段假答案，再用假答案搜索
任务2：实现 Multi-Query：一个问题生成 3 个不同表述，分别搜索后合并结果
任务3：用第 8 周的失败案例测试，对比重写前后的检索质量
任务4：实现 Query Decomposition：把 "对比 A 和 B 的优缺点" 拆成两个子查询
```

##### 2. Hybrid Search（混合检索）

**要做什么：** 结合向量语义搜索和 BM25 关键词搜索，取长补短。

**技术点：**

- 06_BM25 算法原理：基于词频的经典搜索算法
- 07_语义搜索的优势：理解同义词、模糊表达
- 08_关键词搜索的优势：精确匹配错误码、专有名词
- 09_混合策略：两种搜索结果的融合（RRF - Reciprocal Rank Fusion）
- 10_权重调节：语义 vs 关键词的比例

**练习任务：**

```
任务1：安装 rank_bm25 库，实现 BM25 关键词搜索
任务2：对同一个问题，分别用语义搜索和 BM25 搜索，对比结果
任务3：实现 RRF 融合：合并两种搜索的结果并重新排序
任务4：用第 5 周发现的"关键词搜索失败案例"验证混合检索的效果
```

##### 3. Reranking（重排序）

**要做什么：** 初次检索召回 20 条结果，用专门的 Reranker 模型重新打分，只保留最相关的 5 条。

**技术点：**

- 11_为什么需要 Reranking：Embedding 的相似度是粗排，Reranker 是精排
- 12_Cross-Encoder vs Bi-Encoder 的区别
- 13_开源 Reranker 模型：BGE-Reranker、Jina-Reranker
- 14_Reranker 的调用方式：输入 (query, document) 对，输出相关性分数
- 15_Reranking 的性能开销：比 Embedding 慢很多，所以只对 Top-20 重排

**练习任务：**

```
任务1：下载 BGE-Reranker 模型（或调用 API）
任务2：对第 8 周 RAG 的检索结果进行 Reranking，对比排序变化
任务3：测量 Reranking 的延迟开销
任务4：实现完整流程：检索 Top-20 → Rerank → 取 Top-5 → 生成回答
```

##### 4. 完整 Advanced RAG Pipeline

**技术点：**

- 16_完整流程：Query Rewrite → Hybrid Search → Rerank → Generate
- 17_用 LangChain LCEL 串联所有步骤
- 18_A/B 测试：Naive RAG vs Advanced RAG 的效果对比
- 19_延迟 vs 质量的权衡
- 20_缓存策略：相同问题的结果缓存

**练习任务：**

```
任务1：用 LCEL 实现完整的 Advanced RAG Pipeline
任务2：用第 8 周的 10 个测试问题重新评估，对比分数提升
任务3：测量完整 Pipeline 的端到端延迟
任务4：实现简单缓存：相同问题直接返回缓存结果
```

#### 本周验收标准

- [ ]  实现了 Query Rewrite、Hybrid Search、Reranking 三大优化
- [ ]  Advanced RAG 在测试集上的表现明显优于 Naive RAG
- [ ]  有量化的 A/B 测试数据
- [ ]  理解每种优化的适用场景和性能开销

---

### 第 11 周：多模态（Multimodal）入门

**课时：5天 | 技术点：20项 | 学习方式：动手实操**

#### 学习目标

- 01_掌握 Vision API：让大模型"看图说话"
- 02_掌握 Whisper 语音转文字
- 03_理解多模态在实际产品中的应用场景
- 04_能将图片和音频集成到你的 RAG/Agent 系统中
- 05_了解 TTS（文字转语音）的基本使用

#### 主讲内容

##### 1. Vision API（图片理解）

**技术点：**

- 01_Vision API 的调用方式：在 messages 中传入 image_url 或 base64 图片
- 02_图片分析能力：OCR 文字识别、图表理解、场景描述
- 03_多图输入：同时传入多张图片进行对比分析
- 04_图片 Token 消耗计算（图片也占 Token）
- 05_实际应用：发票识别、UI 截图分析、文档图片 OCR

**练习任务：**

```
任务1：传一张包含文字的图片，让模型提取其中的文字内容
任务2：传一张数据图表，让模型分析趋势并生成文字报告
任务3：传两张 UI 截图，让模型对比差异
任务4：实现一个"图片问答"功能：用户上传图片 + 提问，模型回答
```

##### 2. Whisper 语音转文字

**技术点：**

- 06_Whisper 模型介绍：OpenAI 开源的语音识别模型
- 07_本地部署 Whisper（faster-whisper 库）
- 08_API 调用方式（OpenAI Whisper API）
- 09_支持的音频格式与预处理
- 10_中文语音识别的效果与优化

**练习任务：**

```
任务1：用 Whisper API 将一段中文录音转为文字
任务2：本地部署 faster-whisper，对比速度和准确率
任务3：实现一个"语音问答"：录音 → 转文字 → 送入 RAG → 返回答案
任务4：测试不同音频质量（清晰/嘈杂）对识别准确率的影响
```

##### 3. TTS（文字转语音）与多模态整合

**技术点：**

- 11_TTS API 调用（OpenAI TTS、Edge-TTS 免费方案）
- 12_音色选择与语速控制
- 13_多模态 RAG：图片文档的处理（先 OCR 再入库）
- 14_语音交互闭环：语音输入 → 文字 → AI 处理 → 语音输出
- 15_多模态应用场景总结

**练习任务：**

```
任务1：用 TTS API 将一段文字转为语音文件
任务2：实现语音交互闭环：录音 → Whisper → LLM → TTS → 播放
任务3：处理一个包含图片的 PDF，用 Vision API 提取图片中的信息加入 RAG
任务4：总结多模态技术的应用场景清单
```

#### 本周验收标准

- [ ]  能调用 Vision API 分析图片内容
- [ ]  能用 Whisper 将语音转为文字
- [ ]  实现了至少一个多模态应用 Demo
- [ ]  理解多模态技术在实际产品中的价值

---

### 第 12 周：Agent 基础与 MCP 协议

**课时：5天 | 技术点：30项 | 学习方式：动手实操**

#### 学习目标

- 01_深入理解 ReAct（Reasoning + Acting）Agent 模式
- 02_用 LangChain 构建带工具的 Agent
- 03_掌握 MCP（Model Context Protocol）协议规范
- 04_能编写一个标准的 MCP Server
- 05_让 Agent 通过 MCP 协议调用外部工具

#### 主讲内容

##### 1. ReAct Agent 模式

**技术点：**

- 01_ReAct 论文核心思想：Thought → Action → Observation → 循环
- 02_与你第 4 周手写的 Agent 循环的对应关系
- 03_LangChain 的 create_react_agent 实现
- 04_Agent 的工具选择策略：模型如何决定用哪个工具
- 05_Agent 的终止条件：什么时候停止循环给出最终答案

**练习任务：**

```
任务1：用 LangChain create_react_agent 创建一个带 3 个工具的 Agent
任务2：观察 Agent 的思考过程（打印中间步骤）
任务3：对比 LangChain Agent vs 你第 4 周手写 Agent 的代码量和功能
任务4：测试 Agent 在复杂任务上的多步推理能力
```

##### 2. 自定义工具开发

**技术点：**

- 06_LangChain @tool 装饰器：最简单的工具定义方式
- 07_StructuredTool：带 Pydantic 参数校验的工具
- 08_工具的 description 对 Agent 行为的影响
- 09_异步工具：async def 定义的工具
- 10_工具错误处理：handle_tool_error 参数

**练习任务：**

```
任务1：用 @tool 装饰器定义 5 个实用工具（搜索、计算、时间、翻译、数据库查询）
任务2：用 StructuredTool 定义一个带复杂参数的工具
任务3：测试工具 description 的质量对 Agent 选择准确率的影响
任务4：实现工具错误处理：工具报错时 Agent 能自动重试或换工具
```

##### 3. MCP（Model Context Protocol）协议

**要做什么：** 学习 2025-2026 年最重要的 AI 工具标准协议。MCP 让任何 AI 应用都能通过统一接口调用外部工具，就像 USB 接口统一了外设连接。

**要达到的效果：** 能编写 MCP Server，让任何支持 MCP 的客户端（Claude、Kiro、Cursor 等）都能调用你的工具。

**技术点：**

- 11_MCP 协议概述：Client-Server 架构、JSON-RPC 通信
- 12_MCP 的三大能力：Tools（工具）、Resources（资源）、Prompts（提示词模板）
- 13_MCP Server 的生命周期：initialize → 提供能力列表 → 处理调用 → shutdown
- 14_Python MCP SDK 的使用（mcp 库）
- 15_Transport 层：stdio（本地进程）、SSE（HTTP 远程）

**练习任务：**

```
任务1：安装 mcp Python SDK，阅读官方 quickstart
任务2：理解 MCP 的 JSON-RPC 消息格式（request/response/notification）
任务3：列出你日常工作中可以封装为 MCP 工具的 5 个场景
任务4：画出 MCP Client-Server 的通信时序图
```

##### 4. 编写 MCP Server

**技术点：**

- 16_用 Python mcp SDK 创建 Server
- 17_定义 Tool：名称、描述、参数 Schema、处理函数
- 18_定义 Resource：暴露数据源（如数据库内容）
- 19_错误处理与日志
- 20_测试 MCP Server：用 mcp CLI 工具或 Claude Desktop 连接测试

**练习任务：**

```
任务1：写一个 MCP Server，提供 "查询数据库" 工具（连接 SQLite）
任务2：添加第二个工具 "搜索文档"（调用你的 RAG 系统）
任务3：用 MCP Inspector 工具测试你的 Server
任务4：将 MCP Server 配置到 Claude Desktop 或 Kiro 中，验证端到端调用
```

##### 5. Agent + MCP 整合

**技术点：**

- 21_让 LangChain Agent 通过 MCP 调用外部工具
- 22_MCP vs 直接 Function Calling 的区别与优势
- 23_多个 MCP Server 的组合使用
- 24_MCP 的安全考虑：权限控制、输入校验
- 25_MCP 生态：已有的开源 MCP Server（GitHub、Slack、数据库等）

**练习任务：**

```
任务1：让你的 Agent 通过 MCP 协议调用你写的数据库查询工具
任务2：组合使用多个 MCP Server（你的 + 开源的 GitHub MCP Server）
任务3：实现权限控制：某些工具需要确认才能执行
任务4：总结 MCP 的优势：为什么比硬编码 Function Calling 更好
```

#### 本周验收标准

- [ ]  能用 LangChain 构建带多工具的 ReAct Agent
- [ ]  理解 MCP 协议规范并能画出通信流程
- [ ]  独立编写了一个 MCP Server（至少 2 个工具）
- [ ]  MCP Server 能被外部客户端成功调用
- [ ]  理解 MCP 在 AI 工具生态中的定位

---

## 阶段四：编排、可观测性与 Harness（第 13-16 周）

> 目标：让复杂 Agent 稳定运行，具备工业级的调试、评估与容错能力。

---

### 第 13 周：LangGraph 状态机编排

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_理解为什么 while 循环做 Agent 不够用（无法暂停、无法分支、无法回溯）
- 02_掌握 LangGraph 的核心概念：State、Node、Edge、Conditional Edge
- 03_能用 LangGraph 构建多节点的复杂 Agent 工作流
- 04_掌握 Human-in-the-Loop（人工介入）模式
- 05_理解 Checkpoint（检查点）与状态持久化

#### 主讲内容

##### 1. 从 while 循环到状态图

**技术点：**

- 01_while 循环 Agent 的局限：无法暂停等待人工确认、无法并行执行、无法回退
- 02_状态机（State Machine）的基本概念
- 03_LangGraph 的设计理念：Agent 是一个图（Graph），不是一个链（Chain）
- 04_State：用 TypedDict 定义 Agent 的全局状态
- 05_Node：图中的每个节点是一个处理函数

**练习任务：**

```
任务1：安装 langgraph，跑通官方 quickstart
任务2：定义一个 AgentState（messages, current_step, tool_results）
任务3：画出你第 4 周 Agent 的流程图，标注哪些地方需要分支/暂停
任务4：用 LangGraph 重写第 4 周的 Agent，对比代码结构
```

##### 2. 条件边与分支逻辑

**技术点：**

- 06_Edge：节点之间的连接
- 07_Conditional Edge：根据状态决定下一步走哪个节点
- 08_END 节点：图的终止条件
- 09_路由函数：检查状态，返回下一个节点名
- 10_多分支场景：根据用户意图走不同的处理流程

**练习任务：**

```
任务1：实现条件路由：如果模型返回 tool_calls 走"执行工具"节点，否则走"输出结果"节点
任务2：实现多分支：根据用户意图分流到"查询"、"创建"、"删除"三个不同节点
任务3：实现循环：工具执行后回到"模型思考"节点，直到模型决定结束
任务4：可视化你的图结构（LangGraph 支持导出为 Mermaid 图）
```

##### 3. Human-in-the-Loop（人工介入）

**技术点：**

- 11_interrupt_before / interrupt_after：在指定节点前/后暂停等待人工确认
- 12_应用场景：执行危险操作前（如删除数据）需要人工确认
- 13_状态持久化：暂停后状态不丢失，人工确认后继续执行
- 14_Checkpoint：LangGraph 的状态快照机制
- 15_MemorySaver vs SqliteSaver：不同的持久化后端

**练习任务：**

```
任务1：实现一个 Agent，在执行"发送邮件"工具前暂停等待用户确认
任务2：用 MemorySaver 实现状态持久化，验证暂停后能恢复
任务3：实现"拒绝"逻辑：用户拒绝后 Agent 换一种方案
任务4：实现多步确认：复杂任务的每一步都需要人工确认
```

##### 4. 子图与模块化

**技术点：**

- 16_SubGraph：将复杂图拆分为多个子图
- 17_子图的输入输出接口定义
- 18_子图复用：同一个子图在不同场景中使用
- 19_并行节点：多个节点同时执行
- 20_错误处理节点：专门处理异常的节点

**练习任务：**

```
任务1：将 RAG 检索逻辑封装为一个子图
任务2：将工具执行逻辑封装为另一个子图
任务3：在主图中组合使用两个子图
任务4：实现并行节点：同时查询多个数据源
```

##### 5. 实战：构建一个多步骤 Agent

**技术点：**

- 21_需求：构建一个"研究助手"Agent（搜索 → 分析 → 总结 → 输出报告）
- 22_状态设计：research_topic, search_results, analysis, final_report
- 23_节点设计：search_node, analyze_node, summarize_node, output_node
- 24_错误恢复：某个节点失败时的重试逻辑
- 25_完整的图可视化与测试

**练习任务：**

```
任务1：设计"研究助手"的状态和节点
任务2：实现完整的图并跑通
任务3：加入错误处理：搜索失败时重试 3 次
任务4：加入 Human-in-the-Loop：分析结果需要用户确认后才生成报告
```

#### 本周验收标准

- [ ]  掌握 LangGraph 的 State、Node、Edge、Conditional Edge
- [ ]  实现了带条件分支和循环的 Agent 图
- [ ]  实现了 Human-in-the-Loop 模式
- [ ]  构建了一个多节点的"研究助手"Agent
- [ ]  能可视化图结构并解释每个节点的作用

---

### 第 14 周：可观测性（Observability）— Agent 调试命脉

**课时：5天 | 技术点：20项 | 学习方式：动手实操**

#### 学习目标

- 01_理解为什么 Agent 比普通程序更难调试（非确定性、多步骤、黑盒模型）
- 02_掌握 LangSmith / LangFuse 的接入与使用
- 03_能通过 Trace 树图定位 Agent 的问题节点
- 04_掌握 Prompt 版本管理与 A/B 测试
- 05_建立"没有可观测性就不要上线"的工程意识

#### 主讲内容

##### 1. 为什么 Agent 需要可观测性

**技术点：**

- 01_Agent 调试的三大难题：非确定性输出、多步骤链路、模型是黑盒
- 02_传统 print/log 的局限：看不到完整的调用链路
- 03_Trace（链路追踪）的概念：记录每一步的输入、输出、延迟、Token 消耗
- 04_可观测性工具对比：LangSmith（官方）、LangFuse（开源）、Phoenix（本地）
- 05_选型建议：学习用 LangSmith，生产用 LangFuse（可私有部署）

**练习任务：**

```
任务1：注册 LangSmith 账号，获取 API Key
任务2：在你的 LangGraph Agent 中接入 LangSmith（只需设置环境变量）
任务3：运行 Agent，在 LangSmith 网页上查看 Trace
任务4：找到一次"Agent 回答错误"的 Trace，分析是哪一步出了问题
```

##### 2. Trace 分析与问题定位

**技术点：**

- 06_Trace 树结构：父 Span → 子 Span 的层级关系
- 07_每个 Span 的关键信息：输入、输出、延迟、Token 数、模型名
- 08_定位检索问题：Retriever Span 的输入（query）和输出（documents）
- 09_定位生成问题：LLM Span 的完整 Prompt 和 Response
- 10_定位工具问题：Tool Span 的参数和返回值

**练习任务：**

```
任务1：故意让 Agent 犯错（给一个它无法回答的问题），通过 Trace 定位失败原因
任务2：分析一次 RAG 回答错误的 Trace：是检索错了还是生成错了？
任务3：找出延迟最高的 Span，分析性能瓶颈
任务4：对比同一问题在不同 Prompt 版本下的 Trace 差异
```

##### 3. 成本监控与优化

**技术点：**

- 11_Token 消耗的自动统计（按 run、按用户、按时间段）
- 12_成本异常告警：某次调用消耗异常高时报警
- 13_成本优化策略：缓存、摘要压缩、小模型路由
- 14_延迟监控：P50、P95、P99 延迟指标
- 15_错误率监控：工具调用失败率、模型拒绝率

**练习任务：**

```
任务1：统计你的 Agent 在 20 次调用中的总 Token 消耗和费用
任务2：找出消耗最高的那次调用，分析原因（是不是上下文太长？）
任务3：实现缓存：相同问题的第二次调用直接返回缓存结果，对比成本
任务4：设置一个"单次调用不超过 5000 Token"的告警阈值
```

##### 4. Prompt 版本管理与实验

**技术点：**

- 16_在 LangSmith 中管理 Prompt 版本
- 17_A/B 测试：同一问题用不同 Prompt 版本，对比效果
- 18_Prompt 回滚：新版本效果差时快速回退
- 19_数据集（Dataset）：建立标准测试集
- 20_自动化评估：对测试集批量运行并打分

**练习任务：**

```
任务1：在 LangSmith 中创建一个 Prompt，发布 v1 版本
任务2：修改 Prompt 发布 v2，对比两个版本在 10 个问题上的表现
任务3：创建一个包含 20 个问题+标准答案的 Dataset
任务4：对 Dataset 批量运行 Agent，统计正确率
```

#### 本周验收标准

- [ ]  LangSmith/LangFuse 接入完成，能看到完整 Trace
- [ ]  能通过 Trace 定位 Agent 的问题节点
- [ ]  实现了成本监控和异常告警
- [ ]  建立了标准测试 Dataset
- [ ]  理解"没有可观测性就不要上线"的原则

---

### 第 15 周：Harness 工程 — 异常捕获与自纠错

**课时：5天 | 技术点：20项 | 学习方式：动手实操**

#### 学习目标

- 01_理解 Harness（线束）的概念：给 Agent 套上安全网
- 02_实现自纠错循环：工具报错时 Agent 自动修正重试
- 03_实现输入/输出 Guardrails（护栏）：过滤有害内容
- 04_实现超时与熔断机制
- 05_构建一个生产级的 Agent 容错体系

#### 主讲内容

##### 1. Harness 的概念与设计

**技术点：**

- 01_Harness = Agent 的外围工程代码（不是 AI 逻辑，是工程逻辑）
- 02_Harness 的职责：错误恢复、安全限制、资源控制、质量保证
- 03_Harness vs Agent 的关系：Agent 负责"聪明"，Harness 负责"稳定"
- 04_在 LangGraph 中实现 Harness：专门的错误处理节点
- 05_Harness 的设计原则：不改变 Agent 逻辑，只在外围兜底

**练习任务：**

```
任务1：列出你的 Agent 可能出现的所有错误类型（工具失败、模型幻觉、超时、格式错误）
任务2：为每种错误设计对应的 Harness 策略
任务3：在 LangGraph 中添加一个 "error_handler" 节点
任务4：画出加入 Harness 后的完整图结构
```

##### 2. 自纠错循环（Self-Correction）

**技术点：**

- 06_自纠错的原理：把错误信息反馈给模型，让它修正
- 07_SQL 生成场景：生成的 SQL 执行报错 → 把报错信息给模型 → 重新生成
- 08_代码生成场景：生成的代码运行报错 → 反馈错误 → 修正
- 09_最大重试次数：防止无限循环
- 10_重试策略：指数退避、换模型、降级

**练习任务：**

```
任务1：实现 SQL 自纠错：Agent 生成 SQL → 执行 → 报错 → 反馈 → 重新生成 → 再执行
任务2：设置最大重试 3 次，超过后返回友好错误信息
任务3：记录每次重试的 Trace，分析模型的修正能力
任务4：统计自纠错的成功率（重试后能修正的比例）
```

##### 3. Guardrails（护栏）

**技术点：**

- 11_输入护栏：过滤用户的恶意输入（注入攻击、有害内容）
- 12_输出护栏：检查模型输出是否符合业务规则
- 13_Prompt 注入检测：识别用户试图"越狱"的输入
- 14_PII（个人隐私信息）检测与脱敏
- 15_业务规则校验：输出不能包含竞品信息、不能给出医疗建议等

**练习任务：**

```
任务1：实现输入护栏：检测并拒绝包含 "ignore previous instructions" 的输入
任务2：实现输出护栏：检查模型回答中是否包含"我不确定"等低置信度表达
任务3：实现 PII 检测：如果模型输出中包含手机号/身份证号，自动脱敏
任务4：将护栏集成到 LangGraph 中作为独立节点
```

##### 4. 超时与熔断

**技术点：**

- 16_单步超时：某个节点执行超过 N 秒则中断
- 17_总超时：整个 Agent 执行超过 M 秒则终止
- 18_熔断器模式：连续失败 N 次后暂停服务
- 19_降级策略：Agent 不可用时返回预设回答
- 20_资源限制：单次调用的最大 Token 预算

**练习任务：**

```
任务1：实现单步超时：工具调用超过 10 秒则跳过
任务2：实现总超时：Agent 运行超过 60 秒则强制返回当前最佳结果
任务3：实现熔断器：连续 3 次工具调用失败后，跳过该工具
任务4：实现降级：当大模型 API 不可用时，返回"系统繁忙请稍后"
```

#### 本周验收标准

- [ ]  实现了自纠错循环并有成功率数据
- [ ]  实现了输入/输出护栏
- [ ]  实现了超时和熔断机制
- [ ]  Agent 在各种异常情况下都能优雅降级而非崩溃
- [ ]  Harness 代码与 Agent 逻辑清晰分离

---

### 第 16 周：自动化评估（Evaluation）

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_理解为什么不能用肉眼判断 AI 系统的好坏
- 02_掌握 RAG 评估指标：Faithfulness、Relevancy、Recall
- 03_掌握 Agent 评估指标：任务完成率、步骤效率、工具选择准确率
- 04_能用 Ragas/DeepEval 框架自动化评估
- 05_建立"每次改动都要跑评估"的 CI 意识

#### 主讲内容

##### 1. 评估的必要性

**技术点：**

- 01_为什么肉眼评估不可靠：样本量小、主观偏差、无法回归测试
- 02_AI 系统的评估难点：输出非确定性、没有唯一正确答案
- 03_评估的三个层次：组件级（检索）、系统级（端到端）、用户级（满意度）
- 04_评估数据集的构建：问题 + 标准答案 + 参考上下文
- 05_LLM-as-Judge：用大模型当裁判评分

**练习任务：**

```
任务1：构建一个包含 30 个问题的评估数据集（问题、标准答案、来源文档）
任务2：手动评估你的 RAG 系统在这 30 个问题上的表现（打 1-5 分）
任务3：思考：你的评分标准是什么？能否让另一个人用同样标准打出相似的分？
任务4：这就是为什么需要自动化评估——消除主观性
```

##### 2. RAG 评估指标

**技术点：**

- 06_Faithfulness（忠实度）：回答是否基于检索到的内容，而非编造
- 07_Answer Relevancy（答案相关性）：回答是否切题
- 08_Context Precision（上下文精确度）：检索到的内容是否相关
- 09_Context Recall（上下文召回率）：需要的信息是否都被检索到了
- 10_Hallucination（幻觉率）：回答中有多少内容是编造的

**练习任务：**

```
任务1：安装 ragas 库，跑通官方示例
任务2：用 ragas 评估你的 RAG 系统，获取各项指标分数
任务3：分析 Faithfulness 低的案例：模型在哪里编造了信息？
任务4：分析 Context Recall 低的案例：是检索没搜到还是分块有问题？
```

##### 3. Agent 评估

**技术点：**

- 11_任务完成率：Agent 是否成功完成了用户的请求
- 12_步骤效率：完成任务用了多少步（越少越好）
- 13_工具选择准确率：Agent 是否选对了工具
- 14_最终答案质量：即使过程对了，答案质量如何
- 15_安全性评估：Agent 是否执行了不该执行的操作

**练习任务：**

```
任务1：设计 10 个 Agent 测试任务（简单到复杂）
任务2：运行 Agent 并记录：是否完成、用了几步、选对工具没
任务3：计算任务完成率和平均步骤数
任务4：找出 Agent 失败的案例，分析是哪个环节出了问题
```

##### 4. 评估驱动的迭代优化

**技术点：**

- 16_基线建立：第一版系统的各项指标作为基线
- 17_A/B 测试：修改后的系统 vs 基线的对比
- 18_回归测试：确保优化 A 不会破坏 B
- 19_评估自动化：集成到 CI/CD 流程中
- 20_评估报告：每次迭代产出对比报告

**练习任务：**

```
任务1：记录当前系统的基线分数
任务2：做一个优化（如加入 Reranking），重新评估，对比提升
任务3：写一个 eval.py 脚本，一键运行所有评估并生成报告
任务4：模拟 CI 流程：每次代码修改后自动运行 eval.py
```

##### 5. 自定义评估指标

**技术点：**

- 21_业务特定指标：如"回答中是否包含价格信息"
- 22_用 LLM 定义自定义评估标准
- 23_多维度综合评分
- 24_评估结果的可视化
- 25_持续监控：上线后的实时评估

**练习任务：**

```
任务1：定义一个业务特定的评估指标（如"回答是否包含操作步骤"）
任务2：用 LLM-as-Judge 实现这个自定义指标的自动评分
任务3：将所有指标整合为一个综合分数
任务4：产出一份完整的"系统评估报告"
```

#### 本周验收标准

- [ ]  构建了包含 30+ 问题的评估数据集
- [ ]  用 Ragas 完成了 RAG 系统的自动化评估
- [ ]  有基线分数和优化后的对比数据
- [ ]  实现了一键评估脚本 eval.py
- [ ]  产出完整的系统评估报告

---

## 阶段五：全栈整合与业务交付（第 17-20 周）

> 目标：发挥 JS + Python 全栈优势，完成商业级 AI 应用作品集。

---

### 第 17 周：FastAPI 构建 AI 后端服务

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_掌握 FastAPI 框架的核心用法
- 02_能将 LangGraph Agent 封装为 REST API
- 03_实现 SSE 流式响应接口
- 04_实现 WebSocket 实时通信
- 05_掌握 API 的认证、限流、错误处理

#### 主讲内容

##### 1. FastAPI 基础

**技术点：**

- 01_FastAPI 的安装与项目结构
- 02_路由定义：GET、POST、PUT、DELETE
- 03_请求体校验：Pydantic 模型作为请求参数（你第 3 周的知识直接复用）
- 04_响应模型：定义 API 的返回格式
- 05_依赖注入：数据库连接、认证等公共逻辑

**练习任务：**

```
任务1：创建 FastAPI 项目，实现一个 POST /chat 接口（接收消息，返回 AI 回复）
任务2：用 Pydantic 定义请求体和响应体
任务3：实现错误处理：模型调用失败时返回友好错误信息
任务4：用 Swagger UI（FastAPI 自带）测试所有接口
```

##### 2. 流式响应（SSE）

**技术点：**

- 06_StreamingResponse：FastAPI 的流式响应
- 07_SSE 格式：`data: {json}\n\n` 的标准格式
- 08_将 LangGraph 的流式输出转为 SSE 事件
- 09_前端如何消费 SSE（EventSource API）
- 10_流式响应的错误处理与超时

**练习任务：**

```
任务1：实现 POST /chat/stream 接口，返回 SSE 流式响应
任务2：用 curl 测试流式接口，观察逐字输出
任务3：实现流式传输中的错误处理（模型中途报错）
任务4：实现"中间步骤"的流式传输（Agent 的思考过程也实时推送）
```

##### 3. WebSocket 实时通信

**技术点：**

- 11_WebSocket vs SSE 的区别与选择
- 12_FastAPI WebSocket 端点
- 13_双向通信：用户可以中途发送"停止"指令
- 14_连接管理：多用户并发连接
- 15_心跳机制：保持连接活跃

**练习任务：**

```
任务1：实现 WebSocket /ws/chat 端点
任务2：实现用户发送"stop"时中断 Agent 执行
任务3：实现多用户并发（每个用户独立的对话状态）
任务4：对比 SSE 和 WebSocket 在不同场景下的适用性
```

##### 4. 生产级 API 工程

**技术点：**

- 16_API Key 认证：Header 中传递 API Key
- 17_限流（Rate Limiting）：防止滥用
- 18_CORS 配置：允许前端跨域访问
- 19_日志与监控：请求日志、响应时间、错误率
- 20_API 版本管理：/v1/chat、/v2/chat

**练习任务：**

```
任务1：实现 API Key 认证中间件
任务2：实现简单限流：每个 Key 每分钟最多 10 次请求
任务3：配置 CORS 允许前端域名访问
任务4：实现请求日志：记录每次请求的耗时、Token 消耗、用户 ID
```

##### 5. Agent 服务化

**技术点：**

- 21_将 LangGraph Agent 封装为 FastAPI 服务
- 22_会话管理：每个用户维护独立的对话状态
- 23_异步处理：长时间运行的 Agent 任务放入后台
- 24_健康检查接口：/health
- 25_优雅关闭：处理完当前请求再停止服务

**练习任务：**

```
任务1：将你第 13 周的 LangGraph Agent 完整封装为 API 服务
任务2：实现会话管理：用 session_id 区分不同用户的对话
任务3：实现 /health 健康检查接口
任务4：用 Docker 打包你的 API 服务
```

#### 本周验收标准

- [ ]  FastAPI 服务运行正常，支持 REST + SSE + WebSocket
- [ ]  LangGraph Agent 完整封装为 API
- [ ]  实现了认证、限流、CORS、日志
- [ ]  服务可以用 Docker 打包部署
- [ ]  API 文档（Swagger）完整可用

---

### 第 18 周：前端 UX 与状态管理

**课时：5天 | 技术点：25项 | 学习方式：动手实操**

#### 学习目标

- 01_用 React/Next.js 构建 AI 聊天界面
- 02_实现流式渲染（打字机效果）
- 03_实现对话状态管理（多轮、分支、重试）
- 04_实现用户中断（Stop Generating）
- 05_实现 Markdown 渲染与代码高亮

#### 主讲内容

##### 1. 聊天界面基础

**技术点：**

- 01_Next.js 项目搭建（App Router）
- 02_聊天 UI 组件：消息列表、输入框、发送按钮
- 03_消息数据结构：{role, content, timestamp, status}
- 04_自动滚动到底部
- 05_响应式布局（PC + 移动端）

**练习任务：**

```
任务1：用 Next.js 创建项目，搭建基本聊天 UI
任务2：实现消息列表的渲染（区分用户消息和 AI 消息的样式）
任务3：实现输入框 + 发送按钮 + Enter 快捷键
任务4：实现自动滚动到最新消息
```

##### 2. 流式渲染

**技术点：**

- 06_fetch + ReadableStream 消费 SSE
- 07_逐字渲染：每收到一个 chunk 就追加到当前消息
- 08_打字机光标效果
- 09_流式过程中的 Loading 状态管理
- 10_流式错误处理：连接中断时的 UI 反馈

**练习任务：**

```
任务1：用 fetch 连接后端 SSE 接口，实现逐字渲染
任务2：添加打字机光标动画
任务3：实现 Loading 状态：发送后显示"AI 正在思考..."
任务4：实现错误处理：网络断开时显示重试按钮
```

##### 3. 交互控制

**技术点：**

- 11_Stop Generating：用户点击停止按钮中断生成
- 12_AbortController：前端取消 fetch 请求
- 13_Regenerate：重新生成上一条回答
- 14_Edit & Resend：编辑之前的消息重新发送
- 15_对话分支：从某条消息开始分叉

**练习任务：**

```
任务1：实现 Stop 按钮，点击后中断流式接收
任务2：实现 Regenerate 按钮，重新生成最后一条 AI 回复
任务3：实现消息编辑：点击用户消息可以修改并重新发送
任务4：实现对话历史的本地存储（localStorage）
```

##### 4. 富文本渲染

**技术点：**

- 16_Markdown 渲染：react-markdown 库
- 17_代码块高亮：highlight.js 或 Prism
- 18_代码块复制按钮
- 19_表格、列表、链接的正确渲染
- 20_LaTeX 数学公式渲染（如果需要）

**练习任务：**

```
任务1：集成 react-markdown，渲染 AI 回复中的 Markdown
任务2：实现代码块语法高亮 + 复制按钮
任务3：测试各种 Markdown 元素的渲染效果
任务4：实现流式 Markdown 渲染（边接收边渲染，不闪烁）
```

##### 5. 多模态交互

**技术点：**

- 21_文件上传：拖拽或点击上传文档/图片
- 22_图片预览：上传的图片在对话中显示
- 23_语音输入：浏览器 Web Speech API 或录音上传
- 24_来源引用：AI 回答中的引用可以点击查看原文
- 25_反馈机制：👍👎 按钮收集用户反馈

**练习任务：**

```
任务1：实现文件上传功能（支持 PDF、图片）
任务2：上传图片后调用 Vision API，在对话中显示分析结果
任务3：实现 👍👎 反馈按钮，将反馈发送到后端记录
任务4：实现来源引用：点击 [1] 可以展开查看原文片段
```

#### 本周验收标准

- [ ]  完整的聊天 UI，支持流式渲染
- [ ]  实现了 Stop、Regenerate、Edit 等交互控制
- [ ]  Markdown + 代码高亮渲染正常
- [ ]  支持文件/图片上传
- [ ]  前后端联调通过，完整对话流程跑通

---

### 第 19 周：系统联调与商业级打磨

**课时：5天 | 技术点：20项 | 学习方式：项目实战**

#### 学习目标

- 01_将前 18 周的所有组件整合为一个完整产品
- 02_进行端到端测试与性能优化
- 03_实现生产级的部署方案
- 04_编写用户文档和技术文档
- 05_准备作品展示

#### 主讲内容

##### 1. 系统整合

**技术点：**

- 01_前后端联调：解决跨域、认证、数据格式等问题
- 02_环境配置管理：开发/测试/生产环境的配置分离
- 03_数据库选择：对话历史存 PostgreSQL、向量存 ChromaDB/Milvus
- 04_文件存储：上传的文档存储方案
- 05_完整的系统架构图

**练习任务：**

```
任务1：画出完整的系统架构图（前端、后端、向量库、LLM API、MCP Server）
任务2：解决所有联调问题，确保端到端流程顺畅
任务3：实现环境配置分离（.env.development、.env.production）
任务4：编写 docker-compose.yml 一键启动所有服务
```

##### 2. 性能优化

**技术点：**

- 06_首字延迟优化：减少 TTFT（Time To First Token）
- 07_并发处理：多用户同时使用时的性能
- 08_缓存策略：常见问题的答案缓存
- 09_向量库索引优化：大数据量下的检索速度
- 10_前端性能：虚拟列表、懒加载

**练习任务：**

```
任务1：用 locust 或 ab 做压力测试，找出性能瓶颈
任务2：实现 Redis 缓存层，缓存热门问题的答案
任务3：优化前端：消息列表超过 100 条时使用虚拟滚动
任务4：记录优化前后的性能指标对比
```

##### 3. 部署方案

**技术点：**

- 11_Docker 容器化：前端、后端、数据库分别打包
- 12_docker-compose：本地一键部署
- 13_云部署选项：Vercel（前端）+ Railway/Fly.io（后端）
- 14_域名与 HTTPS 配置
- 15_CI/CD：代码推送后自动部署

**练习任务：**

```
任务1：编写 Dockerfile（前端和后端各一个）
任务2：编写 docker-compose.yml 整合所有服务
任务3：部署到云平台，获得一个公网可访问的 URL
任务4：配置 GitHub Actions 实现自动部署
```

##### 4. 文档与展示准备

**技术点：**

- 16_README.md：项目介绍、技术栈、快速启动
- 17_API 文档：接口说明（FastAPI 自动生成）
- 18_架构文档：系统设计决策与权衡
- 19_Demo 视频：录制 2-3 分钟的产品演示
- 20_GitHub 仓库整理：清理代码、添加 .gitignore、LICENSE

**练习任务：**

```
任务1：编写完整的 README.md（项目介绍、截图、技术栈、部署方式）
任务2：编写架构文档：为什么选择这些技术、做了哪些权衡
任务3：录制 Demo 视频展示核心功能
任务4：整理 GitHub 仓库，确保代码整洁、文档完整
```

#### 本周验收标准

- [ ]  系统完整部署并可公网访问
- [ ]  通过压力测试，性能满足基本要求
- [ ]  Docker 一键部署方案可用
- [ ]  README 和架构文档完整
- [ ]  Demo 视频录制完成

---

### 第 20 周：简历更新与面试准备

**课时：5天 | 技术点：15项 | 学习方式：总结输出**

#### 学习目标

- 01_将 20 周的学习成果转化为简历亮点
- 02_准备 AI Engineer 岗位的常见面试题
- 03_能清晰地讲述项目的技术决策与权衡
- 04_建立持续学习的习惯和信息源
- 05_明确下一步的进阶方向

#### 主讲内容

##### 1. 简历重塑

**技术点：**

- 01_从"JS/Python 开发"转变为"AI 应用工程师"的定位
- 02_项目描述的 STAR 法则：Situation、Task、Action、Result
- 03_量化成果：RAG 准确率提升 X%、响应延迟降低 Y%
- 04_技术关键词：LangChain、LangGraph、RAG、Agent、MCP、Vector DB
- 05_GitHub 项目链接 + Demo 链接

**练习任务：**

```
任务1：重写简历的技术栈部分，突出 AI 相关技能
任务2：用 STAR 法则描述你的 RAG 项目和 Agent 项目
任务3：整理所有可量化的成果数据
任务4：请朋友/同事 Review 你的简历
```

##### 2. 面试准备

**技术点：**

- 06_RAG 相关：分块策略、检索优化、评估指标
- 07_Agent 相关：ReAct 原理、LangGraph 状态机、工具调用
- 08_工程相关：可观测性、评估体系、成本控制
- 09_系统设计：如何设计一个企业级 RAG 系统
- 10_编码题：手写 Function Calling 流程、手写 RAG Pipeline

**练习任务：**

```
任务1：准备 20 个 AI Engineer 常见面试题的答案
任务2：练习白板画系统架构图（RAG 系统、Agent 系统）
任务3：准备 3 个"项目中遇到的难题及解决方案"的故事
任务4：模拟面试：让朋友问你技术问题，练习口头表达
```

##### 3. 持续学习路线

**技术点：**

- 11_信息源：AI 领域的优质博客、Newsletter、GitHub 仓库
- 12_进阶方向一：模型微调（LoRA、QLoRA）
- 13_进阶方向二：多 Agent 系统（CrewAI、AutoGen）
- 14_进阶方向三：AI Infra（模型部署、推理优化、vLLM）
- 15_社区参与：开源贡献、技术博客、分享

**练习任务：**

```
任务1：订阅 5 个 AI 领域的优质信息源
任务2：选择一个进阶方向，制定下一个 4 周的学习计划
任务3：写一篇技术博客，分享你 20 周的学习心得
任务4：在 GitHub 上给一个 AI 开源项目提一个 PR（哪怕只是修文档）
```

#### 本周验收标准

- [ ]  简历更新完成，突出 AI Engineer 定位
- [ ]  准备了 20+ 面试题答案
- [ ]  能流畅地讲述项目的技术决策
- [ ]  确定了下一步的进阶方向
- [ ]  产出一篇学习总结博客

---

## 附录

### 推荐资源


| 类别 | 资源                          | 说明                                      |
| ---- | ----------------------------- | ----------------------------------------- |
| 文档 | LangChain 官方文档            | https://python.langchain.com              |
| 文档 | LangGraph 官方文档            | https://langchain-ai.github.io/langgraph/ |
| 文档 | MCP 协议规范                  | https://modelcontextprotocol.io           |
| 课程 | DeepLearning.AI Short Courses | 免费短课，质量极高                        |
| 社区 | LangChain Discord             | 问题讨论和最新动态                        |
| 工具 | Ollama                        | https://ollama.ai 本地模型                |
| 工具 | LangSmith                     | https://smith.langchain.com 可观测性      |
| 评估 | Ragas                         | https://docs.ragas.io RAG 评估            |

### 每周时间分配建议


| 活动     | 时间占比 | 说明               |
| -------- | -------- | ------------------ |
| 动手编码 | 60%      | 写代码、跑实验     |
| 阅读文档 | 20%      | 官方文档、源码     |
| 总结输出 | 10%      | 笔记、博客、速查表 |
| 社区交流 | 10%      | 提问、回答、讨论   |

### 硬件要求


| 配置 | 最低要求                  | 推荐配置         |
| ---- | ------------------------- | ---------------- |
| RAM  | 16GB                      | 32GB             |
| 存储 | 50GB 可用空间             | 100GB SSD        |
| GPU  | 无（用 CPU 跑 Ollama 7B） | NVIDIA 8GB+ 显存 |
| 网络 | 能访问 API                | 稳定的国际网络   |

### 费用预估


| 项目       | 费用         | 说明                   |
| ---------- | ------------ | ---------------------- |
| 大模型 API | ¥100-300/月 | DeepSeek 很便宜，够用  |
| 云部署     | ¥0-50/月    | 免费额度通常够学习用   |
| 工具订阅   | ¥0          | LangSmith 免费额度够用 |
| 总计       | ¥100-350/月 | 比报班便宜 100 倍      |

---

> 最后一句话：**这份大纲的价值不在于"看完"，而在于"做完"。每一周都有明确的验收标准，做到了就往下走，做不到就多花几天。节奏是你自己的，但标准不能降。**
