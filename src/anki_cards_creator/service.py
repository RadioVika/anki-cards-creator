from anki_cards_creator.anki.base import AnkiGateway
from anki_cards_creator.domain import AddResult, CardContent, CardOptions
from anki_cards_creator.llm.base import CardGenerator


class CardService:
    def __init__(self, generator: CardGenerator, anki: AnkiGateway, default_deck: str = "") -> None:
        self._generator = generator
        self._anki = anki
        self.default_deck = default_deck

    def anki_available(self) -> bool:
        return self._anki.is_available()

    def list_decks(self) -> list[str]:
        return self._anki.list_decks()

    def generate_options(self, word: str, level: str) -> CardOptions:
        return self._generator.generate(word, level)

    def approve_cards(
        self, deck: str, cards: list[CardContent], allow_duplicates: bool = False
    ) -> list[AddResult]:
        return self._anki.add_cards(deck, cards, allow_duplicates)
