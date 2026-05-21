import httpx
import pytest
import respx

from languageark.glm_client import (
    DEFAULT_BASE_URL,
    AnthropicJudge,
    GLMClient,
    GLMError,
    MockGLMClient,
    long_name,
    make_glm,
)


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


def test_make_glm_factory_order(monkeypatch):
    """Factory prefers ZHIPU > ANTHROPIC > Mock."""
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(make_glm(), MockGLMClient)

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert isinstance(make_glm(), AnthropicJudge)

    monkeypatch.setenv("ZHIPU_API_KEY", "test")
    assert isinstance(make_glm(), GLMClient)


def test_anthropic_judge_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(GLMError):
        AnthropicJudge()


async def test_anthropic_judge_translate(monkeypatch):
    """The AnthropicJudge maps Anthropic responses → TranslationResult."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    class _Block:
        type = "text"
        text = "你吃饱了吗?"

    class _Resp:
        content = [_Block()]

    class _Messages:
        async def create(self, **kwargs):
            assert "Hokkien" in kwargs["messages"][0]["content"]
            return _Resp()

    class _FakeAsyncAnthropic:
        def __init__(self, api_key):
            self.messages = _Messages()

    import languageark.glm_client as mod

    monkeypatch.setattr(
        "anthropic.AsyncAnthropic", _FakeAsyncAnthropic, raising=True
    )
    j = AnthropicJudge()
    res = await j.translate("你食飽未?", src_lang="nan", tgt_lang="zh-Hans")
    assert res.translation == "你吃饱了吗?"
    assert res.model == AnthropicJudge.DEFAULT_MODEL
