import re
from functools import lru_cache

from qwen_tokenizer import get_tokenizer, list_tokenizers

from framework.consts import DEFAULT_MODEL

# Chat template overhead per message:
# <|im_start|>(1) + role(1) + \n(1) + <|im_end|>(1) + \n(1) = 5
_MSG_OVERHEAD = 5
# Assistant generation prompt: <|im_start|>(1) + assistant(1) + \n(1) = 3
_ASSISTANT_PROMPT = 3
# API internal overhead (thinking mode related, fixed)
_API_OVERHEAD = 4


def count_message_tokens(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
) -> int:
    """Count tokens for a messages array, including chat template overhead."""
    if not messages:
        return 0
    tokenizer = _resolve_tokenizer(model)
    return (
        sum(
            len(tokenizer.encode(msg.get("content", ""))) + _MSG_OVERHEAD
            for msg in messages
        )
        + _ASSISTANT_PROMPT
        + _API_OVERHEAD
    )


@lru_cache(maxsize=4)
def _resolve_tokenizer(model: str = DEFAULT_MODEL):
    """Auto-resolve tokenizer by model generation, like AutoTokenizer."""
    available = list_tokenizers()

    # Exact match
    if model in available:
        return get_tokenizer(model)

    # Match by major version: "qwen3.7-plus" -> major "3"
    match = re.match(r"qwen(\d+)", model)
    if match:
        major = match.group(1)
        candidates = [t for t in available if re.match(rf"qwen{major}[\.\-]", t)]
        if candidates:
            return get_tokenizer(candidates[-1])

    # Fallback: newest available
    return get_tokenizer(available[-1])
