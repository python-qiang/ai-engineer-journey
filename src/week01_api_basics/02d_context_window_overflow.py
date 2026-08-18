"""
第1周 - 第2节 - 任务4: Context Window 与输出限制实验

=== 本任务完成后你需要掌握的 ===

1. 输入越长, 响应越慢, 费用越高 — 即使没溢出也要控制输入长度
2. max_completion_tokens 参数可以限制输出长度, 超过后模型会被强制截断 (回答不完整)
3. 能观察到: 首字延迟 (TTFT) 与输入长度成正比
4. 工程意识: 不是"能塞多少就塞多少", 而是"只塞必要的内容"

=== 本任务不需要关心的 ===

- 如何截断/压缩上下文 → 第2周
- 如何只检索相关片段 → 第5-8周 (RAG)
- 流式输出的详细实现 → 第3节

=== 练习 ===

1. 运行此文件, 观察不同输入长度下的响应时间差异
2. 观察 max_completion_tokens=20 时模型的回答被截断是什么效果
3. 思考: 如果你做客服机器人, 应该给 max_completion_tokens 设多少?
4. 思考: 为什么 RAG 不把整本书塞进 prompt, 而是只检索相关片段?
"""

import os
import time

import httpx

from framework.consts import DEFAULT_MODEL, beijing_openai_base_http_api_url

API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("BEIJING_API_KEY 未设置")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def call_api(user_message: str, max_completion_tokens: int | None = None) -> dict:
    """调用 API 并记录耗时。"""
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个助手, 回答请保持简洁和专业, 尽量控制在200字以内。",
            },
            {"role": "user", "content": user_message},
        ],
        "temperature": 1.0,
        "enable_thinking": False,
    }
    if max_completion_tokens:
        # 用于限制模型本次响应中输出的最大 Token 数, 包含思维链. 若生成内容超过此值, 生成将提前停止, 且返回的 finish_reason 为 length.
        payload["max_completion_tokens"] = max_completion_tokens

    start = time.time()
    response = httpx.post(
        beijing_openai_base_http_api_url,
        headers=headers,
        json=payload,
        timeout=120,
    )
    elapsed = time.time() - start

    if response.status_code == 200:
        data = response.json()
        usage = data["usage"]
        content = data["choices"][0]["message"]["content"]
        finish_reason = data["choices"][0]["finish_reason"]
        return {
            "success": True,
            "elapsed": elapsed,
            "prompt_tokens": usage["prompt_tokens"],
            "completion_tokens": usage["completion_tokens"],
            "total_tokens": usage["total_tokens"],
            "finish_reason": finish_reason,
            "content_preview": content[:100],
            "content": content,  # 原始内容, 用于后续分析
        }
    else:
        return {"success": False, "elapsed": elapsed, "error": response.text[:200]}


if __name__ == "__main__":
    # === 实验1: 小问题 vs 大问题的响应时间对比 ===
    print("=" * 60)
    print("实验1: 小问题 vs 大问题 (读长文档) 的响应时间对比")
    print("=" * 60)
    print()

    # 小问题: 简单提问
    small_question = "Python是什么语言? 一句话回答。"

    # 大问题: 读取 test_data 中的长文档, 让模型总结
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    with open(
        os.path.join(test_data_dir, "chinese_long_text.txt"), "r", encoding="utf-8"
    ) as f:
        long_doc = f.read()
    big_question = f"请用3句话总结以下文档的核心内容:\n\n{long_doc}"

    for label, question in [
        ("小问题", small_question),
        ("大问题(读5000字文档)", big_question),
    ]:
        result = call_api(question)
        if result["success"]:
            print(f"[{label}]")
            print(f"  输入: {result['prompt_tokens']} tokens")
            print(f"  输出: {result['completion_tokens']} tokens")
            print(f"  耗时: {result['elapsed']:.2f}s")
            # print(f"  回答: {result['content']}")
            print(f"  回答: {result['content_preview']}。。。")
        else:
            print(f"[{label}] 失败: {result['error']}")
        print()

    # === 实验2: max_completion_tokens 截断效果 ===
    print("=" * 60)
    print("实验2: max_completion_tokens 限制输出长度")
    print("=" * 60)
    print()

    question = "请简单介绍Python1个最核心的特性"
    # question = "请简单列举Python的2个核心特性"

    for max_tok in [20, 50, 100, None]:
        label = (
            f"max_completion_tokens={max_tok}"
            if max_tok
            else "max_completion_tokens=不限制"
        )
        result = call_api(question, max_completion_tokens=max_tok)

        if result["success"]:
            print(f"[{label}]")
            print(f"  输出 tokens: {result['completion_tokens']}")
            print(f"  finish_reason: {result['finish_reason']}")
            # print(f"  回答预览: {result['content_preview']}...")
            print(f"  回答: {result['content']}")
            print()
            # finish_reason 说明:
            # 触发输入参数中的stop参数, 或自然停止输出时为stop;
            # 生成长度过长而结束为length;
            # 需要调用工具而结束为tool_calls。
        else:
            print(f"[{label}] 失败: {result['error']}")
            print()

    print("=" * 60)
    print("结论:")
    print("  - finish_reason='length' 表示回答被截断, 内容不完整")
    print("  - finish_reason='stop' 表示模型自然结束")
    print("  - 输入越长响应越慢, 即使窗口够大也要控制输入长度")
    print("  - 这就是为什么 RAG 只检索相关片段而不是塞整本书")
