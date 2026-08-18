# Week 2 学习笔记

## 目录

- [1. Messages 三角色与 Prompt Engineering 的关系](#1-messages-三角色与-prompt-engineering-的关系)
- [2. Messages 数组实验结论](#2-messages-数组实验结论)

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
| 非 pinned 早期内容 | 被遗忘 | 第3轮说的"我叫张强"在第19轮已被忘记 |

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
