# Anki Cards Creator

Enter a word, choose from LLM-generated card options, and add the ones you approve to an Anki deck.
See [ARCHITECTURE.md](ARCHITECTURE.md) for the design.

## Setup

1. Install [AnkiConnect](https://ankiweb.net/shared/info/2055492159) in Anki (add-on code `2055492159`) and restart Anki.
2. Copy `.env.example` to `.env` and fill in `ANTHROPIC_API_KEY`. Set `DEFAULT_DECK` to an existing Anki deck to preselect it.

## Run

Keep Anki open, then run:

```sh
uv run anki-cards-creator
```

Open <http://127.0.0.1:8000>.

## Test

```sh
uv run pytest
```
