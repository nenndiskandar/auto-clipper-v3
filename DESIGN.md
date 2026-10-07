# DESIGN.md — Auto Clipper v3 (portal-dark)

## Identity
Auto Clipper v3 — creator tool untuk kreator TikTok/Reels/Shorts (bukan landing, bukan infra). Python engine + Node webjs + PWA dark-only seperti Iskan Portal. Dipakai harian untuk upload long-form, render 9:16, monitor session dan tasks. Karakter: kerja cepat dan tenang, panel padat yang langsung kebaca, bukan neon cinematic.

## Palette (R-01, R-29)
- Dark-only single `:root` — base #09090b page, surface #18181b, surface-2 #1f1f23, inset #0c0c0e, border #27272a, border-hover #3f3f46. Text #f4f4f5 primary 18:1 di base, #a1a1aa muted 7.7:1 = PASS AA. Tanpa cabang light, tanpa `html.dark`.
- Accent SATU: teal #14b8a6, hover #0f766e, accent-text #09090b, dipakai hanya untuk aksi primer + active nav + focus ring (alasan: satu titik fokus per layar, kreator tahu tombol utama tanpa scan). Focus ring #14b8a6, selection teal di atas base.
- Fungsional dibatasi: toast success/error/info versi dark-only + status render (amber pulse, emerald done, red error) hanya di badge/dot dan log, bukan palet baru per halaman.
- Chart dan log tidak menambah warna inti, reuse accent + muted.
- R-29: 2 netral + 1 accent, fungsional hanya untuk status yang butuh beda tanpa label panjang.

## Typography (R-06)
- Body dan heading: ui-sans-serif system stack (`ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto`), mono hanya untuk log/timecode (`ui-monospace, SFMono-Regular, Menlo, Consolas`), bukan headline (alasan: dense panel + angka tabular terbaca di 11-13px tanpa download font, tanpa FOUC).
- Tidak ada Outfit/Jakarta, tidak ada @import Google Fonts, tidak ada uppercase tracking ekstrem, tidak ada monospace besar sebagai dekor.
- Ukuran: judul xs semibold uppercase tracking-wide, angka/body sm, label 10-11px, semua dengan line-height 1.5 agar panel rapat tetap lega.

## Layout (R-05)
- App shell: `body flex` + `#portal-sidebar` collapse 240 ke 64 (desktop) / drawer 280 (mobile) + `#portal-main flex-1 flex flex-col min-w-0` + header portal `mb-2 border-b border-border pb-2` (alasan: ops kreator butuh nav persisten seperti portal, bukan top sub-nav per halaman).
- Sidebar header 57px: brand "I" + label "Auto Clipper", toggle collapse 240/64 + overlay `bg-base/60 backdrop-blur-sm lg:hidden` + mobile close. Nav 5 tab `role=tablist` (sesi/campaign/task/dependencies/settings) pakai SVG stroke 1.8, active `bg-text text-base border-text shadow-sm`, inactive `text-muted hover:text-text hover:bg-base border-transparent`.
- Urutan mengikuti alur kreator: Sesi -> Campaign -> Task -> Dependencies -> Settings. Deep-link `#sesi|#campaign|#task|#dependencies|#settings` via hash + `localStorage[clipperViewTab]`, lazy refresh per tab.
- Grid: library dan tasks pakai card list 1 kolom mobile / 2 kolom tablet, bukan bento mosaic. Variasi ritme dari konten (thumbnail 9:16 vs progress bar vs log), bukan dari ukuran kartu acak.
- Panel: `.card-panel` bg surface border + `shadow-card` ringan, hover hanya `border-color var(--border-hover)` + accent di active, tanpa shadow besar. Input/select/textarea `bg-surface border` dengan `min-h 44px` untuk tap target.

## Motion & Decoration (R-10, R-13, R-19)
- Aurora portal 3 layer radial blur 60px (teal rgba 13,148,136,0.52 / sky 14,165,233,0.46 / rose 244,63,94,0.65) drift alternate 6s/7s/8s via `.portal-bg fixed inset-0 z-0 pointer-events-none`, opacity .75 (alasan R-19: drift lambat di belakang memberi energi tanpa mencuri fokus; konten tetap hover saja).
- Hover: `transition border-color 0.2s` dan `bg-surface-2` pada nav/card, collapse `transition width .28s + transform .28s`, tanpa scale/bounce.
- Dose cap: backdrop-blur hanya di sidebar surface/60 + overlay mobile + modal backdrop (tidak simultan di desktop), shadow hanya `shadow-card` dan `shadow-modal`, glow tidak dipakai di card/button/badge sekaligus (R-10/R-13 PASS).
- `prefers-reduced-motion: reduce` melambatkan aurora ke 12s + matikan shimmer/pulse. Nonaktifkan total: `body.portal-off .portal-bg{display:none}`.

## Dials (Part 3)
Dial: ENERGY 2 / RHYTHM 2 / MOTION 2
- ENERGY 2: balanced (Stripe/Vercel) — alat kreator harian, tidak berteriak seperti agency, tidak mati seperti form admin.
- RHYTHM 2: konsisten dengan break — grid library vs form campaign vs task list vs dependencies table vs settings grouped, variasi dari kebutuhan konten bukan mosaic.
- MOTION 2: hover + aurora slow drift + sidebar collapse transition (alasan di atas). Tidak ada scroll-reveal cinematic di konten.

Reading: creator tool untuk kreator TikTok/Reels, dalam bahasa dashboard ops gelap portal, dial ENERGY 2 / RHYTHM 2 / MOTION 2.

## Liveliness Levers
- Focal: satu accent teal per layar (CTA Buat Campaign/Simpan + active nav), sisanya netral.
- Hierarchical contrast: judul xs uppercase muted, angka/title sm semibold primary, label 10px muted, dibedakan sengaja bukan seragam.
- Whitespace structural: p-1.5/p-2 sebagai scale padat portal, gap-1/1.5 konsisten, bukan sisa.
- Identity motif: dot status h-2 w-2 + border tipis kategori, diulang di sesi list, task, dependencies.
- Accent sengaja sparing: tidak dipakai di icon dekor, hanya di aksi yang mengubah state.

## R-31 — One-line Reasons
- Dark-only portal (bukan light-first + toggle): satu ground #09090b, kreator dan ops portal berbagi bahasa visual, tidak ada cabang tema ganda yang harus diverifikasi dua kali.
- Accent teal #14b8a6 single: satu warna aksi yang kontras di base tanpa ganti hue, mudah diingat kreator.
- System sans (bukan Outfit/Jakarta): tanpa download font, panel dense tetap terbaca, tanpa FOUC.
- Sidebar collapse 240/64 + drawer: nav persisten di desktop, hemat ruang saat render list panjang, tetap reachable di mobile.
- Card-panel dengan border-hover accent: feedback tanpa shadow berat yang menaikkan noise visual.
- Min-h 44px di button/input: tap target aman di HP saat upload di lapangan.
- Toast dan modal pakai token var: warna status konsisten tanpa duplikasi CSS.
- Portal aurora teal/sky/rose blur 60px drift 6s/7s/8s di belakang konten (R-01 ALLOWED: hierarchy/identity, satu-satunya dekor global; R-19 ALLOWED: slow drift ambient, bukan endless pulse di konten).

## Tabs Pipeline (index.html 5 tabs)
- Sidebar `index.html` memakai `role=tablist` + 5 `button[data-view-tab]`: `sesi` / `campaign` / `task` / `dependencies` / `settings`, masing-masing ke `section#{id}-section` (hidden toggle via `initClipperTabs()` mirror `initPortalViewTabs()` + `clipperViewTab`/`clipperSidebarCollapsed` di localStorage). Deep-link `#sesi|#campaign|#task|#dependencies|#settings` via `location.hash` + `hashchange`, lazy refresh: `task` ke `refreshTasks()`, `dependencies` ke `refreshDeps()`, `settings` ke `loadSettings()`. Collapse + overlay + `Escape` + `resize` identik portal.
- Sidebar portal dipertahankan: `hidden lg:flex` desktop, nav `p-2 space-y-0.5`, tombol `gap-2.5 min-h-[44px] lg:min-h-[40px] px-3 rounded-md text-sm`. Active `bg-text text-base border-text shadow-sm`, bukan gaya lama `rounded-lg min-h-28`.
- R-01/R-19 aurora note: `.portal-bg` 3x`<i>` radial blur(60px) teal/sky/rose drift alternate 6s/7s/8s (`portal-drift-a/b/c`), `fixed inset-0 z-0 pointer-events-none`, konten `z-1` di atasnya. `prefers-reduced-motion` ke 12s; `body.portal-off` mematikan total.

## Portal Alignment — why total CSS rewrite
- Satu bahasa visual: v3 sekarang memakai tailwind.config + token + sidebar + header + aurora identik portal, jadi tidak ada dua design system yang harus diingat.
- Satu perilaku nav: collapse 240/64 + drawer + overlay + persist localStorage sama persis, kreator yang biasa portal langsung paham v3.
- Satu maintenance: dark-only tanpa cabang light, tanpa Google Fonts, tanpa darkmode toggle; verifikasi kontras dan click-through cukup sekali.

## Notes
Dark-only keputusan produk (samakan portal ops malam), bukan "dark looks tech" (R-21). Tidak ada light toggle karena tool internal kreator yang dipadankan portal. Tidak ada landing hero, bento, atau fake terminal di app shell. Dekorasi hanya yang melayani monitoring: aurora belakang + hover + collapse transition.
