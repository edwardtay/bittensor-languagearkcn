# OUTREACH — turning the partner list into LOIs

> The fastest credibility win for an ideathon is a **named endorsement** from a real org. One signed LOI or quoted email beats ten more forge tests. This file is the ask-templates + status tracker.

## Status tracker

| Org | Hub | Tier | Status | Owner | Next action |
|---|---|---|---|---|---|
| Xiamen University 闽南语研究所 | Fujian | A | not started | — | cold email to dept secretary |
| 教育部 本土語言組 | Taiwan | A | not started | — | LinkedIn intro via NTU alumni |
| Singapore Hokkien Huay Kuan | SG | A | not started | — | walk-in at Telok Ayer office |
| Penang Hokkien Language Assoc. | MY | A | not started | — | FB Messenger to admin |
| Mozilla Common Voice (nan-tw) | global | A | not started | — | post in `mozilla.discourse` + email program lead |
| iFlytek speech-data team | 合肥 | B | not started | — | warm intro via Zhipu sponsor booth at event |
| UNESCO Endangered Languages | global | B | not started | — | program officer email (slow channel) |
| 国家语言文字工作委员会 | Beijing | C | gated | — | needs domestic intro; revisit post-event |
| NTU 台灣文學所 | Taiwan | B | not started | — | dept email |
| HiNative heritage-learner groups | global | C | not started | — | forum post, low-effort |

**Tier A** = realistic 30-day LOI. **Tier B** = 60-90 days. **Tier C** = political/long sales cycle.

Goal before the Shanghai pitch (May 23): **one Tier-A reply on the record**, even a one-line email "we'd be open to a pilot conversation."

## Template 1 — academic / linguistics dept (EN)

> **Subject:** Hokkien speech-AI preservation — 5-min ask
>
> Dear Prof. ___,
>
> I'm building **LanguageArk-CN**, a Bittensor-based marketplace that pays native speakers and AI miners to produce verified Hokkien speech and translation data. We're launching at the Proof of Intelligence ideathon in Shanghai (2026-05-23) and your dept's POJ / 閩南語 corpus work is exactly the calibration data we want to cite.
>
> We're not asking for funding or code. **We're asking for one of:**
> 1. A one-paragraph statement of interest we can quote in the pitch ("Xiamen University's Min Nan Research Institute would consider participating as an attested-speaker pool, subject to standard research-collaboration review.")
> 2. A 20-min call so I can show you the mechanism and you can tell me what would actually work for your institution.
>
> Live site: https://language-ark-cn.lever-labs.com
> Whitepaper: https://language-ark-cn.lever-labs.com/whitepaper/
>
> If even a soft "interested-pending-review" is on the table, please reply with one sentence — that alone moves the project forward materially.
>
> 谢谢,
> Edward Tay

## Template 2 — diaspora org / clan association (EN/中文 mixed)

> **Subject:** 闽南语 AI 保护 — 想请教 5 分钟
>
> 您好,
>
> 我是 Edward,正在做一个叫 **LanguageArk-CN** 的项目 — 让全球闽南语母语者通过区块链共同保护语言数据,贡献者可以获得报酬。即将在 5 月 23 日上海的 Bittensor 黑客松路演。
>
> **想请教**:贵会是否愿意以"观察者会员 (observer member)"的身份出现在我们的合作机构名单上?不收费,不签合同,只是一句"福建会馆愿意在 v1 阶段以观察者身份参与评估"。
>
> 如果可以,请回一句话即可 — 这对我们项目的可信度帮助巨大。
> 网站:https://language-ark-cn.lever-labs.com
>
> 谢谢您的时间,
> Edward
> (English available on request — happy to switch.)

## Template 3 — Mozilla Common Voice program lead (EN)

> **Subject:** A subnet that produces validated Common Voice clips at scale
>
> Hi ___,
>
> Common Voice's `nan-tw` dataset has been stuck under 1 % of validated hours for two years. I'm building a Bittensor subnet whose explicit output is **validated Hokkien clips in the CV submission format** — paid for by token emissions, vetted by a stake-bonded native-speaker DAO, and quality-gated by a 3-signal score (speaker Elo + back-translation BLEU + FLORES held-out).
>
> What I'd love from CV: a **letter of non-objection** confirming you'd accept bulk submissions from a validated-pipeline pilot, subject to your existing review rules. Not a contract, not money — just confirmation that the submission path exists.
>
> Pitch this Saturday in Shanghai. A single sentence from CV before then would help the judges take the buyer side seriously.
>
> https://language-ark-cn.lever-labs.com
>
> Thanks,
> Edward

## Template 4 — iFlytek / Baidu / Alibaba speech-data buyer (EN)

> **Subject:** Hokkien speech-data supply — pre-launch conversation
>
> Hi ___,
>
> Your team works on Chinese-language speech AI, including low-resource Sinitic varieties. I run **LanguageArk-CN**, a Bittensor subnet that will produce validated Hokkien ASR/MT/TTS corpora — gated by a stake-bonded speaker DAO, scored on FLORES-200 + native-speaker Elo + back-translation BLEU. (Customising this template before sending — happy to align it to any public statements your team has made about Hokkien / Min Nan specifically.)
>
> Asking for **15 minutes**, post our 2026-05-23 Shanghai launch, to walk through:
> - the per-minute price point we'd need to clear
> - the format / metadata you'd need
> - whether a pilot procurement (e.g. 100 validated hours) is realistic for FY26
>
> Even a "circle back after pilot data exists" reply is useful — it lets me cite procurement intent at the ideathon.
>
> https://language-ark-cn.lever-labs.com
>
> Best,
> Edward

## When a reply arrives

Drop the email body verbatim (with permission) into `loi/<org-slug>.md` and add the org to the README's quickstart matrix as **`Endorsement — <org>`**. Even a soft "we're interested" email, quoted with sender permission, is a 产品力 + 组织力 score-move for the ideathon panel.

If permission to publish isn't granted, paraphrase in `partners.md` as: *"Confirmed initial interest from <org category> in <hub> (sender contact on file)."*

## What to do at the event

1. **Zhipu booth**: ask for warm intro to their NLP partnerships team — they often have Chinese-speech-vendor relationships.
2. **Alibaba Cloud booth**: same, but for the PAI speech team.
3. **HackQuest / The Mu organisers**: ask if any judge is from a sponsor speech team; if yes, prep a 30-second pre-pitch ask.
4. **Hallway**: any Bittensor builder (Macrocosm, Apex SN1, SN37 finetuning) — get one "this is well-designed" quote on the record for the deck.
