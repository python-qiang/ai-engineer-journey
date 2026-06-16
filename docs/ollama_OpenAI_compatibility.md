# OpenAI 兼容性

Ollama 提供与部分 [OpenAI API](https://platform.openai.com/docs/api-reference) 的兼容性，帮助将现有应用程序连接到 Ollama。

## 用法

### 简单的 `/v1/chat/completions` 示例

```python
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama',  # 必填但会被忽略
)

chat_completion = client.chat.completions.create(
    messages=[{'role': 'user', 'content': 'Say this is a test'}],
    model='gpt-oss:20b',
)
print(chat_completion.choices[0].message.content)
```

```shell
curl -X POST http://localhost:11434/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "gpt-oss:20b",
  "messages": [{ "role": "user", "content": "Say this is a test" }]
}'
```

### 简单的 `/v1/responses` 示例

```python
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama',  # 必填但会被忽略
)

responses_result = client.responses.create(
    model='qwen3:8b',
    input='Write a short poem about the color blue',
)
print(responses_result.output_text)
```

### 带图像的 `/v1/chat/completions` 示例

```python
response = client.chat.completions.create(
    model='qwen3-vl:8b',
    messages=[{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': "What's in this image?"},
            {'type': 'image_url', 'image_url': 'data:image/png;base64,...'},
        ],
    }],
    max_tokens=300,
)
print(response.choices[0].message.content)
```

## 端点

### `/v1/chat/completions`

#### 支持的功能

- [x] 聊天补全
- [x] 流式输出
- [x] JSON 模式
- [x] 可复现输出
- [x] 图像理解 (Vision)
- [x] 工具调用 (Tools)
- [x] 推理/思考控制（用于思考类模型）
- [ ] Logprobs（对数概率）

#### 支持的请求字段

- [x] `model` — 模型名称
- [x] `messages` — 消息数组
  - [x] 文本 `content`
  - [x] 图像 `content`
    - [x] Base64 编码图像
    - [ ] 图像 URL
  - [x] `content` 部分数组
- [x] `frequency_penalty` — 频率惩罚
- [x] `presence_penalty` — 存在惩罚
- [x] `response_format` — 响应格式
- [x] `seed` — 随机种子
- [x] `stop` — 停止序列
- [x] `stream` — 是否流式
- [x] `stream_options`
  - [x] `include_usage` — 包含 token 使用统计
- [x] `temperature` — 温度
- [x] `top_p` — 核采样
- [x] `max_tokens` — 最大输出 token 数
- [x] `tools` — 工具定义
- [x] `reasoning_effort` — 推理强度（`"high"`, `"medium"`, `"low"`, `"none"`）
- [x] `reasoning`
  - [x] `effort` — 推理强度（`"high"`, `"medium"`, `"low"`, `"none"`）
- [ ] `tool_choice`
- [ ] `logit_bias`
- [ ] `user`
- [ ] `n`

### `/v1/completions`

#### 支持的功能

- [x] 文本补全
- [x] 流式输出
- [x] JSON 模式
- [x] 可复现输出
- [ ] Logprobs

#### 支持的请求字段

- [x] `model`
- [x] `prompt` — 目前只接受字符串
- [x] `frequency_penalty`
- [x] `presence_penalty`
- [x] `seed`
- [x] `stop`
- [x] `stream`
- [x] `stream_options`
  - [x] `include_usage`
- [x] `temperature`
- [x] `top_p`
- [x] `max_tokens`
- [x] `suffix`
- [ ] `best_of`
- [ ] `echo`
- [ ] `logit_bias`
- [ ] `user`
- [ ] `n`

### `/v1/models`

#### 备注

- `created` 对应模型最后修改时间
- `owned_by` 对应 ollama 用户名，默认为 `"library"`

### `/v1/models/{model}`

#### 备注

- `created` 对应模型最后修改时间
- `owned_by` 对应 ollama 用户名，默认为 `"library"`

### `/v1/embeddings`

#### 支持的请求字段

- [x] `model`
- [x] `input`
  - [x] 字符串
  - [x] 字符串数组
  - [ ] token 数组
  - [ ] token 数组的数组
- [x] `encoding_format` — 编码格式
- [x] `dimensions` — 维度
- [ ] `user`

### `/v1/images/generations`（实验性）

> 注意：此端点为实验性功能，未来版本可能更改或移除。

使用图像生成模型生成图像。

#### 支持的请求字段

- [x] `model`
- [x] `prompt`
- [x] `size`（如 "1024x1024"）
- [x] `response_format`（仅支持 `b64_json`）
- [ ] `n`
- [ ] `quality`
- [ ] `style`
- [ ] `user`

### `/v1/responses`

> 注意：在 Ollama v0.13.3 中添加

Ollama 支持 [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)。仅支持无状态方式（即不支持 `previous_response_id` 或 `conversation`）。

#### 支持的功能

- [x] 流式输出
- [x] 工具调用（函数调用）
- [x] 推理摘要（用于思考类模型）
- [ ] 有状态请求

#### 支持的请求字段

- [x] `model`
- [x] `input` — 输入内容
- [x] `instructions` — 指令
- [x] `tools` — 工具
- [x] `stream` — 流式
- [x] `temperature` — 温度
- [x] `top_p` — 核采样
- [x] `max_output_tokens` — 最大输出 token 数
- [ ] `previous_response_id`（不支持有状态请求）
- [ ] `conversation`（不支持有状态请求）
- [ ] `truncation`

## 模型

使用模型前，先用 `ollama pull` 拉取到本地：

```shell
ollama pull llama3.2
```

### 默认模型名称

对于依赖默认 OpenAI 模型名称（如 `gpt-3.5-turbo`）的工具，使用 `ollama cp` 复制已有模型到临时名称：

```shell
ollama cp llama3.2 gpt-3.5-turbo
```

之后可以在 `model` 字段中指定这个新模型名：

```shell
curl http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}]
    }'
```

### 设置上下文大小

OpenAI API 没有设置模型上下文大小的方式。如需更改上下文大小，创建一个 `Modelfile`：

```
FROM <某个模型>
PARAMETER num_ctx <上下文大小>
```

使用 `ollama create mymodel` 命令创建带有更新上下文大小的新模型，然后用更新后的模型名调用 API：

```shell
curl http://localhost:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mymodel",
        "messages": [{"role": "user", "content": "Hello!"}]
    }'
```
