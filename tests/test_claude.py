from types import SimpleNamespace

import pytest

from anki_cards_creator.domain import CardOptions, GenerationError
from anki_cards_creator.llm.claude import ClaudeCardGenerator
from tests.fakes import make_card


def make_generator(stop_reason: str, parsed_output: CardOptions | None):
    response = SimpleNamespace(stop_reason=stop_reason, parsed_output=parsed_output)
    calls = []

    def parse(**kwargs):
        calls.append(kwargs)
        return response

    client = SimpleNamespace(messages=SimpleNamespace(parse=parse))
    return ClaudeCardGenerator(client, "claude-haiku-5-5", "low"), calls


def test_generate_returns_parsed_options_and_sends_settings():
    options = CardOptions(options=[make_card()])
    generator, calls = make_generator("end_turn", options)

    assert generator.generate("bank", "A2") == options
    assert calls[0]["model"] == "claude-haiku-5-5"
    assert calls[0]["output_config"] == {"effort": "low"}
    assert calls[0]["output_format"] is CardOptions
    assert calls[0]["messages"][0]["content"] == "Level: A2\n<word>bank</word>"


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_incomplete_responses_are_errors(stop_reason):
    generator, _ = make_generator(stop_reason, CardOptions(options=[make_card()]))

    with pytest.raises(GenerationError):
        generator.generate("bank", "A2")


def test_missing_output_is_an_error():
    generator, _ = make_generator("end_turn", None)

    with pytest.raises(GenerationError):
        generator.generate("bank", "A2")
