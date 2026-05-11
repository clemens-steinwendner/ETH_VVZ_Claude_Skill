# ETH VVZ Claude Skill

A Claude.ai Agent Skill that lets ETH Zurich students chat about courses and study plans, grounded in factual data from the unofficial [vvzapi](https://github.com/markbeep/vvzapi) (`https://vvzapi.ch`) and the official ETH Studienreglemente.

## What it does

- Look up ETH courses by title, lecturer, semester, ECTS range, language, level, exam type.
- Answer **credit-eligibility** questions: "does this course count toward my BSc CS Wahlfächer?"
- Surface course history, capacity (when published), prerequisites text, and "Offered in" categories.
- Cite the relevant Studienreglement quota and link back to `vvz.ethz.ch` for verification.

## What it does NOT do

- Predict grades or judge lecturer quality.
- Make admission, transfer, or credit-recognition decisions.
- Estimate "workload" beyond ECTS, or recommend "easy ECTS" courses.
- Generate full multi-semester study plans (v1 limit — single-course questions only).
- Detect scheduling conflicts across a basket of courses.
- Report historical enrolment counts (ETH does not publish them).

See `skill/SKILL.md` for the complete behavior contract.

## Data sources

- **vvzapi** (`https://vvzapi.ch`) — unofficial scrape of the ETH Course Catalogue. Used live for every course / lecturer / section / "Offered in" lookup. Credit: [markbeep/vvzapi](https://github.com/markbeep/vvzapi).
- **Bundled programme requirements** — ECTS quotas per programme/category, parsed from a structured reference document compiled from the official ETH Studienreglemente (Rechtssammlung der ETH Zürich). Numeric quotas were independently re-extracted and cross-checked against the source PDFs (188/189 numeric rows match exactly). 34 programmes covered as of the latest build; subcategory rows that carry their KP info inside the label (e.g. "≥ 45 KP") are flagged `is_subcategory: true` with a best-effort `min_kp_constraints` list. See `skill/data/programmes_requirements.json` and the per-record `reglement.url`.

## Installation (claude.ai)

> **Requirements:** A paid claude.ai plan (Pro / Max / Team / Enterprise) — Free does not support custom Skills.

1. **Download the skill bundle:** grab `eth-vvz.zip` from the latest [GitHub Release](https://github.com/clemens-steinwendner/ETH_VVZ_Claude_Skill/releases).
2. **Open claude.ai → Settings → Capabilities → Skills.**
3. **Upload `eth-vvz.zip`** and confirm. claude.ai unpacks the bundle into your account.
4. **Enable the prerequisites** for the skill in claude.ai settings:
   - **Code execution** (Settings → Features).
   - **Network access** for external HTTPS: set domain access to *"All domains"* on personal accounts, or ask your Team/Enterprise admin to allowlist `vvzapi.ch`. (Default is "package managers only" which is not enough — `vvzapi.ch` calls will silently fail.)
5. **Start a new chat.** The skill activates automatically when your message mentions ETH courses, lecturers, programmes, or the VVZ.
6. **Ask away.** Examples: *"What's good for FS26 in MSc INFK with 4–8 ECTS?"* · *"Does 401-3052-10L count toward BSc Math Wahlfächer?"* · *"How long has 263-2400-00L been at ETH?"*

If the skill responds with "vvzapi unreachable", check step 4: domain access is the most common cause.

## Repository layout

```
skill/                       # The shipping skill bundle
├── SKILL.md                 # Orchestration prompt (always loaded)
├── data/
│   ├── programmes_requirements.json  # ECTS quotas, 34 programmes
│   └── programme_aliases.json        # Student vocab → canonical keys
├── references/              # Loaded lazily, only when relevant
│   ├── query_syntax.md
│   ├── semester_codes.md
│   ├── programme_shorthand.md
│   ├── refusals.md
│   └── response_templates.md
├── scripts/
│   ├── vvz_client.py        # vvzapi wrapper (rate-limit, retry, cache, error envelope)
│   └── requirements_lookup.py
└── tests/
    └── test_cases.md        # Manual regression set (not bundled in the zip)

eth-vvz.zip                  # The packaged skill (regenerated per release)
README.md                    # This file
```

## Building / republishing

Regenerating `programmes_requirements.json` from the local source MD (kept private — not in this repo):

```sh
python3 scripts/build_programmes_requirements.py
```

Packaging the skill into the uploadable zip:

```sh
rm -rf /tmp/eth-vvz-build && mkdir -p /tmp/eth-vvz-build/eth-vvz
cp -R skill/SKILL.md skill/references skill/scripts skill/data /tmp/eth-vvz-build/eth-vvz/
(cd /tmp/eth-vvz-build && zip -r "$OLDPWD/eth-vvz.zip" eth-vvz)
```

## Acknowledgements

- [@markbeep](https://github.com/markbeep) for [vvzapi](https://github.com/markbeep/vvzapi), without which this skill would not be feasible.
- ETH Zurich for publishing the Studienreglemente in the [Rechtssammlung](https://rechtssammlung.sp.ethz.ch/).

## Status

Early prototype. Not affiliated with ETH Zurich, and not affiliated with the vvzapi project — we credit it and aim to be a polite client (≤1 req/s, exponential backoff). Verify anything binding (registration, grading, credit transfer) against the official catalogue at [`vvz.ethz.ch`](https://www.vvz.ethz.ch).

Skill licensed under the same terms as the upstream vvzapi: GPL-3.0.
