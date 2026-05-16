"""Zhipu GLM-4.6 API client.

Used by validators for back-translation BLEU scoring. Picked GLM over GPT/Claude
because (a) Zhipu sponsors the hackathon, (b) it outperforms on Chinese benchmarks
(C-Eval, CMMLU), (c) free credits via sponsor, (d) no GFW friction at the demo.
"""
from __future__ import annotations

import os
from typing import Literal

import httpx
from pydantic import BaseModel

DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
DEFAULT_MODEL = "glm-4.6"


class GLMError(Exception):
    pass


class TranslationResult(BaseModel):
    src: str
    tgt: str
    translation: str
    model: str


class GLMClient:
    """Minimal async client. Validators batch translate during scoring."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = 30.0,
    ) -> None:
        key = api_key or os.environ.get("ZHIPU_API_KEY")
        if not key:
            raise GLMError("ZHIPU_API_KEY not set and no api_key passed")
        self._key = key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def translate(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        *,
        temperature: float = 0.0,
    ) -> TranslationResult:
        """Translate text via GLM. We prompt for terse output, no commentary."""
        prompt = (
            f"You are a professional translator. Translate the following from "
            f"{src_lang} into {tgt_lang}. Output ONLY the translation, no quotes, "
            f"no commentary, no explanation. Keep proper nouns. Preserve register.\n\n"
            f"Source ({src_lang}): {text}\n\nTranslation ({tgt_lang}):"
        )
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
            raise GLMError(f"GLM API {resp.status_code}: {resp.text[:200]}")
        body = resp.json()
        try:
            content = body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            raise GLMError(f"Unexpected GLM response shape: {body}") from e
        return TranslationResult(src=src_lang, tgt=tgt_lang, translation=content, model=self._model)


# Convenience for Hokkien: long-form name maps for the prompt
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
