"""Generate card options for words with the real Claude API, without Anki or the web app.

Usage: uv run scripts/try_prompt.py Bank Haus [--level A2]
"""

import argparse
import sys

import anthropic
from pydantic import ValidationError

from anki_cards_creator.config import Settings
from anki_cards_creator.domain import DEFAULT_LEVEL, LEVELS, GenerationError
from anki_cards_creator.llm.claude import ClaudeCardGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Try the card prompt on a few words.")
    parser.add_argument("words", nargs="+")
    parser.add_argument("--level", choices=LEVELS, default=DEFAULT_LEVEL)
    return parser.parse_args()


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        missing = ", ".join(str(error["loc"][0]).upper() for error in e.errors())
        sys.exit(f"Missing settings: {missing}. Set them in .env.")


def main() -> None:
    args = parse_args()
    settings = load_settings()
    generator = ClaudeCardGenerator(
        anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value()),
        settings.llm_model,
        settings.llm_effort,
    )

    for word in args.words:
        print(f"\n=== {word}")
        try:
            options = generator.generate(word, args.level)
        except GenerationError as e:
            print(f"ERROR: {e}")
            continue
        for number, card in enumerate(options.options, start=1):
            print(f"\n[{number}] {card.word}")
            print(f"  front text:  {card.front_text}")
            print(f"  back text:     {card.back_text}")


if __name__ == "__main__":
    main()
