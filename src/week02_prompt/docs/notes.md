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
