"""
第2周 - 第3节 - 任务1: 滑动窗口 + Pinned Messages

=== 本任务完成后你需要掌握的 ===

1. 滑动窗口策略:
   - self.messages 始终保存完整历史(不丢数据)
   - 发送给 API 前, _apply_strategy() 返回精简版 messages
   - 精简逻辑: system + [省略提示] + pinned + 最近 N 轮
   - N 的选择: 太小容易失忆, 太大浪费 token (默认 5)

2. Pinned Messages:
   - /pin 将上一轮(user+assistant)加入 pinned_messages 列表
   - 用 pinned_rounds set 防止重复 pin 同一轮
   - pinned 不计入 N 轮计数, 截断时强制保留
   - 相同问题不同轮次可以分别 pin(回答可能不同)

3. 截断后的提示:
   - 有历史被省略时, 插入一条 system 消息告知模型
   - 让模型知道"前面有上下文但看不到了, 需要时可以问用户"

=== 本任务不需要关心的 ===

- 摘要压缩 -> 任务2 (03b)
- Token 精确计算 -> 任务3 (03c)
- 动态 System Prompt 注入 -> 任务3 (03c)

=== 练习 ===

在 Session class (common/sessions.py) 中实现:
  - __init__ 新增参数: strategy(str|None), window_size(int=5)
  - pin(): 将上一轮加入 pinned, 带防重复(pinned_rounds set)
  - pins(): 打印当前所有 pinned 消息
  - _apply_strategy(): 根据 strategy 返回实际发送的 messages
  - _sliding_window(): system + [省略提示] + pinned + recent N 轮

在 03a CLI 中:
  - 创建 Session 时传入 strategy="sliding_window", window_size=5
  - /pin 和 /pins 命令路由到 session.pin() / session.pins()
  - 测试: 聊 10+ 轮, 验证模型忘了早期内容但还记得 pinned 内容

=== 提示 ===

- self.messages 保存完整历史, _sliding_window() 只负责构造发送版本
- 发送的 messages 顺序: [system, omit_notice?, *pinned, *recent]
- omit_notice 示例: {"role": "system", "content": "[X rounds of history omitted]"}
- pinned 中的消息要从 recent 中排除(避免重复发送)
- 复用 framework/chat.py 的 stream_chat()
"""

# ============================================================
# 你的代码写在下面
# ============================================================

from common.sessions import Session

if __name__ == "__main__":
    session = Session(strategy="sliding_window", window_size=5)

    print("=== Multi-turn Chat CLI (Sliding Window) ===")
    print(
        f"Session: {session.session_id} | Strategy: {session.strategy} | Window: {session.window_size}"
    )
    print("Commands: /new /save /load /list /pin /pins /quit | /exit")

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
