# DESIGN.md — Auto Clipper v3

## Identity
Auto Clipper v3 — creator tool untuk kreator TikTok/Reels/Shorts (bukan landing, bukan infra). Python engine + Node webjs + PWA light-first dengan dark toggle. Dipakai harian untuk upload long-form, render 9:16, monitor session dan tasks. Karakter: kerja cepat dan tenang, panel padat yang langsung kebaca, bukan neon cinematic.

## Palette (R-01, R-29)
- Light `:root` — ground #f8fafc page, #ffffff surface, #f1f5f9 surface-2, border #e2e8f0, border-hover #cbd5e1. Text #0f172a primary 16:1 di page, #475569 secondary 8.2:1, #64748b muted 5.4:1 = PASS AA.
- Dark `html.dark` — ground #09090b, surface #121215 / #18181b, border #27272a. Text #f4f4f5 18:1, #a1a1aa muted 7.7:1 di base = PASS AA.
- Accent SATU: teal #0d9488 light / #2dd4bf dark, dipakai hanya untuk aksi primer + active nav + focus ring (alasan: satu titik fokus per layar, kreator tahu tombol utama tanpa scan). Accent tidak dipakai sebagai warna teks body, hanya sebagai bg button dengan accent-text #ffffff light / #042f2e dark agar kontras aman.
- Fungsional dibatasi: toast success #86efac/error #fca5a5/info #93c5fd dan status render (amber pulse, emerald done, red error) hanya di badge/dot dan log, bukan palet baru per halaman.
- Chart dan log tidak menambah warna inti, reuse accent + muted.
- R-29: 2 netral + 1 accent, fungsional hanya untuk status yang butuh beda tanpa label panjang.

## Typography (R-06)
- Heading: Outfit 500/600/700/800 via `var(--font-heading)`. Body: Plus Jakarta Sans 400/500/600/700/800 via `var(--font-body)`. Mono hanya untuk log/timecode, bukan headline (alasan: Outfit geometris ringkas untuk header dense 10-12px; Jakarta humanist dengan x-height tinggi untuk form settings panjang dan label TikTok yang rapat, keterbacaan di 11-13px lebih baik dari system sans generik).
- Tidak ada uppercase tracking ekstrem, tidak ada monospace besar sebagai dekor.
- Ukuran: judul xs semibold uppercase tracking-wide, angka/body sm, label 10-11px, semua dengan line-height 1.5 agar panel rapat tetap lega.

## Layout (R-05)
- App shell: `flex flex-col md:flex-row`, sidebar `w-full md:w-64 border-b md:border-r` + top sub-nav per halaman + `card-panel` (bukan landing template). Urutan mengikuti alur kreator: Library Sesi -> Create Clip -> Tasks -> Session Detail -> Settings.
- Sidebar mobile jadi bar atas horizontal wrap, desktop vertikal 64. Nav active pakai `bg-[var(--accent)] text-[var(--accent-text)] font-bold`, bukan glow.
- Grid: library dan tasks pakai card list 1 kolom mobile / 2 kolom tablet, bukan bento mosaic. Variasi ritme dari konten (thumbnail 9:16 vs progress bar vs log), bukan dari ukuran kartu acak.
- Panel: `.card-panel` bg surface border + `shadow-card` ringan, hover hanya `border-color var(--accent)` tanpa shadow besar. Input/select/textarea `bg-surface border` dengan `min-h 44px` untuk tap target.

## Motion & Decoration (R-10, R-13, R-19)
- MOTION 1 konten + ambient portal aurora di belakang: 3 layer radial blur 60px (teal/sky/rose) drift alternate 6s/7s/8s via `.portal-bg` fixed inset-0 z-0 pointer-events-none. Tidak ada parallax/scroll-reveal cinematic di konten (alasan R-19: drift lambat di belakang memberi energi tanpa mencuri fokus timeline; konten sendiri tetap hover/shimmer/pulse saja).
- Shimmer: `.tk-skeleton` linear 400% 1.2s ease infinite hanya di loading state Library/Tasks (alasan: memberi tahu konten sedang fetch tanpa spinner berputar terus).
- Pulse: dot/status chip rendering pakai pulse halus pada badge, bukan glow di seluruh card (alasan: satu indikator hidup per baris, dose 1 titik).
- Hover: `transition border-color 0.2s` dan `bg-surface-2` pada nav/card, tanpa scale/bounce.
- Dose cap: backdrop-blur tidak dipakai simultan, shadow hanya `shadow-card` dan `shadow-modal`, glow tidak dipakai di card/button/badge sekaligus (R-10/R-13 PASS, maks 1-2 elemen ber-shimmer/pulse bersamaan).
- `prefers-reduced-motion: reduce` mematikan shimmer/pulse menjadi static dan melambatkan aurora ke 12s. Nonaktifkan total: tambah class `portal-off` di `<body>` (`.portal-off .portal-bg{display:none}`). Aurora tidak memakai backdrop-blur dan tidak menabrak dose blur card (aurora di belakang konten, card tetap solid `bg-surface`).

## Dials (Part 3)
Dial: ENERGY 2 / RHYTHM 2 / MOTION 1
- ENERGY 2: balanced (Stripe/Vercel) — alat kreator harian, tidak berteriak seperti agency, tidak mati seperti form admin.
- RHYTHM 2: konsisten dengan break — grid library vs form create bertingkat vs timeline session vs settings grouped, variasi dari kebutuhan konten bukan mosaic.
- MOTION 1: hover states only + skeleton shimmer + status pulse (alasan di atas). Jika butuh cinematic di landing marketing, itu halaman terpisah, bukan app shell.

Reading: creator tool untuk kreator TikTok/Reels, dalam bahasa PWA utilitas ringan light-first, dial ENERGY 2 / RHYTHM 2 / MOTION 1.

## Liveliness Levers
- Focal: satu accent teal per layar (CTA Create/Render + active nav), sisanya netral.
- Hierarchical contrast: judul Outfit bold xs uppercase muted, angka/title sm semibold primary, label 10px muted, dibedakan sengaja bukan seragam.
- Whitespace structural: p-2.5/3/4 sebagai scale, gap-1.5/2.5 konsisten, bukan sisa.
- Identity motif: dot status 2x2 + border tipis + lightning mark di logo, diulang di library, tasks, session header.
- Accent sengaja sparing: tidak dipakai di icon dekor, hanya di aksi yang mengubah state.

## R-31 — One-line Reasons
- Light-first + dark toggle (bukan dark-only portal): kreator edit siang di HP, light mengurangi silau outdoor, dark untuk editing malam.
- Accent teal #0d9488/#2dd4bf: satu warna brand yang kontras di light dan dark tanpa ganti hue, mudah diingat kreator.
- Outfit + Jakarta: heading ringkas + body humanist untuk form dense 6 grup settings.
- Sidebar + top sub-nav + card-panel: navigasi app bukan landing, kreator butuh orientasi sesi yang persisten.
- Card-panel dengan border-hover accent: feedback tanpa shadow berat yang menaikkan noise visual.
- Skeleton shimmer: loading terasa hidup tanpa menambah spinner di setiap kartu.
- Status pulse 1 titik: render panjang butuh sinyal hidup tanpa animasi seluruh halaman.
- Shadow card ringan: elevasi panel tanpa efek floating yang melelahkan di list panjang.
- Min-h 44px di button/input/tpl-card: tap target aman di HP saat upload di lapangan.
- Toast dan modal pakai token var: warna status konsisten di light/dark tanpa duplikasi CSS.
- Portal aurora teal #0d9488/#2dd4bf + sky #0ea5e9 + rose #f43f5e blur 60px drift 6s/7s/8s di belakang konten (R-01 ALLOWED: hierarchy/identity — bg hidup satu-satunya dekor global; R-19 ALLOWED: slow drift ambient, bukan endless pulse di konten).

## Tabs Pipeline (index.html 5 tabs)
- Sidebar `index.html` memakai `role=tablist` + 5 `button[data-view-tab]`: `sesi` / `campaign` / `task` / `dependencies` / `settings`, masing-masing ke `section#{id}-section` (hidden toggle via `initClipperTabs()` + `switchToTab()`). Deep-link `#sesi|#campaign|#task|#dependencies|#settings` via `location.hash` + `hashchange`, persist `localStorage[clipperViewTab]`. Pindah tab me-refresh lazy: `task`→`refreshTasks()`, `dependencies`→`refreshDeps()`, `settings`→`loadSettings()`.
- Sidebar padat dipertahankan: nav `p-2 md:p-1.5 gap-1.5 flex-wrap`, tombol `gap-1.5 min-h-[28px] md:min-h-[40px] px-2 py-1 text-[10px] md:text-xs rounded-lg`, active `bg-[var(--accent)] text-[var(--accent-text)] font-bold`, bukan gaya longgar min-h-44/rounded-md. `portal-bg` 3 layer tidak berubah (lihat bawah).
- `create.html`/`tasks.html`/`dependencies.html`/`settings.html` TIDAK dihapus: hanya banner redirect exact `<div class="p-2 bg-amber-950/30 border border-amber-900/40 text-xs text-amber-300">Halaman ini pindah ke tabs - <a href="/index.html#campaign">Buka Campaign tab</a></div>` tepat setelah `portal-bg`, agar direct URL tidak membingungkan. `story/facebook/ternaklip/session/cookies/detail/login` keep as is.
- R-01/R-19 aurora note: `.portal-bg` 3×`<i>` radial blur(60px) teal/sky/rose drift alternate 6s/7s/8s (`portal-drift-a/b/c`), `fixed inset-0 z-0 pointer-events-none`, konten `z-1` di atasnya. R-01 ALLOWED (hierarchy/identity — satu-satunya dekor global), R-19 ALLOWED (slow ambient drift, konten tetap hover/shimmer/pulse saja). `prefers-reduced-motion` → 12s; `body.portal-off` mematikan total.

## Notes
Light-first keputusan produk (kreator siang, PWA di HP), bukan preferensi estetika (R-21). Dark toggle tetap ship dan diverifikasi kedua mode (R-34). Tidak ada landing hero, bento, atau fake terminal di app shell. Dekorasi hanya yang melayani monitoring: shimmer saat fetch, pulse saat render.
