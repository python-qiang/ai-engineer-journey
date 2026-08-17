"""
第2周 - 第1节 - 任务2: Messages 数组结构实验

=== 本任务完成后你需要掌握的 ===

1. assistant 角色的用法:
   - 在 messages 数组中插入 assistant 消息, 可以"伪造"对话历史
   - 模型会基于这个虚构的历史继续回答, 实现 few-shot / 风格引导

2. messages 顺序对输出的影响:
   - 标准顺序: system -> user -> assistant -> user -> ...
   - system 放在最前面 = 全局指令, 放在后面遵守度可能下降
   - 模型根据 messages 数组的完整上下文生成回复

3. 构造对话历史的实用技巧:
   - 用 assistant 消息"教"模型输出格式 (few-shot)
   - 用 assistant 消息设定回答风格/语气
   - 用 assistant 消息让模型"接着"上一轮回答继续

=== 本任务不需要关心的 ===

- 真正的多轮对话实现(while循环+历史管理) -> Section 2 会练
- 对话历史的持久化/数据库 -> Section 2

=== 练习 ===

实验 A: 用 assistant 消息构造 few-shot
  - 手动写几组 user+assistant 示例, 然后问新问题
  - 观察模型是否学会了你示范的回答格式

实验 B: 用 assistant 消息设定风格
  - 在 messages 中插入一条 assistant 回复(如用东北话/古文)
  - 观察模型是否延续这个风格

实验 C: messages 顺序实验
  - 同样的内容, 调换 system 和 user 的顺序
  - 观察 system 放在 user 后面时遵守度是否下降

=== 提示 ===

- 复用 01a 中的 chat() 函数, 但这次你需要直接构造完整的 messages 数组
- 关键是理解: messages 就是一个 list, 你可以任意构造
"""

import json
import os

import httpx

from framework.consts import (
    DEFAULT_MODEL,
    LOCAL_WEAK_MODEL,
    beijing_openai_base_http_api_url,
    ollama_base_url,
)

API_KEY = os.environ.get("BEIJING_API_KEY")
if not API_KEY:
    raise RuntimeError("BEIJING_API_KEY 未设置")


def chat_with_messages(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    url: str = beijing_openai_base_http_api_url,
    enable_thinking: bool = True,
    show_thinking: bool = False,
) -> str:
    """直接传入完整的 messages 数组调用 API.

    与 01a 的 chat() 不同, 这里不自动构造 messages,
    而是让调用方完全控制对话结构.
    """
    headers = {"Content-Type": "application/json"}
    if "dashscope" in url:
        headers["Authorization"] = f"Bearer {API_KEY}"

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "enable_thinking": enable_thinking,
    }

    full_content = ""
    reasoning_done = False

    with httpx.stream(
        "POST",
        url,
        headers=headers,
        json=payload,
        timeout=120,
    ) as resp:
        if resp.status_code != 200:
            error = resp.read().decode()
            raise RuntimeError(f"HTTP {resp.status_code}: {error[:200]}")

        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break

            chunk = json.loads(data_str)
            if not chunk["choices"]:
                continue

            delta = chunk["choices"][0].get("delta", {})

            reasoning = delta.get("reasoning_content", "")
            if reasoning and show_thinking:
                print(reasoning, end="", flush=True)

            content = delta.get("content", "")
            if content:
                if not reasoning_done and show_thinking:
                    print("\n--- 思考完毕 ---\n")
                    reasoning_done = True
                print(content, end="", flush=True)
                full_content += content

    print()
    return full_content


if __name__ == "__main__":

    # ============================================================
    # 实验 A: 用 assistant 消息构造 few-shot
    # ============================================================
    print("=" * 60)
    print("实验 A: Few-shot — 用 assistant 历史教模型输出格式")
    print("=" * 60)
    print()

    # 场景: 你想让模型用固定格式 "概念 | 一句话解释 | 例子" 回答
    print("--- 无 few-shot (直接问) ---")
    chat_with_messages([
        {"role": "system", "content": "你是一个编程概念解释助手, 回答控制在50字以内。"},
        {"role": "user", "content": "什么是闭包?"},
    ])
    print()

    print("--- 有 few-shot (先示范格式) ---")
    chat_with_messages([
        {"role": "system", "content": "你是一个编程概念解释助手, 回答控制在50字以内。用固定格式回答。"},
        # few-shot 示例 1
        {"role": "user", "content": "什么是变量?"},
        {"role": "assistant", "content": "概念: 变量\n一句话: 一个指向内存中数据的名字。\n例子: x = 42, 这里 x 就是变量, 指向整数 42。"},
        # few-shot 示例 2
        {"role": "user", "content": "什么是函数?"},
        {"role": "assistant", "content": "概念: 函数\n一句话: 一段可复用的代码块, 接收输入返回输出。\n例子: def add(a, b): return a + b"},
        # 真正的问题
        {"role": "user", "content": "什么是闭包?"},
    ])
    print()

    # ============================================================
    # 实验 B: 用 assistant 消息设定回答风格
    # ============================================================
    print("=" * 60)
    print("实验 B: 风格引导 — 用 assistant 历史设定语气")
    print("=" * 60)
    print()

    print("--- 正常风格 ---")
    chat_with_messages([
        {"role": "system", "content": "你是一个 Python 助手, 回答控制在50字以内。"},
        {"role": "user", "content": "Python 的 GIL 是什么?"},
    ])
    print()

    print("--- 东北话风格 (通过 assistant 示范) ---")
    chat_with_messages([
        {"role": "system", "content": "你是一个 Python 助手, 用东北话回答, 回答控制在50字以内。"},
        # 用一条 assistant 消息示范风格
        {"role": "user", "content": "列表和元组有啥区别?"},
        {"role": "assistant", "content": "哎呀妈呀, 这俩玩意儿区别老大了! 列表就是个能改的筐, 你随便往里扔东西拿东西; 元组就是个封死的盒子, 装好了就别想动了。记住: 列表用方括号[], 元组用圆括号(), 就这么简单, 整不了那花里胡哨的!"},
        # 真正的问题
        {"role": "user", "content": "Python 的 GIL 是什么?"},
    ])
    print()

    print("--- 古文风格 (通过 assistant 示范) ---")
    chat_with_messages([
        {"role": "system", "content": "你是一个 Python 助手, 用文言文回答, 回答控制在50字以内。"},
        {"role": "user", "content": "列表和元组有啥区别?"},
        {"role": "assistant", "content": "列表者, 可增可删之容器也, 以方括号括之; 元组者, 一经铸成便不可更改, 以圆括号括之。二者形似而性异, 用之当审慎择之。"},
        {"role": "user", "content": "Python 的 GIL 是什么?"},
    ])
    print()

    # ============================================================
    # 实验 B2: 用 assistant 消息让模型"接着"回答
    # ============================================================
    print("=" * 60)
    print("实验 B2: 接续 — 用 assistant 消息让模型继续上一轮")
    print("=" * 60)
    print()

    # 场景: 模型上次回答被截断了(或你想让它继续展开), 把上次回复放到 assistant 中
    print("--- 模拟: 上次回答只说了一半, 让模型接着说 ---")
    chat_with_messages([
        {"role": "system", "content": "你是一个编程助手, 回答控制在50字以内。"},
        {"role": "user", "content": "Python 有哪些常用数据结构?"},
        {"role": "assistant", "content": "Python 常用数据结构有: 1. 列表(list) 2. 元组(tuple) 3. 字典(dict)"},
        {"role": "user", "content": "继续"},
    ])
    print()

    # ============================================================
    # 实验 C: Messages 顺序实验
    # ============================================================
    print("=" * 60)
    print("实验 C: Messages 顺序 — system 位置的影响")
    print("=" * 60)
    print()

    system_msg = {"role": "system", "content": "你只能用英文回答, 绝对不能用中文, 回答控制在50字以内。"}
    user_msg = {"role": "user", "content": "什么是递归?"}

    for label, model, url in [
        (f"云端 {DEFAULT_MODEL}", DEFAULT_MODEL, beijing_openai_base_http_api_url),
        (f"本地 {LOCAL_WEAK_MODEL}", LOCAL_WEAK_MODEL, ollama_base_url),
    ]:
        print(f"\n  === {label} ===\n")

        print("--- 标准顺序: [system, user] ---")
        chat_with_messages([system_msg, user_msg], model=model, url=url)
        print()

        print("--- 反转顺序: [user, system] ---")
        chat_with_messages([user_msg, system_msg], model=model, url=url)
        print()

        print("--- system 夹在中间: [user1, system, user2] ---")
        chat_with_messages([
            {"role": "user", "content": "你好"},
            system_msg,
            {"role": "user", "content": "什么是递归?"},
        ], model=model, url=url)
        print()

    # ============================================================
    # 总结
    # ============================================================
    print("=" * 60)
    print("实验总结")
    print("=" * 60)
    print("""
  核心发现:
  1. messages 就是一个普通的 list, 你可以任意构造对话历史
  2. assistant 消息 = "伪造"的模型回复, 模型会当作真实历史来延续
  3. few-shot: 用 user+assistant 示例对教模型输出格式, 比纯文字描述更有效
  4. 风格引导: 一条 assistant 示范比 system prompt 里写"用XX风格"更强
  5. messages 顺序: system 放最前面效果最好, 放后面遵守度可能下降

  实用技巧:
  - 需要固定输出格式? -> few-shot (2-3组示例就够)
  - 需要特定语气/风格? -> system描述 + assistant示范
  - 需要模型接着上文继续? -> 把上一轮的回复放在 assistant 消息里
""")
