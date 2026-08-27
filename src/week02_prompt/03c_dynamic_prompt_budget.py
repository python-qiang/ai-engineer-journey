"""
第2周 - 第3节 - 任务3: 动态 System Prompt + Token 预算分配

=== 本任务完成后你需要掌握的 ===

1. 动态 System Prompt (context block 注入):
   - system prompt 不是固定字符串, 而是 base + 按需拼接的 context block
   - 内容来源: memory(用户手动/模型提取) + 现有的 omit/checkpoint 保持独立消息不变
   - 好处: 关键信息即使被 sliding_window 冲掉, 也在 system prompt 中永远保留

2. 关键信息的两种记忆方式:
   - /remember key value: 用户手动设置(如 /remember name Alice)
   - 用户对话中说"记住这个": 模型提取关键信息存入 memory
   - memory 注入到 system prompt 的 context block 中, 不受 waterline 影响

3. Token 精确计算(复习 Week 1 Section 2 + qwen-tokenizer):
   - qwen-tokenizer 基于 tiktoken, 提供千问系列模型的精确 tokenizer
   - 封装 count_tokens(messages) 到 framework/ 中, 考虑 chat template overhead
   - Qwen chat template: <|im_start|>role\ncontent<|im_end|>\n (每条消息 +4 overhead)
   - 末尾 +3 (assistant prompt: <|im_start|>assistant\n)

4. Token 预算管理:
   - TOKEN_BUDGET = 32000 (性价比最优区间, 推理速度快)
   - 发送前用 count_tokens() 精确预估
   - 超 80%: 打印警告建议 /compact
   - 超 90%: 自动触发 compact(补充 threshold 机制, 基于 token 而非轮次)
   - 双触发机制: 轮次超 threshold OR token 超 90%, 任一触发压缩

5. Token Usage 展示 + Cost 追踪(每轮打印):
   - [Tokens: X / 32000 (Y%) | Input: A | Output: B | Cost: ¥C]
   - 基于 API 返回的 usage.prompt_tokens/completion_tokens 精确值
   - 成本: 输入 2元/百万tokens (8折=1.6元) + 输出 8元/百万tokens (8折=6.4元)
   - 累计追踪 self.total_input_tokens, self.total_output_tokens

=== 本任务不需要关心的 ===

- 模型自动异步提取记忆(后台跑小模型) -> 第13周 LangGraph State
- RAG 向量记忆 -> 第5-8周
- 记忆的持久化存储 -> 了解即可, 本节用内存 dict
- chat template 的精确 BOS/EOS token -> ±5 误差可接受

=== 练习 ===

基于 03b 扩展:

1. framework/tokens.py — 精确 token 计算工具:
   - count_message_tokens(messages: list[dict], model: str = DEFAULT_MODEL) -> int
   - 根据 model 映射到正确的 qwen-tokenizer (按 generation 匹配)
   - 每条消息: content tokens + 5 (chat template overhead, 实测验证)
   - 末尾 +3 (assistant generation prompt) + 4 (API 固定 overhead)
   - 验证: 对比 API 返回的 prompt_tokens, 误差 < 5%

2. Memory 机制 (扩展 Session class):
   - 新增 self.memory: dict[str, str]
   - /remember key value: 手动写入
   - /memory: 查看所有记忆
   - /forget key: 删除某条
   - /unpin N: 按轮次号取消 pin (与 /pin 对称)
   - "记住"触发: 用户消息含"记住"/"remember"时, 调模型提取 JSON, 合并到 memory

3. 动态 System Prompt:
   - 新增 _build_system_prompt(): base + [Memory] block
   - 每次构造发送版本时, messages[0] 替换为动态生成的 system prompt
   - memory 信息独立于 waterline, 永远在 system prompt 中

4. Token 预算管理:
   - TOKEN_BUDGET = 32000 (类变量, 可配置)
   - 在 chat() 中 _apply_strategy() 之后, 发送前调 count_message_tokens()
   - >80%: logger.warning + 打印建议 /compact
   - >90%: 自动触发 compact (即使轮次未超 threshold)

5. Usage 展示:
   - 每轮打印: [Tokens: X / 32000 (Y%) | Input: A | Output: B | Cost: ¥C]
   - self.total_input_tokens += usage.prompt_tokens
   - self.total_output_tokens += usage.completion_tokens
   - cost = input * 1.6e-6 + output * 6.4e-6

=== 提示 ===

- qwen-tokenizer 用法:
    from qwen_tokenizer import get_tokenizer
    tok = get_tokenizer('qwen3.5-27b')
    token_count = len(tok.encode(text))

- model 映射策略(按 generation, 不是精确 model name):
    提取大版本号(qwen3.7-plus -> 3.7, qwen2.5:1.5b -> 2.5)
    >= 3.0: 用 qwen3.5-27b (248K vocab)
    <  3.0: 用 qwen2.5-72b-instruct (151K vocab)
    非千问模型: fallback 到 tiktoken cl100k_base (以后再处理)

- Chat template overhead(实测验证):
    每条消息: <|im_start|>(1) + role(1) + \n(1) + content(N) + <|im_end|>(1) + \n(1) = N+5
    末尾 assistant prompt: <|im_start|>(1) + assistant(1) + \n(1) = 3
    API 额外 overhead: ~4 tokens (thinking mode 相关, 固定值)
    公式: total = sum(content_tokens + 5 for each msg) + 3 + 4

- _build_system_prompt() 示例:
    base = self.system_prompt
    if not self.memory:
        return base
    memory_block = "; ".join(f"{k}: {v}" for k, v in self.memory.items())
    return f"{base}\\n\\n[Memory] {memory_block}"

- "记住"检测: if "记住" in user_input or "remember" in user_input.lower()
- 提取 prompt: "从以下消息提取需要长期记住的关键事实, JSON格式 {key: value}, 无则返回 {}"
- TOKEN_BUDGET 是独立于 threshold 的第二道防线(轮次超了 or token 超了, 任一触发)
- 成本计算用 API 返回的 prompt_tokens/completion_tokens, 不用本地预估值
- count_message_tokens() 只用于发送前预判, 不用于计费(计费用 API 返回值)
"""

# ============================================================
# 你的代码写在下面
# ============================================================

from common.sessions import Session

if __name__ == "__main__":
    session = Session(strategy="summary", threshold=8)

    print("=== Multi-turn Chat CLI (Summary Compression) ===")
    print(
        f"Session: {session.session_id} | Strategy: {session.strategy} | Threshold: {session.threshold}"
    )
    print(
        "Commands: /new /save /load /list /pin /unpin /pins /compact /remember /forget /memory /quit /exit"
    )

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        match user_input:
            case "/quit" | "/exit":
                break
            case "/new":
                session.new()
            case "/save":
                session.save()
            case "/load":
                session.load()
            case "/list":
                session.list_sessions()
            case "/pin":
                session.pin()
            case "/unpin":
                session.unpin(user_input)
            case "/pins":
                session.pins()
            case "/compact":
                session.compact()
            case "/remember":
                session.remember(user_input)
            case "/forget":
                session.forget(user_input)
            case "/memory":
                session.view_memory()
            case _:
                session.chat(user_input)
