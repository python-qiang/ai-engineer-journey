"""
第2周 - 第3节 - 任务2: 摘要压缩

=== 本任务完成后你需要掌握的 ===

1. 摘要压缩策略(与 sliding_window 共享统一架构):
   - self.messages 保留完整历史(永不删除)
   - 水位线(_waterline): 标记已压缩到第几轮
   - 触发条件: 水位线之上的非 pinned 轮数 > threshold
   - 触发时: 调 compact()(API 调用生成摘要), 推进水位线
   - 两次触发之间: 发送 checkpoint + 水位线之上所有轮次

2. 渐进式结构化摘要(参考 Codex + DeepSeek Harness + Kiro):
   - 固定 5 个 section: 用户信息 / 关键事实与决定 / 已完成 / 待完成 / 当前状态
   - 渐进式: 新 summary = 旧 summary 中仍正确的 + 新对话的要点
   - 精确保留: 姓名/数字/路径等不能被模糊化
   - 字数控制: 300 字以内
   - Preamble: 放回 context 时告诉模型"这是背景, 不要复述"

3. 两种策略对比(共享同一套 waterline + threshold 机制):
   - sliding_window: 推进水位线(免费), 发送时用 omit notice, 旧信息彻底丢失
   - summary: 调 compact(有成本), 发送时用 checkpoint, 旧信息浓缩保留
   - 对比结果: summary 信息保留明显优于 sliding_window(如 deadline 被记住)

4. /compact 手动触发:
   - 只要水位线之上有超过 _KEEP_RECENT 轮非 pinned 历史就能执行
   - 不等自动阈值, 用户觉得该压缩时随时触发

=== 本任务不需要关心的 ===

- Token 精确计算和预算管理 -> 03c
- 动态 System Prompt 模板改造 -> 03c
- KV cache 复用优化(DSH 的前缀对齐) -> 了解即可
- messages_snapshot 持久化(Kiro 在 jsonl 中记录) -> 了解即可

=== 练习 ===

基于 03a 扩展 Session class, 实现 strategy="summary":

1. _COMPACTION_PROMPT(类变量):
   结构化渐进式 prompt, 5 个固定 section, 300 字以内

2. compact():
   - 取水位线之上的非 pinned 轮次, 保留最近 _KEEP_RECENT, 压缩其余
   - 拼接 prompt: existing_summary + 新对话文本
   - stream_chat(print_content=False, enable_thinking=self.enable_thinking)
   - 更新 self.summary 和 self._waterline
   - try/except 保护 API 调用

3. _summary_compress():
   - 超阈值时先调 compact()
   - 水位线 > 0 时: system + checkpoint + pinned + 水位线之上所有轮次
   - 水位线 = 0 时: 返回完整 messages 的 copy

4. /compact 命令 + 对比测试:
   - 03b CLI 加 /compact 命令(03a 没有)
   - 用 test_strategies.py 对比两种策略在相同 20 轮对话后的记忆保留差异

=== 提示 ===

- compact() 不修改 self.messages, 只更新 self.summary + self._waterline
- _summary_compress() 和 _sliding_window() 完全对称(只是 omit vs checkpoint)
- 渐进式: 每次 compact 传入 existing_summary, 模型在旧摘要基础上合并
- 水位线避免重复压缩: 只压缩 _waterline+1 到 total_rounds 之间的轮次
- 日志: 打印 compact 的完整决策依据(total_rounds, pinned, compressed_rounds, waterline)
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
    print("Commands: /new /save /load /list /pin /pins /compact /quit /exit")

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
            case "/pins":
                session.pins()
            case "/compact":
                session.compact()
            case _:
                session.chat(user_input)
