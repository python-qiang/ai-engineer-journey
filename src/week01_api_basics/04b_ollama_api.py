"""
第1周 - 第4节 - 任务2: 用 Python 调用 Ollama 本地 API

=== 本任务完成后你需要掌握的 ===

1. Ollama 的 API 与云端 API (百炼) 格式完全一致:
   - 同样的 URL 结构: /v1/chat/completions
   - 同样的请求体: model, messages, temperature, stream
   - 同样的响应体: choices[0].message.content, usage

2. 切换云端/本地只需改两个东西:
   - URL: localhost:11434 vs 云端业务空间专属域名
   - model: "qwen3:4b" vs "qwen3.6-flash-2026-04-16"
   - 其余代码完全不用改

3. 本地模型的特点:
   - 免费无限调用, 不消耗 API 额度
   - CPU 推理速度慢(但学习够用)
   - 不需要网络, 离线可用
   - 适合调试 prompt, 验证逻辑

=== 本任务不需要关心的 ===

- Ollama 内部如何加载权重 → 了解即可
- GPU 加速配置 → 你没有 GPU, 跳过
- 模型量化 (GGUF/Q4/Q8) → 了解即可

=== 练习 ===

1. 运行此文件, 验证本地 Ollama 返回结果的 JSON 结构与云端一致
2. 复用 01c_chat_function.py 的 chat(), 只改 URL 和 model, 验证通用性
3. 试试 stream_chat() 调本地模型, 观察 CPU 推理的逐字速度
4. 对比同一个问题在本地 vs 云端的回答质量和速度差异
"""

import json
import time

import httpx

from framework.consts import LOCAL_MODEL, ollama_base_url


def stream_chat(
    message: str,
    url: str = ollama_base_url,
    model: str = LOCAL_MODEL,
    temperature: float = 0.7,
    system_prompt: str = "你是一个助手, 回答请保持简洁和专业。",
    stream: bool = True,
    include_usage: bool = True,
    enable_thinking: bool = False,
    print_chunks: bool = False,
) -> dict:
    """调用本地 Ollama API。stream=True 时逐字打印, stream=False 时一次性返回。

    Args:
        message: 用户问题
        url: API 地址
        model: 模型名称
        temperature: 随机性
        system_prompt: 系统提示词
        stream: 是否流式输出
        include_usage: 是否返回 token 统计 (仅 stream=True 时需要)
        enable_thinking: 是否开启深度思考 (会输出 reasoning_content)
        print_chunks: 是否打印原始 chunk JSON (调试用)
    Returns:
        回复内容
    """
    headers = {"Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "temperature": temperature,
        "stream": stream,
        "enable_thinking": enable_thinking,
    }

    if stream and include_usage:
        payload["stream_options"] = {"include_usage": True}

    start_time = time.time()
    first_token_time = None
    full_content = ""
    reasoning_done = False
    reasoning_content = ""
    usage = None

    if not stream:
        # 非流式: 一次性返回
        response = httpx.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            raise RuntimeError(
                f"请求失败: HTTP {response.status_code}\n{response.text}"
            )
        data = response.json()
        first_token_time = time.time()
        msg = data["choices"][0]["message"]
        full_content = msg.get("content", "")
        reasoning_content = msg.get("reasoning_content", "")
        usage = data.get("usage")
        print(full_content)
    else:
        with httpx.stream(
            "POST",
            url,
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


if __name__ == "__main__":
    question = "Python的GIL是什么? 用50字回答。"

    # Case 1: 流式, 无思考
    print("=== Case 1: stream=True, thinking=False ===")
    result = stream_chat(question)
    print(
        f"输出: {len(result['content'])} 字符 | {result['usage']['total_tokens']} tokens | {result['total_time']:.2f}s"
    )
    print()

    # Case 2: 流式, 有思考
    print("=== Case 2: stream=True, thinking=True ===")
    result = stream_chat(question, enable_thinking=True)
    print(
        f"输出: {len(result['content'])} 字符 | 思维链: {len(result['reasoning_content'])} 字符 | {result['usage']['total_tokens']} tokens | {result['total_time']:.2f}s"
    )
    print()

    # Case 3: 非流式, 无思考
    print("=== Case 3: stream=False, thinking=False ===")
    result = stream_chat(question, stream=False)
    print(
        f"输出: {len(result['content'])} 字符 | {result['usage']['total_tokens']} tokens | {result['total_time']:.2f}s"
    )
    print()

    # Case 4: 非流式, 有思考 (可以看到 reasoning_content)
    print("=== Case 4: stream=False, thinking=True ===")
    result = stream_chat(question, stream=False, enable_thinking=True)
    print(
        f"输出: {len(result['content'])} 字符 | {result['usage']['total_tokens']} tokens | {result['total_time']:.2f}s"
    )
    if result["reasoning_content"]:
        print(
            f"思维链 ({len(result['reasoning_content'])} 字符): {result['reasoning_content'][:200]}..."
        )
    else:
        print("思维链: 无 (可能 Ollama 不返回此字段)")
    print()
