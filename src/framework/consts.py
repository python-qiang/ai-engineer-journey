beijing_openai_base_http_api_url = (
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
)
frankfurt_openai_base_http_api_url = "https://ws-cehj6r9ybwddsf52.eu-central-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
ollama_base_url = "http://localhost:11434/v1/chat/completions"

# --- 模型名称 (免费额度用完后在这里统一替换) ---
# 云端主力模型 (用于日常练习)
DEFAULT_MODEL = "qwen3.7-plus"
# 本地 Ollama 模型
LOCAL_MODEL = "qwen3:4b"
# 本地弱模型 (用于对比实验)
LOCAL_WEAK_MODEL = "qwen2.5:1.5b"
