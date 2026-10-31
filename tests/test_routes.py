import re

import pytest
from fastapi.testclient import TestClient

from anki_cards_creator.domain import LEVELS
from anki_cards_creator.main import create_app
from anki_cards_creator.service import CardService
from tests.fakes import FakeAnki, FakeGenerator, make_card


def make_client(
    generator: FakeGenerator | None = None,
    anki: FakeAnki | None = None,
    default_deck: str = "",
) -> TestClient:
    service = CardService(generator or FakeGenerator(), anki or FakeAnki(), default_deck)
    return TestClient(create_app(service))


def card_form(front: str = "money", deck: str = "Default", **overrides) -> dict:
    return make_card(front).model_dump() | {"deck": deck} | overrides


def test_index_loads():
    response = make_client().get("/")

    assert response.status_code == 200
    assert "Anki Cards Creator" in response.text
    assert re.findall(r'<option value="(\w+)"', response.text) == LEVELS
    assert '<option value="B1" selected>' in response.text


def test_anki_status_shows_banner_only_when_offline():
    assert "Can't reach Anki" not in make_client().get("/health/anki").text
    offline = make_client(anki=FakeAnki(available=False))
    assert "Can't reach Anki" in offline.get("/health/anki").text


def test_deck_selector_survives_offline_anki():
    response = make_client(anki=FakeAnki(available=False)).get("/decks")

    assert response.status_code == 200
    assert "reach Anki" in response.text


def test_default_deck_is_preselected():
    anki = FakeAnki()
    anki.decks = ["Default", "German"]

    response = make_client(anki=anki, default_deck="German").get("/decks")

    assert '<option value="German" selected>' in response.text


def test_no_default_deck_leaves_placeholder_selected():
    assert " selected>" not in make_client().get("/decks").text


def test_generate_renders_editable_options_and_does_not_touch_anki():
    generator = FakeGenerator([make_card("river edge"), make_card("money")])
    anki = FakeAnki()

    response = make_client(generator, anki).post(
        "/options", data={"word": " bank ", "level": "A2"}
    )

    assert generator.calls == [("bank", "A2")]
    assert response.text.count("<form") == 2
    assert response.text.count("Add to Anki") == 2
    assert 'name="front_text" value="money"' in response.text
    assert anki.added == []


def test_card_shows_formatted_text_without_tick_or_word():
    generator = FakeGenerator([make_card("Mein <b><i>Urlaubstyp</i></b> ist ruhig.")])

    response = make_client(generator).post("/options", data={"word": "bank"})

    assert ">Mein <b><i>Urlaubstyp</i></b> ist ruhig.</div>" in response.text
    assert "checkbox" not in response.text
    assert ">bank<" not in response.text


def test_level_defaults_to_b1():
    generator = FakeGenerator()

    make_client(generator).post("/options", data={"word": "bank"})

    assert generator.calls == [("bank", "B1")]


def test_unknown_level_is_rejected():
    generator = FakeGenerator()

    response = make_client(generator).post("/options", data={"word": "bank", "level": "C2"})

    assert generator.calls == []
    assert "Choose a level" in response.text


def test_generated_content_is_escaped_in_the_page():
    generator = FakeGenerator([make_card(back_text="<script>alert(1)</script>")])

    response = make_client(generator).post("/options", data={"word": "bank"})

    assert "<script>alert" not in response.text
    assert "&lt;script&gt;alert(1)" in response.text


@pytest.mark.parametrize("word", ["", "   ", "x" * 101])
def test_invalid_word_is_rejected(word):
    generator = FakeGenerator()

    response = make_client(generator).post("/options", data={"word": word})

    assert generator.calls == []
    assert "Enter a word" in response.text


def test_generation_error_is_shown():
    response = make_client(FakeGenerator(error="Claude declined.")).post(
        "/options", data={"word": "bank"}
    )

    assert "Claude declined." in response.text


def test_adding_a_card_greys_it_out_and_keeps_it_on_the_page():
    anki = FakeAnki()

    response = make_client(anki=anki).post("/cards", data=card_form(back_text="edited back"))

    assert [(deck, card.front_text, card.back_text) for deck, card, _ in anki.added] == [
        ("Default", "money", "edited back")
    ]
    assert 'class="card added"' in response.text
    assert "disabled>Added</button>" in response.text
    assert "edited back" in response.text
    assert "contenteditable" not in response.text


def test_missing_deck_keeps_card_editable():
    anki = FakeAnki()

    response = make_client(anki=anki).post("/cards", data=card_form(deck=""))

    assert anki.added == []
    assert "Choose a deck" in response.text
    assert "contenteditable" in response.text


def test_offline_anki_keeps_card_for_retry():
    response = make_client(anki=FakeAnki(available=False)).post("/cards", data=card_form())

    assert "reach Anki" in response.text
    assert 'class="card added"' not in response.text
    assert "Add to Anki" in response.text


def test_refreshing_decks_keeps_selection():
    anki = FakeAnki()
    anki.decks = ["Default", "German"]
    client = make_client(anki=anki, default_deck="German")

    response = client.get("/decks", params={"deck": "Default"})

    assert '<option value="Default" selected>' in response.text


def test_duplicate_can_be_added_anyway():
    anki = FakeAnki(duplicate_fronts=("money",))
    client = make_client(anki=anki)

    response = client.post("/cards", data=card_form())

    assert anki.added == []
    assert "Already in Anki" in response.text
    assert "Add anyway" in response.text
    assert 'name="allow_duplicates" value="true"' in response.text

    client.post("/cards", data=card_form(allow_duplicates="true"))

    assert [card.front_text for _, card, _ in anki.added] == ["money"]
