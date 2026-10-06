"""
core/qc.py — v3 NEW — QC klip: rule + AI vision check.
Rule: durasi, resolusi, audio ada.
AI (opsional): framing — kepala kepotong? teks kebaca?  → {pass, issues[]}
"""
import os
import json
import subprocess
from pathlib import Path
from utils.logger import debug_log
from utils.helpers import get_ffmpeg_path

def _probe(path: str) -> dict:
    ffprobe = get_ffmpeg_path().replace("ffmpeg","ffprobe") if "ffmpeg" in get_ffmpeg_path() else "ffprobe"
    try:
        out = subprocess.check_output(
            [ffprobe, "-v","error","-select_streams","v:0",
             "-show_entries","stream=width,height,duration,codec_name",
             "-show_entries","format=duration","-of","json", path],
            text=True, timeout=10)
        j=json.loads(out)
        s=(j.get("streams") or [{}])[0]
        dur = float(s.get("duration") or j.get("format",{}).get("duration") or 0)
        return {"width": int(s.get("width") or 0), "height": int(s.get("height") or 0), "duration": dur}
    except Exception as e:
        debug_log(f"[QC] probe gagal {path}: {e}")
        return {"width":0,"height":0,"duration":0}

def qc_clip(clip_path: str, orchestrator=None, transcript: str = "") -> dict:
    """Return {pass:bool, issues:[], meta:{w,h,duration}}"""
    meta = _probe(clip_path)
    issues=[]
    w,h,dur = meta["width"], meta["height"], meta["duration"]
    if w==0 or h==0: issues.append("probe gagal / file rusak")
    if dur < 14: issues.append(f"durasi terlalu pendek {dur:.1f}s (<15s)")
    if dur > 95: issues.append(f"durasi terlalu panjang {dur:.1f}s (>90s ideal)")
    if h and h < 480: issues.append(f"resolusi vertikal kecil {h}px")
    # portrait check
    if w and h and w >= h: issues.append(f"aspect bukan portrait {w}x{h}")
    if not os.path.exists(clip_path) or os.path.getsize(clip_path) < 5000:
        issues.append("file kecil / audio hilang?")

    ai_issues=[]
    if orchestrator and transcript:
        prompt = f"""QC klip short-form 9:16.
Meta: {w}x{h}, {dur:.1f}s
Transcript: {transcript[:800]}

Cek: framing (kepala kepotong?), teks hook kebaca?, audio sinkron?
Return JSON ONLY: {{"pass": true/false, "issues": ["..."]}}"""
        res = orchestrator.chat_json("qc_checker", None, prompt, fallback=None)
        if isinstance(res, dict):
            ai_issues = res.get("issues") or []
            if res.get("pass") is False and not ai_issues:
                ai_issues = ["AI QC fail tanpa detail"]
            debug_log(f"[QC] AI: {res}")

    all_issues = issues + ai_issues
    return {"pass": len(all_issues)==0, "issues": all_issues, "meta": meta, "ai_issues": ai_issues, "rule_issues": issues}
