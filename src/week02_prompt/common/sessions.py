"""
week02_prompt/common/sessions.py - Session state management

Encapsulates all session-related state and commands.
CLI task files can call these directly without reimplementing.
"""

import json
import logging
import os
import time
import uuid

import httpx

from framework.chat import stream_chat

logger = logging.getLogger(__name__)


class Session:
    """Manage a single conversation session's state."""

    _SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")

    _COMPACTION_PROMPT = """请基于【已有摘要】和【新对话】，生成一份更新后的结构化摘要。

输出以下固定结构(每个 section 必须保留，无内容写"(无)"):

## 用户信息
- [姓名/角色/偏好/约束]

## 关键事实与决定
- [已确认的重要信息、做出的选择及理由]

## 已完成
- [本次对话中完成的工作]

## 待完成
- [明确提出但尚未完成的任务]

## 当前状态
- [正在进行的工作，中断点在哪]

规则:
- 保留精确信息: 姓名、数字、代码片段、文件路径、命令等
- 旧摘要中仍然正确的信息要保留，过时的要丢弃
- 新对话中的新信息要合并进来
- 用简洁要点, 不要长段落, 总字数控制在300字以内
- 只输出摘要，不要解释

---

已有摘要:
{existing_summary}

新对话内容:
{new_conversations}

更新后的摘要:"""

    _CHECKPOINT_PREAMBLE = "[Checkpoint - established background, do not restate. Continue from messages below.]"

    _KEEP_RECENT = 2

    @staticmethod
    def _new_session_id() -> str:
        return uuid.uuid4().hex[:16]

    def __init__(
        self,
        system_prompt: str = "你是一个无所不知的AI智能助手。",
        strategy: str | None = None,
        threshold: int = 10,
        enable_thinking: bool = True,
    ):
        """Initialize a new session.

        Args:
            system_prompt: The system message always at the front.
            strategy: Context management strategy. None/"sliding_window"/"summary".
            threshold: How many new pending rounds to accumulate before triggering.
            enable_thinking: Whether to enable model thinking mode for chat.
        """
        os.makedirs(self._SESSIONS_DIR, exist_ok=True)
        self.system_prompt = system_prompt
        self.session_id = self._new_session_id()
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]
        self.strategy = strategy
        self.threshold = threshold
        self.enable_thinking = enable_thinking
        self.total_rounds = 0
        self._waterline = (
            0  # Rounds 1.._waterline have been processed (omitted/summarized)
        )
        self.pinned_rounds: set[int] = set()
        self.pinned_messages: list[dict] = []
        self.summary: str = ""

    # ------------------------------------------------------------------
    # Strategy internals
    # ------------------------------------------------------------------

    def _reset_state(self):
        self.total_rounds = 0
        self._waterline = 0
        self.pinned_rounds.clear()
        self.pinned_messages.clear()
        self.summary = ""

    def _get_rounds_above_waterline(self) -> list[int]:
        """Get non-pinned round numbers that haven't been processed yet."""
        return [
            r
            for r in range(self._waterline + 1, self.total_rounds + 1)
            if r not in self.pinned_rounds
        ]

    def _count_pending_rounds(self) -> int:
        """Count how many non-pinned rounds are above waterline (awaiting processing)."""
        return len(self._get_rounds_above_waterline())

    # ------------------------------------------------------------------
    # Strategy dispatch
    # ------------------------------------------------------------------

    def _apply_strategy(self) -> list[dict]:
        """Build the messages list to send to the API (truncated/compressed copy)."""
        match self.strategy:
            case "sliding_window":
                return self._sliding_window()
            case "summary":
                return self._summary_compress()
            case _:
                return list(self.messages)

    def _sliding_window(self) -> list[dict]:
        """Sliding window: keep all above waterline until threshold, then cut.

        - Before threshold: send system + omit_notice + pinned + ALL rounds above waterline
        - At threshold: advance waterline, then send system + omit_notice + pinned + ALL above waterline (which is now only _KEEP_RECENT)
        """
        if self._count_pending_rounds() > self.threshold:
            pending_rounds = self._get_rounds_above_waterline()
            if len(pending_rounds) > self._KEEP_RECENT:
                self._waterline = pending_rounds[-(self._KEEP_RECENT)] - 1
                logger.info(
                    "Sliding window triggered: total_rounds=%d, pinned=%s, pending=%d, threshold=%d -> waterline=%d",
                    self.total_rounds,
                    sorted(self.pinned_rounds),
                    len(pending_rounds),
                    self.threshold,
                    self._waterline,
                )

        if self._waterline == 0:
            return list(self.messages)

        # Total omitted (cumulative)
        total_omitted = len(
            [r for r in range(1, self._waterline + 1) if r not in self.pinned_rounds]
        )

        # All rounds above waterline (not just _KEEP_RECENT - accumulates between triggers)
        pending_rounds = self._get_rounds_above_waterline()
        above_messages = []
        for r in pending_rounds:
            idx = (r - 1) * 2 + 1
            above_messages.extend(self.messages[idx : idx + 2])

        result = [self.messages[0]]
        if total_omitted > 0:
            result.append(
                {
                    "role": "system",
                    "content": f"[{total_omitted} rounds of history omitted. Ask user if you need earlier context.]",
                }
            )
        if self.pinned_messages:
            result.extend(self.pinned_messages)
        result.extend(above_messages)
        return result

    def _summary_compress(self) -> list[dict]:
        """Summary compression: keep all above waterline until threshold, then compact.

        - Before threshold: send system + checkpoint + pinned + ALL rounds above waterline
        - At threshold: compact (updates summary & waterline), then send system + checkpoint + pinned + ALL above waterline (which is now only _KEEP_RECENT)
        """
        if self._count_pending_rounds() > self.threshold:
            self.compact()

        if self._waterline == 0:
            return list(self.messages)

        # All rounds above waterline (accumulates between triggers)
        pending_rounds = self._get_rounds_above_waterline()
        above_messages = []
        for r in pending_rounds:
            idx = (r - 1) * 2 + 1
            above_messages.extend(self.messages[idx : idx + 2])

        result = [self.messages[0]]
        if self.summary:
            result.append(
                {
                    "role": "system",
                    "content": f"{self._CHECKPOINT_PREAMBLE}\n\n{self.summary}",
                }
            )
        if self.pinned_messages:
            result.extend(self.pinned_messages)
        result.extend(above_messages)
        return result

    # ------------------------------------------------------------------
    # Pin
    # ------------------------------------------------------------------

    def pin(self):
        """Pin the last round so it survives truncation/compression."""
        if self.total_rounds == 0:
            print("[Nothing to pin]")
            return
        if self.total_rounds in self.pinned_rounds:
            print("[Already pinned]")
            return
        self.pinned_rounds.add(self.total_rounds)
        self.pinned_messages.extend(self.messages[-2:])
        print(f"[Pinned round {self.total_rounds}]")

    def pins(self):
        """Display all pinned messages."""
        if not self.pinned_messages:
            print("[No messages have been pinned.]")
            return
        print(f"[{len(self.pinned_rounds)} pinned round(s)]")
        for msg in self.pinned_messages:
            prefix = "  User:" if msg["role"] == "user" else "  AI:  "
            print(f"{prefix} {msg['content'][:80]}")

    # ------------------------------------------------------------------
    # Compact
    # ------------------------------------------------------------------

    def compact(self):
        """Compress pending rounds into summary. Does NOT modify self.messages."""
        pending_rounds = self._get_rounds_above_waterline()

        if len(pending_rounds) <= self._KEEP_RECENT:
            print("[Nothing to compact]")
            return

        compress = pending_rounds[: -self._KEEP_RECENT]

        # Build conversation text
        new_conversations = []
        for r in compress:
            idx = (r - 1) * 2 + 1
            user_msg = self.messages[idx]["content"]
            assistant_msg = self.messages[idx + 1]["content"]
            new_conversations.append(f"User: {user_msg}\nAI: {assistant_msg}")

        conversations_text = "\n\n".join(new_conversations)

        # Call model
        existing = self.summary if self.summary else "(无)"
        prompt_text = self._COMPACTION_PROMPT.format(
            existing_summary=existing,
            new_conversations=conversations_text,
        )

        try:
            summary_content, _, _ = stream_chat(
                messages=[{"role": "user", "content": prompt_text}],
                enable_thinking=self.enable_thinking,
                print_content=False,
            )
        except (httpx.HTTPError, RuntimeError) as e:
            logger.warning("Compaction failed: %s", e)
            print(f"[Warning: compaction failed: {e}]")
            return

        if summary_content:
            self.summary = summary_content
            self._waterline = compress[-1]
            logger.info(
                "Compaction done: total_rounds=%d, pinned=%s, compressed_rounds=%s, waterline=%d, summary_len=%d",
                self.total_rounds,
                sorted(self.pinned_rounds),
                compress,
                self._waterline,
                len(summary_content),
            )
            print(f"[Compressed {len(compress)} rounds into summary]")
        else:
            logger.warning("Compaction returned empty content")
            print("[Warning: compaction returned empty, summary unchanged]")

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------

    def new(self):
        """Start a new session: clear history and reset state."""
        self.session_id = self._new_session_id()
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self._reset_state()
        print(f"--- New session: {self.session_id} ---")

    def save(self):
        """Save current messages to a JSON file."""
        fpath = os.path.join(self._SESSIONS_DIR, f"{self.session_id}.json")
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
            print(f"--- Saved session {self.session_id} ---")
        except OSError as e:
            print(f"--- Save failed: {e} ---")

    def load(self):
        """Interactively select and load a saved session."""
        sessions = self._get_saved_sessions()
        if not sessions:
            print("--- No saved sessions ---")
            return
        print("--- Select a session to load ---")
        for i, s in enumerate(sessions):
            print(f"  {i + 1}. [{s['id']}] {s['time']} | {s['preview']}")
        choice = input("Enter number or session_id: ").strip()
        target_id = None
        if choice.isdigit() and 1 <= int(choice) <= len(sessions):
            target_id = sessions[int(choice) - 1]["id"]
        elif any(s["id"] == choice for s in sessions):
            target_id = choice
        if not target_id:
            print("--- Invalid selection ---")
            return
        fpath = os.path.join(self._SESSIONS_DIR, f"{target_id}.json")
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list) and all(
                "role" in m and "content" in m for m in loaded
            ):
                self.messages = loaded
                self.session_id = target_id
                self._reset_state()
                print(
                    f"--- Loaded session {self.session_id} ({len(self.messages)} messages) ---"
                )
            else:
                print("--- Invalid file format ---")
        except (OSError, json.JSONDecodeError) as e:
            print(f"--- Load failed: {e} ---")

    def list_sessions(self):
        """List all saved sessions with preview."""
        sessions = self._get_saved_sessions()
        if not sessions:
            print("--- No saved sessions ---")
        else:
            print("--- Saved sessions ---")
            for s in sessions:
                marker = " <- current" if s["id"] == self.session_id else ""
                print(f"  [{s['id']}] {s['time']} | {s['preview']}{marker}")

    def _get_saved_sessions(self) -> list[dict]:
        """Scan session directory and return metadata list."""
        sessions = []
        for f in sorted(os.listdir(self._SESSIONS_DIR)):
            if not f.endswith(".json"):
                continue
            fpath = os.path.join(self._SESSIONS_DIR, f)
            sid = f.removesuffix(".json")
            mtime = os.path.getmtime(fpath)
            try:
                with open(fpath, "r", encoding="utf-8") as fp:
                    msgs = json.load(fp)
                preview = next(
                    (m["content"][:30] for m in msgs if m["role"] == "user"), "(empty)"
                )
            except (OSError, json.JSONDecodeError):
                preview = "(unreadable)"
            sessions.append(
                {
                    "id": sid,
                    "time": time.strftime("%m-%d %H:%M", time.localtime(mtime)),
                    "preview": preview,
                }
            )
        return sessions

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def chat(self, user_input: str):
        """Send user message, apply strategy, stream response, update state."""
        try:
            messages_to_send = self._apply_strategy()
            messages_to_send.append({"role": "user", "content": user_input})
            logger.info(
                "chat: round=%d, strategy=%s, total_rounds=%d, waterline=%d, pinned=%s, pending=%d, sending=%d msgs",
                self.total_rounds + 1,
                self.strategy,
                self.total_rounds,
                self._waterline,
                sorted(self.pinned_rounds),
                self._count_pending_rounds(),
                len(messages_to_send),
            )

            print("\nAI: ", end="", flush=True)
            content, usage, finish_reason = stream_chat(
                messages=messages_to_send, enable_thinking=self.enable_thinking
            )

            if content:
                self.messages.extend(
                    [
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": content},
                    ]
                )
                self.total_rounds += 1

                if finish_reason == "length":
                    print("[Warning: response truncated (max_tokens reached)]")
                elif finish_reason == "tool_calls":
                    print("[Warning: model requested tool_calls (not implemented)]")

                if usage:
                    logger.info(
                        "chat complete: round=%d, input_tokens=%d, output_tokens=%d, sent=%d msgs",
                        self.total_rounds,
                        usage["prompt_tokens"],
                        usage["completion_tokens"],
                        len(messages_to_send),
                    )
                    print(
                        f"\n[Input: {usage['prompt_tokens']} | Output: {usage['completion_tokens']} | Round: {self.total_rounds} | Sent: {len(messages_to_send)} msgs]"
                    )
                else:
                    logger.warning(
                        "chat complete: round=%d, no usage returned", self.total_rounds
                    )
                    print(
                        f"\n[Round: {self.total_rounds} | Warning: no usage returned (stream may have been interrupted)]"
                    )
            else:
                if finish_reason == "length":
                    print("[Warning: no content generated (context window full)]")
                else:
                    print(f"[No content returned, finish_reason: {finish_reason}]")

        except (httpx.HTTPError, RuntimeError) as e:
            print(f"\n--- Request error: {e} ---")
