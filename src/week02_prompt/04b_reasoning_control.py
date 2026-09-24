"""
第2周 - 第4节 - 任务2: Reasoning Control(推理控制) —— 本节重点

=== 本任务完成后你需要掌握的 ===

1. Reasoning Model 时代 Prompt 的核心转变:
   - 不再是"教模型怎么思考"(如传统 Let's think step by step)
   - 而是"控制模型: 何时思考、思考到什么程度、要不要验证、何时不该思考"
   - qwen3.7 自带 thinking, 用 enable_thinking 开关控制

2. thinking 开关的成本/收益权衡:
   - thinking=True: 准, 但慢(TTFT 高)、贵(思考过程也算 output token)
   - thinking=False: 快、便宜, 但复杂任务可能错
   - 核心判断力: 什么任务值得开 thinking? 这是 AI 工程师的日常决策

3. 四种模式的对比认知:
   - thinking=False: 直接答
   - thinking=True: 开思考
   - thinking=True + verification: 思考 + 答前自检(verification/self-check 基础概念)
   - 手写传统 CoT: thinking=False 但 prompt 里加"一步步想"
     (对照组: 验证 reasoning model 时代传统 CoT 是否已多余/无用)

4. 用数据判断(呼应 04a: 靠数据不靠感觉):
   - accuracy / reasoning_tokens / latency / 总 tokens
   - 结论: 在什么难度的任务上, 开 reasoning 才值回票价?
   - 可选(统计味道): 难题多次跑, 看 accuracy 方差(呼应 04a 单次跑分不可靠)

=== 本任务不需要关心的 ===

- verification 的完整工程化(自纠错循环: 报错->反馈->重试) -> 第15周 Harness
- reasoning budget/effort 的 API 级参数(qwen 目前主要是开关) -> 了解概念即可
- 纯 prompt JSON 约束 -> 04c
- Prompt cache 排版 -> 04d
- 抽通用 runner -> 04e

=== 练习 ===

本任务分两部分: Part 1 用数据搞清"什么任务该开 thinking", Part 2 用这个结论做自动路由。

--- Part 1: 四种模式对比实验 ---

1. 构造数据集(你来造, 发挥你对"好测试集"的判断):
   - 逻辑/数学/代码题, 标准答案明确(便于自动判分, 不像意图分类那么主观)
   - 关键: 要有难度梯度
     * 简单题: thinking 关也能对 -> 用来证明"简单任务开 thinking 是浪费"
     * 难题: thinking 关会错、开才对 -> 用来证明"难任务 thinking 值钱"
   - 每题格式: (题目, 标准答案) —— 答案要能被程序判对错(数字/单个词/可归一化的字符串)
   - 8-12 题, 难易搭配

2. 实现四种 prompt / 调用模式:
   - build_direct_prompt(q): 直接问
   - build_cot_prompt(q): 加"请一步步思考"(传统 CoT, 配 thinking=False)
   - 调用时通过 enable_thinking 控制 thinking 开关
   - verification: 在 prompt 里加"给出答案前先验证计算/约束"

3. 跑四种模式, 每种在整个数据集上评测:
   - M1: thinking=False, 直接问
   - M2: thinking=True
   - M3: thinking=True + verification 提示
   - M4: thinking=False + 手写 CoT

4. 每种记录: accuracy / 平均 output(reasoning) tokens / 平均 latency / 总 tokens
   - latency: 用 time.time() 掐每次调用的耗时
   - reasoning tokens: 看 usage 里 thinking 相关字段(或用 output_tokens 近似)

5. 写结论:
   - 简单题上四种模式差别大吗? thinking 带来的额外成本值吗?
   - 难题上 thinking 是否显著提升? verification 有没有额外帮助?
   - 手写 CoT(M4) 相比直接问(M1)还有用吗? 相比开 thinking(M2)呢?
   - 一句话决策: 什么情况下你会在生产里开 thinking?

--- Part 2: 自动路由 (Reasoning Router) ---

背景: 生产里不能人工决定每条请求开不开 thinking, 要自动路由。
架构: 请求 -> [便宜的 router 判断复杂度] -> 简单走 thinking=False, 复杂走 thinking=True
      (cheap model gates expensive model: 便宜模型给贵模型把关)

6. 实现两版 router, 用 Part 1 的数据集验证:
   - 规则版 route_by_rule(q): 关键词/长度判断(简单、零成本、但脆弱)
   - 小模型版 route_by_model(q): 用本地 Ollama 模型判断"这题需要深度推理吗"
     * 复用 stream_chat, url 传 ollama_base_url, model 传 LOCAL_MODEL/LOCAL_WEAK_MODEL
     * 本地模型做 router 的好处: 免费、快, 不给主流程加云端成本
   - router 只返回 "thinking" / "no_thinking" 的决策, 不实际回答问题

7. 验证 router:
   - 对数据集每题跑 router, 看它的决策和题目实际难度是否吻合
   - 对比: 全开 thinking vs router 决策, 省了多少 token/成本, accuracy 掉了吗
   - 结论: router 的判断可靠吗? 规则版 vs 小模型版哪个好?

=== 提示 ===

- 复用 framework/chat.py 的 stream_chat: 它已返回 (content, usage, finish_reason)
- enable_thinking 是 stream_chat 的参数, M1/M4 传 False, M2/M3 传 True
- 判分要能容错: 模型答案可能带解释/单位, 写个 parse 提取核心答案再比对
  (呼应 04a: 纯 prompt 控制输出格式不可靠)
- latency 掐 stream_chat 整个调用的墙钟时间
- Part 2 router 复用 consts 里的 ollama_base_url / LOCAL_MODEL
- 实验入口放 if __name__ == "__main__"(04e 会复用)
- 数据集小、任务简单没关系, 重点是让"thinking 的成本/收益"可观测、可对比
"""

# ============================================================
# 你的代码写在下面
# ============================================================

import time

from framework.chat import stream_chat

DATASET = [
    ("2 + 2 * 4 的值是多少？", "10"),
    ("计算5的阶乘等于多少?", "120"),
    ("在 Python 中, 执行表达式 len('Hello\n') 的返回值是多少?", "6"),
    ("在 Python 中, 表达式 bool([]) 的布尔值是 True 还是 False?", "False"),
    (
        "树上有 10 只鸟, 猎人开枪打死了 1 只, 树上还剩几只鸟？（提示: 从物理现实和常理考虑, 非数学算术）",
        "0",
    ),
    ("小明妈妈有三个孩子, 大儿子叫大毛, 二儿子叫二毛, 三儿子叫什么?", "小明"),
    ("化学元素周期表中, 原子序数为 1 的元素符号是什么?", "H"),
    ("光在真空中传播的速度大约是每秒多少万公里?（请填写整数）", "30"),
    (
        """
光合作用的主要场所是细胞中的哪个结构？
A. 线粒体
B. 叶绿体
C. 高尔基体
D. 细胞核
（请直接回答选项字母 A、B、C 或 D）
""",
        "B",
    ),
    (
        """
下列哪位科学家提出了广义相对论？
A. 艾萨克·牛顿
B. 尼古拉·特斯拉
C. 阿尔伯特·爱因斯坦
D. 斯蒂芬·霍金
（请直接回答选项字母 A、B、C 或 D）
""",
        "C",
    ),
    (
        "一列长 200 米的火车以 72 km/h 的速度完全通过一座长 800 米的大桥, 从车头上桥到车尾完全离开大桥, 共需要多少秒？",
        "50",
    ),
    (
        """
请问以下 Python 代码最终打印出的数字是多少？
nums = [1, 2, 3, 4, 5]
for i in nums:
    if i % 2 == 0:
        nums.remove(i)
print(len(nums))
""",
        "3",
    ),
    (
        "有 5 顶帽子: 3 顶黑色, 2 顶白色。A、B、C 三人按顺序排成一列, 每个人只能看到前面人的帽子颜色 (C 在最后能看到 A 和 B, B 在中间能看到 A, A 在最前谁也看不到）。给他们戴上帽子后, C 说“我不知道自己是什么颜色”, 接着 B 也说“我也不知道自己是什么颜色”。此时, A 能推断出自己戴的帽子颜色是什么？（填写“黑色”或“白色”）",
        "黑色",
    ),
    (
        "连续抛掷一枚均匀硬币 4 次, 已知“至少有一次正面朝上”, 那么“恰好有二次正面朝上”的概率是多少？（请填写最简分数, 如 a/b)",
        "2/5",
    ),
    (
        "在一个 4*4 的网格（包含 5*5 个交叉点）中, 从左下角 (0,0) 走到右上角 (4,4), 每次只能向右或向上走一步。如果不能经过中间点 (2,2), 一共有多少种不同的最短路径？",
        "34",
    ),
    (
        """
请问以下 Python 代码的输出结果是什么？
funcs = []
for i in range(4):
    funcs.append(lambda x: x * i)
i = 10
print(funcs[1](2))
""",
        "20",
    ),
    (
        "桌上有 23 根火柴, A 和 B 轮流拿, 每次只能拿 1 根、2 根或 3 根, 拿走最后一根火柴的人输。如果 A 先拿, 且双方都采取最优策略, A 第一次应该拿几根火柴？",
        "2",
    ),
    (
        "一个正整数 N, 被 3 除余 2, 被 5 除余 3, 被 7 除余 2。请问满足条件的最小正整数 N 是多少？",
        "23",
    ),
    (
        """
有 4 个开关（标记为 1, 2, 3, 4), 初始状态全为“关”。
操作 A: 按下 1 和 2 的状态；
操作 B: 翻转 2 和 3 的状态；
操作 C: 翻转 3 和 4 的状态；
操作 D: 翻转 1 和 4 的状态。
如果依次执行操作 sequence: A -> C -> B -> D -> A, 最终处于“开”状态的开关编号按从小到大排列是什么？（格式如: 1,3 或 2,4, 若全关则填无）
""",
        "1,2",
    ),
    # --- 追加: 直觉/一步到位会错, 必须多步推理的难题 ---
    (
        "一个家庭有两个孩子（生男生女概率相等且独立）。已知这个家庭中至少有一个男孩, 那么两个孩子都是男孩的概率是多少？（请填写最简分数, 如 a/b)",
        "1/3",
    ),
    (
        "某种疾病在人群中的发病率为 0.1%。有一种检测方法: 患病者检测呈阳性的概率为 99%（真阳性率）, 未患病者检测呈阳性的概率为 1%（假阳性率）。现在某人检测结果为阳性, 请问他真正患病的概率约为多少？（请填写百分数, 四舍五入到整数, 如 1%)",
        "9%",
    ),
    (
        "定义函数 f: f(0)=0, f(1)=1, 当 n>=2 时 f(n)=f(n-1)+f(n-2)。请问 f(10) 的值是多少？",
        "55",
    ),
    (
        """
请问以下 Python 代码最终打印出的数字是多少？
gen = (x * x for x in range(5))
first = list(gen)
second = list(gen)
print(len(second))
""",
        "0",
    ),
    (
        "三扇门后有一辆车和两只羊。你选了一扇门（未打开）。主持人知道门后情况, 他打开了你没选的另外两扇门中的一扇, 露出一只羊。现在他问你要不要换到剩下那扇没开的门。如果你选择换门, 赢得汽车的概率是多少？（请填写最简分数, 如 a/b)",
        "2/3",
    ),
    (
        """
甲、乙、丙三人, 职业分别是医生、老师、律师中的一种（互不相同）。已知:
1) 甲不是医生;
2) 乙既不是老师也不是律师;
3) 丙不是律师。
请问医生是谁？（填“甲”“乙”或“丙”）
""",
        "乙",
    ),
]

SYSTEM_PROMPT = "你是答题助手。请在最终答案中只给出结果本身(如数字、单个字母、单个词或题目指定的格式), 不要在最终答案里包含解释、单位或多余标点。"


def build_direct_prompt(text):
    return text


def build_verify_prompt(text):
    return f"""{text}

  请在思考过程中先验证你的计算或推理是否满足题目所有条件, 但最终答案只输出结果本身, 不要包含验证过程。"""


def build_cot_prompt(text):
    return f"""{text}

  请在思考过程中一步步推理, 但最终答案只输出结果本身, 不要包含推理步骤。"""


def run_config(build_fn, enable_thinking):
    """Run one config over the whole dataset.

    Returns list of per-question records:
        {gt, pred, latency, input_tokens, output_tokens}
    """
    records = []
    for text, gt in DATASET:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_fn(text)},
        ]
        start = time.time()
        content, usage, _ = stream_chat(
            messages=messages,
            enable_thinking=enable_thinking,
            print_content=False,
        )
        latency = time.time() - start
        records.append(
            {
                "gt": gt,
                "pred": content,
                "latency": latency,
                "input_tokens": usage["prompt_tokens"] if usage else 0,
                "output_tokens": usage["completion_tokens"] if usage else 0,
            }
        )
    return records


def summarize(records):
    """Aggregate cost/latency stats across a config's records."""
    n = len(records)
    total_out = sum(r["output_tokens"] for r in records)
    total_in = sum(r["input_tokens"] for r in records)
    total_lat = sum(r["latency"] for r in records)
    return {
        "avg_latency": total_lat / n,
        "avg_output_tokens": total_out / n,
        "total_output_tokens": total_out,
        "total_input_tokens": total_in,
    }


if __name__ == "__main__":
    import contextlib
    import os
    from datetime import datetime, timezone

    configs = {
        "M1": (build_direct_prompt, False),
        "M2": (build_direct_prompt, True),
        "M3": (build_verify_prompt, True),
        "M4": (build_cot_prompt, False),
    }

    out_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "devenv_temp",
        "test_results",
        "week02",
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "04b_reasoning_control.md")

    with open(out_path, "a", encoding="utf-8") as out, contextlib.redirect_stdout(out):
        print(f"\n\n{'#' * 70}")
        print(f"# RUN: {datetime.now(timezone.utc).astimezone():%Y-%m-%d %H:%M:%S %Z}")
        print(f"{'#' * 70}")

        all_stats = {}
        all_records = {}
        for name, config in configs.items():
            records = run_config(*config)
            all_records[name] = records
            all_stats[name] = summarize(records)

        # Cost/latency comparison table (the core finding of 04b)
        print("\n## 成本对比 (accuracy 之外的代价)")
        print("| Mode | avg_latency(s) | avg_output_tokens | total_output_tokens |")
        print("|------|---------------|-------------------|---------------------|")
        for name, s in all_stats.items():
            print(
                f"| {name} | {s['avg_latency']:.2f} | "
                f"{s['avg_output_tokens']:.0f} | {s['total_output_tokens']} |"
            )

        # Per-question details for manual accuracy check
        for name, records in all_records.items():
            print(f"\n## {name} details")
            for r in records:
                print(
                    f"- gt={r['gt']!r} | pred={r['pred']!r} | "
                    f"lat={r['latency']:.2f}s | out_tok={r['output_tokens']}"
                )

    print(f"Output saved to {os.path.relpath(out_path)}")
