# Rebuild index.html - 5 Tabs Portal-Style

## Diubah
- `webjs/public/index.html` - rebuild total: 837 baris -> 1535 baris (chars 49514 -> 96876)
- Backup dibuat: `index.html.bak` dan `index.html.bak.20261007_002231` (49549 bytes)
- Tidak mengubah file lain: `tasks.html`, `dependencies.html`, `settings.html`, `create.html` tetap (hanya timestamp tidak, size sama)

## Sidebar
- Ganti `<nav id="sidebarLinks">` anchors (Library Sesi, Create Clip, Antrean Tasks, AI Story, FB, Cookies, TernakKlip, Dependencies, Settings) menjadi 5 buttons portal-style:
  - `data-view-tab="sesi"` - Sesi - icon `bi-collection-play` - default active `bg-text text-base border-text shadow-sm` + `aria-selected="true"`
  - `data-view-tab="campaign"` - Campaign - icon `bi-plus-square`
  - `data-view-tab="task"` - Task - icon `bi-list-task`
  - `data-view-tab="dependencies"` - Dependencies - icon `bi-box-seam`
  - `data-view-tab="settings"` - Settings - icon `bi-gear`
- Inactive class: `text-muted hover:text-text hover:bg-base border-transparent`
- Keep logo/darkmode/logout + Engine Status + disk-widget
- `role="tablist"` `aria-orientation="vertical"` `role="tab"` `aria-selected` seperti portal

## Main - 5 Sections
- `<main>` berisi 5 sections:
  - `id="sesi-section"` - default visible (tanpa `hidden`) - berisi dashboard (d_total, d_clips, d_story, d_fb, d_viral, d_storylist) + sessions list + filters (filterStatus, filterCampaignSel, sortBy) + pagination (pageInfo, prevPage, nextPage) + bulkBar + detailModal/renderModal/regenModal tetap berfungsi
  - `id="campaign-section"` - `hidden` - form sederhana: textarea `campaignBrief` + input `campaignSources` hint URL + button `Buat Campaign` POST `/api/campaigns` dengan JSON `{brief, sources}` + log + alternatif link TernakKlip
  - `id="task-section"` - `hidden` - queue: table `taskBody` polling `/api/tasks` tiap 1.5s (hanya saat tab visible), progress bar, durasi, log, STOP via POST `/api/tasks/stop` + polling `/api/tasks/log`, auto-refresh
  - `id="dependencies-section"` - `hidden` - reuse dependencies.html: System Overview (host, uptime, memory, CPU) + Binaries table `depBinBody` ffmpeg/deno/yt-dlp/mediapipe + Python Packages `depPkgBody` + Whisper models `depWhisperBody` (tiny/base/small/medium/large-v3) + AI Proxy Detail (base_url, model, api_key, status) - endpoint `/api/dependencies`, `/api/binaries`, `/api/system`, `/api/python/packages`, `/api/whisper/models`, `/api/dependencies/install`
  - `id="settings-section"` - `hidden` - reuse settings.html: base_url (`s_server_url`), api_key (`s_hf_api_key`), model (`s_hf_model`/`s_hf_model_filter`), ai_providers (`s_ai_providers` JSON), temperature, subtitle_language, resolution, aspect_ratio, fw_model, captions + save POST `/api/config` + Test Koneksi `/api/test-llm`

## JS initClipperTabs
- `function initClipperTabs()` - copy pattern portal `initPortalViewTabs`:
  - guard `if (window._clipperTabsWired) return; window._clipperTabsWired = true;`
  - KEY `clipperViewTab` default `sesi`
  - query sections: `sesiSection`, `campaignSection`, `taskSection`, `depSection`, `settingsSection`
  - `applyView(tab)` toggle `hidden` via `classList.toggle('hidden', !isX)`, buttons `aria-selected` + `className` active `bg-text text-base border-text shadow-sm` vs inactive `text-muted hover:text-text hover:bg-base border-transparent`, localStorage persist, hash fallback (`location.hash`), history.replaceState
  - lazy load: task -> `refreshTasks()`, dependencies -> `refreshDeps()`, settings -> `loadSettings()`
  - `DOMContentLoaded` + immediate call `try { initClipperTabs(); } catch(e) {}`
  - `window.switchToTab` exposed untuk dependencies/settings "Buka Settings"
- Existing JS (load/render/search/pagination/detailModal, pollTasks, checkEngineStatus, loadDash) tetap utuh, berjalan saat sesi visible
- Campaign/Task/Dependencies/Settings modules isolated IIFE, tidak clash

## Verifikasi
- node --check inline JS: 9 scripts semua OK (tailwind, force clear, big_script 32010 chars, initClipperTabs 3058, campaign 1621, task 6466, deps 10361, settings 5860, serviceWorker 147)
- div balance per tab: sesi 28/28 OK, campaign 5/5 OK, task 5/5 OK, dependencies 42/42 OK, settings 19/19 OK
- overall: div 205/205 OK, section 12/12 OK, script 13/13 OK
- no em dash ( — ) - tidak ada
- portal-bg kept (`<div class="portal-bg" aria-hidden="true"><i></i><i></i><i></i></div>`)
- padat classes kept: text-[11px], bg-surface-1, card-panel, min-h-[36px], md:min-h-[44px]
- 5 buttons + 5 sections verified, sesi default visible, lainnya hidden
