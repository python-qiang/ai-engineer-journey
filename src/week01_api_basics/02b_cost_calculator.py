"""
第1周 - 第2节 - 任务2: cost_calculator 费用计算函数

=== 本任务完成后你需要掌握的 ===

1. 能写一个函数, 输入文本和模型名, 输出预估费用 (元)
2. 理解不同模型的价格差异 (可以差 10-100 倍)
3. 理解 input token 和 output token 分开计价
4. 养成习惯: 选模型时不只看效果, 还要看成本

=== 本任务不需要关心的 ===

- 精确到分的计费 (真实场景看 API 返回的 usage) → 已在任务1学过
- 批量调用的折扣/免费额度 → 看各平台官网
- 缓存优化降低成本 → 第10周

=== 练习 ===

1. 运行此文件, 对比不同模型处理同一文本的费用
2. 修改 output_tokens, 感受输出长度对成本的影响
3. 用你工作中的一段文档 (如 README) 算算费用
4. 思考: 如果你做一个客服机器人, 每天处理 1000 条消息, 选哪个模型?
"""

import tiktoken


# 通义千问/DeepSeek 价格表 (元/百万Token, 2026年参考)
MODEL_PRICING = {
    "qwen3.6-flash":  {"input": 0.0,   "output": 0.0},
    "qwen-turbo":     {"input": 0.3,   "output": 0.6},
    "qwen-plus":      {"input": 0.8,   "output": 2.0},
    "qwen-max":       {"input": 2.0,   "output": 6.0},
    "deepseek-v3":    {"input": 1.0,   "output": 2.0},
    "gpt-4o":         {"input": 17.5,  "output": 70.0},   # 贵100倍, 感受一下
}


def cost_calculator(text: str, model: str = "qwen-turbo", output_tokens: int = 200) -> dict:
    """输入文本和模型名, 输出预估费用 (元)。

    Args:
        text: 要发送给模型的文本 (作为 prompt)
        model: 模型名称
        output_tokens: 预估模型会输出多少 token (无法提前精确知道, 给个估计值)

    Returns:
        包含 input_tokens, output_tokens, input_cost, output_cost, total_cost 的字典
    """
    if model not in MODEL_PRICING:
        raise ValueError(f"未知模型: {model}, 支持: {list(MODEL_PRICING.keys())}")

    encoding = tiktoken.encoding_for_model("gpt-4o")  # 通用估算
    input_tokens = len(encoding.encode(text))
    price = MODEL_PRICING[model]

    input_cost = input_tokens * price["input"] / 1_000_000
    output_cost = output_tokens * price["output"] / 1_000_000

    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_yuan": input_cost,
        "output_cost_yuan": output_cost,
        "total_cost_yuan": input_cost + output_cost,
    }


# === 演示 ===

if __name__ == "__main__":
    sample_text = "请帮我写一段Python代码, 实现快速排序算法, 并解释每一步的作用。要求代码有详细注释。"

    print(f"输入文本: \"{sample_text}\"")
    print("预估输出: 500 tokens")
    print()
    print(f"{'模型':<18} {'输入Token':<10} {'输入费用':<12} {'输出费用':<12} {'总费用':<12} {'日均(1000次)'}")
    print("-" * 85)

    for model in MODEL_PRICING:
        result = cost_calculator(sample_text, model=model, output_tokens=500)
        daily = result["total_cost_yuan"] * 1000
        print(
            f"{result['model']:<18} "
            f"{result['input_tokens']:<10} "
            f"¥{result['input_cost_yuan']:<10.6f} "
            f"¥{result['output_cost_yuan']:<10.6f} "
            f"¥{result['total_cost_yuan']:<10.6f} "
            f"¥{daily:.3f}/天"
        )

    print()
    print("结论: qwen3.6-flash 免费, qwen-turbo 极便宜, gpt-4o 贵 100 倍。")

    
    print("实际选型时在效果满足需求的前提下, 优先选便宜的模型。")
