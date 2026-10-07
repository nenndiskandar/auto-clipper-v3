#!/usr/bin/env python3
"""Redownload single source URL into session _temp (force re-download).
Usage: redownload_source.py <session_dir> <url> [index]
- session_dir: output/sessions/<id>
- url: source URL to re-download
- index: source index label for log (optional)
Force removes old source.* in _temp before download so cache is bypassed.
Uses AutoClipperCore.DownloadMixin.download_video (handles YouTube/TikTok/GDrive via rclone/gdown/yt-dlp).
"""
import sys, os, json, traceback
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: redownload_source.py <session_dir> <url> [index]", file=sys.stderr)
    sys.exit(2)

SESSION_DIR = Path(sys.argv[1]).resolve()
URL = sys.argv[2].strip()
IDX = sys.argv[3] if len(sys.argv) >= 4 else "0"

APP_DIR = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)

from config.config_manager import ConfigManager
from utils.helpers import get_ffmpeg_path, get_ytdlp_path, get_app_dir
from utils.logger import debug_log
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _progress_cb(msg, frac):
    try:
        pct = max(0.0, min(1.0, float(frac))) * 100.0
        debug_log(f"[progress] {msg} (overall: {pct:.1f}%)", flush=True)
    except Exception:
        pass

def main():
    debug_log(f"[redownload] session={SESSION_DIR.name} idx={IDX} url={URL[:120]} (overall: 0.0%)", flush=True)
    if not SESSION_DIR.exists():
        print(json.dumps({"ok": False, "error": f"session dir not found: {SESSION_DIR}"}), flush=True)
        sys.exit(1)
    if not URL:
        print(json.dumps({"ok": False, "error": "url kosong"}), flush=True)
        sys.exit(1)

    app_dir = Path(APP_DIR)
    cfg_mgr = ConfigManager(app_dir / "config.json", app_dir / "output")
    cfg = cfg_mgr.config
    prov = cfg.get("ai_providers") or {}
    # pick any provider for OpenAI client (highlight_finder or base)
    hf = prov.get("highlight_finder") or {}
    api_key = (hf.get("api_key") or cfg.get("api_key") or "")
    base_url = (hf.get("base_url") or cfg.get("base_url") or "https://api.openai.com/v1")
    client = None
    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception:
            client = None
    # if no client, make dummy (DownloadMixin doesn't need OpenAI)
    if client is None and OpenAI:
        try:
            client = OpenAI(api_key="sk-dummy", base_url=base_url)
        except Exception:
            client = object()

    from clipper_core import AutoClipperCore
    core = AutoClipperCore(
        client=client,
        ffmpeg_path=get_ffmpeg_path(),
        ytdlp_path=get_ytdlp_path(),
        output_dir=str(app_dir / "output"),
        model=cfg.get("model", "gpt-4.1"),
        tts_model=cfg.get("tts_model", "tts-1"),
        temperature=cfg.get("temperature", 1.0),
        system_prompt=cfg.get("system_prompt"),
        watermark_settings=cfg.get("watermark"),
        credit_watermark_settings=cfg.get("credit_watermark"),
        hook_style_settings=cfg.get("hook_style"),
        face_tracking_mode=cfg.get("face_tracking_mode", "opencv"),
        portrait_mode=cfg.get("portrait_mode", "crop"),
        subtitle_style=cfg.get("subtitle_style", "pop"),
        aspect_ratio=cfg.get("aspect_ratio", "9:16"),
        resolution=str(cfg.get("resolution", "auto")),
        mediapipe_settings=cfg.get("mediapipe_settings"),
        ai_providers=prov or None,
        pro_settings=cfg.get("pro_settings"),
        auto_bgm_settings=cfg.get("auto_bgm"),
        thumbnail_settings=cfg.get("thumbnail"),
        metadata_settings=cfg.get("metadata_settings"),
        auto_broll_settings=cfg.get("auto_broll"),
        subtitle_language=cfg.get("subtitle_language", "id"),
        subtitle_sync_offset=cfg.get("subtitle_sync_offset", -0.3),
    )
    core.enable_gpu_acceleration(False)
    if cfg.get("face_detector_model"):
        core.face_detector_model = cfg.get("face_detector_model")

    # force session temp dirs
    sess_temp = SESSION_DIR / "_temp"
    sess_temp_gdrive = SESSION_DIR / "_temp_gdrive"
    sess_temp.mkdir(parents=True, exist_ok=True)
    # point core temp to session temp (download_video writes to self.temp_dir/source.*)
    core.temp_dir = sess_temp
    core.output_dir = Path(app_dir / "output")

    # Force re-download: remove old source.* that would cause cache-hit skip
    # Keep other redownload files? just nuke source.* so DownloadMixin will re-fetch.
    # For gdrive, also nuke source.* in _temp_gdrive if exists (fallback writes there? but our temp is _temp)
    try:
        for pat in ["source.*", f"source_{IDX}.*", f"redl_{IDX}.*"]:
            for p in sess_temp.glob(pat):
                try:
                    if p.is_file() and p.stat().st_size > 0:
                        debug_log(f"[redownload] removing old {p.name} for force re-download")
                        p.unlink()
                except Exception:
                    pass
        # also clean _temp_gdrive source if GDrive url (DownloadMixin may write there via fallback? but primary is _temp)
        if sess_temp_gdrive.exists():
            for p in sess_temp_gdrive.glob("source.*"):
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass
    except Exception:
        pass

    debug_log(f"[redownload] downloading idx={IDX} url={URL[:100]} -> {sess_temp} (overall: 5.0%)", flush=True)
    try:
        # Use clip_dir=None so it writes to temp_dir/source.*
        # download_video handles GDrive folder expand + rclone/gdown/yt-dlp
        video_path, srt_path, vinfo = core.download_video(URL)
        debug_log(f"[redownload] done -> {video_path} srt={srt_path} (overall: 100.0%)", flush=True)
        # If file landed in _temp as source.mp4 etc, keep it; also log size
        try:
            vp = Path(video_path) if video_path else None
            if vp and vp.exists():
                debug_log(f"[redownload] file {vp.name} {vp.stat().st_size//1024}KB", flush=True)
        except Exception:
            pass
        # Update session_data.json url/video_info if provided (optional)
        try:
            sd_path = SESSION_DIR / "session_data.json"
            if sd_path.exists():
                data = json.loads(sd_path.read_text(encoding="utf-8"))
                # keep original url if already set, but ensure video_info refresh if we got vinfo
                if vinfo and isinstance(vinfo, dict) and vinfo.get("title"):
                    data["video_info"] = vinfo
                sd_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
        print(json.dumps({"ok": True, "video_path": str(video_path), "srt_path": str(srt_path) if srt_path else None, "video_info": vinfo}, ensure_ascii=False), flush=True)
    except Exception as e:
        traceback.print_exc()
        debug_log(f"[redownload] failed idx={IDX}: {e} (overall: 100.0%)", flush=True)
        print(json.dumps({"ok": False, "error": str(e)[:800]}, ensure_ascii=False), flush=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        try:
            print(json.dumps({"ok": False, "error": traceback.format_exc()[-1500:]}, ensure_ascii=False), flush=True)
        except Exception:
            pass
        sys.exit(1)
