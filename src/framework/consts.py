import os

beijing_openai_base_http_api_url = (
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
)
frankfurt_openai_base_http_api_url = "https://ws-cehj6r9ybwddsf52.eu-central-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
ollama_base_url = "http://localhost:11434/v1/chat/completions"

# --- Model names (read from env, change in .env.dev without touching code) ---
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "qwen3.7-plus")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "qwen3:4b")
LOCAL_WEAK_MODEL = os.environ.get("LOCAL_WEAK_MODEL", "qwen2.5:1.5b")
