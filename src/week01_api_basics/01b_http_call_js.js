/**
 * 第1周 - 第1节 - 任务2: 用 JavaScript fetch 调用大模型 API
 *
 * === 本任务完成后你需要掌握的 ===
 *
 * 1. 用 Node.js 原生 fetch 发送 POST 请求调用大模型 API
 *    - 与 Python httpx.post 完全对等, 只是语法不同
 *    - 请求体结构 (model, messages, temperature) 完全一样
 *
 * 2. 验证"大模型 API 与语言无关":
 *    - 同一个 URL, 同一个 payload, Python 和 JS 都能调
 *    - 这就是 REST API 的本质: 语言无关, 只要能发 HTTP 请求就行
 *
 * 3. JSON 解析:
 *    - response.json() 解析响应体
 *    - 提取 choices[0].message.content 和 usage
 *
 * === 本任务不需要关心的 ===
 *
 * - 流式输出 (ReadableStream) → 任务3会学
 * - 前端浏览器中的调用 → 第18周
 * - 错误重试/超时控制 → 了解即可
 *
 * === 运行方式 ===
 *
 * 需要 Node.js 18+ (支持原生 fetch):
 *   BEIJING_API_KEY=你的key node src/week01_api_basics/01b_http_call_js.mjs
 *
 * 或者如果 direnv 已加载:
 *   node src/week01_api_basics/01b_http_call_js.mjs
 */

const API_KEY = process.env.BEIJING_API_KEY;
if (!API_KEY) {
  console.error("错误: BEIJING_API_KEY 未设置, 请确认 direnv 已加载");
  process.exit(1);
}

const URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions";

const payload = {
  model: "qwen3.6-flash-2026-04-16",
  messages: [
    { role: "system", content: "你是一个简洁的助手, 回答控制在100字以内。" },
    { role: "user", content: "阿里云百炼是什么？能用来做什么？" },
  ],
  temperature: 1.0,
};

console.log(">>> 发送请求...");
console.log(`    URL: ${URL}`);
console.log(`    Model: ${payload.model}`);
console.log(`    Message: ${payload.messages.at(-1).content}`);
console.log();

const response = await fetch(URL, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify(payload),
});

if (response.ok) {
  const data = await response.json();
  const reply = data.choices[0].message.content;
  const reasoningContent = data.choices[0].message.reasoning_content;
  const usage = data.usage;

  console.log("<<< 回复:");
  console.log(`    思维链内容: ${reasoningContent}`);
  console.log();
  console.log(`    ${reply}`);
  console.log();
  console.log("--- Token 消耗 ---");
  console.log(`    输入: ${usage.prompt_tokens} tokens`);
  console.log(`    输出: ${usage.completion_tokens} tokens`);
  console.log(`    总计: ${usage.total_tokens} tokens`);
} else {
  const errorText = await response.text();
  console.log(`!!! 请求失败: HTTP ${response.status}`);
  console.log(`    ${errorText}`);
}
