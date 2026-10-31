from typing import Protocol

from anki_cards_creator.domain import AddResult, CardContent


class AnkiGateway(Protocol):
    def is_available(self) -> bool: ...

    def list_decks(self) -> list[str]: ...

    def add_cards(
        self, deck: str, cards: list[CardContent], allow_duplicates: bool = False
    ) -> list[AddResult]: ...
