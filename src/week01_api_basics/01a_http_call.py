"""
第1周 - 第1节 - 任务1&3: 不用任何SDK, 纯HTTP调用大模型API

=== 本任务完成后你需要掌握的 ===

1. API 调用的基本结构:
   - HTTP POST 请求 + Bearer Token 认证
   - 请求体是 JSON, 响应体也是 JSON

2. 请求体(payload)中本任务只需关心这几个字段:
   - model: 模型名称 (如 "qwen3.6-flash-2026-04-16")
   - messages: 消息数组, 本任务只用 system + user 两种角色
   - temperature: 控制随机性 (0=确定性高, 1.5=创意高)

3. 响应体中本任务只需关心:
   - choices[0].message.content: 模型的回复文本
   - choices[0].message.reasoning_content: 思维链 (部分模型有)
   - usage.prompt_tokens / completion_tokens / total_tokens: Token消耗

4. 错误处理:
   - HTTP 200 = 成功, 其他状态码 = 失败
   - 能看懂常见错误: 401(Key错误), 429(限流), 400(参数错误)

=== 本任务不需要关心的 (后面会学) ===

- stream 参数 (流式输出) → 任务3
- tools / tool_choice 参数 (函数调用) → 第4周
- max_tokens / top_p / stop 等高级参数 → 任务5
- assistant / tool 角色的 message → 第2周(多轮对话) / 第4周(函数调用)
- response_format (结构化输出) → 第3周
- seed 参数 (可复现输出) → 了解即可, 不是重点

=== 练习 ===

1. 运行此文件, 观察完整的请求和响应结构
2. 修改 user message, 问不同的问题
3. 修改 temperature (0 vs 1.5), 各跑5次, 观察输出稳定性差异
4. 故意改错 API Key, 观察错误响应的 HTTP 状态码和错误信息
5. 换一个 model 名称 (如 qwen-turbo), 观察回答风格和 Token 消耗的差异
"""

import os

import httpx

# from framework.consts import frankfurt_openai_base_http_api_url
from framework.consts import beijing_openai_base_http_api_url

# API_KEY = os.environ.get("FRANKFURT_API_KEY")
API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY 未设置, 请确认 direnv 已加载")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": "qwen3.6-flash-2026-04-16",
    # "model": "deepseek-v4-flash",
    "messages": [
        {
            "role": "system",
            "content": "你是一个简洁的助手, 回答控制在100字以内, 不要包含任何广告或营销信息, 请保持简洁和专业。",
        },
        # {"role": "user", "content": "什么是Token? 用大模型开发的角度解释。"},
        {"role": "user", "content": "AI的发展历程是怎样的?"},
    ],
    "temperature": 1.0,
}

print(">>> 发送请求...")
print(f"    URL: {beijing_openai_base_http_api_url}")
print(f"    Model: {payload['model']}")
print(f"    Message: {payload['messages'][-1]['content']}")
print()

response = httpx.post(
    beijing_openai_base_http_api_url, headers=headers, json=payload, timeout=30
)

if response.status_code == 200:
    data = response.json()
    choice = data["choices"][0]
    usage = data["usage"]

    reply = choice["message"]["content"]
    reasoning_content = choice["message"]["reasoning_content"]

    print("<<< 回复:")
    print(f"    思维链内容: {reasoning_content}")
    print()
    print(f"    {reply}")
    print()
    print("--- Token 消耗 ---")
    print(f"    输入: {usage['prompt_tokens']} tokens")
    print(f"    输出: {usage['completion_tokens']} tokens")
    print(f"    总计: {usage['total_tokens']} tokens")
else:
    print(f"!!! 请求失败: HTTP {response.status_code}")
    print(f"    {response.text}")


"""
Response:
{
    "choices": [
        {
            "message": {
                "content": "在大模型开发中，Token是文本处理的基本单位。它由分词器切分为子词或字符，不严格对应人类词汇。模型以Token序列为输入，逐次预测下一Token概率。它是限定上下文窗口与计算API调用的核心计量单位。",
                "reasoning_content": "Here's a thinking process:\n\n1.  **Analyze User Input:**\n   - **Question:** 什么是Token? 用大模型开发的角度解释。 (What is a Token? Explain from the perspective of large model development.)\n   - **Constraints:** \n     - Keep it under 100 Chinese characters.\n     - No ads or marketing info.\n     - Keep it concise and professional.\n\n2.  **Identify Key Concepts (from LLM dev perspective):**\n   - Token is the basic unit of text processing for LLMs.\n   - It's not always a single word/character; it's a subword/unit determined by the tokenizer (e.g., BPE, WordPiece).\n   - Models process sequences of tokens, predict next token probabilities.\n   - Crucial for input/output handling, context window limits, and cost calculation.\n\n3.  **Draft (Mental Refinement - aiming for <100 chars):**\n   在大模型开发中，Token是文本处理的基本单位。它由分词器（Tokenizer）将输入切分为子词、字符或符号构成，并非严格对应人类词汇。模型以Token序列为输入，逐次预测下一个Token的概率分布。它是计算上下文窗口长度和API调用成本的核心计量单位。\n\n4.  **Character Count Check (Chinese characters + punctuation):**\n   在大模型开发中，Token是文本处理的基本单位。(24)\n   它由分词器将输入切分为子词、字符或符号构成，并非严格对应人类词汇。(33)\n   模型以Token序列为输入，逐次预测下一个Token的概率分布。(31)\n   它是计算上下文窗口长度和API调用成本的核心计量单位。(27)\n   Total: ~115 chars including punctuation. Slightly over. Need to trim.\n\n   Let's count precisely:\n   在大模型开发中，Token是文本处理的基本单位。它由分词器切分为子词或字符，非严格对应词汇。模型以Token序列为输入，逐次预测下一Token概率。它是限定上下文窗口与计算API成本的核心单位。\n   Count: \n   在大模型开发中，Token是文本处理的基本单位。(24)\n   它由分词器切分为子词或字符，非严格对应词汇。(22)\n   模型以Token序列为输入，逐次预测下一Token概率。(26)\n   它是限定上下文窗口与计算API成本的核心单位。(23)\n   Total: ~95 chars with punctuation. Good.\n\n5.  **Final Polish (Professional & Concise):**\n   在大模型开发中，Token是文本处理的基本单位。它由分词器切分为子词或字符，不严格对应人类词汇。模型以Token序列为输入，逐次预测下一Token概率。它是限定上下文窗口与计算API调用的核心计量单位。 (98 chars with punctuation)\n\n   Checks:\n   - Under 100? Yes.\n   - LLM dev perspective? Yes (tokenizer, sequence input, next-token prediction, context window, API cost).\n   - No ads/marketing? Yes.\n   - Concise & professional? Yes.\n\n   Ready. Output matches the polished version.✅",
                "role": "assistant",
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": None,
        }
    ],
    "object": "chat.completion",
    "usage": {
        "prompt_tokens": 55,
        "completion_tokens": 765,
        "total_tokens": 820,
        "completion_tokens_details": {"reasoning_tokens": 703, "text_tokens": 765},
        "prompt_tokens_details": {"text_tokens": 55},
    },
    "created": 1780043112,
    "system_fingerprint": None,
    "model": "qwen3.6-flash-2026-04-16",
    "id": "chatcmpl-e26006cf-f16d-9527-9611-427c5c8d9a05",
}
"""
