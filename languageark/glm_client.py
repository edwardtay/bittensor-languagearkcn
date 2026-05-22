"""LLM judge clients for back-translation BLEU scoring.

The validator picks the best available judge via `make_glm()`. Priority is
biased toward **Chinese-native models** for two reasons: (a) Hokkien / Min Nan
is a Sinitic language and Chinese-trained LLMs handle the script + register
better than English-first models, and (b) two of the ideathon sponsors are
Zhipu and Alibaba Cloud — having every major Chinese model wired in is itself
a 产品力 signal.

Wired judges, in `make_glm()` preference order:

  1. ZHIPU_API_KEY      → GLM-4.6           (Zhipu — primary sponsor)
  2. DASHSCOPE_API_KEY  → Qwen3-Max         (Alibaba Cloud — sponsor)
  3. MOONSHOT_API_KEY   → Kimi (Moonshot AI)
  4. DEEPSEEK_API_KEY   → DeepSeek-V3
  5. CLAUDE_CODE_JUDGE=1 (or `claude` CLI present) → Claude Code via Max sub
  6. ANTHROPIC_API_KEY  → Claude API
  7. (none)             → heuristic MockGLMClient

Override with `LANGUAGEARK_JUDGE=zhipu|qwen|kimi|deepseek|claude-code|anthropic|mock`.
"""
from __future__ import annotations

import asyncio
import os
import shutil
from typing import ClassVar

import httpx
from pydantic import BaseModel


class GLMError(Exception):
    pass


class TranslationResult(BaseModel):
    src: str
    tgt: str
    translation: str
    model: str


# ─── language-name helpers ──────────────────────────────────────────────────

LANG_NAMES: dict[str, str] = {
    "nan": "Hokkien (Min Nan, 闽南语)",
    "yue": "Cantonese (粤语)",
    "hak": "Hakka (客家话)",
    "wuu": "Wu Chinese (吴语)",
    "zh-Hans": "Simplified Mandarin Chinese (简体中文)",
    "zh-Hant": "Traditional Mandarin Chinese (繁體中文)",
    "en": "English",
}


def long_name(code: str) -> str:
    return LANG_NAMES.get(code, code)


def _translation_prompt(text: str, src_lang: str, tgt_lang: str) -> str:
    return (
        f"You are a professional translator. Translate the following from "
        f"{long_name(src_lang)} into {long_name(tgt_lang)}. Output ONLY the "
        f"translation, no quotes, no commentary, no explanation. Keep proper "
        f"nouns. Preserve register.\n\n"
        f"Source ({long_name(src_lang)}): {text}\n\n"
        f"Translation ({long_name(tgt_lang)}):"
    )


# ─── shared OpenAI-compatible client ────────────────────────────────────────

class OpenAICompatJudge:
    """Shared implementation for all OpenAI-`/chat/completions`-compatible APIs.

    Zhipu (GLM-4.6), Alibaba Dashscope (Qwen), Moonshot (Kimi) and DeepSeek
    all expose the same wire format, so subclasses only need to set
    `BASE_URL`, `DEFAULT_MODEL`, `ENV_KEY` and `DISPLAY_NAME`.
    """

    BASE_URL: ClassVar[str] = ""
    DEFAULT_MODEL: ClassVar[str] = ""
    ENV_KEY: ClassVar[str] = ""
    DISPLAY_NAME: ClassVar[str] = ""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        key = api_key or os.environ.get(self.ENV_KEY)
        if not key:
            raise GLMError(f"{self.ENV_KEY} not set and no api_key passed")
        self._key = key
        self._base_url = (base_url or self.BASE_URL).rstrip("/")
        self._model = model or self.DEFAULT_MODEL
        self._timeout = timeout

    @property
    def label(self) -> str:
        return f"{self.DISPLAY_NAME} ({self._model})"

    async def translate(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        *,
        temperature: float = 0.0,
    ) -> TranslationResult:
        prompt = _translation_prompt(text, src_lang, tgt_lang)
        async with httpx.AsyncClient(timeout=self._timeout) as http:
            resp = await http.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._key}"},
                json={
                    "model": self._model,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        if resp.status_code != 200:
            raise GLMError(
                f"{self.DISPLAY_NAME} API {resp.status_code}: {resp.text[:200]}"
            )
        body = resp.json()
        try:
            content = body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            raise GLMError(f"Unexpected {self.DISPLAY_NAME} response: {body}") from e
        return TranslationResult(
            src=src_lang, tgt=tgt_lang, translation=content, model=self._model
        )


class GLMClient(OpenAICompatJudge):
    """Zhipu GLM-4.6 — primary judge (ideathon sponsor)."""

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_MODEL = "glm-4.6"
    ENV_KEY = "ZHIPU_API_KEY"
    DISPLAY_NAME = "GLM-4.6 (Zhipu)"


class QwenJudge(OpenAICompatJudge):
    """Alibaba Dashscope — Qwen3 family. Sponsor (Alibaba Cloud).

    Uses the OpenAI-compatible endpoint so the wire format matches GLM/Kimi/DeepSeek.
    Endpoint: https://help.aliyun.com/zh/model-studio/developer-reference/compatibility-of-openai-with-dashscope
    """

    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEFAULT_MODEL = "qwen-max"
    ENV_KEY = "DASHSCOPE_API_KEY"
    DISPLAY_NAME = "Qwen (Alibaba)"


class KimiJudge(OpenAICompatJudge):
    """Moonshot AI — Kimi. Strong long-context Chinese model."""

    BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "moonshot-v1-8k"
    ENV_KEY = "MOONSHOT_API_KEY"
    DISPLAY_NAME = "Kimi (Moonshot)"


class DeepSeekJudge(OpenAICompatJudge):
    """DeepSeek — top open Chinese model (V3 / R1 family)."""

    BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"
    ENV_KEY = "DEEPSEEK_API_KEY"
    DISPLAY_NAME = "DeepSeek"


# ─── Anthropic (non-OpenAI wire format) ─────────────────────────────────────


class AnthropicJudge:
    """Claude via the official Anthropic Python SDK (metered API)."""

    DEFAULT_MODEL: ClassVar[str] = "claude-haiku-4-5-20251001"
    DISPLAY_NAME: ClassVar[str] = "Claude (Anthropic API)"
    ENV_KEY: ClassVar[str] = "ANTHROPIC_API_KEY"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        from anthropic import AsyncAnthropic  # optional dep

        key = api_key or os.environ.get(self.ENV_KEY)
        if not key:
            raise GLMError(f"{self.ENV_KEY} not set")
        self._client = AsyncAnthropic(api_key=key)
        self._model = model or self.DEFAULT_MODEL

    @property
    def label(self) -> str:
        return f"{self.DISPLAY_NAME} ({self._model})"

    async def translate(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        *,
        temperature: float = 0.0,
    ) -> TranslationResult:
        prompt = (
            f"Translate the following text from {long_name(src_lang)} to "
            f"{long_name(tgt_lang)}. Output ONLY the translation — no quotes, "
            f"no commentary, no explanation. Keep proper nouns. Preserve register.\n\n"
            f"Source: {text}"
        )
        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=512,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        translation = ("".join(parts)).strip()
        if not translation:
            raise GLMError(f"Empty Anthropic response: {resp}")
        return TranslationResult(
            src=src_lang, tgt=tgt_lang, translation=translation, model=self._model
        )


# ─── Claude via local Max-subscription CLI ──────────────────────────────────


class ClaudeCodeJudge:
    """Drive Claude through the local `claude` CLI (Max-subscription auth).

    No API key, no per-token billing — uses whatever auth `claude` is logged
    into. Costs ~1 s of CLI startup per call, so a 10-pair eval takes ~10 s
    instead of ~3 s. Fine for the demo.
    """

    DISPLAY_NAME: ClassVar[str] = "Claude Code (local CLI / Max sub)"
    _BIN: ClassVar[str] = "claude"

    def __init__(self, bin_path: str | None = None, timeout: float = 60.0) -> None:
        path = bin_path or shutil.which(self._BIN)
        if path is None:
            raise GLMError(
                "claude CLI not found on PATH — install Claude Code or set "
                "ANTHROPIC_API_KEY to use the API instead"
            )
        self._bin = path
        self._timeout = timeout

    @property
    def label(self) -> str:
        return self.DISPLAY_NAME

    async def translate(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        *,
        temperature: float = 0.0,  # accepted for interface parity; not used
    ) -> TranslationResult:
        prompt = _translation_prompt(text, src_lang, tgt_lang)
        proc = await asyncio.create_subprocess_exec(
            self._bin, "-p", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=self._timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise GLMError(f"claude CLI timed out after {self._timeout}s") from None
        if proc.returncode != 0:
            raise GLMError(
                f"claude CLI exited {proc.returncode}: {err.decode(errors='replace')[:200]}"
            )
        translation = out.decode(errors="replace").strip()
        if not translation:
            raise GLMError("claude CLI returned empty output")
        return TranslationResult(
            src=src_lang, tgt=tgt_lang, translation=translation, model="claude-code"
        )


# ─── Offline-demo fallback ─────────────────────────────────────────────────


class MockGLMClient:
    """Heuristic stand-in so the demo runs offline.

    Looks up the closest Hokkien (or FLORES Cantonese) sample by character
    Jaccard and returns the paired source as the "back-translation". Produces
    varying BLEU across the 3-tier mock miner outputs, ~80 % as informative
    as a real LLM, 100 % reliable.
    """

    DISPLAY_NAME: ClassVar[str] = "mock-heuristic (offline fallback)"

    def __init__(self) -> None:
        from .flores_loader import HOKKIEN_PAIRS, is_available, load_flores_pairs

        self._samples = [(p.mandarin, p.hokkien_han) for p in HOKKIEN_PAIRS]
        if is_available():
            for fp in load_flores_pairs("yue_Hant", "zho_Hans")[:50]:
                self._samples.append((fp.tgt_text, fp.src_text))

    @property
    def label(self) -> str:
        return self.DISPLAY_NAME

    async def translate(self, text: str, src_lang: str, tgt_lang: str) -> TranslationResult:
        best_zh, best_src = max(self._samples, key=lambda pair: _char_overlap(text, pair[0]))
        score = _char_overlap(text, best_zh)
        translation = best_src if score >= 0.3 else best_src[: max(2, len(best_src) // 2)]
        return TranslationResult(
            src=src_lang, tgt=tgt_lang, translation=translation, model="mock-glm"
        )


def _char_overlap(a: str, b: str) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


# ─── factory ────────────────────────────────────────────────────────────────


Judge = (
    GLMClient | QwenJudge | KimiJudge | DeepSeekJudge
    | ClaudeCodeJudge | AnthropicJudge | MockGLMClient
)


_FORCE_MAP: dict[str, type] = {
    "zhipu": GLMClient,
    "glm": GLMClient,
    "qwen": QwenJudge,
    "alibaba": QwenJudge,
    "kimi": KimiJudge,
    "moonshot": KimiJudge,
    "deepseek": DeepSeekJudge,
    "claude-code": ClaudeCodeJudge,
    "claudecode": ClaudeCodeJudge,
    "anthropic": AnthropicJudge,
    "claude": AnthropicJudge,
    "mock": MockGLMClient,
}


def make_glm() -> Judge:
    """Pick the best available judge.

    Override with ``LANGUAGEARK_JUDGE=<name>``. Otherwise the preference order
    is biased toward Chinese-native models (Hokkien/Min Nan is Sinitic; the
    sponsors are Chinese) before falling back to Claude / mock.
    """
    forced = os.environ.get("LANGUAGEARK_JUDGE", "").strip().lower()
    if forced:
        cls = _FORCE_MAP.get(forced)
        if cls is None:
            raise GLMError(
                f"LANGUAGEARK_JUDGE={forced!r} unknown — pick one of "
                f"{sorted(set(_FORCE_MAP))}"
            )
        return cls()

    if os.environ.get("ZHIPU_API_KEY"):
        return GLMClient()
    if os.environ.get("DASHSCOPE_API_KEY"):
        return QwenJudge()
    if os.environ.get("MOONSHOT_API_KEY"):
        return KimiJudge()
    if os.environ.get("DEEPSEEK_API_KEY"):
        return DeepSeekJudge()
    if os.environ.get("CLAUDE_CODE_JUDGE") == "1" or shutil.which("claude"):
        try:
            return ClaudeCodeJudge()
        except GLMError:
            pass
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicJudge()
    return MockGLMClient()
