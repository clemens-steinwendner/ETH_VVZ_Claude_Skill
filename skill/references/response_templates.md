# Response shape & few-shot examples

The skill is opinionated about how it presents course information. Default to the
**detailed** shape; use **compact** only when the user explicitly asks ("just
list them", "in a table", "in einer Zeile pro Kurs"). Always link to vvz.ethz.ch.

---

## Field set

### Always present (every course in every list)

- **Course number** linked to vvz.ethz.ch — see linking rule below.
- **Title** (English if populated, else German with `(DE only)` tag).
- **ECTS** as an integer or `0.5` step.
- **Language** of instruction.

### Default (detailed) — adds:

- **Semester** (`HS25`, `FS26` — student-facing, not `2025W`).
- **Lecturer** (surname + first initial).
- **Exam type** (one short phrase, e.g. "graded session", "ungraded semester perf.", "oral").
- **Relevance** — one sentence grounded in the abstract / objective explaining why this fits the user's question.
- **Counts toward** — matching "Offered in" categories from the user's programme, when known.

### On explicit request only

- Abstract excerpt (~3 sentences max, never the whole thing).
- Prerequisites (verbatim from the catalogue text — do not paraphrase).
- vvzapi rating (with the hedge from `refusals.md`).

### Linking rule

`https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=<unit_id>&semkez=<semkez>&lang=en`

Use the **English** lang param by default (`lang=en`); switch to `lang=de` if the
user wrote in German. The unit_id and semkez come from the vvzapi response.

---

## Few-shot examples

The model should emulate these shapes literally — markdown formatting, line
breaks, ordering, and tone.

### Example 1 — Detailed (default), single recommendation, English query

User: *"I want to take a graph theory course in HS25, what's good?"*

```
Here are two options offered in HS25:

**[252-1407-00L Discrete Mathematics](https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=...&semkez=2025W&lang=en)** — 7 ECTS · English
- HS25 · Steurer A. · graded session exam · 4V + 2U
- Foundational graph theory including spectral methods, expanders, random graphs.
- Counts toward: BSc CS Wahlfächer (W), MSc CS Wahlfächer (W).

**[401-3052-10L Graph Theory](https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=...&semkez=2025W&lang=en)** — 6 ECTS · English
- HS25 · Sudakov B. · graded session exam · 3V + 1U
- Pure mathematics treatment: matchings, colorings, extremal and probabilistic methods.
- Counts toward: BSc Math Wahlfächer (W), MSc Math Pure Math (W+).

Verify both on vvz.ethz.ch before registering.
```

### Example 2 — Detailed, German query

User: *"Welche guten Wahlfächer gibts für BSc Informatik in HS25 mit 4–8 ECTS?"*

```
Aus den BSc-Informatik-Wahlfächern in HS25 (4–8 KP), drei interessante:

**[263-2210-00L Computer Architecture](https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=...&semkez=2025W&lang=de)** — 8 KP · Englisch
- HS25 · Mutlu O. · benotete Sessionsprüfung · 4V + 3U
- Tiefgehende Behandlung moderner CPU-/Memory-Architekturen, mit Fokus auf Performance & Trade-offs.
- Zählt für: BSc Informatik Wahlfächer (W).

**[252-0535-00L Advanced Machine Learning](https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=...&semkez=2025W&lang=de)** — 8 KP · Englisch
- HS25 · Krause A. · benotete Sessionsprüfung · 4V + 3U
- Fortgeschrittene ML-Methoden: kernel methods, deep nets, reinforcement learning.
- Zählt für: BSc Informatik Wahlfächer (W), MSc CS Kernfächer (O+) je nach Vertiefung.

**[252-0463-00L Security Engineering](https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=...&semkez=2025W&lang=de)** — 7 KP · Englisch
- HS25 · Basin D. · benotete Sessionsprüfung · 4V + 2U
- System-/Netzwerksicherheit, Bedrohungsmodellierung, Krypto-Protokolle in der Praxis.
- Zählt für: BSc Informatik Wahlfächer (W).

Auf vvz.ethz.ch bestätigen vor der Anmeldung.
```

### Example 3 — Compact, when user asks for a list

User: *"Just list me all D-MATH courses with ≤4 ECTS in FS26."*

```
| # | Course | ECTS | Lang |
|---|---|---|---|
| 1 | [401-2334-00L Methods of Mathematical Physics II](https://...) | 4 | EN |
| 2 | [401-3531-00L Differential Geometry I](https://...) | 4 | EN |
| 3 | [401-3225-00L Representation Theory of Lie Groups](https://...) | 4 | EN |
| ... | | | |

(N total — verify on vvz.ethz.ch)
```

### Example 4 — Single course deep-dive (when user names one course)

User: *"Tell me about 252-0463-00L."*

```
**[252-0463-00L Security Engineering](https://...)** — 7 ECTS · English

- **Semester:** HS25 (annual)
- **Lecturer:** Basin D., Cremers C.
- **Format:** 4V + 2U + 1A · graded session examination (written, 120 min)
- **Capacity:** no published cap
- **Prerequisites:** *(verbatim)* "Computer Networks (252-0407-00L) and Information Security (252-0211-00L) recommended."
- **History in vvzapi:** offered HS20 – HS25 every year. (Note: vvzapi has no data 2009–2019; the course may be older.)

**Counts toward**
- BSc Informatik – Wahlfächer (W)
- MSc Cyber Security – Kernfächer (O)

**Abstract** (excerpt):
> The course covers principles and techniques to design, build, and analyze secure
> systems. Topics include threat modeling, authentication, access control, network
> security, and applied cryptography...

Verify the latest version on vvz.ethz.ch.
```

### Example 5 — Refusal with redirect

User: *"Is Prof. Krause a good lecturer?"*

```
I don't have a way to evaluate teaching quality — vvzapi has user ratings but
they're a small self-selected sample, not an official metric.

For first-hand impressions, try the ETH student forums (e.g. the ETH subreddit,
VSETH course evaluations on https://n.ethz.ch/~vseth/) and ask peers in your
programme.
```

### Example 6 — vvzapi unreachable

User: *"What's the ECTS for 252-0463-00L?"*  (with helper returning `vvzapi_unreachable`)

```
I couldn't reach the course catalogue API just now (vvzapi unreachable). Please
try again in a moment, or look it up directly:
https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitscode=252-0463-00L&lang=en
```

---

## Counter-examples (don't do this)

- ❌ Don't use checkmark / star emojis for "good fit". Just say it.
- ❌ Don't write multi-paragraph abstract dumps unless asked.
- ❌ Don't bullet-list every field with prefixes ("Title: ...", "ECTS: ..."); use the compact bold-link style above.
- ❌ Don't speculate on lecturer quality, exam difficulty, workload, or grading distribution beyond what's literally in the catalogue.
- ❌ Don't promise that any course "definitely" satisfies a category — always say "counts toward, per the bundled Reglement [date]; verify on vvz.ethz.ch".
- ❌ Don't say "Offered in: 47 sections" when the user wants to know which match *their* programme. Filter to the programme they've stated; if unknown, ask first.
