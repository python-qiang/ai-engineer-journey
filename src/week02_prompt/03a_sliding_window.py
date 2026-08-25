"""
第2周 - 第3节 - 任务1: 滑动窗口 + Pinned Messages

=== 本任务完成后你需要掌握的 ===

1. 滑动窗口策略(与 summary 共享统一架构):
   - self.messages 始终保存完整历史(永不删除)
   - 水位线(_waterline): 标记已处理到第几轮
   - 触发条件: 水位线之上的非 pinned 轮数 > threshold
   - 触发时: 推进水位线(不调 API), omit notice 显示累计省略数
   - 两次触发之间: 发送水位线之上的所有轮次(逐轮累积上下文)

2. Pinned Messages:
   - /pin 将上一轮加入 pinned_messages(用 total_rounds 标识)
   - pinned_rounds set 防止重复 pin
   - pinned 在水位线之上不计入 pending(不触发截断)
   - 发送时 pinned 始终保留, 不受截断影响

3. 统一的策略机制(sliding_window 和 summary 共用):
   - threshold: 用户配置, 攒够多少轮才触发
   - _KEEP_RECENT: 内部常量(=2), 触发时保留几轮
   - _waterline: 水位线, 两种策略共用
   - _count_pending_rounds(): 水位线之上的非 pinned 轮数
   - _get_rounds_above_waterline(): 取水位线之上的非 pinned 轮次号

=== 本任务不需要关心的 ===

- 摘要压缩 -> 任务2 (03b)
- Token 精确计算 -> 任务3 (03c)
- 动态 System Prompt 注入 -> 任务3 (03c)

=== 练习 ===

在 Session class (common/sessions.py) 中实现:
  - __init__: strategy, threshold, total_rounds, _waterline, pinned_rounds
  - pin() / pins(): 管理 pinned 消息
  - _apply_strategy(): 路由到 _sliding_window() 或 _summary_compress()
  - _sliding_window(): 超阈值推进水位线, 构造 system + omit + pinned + above_waterline

在 03a CLI 中:
  - Session(strategy="sliding_window", threshold=5)
  - match-case 路由 /pin /pins /new /save /load /list 命令
  - 测试: 聊 10+ 轮, 验证 threshold 触发后 sent 下降, 然后逐轮累积

=== 提示 ===

- self.messages 永不删除, _sliding_window() 只构造发送版本(必须返回 copy)
- omit 数量是累计值(水位线之下的非 pinned 轮数)
- 水位线之上的所有轮次都发送(不只是 _KEEP_RECENT)
- _KEEP_RECENT 只在触发时决定"砍完保留几轮"
"""

# ============================================================
# 你的代码写在下面
# ============================================================

from common.sessions import Session

if __name__ == "__main__":
    session = Session(strategy="sliding_window", threshold=5)

    print("=== Multi-turn Chat CLI (Sliding Window) ===")
    print(
        f"Session: {session.session_id} | Strategy: {session.strategy} | Threshold: {session.threshold}"
    )
    print("Commands: /new /save /load /list /pin /pins /quit /exit")

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
            case _:
                session.chat(user_input)
