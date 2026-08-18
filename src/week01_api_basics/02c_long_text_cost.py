"""
第1周 - 第2节 - 任务3: 长文本的 Token 计算与费用估算

=== 本任务完成后你需要掌握的 ===

1. 对真实长文本 (5000字级别) 建立 Token 数量的直觉
2. 理解: 把一篇文章塞进 prompt 要花多少钱
3. 感受: "上下文窗口"在实际场景中会被消耗得多快
4. 联想: 如果做 RAG (让模型读文档回答问题), 每次查询的成本是多少

=== 本任务不需要关心的 ===

- 如何切分长文档 → 第6周 (Chunking)
- 如何只检索相关片段而不是全文塞入 → 第5-8周 (RAG)

=== 练习 ===

1. 运行此文件, 观察中文 vs 英文文章的 Token 差异
2. 对比同样 5000 字, 中文和英文的费用差多少
3. 把你大纲文件 (AI_Engineer_20周实战大纲.md) 也算一下, 感受它有多大
4. 思考: 128K 窗口的模型能一次读入多长的文档?
"""

import os

import tiktoken

encoding = tiktoken.encoding_for_model("gpt-4o")

# 价格表 (元/百万Token)
MODEL_PRICING = {
    "qwen3.6-flash": {"input": 0.0, "output": 0.0},
    "qwen-turbo": {"input": 0.3, "output": 0.6},
    "qwen-plus": {"input": 0.8, "output": 2.0},
    "qwen-max": {"input": 2.0, "output": 6.0},
    "deepseek-v3": {"input": 1.0, "output": 2.0},
    "gpt-4o": {"input": 17.5, "output": 70.0},
}


# === 1. 读取真实长文本 ===

test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")

files = {
    "中文文章": os.path.join(test_data_dir, "chinese_long_text.txt"),
    "英文文章": os.path.join(test_data_dir, "english_long_text.txt"),
}

print("=" * 60)
print("长文本 Token 分析")
print("=" * 60)
print()

for label, filepath in files.items():
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    tokens = len(encoding.encode(content))
    chars = len(content)

    print(f"[{label}] {os.path.basename(filepath)}")
    print(f"  字符数: {chars}")
    print(f"  Token 数: {tokens}")
    print(f"  比例: 1 字符 ≈ {tokens / chars:.2f} token")
    print()
    print("  如果全文作为 prompt (假设输出 500 tokens):")
    for model, price in MODEL_PRICING.items():
        input_cost = tokens * price["input"] / 1_000_000
        output_cost = 500 * price["output"] / 1_000_000
        total = input_cost + output_cost
        print(f"    {model:<18} ¥{total:.4f}")
    print()


# === 2. 大纲文件有多大? ===

outline_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "docs", "AI_Engineer_20周实战大纲.md"
)

if os.path.exists(outline_path):
    with open(outline_path, "r", encoding="utf-8") as f:
        outline = f.read()
    outline_tokens = len(encoding.encode(outline))
    print("你的 20周大纲文件:")
    print(f"  字符数: {len(outline)}")
    print(f"  Token 数: {outline_tokens}")
    print(f"  占 128K 窗口的: {outline_tokens / 128000 * 100:.1f}%")
    print()


# === 3. 窗口容量参照 ===

print("=" * 60)
print("Context Window 能装多少内容? (按中文估算)")
print("=" * 60)
print()

windows = [4096, 8192, 32768, 65536, 131072]
for w in windows:
    chars_approx = int(w / 0.82)  # 中文约 1.5 token/字
    pages = chars_approx // 500  # 一页A4约500字
    print(f"  {w:>7,} tokens ≈ {chars_approx:>6,} 中文字 ≈ {pages} 页 A4")

print()
print("注意: 这是输入+输出的总预算, 不是只算输入!")
