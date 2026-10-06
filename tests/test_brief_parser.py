"""Rule-based brief parsing — no API, no network."""
from core.brief_parser import _rule_parse, parse_brief


def test_youtube_watch_url():
    r = _rule_parse("cek https://www.youtube.com/watch?v=dQw4w9WgXcQ mantap")
    assert len(r["sources"]) == 1
    assert r["sources"][0]["type"] == "youtube"
    assert "youtube.com/watch" in r["sources"][0]["url"]


def test_youtu_be_short():
    r = _rule_parse("cek https://youtu.be/dQw4w9WgXcQ")
    assert any(s["type"] == "youtube" for s in r["sources"])


def test_gdrive_url():
    url = "https://drive.google.com/file/d/1ABC/view?usp=sharing"
    r = _rule_parse(f"sumber {url} ya")
    assert any(s["type"] == "gdrive" and s["url"] == url for s in r["sources"])


def test_youtube_and_gdrive_both():
    yt = "https://www.youtube.com/watch?v=AAA111AAA11&ab_channel=test"
    gd = "https://drive.google.com/drive/folders/1XYZ?usp=sharing"
    r = _rule_parse(f"{yt} dan {gd}")
    types = [s["type"] for s in r["sources"]]
    assert "youtube" in types and "gdrive" in types


def test_tiktok_sound_id_extracted():
    # tiktok sound_id diambil dari /video/<id>
    url = "https://www.tiktok.com/@user/video/1234567890123456789"
    r = _rule_parse(f"backsound {url}")
    assert r["sound_id"] == "1234567890123456789"


def test_tiktok_no_video_id_no_sound():
    # vt.tiktok.com tanpa /video/ tidak menghasilkan sound_id
    r = _rule_parse("https://vt.tiktok.com/ZSxxxx/")
    assert r["sound_id"] is None


def test_dedup_same_url_once():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    r = _rule_parse(f"{url} dan lagi {url}")
    assert len([s for s in r["sources"] if s["url"] == url]) == 1


def test_empty_brief_defaults():
    r = _rule_parse("")
    assert r["sources"] == []
    assert r["sound_id"] is None
    assert r["hook_style"] == "viral"
    assert r["target_duration"] == "15-90s"
    assert r["niche"] == ""
    assert r["raw_brief"] == ""


def test_none_brief_treated_as_empty():
    r = _rule_parse(None)  # type: ignore
    assert r["sources"] == []


def test_raw_brief_truncated():
    long_text = "x" * 1000
    r = _rule_parse(long_text)
    assert len(r["raw_brief"]) == 500


def test_parse_brief_without_orchestrator_is_rule():
    r = parse_brief("https://youtu.be/AAA111AAA11 niche parenting", orchestrator=None)
    assert any(s["type"] == "youtube" for s in r["sources"])


def test_parse_brief_orchestrator_merges_rule_when_ai_has_no_sources():
    class FakeO:
        def chat_json(self, *a, **kw):
            return {"niche": "parenting", "sources": [], "sound_id": None}

    yt = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    r = parse_brief(f"brief {yt}", orchestrator=FakeO())
    # AI sources kosong -> fallback ke rule
    assert any(s["url"] == yt for s in r["sources"])
    assert r["niche"] == "parenting"


def test_parse_brief_orchestrator_keeps_ai_sources():
    yt = "https://www.youtube.com/watch?v=AAA111AAA11"
    gd = "https://drive.google.com/file/d/1ABC/view"

    class FakeO:
        def chat_json(self, *a, **kw):
            return {"sources": [{"url": yt, "type": "youtube"}], "niche": "comedy", "sound_id": None}

    r = parse_brief(f"ignored {gd}", orchestrator=FakeO())
    # AI punya sources -> dipakai, bukan rule
    assert r["sources"] == [{"url": yt, "type": "youtube"}]


def test_parse_brief_orchestrator_failure_fallback_to_rule():
    class FakeO:
        def chat_json(self, *a, **kw):
            return None

    yt = "https://youtu.be/dQw4w9WgXcQ"
    r = parse_brief(yt, orchestrator=FakeO())
    assert any(s["type"] == "youtube" for s in r["sources"])


def test_parse_brief_orchestrator_returns_raw_brief():
    class FakeO:
        def chat_json(self, *a, **kw):
            return {"sources": [{"url": "https://youtu.be/AAA111AAA11", "type": "youtube"}], "niche": "business"}

    r = parse_brief("hello world", orchestrator=FakeO())
    assert r["raw_brief"] == "hello world"
