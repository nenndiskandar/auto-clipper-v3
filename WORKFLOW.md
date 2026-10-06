# Workflow — Auto Clipper V3 (AI-First)

Stack: Python engine + Node webjs (sama kayak v2). Beda: hampir semua keputusan kreatif dikerjain AI, bukan manual.

## 0. Preflight (AI guard)
- Parse brief campaign via LLM → validasi source_links / sound_id / tone
- AI estimasi durasi + size + risk kuota metered → warning sebelum download
- Cek disk free

## 1. Campaign Intake
- Input: brief teks bebas / TernakKlip link / GDrive folder+sound TikTok
- AI `brief_parser` → structured { sources[], sound_id, niche, hook_style, target_duration }

## 2. Download (deterministic, bukan AI)
- YouTube → `yt-dlp bestvideo[height<=1080]+bestaudio` (cap 1080p, anti-4K boros)
- GDrive FILE/FOLDER → `gdown` expand → `rclone` per-file
- Sound TikTok → resolve canonical `tiktok.com/@user/video/<id>` + `yt-dlp --cookies cookies.txt --impersonate chrome -x --audio-format mp3` → `output/bgm/<id>.mp3` (mp3 native 697KB test, reuse cache)
- Simpan `output/sessions/<id>/raw/` + `downloaded.json` (skip kalau cached)

## 3. Transcribe
- `faster-whisper large-v3` + silero-vad → `transcript.json` (word-level)
- Fallback: Whisper API via OmniRoute

## 4. Highlight + Hook + Title (AI single-pass)
- LLM `highlight_finder` baca transcript + brief → JSON Array `{start_time, end_time, title, description, virality_score, hook_text, timed_title{0-3s}}`
- Scoring: buang overlap, <15s / >90s, limit top-N, dedup hook

## 5. Metadata AI (NEW in v3)
- `title_maker` → judul YouTube/TikTok per clip (SEO + hook)
- `hashtag_maker` → hashtag niche-aware
- `bgm_matcher` → pilih/rekomendasi sound_id berdasar mood transcript (happy/sad/hype)

## 6. Thumbnail AI (NEW)
- AI `thumbnail_picker` pilih frame paling ekspresif per clip (face + motion)
- Auto overlay `timed_title` typography (Pillow) → `thumb.jpg`

## 7. Render portrait 9:16 — AUTO max source
- `ffprobe` orig_w×orig_h → crop 9:16 → out = crop size (tanpa upscale)
- face-tracking: OpenCV / MediaPipe → crop center dinamis
- `amix` BGM 12-25% (loop/trim ikut durasi)
- burn caption `pop` style via ffmpeg

## 8. QC AI (NEW)
- `qc_checker` → cek durasi/audio/resolusi + AI vision cek framing (kepala kepotong? teks kebaca?)
- tulis `manifest.json` {clip_id, source, start-end, sound_id, resolusi, title, hashtags, qc_pass}
- KEEP-ALL: semua raw + transcript + clips disimpan; cleanup manual via UI

## 9. Upload (opsional)
- `tiktok_uploader.py` / `youtube_uploader.py` pakai title+hashtag AI

## Tooling
- Preflight: `/api/disk` + AI size-guard
- Transcribe: `faster_whisper_models/*`
- Render: `core/portrait.py` → ffmpeg crop+scale+amix
- AI: OmniRoute `/v1` (model `opencos` default 872) via `config.ai_providers`
