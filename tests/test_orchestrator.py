"""Orchestrator — mock OpenAI client, fence extract, no network."""
import json
import types
import pytest
from core.ai_orchestrator import AIOrchestrator, _extract_json


# ---------- _extract_json fence / prose ----------

def test_extract_json_direct_object():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_direct_array():
    assert _extract_json('[1,2,3]') == [1, 2, 3]


def test_extract_json_fence_json():
    assert _extract_json('```json\n{"x": 123}\n```') == {"x": 123}


def test_extract_json_fence_no_lang():
    assert _extract_json('```\n{"y": 2}\n```') == {"y": 2}


def test_extract_json_prose_before_and_after():
    txt = 'Here is result: {"niche": "parenting"} thanks'
    assert _extract_json(txt) == {"niche": "parenting"}


def test_extract_json_array_inside_prose():
    txt = 'result is [{"a":1},{"a":2}] end'
    assert _extract_json(txt) == [{"a": 1}, {"a": 2}]


def test_extract_json_empty_returns_none():
    assert _extract_json("") is None
    assert _extract_json("   ") is None
    assert _extract_json(None) is None  # type: ignore


def test_extract_json_invalid_returns_none():
    assert _extract_json("not json at all") is None


def test_extract_json_trailing_text_after_fence():
    txt = '```json\n{"sources": [{"url": "https://youtu.be/x", "type": "youtube"}]}\n``` extra'
    v = _extract_json(txt)
    assert isinstance(v, dict)
    assert v["sources"][0]["type"] == "youtube"


# ---------- helpers to mock OpenAI client ----------

class _FakeMessage:
    def __init__(self, content):
        self.content = content

class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)

class _FakeResp:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]

class _FakeCompletions:
    def __init__(self, content=None, exc=None):
        self._content = content
        self._exc = exc
        self.last_kwargs = None
    def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self._exc:
            raise self._exc
        return _FakeResp(self._content)

class _FakeChat:
    def __init__(self, content=None, exc=None):
        self.completions = _FakeCompletions(content, exc)

class _FakeClient:
    def __init__(self, content=None, exc=None):
        self.chat = _FakeChat(content, exc)


def _make_orchestrator_with_fake(content=None, exc=None):
    orch = AIOrchestrator({"brief_parser": {"api_key": "sk-test", "model": "gpt-4o-mini", "base_url": "https://api.openai.com/v1"}})
    fake = _FakeClient(content=content, exc=exc)
    orch._clients["brief_parser"] = fake  # inject, bypass real OpenAI()
    return orch, fake


def test_chat_json_parses_fence():
    orch, fake = _make_orchestrator_with_fake(content='```json\n{"sources": [{"url": "https://youtu.be/AAA111AAA11", "type": "youtube"}], "niche": "comedy"}\n```')
    res = orch.chat_json("brief_parser", None, "prompt", fallback=None)
    assert res["niche"] == "comedy"
    assert res["sources"][0]["type"] == "youtube"


def test_chat_json_direct_json():
    orch, fake = _make_orchestrator_with_fake(content='{"niche": "business", "sources": []}')
    res = orch.chat_json("brief_parser", None, "prompt", fallback={"fallback": True})
    assert res["niche"] == "business"


def test_chat_json_non_json_returns_fallback():
    orch, fake = _make_orchestrator_with_fake(content='not json at all')
    res = orch.chat_json("brief_parser", None, "prompt", fallback={"fallback": True})
    assert res == {"fallback": True}


def test_chat_json_empty_content_returns_fallback():
    orch, fake = _make_orchestrator_with_fake(content='')
    res = orch.chat_json("brief_parser", None, "prompt", fallback="FB")
    assert res == "FB"


def test_chat_json_exception_returns_fallback():
    orch, fake = _make_orchestrator_with_fake(exc=RuntimeError("timeout"))
    res = orch.chat_json("brief_parser", None, "prompt", fallback="FALLBACK")
    assert res == "FALLBACK"


def test_chat_json_no_api_key_returns_fallback_without_call():
    orch = AIOrchestrator({"brief_parser": {"api_key": "", "model": "gpt-4o-mini"}})
    # no client injected, _client will return None due to missing api_key
    res = orch.chat_json("brief_parser", None, "prompt", fallback="NOKEY")
    assert res == "NOKEY"


def test_chat_json_missing_provider_returns_fallback():
    orch = AIOrchestrator({})
    res = orch.chat_json("unknown", None, "prompt", fallback=123)
    assert res == 123


def test_chat_json_prose_wrapped_array_extracted():
    orch, fake = _make_orchestrator_with_fake(content='Here you go: [{"title": "A"}, {"title": "B"}] done')
    res = orch.chat_json("brief_parser", None, "prompt", fallback=None)
    assert isinstance(res, list) and res[0]["title"] == "A"


def test_chat_json_sends_model_and_messages(monkeypatch):
    orch, fake = _make_orchestrator_with_fake(content='{"ok": true}')
    # use system message
    orch.chat_json("brief_parser", "you are helper", "user prompt", fallback=None)
    kwargs = fake.chat.completions.last_kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert any(m["role"] == "system" and "helper" in m["content"] for m in kwargs["messages"])
    assert any(m["role"] == "user" for m in kwargs["messages"])
