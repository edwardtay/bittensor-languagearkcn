# LanguageArk-CN — Speaker DAO partner targets

> The native-speaker DAO is the **组织力 (organizational capability)** moat.
> Below are the concrete partner organizations we'd approach for v1 (Hokkien) — by region, with rationale and contact path.

The hackathon pitch claims real recruitment intent, so this list is grounded in actually-existing institutions, not invented.

## Hokkien / Min Nan (v1) — target: 50 stake-bonded speakers across 4 hubs

### Fujian, PRC (target: 15 speakers)

| Org | Role | Why |
|---|---|---|
| **厦门大学 闽南语研究所** (Xiamen University Min Nan Research Institute) | Academic anchor | Largest Hokkien linguistics dept; trains POJ teachers |
| **泉州师范学院 文学与传播学院** | Local-dialect ed | Quanzhou is widely considered the Hokkien "homeland"; PoJ literacy programs |
| **闽南文化研究会** | Community group | Cultural preservation NGO with elder-speaker volunteers |

### Taiwan (target: 15 speakers)

| Org | Role | Why |
|---|---|---|
| **教育部 國語推行委員會 / 本土語言組** | Government | Official Taiwanese-Hokkien certification (`閩南語認證`) — natural pool of attested speakers |
| **臺灣大學 臺灣文學所** (NTU Taiwan Lit) | Academic | Strong POJ + Han-mixed-script research; SeamlessM4T evaluation co-authors |
| **公共電視 台語台** (PTS Taiwanese channel) | Broadcasters | Professional speakers; built-in audio archive for FLORES-style eval set |
| **Lím Phín-jîn 林品任 / 母語復興運動** | Activist orgs | Established Hokkien-rights advocacy; mobilizable speaker base |

### Singapore (target: 10 speakers)

| Org | Role | Why |
|---|---|---|
| **Singapore Hokkien Huay Kuan 福建会馆** | Diaspora anchor | 180-year-old Hokkien clan association; runs Hokkien classes |
| **Speak Hokkien Campaign / Speak Mandarin Counter** | Community | Grassroots Hokkien-revival initiative |
| **NUS Centre for Language Studies** | Academic | Conducts Hokkien sociolinguistics fieldwork |

### Penang/Malaysia + Manila/PH + Diaspora (target: 10 speakers)

| Org | Role | Why |
|---|---|---|
| **Penang Hokkien Language Association** (Persatuan Bahasa Hokkien Pulau Pinang) | Community | Penang Hokkien has unique tonal features; needs its own eval slice |
| **Kaisa Para Sa Kaunlaran** (Manila) | Filipino-Hokkien | Lan-nang variant; ~1M speakers |
| **HiNative / Tandem heritage-learner groups** | Distributed | Self-identified Hokkien heritage learners; voluntary attestation pool |

## Buyer-side LOIs (pre-event outreach prioritization)

Ranked by likelihood of yielding a signable LOI within 30 days of pitch.

1. **Mozilla Common Voice** (highest) — already pays $X/validated-clip; our subnet *is* a validated-clip factory
2. **iFlytek 科大讯飞** — has a Hokkien speech-AI product in development (2024 announcement); buys training data
3. **Penang state gov.** — Penang Hokkien is officially endangered; small but symbolic procurement
4. **UNESCO Atlas of Endangered Languages** — grant program, slow but reputational
5. **Singapore Hokkien Huay Kuan** — cultural-preservation budget; small ticket but PR-friendly
6. **Baidu / Alibaba speech teams** — long sales cycle, large ticket
7. **State Language Commission 国家语委** — 数字化方言 line item; political sensitivity may require domestic-only partner

## Anti-political-risk plan

Some endangered languages (Uyghur, Tibetan, Mongolian) are politically sensitive in PRC.

- **v1 launches ONLY Han-Chinese-language families:** Hokkien, Cantonese, Hakka, Wu. These are non-controversial in both Beijing and Taipei.
- **v2 adds minority languages via international DAO branches** (Geneva-registered foundation), keeping mainland operations clean.
- **State Language Commission is invited as observer-validator, not gatekeeper** — they vote alongside diaspora orgs.

## Speaker DAO mechanism (recap)

A speaker must:

1. Stake **100 TAO** (slashable; returnable on graceful exit)
2. Be **attested by 2 of 3** existing speaker-validators for their language
3. Provide a **POJ-spelled audio sample** for sybil-resistance fingerprinting

Per-language **DAO multisig** holds the staked TAO; a 2/3 quorum can:
- Veto a speaker registration (within 48h of attestation)
- Slash a speaker shown to vote against the BLEU + FLORES consensus repeatedly (≥10 inconsistent votes)
- Approve eval-set rotations (rotating FLORES samples weekly)

This is the **博弈力 + 组织力** combined: the same group whose votes drive Elo also gates entry to that voting pool.
