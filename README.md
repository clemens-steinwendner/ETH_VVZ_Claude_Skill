# ETH VVZ Claude Skill

A Claude skill that lets students chat about ETH Zurich courses and study plans, grounded in factual data from the unofficial [vvzapi](https://github.com/markbeep/vvzapi) (`https://vvzapi.ch`).

## What it does

- Look up courses by title, lecturer, semester, ECTS, language, level, department.
- Answer credit-eligibility questions ("does this count toward BSc MAVT Kernfächer?") using the `Offered in` data exposed by vvzapi's `/unit/{id}/sections` + `/section/{id}/get` endpoints (including the `O` / `W` / `E-` category type).
- Help build and sanity-check personal study plans against a per-programme requirements file the user supplies.

## Data sources

- **vvzapi** (`https://vvzapi.ch`) — unofficial scrape of the ETH Course Catalogue. Used for: learning units, course instances, lecturers, ratings, and the "Offered in" section/category mapping.
- **Studienreglement (user-supplied)** — ECTS quotas per category, prerequisites, and Leistungskontrolle rules are *not* in vvzapi and must come from the official programme regulation.

## Status

Early prototype. Not affiliated with ETH Zurich. Verify anything binding (registration, grading, credit transfer) against the official catalogue at `vvz.ethz.ch`.
