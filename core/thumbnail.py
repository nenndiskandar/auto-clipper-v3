"""
core/thumbnail.py: Thumbnail Generator.

Extracts a representative frame from a rendered clip, darkens it, and
composites the clip title on top as a YouTube-thumbnail-style image.
Adapted from opensource-clipping ``clipping/studio/thumbnail.py``.

AI picker: ai_pick_frame() tries orchestrator.chat_json("thumbnail_picker")
with a prompt for the most expressive frame in 0-3s (face + motion),
returns {timestamp, reason}, falls back to heuristic face+motion.
Overlay timed_title typography via Pillow is applied in buat_thumbnail().
"""

import os
import textwrap
import urllib.request

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from utils.logger import debug_log

# Default thumbnail font (system-fallback to a bold font is attempted first).
THUMBNAIL_FONT_URL = (
    "https://fontsource.org/fonts/inter/latin-800-normal.ttf"
)
THUMBNAIL_FONT_FILE = "Inter-ExtraBold.ttf"


def _pick_thumbnail_font(font_dir: str = None) -> str | None:
    """Resolve a bold TTF usable for thumbnails (downloads Inter ExtraBold if needed)."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ]
    if font_dir:
        candidates.append(os.path.join(font_dir, THUMBNAIL_FONT_FILE))
    # Windows system bold fonts
    if os.name == "nt":
        candidates += [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\impact.ttf",
            r"C:\Windows\Fonts\verdanab.ttf",
        ]
    for c in candidates:
        if c and os.path.exists(c) and os.path.getsize(c) > 1000:
            return c

    dest = None
    if not font_dir:
        from utils.helpers import get_app_dir
        font_dir = os.path.join(str(get_app_dir()), "assets", "fonts")
        os.makedirs(font_dir, exist_ok=True)
        dest = os.path.join(font_dir, THUMBNAIL_FONT_FILE)

    if dest and os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return dest
    try:
        urllib.request.urlretrieve(THUMBNAIL_FONT_URL, dest)
        if os.path.getsize(dest) > 1000:
            return dest
    except Exception as e:
        debug_log(f"[Thumbnail] Gagal unduh font: {e}")
    return None


def _heuristic_pick_frame(video_path: str, window_start: float = 0.0, window_end: float = 3.0) -> dict:
    """Fallback heuristic face+motion: sample 0-3s, score face count + motion + sharpness."""
    default = {"timestamp": 1.0, "reason": "fallback heuristic default 1.0s"}
    if not os.path.exists(video_path):
        return default
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return default
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration = total_frames / fps if fps and total_frames else window_end
        # clamp window to duration
        window_end = min(window_end, max(window_start + 0.5, duration - 0.1) if duration > 0 else window_end)
        timestamps = []
        t = window_start
        while t <= window_end + 1e-6:
            timestamps.append(round(t, 3))
            t += 0.5
        if not timestamps:
            timestamps = [window_start]

        # Haar cascade for face
        face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            if os.path.exists(cascade_path):
                face_cascade = cv2.CascadeClassifier(cascade_path)
                if face_cascade.empty():
                    face_cascade = None
        except Exception:
            face_cascade = None

        best_ts = timestamps[0]
        best_score = -1
        prev_gray = None
        scores = []
        for ts in timestamps:
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # face score
            face_score = 0
            face_area = 0
            if face_cascade is not None:
                try:
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
                    face_score = len(faces) * 30
                    for (x, y, w, h) in faces:
                        face_area += w * h
                    # normalize area to 0-20
                    if face_area:
                        face_score += min(20, face_area / (frame.shape[0] * frame.shape[1]) * 200)
                except Exception:
                    pass
            # motion score vs prev frame
            motion = 0
            if prev_gray is not None and prev_gray.shape == gray.shape:
                try:
                    diff = cv2.absdiff(gray, prev_gray)
                    motion = float(np.mean(diff))  # 0-255
                    # scale to 0-20
                    motion = min(20, motion / 3)
                except Exception:
                    motion = 0
            # sharpness via Laplacian variance (0-20)
            sharp = 0
            try:
                sharp_raw = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                sharp = min(20, sharp_raw / 80)
            except Exception:
                sharp = 0
            total = face_score + motion + sharp
            scores.append((ts, total, face_score, motion, sharp))
            if total > best_score:
                best_score = total
                best_ts = ts
            prev_gray = gray
        cap.release()
        if best_score < 0:
            return default
        # build reason from best scores
        reason_parts = []
        for ts, total, f, m, s in scores:
            if ts == best_ts:
                reason_parts.append(f"face:{f:.1f} motion:{m:.1f} sharp:{s:.1f} total:{total:.1f}")
                break
        reason = f"heuristic face+motion @ {best_ts:.1f}s ({reason_parts[0] if reason_parts else ''})" if reason_parts else f"heuristic @ {best_ts:.1f}s"
        debug_log(f"[Thumbnail] heuristic pick: {best_ts}s score {best_score:.1f} -> {reason}")
        return {"timestamp": float(best_ts), "reason": reason}
    except Exception as e:
        debug_log(f"[Thumbnail] heuristic error: {e}")
        return default


def ai_pick_frame(
    clip_path: str,
    transcript: str = "",
    brief_dict: dict = None,
    orchestrator=None,
    window_start: float = 0.0,
    window_end: float = 3.0,
) -> dict:
    """Pilih frame paling ekspresif via AI, fallback ke heuristic face+motion.

    Args:
        clip_path: path ke clip video.
        transcript: teks transcript clip untuk konteks AI.
        brief_dict: dict brief kampanye (niche, hook_style, dll) untuk konteks.
        orchestrator: AIOrchestrator instance (punya chat_json).
        window_start, window_end: window detik untuk pemilihan (default 0-3s).

    Returns:
        dict {timestamp: float, reason: str} timestamp dalam detik.
    """
    fallback = _heuristic_pick_frame(clip_path, window_start, window_end)
    if orchestrator is None:
        return fallback
    try:
        brief_str = ""
        if isinstance(brief_dict, dict) and brief_dict:
            # ringkas biar prompt tidak terlalu panjang
            parts = []
            for k in ("niche", "hook_style", "tone", "target_duration"):
                v = brief_dict.get(k)
                if v:
                    parts.append(f"{k}:{v}")
            if parts:
                brief_str = ", ".join(parts)
            # jika ada raw_brief
            raw = brief_dict.get("raw_brief") or brief_dict.get("brief_text") or ""
            if raw:
                brief_str += f" | brief:{str(raw)[:300]}"
        transcript_snip = (transcript or "")[:1500]
        prompt = (
            f"Pilih timestamp terbaik untuk thumbnail dari clip dalam window {window_start:.1f}-{window_end:.1f} detik.\n"
            f"Transcript clip:\n{transcript_snip}\n\n"
            f"Brief: {brief_str or '-'}\n\n"
            "Kriteria: ekspresi wajah paling ekspresif, aksi jelas, wajah terlihat, motion tinggi, relevan dengan isi transcript.\n"
            "Return JSON ONLY tanpa teks lain: {\"timestamp\": <float 0-3>, \"reason\": \"alasan singkat max 20 kata\"}"
        )
        res = None
        try:
            res = orchestrator.chat_json("thumbnail_picker", None, prompt, fallback=None)
        except Exception as e:
            debug_log(f"[Thumbnail] chat_json error: {e}")
            res = None
        if isinstance(res, dict):
            raw_ts = res.get("timestamp")
            if raw_ts is None:
                raw_ts = res.get("time", res.get("ts", res.get("frame_time", res.get("sec"))))
            reason = res.get("reason", res.get("caption", res.get("explanation", res.get("desc", ""))))
            ts_val = None
            if raw_ts is not None:
                try:
                    ts_val = float(str(raw_ts).replace(",", ".").strip().split()[0])
                except Exception:
                    ts_val = None
            if ts_val is not None and window_start - 0.05 <= ts_val <= window_end + 0.05:
                ts_val = max(window_start, min(window_end, ts_val))
                debug_log(f"[Thumbnail] AI pick: {ts_val}s reason:{reason}")
                return {"timestamp": float(ts_val), "reason": str(reason or "AI pick")[:200]}
            else:
                if ts_val is not None:
                    debug_log(f"[Thumbnail] AI timestamp out of window {ts_val}, fallback heuristic")
                else:
                    debug_log(f"[Thumbnail] AI response tanpa timestamp valid: {res}")
        elif res is not None:
            debug_log(f"[Thumbnail] AI response bukan dict: {res}")
    except Exception as e:
        debug_log(f"[Thumbnail] ai_pick_frame error: {e}")
    return fallback


# Optional class wrapper for method-style usage
class ThumbnailPicker:
    """Wrapper class agar bisa dipakai sebagai mixin/method: picker.ai_pick_frame(...)"""

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator

    def ai_pick_frame(self, clip_path: str, transcript: str = "", brief_dict: dict = None) -> dict:
        return ai_pick_frame(clip_path, transcript, brief_dict, orchestrator=self.orchestrator)


def buat_thumbnail(
    video_path: str,
    output_image_path: str,
    teks: str = None,
    font_path: str = None,
    frame_ms: int = 1000,
    overlay_alpha: int = 0,
    timed_title: dict = None,
    **kwargs,
) -> str | None:
    """
    Extract a frame from the video, composite the clip title, save as JPEG/PNG.

    Args:
        video_path: Path to the rendered clip video.
        output_image_path: Destination for the thumbnail image.
        teks: Title text to write on the thumbnail.
        font_path: Optional path to a TTF. Auto-resolves a bold font if empty.
        frame_ms: Timestamp (ms) of the frame to extract.
        overlay_alpha: Dark overlay alpha 0-255 (0 = auto 110 when teks ada, 128 = slightly dark).
        timed_title: Optional dict {text, start, end} from highlight_finder, dipakai sebagai teks overlay.

    Returns:
        Path to the created image, or None if creation fails.
    """
    # timed_title overrides teks when provided
    if isinstance(timed_title, dict) and timed_title.get("text"):
        teks = str(timed_title.get("text"))
    elif kwargs.get("timed_title_text"):
        teks = str(kwargs.get("timed_title_text"))
    # also allow explicit teks from kwargs
    if teks is None:
        teks = kwargs.get("text") or kwargs.get("caption") or ""

    if not os.path.exists(video_path):
        debug_log(f"[Thumbnail] Video tidak ditemukan: {video_path}")
        return None

    # clamp frame_ms to 0-4000, avoid seeking beyond short clips
    try:
        frame_ms = int(frame_ms)
    except Exception:
        frame_ms = 1000
    if frame_ms < 0:
        frame_ms = 0
    if frame_ms > 10000:
        frame_ms = 3000

    font_file = font_path or _pick_thumbnail_font()
    pil_font = None
    cap = cv2.VideoCapture(video_path)
    # probe duration to clamp safely
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        fc = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        dur_ms = (fc / fps * 1000) if fps and fc else None
        if dur_ms and frame_ms >= dur_ms:
            frame_ms = max(0, int(dur_ms - 500))
    except Exception:
        pass
    cap.set(cv2.CAP_PROP_POS_MSEC, frame_ms)
    ret, frame = cap.read()
    # if seek failed, try 0
    if not ret or frame is None:
        cap.set(cv2.CAP_PROP_POS_MSEC, 0)
        ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        debug_log("[Thumbnail] Tidak bisa membaca frame (pastikan duration >= 1s).")
        return None

    has_text = bool(str(teks or "").strip())
    # auto overlay alpha when text ada but alpha 0
    if has_text and overlay_alpha == 0:
        # allow explicit alpha via kwargs
        overlay_alpha = int(kwargs.get("overlay_alpha", 110)) if kwargs.get("overlay_alpha") else 110

    if has_text and overlay_alpha > 0:
        img = Image.alpha_composite(
            Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA"),
            Image.new("RGBA", (frame.shape[1], frame.shape[0]), (0, 0, 0, overlay_alpha)),
        ).convert("RGB")
        draw = ImageDraw.Draw(img)
        font_sz = int(img.size[0] * 0.09)
        # clamp font size
        font_sz = max(18, min(font_sz, 72))
        if font_file and os.path.exists(font_file):
            try:
                pil_font = ImageFont.truetype(font_file, font_sz)
            except Exception as e:
                debug_log(f"[Thumbnail] Gagal load font {font_file}: {e}")
                pil_font = None
        if pil_font is None:
            try:
                pil_font = ImageFont.load_default()
            except Exception:
                pil_font = None

        raw_text = str(teks or "").strip() or "Clip"
        # wrap fairly narrow for 9:16 thumbnail readability
        lines = textwrap.wrap(raw_text, width=16) or [raw_text]
        # limit to 3 lines
        if len(lines) > 3:
            lines = lines[:3]
            lines[-1] = lines[-1][:17] + "..."
        # auto shrink font if lines too wide
        if pil_font is not None:
            # measure widest line
            try:
                max_w = 0
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=pil_font)
                    w = bbox[2] - bbox[0]
                    if w > max_w:
                        max_w = w
                # shrink if overflow
                while max_w > img.size[0] * 0.88 and font_sz > 18:
                    font_sz = int(font_sz * 0.9)
                    font_sz = max(18, font_sz)
                    try:
                        pil_font = ImageFont.truetype(font_file, font_sz) if font_file and os.path.exists(font_file) else ImageFont.load_default()
                    except Exception:
                        pil_font = ImageFont.load_default()
                    max_w = 0
                    for line in lines:
                        bbox = draw.textbbox((0, 0), line, font=pil_font)
                        w = bbox[2] - bbox[0]
                        if w > max_w:
                            max_w = w
            except Exception:
                pass

        # vertical center
        try:
            line_heights = []
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=pil_font) if pil_font else (0, 0, len(line) * 10, font_sz)
                h = bbox[3] - bbox[1]
                line_heights.append(h)
            total_h = sum(line_heights) + (len(lines) - 1) * 10
        except Exception:
            total_h = len(lines) * (font_sz + 10)
            line_heights = [font_sz] * len(lines)

        y_text = (img.size[1] - total_h) // 2
        for idx, line in enumerate(lines):
            try:
                bbox = draw.textbbox((0, 0), line, font=pil_font) if pil_font else (0, 0, len(line) * 10, font_sz)
            except Exception:
                bbox = (0, 0, len(line) * 10, font_sz)
            line_w = bbox[2] - bbox[0]
            x_text = (img.size[0] - line_w) // 2
            # ensure x not negative
            x_text = max(8, x_text)
            draw.text(
                (x_text, y_text),
                line,
                font=pil_font,
                fill="white",
                stroke_width=5,
                stroke_fill="black",
            )
            y_text += line_heights[idx] + 10
    else:
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    # ensure parent dir exists
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
    except Exception:
        pass
    try:
        img.save(output_image_path)
    except Exception as e:
        debug_log(f"[Thumbnail] Gagal save {output_image_path}: {e}")
        return None
    debug_log(f"[Thumbnail] Disimpan: {output_image_path} (frame {frame_ms}ms teks:{str(teks)[:30]})")
    return output_image_path
