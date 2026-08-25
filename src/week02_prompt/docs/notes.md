# Week 2 学习笔记

## 目录

- [1. Messages 三角色与 Prompt Engineering 的关系](#1-messages-三角色与-prompt-engineering-的关系)
- [2. Messages 数组实验结论](#2-messages-数组实验结论)
- [3. Python 可变对象引用陷阱](#3-python-可变对象引用陷阱)
- [4. API 内容安全过滤导致流式中断](#4-api-内容安全过滤导致流式中断)
- [5. 03a 滑动窗口实战总结](#5-03a-滑动窗口实战总结)
- [6. 上下文管理策略选型 — 贴合产品定位](#6-上下文管理策略选型--贴合产品定位)
- [7. 03b 摘要压缩 — 统一架构设计历程](#7-03b-摘要压缩--统一架构设计历程)
- [7. API 协议演进与开发者策略](#7-api-协议演进与开发者策略)

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

## 7. 03b 摘要压缩 — 统一架构设计历程

### 7.1 核心设计决策的演变

| 问题 | 初始方案 | 最终方案 | 为什么改 |
|------|---------|---------|---------|
| messages 是否删除 | compact 时删除旧消息 | 永不删除, 保留完整历史 | 和 Kiro jsonl 一致, save 时数据完整 |
| 两种策略的 messages 行为 | 不同(sliding 不删, summary 删) | 统一不删 | 代码对称, 逻辑简单 |
| keep_recent + threshold | 两个变量, 含义重叠 | threshold(用户配置) + _KEEP_RECENT(内部常量) | 职责分离清晰 |
| 何时触发策略 | 每轮都截断 | 攒够 threshold 才触发 | 尽可能保留上下文, 回答才准确 |
| 两次触发之间发什么 | 只发 _KEEP_RECENT 轮 | 发水位线之上所有轮次 | 不浪费已有上下文 |
| rounds 计数 | _current_rounds (基于 messages 长度) | total_rounds (手动+1, 只增不减) | 和 pin 的轮次号绑定, 不受 compact 影响 |
| 避免重复压缩 | 无机制 | _waterline 水位线 | 记录已处理到哪一轮 |

### 7.2 waterline(水位线) 机制

水位线是整个架构的核心概念:
- `_waterline = N` 表示第 1~N 轮已经被处理过(omitted 或 summarized)
- `_count_pending_rounds()` = 水位线之上的非 pinned 轮数
- 触发条件: pending > threshold
- 触发后: 水位线推进, pending 回到 _KEEP_RECENT

两种策略共享同一套机制, 区别只是:
- sliding_window: 推进水位线(免费, 不调 API), 发送时用 omit notice
- summary: 调 compact()(调一次 API 生成摘要), 发送时用 checkpoint

### 7.3 渐进式结构化摘要 (参考 Codex + DSH + Kiro)

COMPACTION_PROMPT 设计要点:
- 5 个固定 section: 用户信息 / 关键事实与决定 / 已完成 / 待完成 / 当前状态
- 渐进式: 新 summary = 旧 summary 中仍正确的 + 新对话要点
- 精确保留: 姓名/数字/路径等不能被模糊化
- 字数控制: 300 字以内, 防止 summary 无限膨胀
- Preamble: 放回 context 时告诉模型"这是背景, 不要复述"

### 7.4 对比测试结果 (threshold=8, 20 轮对话)

| 信息 | 轮次 | Pinned? | Sliding Window | Summary |
|------|------|---------|:-:|:-:|
| 小明 | 2 | ✅ | ✅ 记住 | ✅ 记住 |
| Python 偏好 | 5 | ✅ | ✅ 记住 | ✅ 记住 |
| FastAPI | 8 | ❌ | ✅ (回复携带) | ✅ (在 summary 中) |
| Deadline 下周五 | 12 | ❌ | ❌ 忘了 | ✅ 记住 |
| DB Schema | 15 | ❌ | ❌ 忘了 | ❌ 模糊(被摘要简化) |

结论: Summary 策略信息保留明显优于 Sliding Window, 但有一次 API 调用的成本.

### 7.5 关键踩坑

1. **pinned_rounds 和 waterline 的交互**: pinned 在水位线之上才算"pending", 之下的不用再减
2. **sliding_window 不能每轮都切**: 要攒够 threshold, 两次触发之间逐轮累积上下文
3. **_get_rounds_above_waterline() 复用**: 同一段逻辑写了 3 次才发现要封装
4. **class 变量命名冲突**: `list` 方法名覆盖了 Python 内置 `list`, 导致类型注解报错
5. **变量命名语义**: keep_recent/threshold/KEEP_RECENT 三者职责要清晰分离
