"""
week02_prompt/common/sessions.py - Session state management

Encapsulates all session-related state and commands.
CLI task files can call these directly without reimplementing.
"""

import json
import os
import time
import uuid

import httpx

from framework.chat import stream_chat


class Session:
    """Manage a single conversation session's state."""

    SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")

    @staticmethod
    def _new_session_id() -> str:
        """Generate a short UUID (16 hex chars) for human readability."""
        return uuid.uuid4().hex[:16]

    def __init__(
        self,
        system_prompt: str = "你是一个无所不知的AI智能助手。",
        strategy: str | None = None,
        window_size: int = 5,
        summary_threshold: int = 8,
    ):
        """Initialize a new session.

        Args:
            system_prompt: The system message always at the front.
            strategy: Context management strategy. None/"sliding_window"/"summary".
            window_size: For sliding_window, keep last N rounds.
            summary_threshold: For summary, trigger compression after N rounds.
        """
        os.makedirs(self.SESSIONS_DIR, exist_ok=True)
        self.system_prompt = system_prompt
        self.session_id = self._new_session_id()
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]
        self.strategy = strategy
        self.window_size = window_size
        self.pinned_rounds: set[int] = set()
        self.pinned_messages: list[dict] = []
        self.summary_threshold = summary_threshold
        self.summary: str = ""

    @property
    def rounds(self) -> int:
        """Current number of conversation rounds (user+assistant pairs)."""
        return (len(self.messages) - 1) // 2

    # ------------------------------------------------------------------
    # Strategy methods
    # ------------------------------------------------------------------

    def _reset_state(self):
        """Internal: reset pinned messages and summary."""
        self.pinned_rounds.clear()
        self.pinned_messages.clear()
        self.summary = ""

    def _apply_strategy(self) -> list[dict]:
        """Return the messages list to actually send to the API.

        self.messages always keeps full history.
        This method returns a truncated/compressed version based on strategy.
        """
        match self.strategy:
            case "sliding_window":
                return self._sliding_window()
            case "summary":
                return self._summary_compress()
            case _:
                return list(self.messages)

    def _sliding_window(self) -> list[dict]:
        """Apply sliding window: system + [omit notice] + pinned + recent N rounds.

        Pinned rounds are excluded from the N count (they're always kept).
        Called on completed history (before current user message is appended).
        """
        if self.rounds <= self.window_size:
            return list(self.messages)

        # Collect non-pinned completed rounds
        non_pinned = []
        for r in range(1, self.rounds + 1):
            if r not in self.pinned_rounds:
                idx = (r - 1) * 2 + 1  # round 1 -> messages[1:3]
                non_pinned.extend(self.messages[idx : idx + 2])

        # Take last N rounds from non-pinned
        recent = non_pinned[-(self.window_size * 2) :]

        # Build result
        result = [self.messages[0]]

        omitted = (len(non_pinned) - len(recent)) // 2
        if omitted > 0:
            result.append(
                {
                    "role": "system",
                    "content": f"[{omitted} rounds of history omitted. Ask user if you need earlier context.]",
                }
            )

        if self.pinned_messages:
            result.extend(self.pinned_messages)

        result.extend(recent)
        return result

    def _summary_compress(self) -> list[dict]:
        """Apply summary compression. (To be implemented in 03b.)"""
        # Placeholder: fall back to full messages for now
        return list(self.messages)

    # ------------------------------------------------------------------
    # Pin methods
    # ------------------------------------------------------------------

    def pin(self):
        """Pin the last round (user+assistant) so it survives truncation."""
        if self.rounds == 0:
            print("[Nothing to pin]")
            return
        if self.rounds in self.pinned_rounds:
            print("[Already pinned]")
            return
        self.pinned_rounds.add(self.rounds)
        self.pinned_messages.extend(self.messages[-2:])
        print(f"[Pinned round {self.rounds}]")

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
    # Session persistence methods
    # ------------------------------------------------------------------

    def new(self):
        """Clear conversation, reset all state, generate new session_id."""
        self.session_id = self._new_session_id()
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self._reset_state()
        print(f"--- New session: {self.session_id} ---")

    def save(self):
        """Save current messages to a JSON file named by session_id."""
        fpath = os.path.join(self.SESSIONS_DIR, f"{self.session_id}.json")
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
        fpath = os.path.join(self.SESSIONS_DIR, f"{target_id}.json")
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
        """Internal: scan session directory and return metadata list."""
        sessions = []
        for f in sorted(os.listdir(self.SESSIONS_DIR)):
            if not f.endswith(".json"):
                continue
            fpath = os.path.join(self.SESSIONS_DIR, f)
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
    # Chat method
    # ------------------------------------------------------------------

    def chat(self, user_input: str):
        """Send user message, apply strategy, stream response, update state."""
        try:
            # 1. Build messages to send (strategy applied on existing history)
            messages_to_send = self._apply_strategy()
            messages_to_send.append({"role": "user", "content": user_input})

            # 2. Call API
            print("\nAI: ", end="", flush=True)
            content, usage, finish_reason = stream_chat(
                messages=messages_to_send, enable_thinking=True
            )

            # 3. On success, append to full history
            if content:
                self.messages.extend(
                    [
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": content},
                    ]
                )

                if finish_reason == "length":
                    print("[Warning: response truncated (max_tokens reached)]")
                elif finish_reason == "tool_calls":
                    print("[Warning: model requested tool_calls (not implemented)]")

                if usage:
                    print(
                        f"\n[Input: {usage['prompt_tokens']} | Output: {usage['completion_tokens']} | Rounds: {self.rounds} | Sent: {len(messages_to_send)} msgs]"
                    )
                else:
                    print(
                        f"\n[Rounds: {self.rounds} | Warning: no usage returned (stream may have been interrupted)]"
                    )
            else:
                if finish_reason == "length":
                    print("[Warning: no content generated (context window full)]")
                else:
                    print(f"[No content returned, finish_reason: {finish_reason}]")

        except (httpx.HTTPError, RuntimeError) as e:
            print(f"\n--- Request error: {e} ---")
