import httpx
import pytest
import respx

from languageark.glm_client import DEFAULT_BASE_URL, GLMClient, GLMError, long_name


def test_long_name_known_codes():
    assert "Hokkien" in long_name("nan")
    assert "Cantonese" in long_name("yue")
    assert long_name("unknown-code") == "unknown-code"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    with pytest.raises(GLMError):
        GLMClient()


@respx.mock
async def test_translate_happy_path(monkeypatch):
    monkeypatch.setenv("ZHIPU_API_KEY", "test-key")
    respx.post(f"{DEFAULT_BASE_URL}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "你吃饱了吗?"}}],
            },
        )
    )
    client = GLMClient()
    res = await client.translate("你食飽未?", src_lang="Hokkien", tgt_lang="Mandarin")
    assert res.translation == "你吃饱了吗?"
    assert res.model == "glm-4.6"


@respx.mock
async def test_translate_api_error(monkeypatch):
    monkeypatch.setenv("ZHIPU_API_KEY", "test-key")
    respx.post(f"{DEFAULT_BASE_URL}/chat/completions").mock(
        return_value=httpx.Response(500, text="upstream boom")
    )
    client = GLMClient()
    with pytest.raises(GLMError, match="500"):
        await client.translate("你食飽未?", src_lang="Hokkien", tgt_lang="Mandarin")
