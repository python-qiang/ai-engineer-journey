"""
第1周 - 第2节 - 任务1: Token 分词原理与成本计算

=== 本任务完成后你需要掌握的 ===

1. Token 的概念:
   - 大模型不按"字"或"词"处理文本, 而是按 Token (子词单元)
   - 一个中文字 ≈ 1-2 个 Token, 一个英文单词 ≈ 1-4 个 Token
   - Token 是计费单位, 也是上下文窗口的度量单位

2. 能用 tiktoken 库精确计算 Token 数:
   - 输入任意文本, 得到精确的 Token 数量
   - 能可视化看到文本被切成了哪些 Token 片段

3. 中文 vs 英文的 Token 效率差异:
   - 同样的语义, 中文通常比英文消耗更多 Token
   - 这直接影响成本和上下文窗口的利用率

4. 成本意识:
   - 每次 API 调用都在花钱: 输入 Token + 输出 Token 分别计费
   - 能估算一段文本调用一次大概花多少钱
   - 不同模型价格差异巨大

=== 本任务不需要关心的 (后面会学) ===

- BPE 分词算法的数学原理 → 了解概念即可, 不需要手写实现
- 如何压缩/管理上下文长度 → 第2周
- Embedding 的 Token 计算 → 第5周
- 如何用缓存降低成本 → 第10周
- Context Window 溢出的处理策略 → 第2周

=== 练习 ===

1. 运行此文件, 观察中文 vs 英文的 Token 效率差异
2. 找一段你自己写的代码 (50行左右), 计算它的 Token 数
3. 修改 estimate_cost 中的模型, 对比不同模型的价格差异
4. 思考: 如果你的 system prompt 有 500 Token, 每次对话都要带上,
   一天调用 1000 次, 光 system prompt 就花多少钱?
"""

import tiktoken

# === 1. 计算 Token 数 ===

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """计算文本的 Token 数量。

    注意: tiktoken 是 OpenAI 的分词器。
    通义/DeepSeek 的分词器略有不同, 但误差在 10-20% 以内, 学习阶段够用。
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def show_tokens(text: str, model: str = "gpt-4o"):
    """可视化: 看看文本被切成了哪些 Token 片段。"""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    pieces = [encoding.decode([t]) for t in tokens]
    print(f"原文: {text}")
    print(f"Token 数: {len(tokens)}")
    print(f"切分: {pieces}")
    print()


# === 2. 中英文 Token 效率对比 ===

print("=" * 50)
print("中英文 Token 效率对比")
print("=" * 50)
print()

samples = [
    ("中文", "大语言模型是一种基于深度学习的人工智能技术"),
    ("英文", "Large language models are AI technology based on deep learning"),
    ("代码", "def hello(): return 'world'"),
    ("混合", "使用Python调用OpenAI的API接口"),
]

for label, text in samples:
    count = count_tokens(text)
    print(f"[{label}] \"{text}\"")
    print(f"        {len(text)} 字符 → {count} tokens (平均 1字符 ≈ {count/len(text):.2f} token)")
    print()


# === 3. 分词可视化 ===

print("=" * 50)
print("分词可视化 — 看看模型怎么切的")
print("=" * 50)
print()

show_tokens("我喜欢吃苹果")
show_tokens("I like eating apples")
show_tokens("Token是大模型的计费单位")
show_tokens("def calculate(x, y): return x + y")


# === 4. 成本估算 ===

print("=" * 50)
print("成本估算")
print("=" * 50)
print()

# 通义千问价格 (元/百万Token, 2026年参考价)
PRICING = {
    "qwen3.6-flash":  {"input": 0.0,  "output": 0.0},    # 免费
    "qwen-turbo":     {"input": 0.3,  "output": 0.6},
    "qwen-plus":      {"input": 0.8,  "output": 2.0},
    "qwen-max":       {"input": 2.0,  "output": 6.0},
    "deepseek-v3":    {"input": 1.0,  "output": 2.0},
}


def estimate_cost(input_text: str, output_tokens: int = 200, model: str = "qwen-turbo"):
    """估算一次 API 调用的费用。"""
    input_tokens = count_tokens(input_text) # 用 gpt-4o 分词器估算, 有 10-20% 误差
    price = PRICING[model]

    input_cost = input_tokens * price["input"] / 1_000_000
    output_cost = output_tokens * price["output"] / 1_000_000
    total = input_cost + output_cost

    print(f"模型: {model}")
    print(f"  输入: {input_tokens} tokens × ¥{price['input']}/百万 = ¥{input_cost:.6f}")
    print(f"  输出: ~{output_tokens} tokens × ¥{price['output']}/百万 = ¥{output_cost:.6f}")
    print(f"  单次总计: ¥{total:.6f}")
    print(f"  如果每天调 1000 次: ¥{total * 1000:.3f}/天")
    print()


sample = "请帮我写一段Python代码, 实现快速排序算法, 并解释每一步的作用。"
print(f"示例输入: \"{sample}\"")
print("假设输出: ~500 tokens")
print()

for model in PRICING:
    estimate_cost(sample, output_tokens=500, model=model)
