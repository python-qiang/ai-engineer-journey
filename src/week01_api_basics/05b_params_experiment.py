"""
第1周 - 第5节 - 任务2: 参数综合实验 (Top-p, Penalty, Stop)

=== 本任务完成后你需要掌握的 ===

1. Top-p (核采样):
   - 控制"从多大的候选词池里选", 0.5=只从最可能的一半里选, 1.0=所有词都有机会
   - 通常与 temperature 配合: 要确定性高就 temperature低+top_p低, 要创意就两者都高
   - 大部分情况保持默认 0.9 即可, 不需要频繁调

2. Frequency Penalty (频率惩罚):
   - 惩罚已经出现过的词, 值越大模型越避免重复用词
   - 范围 0~2, 默认 0
   - 适用场景: 模型重复啰嗦时调到 0.5~1.0

3. Presence Penalty (存在惩罚):
   - 惩罚已经出现过的话题, 鼓励模型谈论新话题
   - 范围 0~2, 默认 0
   - 适用场景: 想让模型发散思路时调到 0.5~1.0

4. Stop Sequences (停止序列):
   - 指定字符串, 模型输出中遇到就立即停止生成
   - 适用场景: 只要第一段/只要第一行/遇到特定标记就停

=== 本任务不需要关心的 ===

- 参数的数学原理 (softmax temperature scaling 等) → 了解效果即可
- 不同模型对参数的敏感度差异 → 了解即可

=== 练习 ===

1. 运行此文件, 观察每种参数的效果
2. 对比 Top-p=0.3 vs Top-p=1.0 的输出多样性
3. 观察 Frequency Penalty 如何减少重复
4. 观察 Stop Sequences 如何截断输出
"""

import os

import httpx

from framework.consts import beijing_openai_base_http_api_url

API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("BEIJING_API_KEY 未设置, 请确认 direnv 已加载")

MODEL = "qwen3.7-plus"


def call_api(question: str, system_prompt: str = "你是一个简洁的助手, 回答问题控制在200字以内。", **kwargs) -> str:
    """调用 API, 支持传入任意额外参数。"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "enable_thinking": False,
        **kwargs,
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

    # ============================================================
    # 实验1: Top-p 对比
    # ============================================================
    print("=" * 60)
    print("实验1: Top-p (核采样) 对输出多样性的影响")
    print("=" * 60)
    print("  temperature 固定为 1.0, 只改变 top_p")
    print()

    question = "给一个AI学习项目起个名字。"
    for top_p in [0.3, 0.7, 1.0]:
        print(f"  --- top_p={top_p} (跑3次) ---")
        for i in range(3):
            reply = call_api(question, temperature=1.0, top_p=top_p)
            print(f"    [{i+1}] {reply}")
        print()

    # ============================================================
    # 实验2: Frequency Penalty 对比
    # ============================================================
    print("=" * 60)
    print("实验2: Frequency Penalty (频率惩罚) 减少重复")
    print("=" * 60)
    print("  让模型写一段话, 观察是否有重复用词")
    print()

    question = "用5句话描述春天, 每句话要有不同的意象。"
    for penalty in [0, 0.5, 1.5]:
        print(f"  --- frequency_penalty={penalty} ---")
        reply = call_api(question, temperature=0.7, frequency_penalty=penalty)
        print(f"    {reply}")
        print()

    # ============================================================
    # 实验3: Presence Penalty 对比
    # ============================================================
    print("=" * 60)
    print("实验3: Presence Penalty (存在惩罚) 鼓励发散")
    print("=" * 60)
    print("  让模型列举内容, 观察是否更愿意覆盖新话题")
    print()

    question = "列举10个不同领域的AI应用场景, 越多样越好。"
    for penalty in [0, 1.0, 2.0]:
        print(f"  --- presence_penalty={penalty} ---")
        reply = call_api(question, temperature=0.7, presence_penalty=penalty)
        print(f"    {reply[:200]}...")  # 只打印前200字
        print()

    # ============================================================
    # 实验4: Stop Sequences
    # ============================================================
    print("=" * 60)
    print("实验4: Stop Sequences (停止序列)")
    print("=" * 60)
    print("  让模型列举多项, 但在第3项后停止")
    print()

    question = "列举5种编程语言, 每种一行, 格式为: 1. xxx"

    print("  --- 无 stop (完整输出) ---")
    reply = call_api(question, temperature=0.7)
    print(f"    {reply}")
    print()

    print("  --- stop=['4.'] (在第4项前停止) ---")
    reply = call_api(question, temperature=0.7, stop=["4."])
    print(f"    {reply}")
    print()

    print("  --- stop=['\\n\\n'] (遇到空行就停止) ---")
    reply = call_api(question, temperature=0.7, stop=["\n\n"])
    print(f"    {reply}")
    print()

    # ============================================================
    # 总结
    # ============================================================
    print("=" * 60)
    print("参数速查表")
    print("=" * 60)
    print("""
  | 参数               | 作用              | 常用值       | 典型场景           |
  |--------------------|-------------------|--------------|--------------------|
  | temperature        | 控制随机性        | 0~1.5        | 0=确定, 0.7=通用   |
  | top_p              | 候选词池大小      | 0.9 (默认)   | 配合 temperature   |
  | frequency_penalty  | 惩罚重复用词      | 0~1.0        | 模型啰嗦时调高     |
  | presence_penalty   | 鼓励新话题        | 0~1.0        | 需要发散时调高     |
  | stop               | 指定停止标记      | 字符串列表   | 只要前N项/前1段    |
  | max_tokens         | 限制输出长度      | 按需设置     | 控制成本/截断      |
""")
