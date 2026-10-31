from typing import Any

import httpx

from anki_cards_creator.anki import note_type
from anki_cards_creator.domain import (
    AddResult,
    AnkiError,
    AnkiUnavailableError,
    AppError,
    CardContent,
)

API_VERSION = 6
DUPLICATE_ERROR = "duplicate"


class AnkiConnectGateway:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def is_available(self) -> bool:
        try:
            self._invoke("version")
        except AppError:
            return False
        return True

    def list_decks(self) -> list[str]:
        return sorted(self._invoke("deckNames"))

    def add_cards(
        self, deck: str, cards: list[CardContent], allow_duplicates: bool = False
    ) -> list[AddResult]:
        self._ensure_note_type()
        return [self._add_card(deck, card, allow_duplicates) for card in cards]

    def _add_card(self, deck: str, card: CardContent, allow_duplicates: bool) -> AddResult:
        note = {
            "deckName": deck,
            "modelName": note_type.MODEL_NAME,
            "fields": note_type.to_fields(card),
            "options": {"allowDuplicate": allow_duplicates},
        }
        try:
            note_id = self._invoke("addNote", note=note)
        except AnkiError as e:
            status = "duplicate" if DUPLICATE_ERROR in str(e) else "failed"
            return AddResult(card=card, status=status, error=str(e))
        except AnkiUnavailableError as e:
            return AddResult(card=card, status="failed", error=str(e))
        return AddResult(card=card, status="created", note_id=note_id)

    def _ensure_note_type(self) -> None:
        if note_type.MODEL_NAME in self._invoke("modelNames"):
            return
        self._invoke(
            "createModel",
            modelName=note_type.MODEL_NAME,
            inOrderFields=note_type.FIELDS,
            css=note_type.CSS,
            cardTemplates=[
                {
                    "Name": note_type.TEMPLATE_NAME,
                    "Front": note_type.FRONT_TEMPLATE,
                    "Back": note_type.BACK_TEMPLATE,
                }
            ],
        )

    def _invoke(self, action: str, **params: Any) -> Any:
        payload = {"action": action, "version": API_VERSION, "params": params}
        try:
            response = self._client.post("/", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise AnkiUnavailableError(
                "Can't reach Anki. Make sure it's open and AnkiConnect is installed."
            ) from e
        body = response.json()
        if body["error"]:
            raise AnkiError(body["error"])
        return body["result"]
