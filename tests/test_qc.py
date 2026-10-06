"""QC clip — rule durasi/resolusi/aspect, dummy file + mock probe, no ffprobe."""
import os
import subprocess
import json
import core.qc as qc_mod
from core.qc import qc_clip, _probe


def _dummy(tmp_path, name="clip.mp4", size=6000):
    p = tmp_path / name
    p.write_bytes(b"\x00" * size)
    return str(p)


def test_qc_pass_portrait(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 720, "height": 1280, "duration": 30})
    r = qc_clip(path)
    assert r["pass"] is True
    assert r["issues"] == []
    assert r["meta"] == {"width": 720, "height": 1280, "duration": 30}


def test_qc_fail_too_short(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 720, "height": 1280, "duration": 5})
    r = qc_clip(path)
    assert r["pass"] is False
    assert any("pendek" in i for i in r["issues"])


def test_qc_fail_too_long(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 720, "height": 1280, "duration": 100})
    r = qc_clip(path)
    assert any("panjang" in i for i in r["issues"])


def test_qc_fail_low_resolution(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 480, "height": 400, "duration": 30})
    r = qc_clip(path)
    assert any("resolusi" in i for i in r["issues"])


def test_qc_fail_landscape_aspect(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 1280, "height": 720, "duration": 30})
    r = qc_clip(path)
    assert any("aspect" in i for i in r["issues"])


def test_qc_fail_probe_zero(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 0, "height": 0, "duration": 0})
    r = qc_clip(path)
    assert any("probe gagal" in i for i in r["issues"])


def test_qc_fail_small_file(monkeypatch, tmp_path):
    # probe ok but file <5000 bytes -> issues
    path = _dummy(tmp_path, size=100)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 720, "height": 1280, "duration": 30})
    r = qc_clip(path)
    assert any("kecil" in i for i in r["issues"])
    assert r["pass"] is False


def test_qc_fail_missing_file(monkeypatch, tmp_path):
    missing = str(tmp_path / "nope.mp4")
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 720, "height": 1280, "duration": 30})
    r = qc_clip(missing)
    assert any("kecil" in i or "probe" in i for i in r["issues"])
    assert r["pass"] is False


def test_qc_ai_issues_appended(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 720, "height": 1280, "duration": 30})

    class FakeO:
        def chat_json(self, *a, **kw):
            return {"pass": False, "issues": ["kepala kepotong"]}

    r = qc_clip(path, orchestrator=FakeO(), transcript="halo ini transcript panjang")
    assert "kepala kepotong" in r["issues"]
    assert r["ai_issues"] == ["kepala kepotong"]
    assert r["rule_issues"] == []
    assert r["pass"] is False  # karena ai_issues


def test_qc_ai_pass_no_extra_issues(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 720, "height": 1280, "duration": 30})

    class FakeO:
        def chat_json(self, *a, **kw):
            return {"pass": True, "issues": []}

    r = qc_clip(path, orchestrator=FakeO(), transcript="transcript ok")
    assert r["pass"] is True
    assert r["ai_issues"] == []


def test_qc_ai_not_called_without_transcript(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    monkeypatch.setattr(qc_mod, "_probe", lambda p: {"width": 720, "height": 1280, "duration": 30})

    called = {}

    class FakeO:
        def chat_json(self, *a, **kw):
            called["yes"] = True
            return {"pass": True, "issues": []}

    r = qc_clip(path, orchestrator=FakeO(), transcript="")
    assert "yes" not in called
    assert r["pass"] is True


def test_qc_probe_handles_exception(monkeypatch, tmp_path):
    # _probe should return zeros if ffprobe fails — test via subprocess mock
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("ffprobe missing")))
    monkeypatch.setattr(qc_mod, "get_ffmpeg_path", lambda: "ffmpeg")
    r = _probe(str(tmp_path / "x.mp4"))
    assert r == {"width": 0, "height": 0, "duration": 0}


def test_qc_border_durations(monkeypatch, tmp_path):
    path = _dummy(tmp_path)
    # 14s should pass (threshold <14), 15s passes, 95s passes, 96 fails
    for dur, should_pass in [(14, True), (15, True), (95, True), (96, False)]:
        monkeypatch.setattr(qc_mod, "_probe", lambda p, d=dur: {"width": 720, "height": 1280, "duration": d})
        r = qc_clip(path)
        if should_pass:
            assert not any("durasi" in i for i in r["issues"]), f"dur={dur} should not have durasi issue"
        else:
            assert any("durasi" in i for i in r["issues"]), f"dur={dur} should have durasi issue"
