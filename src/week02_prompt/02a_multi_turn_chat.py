"""
第2周 - 第2节 - 多轮对话的实现原理

=== 本任务完成后你需要掌握的 ===

1. 大模型 API 是无状态的:
   - 每次请求都是独立的, 模型不记得上一轮说了什么
   - 多轮对话完全靠你在每次请求中把历史消息全部带上
   - messages 列表就是"记忆", 你管理它就是管理对话

2. Token 消耗是累加的:
   - 每轮对话的 input tokens = system + 所有历史 + 本轮问题
   - 聊越久越贵, 因为每次都要把完整历史发给模型
   - 这就是为什么需要上下文窗口管理(Section 3 学)

3. 会话管理的基本模式:
   - 用一个 list 存 messages, 每轮追加 user 和 assistant
   - "新建对话" = 清空 list(只保留 system prompt)
   - 持久化 = 把 messages list 序列化存到文件

4. finish_reason 的含义:
   - stop: 正常结束
   - length: 达到 max_tokens 限制或 context window 已满
   - tool_calls: 模型请求调用工具(第4周学)
   - null: 生成未结束(流式中间 chunk)

=== 本任务不需要关心的 ===

- 上下文窗口截断/压缩策略 -> Section 3
- 数据库持久化 -> 了解即可, 本节用文件存储
- Web 框架集成 -> 第17周 FastAPI

=== 练习(在一个文件中完成) ===

任务1: 命令行多轮对话
  - while True + match-case 循环
  - 维护 messages 列表, 每轮追加 user 和 assistant
  - 流式输出, 根据 finish_reason 给出友好提示

任务2: Token 消耗追踪
  - 每轮打印: 本轮生成 tokens / 累计生成 tokens / 对话轮数
  - 观察 prompt_tokens 随轮数线性增长(每次都带完整历史)

任务3: Context Window 压力测试
  - 不设 max_completion_tokens, 让模型尽情输出
  - 连续问长回答问题, 撑大 messages 历史
  - 观察超过 32K tokens 后的表现(报错? 截断?)

任务4: 会话管理命令
  - /new: 清空历史(保留 system prompt) + 重置 token 统计
  - /save: messages 序列化为 JSON 文件(时间戳命名)
  - /load: 从 JSON 文件恢复对话历史(带格式校验)

=== 踩坑记录 ===

- 每个 chunk 都带 "usage": null, 用 "usage" in chunk 会误判
  正确写法: not chunk.get("choices") and chunk.get("usage")
- qwen3.7-plus 默认开启思考模式, 不处理 reasoning_content 会导致
  content 为空. 多轮对话建议关闭: "enable_thinking": False
- max_completion_tokens 限制的是输出长度, 不是 context window
  要撑爆窗口应该不设此参数, 让历史自然累积
"""

import json
import os
import time
import uuid

import httpx

from framework.consts import DEFAULT_MODEL, beijing_openai_base_http_api_url

API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("BEIJING_API_KEY 未设置")


def chat(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    max_tokens: int | None = None,
) -> tuple[str, dict | None]:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
        # "enable_thinking": False,
    }

    if max_tokens is not None:
        payload["max_completion_tokens"] = max_tokens

    answer_content = ""
    usage_info = None
    finish_reason = None

    with httpx.stream(
        "POST",
        beijing_openai_base_http_api_url,
        headers=headers,
        json=payload,
        timeout=httpx.Timeout(120.0, connect=10.0),  # 区分连接超时和读取超时
    ) as response:
        if response.status_code != 200:
            error = response.read().decode()
            raise RuntimeError(f"请求失败: HTTP {response.status_code}\n{error}")

        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue

            # 更安全的去除前缀方式 (兼容 "data: " 或 "data:")
            data_str = line.removeprefix("data:").strip()

            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                # 忽略无法解析的残缺行，防止程序崩溃
                continue

            # 处理 usage 信息 (最后一个 chunk: choices=[], usage 有值)
            if not chunk.get("choices") and chunk.get("usage"):
                usage_info = chunk["usage"]
                continue

            # 处理正文内容
            choices = chunk.get("choices", [])
            if not choices:
                continue

            choice = choices[0]
            delta = choice.get("delta", {})
            content = delta.get("content", "")
            if content:
                print(content, end="", flush=True)
                answer_content += content

            # 捕获 finish_reason
            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]

    print()  # 换行

    return answer_content, usage_info, finish_reason


SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)


def new_session_id() -> str:
    """生成一个短 session_id (UUID 前8位, 方便人类阅读)."""
    return uuid.uuid4().hex[:8]


def session_file_path(session_id: str) -> str:
    """根据 session_id 返回对应的文件路径."""
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def list_sessions() -> list[dict]:
    """列出所有已保存的 session, 返回 [{id, file, mtime, preview}, ...]."""
    sessions = []
    for f in sorted(os.listdir(SESSIONS_DIR)):
        if not f.endswith(".json"):
            continue
        fpath = os.path.join(SESSIONS_DIR, f)
        sid = f.removesuffix(".json")
        mtime = os.path.getmtime(fpath)
        # 读取第一条 user 消息作为预览
        try:
            with open(fpath, "r", encoding="utf-8") as fp:
                msgs = json.load(fp)
            preview = next(
                (m["content"][:30] for m in msgs if m["role"] == "user"), "(空对话)"
            )
        except (OSError, json.JSONDecodeError):
            preview = "(无法读取)"
        sessions.append({
            "id": sid,
            "time": time.strftime("%m-%d %H:%M", time.localtime(mtime)),
            "preview": preview,
        })
    return sessions


if __name__ == "__main__":
    total_completion_tokens = 0
    total_prompt_tokens = 0
    session_id = new_session_id()
    messages = [{"role": "system", "content": "你是一个无所不知的AI智能助手。"}]

    print("=== 欢迎使用多轮对话 CLI ===")
    print(f"当前会话: {session_id}")
    print("指令: /new (新建), /save (保存), /load (加载), /list (列出会话), quit/exit (退出)")

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue

        match user_input:
            case "quit" | "exit":
                print("对话结束。")
                break

            case "/new":
                session_id = new_session_id()
                messages = messages[:1]
                total_completion_tokens = 0
                total_prompt_tokens = 0
                print(f"--- 新会话: {session_id} ---")

            case "/save":
                fpath = session_file_path(session_id)
                try:
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    print(f"--- 已保存会话 {session_id} ---")
                except OSError as e:
                    print(f"--- 保存失败: {e} ---")

            case "/list":
                sessions = list_sessions()
                if not sessions:
                    print("--- 暂无已保存的会话 ---")
                else:
                    print("--- 已保存的会话 ---")
                    for s in sessions:
                        marker = " ← 当前" if s["id"] == session_id else ""
                        print(f"  [{s['id']}] {s['time']} | {s['preview']}{marker}")

            case "/load":
                sessions = list_sessions()
                if not sessions:
                    print("--- 暂无已保存的会话 ---")
                    continue
                print("--- 选择要加载的会话 ---")
                for i, s in enumerate(sessions):
                    print(f"  {i + 1}. [{s['id']}] {s['time']} | {s['preview']}")
                choice = input("输入编号或 session_id: ").strip()
                # 支持输入编号或 id
                target_id = None
                if choice.isdigit() and 1 <= int(choice) <= len(sessions):
                    target_id = sessions[int(choice) - 1]["id"]
                elif any(s["id"] == choice for s in sessions):
                    target_id = choice
                if not target_id:
                    print("--- 无效选择 ---")
                    continue
                fpath = session_file_path(target_id)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, list) and all(
                        "role" in m and "content" in m for m in loaded
                    ):
                        messages = loaded
                        session_id = target_id
                        total_completion_tokens = 0
                        total_prompt_tokens = 0
                        print(f"--- 已加载会话 {session_id} ({len(messages)} 条消息) ---")
                    else:
                        print("--- 文件格式不正确 ---")
                except (OSError, json.JSONDecodeError) as e:
                    print(f"--- 加载失败: {e} ---")

            case _:
                messages.append({"role": "user", "content": user_input})
                try:
                    print("\nAI: ", end="", flush=True)
                    answer_content, usage, finish_reason = chat(messages)

                    if answer_content:
                        messages.append(
                            {"role": "assistant", "content": answer_content}
                        )

                        # finish_reason 友好提示
                        if finish_reason == "length":
                            print("[⚠️ 回复被截断: 达到 max_tokens 限制]")
                        elif finish_reason == "tool_calls":
                            print("[⚠️ 模型请求调用工具 (本程序未实现 tool_calls)]")

                        # 准确统计 Token
                        if usage:
                            comp_tokens = usage.get("completion_tokens", 0)
                            prompt_tokens = usage.get("prompt_tokens", 0)
                            total_completion_tokens += comp_tokens
                            total_prompt_tokens += prompt_tokens

                            print(
                                f"\n[本轮生成: {comp_tokens} | 累计生成: {total_completion_tokens} | 对话轮数: {(len(messages) - 1) // 2}]"
                            )
                        else:
                            print(f"\n[对话轮数: {(len(messages) - 1) // 2}]")
                    else:
                        if finish_reason == "length":
                            print("[⚠️ 未生成内容: input tokens 已占满 context window, 无空间生成回复]")
                        else:
                            print(f"[AI 未返回有效内容, finish_reason: {finish_reason}]")

                except (httpx.HTTPError, RuntimeError) as e:
                    print(f"\n--- 请求异常: {e} ---")
                    if messages[-1]["role"] == "user":
                        messages.pop()
