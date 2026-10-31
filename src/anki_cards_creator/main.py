import sys
from pathlib import Path

import anthropic
import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from anki_cards_creator.anki.anki_connect import AnkiConnectGateway
from anki_cards_creator.config import Settings
from anki_cards_creator.llm.claude import ClaudeCardGenerator
from anki_cards_creator.service import CardService
from anki_cards_creator.web.routes import router

HOST = "127.0.0.1"
PORT = 8000
ANKI_TIMEOUT_SECONDS = 10


def build_service(settings: Settings) -> CardService:
    generator = ClaudeCardGenerator(
        anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value()),
        settings.llm_model,
        settings.llm_effort,
    )
    anki = AnkiConnectGateway(
        httpx.Client(base_url=settings.anki_connect_url, timeout=ANKI_TIMEOUT_SECONDS)
    )
    return CardService(generator, anki, settings.default_deck)


def create_app(service: CardService | None = None) -> FastAPI:
    app = FastAPI(title="Anki Cards Creator")
    app.state.service = service or build_service(Settings())
    app.mount(
        "/static", StaticFiles(directory=Path(__file__).parent / "web" / "static"), name="static"
    )
    app.include_router(router)
    return app


def main() -> None:
    try:
        Settings()
    except ValidationError as e:
        missing = ", ".join(str(error["loc"][0]).upper() for error in e.errors())
        sys.exit(f"Missing or invalid settings: {missing}. Set them in .env (see .env.example).")
    uvicorn.run("anki_cards_creator.main:create_app", factory=True, host=HOST, port=PORT)
