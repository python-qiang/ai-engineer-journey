/**
 * 第1周 - 第3节 - 任务2: 用 Node.js fetch 实现流式接收 (SSE)
 *
 * === 本任务完成后你需要掌握的 ===
 *
 * 1. JS 中流式接收的核心 API:
 *    - fetch 返回的 response.body 是一个 ReadableStream
 *    - 用 getReader() 获取 reader, 然后循环 reader.read() 逐块读取
 *    - 用 TextDecoder 把 Uint8Array 转为字符串
 *
 * 2. 与 Python 版本的对应关系:
 *    - Python httpx.stream().iter_lines() ↔ JS reader.read() + 手动按行切分
 *    - 数据格式完全一样: "data: {json}\n\n"
 *    - 解析逻辑一样: 去掉 "data: " 前缀, JSON.parse, 取 delta.content
 *
 * 3. JS 的特殊之处:
 *    - reader.read() 返回的 chunk 不保证按行对齐, 可能需要自己处理 buffer 拼接
 *    - done=true 表示流结束
 *
 * === 本任务不需要关心的 ===
 *
 * - 浏览器中的 EventSource API → 第18周
 * - async generator / for await 语法 → 了解即可
 * - 错误重连机制 → 第15周
 *
 * === 运行方式 ===
 *
 * node src/week01_api_basics/03b_streaming_js.js
 */

// TODO: 你来实现

const API_KEY = process.env.BEIJING_API_KEY;
if (!API_KEY) {
  console.error("错误: BEIJING_API_KEY 未设置, 请确认 direnv 已加载");
  process.exit(1);
}

const API_HOST = process.env.API_HOST;
if (!API_HOST) {
  console.error("错误: API_HOST 未设置, 请确认 direnv 已加载");
  process.exit(1);
}

const URL = `${API_HOST}/compatible-mode/v1/chat/completions`;

/**
 * 流式调用大模型 API, 逐字打印回复。
 *
 * @param {Object} options
 * @param {string} options.message - 用户问题 (必填)
 * @param {string} [options.model="qwen3.6-flash-2026-04-16"] - 模型名称
 * @param {number} [options.temperature=0.7] - 随机性
 * @param {string} [options.systemPrompt="你是一个助手, 回答请保持简洁和专业。"] - 系统提示词
 * @param {boolean} [options.includeUsage=true] - 是否在最后一个 chunk 中返回 token 统计
 * @param {boolean} [options.enableThinking=false] - 是否开启深度思考
 * @param {boolean} [options.printChunks=false] - 是否打印原始 chunk JSON (调试用)
 * @returns {Promise<{content: string, reasoningContent: string, usage: object|null, ttft: number, total_time: number}>}
 */

async function streamChat({
  message,
  model = "qwen3.6-flash-2026-04-16",
  temperature = 0.7,
  systemPrompt = "你是一个助手, 回答请保持简洁和专业。",
  includeUsage = true,
  enableThinking = false,
  printChunks = false,
} = {}) {
  const headers = {
    Authorization: `Bearer ${API_KEY}`,
    "Content-Type": "application/json",
  };

  const payload = {
    model: model,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: message },
    ],
    temperature: temperature,
    stream: true,
    enable_thinking: enableThinking,
  };

  if (includeUsage) {
    payload["stream_options"] = { include_usage: true };
  }

  const startTime = Date.now();
  let firstTokenTime = null;
  let fullContent = "";
  let reasoningDone = false;
  let reasoningContent = "";
  let usage = null;

  const response = await fetch(URL, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`请求失败: HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop(); // 最后一段留着（可能是半行）

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;

      const dataStr = line.slice(6); // 去掉 "data: " 前缀
      if (dataStr == "[DONE]") break;

      const chunk = JSON.parse(dataStr);

      if (printChunks) {
        console.log(`[chunk] ${dataStr}`);
      }

      // include_usage=True 时, 最后一个 chunk: choices=[], 只有 usage
      if (chunk.choices.length === 0) {
        usage = chunk.usage;
        continue;
      }
      const choice = chunk.choices[0];
      const delta = choice.delta ?? {};

      // 思维链内容 (enable_thinking=True 时)
      const reasoning = delta.reasoning_content;
      if (reasoning) {
        if (firstTokenTime === null) {
          firstTokenTime = Date.now();
        }
        process.stdout.write(reasoning);
        reasoningContent += reasoning;
      }

      // 正文内容
      const content = delta.content;
      if (content) {
        if (!reasoningDone && reasoningContent) {
          console.log("\n\n--- 思考完毕，开始回答 ---\n");
          reasoningDone = true;
        }
        if (firstTokenTime === null) {
          firstTokenTime = Date.now();
        }
        process.stdout.write(content);
        fullContent += content;
      }
    }
  }

  const totalTime = Date.now() - startTime;
  const ttft = firstTokenTime ? firstTokenTime - startTime : totalTime;

  console.log(); // 换行

  return {
    content: fullContent,
    reasoningContent: reasoningContent,
    usage: usage,
    ttft: ttft,
    total_time: totalTime,
  };
}

// === 演示 ===
(async () => {
  console.log("=".repeat(60));
  console.log("流式调用演示");
  console.log("=".repeat(60));
  console.log();

  const result = await streamChat({
    message: "用100字介绍什么是SSE (Server-Sent Events)。",
    model: "qwen3.6-plus",
    enableThinking: false,
    includeUsage: false,
  });

  console.log();
  console.log("--- 统计 ---");
  console.log(`TTFT (首字延迟): ${(result.ttft / 1000).toFixed(2)}s`);
  console.log(`总耗时: ${(result.total_time / 1000).toFixed(2)}s`);
  console.log(`输出长度: ${result.content.length} 字符`);
  if (result.usage) {
    const u = result.usage;
    console.log(
      `Token 消耗: 输入 ${u.prompt_tokens} + 输出 ${u.completion_tokens} = ${u.total_tokens}`,
    );
  }
  if (result.reasoningContent) {
    console.log(`思维链长度: ${result.reasoningContent.length} 字符`);
  }
})();
