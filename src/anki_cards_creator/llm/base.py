from typing import Protocol

from anki_cards_creator.domain import CardOptions


class CardGenerator(Protocol):
    def generate(self, word: str, level: str) -> CardOptions: ...
