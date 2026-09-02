"""
Test script for 03c: dynamic system prompt + memory + token budget.

Covers all new 03c features:
- Memory: /remember, /memory, /forget, /unpin
- Auto-extract: messages containing "记住" trigger fact extraction into memory
- Dynamic system prompt: memory injected as [Memory] block, visible every round
- Token budget trigger: a small token_budget forces compression regardless of
  round count (the key thing to observe)
- Cumulative usage display: [Token Usage: X / 1M | Input | Output | Cost]

Two scenarios:
1. `budget`  - small token_budget + long messages -> observe budget-triggered
               compression happening BEFORE the round threshold is reached.
2. `memory`  - exercise /remember, /forget, /unpin, and "记住" auto-extract,
               then verify the model still knows the memorized facts.

Usage:
  python 03c_test_dynamic_budget.py budget
  python 03c_test_dynamic_budget.py memory
"""

from week02_prompt.common.sessions import Session


def dispatch_command(session: Session, user_input: str):
    """Test helper: route input to session commands or chat."""
    match user_input.split(None, 1):
        case ["/pin"]:
            session.pin()
        case ["/pins"]:
            session.pins()
        case ["/compact"]:
            session.compact()
        case ["/memory"]:
            session.view_memory()
        case ["/new"]:
            session.new()
        case ["/unpin", arg]:
            session.unpin(arg)
        case ["/remember", arg]:
            session.remember(arg)
        case ["/forget", arg]:
            session.forget(arg)
        case _:
            session.chat(user_input)


# ----------------------------------------------------------------------
# Scenario 1: token budget trigger
# ----------------------------------------------------------------------
# A long paragraph so each round consumes a lot of tokens quickly.
# With a small token_budget, compression should trigger after only a few
# rounds -- long before a normal round threshold would.
_LONG_TEXT = (
    "请详细解释一下这个概念，我需要一个包含背景、原理、优缺点、"
    "实际应用场景以及代码示例的完整回答，越详细越好，最好能举多个例子。"
)

BUDGET_MESSAGES = [
    f"什么是 Embedding？{_LONG_TEXT}",
    f"什么是向量数据库？{_LONG_TEXT}",
    f"什么是 RAG？{_LONG_TEXT}",
    f"什么是 Function Calling？{_LONG_TEXT}",
    f"什么是 Fine-tuning？{_LONG_TEXT}",
    f"什么是 Prompt Engineering？{_LONG_TEXT}",
]


# ----------------------------------------------------------------------
# Scenario 2: memory commands + auto-extract
# ----------------------------------------------------------------------
MEMORY_MESSAGES = [
    "你好，我想做一个AI学习项目",
    "/remember name Alice",  # manual memory
    "/remember lang Python",  # manual memory
    "/memory",  # view memory
    "记住，我的项目截止日期是下周五，数据库用 PostgreSQL",  # auto-extract
    "/memory",  # view memory after auto-extract
    "帮我推荐一个向量数据库",  # normal chat (memory should be in system prompt)
    "/pin",  # pin this round (round 3)
    "/pins",  # verify pinned
    "/unpin 3",  # unpin the round just pinned (round 3)
    "/pins",  # verify unpinned
    "/forget lang",  # forget one memory key
    "/memory",  # verify forgotten
]

MEMORY_QUESTION = "你还记得我叫什么名字吗？我的项目截止日期是什么时候？数据库用什么？"


def run_budget_test(token_budget: int, threshold: int):
    """Send long messages with a small budget to force budget-triggered compaction."""
    print(f"\n{'=' * 70}")
    print(
        f"BUDGET TEST | strategy=summary | token_budget={token_budget} | threshold={threshold}"
    )
    print("Expect: compaction triggered by TOKEN BUDGET before round threshold")
    print(f"{'=' * 70}\n")

    session = Session(
        system_prompt="你是一个AI助手, 回答控制在150字以内, 简洁专业。",
        strategy="summary",
        threshold=threshold,
        token_budget=token_budget,
        enable_thinking=False,
    )

    for msg in BUDGET_MESSAGES:
        print(f"[Round {session.total_rounds + 1}] User: {msg[:40]}...")
        prev_waterline = session._waterline
        session.chat(msg)
        if session._waterline != prev_waterline:
            print(
                f"  >>> COMPACTION TRIGGERED: waterline {prev_waterline} -> {session._waterline} "
                f"(pending was {session._count_pending_rounds()}, threshold={threshold})"
            )
        print()

    _print_stats(session)


def run_memory_test(threshold: int):
    """Exercise memory commands and auto-extract, then verify retention."""
    print(f"\n{'=' * 70}")
    print(f"MEMORY TEST | strategy=summary | threshold={threshold}")
    print("Expect: /remember, auto-extract, /unpin, /forget all work; facts retained")
    print(f"{'=' * 70}\n")

    session = Session(
        system_prompt="你是一个AI助手, 回答控制在150字以内, 简洁专业。",
        strategy="summary",
        threshold=threshold,
        enable_thinking=False,
    )

    for msg in MEMORY_MESSAGES:
        if msg.startswith("/"):
            print(f"[Cmd] {msg}")
        else:
            print(f"[Round {session.total_rounds + 1}] User: {msg}")
        dispatch_command(session, msg)
        print()

    print(f"\n{'=' * 70}")
    print("RETENTION TEST: asking about memorized facts")
    print(f"{'=' * 70}\n")
    print(f"User: {MEMORY_QUESTION}\n")
    session.chat(MEMORY_QUESTION)

    _print_stats(session)


def _print_stats(session: Session):
    print(f"\n{'=' * 70}")
    print("SESSION STATS")
    print(f"{'=' * 70}")
    print(f"Total rounds: {session.total_rounds}")
    print(f"Waterline: {session._waterline}")
    print(f"Pending rounds: {session._count_pending_rounds()}")
    print(f"Pinned rounds: {sorted(session.pinned_rounds)}")
    print(f"Memory: {session.memory}")
    print(f"Total input tokens: {session.total_input_tokens}")
    print(f"Total output tokens: {session.total_output_tokens}")
    if session.summary:
        print(f"Summary:\n{session.summary}")


if __name__ == "__main__":
    import contextlib
    import os
    import sys

    if len(sys.argv) < 2 or sys.argv[1] not in ("budget", "memory"):
        print("Usage: python 03c_test_dynamic_budget.py <budget|memory> [arg]")
        print("  budget [token_budget]  - default 32000, small to force trigger")
        print("  memory [threshold]     - default 8")
        sys.exit(1)

    # Save all test output to a fixed file instead of printing to terminal.
    _OUT_DIR = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "devenv_temp",
        "test_results",
        "week02",
    )
    os.makedirs(_OUT_DIR, exist_ok=True)
    _OUT_PATH = os.path.join(_OUT_DIR, "03c_dynamic_budget.md")

    scenario = sys.argv[1]
    with open(_OUT_PATH, "a", encoding="utf-8") as out, contextlib.redirect_stdout(out):
        print(f"\n\n{'#' * 70}")
        print(f"# RUN: scenario={scenario} args={sys.argv[2:]}")
        print(f"{'#' * 70}")
        if scenario == "budget":
            token_budget = int(sys.argv[2]) if len(sys.argv) > 2 else 800
            run_budget_test(token_budget=token_budget, threshold=100)
        else:
            threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 8
            run_memory_test(threshold=threshold)

    print(f"Test output saved to {os.path.relpath(_OUT_PATH)}")
