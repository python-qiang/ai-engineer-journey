# Week 2 学习笔记

## 目录

- [1. Messages 三角色与 Prompt Engineering 的关系](#1-messages-三角色与-prompt-engineering-的关系)
- [2. Messages 数组实验结论](#2-messages-数组实验结论)
- [3. Python 可变对象引用陷阱](#3-python-可变对象引用陷阱)
- [4. API 内容安全过滤导致流式中断](#4-api-内容安全过滤导致流式中断)
- [5. 03a 滑动窗口实战总结](#5-03a-滑动窗口实战总结)
- [6. 上下文管理策略选型 — 贴合产品定位](#6-上下文管理策略选型--贴合产品定位)
- [7. API 协议演进与开发者策略](#7-api-协议演进与开发者策略)
- [8. 03b 摘要压缩 — 统一架构设计历程](#8-03b-摘要压缩--统一架构设计历程)
- [9. 千问 Token 计算详解](#9-千问-token-计算详解)
- [10. Pin vs Memory vs Remember — 上下文记忆三件套](#10-pin-vs-memory-vs-remember--上下文记忆三件套)
- [11. 04a Zero-shot vs Few-shot 实验 — few-shot 不是万能药](#11-04a-zero-shot-vs-few-shot-实验--few-shot-不是万能药)
- [12. 04b Reasoning Control 实验 — thinking 的真实代价](#12-04b-reasoning-control-实验--thinking-的真实代价)
- [13. 2026 年 Prompt Engineering 还剩什么用？—— 认知升华](#13-2026-年-prompt-engineering-还剩什么用--认知升华)

---

## 1. Messages 三角色与 Prompt Engineering 的关系

### 1.1 三个 Role 的定位

| Role | 定位 | 适合放什么 |
|------|------|-----------|
| system | 全局指令, 模型的"出厂设置" | 角色定义, 规则约束, 输出格式要求 |
| user | 用户输入 | 真实问题, 待处理的数据 |
| assistant | 模型的"历史回复" | few-shot 示例, 风格示范, 接续上文 |

### 1.2 Few-shot 放 system vs 放 assistant 的区别

- 模型把 assistant 消息当作"自己说过的话", 会强烈倾向于保持一致性
- system 里的示例只是"指令描述", 模型可能理解但不一定严格遵循格式
- **assistant 示例 = 肌肉记忆, system 描述 = 口头叮嘱**

### 1.3 Prompt Engineering 的完整视角

```
system (定规则) + user/assistant 对话历史 (教格式/风格) + user (问问题)
       ↓                    ↓                              ↓
    "你是谁"          "你之前是这样回答的"              "现在回答这个"
```

三者配合才是完整的 prompt 设计。实际工程中经常混用——简单约束放 system, 复杂格式用 few-shot assistant 示范, 两者不冲突。

---

## 2. Messages 数组实验结论

### 2.1 实验 A: Few-shot 效果

| 方式 | 输出 |
|------|------|
| 无 few-shot (直接问"什么是闭包") | 自由格式, 较长 |
| 有 few-shot (2组 user+assistant 示例) | 严格遵循"概念/一句话/例子"格式 |

**结论:** assistant 示例比 system 里写"用固定格式"更有效。模型把 assistant 消息当作"自己说过的话", 会强烈保持一致性。

### 2.2 实验 B: 风格引导

通过一条 assistant 示范(东北话/古文), 模型会延续该风格回答后续问题。比单纯在 system 里写"用XX风格回答"效果更强。

### 2.3 实验 B2: 接续回答

把模型上一轮的(不完整)回复放在 assistant 消息中, 然后 user 发"继续", 模型会接着上次的内容继续生成。这就是多轮对话的本质。

### 2.4 实验 C: Messages 顺序 (核心发现)

System prompt: "你只能用英文回答, 绝对不能用中文"

| 顺序 | 云端 qwen3.7-plus | 本地 qwen2.5:1.5b |
|------|-------------------|---------------------|
| 标准 [system, user] | ✅ 英文 | ✅ 英文 |
| 反转 [user, system] | ✅ 英文 | ✅ 英文 |
| 夹中间 [user1, system, user2] | ✅ 英文 | ❌ 用了中文 |

**结论:** 弱模型在非标准 messages 顺序下会忽略 system 约束。强模型不受影响。

### 2.5 工程实践总结

```
messages 构造规则:
1. system 永远放最前面 (弱模型兼容性)
2. few-shot 用 user+assistant 对话对, 比纯文字描述更有效
3. 风格引导: system 描述 + assistant 示范 = 最强组合
4. 接续上文: 把上一轮回复放 assistant, user 发"继续"
5. 不要假设模型能处理非标准的 messages 结构
```

---

## 3. Python 可变对象引用陷阱

### 3.1 问题

```python
def get_messages(self):
    return self.messages  # 返回的是引用, 不是副本!

result = self.get_messages()
result.append(new_item)  # 同时修改了 self.messages!
```

Python 的 list/dict 赋值和函数返回都是**引用传递**(浅拷贝都不是), 不会自动创建副本.

### 3.2 修复

```python
def get_messages(self):
    return list(self.messages)  # 返回浅拷贝, 互不影响
```

### 3.3 教训

- 如果函数返回一个 list 且调用方会修改它, **必须返回 copy**
- `list(original)` 或 `original[:]` 或 `original.copy()` 都能创建浅拷贝
- 在我们的 Session 中: `_apply_strategy()` 返回的 messages_to_send 和 self.messages 必须是独立对象

---

## 4. API 内容安全过滤导致流式中断

### 4.1 现象

- 模型回复到一半突然停止
- usage 为 None (没有返回 token 统计)
- finish_reason 为 None (不是正常的 "stop" 或 "length")
- 重复问同一个问题, 每次都在相同位置中断

### 4.2 原因

阿里百炼 API 有内置的内容安全策略. 当模型生成的内容触发违禁词(如脏话, 敏感政治内容等)时, 流式传输被强制中断, 不会发送 usage chunk 和正常的 finish_reason.

### 4.3 如何识别

- 不是 "length" 截断(那样有 warning 且 usage 正常返回)
- 不是网络超时(那样会抛 httpx.HTTPError)
- 特征: 有 content 但 usage=None 且 finish_reason=None

### 4.4 应对

- 这不是代码 bug, 是 API 平台行为
- 换个表述方式重新提问, 避免引导模型输出敏感内容
- 如果业务需要, 可以在 system prompt 中限制模型不使用粗口/敏感词

---

## 5. 03a 滑动窗口实战总结

### 5.1 验证结果

| 指标 | 表现 | 说明 |
|------|------|------|
| Sent messages | 稳定 17 条 | 不随轮数增长, 窗口生效 |
| Input tokens | 5000-7000 徘徊 | 不再线性增长, 成本可控 |
| Pinned 内容 | 始终保留 | pin 的"大话数据结构"话题一直被模型记住 |
| 非 pinned 早期内容 | 被遗忘 | 第3轮说的"我叫小明"在第19轮已被忘记 |

17 条的组成: system(1) + omit_notice(1) + pinned(4) + recent_5_rounds(10) + current_user(1)

### 5.2 踩坑记录

1. **user 消息丢失 bug**: 先 append user 再 apply_strategy(), 导致未配对的 user 不在发送列表中.
   修复: 先 apply_strategy() 构造副本, 再 append user 到副本, 成功后才存入 self.messages.

2. **可变对象引用污染**: _apply_strategy() 返回 self.messages 引用(不是 copy),
   chat() 对返回值 append 时直接修改了 self.messages.
   修复: 所有返回 self.messages 的地方改为 list(self.messages).

3. **内容安全过滤导致中断**: 模型生成违禁词(如 fuck)时被强制截断,
   usage=None, finish_reason=None, 不是代码 bug.

### 5.3 关键设计决策

- self.messages 始终保存完整历史, 发送给 API 的是独立副本
- strategy 在 chat() 调用前执行, 当前 user 消息追加到副本末尾
- pinned 用 pinned_rounds set 防重复, 不按内容比较
- Session class 封装所有状态, CLI 文件只负责 match-case 路由

### 5.4 心得

这只是一个最基础的上下文管理方案. 离生产级还有很多差距:
- 没有 token 精确计算(靠 window_size 粗控)
- 没有摘要压缩(丢弃的历史彻底丢失)
- 没有动态 system prompt(关键信息只能靠 pin 手动保留)
- pinned 内容没有优先级, 无法自动识别什么该保留

这些正是 03b(摘要压缩) 和 03c(动态 prompt + token 预算) 要解决的.
一步步来, 先把地基打牢.

---

## 6. 上下文管理策略选型 — 贴合产品定位

### 6.1 主流产品的策略对比

| 产品 | 策略 | 用户感知 | 适合场景 |
|------|------|----------|----------|
| Gemini | 不压缩, 靠超大窗口(1-2M), 满了提醒开新 session | 透明 | 简单对话, 大窗口兜底 |
| ChatGPT | 满了推荐新 session, 自动 summary 带入新对话 | 半透明 | 消费级通用对话 |
| 豆包 | 后台静默 compact + 全局 memory 持久化, 用户永远看到同一个 session | 完全无感知 | 企业级/长期陪伴型 |
| Kiro/Cursor | 自动 compact + 手动 /compact, 过程有提示 | 半透明 | 开发者工具 |

### 6.2 不同策略的设计哲学

- **不压缩(Gemini)**: 用硬件(超大 context)解决软件问题. 简单但贵.
- **提醒用户新开 session(ChatGPT)**: 把决策权交给用户, 产品逻辑简单.
- **后台静默管理(豆包)**: 最复杂但体验最好. 需要 summary + 全局 memory + 持久化.
- **透明可见的自动管理(Kiro)**: 适合开发者 — 我们既要自动化, 也要能看到发生了什么.

### 6.3 我们的 CLI 产品定位与策略选择

定位: AI 学习助手的实验性 CLI 工具, 面向单个开发者, 用于理解底层原理.

选择: Kiro/Cursor 模式(透明可见的自动管理)
- 自动压缩但打印过程(token 使用率, 压缩提示)
- 支持手动 /compact
- 不追求"无感知" — 看到压缩过程本身就是学习目的
- 策略可切换(sliding_window / summary) — 方便对比实验

### 6.4 核心认知

**没有"最好的"上下文管理策略, 只有"最适合当前产品定位"的策略.**
- 消费级产品追求无感知体验 -> 后台静默管理
- 开发者工具追求可观测性 -> 透明 + 手动控制
- 学习项目追求理解原理 -> 所有过程可见, 可对比

这就是为什么我们在 03a/03b/03c 中逐步实现多种策略, 而不是只选一种.


---

## 7. API 协议演进与开发者策略

### 7.1 Chat Completions vs Responses API

| 维度 | Chat Completions | Responses API |
|------|-----------------|---------------|
| 定位 | 为聊天而生的无状态协议 | 为 Agent 设计的有状态协议 |
| 状态管理 | 每次发完整 messages 数组 | 支持 previous_response_id 服务端记忆 |
| 工具调用 | 需自己实现 function calling 循环 | 内置 web_search/code_interpreter 等 |
| 输出格式 | 统一的 choices[].message | 类型化的 output 数组(message/reasoning/function_call) |
| 生态兼容性 | 所有 provider 都支持(事实标准) | OpenAI 主推, 阿里/DeepSeek 跟进, Anthropic 走自己的路 |

### 7.2 为什么各家 API 不统一

- OpenAI 先发定义了 Chat Completions, 成为事实标准
- 其他家"兼容但扩展": 阿里有 DashScope + OpenAI 兼容, Anthropic 有 Messages API
- 每家有自己的产品策略和差异化功能(如阿里的 enable_search, Anthropic 的 system 独立参数)

### 7.3 开发者应该关注什么

1. **理解协议本质**(Week 1-4): messages/streaming/function calling 的数据流, 不管 API 怎么变这些概念不变
2. **掌握一个框架**(Week 9): LangChain/LiteLLM 做适配层, 一行代码切换 provider
3. **不需要背各家差异**: 遇到时查文档
4. **不需要专门学 Responses API**: 框架会处理协议选择, 核心概念已通过 Chat Completions 掌握

### 7.4 原始 API / 官方 SDK / 框架的分工

```
你(业务代码) -> 框架(LangChain) -> 官方 SDK(openai/dashscope) -> 原始 HTTP API -> provider
```

| 层 | 谁用 | 价值 |
|----|------|------|
| 原始 HTTP API | 学习者 / 极致性能需求 | 理解底层, 零抽象开销 |
| 官方 SDK (pip package) | 框架开发者 / 单 provider 团队 | 类型安全, 封装了 HTTP 细节 |
| 框架 (LangChain) | 应用开发者 | 统一接口, 自由切换 provider, 解耦 |

### 7.5 我们的学习路径与协议的关系

- Week 1-4: 手写 HTTP 调 Chat Completions (理解本质, 体会"换 provider 要改一堆代码"的痛)
- Week 9: 引入 LangChain (理解框架的价值: 解耦, 不是偷懒)
- Week 12: Agent + MCP (如果内置工具有价值, 顺手了解 Responses API 即可)

---

## 8. 03b 摘要压缩 — 统一架构设计历程

### 8.1 核心设计决策的演变

| 问题 | 初始方案 | 最终方案 | 为什么改 |
|------|---------|---------|---------|
| messages 是否删除 | compact 时删除旧消息 | 永不删除, 保留完整历史 | 和 Kiro jsonl 一致, save 时数据完整 |
| 两种策略的 messages 行为 | 不同(sliding 不删, summary 删) | 统一不删 | 代码对称, 逻辑简单 |
| keep_recent + threshold | 两个变量, 含义重叠 | threshold(用户配置) + _KEEP_RECENT(内部常量) | 职责分离清晰 |
| 何时触发策略 | 每轮都截断 | 攒够 threshold 才触发 | 尽可能保留上下文, 回答才准确 |
| 两次触发之间发什么 | 只发 _KEEP_RECENT 轮 | 发水位线之上所有轮次 | 不浪费已有上下文 |
| rounds 计数 | _current_rounds (基于 messages 长度) | total_rounds (手动+1, 只增不减) | 和 pin 的轮次号绑定, 不受 compact 影响 |
| 避免重复压缩 | 无机制 | _waterline 水位线 | 记录已处理到哪一轮 |

### 8.2 waterline(水位线) 机制

水位线是整个架构的核心概念:
- `_waterline = N` 表示第 1~N 轮已经被处理过(omitted 或 summarized)
- `_count_pending_rounds()` = 水位线之上的非 pinned 轮数
- 触发条件: pending > threshold
- 触发后: 水位线推进, pending 回到 _KEEP_RECENT

两种策略共享同一套机制, 区别只是:
- sliding_window: 推进水位线(免费, 不调 API), 发送时用 omit notice
- summary: 调 compact()(调一次 API 生成摘要), 发送时用 checkpoint

### 8.3 渐进式结构化摘要 (参考 Codex + DSH + Kiro)

COMPACTION_PROMPT 设计要点:
- 5 个固定 section: 用户信息 / 关键事实与决定 / 已完成 / 待完成 / 当前状态
- 渐进式: 新 summary = 旧 summary 中仍正确的 + 新对话要点
- 精确保留: 姓名/数字/路径等不能被模糊化
- 字数控制: 300 字以内, 防止 summary 无限膨胀
- Preamble: 放回 context 时告诉模型"这是背景, 不要复述"

### 8.4 对比测试结果 (threshold=8, 20 轮对话)

| 信息 | 轮次 | Pinned? | Sliding Window | Summary |
|------|------|---------|:-:|:-:|
| 小明 | 2 | ✅ | ✅ 记住 | ✅ 记住 |
| Python 偏好 | 5 | ✅ | ✅ 记住 | ✅ 记住 |
| FastAPI | 8 | ❌ | ✅ (回复携带) | ✅ (在 summary 中) |
| Deadline 下周五 | 12 | ❌ | ❌ 忘了 | ✅ 记住 |
| DB Schema | 15 | ❌ | ❌ 忘了 | ❌ 模糊(被摘要简化) |

结论: Summary 策略信息保留明显优于 Sliding Window, 但有一次 API 调用的成本.

### 8.5 关键踩坑

1. **pinned_rounds 和 waterline 的交互**: pinned 在水位线之上才算"pending", 之下的不用再减
2. **sliding_window 不能每轮都切**: 要攒够 threshold, 两次触发之间逐轮累积上下文
3. **_get_rounds_above_waterline() 复用**: 同一段逻辑写了 3 次才发现要封装
4. **class 变量命名冲突**: `list` 方法名覆盖了 Python 内置 `list`, 导致类型注解报错
5. **变量命名语义**: keep_recent/threshold/KEEP_RECENT 三者职责要清晰分离

---

## 9. 千问 Token 计算详解

### 9.1 官方资料

- [阿里 Token 计算 API](https://help.aliyun.com/zh/open-search/search-platform/developer-reference/token-calculation#b36dcf4191t3y) — OpenSearch 平台的 tokenizer 端点(非 DashScope)
- [Qwen 官方 Tokenization 文档](https://qwen.readthedocs.io/en/latest/getting_started/concepts.html#tokens-tokenization)
- [Qwen GitHub tokenization_note_zh.md](https://github.com/QwenLM/Qwen/blob/main/tokenization_note_zh.md) — 详细的 BPE 原理和注意事项

### 9.2 Tokenizer 选择

千问全系列使用 Byte-level BPE on UTF-8, 基于 tiktoken. 第三方包 `qwen-tokenizer` (pipenv install) 提供精确本地 tokenizer.

两套 vocab (实测确认):
| Generation | Vocab Size | 对应 tokenizer | 我们的 model |
|---|---|---|---|
| Qwen1/2/2.5 | 151,851 | `qwen2.5-72b-instruct` | `qwen2.5:1.5b` |
| Qwen3/3.5/3.6+ | 248,077 | `qwen3.5-27b` | `qwen3.7-plus`, `qwen3:4b` |

同 generation 内所有 size 共用同一个 vocab, 映射按大版本号做即可.

### 9.3 Token 效率 (官方数据 + 实测)

官方: "1 token ≈ 3~4 chars for English, 1.5~1.8 chars for Chinese"

实测对比:
- "你好世界" = 2 tokens (qwen3, 248K vocab)
- "苹果" = 1 token (官方示例)
- "测试用例" = 3 tokens (官方示例)
- "OpenSearch" = 2 tokens (官方示例)

千问对中文优化远超 OpenAI 系列 (cl100k_base 同样文本要多 50%+ tokens).

### 9.4 Chat Template (ChatML 格式, 官方确认)

官方文档明确: Qwen 使用 ChatML 格式, 每轮对话结构为:
```
<|im_start|>{{role}}
{{content}}<|im_end|>
```

control tokens:
- `<|im_start|>` (bot token): 每轮开始
- `<|im_end|>` (eot token): 每轮结束
- `<|endoftext|>` (eod token): 文档/对话结束
- 无 bos/eos/unk/pad token

完整对话示例:
```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
hello<|im_end|>
<|im_start|>assistant
Hi there!<|im_end|>
```

### 9.5 Thinking 模式的影响

官方模板:
```
<|im_start|>assistant
<think>
{{thinking content}}
</think>

{{assistant content}}<|im_end|>
```

- `<think>` 和 `</think>` 是 special tokens (各 1 token)
- enable_thinking=False 时, API 可能注入 `</think>` 强制跳过思考
- 这解释了本地计算与 API 返回值的 ~4 token 差异

### 9.6 Context Length (官方数据)

| Model | 预训练序列长度 | 最大输出 (thinking) | 最大输出 (non-thinking) |
|---|---|---|---|
| Qwen3 | 32,768 (可扩展至 131,072) | 38,912 | 16,384 |
| Qwen3-2507 | 262,144 (可扩展至 1M) | 81,920 | 16,384 |

### 9.7 本地计算公式 (实测验证)

```python
total = sum(len(tok.encode(msg["content"])) + 5 for msg in messages) + 3 + 4
```

- +5/msg: `<|im_start|>`(1) + role(1) + `\n`(1) + `<|im_end|>`(1) + `\n`(1)
- +3: 末尾 assistant prompt `<|im_start|>assistant\n`
- +4: API 内部 overhead (thinking 相关, 固定值)

精度验证: 本地 37 vs API 41, 差 4 tokens (固定 offset, 不随消息数增长).

### 9.8 阿里官方 Token 计算途径

- DashScope API (我们用的): 无独立 tokenizer 端点, 只在响应 `usage` 字段返回精确值
- OpenSearch 平台: 有独立 `/tokenizer` API, 支持 ops-qwen-turbo/qwen-turbo/qwen-plus/qwen-max
- 本地: `qwen-tokenizer` 包 (基于 tiktoken, 加载官方 BPE 文件)

### 9.9 注意事项 (来自官方 tokenization_note)

- BPE 基于 UTF-8 字节序列, 不保证按 Unicode 字符边界切分
- 同一个词在不同上下文中可能被不同切分 (如 "Panda" vs " Panda")
- special tokens 在 input 中默认会被当作 special 解析, 需注意注入攻击
- 目前 `qwen-tokenizer` 默认 `allowed_special="all"`, 适合我们计算 token 的场景

---

## 10. Pin vs Memory vs Remember — 上下文记忆三件套

### 10.1 三者对比

| | /pin | /remember key value | "记住..." (自然语言) |
|--|------|---------------------|---------------------|
| 存什么 | 完整 user+assistant 消息对 | 一个 key-value 事实 | 模型自动提取的 key-value |
| 存在哪 | `pinned_messages` list | `self.memory` dict | `self.memory` dict |
| 怎么用 | 作为独立消息拼接到发送版本 | 注入到 system prompt 的 [Memory] block | 同左 |
| 体积 | 大 (整段对话原文) | 小 (一行) | 小 (一行) |
| 受 waterline 影响 | 不受 (独立拼接) | 不受 (在 system prompt 里) | 不受 |
| 触发 | 手动 /pin | 手动 /remember | 半自动: 用户说"记住", 提取自动 |
| 例子 | pin 一整轮架构讨论 | /remember lang Python | "记住，截止日期是下周五" |

### 10.2 remember 的两种输入方式

两条路最终都是往 `self.memory` 写 key-value:

- `/remember key value`: 用户手动拆好, 直接写入, 无 API 调用
- "记住...": 检测到关键词 → 静默调一次 API 提取 JSON → 合并到 memory

提取 prompt 示例:
```
从以下用户消息中提取需要长期记住的关键事实, 用 JSON 格式返回 {"key": "value"}, 无则返回 {}

用户消息: 记住，我的截止日期是下周五，用 PostgreSQL 数据库
```

模型返回: `{"deadline": "下周五", "db": "PostgreSQL"}`

### 10.3 发送版本的完整拼接顺序

```
messages[0]: system prompt (base + [Memory] block)    ← memory (永远可见)
messages[1]: omit notice / checkpoint                  ← 策略消息 (水位线 > 0 时)
messages[2..]: pinned messages                         ← pin (完整保留)
messages[..]: waterline 之上的普通消息                   ← 正常对话
messages[-1]: user 新消息                              ← 当前输入 (chat() 中追加)
```

### 10.4 使用场景选择

- 信息是一个**事实** (姓名/偏好/配置) → /remember 或 "记住"
- 信息是一段**完整对话** (设计讨论/需求确认) → /pin
- 两者可以叠加: pin 保留完整讨论, remember 提取其中的关键结论

---

## 11. 04a Zero-shot vs Few-shot 实验 — few-shot 不是万能药

### 11.1 实验设置

- 任务: 电商客服意图分类, 6 个标签(退换货/物流查询/商品咨询/投诉/催单/其他)
- 故意选业务专属 + 有歧义的标签, 让模型无法 zero-shot 靠常识猜准
- 模型: qwen3.7-flash, enable_thinking=False
- 测试集 12 条(含多条边界案例: 跨两个意图的模糊消息)
- 示例池与测试集严格分开(避免 answer leakage 答案泄漏)

### 11.2 五种配置结果

| 配置 | accuracy | invalid_rate |
|------|---------|-------------|
| V1 zero-shot | 66.7% | 0 |
| V2 随机示例×3 | 66.7% | 0 |
| V3 高质量示例×3 | **58.3%** ↓ | 0 |
| V4 高质量全量(含边界) | 66.7% | 0 |
| V5 打乱顺序 | 66.7% | 0 |

### 11.3 关键发现(和教科书预期相反, 但更真实)

1. **2026 模型 zero-shot 基线已经很强**: 66.7% 起步, few-shot 边际收益很小甚至为负。
   "few-shot 一定比 zero-shot 好"在现代模型 + 简单任务上不成立。

2. **few-shot 是双刃剑(可以理解为: 示例改变了模型的决策边界 decision boundary)**:
   示例不是单调增益, 而是改变模型对"输入模式与标签之间关系"的判断, 因此可能移动
   某些样本的分类边界——既可能提供有用的 task-specific evidence(任务专属证据),
   也可能引入错误归纳/过拟合某些模式。
   (注: "移动决策边界"是对实验现象的一个有用解释, 本实验并未观测模型内部状态。)
   V3(3个高质量示例)反而比 zero-shot 更差, 多错的那条"要退货并投诉"被示例
   影响判成了投诉。所以示例的**质量和边界覆盖比数量更重要**。

3. **示例顺序影响可忽略**: V4 vs V5 结果完全一样。
   现代模型对示例顺序不敏感(早期小模型有 recency bias, 最后一个示例权重高)。

4. **few-shot 只能教"示范过的模式"**: 有三条"顽固错误"所有配置全错——
   因为示例里没有针对性地教这些边界(如"问发货进度=催单"、"抱怨没明确诉求=投诉")。
   没覆盖到的边界, few-shot 救不了。

5. **深层问题——标准答案本身有歧义**: "要退货并投诉"算退换货还是投诉?
   "颜色差太失望"算投诉还是咨询? 这些边界连人都会吵。
   模型的"错"未必是错, 而是我们的标注定义没和模型对齐。

6. **invalid_rate 全程为 0**: 纯 prompt 的格式约束("只返回标签")在 2026 模型上
   遵守度很高。格式其实不难, 难的是判断准确性。
   (注: 换更弱的模型或更复杂输出格式如 JSON, invalid_rate 才会非 0 -> 04c 验证)

### 11.4 现代 few-shot 的正确用法

- few-shot 不是"多塞几个示例提准确率", 而是**针对性地教边界/格式/业务黑话**
- 要救某个顽固错误, 得加一条**专门区分该边界**的示例, 而非随便加高质量示例
- 见 11.5 加餐验证

### 11.5 加餐: 针对性示例能否救回顽固错误

给三条顽固错误各补一条专门教边界的示例(EXAMPLES_TARGETED = EXAMPLES_GOOD + 3条):
- "催一下订单怎么还不发货" -> 催单 (教: 催发货=催单)
- "最近有什么促销活动吗" -> 其他 (教: 问活动=其他)
- "质量太差非常不满意" -> 投诉 (教: 表达不满无诉求=投诉)

结果 V6_targeted: **83.3%**, 全场最高。

**救回的**:
- "双十一活动" 其他 ✅ (原错判商品咨询)
- "颜色差太失望" 投诉 ✅ (原错判商品咨询)

**没救回的**:
- "物流不更新发货没" 催单 ✗ (措辞太像物流查询, 针对示例也没完全扭转)

**新引入的错误**:
- "和描述不符怎么处理" 退换货 -> 商品咨询 ✗ (V1-V5 全对, 只有 V6 错)

### 11.6 加餐的两个重磅发现

1. **加示例是"按下葫芦浮起瓢"**: V6 净提升 +2 条, 但代价是把一条原本对的
   带偏了。针对性示例修复目标边界的同时, 可能干扰其他样本。
   -> 生产环境必须做**回归测试**: 不能只看"救回了想救的", 还要确认"没弄坏原本对的"。
   这就是 04e Mini Runner 和第16周 Evaluation 的意义。

2. **单次跑分不可靠**: V3 两次运行结果不同(58.3% vs 75%)。
   即使 enable_thinking=False, 模型输出仍有随机性(temperature 默认非0)。
   -> 靠单次跑分对比 prompt 好坏是危险的, 需要**多次跑取平均 / 固定 seed**。
   又一个指向"评估工程"的伏笔。

### 11.7 04a 最终结论

- few-shot 的现代价值 = **针对性教边界/业务黑话**, 不是"多塞示例提准确率"
- few-shot 有副作用(引入偏见、干扰其他样本), 不是免费午餐
- 现代模型: zero-shot 基线强、对示例顺序不敏感、格式遵守度高
- 判断 prompt 好坏必须靠**数据 + 多次运行 + 回归测试**, 不能凭单次或感觉
- 这些痛点(随机性、回归、按下葫芦浮起瓢)正是后续 04e / 第16周要解决的


---

## 12. 04b Reasoning Control 实验 — thinking 的真实代价

### 12.1 实验设置

- 任务: 25 道有明确答案的推理题(算术/代码追踪/逻辑/概率/博弈), 答案可归一化
- 模型: qwen3.7-flash
- 四种模式(同一批题):
  - M1: thinking=False, 直接问
  - M2: thinking=True
  - M3: thinking=True + prompt 要求"先验证"
  - M4: thinking=False + prompt 要求"一步步推理"(手写 CoT 思维链)

### 12.2 一个重要的前置发现: 靠"加难题"制造 reasoning gap 走不通

想用"更难的题"区分 thinking 开/关, 但在本实验里失败了: 加了贝叶斯/蒙提霍尔/
递归等"人类直觉容易出错"的题后, thinking=True 仍然 100%(另用 gemini-2.5-flash
抽查亦然)。

限定结论: **在本实验的数据集(25道小型题)和模型配置下, 单纯继续增加这类题目的
表面难度, 很难稳定制造出明显的 reasoning gap(推理能力差距)。**

注意边界: 这不等于"标准答案题难不住现代 LLM"——"有明确答案"的范围极大, 例如
很长的代码追踪、多约束组合优化、长文档信息整合、adversarial reasoning(对抗性
推理)、超大搜索空间、需要外部知识/工具的问题、长链条数学证明, 都可能仍然很难。
本实验只能说明小型 benchmark 题难以拉开差距。

-> 因此本实验更适合研究 thinking 的 **quality-cost trade-off(质量-成本权衡)**,
   而不是试图建立通用的"什么题算难题"标准。实验重心从 accuracy 转向 cost。

### 12.3 核心数据: 成本对比

| Mode | avg_latency | avg_output_tokens | accuracy | 输出干净? |
|------|------------|-------------------|----------|----------|
| M1 直接 | 1.19s | 2 | 84% (4错) | ✅ |
| M2 thinking | 12.79s | 872 | 100% | ✅ |
| M3 thinking+验证 | 17.62s | 1228 | 100% | ❌ 部分污染 |
| M4 手写CoT | 1.32s | 2 | 84% (4错) | ✅ |

极端单题: M2 火柴博弈题 43 秒、3076 output tokens(只为得到答案"2")。

指标口径说明(重要): 表中 output tokens 取自 API 的 `completion_tokens`, 它是
**reasoning(思考) + visible output(可见回答) 的合计**, 不等于纯 reasoning_tokens。
本实验用它作为 thinking 额外成本的**近似指标**。若 provider 能单独提供
reasoning_tokens, 应优先分开记录 input / reasoning / visible output。

### 12.4 四个关键结论

1. **thinking 提升准确率, 但只在少数难题上**: 84% -> 100%, 差的就是那 4 道
   多步推理题(格路计数、火柴博弈、条件概率等)。大部分题 M1 也对。

2. **代价极大(本实验)**: 本次 25 题中, M2 相比 M1 平均 output token 从 2 涨到 872
   (约 436×), latency 约 10×。注意这是"本模型+本数据集"的 output token 比,
   不等于"thinking 永远贵 436×", 也不等于"金钱成本 436×"(计费还看 input/cached)。
   结论: 对简单任务全量开 thinking 可能造成很高的资源浪费。

3. **手写 CoT(M4) 在本实验中无效**: M4 的 latency/token/错题和 M1 **几乎完全相同**
   (都是 2 tokens, 错同样 4 题), thinking=False 时喊"一步步推理"模型没照做。
   -> 限定结论: 对**原生 reasoning model**, 手写 CoT 已不是主要的推理控制手段
      (模型有内置 thinking, 不需人工规定思考步骤)。
   -> 注意边界: 这不等于"CoT 已死"。对**非 reasoning model / 小模型**, CoT 仍可能
      有效——它本就是为那类模型设计的。现代做法是优先控制 reasoning effort /
      thinking 开关, 给目标+约束, 而非规定内部思考步骤。

4. **verification(M3) 在本实验中未见收益**: 准确率和 M2 一样(都100%), 但更慢更贵
   (1228 vs 872 token), 还污染输出(把验证过程写进最终答案, 尤其难题)。
   -> 注意 ceiling effect(天花板效应): M2 已经 100%, verification 根本没有提升空间,
      所以只能说"本数据集上未观察到收益", 不能推广为"verification 无效"。
   -> 更深的认知: 生产级 verification 不是 prompt 里加一句"请验证", 而是
      check -> detect -> retry/repair 的可执行闭环(留待第15周 Harness)。
      单纯增加"请先验证"的提示**不能替代可观测、可执行的 verification loop**;
      本实验还观察到它可能增加 token/latency 并污染最终输出。

### 12.5 thinking=False 藏不住思考(设计层面的领悟)

M4 想让模型"思考过程一步步推理, 但最终只给结果"——可 thinking=False 没有
独立的 <think> 空间, 模型要么无视引导(退化成 M1), 要么把思考写进 content。
反证了**原生 thinking(M2)的价值**: 它提供了"思考归思考、答案归答案"的分离机制,
这是手写 CoT 给不了的。

### 12.6 最终认知: 这就是 Router 的意义

- 对标准答案类推理任务, 现代模型 thinking=False 已够准, 开 thinking 几乎不提升
  准确率, 却付出数百倍 token 和 10 倍延迟。
- 但你事先不知道哪道题属于"M1 会栽"的少数难题。
- 所以生产策略: **默认关 thinking(省钱快), 用一个前置 router 识别出真正需要深度
  推理的少数请求才开**。用 M1 成本处理简单题, 用 M2 能力处理难题。
- thinking 真正的价值场景不是"标准答案题", 而是 Agent 多步规划、长文档综合权衡、
  代码库级决策等**没有唯一答案**的任务(留待 Week 12/13 Agent 周体会)。
- -> Part 2 实现 router 验证这个策略。

---

## 13. 2026 年 Prompt Engineering 还剩什么用？—— 认知升华

做完 04a/04b, 会产生一个疑问: 既然 CoT 失效、few-shot 教逻辑也没用,
prompt engineering 是不是没用了? 结论不是"没用了", 而是**重心彻底转移了**。

### 13.1 在原生 reasoning model 上失效/降级的(本项目实验范围内验证过)

- 手写 CoT("一步步想") -> 04b: 在 reasoning model 上被原生 thinking 取代
  (非 reasoning model 上仍可能有效)
- verification 引导 -> 04b: 本数据集未见收益, 且污染输出
  (但因 M2 已 100% 存在天花板效应, 不能推广为"无效")
- 情绪勒索("做错有严重后果"/"给你小费") -> 普遍认为是玄学
- few-shot 教逻辑 -> 04a: 现代模型逻辑够强, 教逻辑收益低(教格式/边界仍有用)

### 13.2 依然核心的

- Instruction / 约束设计: 让模型知道要什么、不要什么、边界在哪(永恒)
- Few-shot 教**格式/业务黑话/分类边界**(不是教逻辑) -> 04a 的 V6 验证
- 结构化输出约束: 让输出能被程序消费(第3周深入)
- Role / 人设: 定角色、语气、职责边界
- RAG: 模型不知道你的私有数据, 必须喂进 context

### 13.3 重心转移(这才是关键)

prompt engineering 从"怎么写一句聪明的 prompt"变成了
"**怎么设计、组装、控制整个模型的输入**":

1. **Prompt Engineering 扩展为 Context Engineering**(不是谁大于谁, 是包含/长大)
   Context Engineering 本身就**包含** prompt/instruction/few-shot/message 排序,
   再加上历史、摘要、RAG、memory、工具结果、状态的组装。
   Section 3 手写的滑动窗口/摘要/动态 system prompt/memory 就是这个。
   怎么在有限 context 里组装得又准又省, 比写一句好 prompt 难/值钱得多。

2. **Reasoning Control**: 04b 做的——何时开/关 thinking、router 路由。2026 新核心。

3. **Prompt as Code**: Section 5 要做的——模板化、版本化、可测试、可评估。
   prompt 是像代码一样管理的工程资产, 不是随手写的字符串。

4. **评估驱动**: 04a/04b 都撞到"单次跑分不可靠""按下葫芦浮起瓢"。
   判断 prompt 好坏靠数据/评估, 不靠感觉(第16周核心)。

### 13.4 一句话

> Prompt engineering 没消失, 它长大了——从"写咒语"进化成
> "**设计 LLM 的输入程序 + 控制推理 + 管理上下文 + 用评估迭代**"。

降级的是"哄模型"的小聪明(谁都能学); 升级的是工程能力(context engineering /
reasoning control / evaluation)——这是软开 + 统计背景的用武之地, 也是 AI 应用
工程岗位中**值得重点展示**的工程能力。
(注: 这是基于本项目实验和公开文档趋势的判断, 不是经过验证的市场结论。)
