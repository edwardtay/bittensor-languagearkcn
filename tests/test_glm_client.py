import httpx
import pytest
import respx

from languageark.glm_client import (
    AnthropicJudge,
    ClaudeCodeJudge,
    DeepSeekJudge,
    GLMClient,
    GLMError,
    KimiJudge,
    MockGLMClient,
    QwenJudge,
    long_name,
    make_glm,
)

DEFAULT_BASE_URL = GLMClient.BASE_URL


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


def _clear_all_keys(monkeypatch):
    for k in (
        "ZHIPU_API_KEY", "DASHSCOPE_API_KEY", "MOONSHOT_API_KEY",
        "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_JUDGE", "LANGUAGEARK_JUDGE",
    ):
        monkeypatch.delenv(k, raising=False)


def test_make_glm_factory_order(monkeypatch):
    """Factory prefers Chinese sponsors first, then Claude, then mock."""
    _clear_all_keys(monkeypatch)
    # Block claude CLI auto-detect so we get a clean fall-through to Mock
    monkeypatch.setattr("languageark.glm_client.shutil.which", lambda _: None)

    assert isinstance(make_glm(), MockGLMClient)

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert isinstance(make_glm(), AnthropicJudge)

    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test")
    assert isinstance(make_glm(), DeepSeekJudge)

    monkeypatch.setenv("MOONSHOT_API_KEY", "mk-test")
    assert isinstance(make_glm(), KimiJudge)

    monkeypatch.setenv("DASHSCOPE_API_KEY", "qw-test")
    assert isinstance(make_glm(), QwenJudge)

    monkeypatch.setenv("ZHIPU_API_KEY", "test")
    assert isinstance(make_glm(), GLMClient)


def test_make_glm_override_via_env(monkeypatch):
    """LANGUAGEARK_JUDGE forces a specific judge regardless of env keys."""
    _clear_all_keys(monkeypatch)
    monkeypatch.setenv("ZHIPU_API_KEY", "z")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "d")
    monkeypatch.setenv("LANGUAGEARK_JUDGE", "deepseek")
    assert isinstance(make_glm(), DeepSeekJudge)
    monkeypatch.setenv("LANGUAGEARK_JUDGE", "kimi")
    monkeypatch.setenv("MOONSHOT_API_KEY", "m")
    assert isinstance(make_glm(), KimiJudge)
    monkeypatch.setenv("LANGUAGEARK_JUDGE", "mock")
    assert isinstance(make_glm(), MockGLMClient)


def test_make_glm_unknown_override_raises(monkeypatch):
    _clear_all_keys(monkeypatch)
    monkeypatch.setenv("LANGUAGEARK_JUDGE", "gpt-5")
    with pytest.raises(GLMError, match="unknown"):
        make_glm()


@pytest.mark.parametrize("cls,env_key", [
    (DeepSeekJudge, "DEEPSEEK_API_KEY"),
    (KimiJudge,     "MOONSHOT_API_KEY"),
    (QwenJudge,     "DASHSCOPE_API_KEY"),
])
async def test_openai_compat_judges_share_translate(monkeypatch, cls, env_key):
    """Each OpenAI-compatible Chinese judge uses the same wire shape."""
    monkeypatch.setenv(env_key, "test-key")
    with respx.mock(base_url=cls.BASE_URL) as router:
        router.post("/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": f"hi-from-{cls.__name__}"}}]},
            )
        )
        client = cls()
        r = await client.translate("test", "nan", "zh-Hans")
        assert r.translation == f"hi-from-{cls.__name__}"
        assert r.model == cls.DEFAULT_MODEL


def test_claude_code_judge_requires_cli(monkeypatch):
    monkeypatch.setattr("languageark.glm_client.shutil.which", lambda _: None)
    with pytest.raises(GLMError, match="claude CLI"):
        ClaudeCodeJudge()


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
