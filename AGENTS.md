# 🤖 AGENTS.md - AI Developer Guide for Auto Clipper

## 📌 Project Overview
**Auto Clipper** automates short-form clips (TikTok, Reels, Shorts) from long YouTube
videos using AI (GPT-4 / Whisper) for highlight detection & captioning, and Computer
Vision (OpenCV / MediaPipe) for 9:16 smart cropping.

**Fokus repositori ini: Web App + Telegram Bot.** GUI desktop (CustomTkinter) sudah
dihapus. Engine pemrosesan (`clipper_core.py` + `core/`) dipakai bersama oleh kedua
antarmuka.

## 🏗️ Architecture & Tech Stack
- **Language**: Python 3.10+ (engine + bot), Node.js >= 16 (web server)
- **Web**: `webjs/server.js` (HTTP, zero-dep) + `webjs/public/` (static PWA). Server
  memanggil helper Python (`webjs/*.py`) via `child_process`, yang memanggil engine.
- **Telegram**: `python-telegram-bot` (Bot API) + `telethon` (userbot/MTProto).
- **Video**: FFmpeg (subprocess) + OpenCV (face detection) + MediaPipe (active speaker).
- **AI/ML**: OpenAI API (GPT-4 / Whisper) lewat `config.ai_providers`.

## 🔄 Core Pipeline (`clipper_core.py` + `core/`)
`clipper_core.AutoClipperCore` menyusun seluruh pipeline dan mewarisi mixin:
- `core/download.py` (DownloadMixin): download video & subtitle, yt-dlp, progress.
- `core/transcribe.py` (TranscribeMixin): Whisper API + faster-whisper lokal.
- `core/highlight.py` (HighlightMixin): deteksi highlight via LLM, parse SRT.
- `core/portrait.py` (PortraitMixin): crop 9:16, face-tracking, stabilisasi.
- `core/caption.py` (CaptionMixin): hook, caption, watermark, `process_clip`.
- `core/subtitle_generator.py`, `core/effects.py`: mixin lama (tetap dipertahankan).

Alur inti:
1. `download_video` / `download_subtitle_only` -> dapat video + `.srt`.
2. `transcribe_*` -> word-level transcript (Whisper).
3. `find_highlights` / `find_highlights_with_transcription` -> timestamp + hook.
4. `process_clip` -> potong -> portrait -> hook -> caption (burn via FFmpeg).

## 📂 Key Directories
| Path | Deskripsi |
|------|-----------|
| `webjs/server.js` | Server web utama |
| `webjs/public/` | UI statis + PWA |
| `webjs/*.py` | Helper Python per-session (panggil engine) |
| `telegram_bot.py` / `telegram_client.py` | Antarmuka Telegram |
| `clipper_core.py` | Orchestrator + komposisi mixin |
| `core/` | Mixin engine (download/transcribe/highlight/portrait/caption) |
| `config/` | `config_manager.py`, profil provider AI |
| `utils/` | `helpers`, `logger`, `gpu_detector`, `dependency_manager`, `font_scanner` |
| `tiktok_uploader.py` / `youtube_uploader.py` | Uploader (standalone, berbagi) |
| `assets/watermarks/` | Aset watermark (dipakai bot) |
| `tests/` | Unit test (`pytest tests`) |

## 🛠️ Coding Standards
- **Logging**: selalu pakai `utils.logger.debug_log` (bukan `print`). `debug_log`
  menerima multi-arg & kwarg print-like.
- **Error handling**: jangan `except:` kosong. Gunakan
  `except Exception as e:` lalu `debug_log(...)` / `log_error(...)`.
- **Tidak ada GUI**: jangan impor `tkinter`/`customtkinter`/`CTk*` lagi.
- **Modular**: tambah fitur ke mixin `core/` yang sesuai, jangan menumpuk di
  `clipper_core.py`.
- **Tests**: jalankan `pytest tests` sebelum commit.

## 🔗 Related
- `README.md`: quick start web & bot.
<!-- antislop:start -->
## antislop
For UI, copy, people, mobile layout, or code comments work, read `antislop.md` (core) and then the skill for the task:
- UI / visual: `skills/antislop-ui/SKILL.md`
- Copy & text: `skills/antislop-copywriting/SKILL.md`
- People: `skills/antislop-human/SKILL.md`
- Mobile / responsive: `skills/antislop-layoutmobile/SKILL.md`
- Code comments: `skills/antislop-code/SKILL.md`
Before starting, follow the core's "Two Usage Modes" section in strict order: explicit session instruction first, then global preference, then ask. A session instruction always wins. For a resolved mode, say `antislop active: <mode> (session override).` or `antislop active: <mode> (global preference).` once before presenting findings or making edits, using the actual mode and source. Acknowledging the user's request without naming the source does not replace this notice.
Only an explicit choice of antislop during or after selects a session mode. A request to review, audit, or avoid file edits does not select a mode; read the global preference in that case. Another skill's mode does not select antislop's mode.
If the mode is unresolved, ask during/after and end the response; wait for the answer before any UI review, planning, or concept. For read-only tasks, put the active-mode notice only at the start of the final answer, never in progress messages. For editing tasks, announce before the first edit and omit it from the final answer.
To update antislop later: download `antislop.md` again, or run `npx antislop-ai --update` if it was installed as skill folders.
<!-- antislop:end -->
