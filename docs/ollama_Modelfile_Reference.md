# Modelfile 参考文档

Modelfile 是使用 Ollama 创建和分享自定义模型的蓝图。

## 目录

* [格式](#格式)
* [示例](#示例)
* [指令](#指令)
  * [FROM（必需）](#from必需)
  * [PARAMETER](#parameter)
  * [TEMPLATE](#template)
  * [SYSTEM](#system)
  * [ADAPTER](#adapter)
  * [LICENSE](#license)
  * [MESSAGE](#message)
  * [REQUIRES](#requires)
* [注意事项](#注意事项)

## 格式

Modelfile 的格式：

```
# 注释
指令 参数
```

| 指令 | 描述 |
|------|------|
| `FROM`（必需） | 定义要使用的基础模型 |
| `PARAMETER` | 设置 Ollama 运行模型时的参数 |
| `TEMPLATE` | 发送给模型的完整提示词模板 |
| `SYSTEM` | 指定模板中设置的系统消息 |
| `ADAPTER` | 定义要应用于模型的 (Q)LoRA 适配器 |
| `LICENSE` | 指定法律许可证 |
| `MESSAGE` | 指定消息历史 |
| `REQUIRES` | 指定模型所需的最低 Ollama 版本 |

## 示例

### 基本 Modelfile

创建一个 Mario 角色的示例：

```
FROM llama3.2
# 设置温度为 1 [越高越有创意，越低越连贯]
PARAMETER temperature 1
# 设置上下文窗口大小为 4096，控制 LLM 可以使用多少 token 作为上下文来生成下一个 token
PARAMETER num_ctx 4096

# 设置自定义系统消息来指定聊天助手的行为
SYSTEM You are Mario from super mario bros, acting as an assistant.
```

使用方法：

1. 保存为文件（例如 `Modelfile`）
2. `ollama create 自定义模型名 -f <文件路径，如 ./Modelfile>`
3. `ollama run 自定义模型名`
4. 开始使用！

查看已有模型的 Modelfile：

```shell
ollama show --modelfile llama3.2
```

## 指令

### FROM（必需）

定义创建模型时使用的基础模型。

```
FROM <模型名>:<标签>
```

#### 从现有模型构建

```
FROM llama3.2
```

#### 从 Safetensors 模型构建

```
FROM <模型目录>
```

模型目录应包含支持架构的 Safetensors 权重文件。

#### 从 GGUF 文件构建

```
FROM ./ollama-model.gguf
```

GGUF 文件位置应指定为绝对路径或相对于 Modelfile 位置的路径。

### PARAMETER

定义模型运行时可以设置的参数。

```
PARAMETER <参数名> <参数值>
```

#### 有效参数和值

| 参数 | 描述 | 值类型 | 示例 |
|------|------|--------|------|
| num_ctx | 上下文窗口大小（默认: 2048） | int | num_ctx 4096 |
| repeat_last_n | 模型回看多远以防止重复（默认: 64，0=禁用，-1=num_ctx） | int | repeat_last_n 64 |
| repeat_penalty | 重复惩罚强度，越高惩罚越强（默认: 1.1） | float | repeat_penalty 1.1 |
| temperature | 模型温度，越高回答越有创意（默认: 0.8） | float | temperature 0.7 |
| seed | 随机种子，设定后同一 prompt 生成相同文本（默认: 0） | int | seed 42 |
| stop | 停止序列，遇到此模式时 LLM 停止生成。可设置多个 | string | stop "AI assistant:" |
| num_predict | 生成文本时预测的最大 token 数（默认: -1，无限生成） | int | num_predict 42 |
| top_k | 降低生成无意义内容的概率，越高越多样（默认: 40） | int | top_k 40 |
| top_p | 与 top_k 配合，越高文本越多样（默认: 0.9） | float | top_p 0.9 |
| min_p | top_p 的替代方案，表示相对于最可能 token 的最小概率（默认: 0.0） | float | min_p 0.05 |

### TEMPLATE

发送给模型的完整提示词模板。可选地包含系统消息、用户消息和模型回复。使用 Go template 语法。

#### 模板变量

| 变量 | 描述 |
|------|------|
| `{{ .System }}` | 系统消息 |
| `{{ .Prompt }}` | 用户提示消息 |
| `{{ .Response }}` | 模型的回复。生成回复时，此变量之后的文本被省略 |

```
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
```

### SYSTEM

指定模板中使用的系统消息。

```
SYSTEM """<系统消息>"""
```

### ADAPTER

指定要应用于基础模型的微调 LoRA 适配器。值应为绝对路径或相对于 Modelfile 的路径。基础模型需用 FROM 指令指定。

#### Safetensor 适配器

```
ADAPTER <safetensor 适配器路径>
```

#### GGUF 适配器

```
ADAPTER ./ollama-lora.gguf
```

### LICENSE

指定模型的法律许可证。

```
LICENSE """
<许可证文本>
"""
```

### MESSAGE

指定模型响应时使用的消息历史。使用多个 MESSAGE 命令构建对话，引导模型以类似方式回答。

```
MESSAGE <角色> <消息>
```

#### 有效角色

| 角色 | 描述 |
|------|------|
| system | 提供系统消息的替代方式 |
| user | 用户可能提问的示例 |
| assistant | 模型应如何回复的示例 |

#### 示例对话

```
MESSAGE user 多伦多在加拿大吗？
MESSAGE assistant 是的
MESSAGE user 萨克拉门托在加拿大吗？
MESSAGE assistant 不是
MESSAGE user 安大略在加拿大吗？
MESSAGE assistant 是的
```

### REQUIRES

指定模型所需的最低 Ollama 版本。

```
REQUIRES <版本号>
```

版本应为有效的 Ollama 版本号（如 0.14.0）。

## 注意事项

* **Modelfile 不区分大小写**。示例中使用大写指令是为了便于与参数区分。
* 指令可以按任意顺序排列。示例中 FROM 指令放在最前面是为了便于阅读。
