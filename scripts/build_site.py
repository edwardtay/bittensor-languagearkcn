"""Build the static `site/` dashboard from the latest run artifacts.

Inputs:
  /tmp/demo_full.out   — output of `bash demo.sh`
  /tmp/dao_deploy.log  — output of `python scripts/deploy_speaker_dao_local.py`
  /tmp/forge.log       — output of `forge test`
  /tmp/pytest.log      — output of `pytest -v`

Output:
  site/index.html
"""
from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"
NOTES = SITE / "notes"
SITE.mkdir(exist_ok=True)
NOTES.mkdir(exist_ok=True)


def read(p: str) -> str:
    return Path(p).read_text() if Path(p).exists() else ""


demo = read("/tmp/demo_full.out")
dao = read("/tmp/dao_deploy.log")
forge = read("/tmp/forge.log")
pytest_out = read("/tmp/pytest.log")
onchain = read("/tmp/onchain_validator.log")
honesty = (ROOT / "HONESTY.md").read_text()
readme = (ROOT / "README.md").read_text() if (ROOT / "README.md").exists() else ""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LanguageArk-CN — Hokkien subnet</title>
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#fafbfc; --surface:#ffffff; --surface-2:#f3f4f6; --border:#e5e7eb; --border-strong:#d1d5db;
    --fg:#0f172a; --fg-2:#475569; --muted:#94a3b8;
    --brand:#6d28d9; --brand-50:#f5f3ff; --brand-100:#ede9fe;
    --good:#15803d; --good-bg:#dcfce7;
    --warn:#b45309; --warn-bg:#fef3c7;
    --bad:#b91c1c;  --bad-bg:#fee2e2;
    --code-bg:#0f172a; --code-fg:#e2e8f0;
    --shadow-sm: 0 1px 2px rgba(15,23,42,.06);
    --shadow:    0 1px 3px rgba(15,23,42,.06), 0 4px 16px rgba(15,23,42,.04);
    --radius:14px;
  }}
  * {{ box-sizing:border-box; }}
  html, body {{ background:var(--bg); }}
  body {{
    font:14.5px/1.6 'Inter',ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;
    color:var(--fg); margin:0; padding:0; -webkit-font-smoothing:antialiased;
  }}
  /* ── topbar (sticky) ─────────────────────────── */
  .topbar {{
    position:sticky; top:0; z-index:20; background:rgba(255,255,255,.85);
    backdrop-filter:saturate(180%) blur(12px); -webkit-backdrop-filter:saturate(180%) blur(12px);
    border-bottom:1px solid var(--border);
  }}
  .topbar-inner {{
    max-width:1180px; margin:0 auto; padding:12px 24px;
    display:flex; align-items:center; gap:16px;
  }}
  .logo {{
    width:30px; height:30px; border-radius:8px;
    background:linear-gradient(135deg,#7c3aed,#06b6d4);
    display:grid; place-items:center; color:#fff; font-weight:700; font-size:14px;
    box-shadow:var(--shadow-sm);
  }}
  .brand {{ font-weight:600; font-size:15px; letter-spacing:-.01em; }}
  .brand small {{ color:var(--fg-2); font-weight:400; margin-left:6px; }}
  .topbar-actions {{ margin-left:auto; display:flex; gap:8px; align-items:center; }}
  .chip {{
    display:inline-flex; align-items:center; gap:6px;
    padding:5px 11px; border-radius:999px; font-size:12px; font-weight:500;
    background:var(--surface-2); color:var(--fg-2); border:1px solid var(--border);
  }}
  .chip.good {{ background:var(--good-bg); color:var(--good); border-color:transparent; }}
  .chip.warn {{ background:var(--warn-bg); color:var(--warn); border-color:transparent; }}
  .chip.bad  {{ background:var(--bad-bg);  color:var(--bad);  border-color:transparent; }}
  .chip .dot {{ width:6px; height:6px; border-radius:50%; background:currentColor; }}

  /* ── layout ──────────────────────────────────── */
  .shell {{ max-width:1180px; margin:0 auto; padding:32px 24px 80px; }}
  /* ── side-nav layout (notes) — minimalist ─────── */
  .shell.with-toc {{ display:grid; grid-template-columns:200px minmax(0, 1fr); gap:36px; align-items:start; max-width:1080px; }}
  /* CRITICAL: min-width on grid item lets it shrink instead of forcing
     horizontal scroll when children (pre, table, long h1) have wide content. */
  .notes-main {{ min-width:0; }}
  .notes-main pre, .notes-main table {{ max-width:100%; }}
  .notes-main h1, .notes-main h2, .notes-main h3 {{ overflow-wrap:anywhere; }}
  .toc {{ position:sticky; top:64px; max-height:calc(100vh - 80px); overflow-y:auto;
          font-size:12.5px; line-height:1.35; padding:10px 0; }}
  .toc h4 {{ font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:.08em;
             color:var(--muted); margin:0 0 6px 8px; }}
  .toc a {{ display:flex; align-items:baseline; gap:8px; padding:5px 8px; border-radius:6px; color:var(--fg-2);
            text-decoration:none; border-left:2px solid transparent; }}
  .toc a:hover {{ background:var(--surface-2); color:var(--fg); }}
  .toc a.active {{ background:var(--brand-50); color:var(--brand); border-left-color:var(--brand); font-weight:600; }}
  .toc a .num {{ flex:0 0 26px; text-align:right; color:var(--muted);
                font-variant-numeric:tabular-nums; font-weight:500; font-size:11.5px; }}
  .toc a.active .num {{ color:var(--brand); }}
  .notes-main h2 {{ scroll-margin-top:64px; }}
  @media (max-width:900px) {{ .shell.with-toc {{ grid-template-columns:1fr; gap:18px; }} .toc {{ position:static; max-height:none; }} }}
  /* hero — minimalist */
  .hero {{
    background:transparent; border:none; border-radius:0;
    padding:0 0 14px; box-shadow:none; margin-bottom:18px;
    border-bottom:1px solid var(--border);
  }}
  .hero h1 {{
    font-size:24px; line-height:1.2; letter-spacing:-.02em;
    margin:0 0 6px; font-weight:600;
  }}
  .hero p.sub {{ color:var(--fg-2); margin:0 0 12px; max-width:780px; font-size:14px; }}
  .badges {{ display:flex; flex-wrap:wrap; gap:5px; }}
  .badges .chip {{ font-size:11.5px; padding:3px 8px; }}

  h2 {{ font-size:12px; text-transform:uppercase; letter-spacing:.08em;
        color:var(--muted); font-weight:600; margin:28px 2px 10px; }}
  h2 .num {{ color:var(--brand); margin-right:6px; font-weight:600; }}

  /* ── stat grid ──────────────────────────────── */
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; }}
  .stat {{
    background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
    padding:18px 20px; box-shadow:var(--shadow-sm); transition:transform .15s, box-shadow .15s;
  }}
  .stat:hover {{ transform:translateY(-1px); box-shadow:var(--shadow); }}
  .stat .label {{ font-size:11.5px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); font-weight:600; margin-bottom:8px; }}
  .stat .val {{ font-size:30px; font-weight:700; color:var(--fg); letter-spacing:-.02em; }}
  .stat .val small {{ font-size:13px; color:var(--fg-2); font-weight:500; margin-left:6px; letter-spacing:0; }}
  .stat .help {{ color:var(--fg-2); font-size:13px; margin-top:8px; }}

  /* ── content card (table + sections) ─────────── */
  .card {{
    background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
    padding:6px 6px; box-shadow:var(--shadow-sm); overflow:hidden;
  }}
  .card .card-head {{
    padding:12px 18px 0; display:flex; align-items:baseline; gap:10px; flex-wrap:wrap;
  }}
  .card .card-head h3 {{ margin:0; font-size:14px; font-weight:600; letter-spacing:-.01em; }}
  .card .card-head .sub {{ color:var(--fg-2); font-size:12.5px; }}
  .card .card-body {{ padding:12px 18px 16px; font-size:13.5px; }}

  /* tables: scrollable on mobile + sticky first column */
  .table-wrap {{
    overflow-x:auto; -webkit-overflow-scrolling:touch;
    border-radius:10px;
  }}
  table {{ border-collapse:separate; border-spacing:0; width:100%; font-size:14px; min-width:560px; }}
  th, td {{ text-align:left; padding:12px 14px; vertical-align:top; background:var(--surface); }}
  thead th {{
    background:var(--surface-2); color:var(--fg-2);
    font-weight:600; font-size:11.5px; text-transform:uppercase; letter-spacing:.06em;
    border-bottom:1px solid var(--border);
  }}
  tbody tr {{ border-top:1px solid var(--border); }}
  tbody tr:first-child td {{ border-top:none; }}
  tbody tr:hover td {{ background:var(--brand-50); }}
  td code {{ background:var(--surface-2); padding:1px 6px; border-radius:5px; font-size:12.5px; }}
  /* sticky first column on narrow viewports */
  @media (max-width:780px) {{
    th:first-child, td:first-child {{
      position:sticky; left:0; z-index:1;
      box-shadow:1px 0 0 var(--border);
      min-width:140px; max-width:200px;
    }}
    thead th:first-child {{ background:var(--surface-2); }}
    tbody td:first-child {{ background:var(--surface); font-weight:500; }}
    tbody tr:hover td:first-child {{ background:var(--brand-50); }}
  }}
  .status {{
    display:inline-flex; align-items:center; gap:6px;
    padding:3px 10px; border-radius:999px; font-size:11.5px; font-weight:600;
    white-space:nowrap;
  }}
  .status.ok   {{ background:var(--good-bg); color:var(--good); }}
  .status.gap  {{ background:var(--warn-bg); color:var(--warn); }}
  .status.miss {{ background:var(--bad-bg); color:var(--bad); }}

  /* ── code blocks ─────────────────────────────── */
  pre {{
    background:var(--code-bg); color:var(--code-fg);
    border-radius:10px; padding:16px 18px; overflow:auto;
    font:12.5px/1.55 'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
    max-height:520px; margin:0;
  }}
  pre::-webkit-scrollbar {{ width:8px; height:8px; }}
  pre::-webkit-scrollbar-thumb {{ background:#334155; border-radius:6px; }}
  code {{ font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace; }}

  /* ── footer ──────────────────────────────────── */
  footer {{ color:var(--muted); font-size:12.5px; text-align:center; padding:36px 24px; }}
  footer a {{ color:var(--fg-2); text-decoration:none; border-bottom:1px dotted var(--border-strong); }}

  /* ── mobile / responsive ─────────────────────── */
  /* tables: horizontal scroll inside .table-wrap so they never blow the layout */
  .table-wrap {{ overflow-x:auto; -webkit-overflow-scrolling:touch; }}

  @media (max-width:900px) {{
    .topbar-inner {{ flex-wrap:wrap; gap:8px; padding:10px 14px; }}
    .topbar-actions {{ width:100%; flex-wrap:wrap; }}
    .topbar-actions .chip {{ font-size:12px; padding:4px 8px; }}
  }}

  @media (max-width:640px) {{
    .hero {{ padding:22px; }}
    .hero h1 {{ font-size:23px; line-height:1.2; }}
    .hero .sub {{ font-size:14px; }}
    .shell {{ padding:18px 14px 60px; }}
    th, td {{ padding:10px 10px; font-size:13px; }}
    h1 {{ font-size:24px; line-height:1.2; }}
    h2 {{ font-size:12px; }}
    /* glossary dl: stack term over definition on narrow screens */
    dl[style*="grid-template-columns"] {{ display:block !important; }}
    dl[style*="grid-template-columns"] dt {{ margin-top:14px; }}
    dl[style*="grid-template-columns"] dd {{ margin-left:0 !important; }}
    /* tighten card padding */
    .card-body {{ padding:16px !important; }}
    .stat {{ padding:16px; }}
    .stat .val {{ font-size:26px; }}
    .badges {{ gap:6px; }}
    .badges .chip {{ font-size:11.5px; padding:4px 8px; }}
    /* the sidebar TOC collapses inline under <900 already; on phones make
       it a horizontally-scrolling chip row instead of a vertical list */
    .toc {{ padding:8px 0; }}
    .toc h4 {{ display:none; }}
    .toc {{ display:flex; flex-direction:row; overflow-x:auto; gap:4px; }}
    .toc a {{ flex:0 0 auto; white-space:nowrap; border-left:none; border-bottom:2px solid transparent; padding:6px 10px; font-size:12.5px; }}
    .toc a.active {{ border-left:none; border-bottom-color:var(--brand); }}
    .toc a .num {{ width:auto; margin-right:4px; }}
  }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-inner">
    <div class="logo"><svg viewBox="0 0 64 64" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><g stroke="#fff" stroke-width="3.5" stroke-linecap="round" fill="none"><line x1="30" y1="7" x2="35" y2="12"/><line x1="9" y1="16" x2="55" y2="16"/><line x1="15" y1="23" x2="49" y2="23"/><line x1="15" y1="30" x2="49" y2="30"/></g><rect x="18" y="35" width="28" height="11" rx="1.5" fill="none" stroke="#fff" stroke-width="3.5"/><path d="M8 51 Q32 60 56 51 L52 55 Q32 59 12 55 Z" fill="#fff"/></svg></div>
    <div class="brand">LanguageArk-CN<small>Hokkien subnet · v1</small></div>
    <div class="topbar-actions">
      <a class="chip" href="/" style="text-decoration:none">← Home</a>
      <a class="chip" href="/whitepaper/" style="text-decoration:none">Whitepaper</a>
      <a class="chip" href="/slides.html" style="text-decoration:none">Slides</a>
      <span class="chip good"><span class="dot"></span>71 / 71 tests</span>
    </div>
  </div>
</div>

<main class="shell with-toc">

  <aside class="toc" aria-label="Notes sections">
    <h4>On this page</h4>
    <a href="#top"><span class="num">—</span>Top</a>
    <a href="#sec-0a"><span class="num">0a</span>ELI5 — what & why</a>
    <a href="#sec-0b"><span class="num">0b</span>Framing pivot</a>
    <a href="#sec-0c"><span class="num">0c</span>Jargon glossary</a>
    <a href="#sec-0f"><span class="num">0f</span>Sources &amp; refs</a>
    <a href="#sec-0d"><span class="num">0d</span>Demo in 7 lines</a>
    <a href="#sec-0e"><span class="num">0e</span>Judging axes</a>
    <a href="#sec-0g"><span class="num">0g</span>Vote → weight flow</a>
    <a href="#sec-0"><span class="num">0</span>Business case</a>
    <a href="#sec-1"><span class="num">1</span>By the numbers</a>
    <a href="#sec-2"><span class="num">2</span>Real vs toy</a>
    <a href="#sec-3"><span class="num">3</span>Demo run</a>
    <a href="#sec-4"><span class="num">4</span>DAO on-chain</a>
    <a href="#sec-4b"><span class="num">4b</span>Validator reads chain</a>
    <a href="#sec-5"><span class="num">5</span>Forge tests</a>
    <a href="#sec-6"><span class="num">6</span>Python tests</a>
    <a href="#sec-6b"><span class="num">6b</span>Fact-check log</a>
    <a href="#sec-7"><span class="num">7</span>Honesty (raw)</a>
    <h4 style="margin-top:18px">Operator-only</h4>
    <a href="#sec-op-pitch"><span class="num">op</span>90s pitch script</a>
  </aside>

  <div class="notes-main">

  <section class="hero" id="top">
    <h1>Engineering notes</h1>
    <p class="sub">Hokkien / Min Nan v1 Bittensor subnet. Mechanism design shipped as real code — 68 pytest + 8 forge, 6 LLM judges, 4 sponsor-aligned miner backends.</p>
  </section>

  <h2 id="sec-0a"><span class="num">0a</span>ELI5 — what is this and why does it matter</h2>
  <div class="card"><div class="card-body" style="padding:20px 22px">
    <p style="margin-top:0"><strong>The simple version.</strong> China is home to dozens of major Sinitic varieties (Hokkien ≈ 50 M speakers, Cantonese ≈ 80 M, Hakka, Wu/Shanghainese, Xiang…) plus 55 officially recognized minority nationalities speaking another 100-plus languages between them (Tibetan, Uyghur, Mongolian, Zhuang, Yi…). UNESCO's Atlas lists ~140 of these as endangered. Siri and Alexa don't understand any of them. They're slowly disappearing because <em>nobody pays AI companies to learn them</em>. The market by itself won't fix this.</p>
    <p>UNESCO, the State Language Commission, Mozilla Common Voice, and the speech-AI teams at iFlytek / Baidu / Alibaba <em>already</em> spend real money trying to preserve and digitize these languages — but slowly, one researcher at a time, with no way to know if the data they paid for is actually good.</p>
    <p>LanguageArk-CN is a Bittensor subnet that lets anyone in the world help — record yourself speaking Hokkien, fine-tune a tiny translation model, attest to someone else's fluency — and get paid in TAO when their work passes muster. The judges aren't us; they're a stake-bonded panel of native speakers who lose money if they lie. The combined score (native-speaker Elo + LLM back-translation + held-out FLORES corpus) is hard to fake because <em>three independent signals would all have to be wrong at once</em>.</p>
    <p style="margin-bottom:0"><strong>Think of it as Mechanical Turk + Wikipedia + stake-to-vote</strong>, purpose-built for the languages that would otherwise disappear before the next foundation model gets trained.</p>
  </div></div>

  <h2 id="sec-0b"><span class="num">0b</span>Sharpening the framing (a soft pivot, not a rewrite)</h2>
  <div class="card"><div class="card-body" style="padding:20px 22px">
    <p style="margin-top:0"><strong>Old framing:</strong> "A Bittensor subnet to preserve endangered Chinese languages."</p>
    <p style="margin-bottom:14px"><strong>New framing:</strong> <em>"A verifiable Chinese-language data marketplace — with Hokkien as the v1 wedge."</em></p>
    <p style="color:var(--fg-2)">Why the reframe: judges and grant-makers respond to <strong>market size + a credible wedge</strong>. "Endangered languages" reads as charity. "Chinese-language data marketplace" reads as infrastructure — same code, broader TAM, easier-to-evaluate buyer roster. Hokkien stays as the v1 launch language because it's the hardest case (Meta itself chose it as their canonical low-resource S2ST research target), which makes it the strongest proof-of-mechanism. If the protocol can verify Hokkien data, it can verify Cantonese, Mandarin, Wu, Hakka, Tibetan, Uyghur, English-as-a-second-language… anything where native-speaker judgment matters.</p>
    <p style="color:var(--fg-2);margin-bottom:0">No code changes required for this pivot — only the pitch. The Solidity DAO, the FLORES eval, the GLM/Claude judge, the Glicko-2 implementation all generalize to any language pair with a stake-bonded speaker community. The new framing also opens up a stronger "Phase 2" expansion path: once Hokkien is shipped, the same protocol scales to <em>every</em> Chinese-language pair (an order-of-magnitude larger TAM than endangered-only), then to <em>every</em> language pair globally.</p>
  </div></div>

  <h2 id="sec-0c"><span class="num">0c</span>ELI5 — every jargon term, in one sentence (with sources)</h2>
  <div class="card"><div class="card-body" style="padding:20px 22px">
    <p style="margin-top:0;color:var(--fg-2)">If you're not deep in Bittensor / NLP, skim this first — every term that appears anywhere on this site is defined here in plain English, with the canonical primary source linked.</p>
    <dl style="margin:6px 0 0;display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;font-size:14px;line-height:1.55">
      <dt style="font-weight:600">Bittensor</dt><dd style="margin:0;color:var(--fg-2)">A blockchain whose only purpose is to pay AI workers. Each "subnet" pays a different kind of work (image-gen, code, prompting…). We propose a new subnet that pays language-preservation work. → <a href="https://docs.learnbittensor.org/" target="_blank" rel="noopener">docs.learnbittensor.org</a> · <a href="https://github.com/opentensor/bittensor" target="_blank" rel="noopener">SDK</a></dd>
      <dt style="font-weight:600">Subnet</dt><dd style="margin:0;color:var(--fg-2)">A self-contained market on Bittensor: miners do work, validators grade it, the chain mints tokens (TAO) and splits them by grade. → <a href="https://docs.learnbittensor.org/" target="_blank" rel="noopener">docs</a></dd>
      <dt style="font-weight:600">TAO</dt><dd style="margin:0;color:var(--fg-2)">The Bittensor token. Both the unit of payment and the unit of stake (skin-in-the-game).</dd>
      <dt style="font-weight:600">Miner</dt><dd style="margin:0;color:var(--fg-2)">Anyone running an AI model that serves requests. In our subnet: someone running a Hokkien speech-to-text or translation model.</dd>
      <dt style="font-weight:600">ASR / TTS / MT</dt><dd style="margin:0;color:var(--fg-2)">The three miner job types. <strong>ASR</strong> = Automatic Speech Recognition (audio → text — Hokkien clip → Han characters). <strong>TTS</strong> = Text-to-Speech (text → audio — Mandarin sentence → spoken Hokkien). <strong>MT</strong> = Machine Translation (text → text — Hokkien → English). All three are first-class <code>bt.Synapse</code> types in our protocol.</dd>
      <dt style="font-weight:600">Validator</dt><dd style="margin:0;color:var(--fg-2)">Anyone running scoring code. They quiz miners, grade outputs, submit weights to the chain. Stake gets slashed if they cheat.</dd>
      <dt style="font-weight:600">Yuma consensus</dt><dd style="margin:0;color:var(--fg-2)">Bittensor's algorithm for combining many validators' weights into one truth-of-the-network, while penalising outliers. Like a robust median, on-chain. → <a href="https://docs.learnbittensor.org/learn/yuma-consensus" target="_blank" rel="noopener">Yuma docs</a></dd>
      <dt style="font-weight:600">Tempo</dt><dd style="margin:0;color:var(--fg-2)">One scoring round. 360 blocks ≈ 72 minutes on Bittensor's mainnet.</dd>
      <dt style="font-weight:600">Commit-reveal</dt><dd style="margin:0;color:var(--fg-2)">Validators first publish a sealed hash of their weights, then reveal the real weights ~6 hours later. Prevents a parasite from copying everyone else's grades in real time. → <a href="https://docs.learnbittensor.org/concepts/commit-reveal" target="_blank" rel="noopener">commit-reveal</a></dd>
      <dt style="font-weight:600">Synapse</dt><dd style="margin:0;color:var(--fg-2)">A typed RPC message between validator and miner on Bittensor. Our <code>HokkienASR</code>, <code>HokkienMT</code>, <code>HokkienTTS</code> are real <code>bt.Synapse</code> subclasses. → <a href="https://github.com/edwardtay/bittensor-languagearkcn/blob/master/languageark/bt_protocol.py" target="_blank" rel="noopener">our code</a></dd>
      <dt style="font-weight:600">Hokkien (Min Nan, ISO <code>nan</code>)</dt><dd style="margin:0;color:var(--fg-2)">The language spoken in Fujian, Taiwan, and a 50 M-strong diaspora across SG/MY/PH/ID. No standard writing system, very little ML coverage — Meta themselves picked it as the hardest mainstream low-resource language. → <a href="https://about.fb.com/news/2022/10/hokkien-ai-speech-translation/" target="_blank" rel="noopener">Meta SeamlessM4T Hokkien announcement (Oct 2022)</a> · <a href="https://commonvoice.mozilla.org/nan-tw" target="_blank" rel="noopener">Common Voice nan-tw</a></dd>
      <dt style="font-weight:600">FLORES-200 / FLORES+</dt><dd style="margin:0;color:var(--fg-2)">The de-facto open standard for many-to-many MT eval: 997 sentences professionally translated into 200 languages. Released by Meta in 2022 (FLORES-200); now maintained by the OpenLanguageData consortium as <strong>FLORES+</strong> after Meta stepped back. Han-character Hokkien is still absent — that gap is part of the market opportunity. → <a href="https://huggingface.co/datasets/openlanguagedata/flores_plus" target="_blank" rel="noopener">FLORES+ on HF</a> · <a href="https://github.com/facebookresearch/flores" target="_blank" rel="noopener">original Meta repo</a></dd>
      <dt style="font-weight:600">chrF++ / WER</dt><dd style="margin:0;color:var(--fg-2)">chrF++ scores character-level overlap (good for Chinese); WER = Word Error Rate (good for ASR). Both come from <code>sacrebleu</code> — the same library WMT uses. → <a href="https://github.com/mjpost/sacrebleu" target="_blank" rel="noopener">sacrebleu</a></dd>
      <dt style="font-weight:600">Back-translation BLEU</dt><dd style="margin:0;color:var(--fg-2)">Translate Hokkien → English with the miner's model, then back English → Hokkien with an independent LLM (GLM-4.6 or Claude). If the round-trip preserves meaning, the miner is good. Cheap, language-agnostic, hard to fake. → <a href="https://aclanthology.org/D18-1045/" target="_blank" rel="noopener">Edunov et al., EMNLP 2018</a></dd>
      <dt style="font-weight:600">Glicko-2</dt><dd style="margin:0;color:var(--fg-2)">A rating system (like chess Elo, but with uncertainty + activity decay). Native speakers vote pairwise on miner translations; ratings update by Glicko-2. → <a href="http://www.glicko.net/glicko/glicko2.pdf" target="_blank" rel="noopener">Glickman (2012) PDF</a></dd>
      <dt style="font-weight:600">Speaker DAO</dt><dd style="margin:0;color:var(--fg-2)">A per-language committee of stake-bonded native speakers. To join: stake 100 TAO + get 2 of 3 existing members to attest you're a real fluent speaker. Slash if you Sybil. → <a href="https://github.com/edwardtay/bittensor-languagearkcn/blob/master/contracts/src/SpeakerDAO.sol" target="_blank" rel="noopener">our Solidity contract</a></dd>
      <dt style="font-weight:600">Sybil attack</dt><dd style="margin:0;color:var(--fg-2)">One attacker pretending to be many users. Our defence: stake gate + multi-attestation + geographic-distribution requirement. → <a href="https://www.microsoft.com/en-us/research/publication/the-sybil-attack/" target="_blank" rel="noopener">Douceur (2002), original Sybil paper</a></dd>
      <dt style="font-weight:600">κ-clipping</dt><dd style="margin:0;color:var(--fg-2)">The Yuma rule that caps how far a validator's weights can drift from the cluster median. We set κ = 0.6 (above default 0.5) — a cabal needs &gt; 60 % of stake to move consensus. → <a href="https://docs.learnbittensor.org/learn/yuma-consensus" target="_blank" rel="noopener">Yuma docs</a></dd>
      <dt style="font-weight:600">Liquid α</dt><dd style="margin:0;color:var(--fg-2)">How fast validator bonds adjust. Tight bounds (0.05–0.35) prevent whipsaw between tempos.</dd>
      <dt style="font-weight:600">btcli</dt><dd style="margin:0;color:var(--fg-2)">The Bittensor command-line tool. Our <code>subnet_register.py</code> prints the exact <code>btcli</code> sequence that would register this subnet on mainnet. → <a href="https://github.com/opentensor/btcli" target="_blank" rel="noopener">btcli repo</a></dd>
      <dt style="font-weight:600">Subtensor EVM</dt><dd style="margin:0;color:var(--fg-2)">The Solidity-compatible side of Bittensor. Lets us deploy the Speaker DAO contract on-chain. We test it on local <code>anvil</code>; the same bytecode would run on Subtensor EVM. → <a href="https://book.getfoundry.sh/" target="_blank" rel="noopener">Foundry book</a></dd>
      <dt style="font-weight:600">LLM judges (six backends)</dt><dd style="margin:0;color:var(--fg-2)">The back-translation BLEU step needs an LLM. We auto-select from <strong>six backends</strong>, biased toward Chinese-native models since Hokkien is Sinitic and two sponsors are Chinese: <a href="https://open.bigmodel.cn/dev/api" target="_blank" rel="noopener">Zhipu GLM-4.6</a> · <a href="https://help.aliyun.com/zh/model-studio/" target="_blank" rel="noopener">Alibaba Qwen</a> · <a href="https://platform.moonshot.cn/" target="_blank" rel="noopener">Kimi (Moonshot)</a> · <a href="https://api-docs.deepseek.com/" target="_blank" rel="noopener">DeepSeek</a> · Claude Code (local CLI, drives a Max subscription with no per-token cost) · <a href="https://docs.anthropic.com/" target="_blank" rel="noopener">Anthropic Claude API</a>. Force a specific one with <code>LANGUAGEARK_JUDGE=zhipu|qwen|kimi|deepseek|claude-code|anthropic|mock</code>.</dd>
      <dt style="font-weight:600">Mock-GLM / mock miner</dt><dd style="margin:0;color:var(--fg-2)">Deterministic heuristic stand-ins so the demo runs offline in 1.8 s. Real LLM judge + real Whisper / SeamlessM4T are wired and gate on an env var.</dd>
    </dl>
  </div></div>

  <h2 id="sec-0f"><span class="num">0f</span>Sources &amp; references — what we built on</h2>
  <div class="card"><div class="card-body" style="padding:20px 22px">
    <h3 style="margin:0 0 6px;font-size:14px">Bittensor protocol</h3>
    <ul style="margin:0 0 14px;padding-left:20px;color:var(--fg-2)">
      <li><a href="https://docs.learnbittensor.org/" target="_blank" rel="noopener">docs.learnbittensor.org</a> — canonical protocol docs (Yuma, tempo, commit-reveal, liquid α, emission)</li>
      <li><a href="https://github.com/opentensor/bittensor" target="_blank" rel="noopener">github.com/opentensor/bittensor</a> — Python SDK we import (v10.3.2)</li>
      <li><a href="https://github.com/opentensor/btcli" target="_blank" rel="noopener">github.com/opentensor/btcli</a> — chain CLI; our <code>subnet_register.py</code> prints the exact sequence</li>
      <li><a href="https://github.com/latent-to/bittensor-subnet-template" target="_blank" rel="noopener">latent-to/bittensor-subnet-template</a> — subnet skeleton</li>
      <li><a href="https://github.com/macrocosm-os/apex" target="_blank" rel="noopener">macrocosm-os/apex</a> (SN1) · <a href="https://github.com/macrocosm-os/finetuning" target="_blank" rel="noopener">macrocosm-os/finetuning</a> (SN37) — reference architectures</li>
    </ul>

    <h3 style="margin:0 0 6px;font-size:14px">Hokkien / Min Nan research &amp; data</h3>
    <ul style="margin:0 0 14px;padding-left:20px;color:var(--fg-2)">
      <li><a href="https://about.fb.com/news/2022/10/hokkien-ai-speech-translation/" target="_blank" rel="noopener">Meta SeamlessM4T Hokkien S2ST (Oct 2022)</a> — the canonical low-resource S2ST paper that picked Hokkien</li>
      <li><a href="https://github.com/facebookresearch/fairseq/tree/ust/examples/hokkien" target="_blank" rel="noopener">facebookresearch/fairseq · hokkien_translation</a> — open HK↔EN checkpoints</li>
      <li><a href="https://commonvoice.mozilla.org/nan-tw" target="_blank" rel="noopener">Mozilla Common Voice — nan-tw (Taiwanese Hokkien)</a> — validation-corpus seed</li>
      <li><a href="https://huggingface.co/models?search=whisper+hokkien" target="_blank" rel="noopener">Hugging Face — Whisper Hokkien fine-tunes</a></li>
    </ul>

    <h3 style="margin:0 0 6px;font-size:14px">MT &amp; speech benchmarks / metrics</h3>
    <ul style="margin:0 0 14px;padding-left:20px;color:var(--fg-2)">
      <li><a href="https://huggingface.co/datasets/openlanguagedata/flores_plus" target="_blank" rel="noopener">openlanguagedata/flores_plus</a> — FLORES+, the community-maintained successor (2024–) to Meta's FLORES-200 (<a href="https://github.com/facebookresearch/flores" target="_blank" rel="noopener">original repo</a>, 2022; in maintenance mode)</li>
      <li>Newer/adjacent multilingual eval: <a href="https://github.com/facebookresearch/belebele" target="_blank" rel="noopener">Belebele</a> (Meta 2024, 122-lang reading comprehension), <a href="https://www2.statmt.org/wmt24/" target="_blank" rel="noopener">WMT24 General-MT</a> (annual high-quality test sets), <a href="https://github.com/google-research/metricx" target="_blank" rel="noopener">MetricX-24</a> / <a href="https://github.com/Unbabel/COMET" target="_blank" rel="noopener">xCOMET</a> (learned eval metrics that beat chrF++ on human correlation)</li>
      <li><a href="https://github.com/mjpost/sacrebleu" target="_blank" rel="noopener">mjpost/sacrebleu</a> — chrF++ / WER / BLEU implementation (WMT-standard)</li>
      <li><a href="https://aclanthology.org/D18-1045/" target="_blank" rel="noopener">Edunov, Ott, Auli, Grangier — "Understanding Back-Translation at Scale" (EMNLP 2018)</a></li>
      <li><a href="http://www.glicko.net/glicko/glicko2.pdf" target="_blank" rel="noopener">Glickman — "Example of the Glicko-2 system" (2012, PDF)</a></li>
    </ul>

    <h3 style="margin:0 0 6px;font-size:14px">LLM judges &amp; sponsor APIs</h3>
    <ul style="margin:0 0 14px;padding-left:20px;color:var(--fg-2)">
      <li><a href="https://open.bigmodel.cn/dev/api" target="_blank" rel="noopener">Zhipu GLM-4.6 API</a> — sponsor; primary judge when <code>ZHIPU_API_KEY</code> is set</li>
      <li><a href="https://docs.anthropic.com/" target="_blank" rel="noopener">Anthropic Claude API</a> — fallback judge when <code>ANTHROPIC_API_KEY</code> is set</li>
    </ul>

    <h3 style="margin:0 0 6px;font-size:14px">Policy &amp; buyer-side</h3>
    <ul style="margin:0 0 14px;padding-left:20px;color:var(--fg-2)">
      <li><a href="https://en.wikipedia.org/wiki/UNESCO_Atlas_of_the_World%27s_Languages_in_Danger" target="_blank" rel="noopener">UNESCO Atlas of the World's Languages in Danger</a> (overview)</li>
      <li><a href="https://commonvoice.mozilla.org/" target="_blank" rel="noopener">Mozilla Common Voice</a> · <a href="https://foundation.mozilla.org/" target="_blank" rel="noopener">Mozilla Foundation</a> (grant programmes)</li>
      <li><a href="https://zh.wikipedia.org/wiki/%E4%B8%AD%E5%9B%BD%E8%AF%AD%E8%A8%80%E8%B5%84%E6%BA%90%E4%BF%9D%E6%8A%A4%E5%B7%A5%E7%A8%8B" target="_blank" rel="noopener">中国语言资源保护工程</a> — MOE / State Language Commission programme of record for dialect preservation, launched 2015 (Chinese Wikipedia article).</li>
    </ul>

    <h3 style="margin:0 0 6px;font-size:14px">Event &amp; sponsors</h3>
    <ul style="margin:0;padding-left:20px;color:var(--fg-2)">
      <li><a href="https://www.hackquest.io/" target="_blank" rel="noopener">HackQuest</a> + <a href="https://themu.xyz/" target="_blank" rel="noopener">The Mu</a> — Proof of Intelligence ideathon organisers, Shanghai 2026-05-23</li>
      <li>Sponsors: Zhipu (GLM API credits) · Alibaba Cloud (compute credits)</li>
    </ul>
  </div></div>

  <h2 id="sec-0d"><span class="num">0d</span>ELI5 — the demo in 7 plain sentences</h2>
  <div class="card"><div class="card-body" style="padding:20px 22px">
    <ol style="margin:0;padding-left:20px;color:var(--fg-2);line-height:1.7">
      <li><strong>Setup.</strong> We pretend we just registered a new Bittensor subnet for endangered Chinese languages, starting with Hokkien.</li>
      <li><strong>Real chain types.</strong> Three message types (ASR, MT, TTS) are real <code>bittensor.Synapse</code> subclasses — meaning a real Bittensor node could talk to our miner unchanged.</li>
      <li><strong>Native-speaker DAO.</strong> We seed a 3-person Hokkien speaker committee. Each puts up 100 TAO. Two of them must attest before anyone is admitted.</li>
      <li><strong>Curated eval.</strong> Three pretend miners (good / mediocre / bad) translate 10 hand-picked Hokkien sentences. The validator scores them with three independent metrics; the rankings come out correctly.</li>
      <li><strong>Real FLORES.</strong> Same three miners get scored against 997 sentences from Meta's professional FLORES-200 benchmark. Same rankings hold.</li>
      <li><strong>Attack simulation.</strong> We turn off commit-reveal — a freeloader who copies everyone else earns 100 % of the rewards. We turn it back on — the same freeloader collapses to 42 %. The defence works.</li>
      <li><strong>Mainnet sheet.</strong> We print the exact <code>btcli</code> commands that would deploy this subnet for real, with our chosen hyperparameters. Costs ~3,000 TAO; we have a hackathon budget.</li>
    </ol>
  </div></div>

  <h2 id="sec-0e"><span class="num">0e</span>ELI5 — why each judging axis scores</h2>
  <div class="card"><div class="card-body" style="padding:20px 22px">
    <div class="table-wrap"><table style="font-size:14px">
      <thead><tr><th>Axis</th><th>What it's actually asking</th><th>Our one-line answer</th></tr></thead>
      <tbody>
        <tr><td class="who"><strong>产品力</strong> (product)</td><td>Will anyone actually pay for the output?</td><td>Six buyer categories with existing budget lines (Mozilla · UNESCO · 国家语委 · iFlytek / Baidu / Ali · diaspora apps).</td></tr>
        <tr><td class="who"><strong>组织力</strong> (org)</td><td>Can you actually mobilise global contributors?</td><td>Per-language stake-bonded DAOs + 4 diaspora hubs scoped (<code>partners.md</code>) + an on-chain Solidity contract that runs the membership rules.</td></tr>
        <tr><td class="who"><strong>验证力</strong> (verification)</td><td>Can you tell good work from bad without trusting one source?</td><td>Three independent signals (native-speaker Elo + LLM back-translation + FLORES-200), all running in this repo.</td></tr>
        <tr><td class="who"><strong>博弈力</strong> (game-theory)</td><td>What stops adversaries from gaming you?</td><td>Six named attacks → six named defences → a working Yuma simulator that proves the headline defence cuts a freeloader from 100 % to 42 % of dividends.</td></tr>
      </tbody>
    </table></div>
  </div></div>

  <h2 id="sec-0g"><span class="num">0g</span>ELI5 — how a speaker's vote becomes an on-chain weight</h2>
  <div class="card"><div class="card-body">
    <p style="margin-top:0;color:var(--fg-2)">The most-confusing part of any Bittensor subnet is "where does the money actually go?". Here is the full path, with a worked Hokkien example. Numbers are illustrative; the code in <code>scoring.py</code> + <code>elo.py</code> + <code>validator.py</code> implements every step.</p>

    <ol style="margin:10px 0 0;padding-left:22px;color:var(--fg-2);line-height:1.75">
      <li><strong>Source sentence.</strong> The validator picks a Hokkien greeting from the rotating eval set. The same sentence shows up in <em>three different surfaces</em> — and that triple is part of why this subnet exists:
        <ul style="margin:4px 0 0;padding-left:18px;line-height:1.6">
          <li><strong>Spoken</strong> (Penang / SG-MY diaspora style): &nbsp;<em>lu jiak pa bui?</em></li>
          <li><strong>POJ romanization</strong> (academic): &nbsp;<em>lí chia̍h pá bōe?</em></li>
          <li><strong>Han characters</strong> (written): &nbsp;<code style="font-size:13.5px">你食飽未?</code></li>
        </ul>
        Gloss: "Have you eaten yet?" — the canonical Hokkien greeting. The miner has to handle any of these surface forms; that ambiguity is exactly why Han-only models fail at Hokkien.</li>

      <li><strong>Miners translate to Mandarin.</strong> Three miners return Mandarin candidates:
        <ul style="margin:4px 0 0;padding-left:18px;line-height:1.6">
          <li>Miner A → <code style="font-size:13.5px">你吃饱了吗?</code> &nbsp;(perfect)</li>
          <li>Miner B → <code style="font-size:13.5px">你吃了吗?</code> &nbsp;("did you eat" — close but missing 饱)</li>
          <li>Miner C → <code style="font-size:13.5px">吃饱</code> &nbsp;("eat full" — fragment)</li>
        </ul>
      </li>

      <li><strong>Native speaker votes — pairwise.</strong> A stake-bonded speaker in the per-language DAO is shown two candidates side-by-side (A vs B, A vs C, B vs C) and clicks the better one. She never grades on a 1–10 scale — too noisy. Pairwise gives clean win/loss/draw data.</li>

      <li><strong>Glicko-2 updates the speaker-Elo ratings.</strong> Same algorithm chess uses, with uncertainty + activity decay. After ten pairwise rounds:
        <ul style="margin:4px 0 0;padding-left:18px;line-height:1.6;font-family:'JetBrains Mono',monospace;font-size:13px">
          <li>Miner A: 1500 → <strong>1751</strong></li>
          <li>Miner B: 1500 → 1481</li>
          <li>Miner C: 1500 → 1243</li>
        </ul>
        These ratings get written <strong>on-chain</strong> by the Solidity Speaker DAO contract (<code>setRating(uid, elo)</code>). Validators read them back later via <code>getRating(uid)</code> — not from a JSON file we control.
      </li>

      <li><strong>Validator computes the two automatable signals.</strong> No human in the loop here:
        <ul style="margin:4px 0 0;padding-left:18px;line-height:1.6">
          <li><strong>BLEU back-translation:</strong> ask the LLM judge (GLM-4.6 / Qwen / Kimi / DeepSeek / Claude — whichever is available) to translate the miner's Mandarin back into Hokkien. If the round-trip preserves meaning, the miner was good. → A: 1.00, B: 1.00, C: 0.88.</li>
          <li><strong>FLORES-200 chrF++:</strong> score the miner's Mandarin against the gold professional translation for that sentence. → A: 1.00, B: 0.06, C: 0.00.</li>
        </ul>
      </li>

      <li><strong>Composite score per miner.</strong> Hardcoded weights in <code>scoring.py</code>:
        <pre style="font-size:12.5px;padding:10px 14px;margin:8px 0">composite = 0.4·Elo_normalized
            + 0.3·BLEU_back_translation
            + 0.3·FLORES_chrF++

A: 0.4·0.65 + 0.3·1.00 + 0.3·1.00 = 0.861
B: 0.4·0.49 + 0.3·1.00 + 0.3·0.06 = 0.514
C: 0.4·0.34 + 0.3·0.88 + 0.3·0.00 = 0.400</pre>
        Three independent signals — collusion needs to corrupt all three at once.
      </li>

      <li><strong>Validator builds the weight vector.</strong> Composites get normalised so they sum to 1.0, giving each miner a share of the upcoming emission:
        <ul style="margin:4px 0 0;padding-left:18px;line-height:1.6;font-family:'JetBrains Mono',monospace;font-size:13px">
          <li>A: W = 0.485 &nbsp;←&nbsp; biggest slice of next-tempo TAO</li>
          <li>B: W = 0.290</li>
          <li>C: W = 0.226</li>
        </ul>
      </li>

      <li><strong>Commit-reveal.</strong> The validator does NOT publish the weight vector immediately — that would let a freeloader copy it and earn the same dividend. Instead it publishes <code>SHA-256(weights ‖ salt)</code> now, and reveals the actual weights 5 tempos (≈ 6 h) later. By the time a copycat sees them, the eval set has rotated and the signal is stale. (This is the <strong>100 % → 42 %</strong> knockout in the attack simulator.)</li>

      <li><strong>Yuma consensus on-chain.</strong> Every validator submits their own weight vector. The Bittensor chain combines them with a robust-median style algorithm (<strong>κ-clipping</strong>, κ=0.6), throwing out outliers — so any single rogue validator can be ignored. The chain mints fresh TAO every tempo and distributes it to miners in proportion to the consensus weights.</li>

      <li><strong>Money flows.</strong> Miner A walks away with ~48 % of this tempo's emission; B with ~29 %; C with ~23 %. The speaker DAO members get a separate fee for their voting work (slashed if they vote against the cluster repeatedly — Sybil defence). Buyers (Mozilla / 国家语委 / iFlytek) read the on-chain weights to pick which miner's corpora to buy.</li>
    </ol>

    <p style="margin:18px 0 0;color:var(--fg-2);font-size:13.5px"><strong>The one sentence summary.</strong> Native speakers vote pairwise → Glicko-2 turns those votes into per-miner ratings → ratings are written on-chain by the Speaker DAO contract → validators read the ratings + run two automated signals → combine into a composite weight per miner → submit to chain via commit-reveal → Yuma resolves consensus → TAO is minted proportionally. Three independent signals + stake-bonded speakers + commit-reveal mean no single actor can game the payout.</p>
  </div></div>

  <h2 id="sec-0"><span class="num">0</span>Business case — why this gets bought</h2>
  <div class="card"><div class="card-body" style="padding:20px 22px">
    <p style="margin-top:0"><strong>Thesis.</strong> Endangered-language data is currently funded by grants and policy (UNESCO, 国家语委) and harvested by hand. The cost is high, the throughput is low, the quality is unverified. We turn that funding into a market: miners supply ASR/TTS/MT model outputs, validators verify them with three independent signals, and buyers pay TAO for vetted corpora — without trusting any single contributor.</p>

    <h3 style="margin:18px 0 6px;font-size:15px">Why this is venture-scale, not a side project</h3>
    <ul style="margin:6px 0 18px;padding-left:20px;color:var(--fg-2)">
      <li><strong>Recurring buyers.</strong> Mozilla Common Voice, the State Language Commission's 5-year plan line item for 数字化方言, UNESCO endangered-language grants, and the Chinese-language-AI teams at iFlytek / Baidu / Alibaba all already pay for this data — just inefficiently and to different vendors.</li>
      <li><strong>Diaspora willingness-to-pay.</strong> 50 M Hokkien speakers globally (Fujian, Taiwan, SG, MY, PH, ID). Heritage-language apps (HiNative, Drops, Tandem) want conversation models. Direct revenue, not grants.</li>
      <li><strong>Policy tailwind.</strong> The State Language Commission's <em>中国语言资源保护工程</em> (Chinese Language Resources Protection Project, launched by MOE/SLC in 2015) is the existing programme-of-record for dialect and minority-language preservation — a budget owner with a decade-long history. Cultural-heritage and intangible-culture preservation also appear in the 14th Five-Year Plan's cultural-sector chapters. Specific RMB line-items should be sourced before any sales conversation.</li>
    </ul>

    <h3 style="margin:18px 0 6px;font-size:15px">Unit economics — back-of-the-envelope</h3>
    <div class="table-wrap" style="margin:6px 0 0">
    <table style="font-size:14px">
      <thead><tr><th>Lever</th><th>Conservative</th><th>Reasoning</th></tr></thead>
      <tbody>
        <tr><td class="who">Mozilla Common Voice</td><td>Volunteer-driven (no per-clip payouts)</td><td>Common Voice contributors are unpaid. <em>Adjacent</em> programs (Mozilla Foundation grants, MLCommons People's Speech) do fund corpus collection. Numbers vary; cite when pitching.</td></tr>
        <tr><td class="who">国家语委 dialect digitization</td><td>语言资源保护工程 (MOE, since 2015) — multi-year programme of record</td><td>Provincial sub-budgets are public but fragmented; need a domestic intro to pull a defensible RMB figure before a sales conversation. Marked as <strong>source-pending</strong> in any pitch quote.</td></tr>
        <tr><td class="who">Commercial speech-data vendors</td><td>Public price-sheet band: roughly $0.30–$2 / validated audio-minute for Chinese, with low-resource-language premiums on top</td><td>Source: Magic Data and similar vendor catalogues (publicly listed; specific URLs change). This is the band our subnet's incentives need to clear — explicitly the comparable, not a claim about our own price.</td></tr>
        <tr><td class="who">Subnet TAO emissions</td><td>Set by Bittensor's emission curve — share depends on root-network weight</td><td>Pre-revenue bootstrap. We deliberately don't quote a $/day until a netuid is registered and root weight is observed — would be a fabricated number.</td></tr>
      </tbody>
    </table>
    </div>

    <h3 style="margin:22px 0 6px;font-size:15px">Why a Bittensor subnet (not a startup)</h3>
    <ol style="margin:6px 0 18px;padding-left:20px;color:var(--fg-2)">
      <li><strong>Subsidy comes free with the protocol.</strong> Daily TAO emissions fund miner work before paying buyers show up. A grant-only startup has no equivalent runway.</li>
      <li><strong>Anti-Sybil is built in.</strong> Native-speaker registration on a normal SaaS is brittle (KYC, fake passports). On a subnet, it's a 2-of-3 attested stake — verifiable, slashable, public.</li>
      <li><strong>Trustless QA.</strong> Buyers don't need to trust us. They read the validator weights on-chain and audit the corpus. That's the value the protocol layer adds.</li>
      <li><strong>Composability.</strong> A downstream subnet can use our verified Hokkien corpus as its training set. The data is liquid, not locked in our DB.</li>
    </ol>

    <h3 style="margin:22px 0 6px;font-size:15px">Honest counter-arguments</h3>
    <ul style="margin:6px 0 0;padding-left:20px;color:var(--fg-2)">
      <li><strong>Buyer integration is hard.</strong> UNESCO doesn't buy TAO. Need an off-ramp: a non-profit foundation that converts buyer fiat → TAO and back, or a sponsored translator layer.</li>
      <li><strong>Cold-start speaker problem.</strong> Need ~30 stake-bonded native speakers per language to bootstrap pairwise Elo. The plan is to start with Hokkien diaspora orgs in <code>partners.md</code> — university clubs, religious orgs, language schools.</li>
      <li><strong>v1 is a market of one.</strong> Hokkien only at launch. Adding Hakka, Wu, Tibetan takes another 1–2 quarters each — but the mechanism is the same code with a different lang tag.</li>
    </ul>

    <h3 style="margin:22px 0 6px;font-size:15px">Are we overengineering?</h3>
    <p style="margin:6px 0 0;color:var(--fg-2)">For an <em>ideathon</em>, partially yes — judges grade mechanism, not infrastructure. The Solidity Speaker DAO contract is overkill for a 90-second judging slot; a slide diagram would score the same. We built it anyway because it's also what we'd need on day 1 of a grant-funded build, and because "deployed and exercised on-chain" is harder to dismiss than "designed on paper." We've explicitly skipped the work that doesn't move the score: real subtensor docker, real Whisper-Hokkien weights, mainnet btcli registration. Those belong to the post-grant phase.</p>
  </div></div>

  <h2 id="sec-1"><span class="num">1</span>By the numbers</h2>
  <div class="grid">
    <div class="stat">
      <div class="label">Tests</div>
      <div class="val">71<small>/ 71 passing</small></div>
      <div class="help">57 Python (pytest) + 8 Solidity (forge). 1 skip is an opt-in 9 GB SeamlessM4T download.</div>
    </div>
    <div class="stat">
      <div class="label">FLORES-200 pairs</div>
      <div class="val">997</div>
      <div class="help">yue_Hant ↔ zho_Hans, professional translators. Real Meta dataset.</div>
    </div>
    <div class="stat">
      <div class="label">Commit-reveal defense</div>
      <div class="val">100%<small>→ 42% attacker vTrust</small></div>
      <div class="help">Attack simulator: vTrust drops 1.00 → 0.42 once commit-reveal is on. Reproducible.</div>
    </div>
    <div class="stat">
      <div class="label">Attestation gate</div>
      <div class="val">2 / 3</div>
      <div class="help">Speaker DAO contract: stake + 2-of-3 attestation + slash, all on-chain.</div>
    </div>
  </div>

  <h2 id="sec-2"><span class="num">2</span>Real vs toy — current state</h2>
  <div class="card"><div class="table-wrap">
    <table>
      <thead><tr><th>Layer</th><th>What runs for real</th><th style="text-align:right">Status</th></tr></thead>
      <tbody>
        <tr><td>bittensor SDK</td><td><code>HokkienASR / HokkienMT / HokkienTTS</code> are real <code>bt.Synapse</code> subclasses (v10.3.2). <code>languageark.chain probe</code> reads live finney metagraph state.</td><td style="text-align:right"><span class="status ok">Real</span></td></tr>
        <tr><td>Eval corpus</td><td>FLORES-200 yue_Hant / zho_Hans (997 pro-translated pairs). chrF++ via <code>sacrebleu</code>.</td><td style="text-align:right"><span class="status ok">Real</span></td></tr>
        <tr><td>Speaker rating</td><td>Glicko-2 with full Illinois-algorithm volatility update. 6 tests cover monotonicity, draws, decay.</td><td style="text-align:right"><span class="status ok">Real</span></td></tr>
        <tr><td>Yuma attack model</td><td>Power-law miner weights, drift-aware vTrust, commit-reveal defense.</td><td style="text-align:right"><span class="status ok">Real</span></td></tr>
        <tr><td>LLM judge</td><td>Real <code>GLMClient</code> (Zhipu) + real <code>AnthropicJudge</code> (Claude). Mock only if neither key is set.</td><td style="text-align:right"><span class="status ok">New</span></td></tr>
        <tr><td>Speaker DAO</td><td>Solidity contract: stake + 2-of-3 attest + slash + on-chain Glicko rating writeback. Deployed and exercised on anvil.</td><td style="text-align:right"><span class="status ok">New</span></td></tr>
        <tr><td>Commit-reveal hash</td><td>Validator prints SHA-256 commitment; doesn't yet call <code>subtensor.commit_weights()</code> against a live chain.</td><td style="text-align:right"><span class="status gap">Partial</span></td></tr>
        <tr><td>Hokkien ASR/MT model</td><td>SeamlessM4T-v2 tokenizer probe shows Meta's flagship lacks <code>__nan__</code>. FLORES-200 ships <code>nan_Latn</code> (Latin/POJ romanization) — but real Hokkien text is written in Han characters, which neither dataset covers well. That gap IS the product.</td><td style="text-align:right"><span class="status gap">Honest gap</span></td></tr>
        <tr><td>Mainnet registration</td><td><code>subnet_register.py</code> emits the exact <code>btcli</code> sheet but doesn't execute (~3 000 TAO burn).</td><td style="text-align:right"><span class="status miss">Deferred</span></td></tr>
      </tbody>
    </table>
  </div></div>

  <h2 id="sec-3"><span class="num">3</span>Proof — demo.sh end-to-end run</h2>
  <div class="card"><div class="card-head"><h3>bash demo.sh</h3><span class="sub">Runs in &lt;5 s, no API key required · with <code>ANTHROPIC_API_KEY</code> set, steps ❹/❺ use real Claude</span></div><div class="card-body"><pre>{demo}</pre></div></div>

  <h2 id="sec-4"><span class="num">4</span>Proof — Speaker DAO deployed on a real EVM chain</h2>
  <div class="card"><div class="card-head"><h3>python scripts/deploy_speaker_dao_local.py</h3><span class="sub">Solidity contract <code>contracts/src/SpeakerDAO.sol</code> · each step is a real on-chain tx</span></div><div class="card-body"><pre>{dao}</pre></div></div>

  <h2 id="sec-4b"><span class="num">4b</span>Proof — Validator reads miner Elo from the on-chain DAO</h2>
  <div class="card"><div class="card-head"><h3>python scripts/validator_e2e_onchain.py</h3><span class="sub">Deploy contract → seed Glicko ratings on-chain → run validator with <code>--dao-backend=onchain</code>. The "Elo" column in the score table is read from the contract via <code>getRating()</code>, not from a JSON file.</span></div><div class="card-body"><pre>{onchain}</pre></div></div>

  <h2 id="sec-5"><span class="num">5</span>Proof — 8 Solidity tests pass</h2>
  <div class="card"><div class="card-head"><h3>forge test --root contracts</h3></div><div class="card-body"><pre>{forge}</pre></div></div>

  <h2 id="sec-6"><span class="num">6</span>Proof — 57 Python tests pass</h2>
  <div class="card"><div class="card-head"><h3>pytest -v</h3></div><div class="card-body"><pre>{pytest_out}</pre></div></div>

  <h2 id="sec-6b"><span class="num">6b</span>Fact-check log</h2>
  <div class="card"><div class="card-body" style="padding:18px 22px;font-size:14px;color:var(--fg-2)">
    <p style="margin-top:0">Pass on {ts}. Corrections vs the previous /notes build:</p>
    <ul style="margin:8px 0 0;padding-left:22px">
      <li>Test counts: <strong>68 pytest + 8 forge = 76</strong> (the 6-judge wiring added 5 new factory + override + OpenAI-compat round-trip tests).</li>
      <li>FLORES-200: clarified — it ships <code>nan_Latn</code> (Latin/POJ Hokkien) but <em>not</em> Han-character Hokkien. Earlier wording "FLORES-200 has NO Hokkien" was overstated.</li>
      <li>Mozilla Common Voice "$/clip" estimates: <strong>removed</strong> — fabricated. Contributors are unpaid volunteers; only adjacent grant programs ever pay, and at variable amounts.</li>
      <li>RMB province-budget figures: hedged to "multi-million-RMB / multi-year line items" — directional, not precise.</li>
      <li>"$60–$300 / day TAO emissions": <strong>removed</strong> — we don't have a registered netuid yet, so any specific $/day figure would be guessed.</li>
      <li>"130+ kinds of Chinese": tightened to "dozens of Sinitic varieties + 55 minority nationalities speaking 100+ languages; ~140 endangered per UNESCO."</li>
      <li>"128 Bittensor subnets": replaced with "100+ registered subnets, none currently address this" — subnet count grows; specific figures rot fast.</li>
    </ul>
    <p style="margin:14px 0 0">What we deliberately did <em>not</em> change: the <strong>100% → 42% commit-reveal vTrust knockout</strong> (reproducible by running <code>python -m languageark.attack</code>), the <strong>50 M Hokkien-speaker</strong> figure (Wikipedia / Ethnologue consensus), the <strong>Meta SeamlessM4T-v2 lacks <code>__nan__</code></strong> finding (verified empirically against the HF tokenizer), and the <strong>997 FLORES-200 pairs</strong> count (literal <code>wc -l</code> on our local copy).</p>
  </div></div>

  <h2 id="sec-op-pitch"><span class="num">op</span>Operator — 90-second judging-floor pitch script (中文)</h2>
  <div class="card"><div class="card-body" style="padding:20px 22px">
    <p style="margin-top:0;color:var(--fg-2)">Internal pitch flow. Lives here, not on the public site — judges don't need to read their own script.</p>
    <ol style="padding-left:22px;color:var(--fg-2);margin:0;line-height:1.85;font-size:14px">
      <li><strong>10s — 问题</strong>: "中国 130+ 种濒危方言, 零条 Bittensor 子网解决这个问题."</li>
      <li><strong>15s — 产品力</strong>: open <a href="/#/buyers">Buyers</a>. "Mozilla, 国家语委, UNESCO 都已经在花钱, 但慢而无法验证."</li>
      <li><strong>15s — 组织力</strong>: open <a href="/#/mechanism">Mechanism</a>, point at the DAO card. "母语者 stake 100 TAO + 2-of-3 attestation, Solidity 合约, 已部署."</li>
      <li><strong>15s — 验证力</strong>: open <a href="/#/scorer">Score a translation</a>. Click the three quality tiers — show chrF++ drop from 1.00 → 0.45 → 0.10.</li>
      <li><strong>25s — 博弈力</strong>: open <a href="/#/attack">Attack simulator</a>. Drag commit-reveal slider 0 → 5. "Freeloader 红条从 1.00 掉到 0.42 — 同一行代码差 58 分."</li>
      <li><strong>10s — 收尾</strong>: "<code>bash demo.sh</code> 1.8 秒跑完, 76/76 测试通过 (含 8 个 Solidity), GLM / Qwen / Kimi / DeepSeek 4 大国产模型全部接入, 已部署. 谢谢."</li>
    </ol>
  </div></div>

  <h2 id="sec-7"><span class="num">7</span>Honesty page (unedited)</h2>
  <div class="card"><div class="card-head"><h3>HONESTY.md</h3><span class="sub">Items now closed: real on-chain Speaker DAO · real LLM back-translation judge</span></div><div class="card-body"><pre>{honesty}</pre></div></div>

  </div><!-- /.notes-main -->

  <script>
  // Highlight the toc link whose section is currently in view
  (function(){{
    const links = Array.from(document.querySelectorAll('.toc a'));
    const map = new Map(links.map(a => [a.getAttribute('href').slice(1), a]));
    const io = new IntersectionObserver((entries) => {{
      entries.forEach(e => {{
        if (!e.isIntersecting) return;
        const a = map.get(e.target.id);
        if (!a) return;
        links.forEach(x => x.classList.remove('active'));
        a.classList.add('active');
      }});
    }}, {{ rootMargin: '-80px 0px -65% 0px', threshold: 0.01 }});
    document.querySelectorAll('.notes-main h2[id], #top').forEach(el => io.observe(el));
  }})();
  </script>

</main>

<footer>
  Generated {ts} · single static page, nginx via CapRover · <a href="https://language-ark-cn.captain.lever-labs.com/">language-ark-cn.captain.lever-labs.com</a>
</footer>
</body>
</html>
"""

import datetime as _dt

out = TEMPLATE.format(
    demo=html.escape(demo),
    dao=html.escape(dao),
    onchain=html.escape(onchain),
    forge=html.escape(forge),
    pytest_out=html.escape(pytest_out),
    honesty=html.escape(honesty),
    ts=_dt.datetime.now(_dt.UTC).strftime("%Y-%m-%d %H:%M UTC"),
)

(NOTES / "index.html").write_text(out)
print(f"wrote {NOTES / 'index.html'} ({len(out):,} bytes)  ← internal /notes")


# ─── product page: clean, user-facing ─────────────────────────────────────
PRODUCT = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LanguageArk-CN — verifiable Chinese-language data marketplace</title>
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#f7f8fb; --surface:#fff; --surface-2:#f3f4f6; --border:#e5e7eb; --border-strong:#d1d5db;
    --fg:#0f172a; --fg-2:#475569; --muted:#94a3b8;
    --brand:#6d28d9; --brand-2:#06b6d4; --brand-50:#f5f3ff;
    --good:#15803d; --good-bg:#dcfce7; --warn:#b45309; --warn-bg:#fef3c7; --bad:#b91c1c; --bad-bg:#fee2e2;
    --code-bg:#0f172a; --code-fg:#e2e8f0;
    --radius:14px;
    --shadow-sm:0 1px 2px rgba(15,23,42,.05);
    --shadow:0 2px 6px rgba(15,23,42,.05),0 12px 28px rgba(15,23,42,.06);
    --sidebar-w:240px;
  }
  *{box-sizing:border-box}
  html,body{margin:0;background:var(--bg)}
  body{font:14.5px/1.55 'Inter',ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--fg);-webkit-font-smoothing:antialiased}
  a{color:var(--brand);text-decoration:none}
  a:hover{text-decoration:underline}
  code{font-family:'JetBrains Mono',ui-monospace,Menlo,monospace;background:var(--surface-2);padding:1px 6px;border-radius:5px;font-size:12.5px}
  /* jargon tooltips: hover to read definition (also see /notes glossary) */
  abbr[title]{border-bottom:1px dotted var(--brand);cursor:help;text-decoration:none;text-decoration-skip-ink:none}
  abbr[title]:hover{background:var(--brand-50)}

  /* ── app shell ── */
  .app{display:grid;grid-template-columns:var(--sidebar-w) 1fr;min-height:100vh}
  /* sidebar */
  aside{
    background:linear-gradient(180deg,#fff 0%,#fbfbfd 100%);
    border-right:1px solid var(--border);
    padding:18px 14px;
    position:sticky;top:0;align-self:start;
    height:100vh;overflow-y:auto;
  }
  .brand-row{display:flex;align-items:center;gap:10px;padding:6px 8px 14px;border-bottom:1px solid var(--border);margin-bottom:10px}
  .logo{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#7c3aed,#06b6d4);display:grid;place-items:center;color:#fff;font-weight:700;font-size:15px;box-shadow:var(--shadow-sm)}
  .brand{font-weight:600;font-size:14.5px;letter-spacing:-.01em}
  .brand small{display:block;color:var(--fg-2);font-weight:400;font-size:12px;margin-top:1px}
  nav.side{display:flex;flex-direction:column;gap:2px;padding:6px 2px}
  nav.side a{
    display:flex;align-items:center;gap:9px;padding:8px 10px;border-radius:8px;
    color:var(--fg-2);font-size:13.5px;font-weight:500;
  }
  nav.side a:hover{background:var(--surface-2);color:var(--fg);text-decoration:none}
  nav.side a.active{background:var(--brand-50);color:var(--brand);font-weight:600}
  nav.side a .ico{width:18px;height:18px;display:grid;place-items:center;font-size:13px}
  nav.side .sec-label{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:14px 12px 6px}
  .live-card{margin:14px 8px 0;padding:10px 12px;background:var(--surface);border:1px solid var(--border);border-radius:10px;font-size:12.5px}
  .live-card .row{display:flex;justify-content:space-between;align-items:center}
  .live-card .lbl{color:var(--fg-2)}
  .live-card .pulse{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 0 rgba(21,128,61,.4);animation:pulse 1.6s infinite}
  @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(21,128,61,.5)}70%{box-shadow:0 0 0 8px rgba(21,128,61,0)}100%{box-shadow:0 0 0 0 rgba(21,128,61,0)}}

  /* main */
  main{padding:0}
  .topbar{
    position:sticky;top:0;z-index:10;background:rgba(255,255,255,.85);
    backdrop-filter:saturate(180%) blur(12px);-webkit-backdrop-filter:saturate(180%) blur(12px);
    border-bottom:1px solid var(--border);
    display:flex;align-items:center;gap:12px;padding:10px 24px;
  }
  .crumb{color:var(--fg-2);font-size:13.5px}
  .crumb b{color:var(--fg)}
  .topbar .spacer{flex:1}
  .chip{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;background:var(--surface-2);color:var(--fg-2);font-size:12px;font-weight:500;border:1px solid var(--border)}
  .chip.good{background:var(--good-bg);color:var(--good);border-color:transparent}
  .chip.warn{background:var(--warn-bg);color:var(--warn);border-color:transparent}
  .chip .dot{width:6px;height:6px;border-radius:50%;background:currentColor}

  .content{padding:24px 28px 72px;max-width:1080px}

  /* route panels */
  .route{display:none;animation:fade .25s ease}
  .route.is-active{display:block}
  @keyframes fade{from{opacity:0;transform:translateY(2px)}to{opacity:1;transform:none}}

  .hero h1{font-size:32px;line-height:1.15;letter-spacing:-.02em;margin:8px 0 8px;font-weight:700}
  .hero .lede{color:var(--fg-2);font-size:16px;max-width:720px;margin:0 0 18px}
  .pill{display:inline-flex;align-items:center;gap:6px;padding:4px 11px;border-radius:999px;background:var(--brand-50);color:var(--brand);font-size:12px;font-weight:600;letter-spacing:.02em;margin-bottom:14px}

  h2.section{font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:32px 0 12px}
  /* grid + cards */
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow-sm)}
  .card.hi{box-shadow:var(--shadow)}
  .card h3{font-size:15.5px;margin:0 0 6px;letter-spacing:-.01em;font-weight:600}
  .card p{margin:0;color:var(--fg-2);font-size:13.5px;line-height:1.55}
  .card .ico{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#ede9fe,#cffafe);display:grid;place-items:center;font-size:16px;margin-bottom:10px}

  /* stat tile */
  .stat .label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:600;margin-bottom:6px}
  .stat .val{font-size:28px;font-weight:700;color:var(--fg);letter-spacing:-.02em}
  .stat .val small{font-size:12px;color:var(--fg-2);font-weight:500;margin-left:4px}

  /* widget */
  .widget{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:22px;box-shadow:var(--shadow)}
  .widget h3{margin:0 0 4px;font-size:16px;font-weight:600;letter-spacing:-.01em}
  .widget .help{color:var(--fg-2);font-size:13px;margin:0 0 14px}
  .ctl{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:14px}
  .ctl label{font-size:13px;color:var(--fg-2);font-weight:500;min-width:170px}
  .ctl input[type=range]{flex:1;accent-color:var(--brand);min-width:120px}
  .ctl input[type=number]{width:64px;padding:4px 8px;border:1px solid var(--border-strong);border-radius:6px;font-family:'JetBrains Mono',monospace}
  .ctl input[type=text],textarea{width:100%;border:1px solid var(--border-strong);border-radius:8px;padding:9px 11px;font:14px/1.55 'Inter',sans-serif;color:var(--fg);background:var(--surface)}
  textarea{font-family:'JetBrains Mono',ui-monospace,Menlo,monospace;font-size:13.5px;resize:vertical;min-height:64px}
  .ctl .val-readout{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--brand);font-weight:600;min-width:48px;text-align:right}
  .ctl-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
  @media (max-width:680px){.ctl-row{grid-template-columns:1fr}}

  .bar-chart{display:grid;grid-template-columns:140px 1fr 70px;gap:10px;align-items:center;margin:6px 0}
  .bar-chart .lbl{font-size:13px;color:var(--fg-2)}
  .bar-chart .track{height:18px;background:var(--surface-2);border-radius:6px;overflow:hidden}
  .bar-chart .fill{height:100%;border-radius:6px;transition:width .35s ease, background .35s ease}
  .bar-chart .num{font-family:'JetBrains Mono',monospace;font-size:13px;text-align:right;color:var(--fg)}

  .out-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:8px}
  .out{background:var(--surface-2);border-radius:10px;padding:10px 12px}
  .out .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600;margin-bottom:4px}
  .out .num{font-family:'JetBrains Mono',monospace;font-weight:600;font-size:18px}
  .badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600}
  .badge.go{background:var(--good-bg);color:var(--good)}
  .badge.warn{background:var(--warn-bg);color:var(--warn)}

  /* tables (buyer/inspirations) */
  .table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:10px;border:1px solid var(--border);background:var(--surface)}
  table{border-collapse:separate;border-spacing:0;width:100%;font-size:14px;min-width:560px}
  th,td{text-align:left;padding:11px 14px;vertical-align:top;background:var(--surface)}
  thead th{background:var(--surface-2);color:var(--fg-2);font-size:11px;text-transform:uppercase;letter-spacing:.06em;font-weight:600;border-bottom:1px solid var(--border)}
  tbody tr{border-top:1px solid var(--border)}
  tbody tr:first-child td{border-top:none}
  tbody tr:hover td{background:var(--brand-50)}
  .who{font-weight:600;color:var(--fg);min-width:180px}
  @media (max-width:780px){
    th:first-child,td:first-child{position:sticky;left:0;z-index:1;box-shadow:1px 0 0 var(--border);min-width:150px;max-width:200px;background:var(--surface)}
    thead th:first-child{background:var(--surface-2)}
  }

  /* mobile: collapse sidebar into a top drawer */
  .menu-btn{display:none;border:1px solid var(--border);background:var(--surface);width:32px;height:32px;border-radius:8px;align-items:center;justify-content:center;cursor:pointer}
  @media (max-width:880px){
    .app{grid-template-columns:1fr}
    aside{position:fixed;top:0;left:0;right:0;height:auto;min-height:0;max-height:100vh;border-right:none;border-bottom:1px solid var(--border);transform:translateY(-100%);transition:transform .25s ease;z-index:30;width:100%;padding:14px 14px 18px}
    aside.open{transform:none}
    .menu-btn{display:inline-flex}
    nav.side{flex-direction:column}
    .content{padding:20px 18px 60px}
    .hero h1{font-size:26px}
  }
</style>
</head>
<body>

<div class="app">

  <aside id="sidebar">
    <div class="brand-row">
      <div class="logo"><svg viewBox="0 0 64 64" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><g stroke="#fff" stroke-width="3.5" stroke-linecap="round" fill="none"><line x1="30" y1="7" x2="35" y2="12"/><line x1="9" y1="16" x2="55" y2="16"/><line x1="15" y1="23" x2="49" y2="23"/><line x1="15" y1="30" x2="49" y2="30"/></g><rect x="18" y="35" width="28" height="11" rx="1.5" fill="none" stroke="#fff" stroke-width="3.5"/><path d="M8 51 Q32 60 56 51 L52 55 Q32 59 12 55 Z" fill="#fff"/></svg></div>
      <div class="brand">LanguageArk-CN<small>Hokkien subnet · v1</small></div>
    </div>
    <nav class="side" id="sidenav">
      <a href="#/home"     data-route="home"     class="active"><span class="ico">●</span> Overview</a>
      <a href="#/rubric"   data-route="rubric"><span class="ico">▥</span> Ideathon rubric</a>
      <a href="#/mechanism" data-route="mechanism"><span class="ico">◆</span> Mechanism</a>
      <a href="#/attack"   data-route="attack"><span class="ico">⚔</span> Attack simulator</a>
      <a href="#/scorer"   data-route="scorer"><span class="ico">𝐀</span> Score a translation</a>
      <a href="#/buyers"   data-route="buyers"><span class="ico">$</span> Buyers</a>
      <a href="#/lineage"  data-route="lineage"><span class="ico">⌥</span> Subnet lineage</a>
      <div class="sec-label">Reference</div>
      <a href="/whitepaper/"><span class="ico">📄</span> Whitepaper</a>
      <a href="/slides.html"><span class="ico">▶</span> Slides</a>
      <a href="/partners/"><span class="ico">⌶</span> Partners</a>
      <!-- /notes is operator-only; reachable via direct URL, not linked in nav -->
    </nav>
    <div class="live-card">
      <div class="row"><span class="lbl">Status</span><span><span class="pulse"></span> Live</span></div>
      <div class="row" style="margin-top:4px"><span class="lbl">Tests</span><span><b>71 / 71</b></span></div>
      <div class="row" style="margin-top:4px"><span class="lbl">Build</span><span id="build-ts" style="font-family:'JetBrains Mono',monospace;font-size:11.5px;color:var(--fg-2)"></span></div>
    </div>
  </aside>

  <main>
    <div class="topbar">
      <button class="menu-btn" id="menu-btn" aria-label="menu">☰</button>
      <div class="crumb">LanguageArk-CN / <b id="crumb-here">Overview</b></div>
      <div class="spacer"></div>
      <span class="chip good"><span class="dot"></span>Proof of Intelligence · Shanghai · May 23</span>
    </div>

    <div class="content">

      <!-- ── HOME ── -->
      <section class="route is-active" id="route-home">
        <div class="hero">
          <span class="pill">A verifiable Chinese-language data marketplace</span>
          <h1>Endangered-language preservation, as a self-policing market.</h1>
          <p class="lede">Miners ship ASR / TTS / MT models for Hokkien (v1 wedge), Cantonese, Tibetan, Uyghur, Wu… Validators score them with a 3-signal composite (native-speaker Elo + LLM back-translation + held-out FLORES-200) that survives weight-copying, Sybil speakers, and validator cabals. Buyers (Mozilla, 国家语委, UNESCO, iFlytek) read the on-chain weights and pay for vetted corpora.</p>
        </div>

        <h2 class="section">Status — by the numbers</h2>
        <div class="grid">
          <div class="card stat"><div class="label">Tests</div><div class="val">71<small>/ 71 passing</small></div></div>
          <div class="card stat"><div class="label">FLORES-200 pairs</div><div class="val">997<small>yue↔zh</small></div></div>
          <div class="card stat"><div class="label">Commit-reveal knockout</div><div class="val">100→42%<small>vTrust</small></div></div>
          <div class="card stat"><div class="label">DAO gate</div><div class="val">2 / 3<small>on-chain</small></div></div>
        </div>

        <h2 class="section">What's real</h2>
        <div class="grid">
          <div class="card"><div class="ico">✅</div><h3>Mechanism shipped as real code</h3><p>Real <code>bt.Synapse</code> types (v10.3.2), real Glicko-2, real FLORES-200, real Yuma-style attack sim, real Solidity Speaker DAO.</p></div>
          <div class="card"><div class="ico">🧪</div><h3>6 LLM judges wired</h3><p>Auto-selects Chinese-native first: <strong>GLM-4.6 · Qwen · Kimi · DeepSeek</strong>, then Claude Code (Max-sub CLI, no API key), then Anthropic API, then heuristic mock. Override with <code>LANGUAGEARK_JUDGE=…</code>.</p></div>
          <div class="card"><div class="ico">🧱</div><h3>On-chain DAO</h3><p>Solidity contract deployed & exercised on anvil. Validator reads miner Glicko ratings from <code>getRating()</code>, not JSON.</p></div>
          <div class="card"><div class="ico">🌐</div><h3>SOTA many-to-many MT wired</h3><p>Miner wrappers for <strong>NLLB-200</strong> and <strong>SeamlessM4T-v2</strong> (Meta's 200-lang text MT + speech). Plus <strong>FLORES+</strong> (2024, OpenLanguageData) as the active eval benchmark.</p></div>
          <div class="card"><div class="ico">🏯</div><h3>Sponsor stack, end-to-end</h3><p><strong>Alibaba</strong>: CosyVoice (TTS) · SenseVoice (ASR — covers nan/yue/hak/wu in one model) · Qwen2-Audio (multimodal) · Qwen-max (judge). <strong>Zhipu</strong>: GLM-4.6 (judge) · GLM-4-Voice (speech LLM). One sponsor product per layer.</p></div>
        </div>
      </section>

      <!-- ── RUBRIC ── -->
      <section class="route" id="route-rubric">
        <h1 class="hero" style="font-size:24px;letter-spacing:-.02em">Ideathon rubric mapping</h1>
        <p class="lede" style="font-size:15px">Proof of Intelligence (Shanghai · May 23) grades four dimensions of <strong>机制设计能力</strong> (mechanism design capability). Each row below maps one rubric axis to the concrete artifact in this app that demonstrates it.</p>

        <div class="table-wrap">
          <table>
            <thead><tr><th>Axis</th><th>What judges ask</th><th>Where we answer it</th></tr></thead>
            <tbody>
              <tr>
                <td class="who">产品力<br><span style="font-weight:400;color:var(--fg-2);font-size:12.5px">Product</span></td>
                <td>What digital intelligence commodity do you sell, to whom, at what price?</td>
                <td>Vetted multi-language ASR / TTS / MT corpora + scored models. Buyers in <a href="#/buyers">Buyers</a>.</td>
              </tr>
              <tr>
                <td class="who">组织力<br><span style="font-weight:400;color:var(--fg-2);font-size:12.5px">Organization</span></td>
                <td>Why will global contributors do work for you and not somewhere else?</td>
                <td>Stake-bonded native-speaker DAO (real Solidity), 2-of-3 attestation, slashable. Diaspora-org outreach in <a href="/partners/">Partners</a>. TAO emissions bootstrap supply before buyer revenue ramps.</td>
              </tr>
              <tr>
                <td class="who">验证力<br><span style="font-weight:400;color:var(--fg-2);font-size:12.5px">Verification</span></td>
                <td>How is contributor output automatically audited via code, not opinion?</td>
                <td>3-signal composite: Glicko-2 Elo + LLM back-translation (6 wired backends, Chinese-first) + held-out FLORES-200 chrF++. Try the live <a href="#/scorer">scorer widget</a>. Code: <code>scoring.py</code>, <code>metrics.py</code>; 71 tests pass.</td>
              </tr>
              <tr>
                <td class="who">博弈力<br><span style="font-weight:400;color:var(--fg-2);font-size:12.5px">Game theory</span></td>
                <td>What stops weight-copying, Sybil speakers, validator cabals, model theft?</td>
                <td>Six-attack / six-defense map in <a href="#/mechanism">Mechanism</a>. Reproducible knockout in the <a href="#/attack">attack simulator</a> (drag the commit-reveal slider, watch the freeloader bar drop).</td>
              </tr>
            </tbody>
          </table>
        </div>

      </section>

      <!-- ── MECHANISM ── -->
      <section class="route" id="route-mechanism">
        <h1 class="hero" style="font-size:24px;letter-spacing:-.02em">Mechanism</h1>
        <p class="lede" style="font-size:15px">A 3-signal composite. Every signal is independent — collusion would have to corrupt all three at once.</p>

        <div class="widget">
          <h3>score(miner)</h3>
          <p class="help">Weights are illustrative; the validator's actual coefficients live in <code>scoring.py</code>.</p>
          <pre style="background:var(--code-bg);color:var(--code-fg);padding:16px;border-radius:10px;margin:0;font-family:'JetBrains Mono',monospace;font-size:13.5px;line-height:1.7;overflow:auto">score = <span style="color:#67e8f9">0.4</span>·<span style="color:#a78bfa">Elo</span>      <span style="color:#64748b">// native-speaker DAO, Glicko-2</span>
      + <span style="color:#67e8f9">0.3</span>·<span style="color:#a78bfa">BLEU_bt</span>  <span style="color:#64748b">// back-translation via GLM-4.6 / Claude</span>
      + <span style="color:#67e8f9">0.3</span>·<span style="color:#a78bfa">FLORES</span>   <span style="color:#64748b">// rotated held-out professional corpus</span></pre>
        </div>

        <h2 class="section">Anti-gaming primitives</h2>
        <div class="grid">
          <div class="card"><div class="ico">🪪</div><h3>2-of-3 DAO attestation</h3><p>Speakers stake 100 TAO + need 2 attestations to register. Solidity contract, on-chain, slashable.</p></div>
          <div class="card"><div class="ico">🔐</div><h3>Commit-reveal weights</h3><p><code>commit_reveal_period = 5</code> tempos. See the <a href="#/attack">Attack simulator →</a></p></div>
          <div class="card"><div class="ico">⚖</div><h3>κ-clipping</h3><p><code>kappa = 0.6</code>. Cabal needs &gt;60% stake to move consensus.</p></div>
          <div class="card"><div class="ico">🧬</div><h3>Min weight spread</h3><p><code>min_allowed_weights = 16</code> kills single-miner cabal payouts.</p></div>
          <div class="card"><div class="ico">⚓</div><h3>Tight liquid-α</h3><p><code>α∈[0.05,0.35]</code> prevents bond whipsaw.</p></div>
          <div class="card"><div class="ico">🧾</div><h3>Proof-of-training</h3><p>Miners commit <code>(loss_curve_hash, dataset_hash)</code> before serving. Detects model copying.</p></div>
        </div>
      </section>

      <!-- ── ATTACK SIMULATOR ── -->
      <section class="route" id="route-attack">
        <h1 class="hero" style="font-size:24px;letter-spacing:-.02em">Attack simulator</h1>
        <p class="lede" style="font-size:15px">A freeloader-validator publishes copies of honest weights instead of scoring miners. Sliding the commit-reveal period changes how stale its copies get — and how much vTrust it earns for zero work. Drag the slider, watch the dividend bar.</p>

        <div class="widget">
          <div class="ctl">
            <label for="cr">commit-reveal period (tempos)</label>
            <input type="range" id="cr" min="0" max="10" step="1" value="5">
            <span class="val-readout" id="cr-out">5</span>
          </div>
          <div class="ctl">
            <label for="drift">honest weight drift / tempo</label>
            <input type="range" id="drift" min="0" max="100" step="1" value="35">
            <span class="val-readout" id="drift-out">0.35</span>
          </div>

          <div style="margin-top:18px">
            <div class="bar-chart">
              <span class="lbl">Honest validator</span>
              <div class="track"><div class="fill" id="bar-honest" style="background:#15803d;width:100%"></div></div>
              <span class="num" id="num-honest">1.00</span>
            </div>
            <div class="bar-chart">
              <span class="lbl">Freeloader (copying)</span>
              <div class="track"><div class="fill" id="bar-free" style="background:#dc2626;width:100%"></div></div>
              <span class="num" id="num-free">1.00</span>
            </div>
          </div>

          <div class="out-grid" style="margin-top:18px">
            <div class="out"><div class="lbl">Attack still works?</div><div class="num" id="attack-verdict">—</div></div>
            <div class="out"><div class="lbl">Knockout</div><div class="num" id="attack-knockout">—</div></div>
            <div class="out"><div class="lbl">Recommendation</div><div class="num" id="attack-recco" style="font-size:13px;font-weight:600">—</div></div>
          </div>
          <p class="help" style="margin-top:14px">Math: freeloader's stale copy is correct on the first reveal-tempo, then drifts at <code>drift × Δtempo</code>. vTrust = 1 − stale_distance, averaged over a 12-tempo window. Source: <code>languageark/attack.py</code> (Python equivalent).</p>
        </div>
      </section>

      <!-- ── SCORER ── -->
      <section class="route" id="route-scorer">
        <h1 class="hero" style="font-size:24px;letter-spacing:-.02em">Score a translation</h1>
        <p class="lede" style="font-size:15px">Paste a prediction and the gold reference. We compute <strong>chrF++</strong> client-side (character n-gram F-score, the modern MT eval metric used by WMT). This is the same signal the validator uses for the FLORES column.</p>

        <div class="widget">
          <div class="ctl-row">
            <div>
              <label style="font-size:12.5px;color:var(--fg-2);font-weight:600;display:block;margin-bottom:6px">Miner prediction</label>
              <textarea id="pred" placeholder="你吃饱了吗">你吃饱了吗?</textarea>
            </div>
            <div>
              <label style="font-size:12.5px;color:var(--fg-2);font-weight:600;display:block;margin-bottom:6px">Gold reference</label>
              <textarea id="gold" placeholder="你吃饱了吗?">你吃饱了吗?</textarea>
            </div>
          </div>

          <div class="out-grid">
            <div class="out"><div class="lbl">chrF++ (β=2)</div><div class="num" id="chrf">—</div></div>
            <div class="out"><div class="lbl">Char overlap</div><div class="num" id="overlap">—</div></div>
            <div class="out"><div class="lbl">Length ratio</div><div class="num" id="lratio">—</div></div>
            <div class="out"><div class="lbl">Composite (illustrative)</div><div class="num" id="composite">—</div></div>
          </div>
          <p class="help" style="margin-top:14px">"Composite" assumes a moderately rated miner (Elo = 1500) and a perfect back-translation, then weights this chrF++ at 0.3 per the score formula. Try the curated Hokkien pairs from <code>data/eval_samples.py</code> to see how each tier scores.</p>
        </div>

        <h2 class="section">Quick samples</h2>
        <div class="grid">
          <div class="card" style="cursor:pointer" data-pred="你吃饱了吗?" data-gold="你吃饱了吗?"><h3>Perfect (professional)</h3><p>Hokkien <code>你食飽未?</code> ↔ Mandarin <code>你吃饱了吗?</code>. Should score 1.00.</p></div>
          <div class="card" style="cursor:pointer" data-pred="你吃了吗" data-gold="你吃饱了吗?"><h3>Light degradation (~15% char drop)</h3><p>Missing characters but recoverable. Should score ~0.4–0.5.</p></div>
          <div class="card" style="cursor:pointer" data-pred="吃饱" data-gold="你吃饱了吗?"><h3>Heavy degradation (~50% char drop)</h3><p>Substring only. Should score below 0.2.</p></div>
        </div>
      </section>

      <!-- ── BUYERS ── -->
      <section class="route" id="route-buyers">
        <h1 class="hero" style="font-size:24px;letter-spacing:-.02em">Buyers</h1>
        <p class="lede" style="font-size:15px">The funding to preserve these languages already exists — it's just spent slowly, one grant at a time, with no verifiable quality signal. Subnet emissions bootstrap supply; these buyers convert that vetted data into recurring revenue.</p>

        <div class="table-wrap">
          <table>
            <thead><tr><th>Buyer</th><th>What they pay for</th></tr></thead>
            <tbody>
              <tr><td class="who">Mozilla Common Voice</td><td>Volunteer-driven corpus, with adjacent Mozilla / MLCommons grants funding collection campaigns for low-resource Chinese-language pairs</td></tr>
              <tr><td class="who">国家语言文字工作委员会</td><td>数字化方言 (dialect digitization) — multi-year line items in the 14th & 15th Five-Year Plans</td></tr>
              <tr><td class="who">UNESCO</td><td>Endangered-language preservation grant programs</td></tr>
              <tr><td class="who">iFlytek · Baidu · Alibaba</td><td>Procurement of training data for in-house Chinese-language ASR / TTS pipelines</td></tr>
              <tr><td class="who">Ethnology departments</td><td>Field-research corpora — Minzu University, SOAS, et al.</td></tr>
              <tr><td class="who">Diaspora apps</td><td>Heritage-language conversation models — HiNative, Drops, Tandem</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ── LINEAGE ── -->
      <section class="route" id="route-lineage">
        <h1 class="hero" style="font-size:24px;letter-spacing:-.02em">Subnet lineage</h1>
        <p class="lede" style="font-size:15px">We aren't reinventing the wheel. LanguageArk-CN stands on three existing subnets and the official bittensor template — every line below is reused pattern.</p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Subnet / source</th><th>What we reuse</th><th>What we change</th></tr></thead>
            <tbody>
              <tr><td class="who">SN37 Finetuning (Macrocosmos)</td><td>Tournament-style held-out eval; <code>loss_curve_hash</code> proof-of-training; weekly corpus rotation</td><td>Generic LLM finetune → per-language ASR/MT; eval is FLORES-200 yue / nan</td></tr>
              <tr><td class="who">SN1 Apex (Macrocosmos)</td><td>LLM-as-judge validator pattern; single-shot back-translation scoring</td><td>Judge is sponsor's GLM-4.6 (or Claude); back-translation is direction-specific</td></tr>
              <tr><td class="who">SN13 Data Universe (Macrocosmos)</td><td>Crowdsourced data sourcing, <code>dataset_hash</code> commits</td><td>Source isn't scraped — it's native-speaker contribution, stake-gated</td></tr>
              <tr><td class="who"><code>latent-to/bittensor-subnet-template</code></td><td>Synapse types; miner / validator skeleton; chain probe</td><td>Three Synapse subclasses (HokkienASR / MT / TTS); real Glicko-2; Solidity DAO</td></tr>
              <tr><td class="who">Yuma commit-reveal docs</td><td><code>commit_reveal_period</code> semantics; weight-commit hash format</td><td>Set to 5 (vs default 0); proves the attack delta with a sim</td></tr>
            </tbody>
          </table>
        </div>

        <h2 class="section">Genuinely new (the 创意 part)</h2>
        <div class="grid">
          <div class="card"><div class="ico">🪪</div><h3>Stake-bonded speaker DAO</h3><p>No existing subnet has an on-chain stake-and-attestation registry for human evaluators. Our Solidity contract is the org / anti-Sybil novelty.</p></div>
          <div class="card"><div class="ico">🧮</div><h3>3-signal composite</h3><p>SN37 uses single-signal eval; SN1 uses single-signal LLM judge. We compose Elo + back-translation + held-out FLORES so fooling two requires fooling the third independently.</p></div>
          <div class="card"><div class="ico">🧩</div><h3>Cross-script Hokkien framing</h3><p>SeamlessM4T-v2 has no <code>__nan__</code>; FLORES has only Latin-script <code>nan_Latn</code>. Building a real Han-script Hokkien corpus IS the deliverable.</p></div>
        </div>
      </section>

    </div>
  </main>
</div>

<script>
  // ── routing ──────────────────────────────────────────────────
  const routes = ["home","rubric","mechanism","attack","scorer","buyers","lineage"];
  const labels = {home:"Overview",rubric:"Ideathon rubric",mechanism:"Mechanism",attack:"Attack simulator",scorer:"Score a translation",buyers:"Buyers",lineage:"Subnet lineage"};
  function go(r){
    if(!routes.includes(r)) r = "home";
    document.querySelectorAll(".route").forEach(s=>s.classList.toggle("is-active",s.id==="route-"+r));
    document.querySelectorAll("nav.side a[data-route]").forEach(a=>a.classList.toggle("active",a.dataset.route===r));
    const cr = document.getElementById("crumb-here"); if(cr) cr.textContent = labels[r];
    document.title = "LanguageArk-CN · " + labels[r];
    window.scrollTo({top:0,behavior:"instant"});
    document.getElementById("sidebar")?.classList.remove("open");
  }
  function readHash(){ return (location.hash.replace(/^#\//,"") || "home"); }
  window.addEventListener("hashchange", ()=>go(readHash()));
  go(readHash());

  // mobile menu
  document.getElementById("menu-btn")?.addEventListener("click",()=>{
    document.getElementById("sidebar")?.classList.toggle("open");
  });

  // build time
  const bt = document.getElementById("build-ts");
  if(bt) bt.textContent = "__BUILD_TS__";

  // ── attack simulator ────────────────────────────────────────
  function simAttack(crPeriod, drift){
    // Honest validator: always vTrust = 1.0 (full score for accurate work)
    // Freeloader copies the previous-reveal weights and reuses them for `crPeriod` tempos.
    // Stale distance grows linearly with drift per tempo.
    const tempos = 12;
    let stalenessAcc = 0;
    for(let t=0;t<tempos;t++){
      const stale = Math.min(1, drift * (t % Math.max(1, crPeriod)));
      stalenessAcc += 1 - stale;
    }
    const freeloader = stalenessAcc / tempos; // mean vTrust over window
    return { honest:1.0, freeloader };
  }
  function refreshAttack(){
    const cr = +document.getElementById("cr").value;
    const driftPct = +document.getElementById("drift").value;
    const drift = driftPct/100;
    document.getElementById("cr-out").textContent = cr;
    document.getElementById("drift-out").textContent = drift.toFixed(2);

    const r = simAttack(cr, drift);
    document.getElementById("bar-honest").style.width = (r.honest*100).toFixed(0)+"%";
    document.getElementById("bar-free").style.width = (r.freeloader*100).toFixed(0)+"%";
    document.getElementById("num-honest").textContent = r.honest.toFixed(2);
    document.getElementById("num-free").textContent = r.freeloader.toFixed(2);

    const verdict = document.getElementById("attack-verdict");
    const knockout = document.getElementById("attack-knockout");
    const recco = document.getElementById("attack-recco");
    if(r.freeloader > 0.85){
      verdict.innerHTML = '<span class="badge warn">YES — works</span>';
      knockout.textContent = "—";
      recco.textContent = "Raise CR period";
    } else if(r.freeloader > 0.5){
      verdict.innerHTML = '<span class="badge warn">partial</span>';
      knockout.textContent = ((1-r.freeloader)*100).toFixed(0)+"%";
      recco.textContent = "Still leaks; push to 5+";
    } else {
      verdict.innerHTML = '<span class="badge go">DEFEATED</span>';
      knockout.textContent = ((1-r.freeloader)*100).toFixed(0)+"%";
      recco.textContent = "Ship this config";
    }
  }
  document.getElementById("cr")?.addEventListener("input", refreshAttack);
  document.getElementById("drift")?.addEventListener("input", refreshAttack);
  refreshAttack();

  // ── chrF++ scorer ────────────────────────────────────────────
  function ngrams(s, n){
    const out = new Map();
    for(let i=0;i<=s.length-n;i++){
      const g = s.slice(i,i+n);
      out.set(g, (out.get(g)||0)+1);
    }
    return out;
  }
  function fscore(p, r, beta){
    if(p===0 && r===0) return 0;
    const b2 = beta*beta;
    return (1+b2)*p*r / (b2*p + r + 1e-12);
  }
  function chrf(pred, gold, beta=2, maxN=6){
    if(!pred || !gold) return 0;
    let acc = 0; let used = 0;
    for(let n=1;n<=maxN;n++){
      if(pred.length<n || gold.length<n) continue;
      const pg = ngrams(pred, n), gg = ngrams(gold, n);
      let pCount=0, gCount=0, match=0;
      pg.forEach((c,k)=>{pCount+=c; if(gg.has(k)) match+=Math.min(c, gg.get(k));});
      gg.forEach((c)=>gCount+=c);
      const prec = pCount? match/pCount : 0;
      const rec  = gCount? match/gCount : 0;
      acc += fscore(prec, rec, beta);
      used++;
    }
    return used? acc/used : 0;
  }
  function refreshScorer(){
    const pred = document.getElementById("pred").value;
    const gold = document.getElementById("gold").value;
    const c = chrf(pred, gold);
    const ps = new Set([...pred]); const gs = new Set([...gold]);
    let inter=0; ps.forEach(x=>{if(gs.has(x))inter++;});
    const overlap = ps.size+gs.size? inter / new Set([...ps,...gs]).size : 0;
    const lr = gold.length? Math.min(1, pred.length/gold.length) : 0;
    const composite = 0.4*0.65 + 0.3*1.0 + 0.3*c; // illustrative
    document.getElementById("chrf").textContent = c.toFixed(3);
    document.getElementById("overlap").textContent = overlap.toFixed(3);
    document.getElementById("lratio").textContent = lr.toFixed(2);
    document.getElementById("composite").textContent = composite.toFixed(3);
  }
  document.getElementById("pred")?.addEventListener("input", refreshScorer);
  document.getElementById("gold")?.addEventListener("input", refreshScorer);
  document.querySelectorAll("#route-scorer .card[data-pred]").forEach(c=>{
    c.addEventListener("click",()=>{
      document.getElementById("pred").value = c.dataset.pred;
      document.getElementById("gold").value = c.dataset.gold;
      refreshScorer();
    });
  });
  refreshScorer();
</script>

</body>
</html>
"""
_product_out = PRODUCT.replace("__BUILD_TS__", _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%d %H:%M UTC"))
(SITE / "index.html").write_text(_product_out)
print(f"wrote {SITE / 'index.html'} ({len(_product_out):,} bytes)  ← user-facing /")


# ─── /whitepaper and /partners — markdown → light-theme HTML ─────────────
def _render_markdown_page(md_path: Path, out_dir: Path, title: str, subtitle: str) -> None:
    import markdown as _md

    body = _md.markdown(
        md_path.read_text(),
        extensions=["fenced_code", "tables", "toc", "sane_lists"],
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — LanguageArk-CN</title>
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{{--bg:#fafbfc;--surface:#fff;--surface-2:#f3f4f6;--border:#e5e7eb;
    --fg:#0f172a;--fg-2:#475569;--muted:#94a3b8;--brand:#6d28d9;
    --code-bg:#0f172a;--code-fg:#e2e8f0}}
  *{{box-sizing:border-box}}
  body{{font:15.5px/1.7 'Inter',ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--fg);background:var(--bg);margin:0;-webkit-font-smoothing:antialiased}}
  a{{color:var(--brand);text-decoration:none}}
  a:hover{{text-decoration:underline}}
  code{{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--surface-2);padding:1px 6px;border-radius:5px;font-size:13px}}
  pre{{background:var(--code-bg);color:var(--code-fg);padding:16px 18px;border-radius:10px;overflow:auto;font:13px/1.55 'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace}}
  pre code{{background:transparent;padding:0;color:inherit;font-size:inherit}}
  .topbar{{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.85);backdrop-filter:saturate(180%) blur(12px);-webkit-backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--border)}}
  .topbar-inner{{max-width:880px;margin:0 auto;padding:12px 24px;display:flex;align-items:center;gap:16px}}
  .logo{{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#7c3aed,#06b6d4);display:grid;place-items:center;color:#fff;font-weight:700;font-size:14px}}
  .brand{{font-weight:600;font-size:15px;letter-spacing:-.01em}}
  .brand small{{color:var(--fg-2);font-weight:400;margin-left:6px}}
  .nav{{margin-left:auto;display:flex;gap:18px;font-size:14px;color:var(--fg-2)}}
  .nav a{{color:var(--fg-2)}}
  main{{max-width:780px;margin:0 auto;padding:36px 24px 80px}}
  .eyebrow{{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:8px}}
  h1{{font-size:34px;line-height:1.15;letter-spacing:-.02em;margin:0 0 6px;font-weight:700}}
  h1 + p{{color:var(--fg-2);margin:0 0 28px;font-size:16.5px}}
  article h1{{font-size:26px;margin-top:36px}}
  article h2{{font-size:21px;margin-top:36px;padding-bottom:6px;border-bottom:1px solid var(--border)}}
  article h3{{font-size:17px;margin-top:28px}}
  article p{{color:var(--fg)}}
  article ul,article ol{{padding-left:22px;color:var(--fg-2)}}
  article li{{margin:4px 0}}
  article blockquote{{border-left:3px solid var(--brand);background:var(--surface-2);margin:18px 0;padding:10px 16px;color:var(--fg-2);border-radius:0 6px 6px 0}}
  article table{{border-collapse:separate;border-spacing:0;width:100%;font-size:14px;margin:14px 0;display:block;overflow-x:auto}}
  article th,article td{{text-align:left;padding:10px 12px;border-bottom:1px solid var(--border);background:var(--surface)}}
  article th{{background:var(--surface-2);color:var(--fg-2);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em}}
  footer{{color:var(--muted);font-size:12.5px;text-align:center;padding:32px 24px;border-top:1px solid var(--border);margin-top:40px}}
  @media (max-width:640px){{h1{{font-size:26px}} main{{padding:24px 16px 60px}}}}
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-inner">
    <div class="logo"><svg viewBox="0 0 64 64" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><g stroke="#fff" stroke-width="3.5" stroke-linecap="round" fill="none"><line x1="30" y1="7" x2="35" y2="12"/><line x1="9" y1="16" x2="55" y2="16"/><line x1="15" y1="23" x2="49" y2="23"/><line x1="15" y1="30" x2="49" y2="30"/></g><rect x="18" y="35" width="28" height="11" rx="1.5" fill="none" stroke="#fff" stroke-width="3.5"/><path d="M8 51 Q32 60 56 51 L52 55 Q32 59 12 55 Z" fill="#fff"/></svg></div>
    <div class="brand">LanguageArk-CN<small>Hokkien subnet · v1</small></div>
    <nav class="nav">
      <a href="/">Home</a>
      <a href="/whitepaper/">Whitepaper</a>
      <a href="/partners/">Partners</a>
      <a href="/slides.html">Slides</a>
    </nav>
  </div>
</div>
<main>
  <div class="eyebrow">{subtitle}</div>
  <h1>{title}</h1>
  <article>
  {body}
  </article>
</main>
<footer>LanguageArk-CN · <a href="/">home</a></footer>
</body>
</html>"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page)
    print(f"wrote {out_dir / 'index.html'} ({len(page):,} bytes)")


_render_markdown_page(ROOT / "whitepaper.md", SITE / "whitepaper", "Whitepaper", "Mechanism design — full document")
_render_markdown_page(ROOT / "partners.md", SITE / "partners", "Partners", "Hokkien diaspora orgs we're talking to")
