from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from anki_cards_creator.anki.note_type import to_html
from anki_cards_creator.domain import DEFAULT_LEVEL, LEVELS, AppError, CardContent
from anki_cards_creator.service import CardService

MAX_WORD_LENGTH = 100

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.filters["card_html"] = lambda text: Markup(to_html(text))
router = APIRouter()


def get_service(request: Request) -> CardService:
    return request.app.state.service


Service = Annotated[CardService, Depends(get_service)]


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "index.html", {"levels": LEVELS, "default_level": DEFAULT_LEVEL}
    )


@router.get("/health/anki", response_class=HTMLResponse)
def anki_status(request: Request, service: Service) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "anki_status.html", {"available": service.anki_available()}
    )


@router.get("/decks", response_class=HTMLResponse)
def decks(request: Request, service: Service, deck: str = "") -> HTMLResponse:
    names, error = [], ""
    try:
        names = service.list_decks()
    except AppError as e:
        error = str(e)
    selected = deck or service.default_deck
    return templates.TemplateResponse(
        request, "decks.html", {"decks": names, "selected": selected, "error": error}
    )


@router.post("/options", response_class=HTMLResponse)
def generate_options(
    request: Request,
    service: Service,
    word: Annotated[str, Form()] = "",
    level: Annotated[str, Form()] = DEFAULT_LEVEL,
) -> HTMLResponse:
    word = word.strip()
    if not word or len(word) > MAX_WORD_LENGTH:
        message = f"Enter a word of up to {MAX_WORD_LENGTH} characters."
        return render_options(request, [], error=message)
    if level not in LEVELS:
        return render_options(request, [], error=f"Choose a level: {', '.join(LEVELS)}.")
    try:
        cards = service.generate_options(word, level).options
    except AppError as e:
        return render_options(request, [], error=str(e))
    return render_options(request, cards)


@router.post("/cards", response_class=HTMLResponse)
def add_card(
    request: Request,
    service: Service,
    word: Annotated[str, Form()] = "",
    front_text: Annotated[str, Form()] = "",
    back_text: Annotated[str, Form()] = "",
    deck: Annotated[str, Form()] = "",
    allow_duplicates: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    card = CardContent(
        word=word.strip(), front_text=front_text.strip(), back_text=back_text.strip()
    )
    deck = deck.strip()

    if not deck:
        return render_card(request, card, error="Choose a deck first.")
    try:
        result = service.approve_cards(deck, [card], allow_duplicates)[0]
    except AppError as e:
        return render_card(request, card, error=str(e))
    return render_card(request, card, status=result.status, error=result.error)


def render_options(request: Request, cards: list[CardContent], **context) -> HTMLResponse:
    return templates.TemplateResponse(request, "options.html", {"cards": cards, **context})


def render_card(request: Request, card: CardContent, **context) -> HTMLResponse:
    return templates.TemplateResponse(request, "card.html", {"card": card, **context})
