"""
第1周 - 第1节 - 任务4: 封装一个 chat() 函数

=== 本任务完成后你需要掌握的 ===

1. 将重复的 API 调用逻辑封装为可复用函数:
   - 不用每次都写 headers, URL, httpx.post
   - 调用方只需要传 message 就能得到回复

2. 函数参数设计:
   - 必填参数: message (用户的问题)
   - 可选参数: model, temperature, system_prompt
   - 用默认值让简单场景一行搞定

3. 返回值设计:
   - 返回结构化数据 (回复文本 + Token 消耗), 不只是字符串
   - 调用方可以选择只取回复, 也可以查看消耗

4. 这个函数后续会反复使用:
   - 第2周多轮对话会基于它扩展
   - 第3周结构化输出会在它基础上加 response_format
   - 第4周函数调用会加 tools 参数

=== 本任务不需要关心的 ===

- 多轮对话 (messages 历史管理) → 第2周
- 流式输出 → 任务3
- 错误重试机制 → 第15周 (Harness)
- 异步调用 (async) → 了解即可, 现阶段用同步

=== 练习 ===

1. 运行此文件, 观察封装后的调用有多简洁
2. 试着只传 message, 用默认参数调用
3. 试着传不同的 temperature 和 model, 观察差异
4. 思考: 如果要支持多轮对话, 这个函数需要怎么改?  (加Assistant Message)
"""

import os

import httpx

from framework.consts import beijing_openai_base_http_api_url

API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("BEIJING_API_KEY 未设置, 请确认 direnv 已加载")


def chat(
    message: str,
    model: str = "qwen3.6-flash-2026-04-16",
    temperature: float = 0.7,
    system_prompt: str = "你是一个简洁的助手, 回答控制在100字以内, 不要包含任何广告或营销信息, 请保持简洁和专业。",
) -> dict:
    """调用大模型 API, 返回回复和 Token 消耗。

    Args:
        message: 用户的问题
        model: 模型名称
        temperature: 随机性 (0=确定, 1.5=创意)
        system_prompt: 系统提示词

    Returns:
        {"reply": str, "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}}
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
    }

    response = httpx.post(
        beijing_openai_base_http_api_url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(f"API 调用失败: HTTP {response.status_code}\n{response.text}")

    data = response.json()
    return {
        "reply": data["choices"][0]["message"]["content"],
        "usage": data["usage"],
    }


# === 使用示例 ===

if __name__ == "__main__":
    # 最简调用: 只传一个问题
    print("=== 示例1: 最简调用 ===")
    result = chat("Python的GIL是什么?")
    print(f"回复: {result['reply']}")
    print(f"消耗: {result['usage']['total_tokens']} tokens")
    print()

    # 指定参数
    print("=== 示例2: 指定参数 ===")
    result = chat(
        message="给我的Python项目起3个名字",
        temperature=1.5,  # 高创意
        system_prompt="你是一个创意命名专家, 每个名字附带一句话解释。",
    )
    print(f"回复: {result['reply']}")
    print(f"消耗: {result['usage']['total_tokens']} tokens")
    print()

    # 低温度: 确定性输出
    print("=== 示例3: temperature=0 (确定性) ===")
    for i in range(3):
        result = chat("1+1等于几? 只回答数字。", temperature=0)
        print(f"  第{i+1}次: {result['reply']}")
