"""Week 2 / Section 4.1 — Zero-shot & Few-shot

Goal:
    Understand how demonstrations change model behavior, and learn to choose
    examples by quantity, quality, order, and boundary coverage.

This task deliberately uses the existing low-level HTTP/chat infrastructure
instead of LangChain or another prompt framework.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Example:
    """A single few-shot demonstration."""

    text: str
    label: str


# Keep the dataset intentionally small: the point of this exercise is to make
# prompt behavior observable, not to build a production classifier.
DATASET: list[Example] = [
    Example("The battery lasts all day and the screen is excellent.", "positive"),
    Example("Setup was easy and the app feels responsive.", "positive"),
    Example("The device stopped charging after two weeks.", "negative"),
    Example("The interface is confusing and slow.", "negative"),
    Example("The camera is okay, but nothing special.", "neutral"),
    Example("It works as expected, although the design is ordinary.", "neutral"),
    # Boundary cases: deliberately mixed or weakly polarized language.
    Example("Good performance, but the battery is disappointing.", "mixed"),
    Example("I expected more for the price, though it is not unusable.", "mixed"),
]


LABELS = {"positive", "negative", "neutral", "mixed"}



def build_zero_shot_prompt(text: str) -> str:
    """Build a zero-shot classification prompt."""

    return f"""Classify the following review into exactly one label:
positive, negative, neutral, or mixed.

Review:
{text}

Return only the label."""



def build_few_shot_prompt(text: str, examples: list[Example]) -> str:
    """Build a few-shot classification prompt from demonstrations."""

    demonstrations = "\n\n".join(
        f"Review: {example.text}\nLabel: {example.label}"
        for example in examples
    )

    return f"""Classify the following review into exactly one label:
positive, negative, neutral, or mixed.

Examples:
{demonstrations}

Now classify:
Review: {text}
Label:"""



def validate_label(label: str) -> bool:
    """Check the semantic label returned by a model."""

    return label.strip().lower() in LABELS


# TODO (student):
# 1. Connect this file to src/framework/chat.py.
# 2. Run the same test cases with zero-shot and few-shot prompts.
# 3. Compare different example counts (1 / 3 / 5).
# 4. Compare random examples against deliberately high-quality examples.
# 5. Change demonstration order and observe whether the result changes.
# 6. Add at least two boundary cases and record failure modes.
# 7. Record accuracy and invalid-label rate for each experiment.
#
# Keep the experiment code simple. Section 4.4 will later extract the common
# execution/evaluation loop into a minimal experiment runner.


if __name__ == "__main__":
    sample = "The product is expensive, but the performance is impressive."

    print("=== Zero-shot ===")
    print(build_zero_shot_prompt(sample))

    print("\n=== Few-shot ===")
    print(build_few_shot_prompt(sample, DATASET[:3]))
