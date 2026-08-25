"""
Test script: Compare sliding_window vs summary strategies with the same 20 messages.

Messages are designed to include key facts that should be remembered:
- Round 2: user name (test user)
- Round 5: user preference (only use Python, no Java)
- Round 8: key decision (use FastAPI not Flask)
- Round 12: important constraint (deadline is next Friday)
- Round 15: completed task (database schema is done)

After 20 rounds, ask about early information to test retention.
"""

from week02_prompt.common.sessions import Session


def dispatch_command(session: Session, user_input: str):
    """Test helper: route input to session commands or chat."""
    match user_input:
        case "/pin":
            session.pin()
        case "/pins":
            session.pins()
        case "/compact":
            session.compact()
        case "/new":
            session.new()
        case _:
            session.chat(user_input)


# 20+ messages with commands mixed in, simulating real interaction
TEST_MESSAGES = [
    "你好，我想做一个AI学习项目",
    "对了，我叫小明，是一个前端工程师，想转型AI方向",
    "/pin",  # Pin the name introduction
    "我目前会JavaScript和Python，其他语言不太熟",
    "你觉得我应该从哪里开始学起？",
    "我只想用Python来做AI项目，Java太重了我不想碰",
    "/pin",  # Pin the language preference
    "Embedding是什么意思？能不能用大白话解释一下",
    "向量数据库有哪些选择？推荐一个适合个人项目的",
    "我决定后端用FastAPI不用Flask，因为FastAPI性能更好而且支持异步",
    "RAG和Fine-tuning有什么区别？什么场景用什么",
    "你帮我梳理一下接下来要学的技术路线",
    "我今天学了Token的概念，感觉中文比英文贵",
    "项目deadline是下周五，我需要在那之前完成一个demo",
    "Stream流式输出是怎么实现的？SSE协议是什么",
    "prompt engineering有哪些核心技巧",
    "数据库schema我设计好了，用的PostgreSQL，3张表：users, documents, embeddings",
    "/pins",  # Check what's pinned at this point
    "上下文窗口管理有几种策略",
    "我的demo需要支持多轮对话，有什么建议？",
    "Function Calling是什么原理？和MCP有什么区别",
    "LangChain值不值得学？还是直接手写比较好",
    "/compact",  # Manual compact (only works for summary strategy)
    "今天就到这里吧，帮我总结一下今天学了什么",
]

# Final test question: ask about early information
TEST_QUESTION = "你还记得我叫什么名字吗？我的编程语言偏好是什么？后端框架用的什么？deadline是什么时候？数据库schema是什么？"


def run_test(strategy: str, threshold: int):
    """Run all 20 messages through a session, then ask the test question."""
    print(f"\n{'=' * 70}")
    print(f"Strategy: {strategy} | Threshold: {threshold}")
    print(f"{'=' * 70}\n")

    session = Session(
        system_prompt="你是一个AI助手, 回答控制在200字以内, 简洁专业。",
        strategy=strategy,
        threshold=threshold,
        enable_thinking=False,
    )

    for i, msg in enumerate(TEST_MESSAGES, 1):
        if strategy == "sliding_window" and msg == "/compact":
            continue
        if msg.startswith("/"):
            print(f"[Cmd] {msg}")
        else:
            print(f"[Round {session.total_rounds + 1}] User: {msg}")
        dispatch_command(session, msg)
        print()

    # Final test: ask about early information
    print(f"\n{'=' * 70}")
    print("RETENTION TEST: Asking about information from early rounds")
    print(f"{'=' * 70}\n")
    print(f"User: {TEST_QUESTION}\n")
    dispatch_command(session, TEST_QUESTION)

    # Print session stats
    print(f"\n{'=' * 70}")
    print("SESSION STATS")
    print(f"{'=' * 70}")
    print(f"Total rounds: {session.total_rounds}")
    print(f"Waterline: {session._waterline}")
    print(f"Pending rounds: {session._count_pending_rounds()}")
    print(f"Messages in history: {len(session.messages)}")
    if session.summary:
        print(f"Summary:\n{session.summary}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_strategies.py <sliding_window|summary> [threshold]")
        print("  Example: python test_strategies.py sliding_window 8")
        print("  Example: python test_strategies.py summary 8")
        sys.exit(1)

    strategy = sys.argv[1]
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    run_test(strategy, threshold)
