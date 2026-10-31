import anthropic

from anki_cards_creator.domain import CardOptions, GenerationError
from anki_cards_creator.llm.prompts import SYSTEM_PROMPT, build_user_prompt


class ClaudeCardGenerator:
    def __init__(self, client: anthropic.Anthropic, model: str, effort: str) -> None:
        self._client = client
        self._model = model
        self._effort = effort

    def generate(self, word: str, level: str) -> CardOptions:
        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                output_config={"effort": self._effort},
                messages=[{"role": "user", "content": build_user_prompt(word, level)}],
                output_format=CardOptions,
            )
        except anthropic.AuthenticationError as e:
            raise GenerationError("The Anthropic API key was rejected.") from e
        except anthropic.RateLimitError as e:
            raise GenerationError("Rate limited by the Claude API. Try again shortly.") from e
        except anthropic.APIStatusError as e:
            raise GenerationError(f"Claude API error ({e.status_code}). Try again.") from e
        except anthropic.APIConnectionError as e:
            raise GenerationError("Could not reach the Claude API. Check your connection.") from e

        if response.stop_reason == "refusal":
            raise GenerationError("Claude declined to generate cards for this word.")
        if response.stop_reason == "max_tokens":
            raise GenerationError("The response was cut off. Try again.")
        if response.parsed_output is None:
            raise GenerationError("Claude returned no usable cards. Try again.")
        return response.parsed_output
