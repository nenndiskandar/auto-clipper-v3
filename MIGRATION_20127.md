# Migrasi base_url 20128 -> 20127 opencos
Tanggal: 2026-10-07 WIB
Scope: auto-clipper-v3/config.example.json + config/config_manager.py

Edits:
- config.example.json: 10 base_url 20128 -> 20127 (1 top-level + 7 chat providers + caption_maker + hook_maker)
- config/config_manager.py: 3 edits (base var line 242, caption_maker 294, hook_maker 302)
Total 20127: 13 (10 + 3), 20128: 0

Verify:
- grep -n 20127 count 13 (>=9 OK), grep 20128 count 0 OK
- python3 -m py_compile OK, json.tool OK
- migrate/backfill: _get_default_ai_providers all 20127, _migrate_to_multi_provider preserves 20127 when seeded with 20127
- runtime: 20127 next-server 9router, 20128 omniroute; /root/.hermes/config.yaml base_url 127.0.0.1:20127

Probe:
- GET http://127.0.0.1:20127/v1/models no-auth -> 200, 875 models, has opencos true
- GET http://127.0.0.1:20128/v1/models no-auth -> 401
- POST http://127.0.0.1:20127/v1/chat/completions model=opencos auth=OPENAI_API_KEY(len=35) -> 200 (3 payloads: 200,200,200; last returned "Pong! How can I help you today?" finish stop)
