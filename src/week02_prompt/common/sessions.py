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
from framework.tokens import count_message_tokens

logger = logging.getLogger(__name__)


class Session:
    """Manage a single conversation session's state."""

    _SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")

    _COMPACTION_SYSTEM = """You are a precise summarization assistant. \
Your job is to produce structured progressive summaries of conversations. \
Output only the summary, no explanations."""

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

    _EXTRACT_SYSTEM = """You are a fact extraction assistant. \
Extract key facts from user messages and return them as JSON. \
Output only valid JSON, no explanations."""

    _EXTRACT_PROMPT = (
        '从以下用户消息中提取需要长期记住的关键事实, 用JSON格式返回 {{"key": "value"}}, 无则返回 {{}}\n\n'
        "用户消息: {user_input}"
    )

    _KEEP_RECENT = 2

    _TOKEN_BUDGET = 32000

    # Context window upper bound (qwen3.7-plus)
    _CONTEXT_WINDOW = 1048576
    # Cost per token (RMB, 8-fold discount): input 1.6/M, output 6.4/M
    _INPUT_COST_PER_TOKEN = 1.6e-6
    _OUTPUT_COST_PER_TOKEN = 6.4e-6

    @staticmethod
    def _new_session_id() -> str:
        return uuid.uuid4().hex[:16]

    def __init__(
        self,
        system_prompt: str = "你是一个无所不知的AI智能助手。",
        strategy: str | None = None,
        threshold: int = 10,
        token_budget: int = _TOKEN_BUDGET,
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
        self.token_budget = token_budget
        self.enable_thinking = enable_thinking
        self.total_rounds = 0
        self._waterline = (
            0  # Rounds 1.._waterline have been processed (omitted/summarized)
        )
        self.pinned_rounds: set[int] = set()
        self.summary: str = ""
        self.memory: dict[str, str] = {}
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    # ------------------------------------------------------------------
    # Strategy internals
    # ------------------------------------------------------------------

    def _reset_state(self):
        self.total_rounds = 0
        self._waterline = 0
        self.pinned_rounds.clear()
        self.summary = ""
        self.memory.clear()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

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

    def _get_pinned_messages(self) -> list[dict]:
        """Extract pinned messages from self.messages by round number."""
        result = []
        for r in sorted(self.pinned_rounds):
            idx = (r - 1) * 2 + 1
            result.extend(self.messages[idx : idx + 2])
        return result

    def _build_system_prompt(self) -> dict:
        """Build the system prompt dict, injecting memory as a context block."""
        content = self.system_prompt
        if self.memory:
            memory_block = "; ".join(f"{k}: {v}" for k, v in self.memory.items())
            content = f"{self.system_prompt}\n\n[Memory] {memory_block}"
        return {"role": "system", "content": content}

    # ------------------------------------------------------------------
    # Strategy dispatch
    # ------------------------------------------------------------------

    def _apply_strategy(self, user_input: str) -> list[dict]:
        """Build the messages list to send to the API (truncated/compressed copy)."""
        match self.strategy:
            case "sliding_window":
                return self._sliding_window(user_input)
            case "summary":
                return self._summary_compress(user_input)
            case _:
                return self._build_messages(user_input)

    def _should_trigger(self, user_input: str) -> bool:
        """Decide whether to trigger compression, logging which condition fired.

        Two independent triggers (either one fires):
        - Round count: non-pinned pending rounds exceed threshold
        - Token budget: the messages we are about to send exceed token_budget
          (guards against a few very long rounds blowing past context limits
          before the round threshold is reached)
        """
        pending = self._count_pending_rounds()
        estimated = count_message_tokens(self._build_messages(user_input))
        by_rounds = pending > self.threshold
        by_tokens = estimated > self.token_budget
        if by_rounds or by_tokens:
            logger.info(
                "Trigger check: FIRED (by_rounds=%s pending=%d/threshold=%d, "
                "by_tokens=%s estimated=%d/budget=%d)",
                by_rounds,
                pending,
                self.threshold,
                by_tokens,
                estimated,
                self.token_budget,
            )
        else:
            logger.info(
                "Trigger check: no trigger (pending=%d/threshold=%d, estimated=%d/budget=%d)",
                pending,
                self.threshold,
                estimated,
                self.token_budget,
            )
        return by_rounds or by_tokens

    def _sliding_window(self, user_input: str) -> list[dict]:
        """Sliding window: keep all above waterline until threshold, then cut.

        - Before trigger: send system + omit_notice + pinned + ALL rounds above waterline
        - On trigger: advance waterline so only _KEEP_RECENT rounds remain above it,
          then rebuild (older rounds are dropped, replaced by an omit notice)
        """
        if self._should_trigger(user_input):
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
        return self._build_messages(user_input)

    def _summary_compress(self, user_input: str) -> list[dict]:
        """Summary compression: keep all above waterline until trigger, then compact.

        - Before trigger: send system + checkpoint + pinned + ALL rounds above waterline
        - On trigger: compact() (updates summary & waterline via an API call),
          then rebuild (older rounds replaced by the checkpoint summary)
        """
        if self._should_trigger(user_input):
            logger.info(
                "Summary compress: trigger fired, calling compact() (waterline=%d, pending=%d)",
                self._waterline,
                self._count_pending_rounds(),
            )
            self.compact()
        return self._build_messages(user_input)

    def _build_messages(self, user_input: str) -> list[dict]:
        """Build the messages list to send to the API (truncated/compressed copy)."""
        result = [self._build_system_prompt()]
        pending_rounds = self._get_rounds_above_waterline()
        above_messages = []
        for r in pending_rounds:
            idx = (r - 1) * 2 + 1
            above_messages.extend(self.messages[idx : idx + 2])
        if self.strategy == "sliding_window":
            # Total omitted (cumulative)
            total_omitted = len(
                [
                    r
                    for r in range(1, self._waterline + 1)
                    if r not in self.pinned_rounds
                ]
            )
            if total_omitted > 0:
                result.append(
                    {
                        "role": "system",
                        "content": f"[{total_omitted} rounds of history omitted. Ask user if you need earlier context.]",
                    }
                )
        elif self.strategy == "summary" and self.summary:
            result.append(
                {
                    "role": "system",
                    "content": f"{self._CHECKPOINT_PREAMBLE}\n\n{self.summary}",
                }
            )
        if self.pinned_rounds:
            result.extend(self._get_pinned_messages())
        result.extend(above_messages)
        result.append({"role": "user", "content": user_input})
        return result

    # ------------------------------------------------------------------
    # Compact
    # ------------------------------------------------------------------

    def compact(self):
        """Compress pending rounds into summary. Does NOT modify self.messages."""
        pending_rounds = self._get_rounds_above_waterline()

        if len(pending_rounds) <= self._KEEP_RECENT:
            logger.info(
                "Compact skipped: pending=%d <= keep_recent=%d (nothing to compress)",
                len(pending_rounds),
                self._KEEP_RECENT,
            )
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
                messages=[
                    {"role": "system", "content": self._COMPACTION_SYSTEM},
                    {"role": "user", "content": prompt_text},
                ],
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
        logger.info(
            "Pinned round %d, pinned=%s",
            self.total_rounds,
            sorted(self.pinned_rounds),
        )
        print(f"[Pinned round {self.total_rounds}]")

    def unpin(self, round_str: str):
        """Unpin a round by its round number."""
        try:
            round_num = int(round_str)
        except (TypeError, ValueError):
            print("[Invalid round number]")
            return
        if round_num not in self.pinned_rounds:
            print("[Not pinned]")
            return
        self.pinned_rounds.discard(round_num)
        logger.info(
            "Unpinned round %d, pinned=%s", round_num, sorted(self.pinned_rounds)
        )
        print(f"[Unpinned round {round_num}]")

    def pins(self):
        """Display all pinned messages."""
        if not self.pinned_rounds:
            print("[No messages have been pinned.]")
            return
        print(f"[{len(self.pinned_rounds)} pinned round(s)]")
        for r in sorted(self.pinned_rounds):
            idx = (r - 1) * 2 + 1
            user_msg = self.messages[idx]["content"][:80]
            ai_msg = self.messages[idx + 1]["content"][:80]
            print(f"  Round {r}:")
            print(f"    User: {user_msg}")
            print(f"    AI:   {ai_msg}")

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def remember(self, user_input: str):
        """Store a key-value fact in memory. Usage: /remember key value"""
        parts = user_input.split(None, 1)
        if len(parts) < 2:
            print("[Usage: /remember key value]")
            return
        key, value = parts[0], parts[1]
        if key in self.memory:
            print(f"[Overwriting '{key}': '{self.memory[key]}' -> '{value}']")
        self.memory[key] = value
        logger.info("Remembered: %s = %s, memory=%s", key, value, self.memory)
        print(f"[Remembered: {key} = {value}]")

    def forget(self, key: str):
        """Remove a key from memory."""
        if key not in self.memory:
            print(f"[Key '{key}' not found in memory]")
            return
        del self.memory[key]
        logger.info("Forgot: %s, memory=%s", key, self.memory)
        print(f"[Forgotten: {key}]")

    def view_memory(self):
        """Display all memory keys and values."""
        if not self.memory:
            print("[Memory is empty]")
            return
        print(f"[{len(self.memory)} key(s) in memory]")
        for key, value in self.memory.items():
            print(f"  {key}: {value}")

    def _extract_memory(self, user_input: str):
        """Auto-extract key facts from user input via model call."""
        try:
            raw, _, _ = stream_chat(
                messages=[
                    {"role": "system", "content": self._EXTRACT_SYSTEM},
                    {
                        "role": "user",
                        "content": self._EXTRACT_PROMPT.format(user_input=user_input),
                    },
                ],
                enable_thinking=self.enable_thinking,
                print_content=False,
            )
        except (httpx.HTTPError, RuntimeError) as e:
            logger.warning("Auto-extract key facts from user input failed: %s", e)
            print(f"[Warning: auto-extract key facts from input failed: {e}]")
            return

        if not raw:
            return
        try:
            extracted = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(
                "Auto-extract key facts from input failed: could not parse raw response: %s]",
                raw[:100],
            )
            print("[Warning: could not parse extracted memory]")
            return
        if extracted:
            self.memory.update(extracted)
            logger.info("Memory extracted: %s", extracted)
            print(
                f"[Remembered: {', '.join(f'{k} = {v}' for k, v in extracted.items())}]"
            )
        else:
            logger.info("Memory extraction returned no facts")

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------

    def new(self):
        """Start a new session: clear history and reset state."""
        self._reset_state()
        self.session_id = self._new_session_id()
        self.messages = [self._build_system_prompt()]
        logger.info("New session started: %s (state reset)", self.session_id)
        print(f"--- New session: {self.session_id} ---")

    def save(self):
        """Save current messages to a JSON file."""
        fpath = os.path.join(self._SESSIONS_DIR, f"{self.session_id}.json")
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
            logger.info(
                "Saved session %s (%d messages)", self.session_id, len(self.messages)
            )
            print(f"--- Saved session {self.session_id} ---")
        except OSError as e:
            logger.warning("Save failed for %s: %s", self.session_id, e)
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
                logger.info(
                    "Loaded session %s (%d messages, state reset)",
                    self.session_id,
                    len(self.messages),
                )
                print(
                    f"--- Loaded session {self.session_id} ({len(self.messages)} messages) ---"
                )
            else:
                logger.warning("Load failed: invalid file format for %s", target_id)
                print("--- Invalid file format ---")
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Load failed for %s: %s", target_id, e)
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
        # Keyword-based trigger for auto memory extraction.
        # TODO: keyword matching is brittle; consider a lightweight classifier later.
        if "记住" in user_input or "remember" in user_input.lower():
            logger.info("Memory extraction triggered by keyword in user input")
            self._extract_memory(user_input)

        try:
            messages_to_send = self._apply_strategy(user_input)
            estimated_tokens = count_message_tokens(messages_to_send)
            logger.info(
                "chat: round=%d, strategy=%s, total_rounds=%d, waterline=%d, pinned=%s, pending=%d, sending=%d msgs, estimated_input_tokens=%d",
                self.total_rounds + 1,
                self.strategy,
                self.total_rounds,
                self._waterline,
                sorted(self.pinned_rounds),
                self._count_pending_rounds(),
                len(messages_to_send),
                estimated_tokens,
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
                    logger.warning(
                        "Response truncated at round %d (max_tokens reached)",
                        self.total_rounds,
                    )
                    print("[Warning: response truncated (max_tokens reached)]")
                elif finish_reason == "tool_calls":
                    logger.warning(
                        "Model requested tool_calls at round %d (not implemented)",
                        self.total_rounds,
                    )
                    print("[Warning: model requested tool_calls (not implemented)]")

                if usage:
                    self.total_input_tokens += usage["prompt_tokens"]
                    self.total_output_tokens += usage["completion_tokens"]
                    total_tokens = self.total_input_tokens + self.total_output_tokens
                    cost = (
                        self.total_input_tokens * self._INPUT_COST_PER_TOKEN
                        + self.total_output_tokens * self._OUTPUT_COST_PER_TOKEN
                    )
                    logger.info(
                        "chat complete: round=%d, input_tokens=%d, output_tokens=%d, sent=%d msgs",
                        self.total_rounds,
                        usage["prompt_tokens"],
                        usage["completion_tokens"],
                        len(messages_to_send),
                    )
                    # Compare our local token estimate against the API's actual count
                    actual_input = usage["prompt_tokens"]
                    diff = estimated_tokens - actual_input
                    pct = (diff / actual_input * 100) if actual_input else 0.0
                    logger.info(
                        "token check: estimated=%d, actual=%d, diff=%+d (%.1f%%)",
                        estimated_tokens,
                        actual_input,
                        diff,
                        pct,
                    )
                    print(
                        f"\n[Token Usage: {total_tokens} / {self._CONTEXT_WINDOW} | "
                        f"Input: {self.total_input_tokens} | "
                        f"Output: {self.total_output_tokens} | "
                        f"Cost: ¥{cost:.4f} | Round: {self.total_rounds}]"
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
