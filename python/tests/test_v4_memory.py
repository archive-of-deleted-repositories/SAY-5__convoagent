from __future__ import annotations

from convoagent.memory import Memory, extract


def test_extract_email() -> None:
    f = extract("you can reach me at alice@example.com any time")
    assert f["email"] == "alice@example.com"


def test_extract_order_id_with_hash() -> None:
    f = extract("my order #ABC-1234 hasn't arrived")
    assert f["order_id"] == "ABC-1234"


def test_extract_version() -> None:
    f = extract("hit a bug in v1.2.3 of the app")
    assert f["version"] == "1.2.3"


def test_memory_overwrites_on_correction() -> None:
    m = Memory()
    m.update_from("my email is old@example.com")
    m.update_from("oh sorry, my email is new@example.com")
    assert m.get("email") == "new@example.com"


def test_memory_render_summarizes_facts() -> None:
    m = Memory()
    m.update_from("order #42, email alice@x.com")
    rendered = m.render()
    assert "order_id=42" in rendered
    assert "email=alice@x.com" in rendered


def test_memory_has_returns_bool() -> None:
    m = Memory()
    assert not m.has("email")
    m.update_from("alice@x.com")
    assert m.has("email")


def test_no_extraction_returns_empty_dict() -> None:
    f = extract("just chatting, nothing structured to share")
    assert f == {}
