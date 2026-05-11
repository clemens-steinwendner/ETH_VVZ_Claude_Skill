# ETH VVZ Claude Skill

A Claude skill that lets students chat about ETH Zurich courses and study plans, grounded in factual data from the unofficial [vvzapi](https://github.com/markbeep/vvzapi) (`https://vvzapi.ch`).

## What it does

- Look up courses by title, lecturer, semester, ECTS, language, level, department.
- Answer credit-eligibility questions ("does this count toward BSc MAVT Kernfächer?") using the `Offered in` data exposed by vvzapi's `/unit/{id}/sections` + `/section/{id}/get` endpoints (including the `O` / `W` / `E-` category type).
- Help build and sanity-check personal study plans against a per-programme requirements file the user supplies.

## Data sources

- **vvzapi** (`https://vvzapi.ch`) — unofficial scrape of the ETH Course Catalogue. Used live for: learning units, course instances, lecturers, ratings, and the "Offered in" section/category mapping.
- **Bundled programme requirements** — ECTS quotas per programme/category are not exposed by vvzapi. We extract them from the official ETH Studienreglement PDFs (Rechtssammlung) and ship them as a structured `programmes_requirements.json` inside the skill. Independently verified row-by-row against the PDFs (see `eth_program_requirements_verified.md`).

## Audience

Paid claude.ai users (Pro / Max / Team / Enterprise) at ETH Zurich. Free claude.ai does not support custom Agent Skills. The skill is distributed as a `.zip` via GitHub releases and installed manually under Settings → Features.

## Status

Early prototype. Not affiliated with ETH Zurich, and not affiliated with the upstream vvzapi project — we credit it and aim to be a polite client. Verify anything binding (registration, grading, credit transfer) against the official catalogue at `vvz.ethz.ch`.
