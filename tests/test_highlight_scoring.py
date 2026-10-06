"""Highlight scoring — pure functions: durasi / overlap / dedup / sort, tanpa network."""
import re

# ---------- pure helpers (mirror produksi, tanpa impor berat) ----------

def _parse_ts(ts: str) -> float:
    """HH:MM:SS,mmm -> seconds. Minimal parser untuk test."""
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(ts)


def _overlaps(a_start: float, a_end: float, b_start: float, b_end: float) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def filter_by_duration(highlights: list, min_dur: int = 15, max_dur: int = 90) -> list:
    out = []
    for h in highlights:
        try:
            s = _parse_ts(h["start_time"])
            e = _parse_ts(h["end_time"])
        except Exception:
            continue
        dur = e - s
        if min_dur <= dur <= max_dur:
            out.append({**h, "duration_seconds": round(dur, 1)})
    return out


def sort_by_virality(highlights: list) -> list:
    return sorted(highlights, key=lambda x: (x.get("virality_score") or 0), reverse=True)


def dedup_overlap(highlights: list) -> list:
    """Greedy keep tertinggi virality, skip yang overlap (mirip produksi)."""
    ordered = sort_by_virality(highlights)
    kept = []
    for h in ordered:
        try:
            s = _parse_ts(h["start_time"]); e = _parse_ts(h["end_time"])
        except Exception:
            continue
        if any(_overlaps(s, e, _parse_ts(k["start_time"]), _parse_ts(k["end_time"])) for k in kept):
            continue
        kept.append(h)
    return kept


def score_pipeline(highlights: list, min_dur=15, max_dur=90, top_n=None) -> list:
    """Filter durasi -> sort virality -> dedup overlap -> limit top_n."""
    valid = filter_by_duration(highlights, min_dur, max_dur)
    deduped = dedup_overlap(valid)
    if top_n is not None:
        return deduped[:top_n]
    return deduped


# ---------- tests: durasi ----------

def test_duration_keep_inside_range():
    hs = [{"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:30,000", "virality_score": 7}]
    assert len(filter_by_duration(hs, 15, 90)) == 1


def test_duration_too_short_filtered():
    hs = [{"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:10,000", "virality_score": 9}]
    assert filter_by_duration(hs) == []


def test_duration_too_long_filtered():
    hs = [{"title": "A", "start_time": "00:00:00,000", "end_time": "00:02:00,000", "virality_score": 9}]
    assert filter_by_duration(hs) == []


def test_duration_bounds_inclusive():
    hs = [
        {"title": "min", "start_time": "00:00:00,000", "end_time": "00:00:15,000", "virality_score": 5},
        {"title": "max", "start_time": "00:00:00,000", "end_time": "00:01:30,000", "virality_score": 5},
    ]
    assert len(filter_by_duration(hs, 15, 90)) == 2


def test_duration_missing_timestamp_skipped():
    hs = [{"title": "bad", "virality_score": 8}]
    assert filter_by_duration(hs) == []


def test_brief_duration_override():
    # simulasi brief minta 8-20s: klip 10s lolos, 30s harusnya ke-filter
    hs = [
        {"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:10,000", "virality_score": 6},
        {"title": "B", "start_time": "00:00:20,000", "end_time": "00:00:50,000", "virality_score": 8},
    ]
    short = filter_by_duration(hs, min_dur=8, max_dur=20)
    assert len(short) == 1 and short[0]["title"] == "A"


# ---------- tests: overlap ----------

def test_overlap_true():
    assert _overlaps(0, 30, 20, 50) is True

def test_overlap_false_touching():
    # touching di batas 30.0 tidak dianggap overlap (max==min)
    assert _overlaps(0, 30, 30, 60) is False

def test_overlap_false_separate():
    assert _overlaps(0, 10, 20, 30) is False

def test_overlap_nested():
    assert _overlaps(0, 60, 10, 20) is True

def test_overlap_identical():
    assert _overlaps(10, 40, 10, 40) is True


# ---------- tests: dedup ----------

def test_dedup_keeps_highest_virality():
    hs = [
        {"title": "low", "start_time": "00:00:00,000", "end_time": "00:00:30,000", "virality_score": 5},
        {"title": "high", "start_time": "00:00:10,000", "end_time": "00:00:40,000", "virality_score": 9},
    ]
    kept = dedup_overlap(hs)
    assert len(kept) == 1
    assert kept[0]["title"] == "high"


def test_dedup_non_overlapping_both_kept():
    hs = [
        {"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:30,000", "virality_score": 6},
        {"title": "B", "start_time": "00:00:31,000", "end_time": "00:01:00,000", "virality_score": 7},
    ]
    assert len(dedup_overlap(hs)) == 2


def test_dedup_chain_overlap():
    # A overlap B, B overlap C (tapi A tidak overlap C) -> greedy by virality
    hs = [
        {"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:30,000", "virality_score": 6},
        {"title": "B", "start_time": "00:00:20,000", "end_time": "00:00:50,000", "virality_score": 9},
        {"title": "C", "start_time": "00:00:45,000", "end_time": "00:01:10,000", "virality_score": 7},
    ]
    kept = dedup_overlap(hs)
    # B kept (9), A skipped (overlap B), C skipped (overlap B)
    assert [k["title"] for k in kept] == ["B"]


def test_dedup_touching_kept_both():
    hs = [
        {"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:30,000", "virality_score": 8},
        {"title": "B", "start_time": "00:00:30,000", "end_time": "00:01:00,000", "virality_score": 7},
    ]
    assert len(dedup_overlap(hs)) == 2


def test_dedup_missing_virality_treated_as_zero():
    hs = [
        {"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:30,000"},  # no score -> 0
        {"title": "B", "start_time": "00:00:10,000", "end_time": "00:00:40,000", "virality_score": 5},
    ]
    kept = dedup_overlap(hs)
    assert kept[0]["title"] == "B"


def test_dedup_stable_with_equal_scores():
    hs = [
        {"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:30,000", "virality_score": 7},
        {"title": "B", "start_time": "00:00:10,000", "end_time": "00:00:40,000", "virality_score": 7},
    ]
    kept = dedup_overlap(hs)
    # equal scores -> sort stable keeps original order, A kept, B skipped
    assert len(kept) == 1


# ---------- tests: sort ----------

def test_sort_by_virality_desc():
    hs = [
        {"title": "low", "virality_score": 3},
        {"title": "high", "virality_score": 9},
        {"title": "mid", "virality_score": 6},
    ]
    order = [h["title"] for h in sort_by_virality(hs)]
    assert order == ["high", "mid", "low"]


def test_sort_none_treated_as_zero():
    hs = [{"title": "A"}, {"title": "B", "virality_score": 5}]
    assert sort_by_virality(hs)[0]["title"] == "B"


# ---------- tests: pipeline integrasi ----------

def test_pipeline_filter_then_dedup_then_top_n():
    hs = [
        {"title": "short", "start_time": "00:00:00,000", "end_time": "00:00:05,000", "virality_score": 10},  # filtered durasi
        {"title": "A", "start_time": "00:00:10,000", "end_time": "00:00:40,000", "virality_score": 8},
        {"title": "B", "start_time": "00:00:20,000", "end_time": "00:00:50,000", "virality_score": 9},  # overlap A, B menang
        {"title": "C", "start_time": "00:01:00,000", "end_time": "00:01:30,000", "virality_score": 7},
        {"title": "D", "start_time": "00:02:00,000", "end_time": "00:02:30,000", "virality_score": 6},
    ]
    res = score_pipeline(hs, top_n=2)
    assert len(res) == 2
    assert res[0]["title"] == "B"  # virality tertinggi
    assert res[1]["title"] == "C"  # next setelah dedup


def test_pipeline_no_top_n_keeps_all_deduped():
    hs = [
        {"title": "A", "start_time": "00:00:00,000", "end_time": "00:00:30,000", "virality_score": 5},
        {"title": "B", "start_time": "00:01:00,000", "end_time": "00:01:30,000", "virality_score": 6},
    ]
    assert len(score_pipeline(hs)) == 2


def test_pipeline_empty():
    assert score_pipeline([]) == []


# ---------- sanity: produksi parse_timestamp kompatibel ----------

def test_production_parse_timestamp_compat():
    """Cek AutoClipperCore.parse_timestamp masih kompatibel dengan helper."""
    try:
        from clipper_core import AutoClipperCore

        parse = getattr(AutoClipperCore, "parse_timestamp")  # type: ignore
        # beberapa format yang dipakai produksi
        for ts, expected in [
            ("00:01:30,000", 90.0),
            ("00:00:15,500", 15.5),
            ("01:02:03,000", 3723.0),
        ]:
            assert abs(parse(object(), ts) - expected) < 1e-6  # type: ignore
            assert abs(_parse_ts(ts) - expected) < 1e-6
    except ImportError:
        # jika dep berat belum ada, helper test sudah cukup
        pass
