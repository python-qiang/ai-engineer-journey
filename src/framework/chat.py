"""
framework/chat.py - 统一的流式对话函数

所有练习文件复用此函数, 不再各自重写流式逻辑.
"""

import json
import os

import httpx

from framework.consts import DEFAULT_MODEL, beijing_openai_base_http_api_url

API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("BEIJING_API_KEY 未设置, 请确认 direnv 已加载")


def stream_chat(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    url: str = beijing_openai_base_http_api_url,
    max_tokens: int | None = None,
    enable_thinking: bool = False,
    show_thinking: bool = False,
    print_content: bool = True,
) -> dict:
    """流式调用大模型 API.

    Args:
        messages: 完整的 messages 数组 (调用方自己构造)
        model: 模型名称
        url: API 地址 (云端或本地 Ollama)
        max_tokens: 最大输出 token 数 (None=不限制)
        enable_thinking: 是否开启思考模式
        show_thinking: 是否打印思考过程
        print_content: 是否打印回复内容到终端

    Returns:
        {
            "content": str,          # 完整回复
            "usage": dict | None,    # token 统计
            "finish_reason": str | None,  # stop/length/tool_calls
        }
    """
    headers = {"Content-Type": "application/json"}
    if "dashscope" in url:
        headers["Authorization"] = f"Bearer {API_KEY}"

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
        "enable_thinking": enable_thinking,
    }

    if max_tokens is not None:
        payload["max_completion_tokens"] = max_tokens

    full_content = ""
    reasoning_content = ""
    reasoning_done = False
    usage_info = None
    finish_reason = None

    with httpx.stream(
        "POST", url, headers=headers, json=payload, timeout=httpx.Timeout(120.0, connect=10.0)
    ) as resp:
        if resp.status_code != 200:
            error = resp.read().decode()
            raise RuntimeError(f"HTTP {resp.status_code}: {error[:200]}")

        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue

            data_str = line[6:]

            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            # usage chunk: choices 为空且 usage 有值
            if not chunk.get("choices") and chunk.get("usage"):
                usage_info = chunk["usage"]
                continue

            choices = chunk.get("choices", [])
            if not choices:
                continue

            choice = choices[0]
            delta = choice.get("delta", {})

            # 思考内容
            reasoning = delta.get("reasoning_content", "")
            if reasoning:
                reasoning_content += reasoning
                if show_thinking and print_content:
                    print(reasoning, end="", flush=True)

            # 正文内容
            content = delta.get("content", "")
            if content:
                if not reasoning_done and reasoning_content and show_thinking and print_content:
                    print("\n--- 思考完毕 ---\n")
                    reasoning_done = True
                full_content += content
                if print_content:
                    print(content, end="", flush=True)

            # finish_reason
            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]

    if print_content:
        print()  # 换行

    return {
        "content": full_content,
        "usage": usage_info,
        "finish_reason": finish_reason,
    }
