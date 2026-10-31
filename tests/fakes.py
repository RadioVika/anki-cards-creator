from anki_cards_creator.domain import (
    AddResult,
    AnkiUnavailableError,
    CardContent,
    CardOptions,
    GenerationError,
)


def make_card(front_text: str = "river edge", **overrides) -> CardContent:
    fields = {
        "word": "bank",
        "front_text": front_text,
        "back_text": "берег",
    }
    return CardContent(**(fields | overrides))


class FakeGenerator:
    def __init__(self, cards: list[CardContent] | None = None, error: str | None = None) -> None:
        self.cards = cards or []
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def generate(self, word: str, level: str) -> CardOptions:
        self.calls.append((word, level))
        if self.error:
            raise GenerationError(self.error)
        return CardOptions(options=self.cards)


class FakeAnki:
    def __init__(self, available: bool = True, duplicate_fronts: tuple[str, ...] = ()) -> None:
        self.available = available
        self.duplicate_fronts = duplicate_fronts
        self.decks = ["Default"]
        self.added: list[tuple[str, CardContent, bool]] = []

    def is_available(self) -> bool:
        return self.available

    def _require_available(self) -> None:
        if not self.available:
            raise AnkiUnavailableError("Can't reach Anki.")

    def list_decks(self) -> list[str]:
        self._require_available()
        return self.decks

    def add_cards(
        self, deck: str, cards: list[CardContent], allow_duplicates: bool = False
    ) -> list[AddResult]:
        self._require_available()
        results = []
        for card in cards:
            if card.front_text in self.duplicate_fronts and not allow_duplicates:
                results.append(AddResult(card=card, status="duplicate", error="duplicate"))
            else:
                self.added.append((deck, card, allow_duplicates))
                results.append(AddResult(card=card, status="created", note_id=1))
        return results
