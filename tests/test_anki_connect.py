import json

import httpx
import pytest

from anki_cards_creator.anki.anki_connect import AnkiConnectGateway
from anki_cards_creator.anki.note_type import MODEL_NAME, to_html
from anki_cards_creator.domain import AnkiError, AnkiUnavailableError
from tests.fakes import make_card


def make_gateway(responses: dict[str, object], calls: list[dict] | None = None):
    calls = calls if calls is not None else []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        outcome = responses[payload["action"]]
        if isinstance(outcome, Exception):
            return httpx.Response(200, json={"result": None, "error": str(outcome)})
        return httpx.Response(200, json={"result": outcome, "error": None})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://anki")
    return AnkiConnectGateway(client)


def offline_gateway() -> AnkiConnectGateway:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    return AnkiConnectGateway(
        httpx.Client(transport=httpx.MockTransport(handler), base_url="http://anki")
    )


def test_list_decks_sends_v6_request_and_sorts():
    calls = []
    gateway = make_gateway({"deckNames": ["b", "a"]}, calls)

    assert gateway.list_decks() == ["a", "b"]
    assert calls == [{"action": "deckNames", "version": 6, "params": {}}]


def test_anki_error_is_raised():
    gateway = make_gateway({"deckNames": Exception("bad deck")})

    with pytest.raises(AnkiError, match="bad deck"):
        gateway.list_decks()


def test_offline_anki():
    gateway = offline_gateway()

    assert gateway.is_available() is False
    with pytest.raises(AnkiUnavailableError):
        gateway.list_decks()


def test_add_cards_creates_missing_note_type():
    calls = []
    gateway = make_gateway({"modelNames": ["Basic"], "createModel": {}, "addNote": 7}, calls)

    results = gateway.add_cards("Deck", [make_card()])

    assert [c["action"] for c in calls] == ["modelNames", "createModel", "addNote"]
    assert results[0].status == "created"
    assert results[0].note_id == 7


def test_created_note_type_is_one_sided():
    calls = []
    gateway = make_gateway({"modelNames": [], "createModel": {}, "addNote": 7}, calls)

    gateway.add_cards("Deck", [make_card()])

    params = calls[1]["params"]
    assert params["modelName"] == MODEL_NAME
    assert params["inOrderFields"] == ["Front", "Back"]
    assert len(params["cardTemplates"]) == 1


def test_add_cards_skips_existing_note_type():
    calls = []
    gateway = make_gateway({"modelNames": [MODEL_NAME], "addNote": 7}, calls)

    gateway.add_cards("Deck", [make_card()])

    assert [c["action"] for c in calls] == ["modelNames", "addNote"]


def test_note_fields_are_html_escaped():
    calls = []
    gateway = make_gateway({"modelNames": [MODEL_NAME], "addNote": 7}, calls)

    gateway.add_cards("Deck", [make_card(back_text="<u>under</u> & more")], allow_duplicates=True)

    note = calls[-1]["params"]["note"]
    assert note["modelName"] == MODEL_NAME
    assert note["fields"] == {
        "Front": "river edge",
        "Back": "&lt;u&gt;under&lt;/u&gt; &amp; more",
    }
    assert note["options"] == {"allowDuplicate": True}


def test_formatting_tags_are_kept_in_note_fields():
    calls = []
    gateway = make_gateway({"modelNames": [MODEL_NAME], "addNote": 7}, calls)
    back_text = "<b><i>anbieten</i></b> — предлагать<br><small>bietet an</small>"

    gateway.add_cards("Deck", [make_card(front_text="<b><i>Bank</i></b>", back_text=back_text)])

    assert calls[-1]["params"]["note"]["fields"] == {
        "Front": "<b><i>Bank</i></b>",
        "Back": back_text,
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("<b onclick='x()'>a</b>", "&lt;b onclick='x()'&gt;a</b>"),
        ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
        ("<img src=x onerror=y>", "&lt;img src=x onerror=y&gt;"),
        ("&lt;b&gt;", "&amp;lt;b&amp;gt;"),
    ],
)
def test_unsafe_markup_stays_escaped(text, expected):
    assert to_html(text) == expected


def test_line_breaks_are_kept_in_note_fields():
    calls = []
    gateway = make_gateway({"modelNames": [MODEL_NAME], "addNote": 7}, calls)

    gateway.add_cards("Deck", [make_card(back_text="берег\r\nbank — берег\nder Bank, -e")])

    assert calls[-1]["params"]["note"]["fields"]["Back"] == "берег<br>bank — берег<br>der Bank, -e"


def test_duplicate_and_failure_are_reported_per_card():
    gateway = make_gateway(
        {
            "modelNames": [MODEL_NAME],
            "addNote": Exception("cannot create note because it is a duplicate"),
        }
    )
    assert gateway.add_cards("Deck", [make_card()])[0].status == "duplicate"

    gateway = make_gateway({"modelNames": [MODEL_NAME], "addNote": Exception("deck missing")})
    result = gateway.add_cards("Deck", [make_card()])[0]
    assert result.status == "failed"
    assert result.error == "deck missing"
