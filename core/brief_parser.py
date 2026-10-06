"""
core/brief_parser.py — v3 NEW — Parse brief bebas jadi structured campaign via LLM.
Input: teks bebas user ("TernakKlip X + backsound TikTok Y untuk niche parenting")
Output: { sources:[{url,type}], sound_id, niche, hook_style, target_duration, tone }
Fallback rule-based kalau LLM off.
"""
import re
from utils.logger import debug_log

TIKTOK_RE = re.compile(r"https?://(?:vt\.tiktok\.com/\S+|www\.tiktok\.com/@[^\s]+/video/\d+|vm\.tiktok\.com/\S+)")
YOUTUBE_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?[^\s]+|youtu\.be/[^\s]+)")
GDRIVE_RE = re.compile(r"https?://drive\.google\.com/[^\s]+")

def _rule_parse(brief: str) -> dict:
    t = brief or ""
    sources = []
    for m in YOUTUBE_RE.findall(t): sources.append({"url": m, "type": "youtube"})
    for m in GDRIVE_RE.findall(t): sources.append({"url": m, "type": "gdrive"})
    # tiktok sound id dari url tiktok
    sound_id = None
    m = TIKTOK_RE.search(t)
    if m:
        # ambil id video sebagai sound_id candidate
        vid = re.search(r"/video/(\d+)", m.group(0))
        if vid: sound_id = vid.group(1)
    # dedup
    seen=set(); uniq=[]
    for s in sources:
        if s["url"] not in seen:
            seen.add(s["url"]); uniq.append(s)
    return {
        "sources": uniq,
        "sound_id": sound_id,
        "niche": "",
        "hook_style": "viral",
        "target_duration": "15-90s",
        "tone": "",
        "raw_brief": t[:500],
    }

def parse_brief(brief_text: str, orchestrator=None) -> dict:
    """Coba AI dulu, fallback rule."""
    if orchestrator is None:
        return _rule_parse(brief_text)
    prompt = f"""Brief kampanye (bebas, bisa campur link):
{brief_text}

Tugas: kembalikan JSON ONLY:
{{"sources":[{{"url":"...","type":"youtube|gdrive|tiktok"}}],"sound_id":"id tiktok jika ada else null","niche":"parenting|business|comedy|...","hook_style":"viral|educative|emotional","target_duration":"15-90s","tone":"energetic|calm|..."}}"""
    res = orchestrator.chat_json("brief_parser", None, prompt, fallback=None)
    if isinstance(res, dict) and ("sources" in res or "niche" in res):
        # merge dengan rule sebagai safety
        rule = _rule_parse(brief_text)
        # kalau AI tidak deteksi sources, pakai rule
        if not res.get("sources"):
            res["sources"] = rule["sources"]
        if not res.get("sound_id"):
            res["sound_id"] = rule["sound_id"]
        res.setdefault("raw_brief", brief_text[:500])
        debug_log(f"[BriefParser] AI OK: {res}")
        return res
    debug_log("[BriefParser] AI gagal, pakai rule")
    return _rule_parse(brief_text)
