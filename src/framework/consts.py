import os

# API host is workspace-specific (contains your workspace ID).
# Set API_HOST in .env.dev, e.g.
#   https://llm-xxxxxx.cn-beijing.maas.aliyuncs.com
# The legacy public host (dashscope.aliyuncs.com) is being deprecated by Alibaba.
_api_host = os.environ.get("API_HOST", "")

beijing_openai_base_http_api_url = f"{_api_host}/compatible-mode/v1/chat/completions"
ollama_base_url = "http://localhost:11434/v1/chat/completions"

# --- Model names (read from env, change in .env.dev without touching code) ---
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "qwen3.7-plus")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "qwen3:4b")
LOCAL_WEAK_MODEL = os.environ.get("LOCAL_WEAK_MODEL", "qwen2.5:1.5b")
