"""
第2周 - 第4节 - 任务1: Zero-shot vs Few-shot 对照实验

=== 本任务完成后你需要掌握的 ===

1. Zero-shot vs Few-shot 的本质区别:
   - Zero-shot: 只给指令, 不给示例
   - Few-shot: 指令 + 几个"输入->输出"示例, 让模型模仿
   - 2026 认知: Few-shot 不再是"教模型逻辑"(reasoning model 自己会),
     而是"教格式/风格/业务黑话/边界判定"

2. 示例(demonstration)的四个维度如何影响效果:
   - 数量: 3 个 vs 全量
   - 质量: 随机示例 vs 精心挑选的高质量示例 vs 针对性边界示例
   - 顺序: 打乱示例顺序会不会改变结果
   - 针对性: 专门为易错边界补一条示例(教模型你的判定规则)

3. Few-shot 的真实局限(和"few-shot 一定更好"的直觉相反):
   - few-shot 是双刃剑, 选不好会引入偏见反而更差
   - 加示例"按下葫芦浮起瓢": 修好目标边界可能干扰其他样本 -> 需要回归测试
   - 只能教"示范过的模式", 没覆盖的边界照样错
   - 深层: 分类的"标准答案"本身可能有歧义, 模型的错未必是错

4. 用数据而非感觉判断 prompt 好坏:
   - accuracy(准确率)
   - invalid label rate(返回了候选集外的标签 = 格式不听话)
   - 单次跑分不可靠(有随机性), 判断好坏需多次运行 / 回归对比

=== 本任务不需要关心的 ===

- Reasoning / thinking 控制 -> 04b
- JSON 结构化约束 -> 04c
- Prompt cache 排版 -> 04d
- 把实验逻辑抽成通用 runner -> 04e (先手写重复代码, 体会痛点)
- token / 成本统计 -> Week 1 已练, 04b thinking 开关处再深入
- Pydantic / JSON Schema / 校验重试 -> 第3周

=== 练习 ===

场景: 电商客服意图分类, 标签 = {退换货, 物流查询, 商品咨询, 投诉, 催单, 其他}
(选业务专属 + 有歧义的标签, 让模型无法 zero-shot 靠常识猜准, few-shot 才有用武之地)

1. 准备数据集:
   - 10-12 条中文客户消息, 每条人工标注一个"标准答案"意图
   - 多条边界案例(消息跨两个意图, 如"下单一周没到, 不想要了能退款吗")
   - 示例池与测试集严格分开(避免 answer leakage 答案泄漏)

2. 实现两个 prompt 构造函数:
   - build_zero_shot_prompt(text): 指令 + 待分类文本
   - build_few_shot_prompt(text, examples): 指令 + 示例 + 待分类文本

3. 跑多种配置, 每种都在整个数据集上评测:
   - V1: Zero-shot (基线)
   - V2: 3 个随机/低质量示例
   - V3: 3 个高质量示例
   - V4: 全量高质量示例(覆盖所有标签)
   - V5: V4 但打乱示例顺序
   - V6: 针对易错边界补针对性示例(加餐, 教模型你的判定规则)

4. 每种配置记录:
   - accuracy (预测对的比例)
   - invalid label rate (返回了候选集外的标签)

5. 写结论:
   - few-shot 相比 zero-shot 提升了吗? 哪个配置最好?
   - 有没有配置反而变差? 为什么?
   - 顺序有影响吗? 针对性示例能救回顽固错误吗? 有没有副作用?

=== 提示 ===

- 复用 framework/chat.py 的 stream_chat(print_content=False) 拿到 content
- 需要一个 parse_label 从模型返回里提取标签(模型可能带多余字)
- prompt 里明确要求"只返回标签, 不要解释", 观察 invalid_rate(现代模型通常很听话)
- 标签用中文, 保持 prompt 中文的项目基调
- 数据集小没关系, 重点是让 prompt 行为"可观测、可对比", 不是做生产分类器
- 实验入口放 if __name__ == "__main__", 保证 import 不触发 API 调用(04e 会复用这些函数)
- 关键心态: 判断 prompt 好坏靠数据, 不靠感觉; 且单次跑分有随机性, 别轻易下结论
"""

# ============================================================
# 你的代码写在下面
# ============================================================

import random

from framework.chat import stream_chat

# Candidate labels: e-commerce customer-service INTENT classification.
# These intents are business-specific and overlap on purpose, so the model
# cannot reliably guess our boundaries zero-shot -- few-shot examples are
# needed to align it with OUR definition of each intent.
LABELS = {"退换货", "物流查询", "商品咨询", "投诉", "催单", "其他"}

# Test set: each item is (customer_message, standard_answer_intent).
# Many items are deliberately ambiguous (straddle two intents), which is
# where zero-shot tends to fail and few-shot helps.
DATASET = [
    ("我买的鞋子尺码不合适，想换一双大的", "退换货"),
    ("这个商品有货吗？支持7天无理由吗", "商品咨询"),
    ("下单三天了物流一直不更新，到底发货了没", "催单"),
    ("客服态度极差，我要投诉你们店", "投诉"),
    ("我的快递到哪了，什么时候能到", "物流查询"),
    ("这件衣服掉色严重，我要退货并且投诉质量问题", "退换货"),
    ("你们双十一有活动吗，什么时候最便宜", "其他"),
    ("东西收到了但是和描述不符，怎么处理", "退换货"),
    # Boundary cases: straddle two intents, hard without examples.
    ("我的订单怎么还没发货，是不是没货了", "催单"),
    ("这个颜色和图片差好多，太失望了", "投诉"),
    ("我想知道这个多少钱，另外能不能包邮", "商品咨询"),
    ("下单一周了还没到，我不想要了能退款吗", "退换货"),
]

# Few-shot example pool, kept SEPARATE from DATASET (avoid answer leakage).
# High-quality examples: cover all six intents, include a boundary case that
# teaches how we disambiguate (e.g. "没发货+想退款" -> 退换货, not 催单).
EXAMPLES_GOOD = [
    ("我收到的商品有破损，想申请退货", "退换货"),
    ("请问这款手机什么时候补货", "商品咨询"),
    ("我的包裹显示已签收但我没收到", "物流查询"),
    ("等了半个月都没发货，太过分了必须投诉", "投诉"),
    ("已经付款两天了怎么还没安排发货", "催单"),
    ("你们店铺支持开发票吗", "其他"),
]

# Random / low-quality examples: skewed toward a few intents, no boundary
# disambiguation, for contrast against EXAMPLES_GOOD.
EXAMPLES_RANDOM = [
    ("我要退货", "退换货"),
    ("退款", "退换货"),
    ("这个怎么样", "商品咨询"),
]

# Targeted examples: one per stubborn error, each teaching a specific boundary.
EXAMPLES_TARGETED = EXAMPLES_GOOD + [
    ("催一下我的订单，怎么还不发货", "催单"),  # teach: chasing shipment = 催单
    ("你们最近有什么促销活动吗", "其他"),  # teach: asking about promo = 其他
    ("这质量也太差了吧，非常不满意", "投诉"),  # teach: complaint w/o request = 投诉
]

_INTENT_INSTRUCTION = (
    '判断下面这条客户消息的意图，从"退换货"/"物流查询"/"商品咨询"/"投诉"/"催单"/"其他"'
    "中六选一。只返回标签，不需要解释。"
)


def build_zero_shot_prompt(text):
    return f"""{_INTENT_INSTRUCTION}
客户消息：{text}
意图："""


def build_few_shot_prompt(text, examples):
    demo = "\n".join(f"客户消息：{t}\n意图：{label}" for t, label in examples)
    return f"""{_INTENT_INSTRUCTION}
示例：
{demo}

客户消息：{text}
意图："""


def parse_label(answer: str):
    """Extract a valid label from the model output; return raw text if none."""
    answer = answer.strip()
    if answer in LABELS:
        return answer
    for label in LABELS:
        if label in answer:
            return label
    return answer


def run_config(build_fn):
    """Run one config over the whole dataset, return [(gt, pred), ...]."""
    results = []
    for text, gt in DATASET:
        messages = [{"role": "user", "content": build_fn(text)}]
        content, _, _ = stream_chat(
            messages=messages,
            enable_thinking=False,
            print_content=False,
        )
        results.append((gt, parse_label(content)))
    return results


def score(results):
    total = len(results)
    correct = invalid = 0
    for gt, pred in results:
        if pred == gt:
            correct += 1
        if pred not in LABELS:
            invalid += 1
    return {"accuracy": correct / total, "invalid_rate": invalid / total}


if __name__ == "__main__":
    shuffled = EXAMPLES_GOOD.copy()
    random.shuffle(shuffled)

    configs = {
        "V1_zero_shot": build_zero_shot_prompt,
        "V2_random_3": lambda t: build_few_shot_prompt(t, EXAMPLES_RANDOM[:3]),
        "V3_good_3": lambda t: build_few_shot_prompt(t, EXAMPLES_GOOD[:3]),
        "V4_good_all": lambda t: build_few_shot_prompt(t, EXAMPLES_GOOD),
        "V5_good_shuffled": lambda t: build_few_shot_prompt(t, shuffled),
        "V6_targeted": lambda t: build_few_shot_prompt(t, EXAMPLES_TARGETED),
    }

    for name, build_fn in configs.items():
        results = run_config(build_fn)
        print(f"{name}: {score(results)}")
        print(f"  details: {results}")

