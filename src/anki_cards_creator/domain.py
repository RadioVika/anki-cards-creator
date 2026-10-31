from typing import Literal

from pydantic import BaseModel

LEVELS = ["A1", "A2", "B1", "B2", "C1"]
DEFAULT_LEVEL = "B1"


class CardContent(BaseModel):
    word: str
    front_text: str
    back_text: str


class CardOptions(BaseModel):
    options: list[CardContent]


class AddResult(BaseModel):
    card: CardContent
    status: Literal["created", "duplicate", "failed"]
    note_id: int | None = None
    error: str | None = None


class AppError(Exception):
    """A failure with a message that is safe to show in the UI."""


class AnkiUnavailableError(AppError):
    pass


class AnkiError(AppError):
    pass


class GenerationError(AppError):
    pass
