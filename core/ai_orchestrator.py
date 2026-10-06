"""
core/ai_orchestrator.py — v3 AI Gateway (OmniRoute / OpenAI-compatible)
Satu pintu untuk semua step AI: brief_parser, highlight, title, bgm, thumbnail, qc.
Memakai openai>=1.0 Python SDK. Tiap provider punya base_url/api_key/model sendiri.
"""
import json
import re
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # di-install via requirements.txt, pakai venv v2 untuk test
from utils.logger import debug_log


JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.S)

def _extract_json(text: str) -> Any:
    """Ambil JSON dari response yang kadang dibungkus fence / prose."""
    if not text:
        return None
    text = text.strip()
    # fence
    m = JSON_FENCE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # direct
    try:
        return json.loads(text)
    except Exception:
        pass
    # cari kurung pertama
    for start, end in [("[", "]"), ("{", "}")]:
        s = text.find(start)
        e = text.rfind(end)
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(text[s:e+1])
            except Exception:
                continue
    return None


class AIOrchestrator:
    """Thin wrapper — satu instance per AutoClipperCore, re-use OpenAI clients."""

    def __init__(self, ai_providers: dict | None):
        self.providers = ai_providers or {}
        self._clients: dict[str, OpenAI] = {}

    def _client(self, provider_key: str):
        cfg = self.providers.get(provider_key) or {}
        base_url = cfg.get("base_url") or "https://api.openai.com/v1"
        api_key = cfg.get("api_key") or ""
        model = cfg.get("model") or "gpt-4o-mini"
        if not api_key:
            debug_log(f"[AI] provider {provider_key} tanpa api_key — skip")
            return None, cfg
        if OpenAI is None:
            debug_log(f"[AI] openai lib belum install — pip install -r requirements.txt dulu")
            return None, cfg
        if provider_key not in self._clients:
            try:
                self._clients[provider_key] = OpenAI(api_key=api_key, base_url=base_url)
            except Exception as e:
                debug_log(f"[AI] gagal buat client {provider_key}: {e}")
                return None, cfg
        return self._clients[provider_key], cfg

    def chat_json(
        self,
        provider_key: str,
        system: str | None,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        fallback: Any = None,
    ) -> Any:
        """Chat → parse JSON. Return fallback jika gagal."""
        client, cfg = self._client(provider_key)
        if client is None:
            return fallback
        model = cfg.get("model") or "gpt-4o-mini"
        sys_msg = system or cfg.get("system_message") or ""
        # allow template vars still in system_message
        try:
            msgs = []
            if sys_msg:
                msgs.append({"role": "system", "content": sys_msg})
            msgs.append({"role": "user", "content": user})
            # minta JSON mode kalau provider support
            extra = {}
            if "response_format" not in cfg:
                # hint JSON via system, tidak paksa response_format biar kompatibel OmniRoute
                pass
            else:
                extra["response_format"] = cfg["response_format"]
            resp = client.chat.completions.create(
                model=model,
                messages=msgs,
                temperature=float(cfg.get("temperature", temperature)),
                max_tokens=int(cfg.get("max_tokens", max_tokens)),
                **extra,
            )
            text = (resp.choices[0].message.content or "").strip()
            parsed = _extract_json(text)
            if parsed is not None:
                return parsed
            debug_log(f"[AI:{provider_key}] bukan JSON, raw 300ch: {text[:300]}")
            return fallback
        except Exception as e:
            debug_log(f"[AI:{provider_key}] error: {e}")
            return fallback

    def chat_text(self, provider_key: str, system: str | None, user: str, temperature: float = 0.7) -> str | None:
        client, cfg = self._client(provider_key)
        if client is None:
            return None
        model = cfg.get("model") or "gpt-4o-mini"
        sys_msg = system or cfg.get("system_message") or ""
        try:
            msgs = []
            if sys_msg:
                msgs.append({"role": "system", "content": sys_msg})
            msgs.append({"role": "user", "content": user})
            resp = client.chat.completions.create(
                model=model,
                messages=msgs,
                temperature=float(cfg.get("temperature", temperature)),
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            debug_log(f"[AI:{provider_key}] chat_text error: {e}")
            return None
