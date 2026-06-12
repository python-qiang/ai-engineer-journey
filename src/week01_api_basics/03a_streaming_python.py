"""
第1周 - 第3节 - 任务1: 用 Python httpx 实现流式调用 (SSE)

=== 本任务完成后你需要掌握的 ===

1. SSE (Server-Sent Events) 协议的数据格式:
   - 每行以 "data: " 开头, 后面跟一个 JSON 对象
   - 最后一行是 "data: [DONE]" 表示结束
   - 每个 chunk 之间用空行分隔

2. 流式调用的关键区别:
   - 请求时加 "stream": true
   - 响应不再是一次性返回完整 JSON, 而是一行一行推送 chunk
   - 每个 chunk 里的内容在 choices[0].delta.content (注意是 delta 不是 message)

3. 为什么要流式:
   - 用户体验: 不用等模型全部生成完才看到结果
   - 首字延迟 (TTFT): 从请求发出到看到第一个字的时间大幅缩短
   - 防止触发服务端超时

4. httpx 流式响应的用法:
   - 用 with httpx.stream() 上下文管理器
   - 用 response.iter_lines() 逐行读取

5. include_usage 的影响:
   - True: finish_reason=stop 之后还有一个 choices=[] 的 chunk 带 usage, 最后才是 [DONE]
   - False: finish_reason=stop 就是最后一个有意义的 chunk, 然后直接 [DONE]

=== 本任务不需要关心的 ===

- WebSocket 双向通信 → 第17周 (FastAPI)
- 前端如何消费 SSE → 第18周 (前端)
- 流式中的错误处理/重连 → 了解即可

=== 练习 ===

1. 运行此文件, 观察终端逐字打印的效果
2. 调用时传 include_usage=False, 对比 chunk 结构的差异
3. 调用时传 enable_thinking=True, 观察 reasoning_content 的流式输出
4. 对比流式 vs 非流式 (01a_http_call.py) 的用户体验差异
"""

import os
import json
import time
import httpx
from framework.consts import beijing_openai_base_http_api_url

API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("BEIJING_API_KEY 未设置")


def stream_chat(
    message: str,
    model: str = "qwen3.6-flash-2026-04-16",
    temperature: float = 0.7,
    system_prompt: str = "你是一个助手, 回答请保持简洁和专业。",
    include_usage: bool = True,
    enable_thinking: bool = False,
    print_chunks: bool = False,
) -> dict:
    """流式调用大模型 API, 逐字打印回复。

    Args:
        message: 用户问题
        model: 模型名称
        temperature: 随机性
        system_prompt: 系统提示词
        include_usage: 是否在最后一个 chunk 中返回 token 统计
        enable_thinking: 是否开启深度思考 (会输出 reasoning_content)
        print_chunks: 是否打印原始 chunk JSON (调试用)

    Returns:
        {
            "content": str,           # 完整回复
            "reasoning_content": str, # 思维链 (enable_thinking=True 时)
            "usage": dict or None,    # token 统计 (include_usage=True 时)
            "ttft": float,            # 首字延迟 (秒)
            "total_time": float,      # 总耗时 (秒)
        }
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "temperature": temperature,
        "stream": True,
        "enable_thinking": enable_thinking,
    }

    if include_usage:
        payload["stream_options"] = {"include_usage": True}

    start_time = time.time()
    first_token_time = None
    full_content = ""
    reasoning_done = False
    reasoning_content = ""
    usage = None

    with httpx.stream(
        "POST",
        beijing_openai_base_http_api_url,
        headers=headers,
        json=payload,
        timeout=120,
    ) as response:
        if response.status_code != 200:
            error = response.read().decode()
            raise RuntimeError(f"请求失败: HTTP {response.status_code}\n{error}")

        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue

            data_str = line[6:]  # 去掉 "data: " 前缀

            if data_str == "[DONE]":
                break

            chunk = json.loads(data_str)

            if print_chunks:
                print(f"[chunk] {data_str}")

            # include_usage=True 时, 最后一个 chunk: choices=[], 只有 usage
            if not chunk["choices"]:
                usage = chunk.get("usage")
                continue

            choice = chunk["choices"][0]
            delta = choice.get("delta", {})

            # 思维链内容 (enable_thinking=True 时)
            reasoning = delta.get("reasoning_content", "")
            if reasoning:
                if first_token_time is None:
                    first_token_time = time.time()
                print(reasoning, end="", flush=True)
                reasoning_content += reasoning

            # 正文内容
            content = delta.get("content", "")
            if content:
                if not reasoning_done and reasoning_content:
                    print("\n\n--- 思考完毕，开始回答 ---\n")
                    reasoning_done = True
                if first_token_time is None:
                    first_token_time = time.time()
                print(content, end="", flush=True)
                full_content += content

    total_time = time.time() - start_time
    ttft = (first_token_time - start_time) if first_token_time else total_time

    print()  # 换行

    return {
        "content": full_content,
        "reasoning_content": reasoning_content,
        "usage": usage,
        "ttft": ttft,
        "total_time": total_time,
    }


# === 演示 ===

if __name__ == "__main__":
    print("=" * 60)
    print("流式调用演示")
    print("=" * 60)
    print()

    result = stream_chat(
        model="qwen3.6-plus",
        message="用100字介绍什么是SSE (Server-Sent Events)。",
        include_usage=True,
        enable_thinking=True,
    )

    print()
    print("--- 统计 ---")
    print(f"TTFT (首字延迟): {result['ttft']:.2f}s")
    print(f"总耗时: {result['total_time']:.2f}s")
    print(f"输出长度: {len(result['content'])} 字符")
    if result["usage"]:
        u = result["usage"]
        print(
            f"Token 消耗: 输入 {u['prompt_tokens']} + 输出 {u['completion_tokens']} = {u['total_tokens']}"
        )
    if result["reasoning_content"]:
        print(f"思维链长度: {len(result['reasoning_content'])} 字符")
