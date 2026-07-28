"""
第1周 - 第5节 - 任务1: Temperature 对输出稳定性的影响

=== 本任务完成后你需要掌握的 ===

1. Temperature 的直观理解:
   - temperature=0: 几乎每次输出相同 (确定性高, 适合事实性问答)
   - temperature=0.7: 有一定变化但整体稳定 (通用场景的默认值)
   - temperature=1.5: 每次输出差异大 (创意写作, 头脑风暴)

2. 如何判断 temperature 是否合适:
   - 多跑几次同一个 prompt, 看输出的"方差"
   - 业务需要一致性 → 低 temperature
   - 业务需要多样性 → 高 temperature

3. 建立选型直觉:
   - 客服/FAQ → 0~0.3
   - 通用助手 → 0.5~0.7
   - 创意生成 → 0.9~1.5

=== 本任务不需要关心的 ===

- Top-p 与 Temperature 的联合调优 → 任务2 会涉及
- Frequency/Presence Penalty → 后面的任务
- 不同模型对 temperature 的敏感度差异 → 了解即可

=== 练习 ===

1. 运行此文件, 观察三种 temperature 下 10 次输出的差异
2. 看 temperature=0 时是否真的每次一样 (思考类模型可能仍有微小差异)
3. 看 temperature=1.5 时输出是否有时"跑偏"
4. 思考: 你日常用 AI 的场景, 应该用哪个 temperature?
"""

import os

import httpx

from framework.consts import beijing_openai_base_http_api_url

API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("BEIJING_API_KEY 未设置, 请确认 direnv 已加载")

MODEL = "qwen3.7-plus"
QUESTION = "用一句话解释什么是递归。"
TEMPERATURES = [0, 0.7, 1.5]
RUNS_PER_TEMP = 10


def call_api(question: str, temperature: float) -> str:
    """调用 API, 返回回复文本。"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个简洁的助手, 用一句话回答问题。"},
            {"role": "user", "content": question},
        ],
        "temperature": temperature,
        "enable_thinking": False,
    }

    response = httpx.post(
        beijing_openai_base_http_api_url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        return f"[ERROR: {response.status_code} {response.text[:100]}]"

    if not response.content:
        return "[ERROR: 空响应]"

    data = response.json()
    return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print(f"模型: {MODEL}")
    print(f"问题: {QUESTION}")
    print(f"每种 temperature 调用 {RUNS_PER_TEMP} 次")
    print()

    for temp in TEMPERATURES:
        print("=" * 60)
        print(f"Temperature = {temp}")
        print("=" * 60)

        results = []
        for i in range(RUNS_PER_TEMP):
            reply = call_api(QUESTION, temp)
            results.append(reply)
            print(f"  [{i + 1:2d}] {reply}")

        # 统计: 有多少条是完全相同的
        unique = len(set(results))
        print(
            f"\n  → {RUNS_PER_TEMP} 次调用中有 {unique} 种不同回答 (唯一率: {unique}/{RUNS_PER_TEMP})"
        )
        print()
