# Auto Clipper v3

AI-first video short generator: YouTube / GDrive / TikTok sound jadi klip portrait 9:16 siap upload (TikTok, Reels, Shorts). Stack sama kayak v2 (Python engine + Node webjs), tapi lebih banyak step yang dikerjain AI.

## Beda v2 -> v3

- v2: AI cuma di highlight + caption
- v3: AI handle lebih banyak — hook, judul/hashtag, thumbnail, BGM matching, QC
- v3: 1 campaign = 1 sesi multi-source paralel (pool 3, max 8 source), bukan 1 URL = 1 sesi
- v3: single-page UI — semua halaman dilebur jadi tab di `index.html` (hash routing)

## Fitur

- **Campaign TernakKlip**: one-click `POST /api/campaign/auto/:id` — folder `tk_<id>` + brief + ranking + download top-1 + whisper + highlight + render otomatis
- **Multi-source paralel**: session `tk_<campId>`, isolate `_work_i`, merge `source_url/label/index`, filter brief 15-30 dtk, dedup, sort virality, cache `_full_src<idx>.mp4` hemat kuota
- **Redownload per-source**: tombol Redl kuning di samping tiap URL source (rclone → gdown chain)
- **Render portrait AUTO**: max source tanpa upscale, face-tracking OpenCV/MediaPipe, BGM amix 12-25%, caption pop
- **AI metadata**: title_maker, hashtag_maker, bgm_matcher, thumbnail_picker, qc_checker via OmniRoute `/v1` (model `opencos`)
- **UI portal-dark**: sidebar collapse 240/64, aurora teal/sky/rose, dark-only `#09090b`, 5 tab + hidden create/session-detail/detail-modal

## Quick Start

### Prasyarat

- Python 3.10+ (venv di `venv/`, probe dulu sebelum install deps)
- Node.js >= 22 (webjs zero-dependency, serve `:3006`)
- `ffmpeg` sistem + `bin/deno` bundled (copy dari v2, jangan download ulang)
- `faster_whisper_models/medium` (default; large korup, tiny/base/small opsional)
- `config.json` dari `config.example.json` (base_url OmniRoute `http://127.0.0.1:20127/v1`)

```bash
python -m venv venv && venv/bin/pip install -r requirements.txt
cp config.example.json config.json  # isi api_key + telegram_bot_token
PORT=3006 node webjs/server.v3.js    # atau systemctl start autoclipper-v3
# buka http://localhost:3006 (auth password) atau https://clip.nendi.web.id
```

### Systemd

```bash
systemctl restart autoclipper-v3  # unit: /etc/systemd/system/autoclipper-v3.service
curl -s http://localhost:3006/api/me  # {"id":"local"}
```

## Struktur

| Path | Deskripsi |
|------|-----------|
| `webjs/server.v3.js` | HTTP server Node (auth HMAC, serve `public/`, paralel pool, legacy 302 redirect) |
| `webjs/public/index.html` | Single-page UI: 5 tab sidebar + hidden create/session-detail + detail modal |
| `webjs/public/app.css` | Portal-dark CSS (sidebar 0.6, cards 0.4, aurora 60/54/52vmax) |
| `webjs/phase1_campaign.py` | Folder campaign `tk_<id>` + brief + ranking top-N |
| `webjs/phase1_create.py` | Spawn per-source (dipakai pool paralel) |
| `webjs/process_session.py` | Orchestrator: merge multi-source → highlight → render |
| `webjs/redownload_source.py` | Redownload 1 source via rclone/gdown |
| `webjs/render_clip.py` | Render 1 klip portrait |
| `core/` | Engine: download, transcribe, highlight, portrait, caption, bgm, metadata, thumbnail, qc |
| `config/config_manager.py` | Config loader (Path wrap untuk brief/parse) |
| `bin/deno` | Deno bundled 2.6.7 (copy dari v2) |
| `faster_whisper_models/` | Model whisper lokal (medium default, di-ignore git) |
| `output/sessions/` | Data sesi (di-ignore git, jangan cleanup — bisa render ulang) |

## Routing UI

Sidebar: `#sesi #campaign #task #dependencies #settings` (persist `clipperViewTab`).
Hidden: `#create` (form buat klip), `#session/<id>` (detail sesi), `#detail/<sid>/<cid>` (modal klip).
Legacy `/create.html`, `/session.html?id=x`, `/detail.html`, `/tasks.html`, `/dependencies.html`, `/settings.html` → 302 ke hash.

## API penting

- `POST /api/campaign/auto/:id` — one-click campaign (top_n:1)
- `POST /api/create` + `/api/create/status` — buat sesi manual
- `GET /api/sessions/:id` — detail sesi + campaign + clips + logs
- `GET /api/highlights/:id` — fallback highlights
- `POST /api/process/:session` — render terpilih
- `GET /api/dependencies` — status binaries/models (probe venv dulu)

## Testing

```bash
pytest tests  # mock, no network — jangan yt-dlp/gdown/rclone tanpa izin (kuota metered)
```

## Catatan

- Cache WAJIB simpan (`output/`, `_full_src<idx>.mp4`) — bisa render ulang.
- Base AI wajib `http://127.0.0.1:20127/v1` model `opencos`, bukan 20128.
- Semua log lewat `utils.logger.debug_log`, bukan `print`.
