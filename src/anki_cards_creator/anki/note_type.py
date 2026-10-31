import re
from html import escape

from anki_cards_creator.domain import CardContent

# Not the name of the earlier five-field model, which may still exist in a collection.
MODEL_NAME = "Anki Cards Creator Basic"

# Anki checks duplicates against the first field, so repeats are matched on Front.
FIELDS = ["Front", "Back"]

TEMPLATE_NAME = "Card 1"

FRONT_TEMPLATE = "{{Front}}"

BACK_TEMPLATE = """\
{{FrontSide}}
<hr id="answer">
{{Back}}"""

CSS = """\
.card { font-family: system-ui, sans-serif; font-size: 20px; text-align: center; }"""

# The tags the system prompt allows, without attributes, in their escaped form.
ESCAPED_ALLOWED_TAG = re.compile(r"&lt;(/?(?:b|i|small)|br\s*/?)&gt;")


def to_fields(card: CardContent) -> dict[str, str]:
    """Build Anki field values, which Anki treats as HTML."""
    return {
        "Front": to_html(card.front_text),
        "Back": to_html(card.back_text),
    }


def to_html(text: str) -> str:
    """Escape text, then restore the formatting tags the LLM is allowed to use."""
    escaped = "<br>".join(escape(text, quote=False).splitlines())
    return ESCAPED_ALLOWED_TAG.sub(r"<\1>", escaped)
