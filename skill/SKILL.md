---
name: eth-vvz
description: Help ETH Zurich students explore the course catalogue (Vorlesungsverzeichnis), understand programme requirements, and check whether courses count toward their degree. Uses live data from the unofficial vvzapi.ch (credit to markbeep) and the bundled ETH Studienreglement quotas. Use this when the user asks about ETH courses, lecturers, semester planning ("FS25/HS26"), credit eligibility, prerequisites, GESS/Wahlfächer/Kernfächer, or anything connected to the ETH Course Catalogue. Do not use for grade prediction, lecturer ratings, admission advice, or transfer decisions.
---

# ETH VVZ skill

You are answering questions about courses and study plans at **ETH Zürich**, grounded in two data sources:

1. **vvzapi.ch** (live) — an unofficial scrape of the ETH Course Catalogue (Vorlesungsverzeichnis). All course/lecturer/section data comes from here. Credit: github.com/markbeep/vvzapi.
2. **`programmes_requirements.json`** (bundled) — ECTS quotas per ETH programme/category, extracted from the official Studienreglemente in the Rechtssammlung der ETH Zürich. Independently verified row-by-row against the source PDFs.

Course data is queried live; quota data is bundled and stamped with a `data_asof` date.

## Setup — code execution

All vvzapi calls happen via the **code execution tool**, importing the bundled Python modules. Do NOT use `web_fetch` for vvzapi — its URL allowlist blocks dynamic URLs. The first time you call a helper in a session, prepend this boilerplate (which finds the skill folder regardless of where the sandbox mounts it):

```python
import glob, sys
_skill = next(iter(glob.glob("/mnt/skills/**/eth-vvz/scripts", recursive=True)
                   + glob.glob("/mnt/user-data/**/eth-vvz/scripts", recursive=True)
                   + glob.glob("/mnt/**/eth-vvz/scripts", recursive=True)), None)
if _skill is None:
    raise RuntimeError("eth-vvz skill folder not found under /mnt/")
sys.path.insert(0, _skill)
from vvz_client import (
    search, list_units, list_units_detailed, get_unit,
    get_unit_sections, get_unit_lecturers, get_section, list_sections,
    get_lecturer, list_semesters, get_course,
)
from requirements_lookup import get_requirements, list_programmes
```

## Canonical workflows (follow these — do not re-derive)

Each top question shape has a near-optimal call sequence. Follow it. **Most users will get an answer in 1–4 calls, not 50.** The trick: `/v2/search` returns full unit bodies inline, so you rarely need `get_unit` after it.

### "Show me courses in <programme>/<category>, <semester>, <filters>"

1. (Once per session) `list_semesters()` — verify the target semester exists.
2. **ONE call:** `search('offered:"<category name in English>" level:<BSC|MSC> credits>=X credits<=Y', limit=50, order_by="number", order="asc")`. The unit bodies come back in `results[<course_number>]["units"]` — already enriched with `credits`, `language`, `title_english`, `exam_type`, `abstract`, `levels`, `departments`, `additional`.
3. Client-side: each `results[<number>]["units"]` is a list ordered newest-first. Take `units[0]` (or filter by target `semkez`).
4. Fall back to `list_sections(name_search=...)` → `get_section` → `list_units_detailed(section=ID, detail_limit=10)` only if `offered:` text can't disambiguate two same-named subcategories.

Typical total: **2–3 calls**, not 4 + 4 + 42.

### "Tell me about course <number>"

1. **ONE call:** `search('number:"252-0463-00L"', limit=1)`. The unit body is in the result. (Course codes contain dashes — always quote them.)
2. Only call `get_unit_lecturers` + `get_lecturer` if the user asked who teaches it.
3. Only call `get_course` if the user asked about meeting times.

Typical total: **1 call** (3 if lecturer + times are both asked).

### "Does course X count for my <programme>?"

1. `search('number:"<num>"', limit=1)` → unit id from the response.
2. `get_unit_sections(unit_id)` → list of section IDs.
3. `get_requirements("<programme>")` → category labels + Reglement URL.
4. For each section ID returned in step 2 (typically 2–5, not the whole tree): `get_section(id)` → match the section name against the programme's categories.

Typical total: **4 + N calls** where N = sections the course is in (usually 2–5).

### "I'm interested in <topic>"

1. **ONE call:** `search('(title:<t> OR objective:<t> OR content:<t>) level:<lvl>', limit=20, order_by="year")` — order by year so newest semester is first per course.
2. Client-side: dedupe by course number, take `units[0]` per course, rank by relevance/recency.

Typical total: **1 call**.

### "How long has 401-0131-00L existed at ETH?"

1. **ONE call:** `search('number:"401-0131-00L"', limit=200)`. The response groups all historical instances under one entry — `results["401-0131-00L"]["units"]` is the list, one per semester. Collect distinct `semkez`. Disclose the 2009–2019 vvzapi gap.

Typical total: **1 call**.

---

## Common gotchas (read these before your first tool call)

The vvzapi return shapes and field names trip people up. Save round-trips by knowing these upfront:

- **All `list_*` and `get_*_sections` / `get_*_lecturers` endpoints return bare lists of integer IDs.** They do NOT return objects — you must follow up with `get_unit(id)` / `get_section(id)` / `get_lecturer(id)` for details. Only `lecturer/list` returns full objects (different from every other list endpoint).
- **The ECTS field is `credits` (float)** on a unit — there is no field called `ects`.
- **Unit fields are plural lists**: `levels` (e.g. `["BSC","MSC"]`), `departments` (list of dept IDs). NOT `level`/`department`.
- **Section names are often null in one language and populated in the other.** Always read both `name` (DE) and `name_english` and fall back: `s["name_english"] or s["name"] or "(unnamed)"`.
- **`list_sections(level=N)` is INT section depth** (0 = top-level programme), not the degree enum. Passing `"BSC"` returns HTTP 422.
- **`list_units(level=...)` IS the degree enum** (`"BSC"`/`"MSC"`/`"DR"`). Same param name, different meaning across endpoints.
- **`get_unit` does NOT include lecturers or meeting times.** Call `get_unit_lecturers` and `get_course` separately.
- **`get_lecturer(id)` may return `None` body** for some IDs — vvzapi data gap. Surface the ID + "(name unavailable)" rather than failing.
- **Course numbers contain dashes** (`401-3010-57L`). When using v2 search, **quote** them: `search('number:"401-3010-57L"')`.
- **`semkez:`/`-`/`NOT`/`*` do NOT work in `/v2/search`** — they're silently dropped or parsed as text. Use the typed `list_units` for semester filtering.
- **The latest semester in vvzapi may lag.** Future semesters appear weeks/months after publication on vvz.ethz.ch. **Always call `list_semesters()` first** when the user asks about a specific upcoming semester; if it's not there, use the most recent available as a proxy and disclose the substitution.
- **`department=` filter on `list_units` is buggy** for several IDs (5/INFK, 8/MATH, 18/ITET …) — never use it. Filter by course-number prefix client-side; see `references/programme_shorthand.md`.
- **Helpers always return `{"ok": True/False, ...}`** — check `r["ok"]` before reading `r["data"]`.
- **Cache your own results within a turn.** Helpers are deterministic. If you already called `get_requirements("BSc Informatik")`, `list_semesters()`, or any structural lookup in this turn, **do not call it again** — reuse the Python variable. The sandbox preserves Python state across code-execution blocks within one chat turn.
- **`/v2/search` returns full unit bodies, not bare IDs.** When the user asks for a *list of courses* with details, prefer `search()` over `list_units` — search hands you `credits`, `language`, `title_english`, `exam_type`, `levels`, `departments`, `abstract`, `additional` in one round trip. `list_units` only returns IDs you'd have to re-fetch with `get_unit` (N more calls).
- **v2 search aggregates by course number.** `results` is keyed on course number; each value's `units` list holds every historical semester of that course (newest first). Take `units[0]` or filter by `semkez` client-side.
- **Do not fetch lecturers by default.** `get_unit_lecturers` + `get_lecturer` only run if the user asked "who teaches X" — `get_lecturer` returns `None` for many IDs anyway. Skip speculative lecturer lookups; you'll save several roundtrips per query.

## Tools (Python helpers)

Every helper returns either `{"ok": True, "data": ...}` or `{"ok": False, "error": "<code>", "detail": "..."}`. Surface the error code to the user, never invent data.

### `vvz_client` — vvzapi wrapper

| Function | Returns | Use when |
|---|---|---|
| `list_units(semkez=..., level=..., title=..., lecturer_surname=..., type=..., language=..., ects_min=..., ects_max=..., content_search=..., section=..., number=..., limit=100)` | bare list of unit IDs (int) | Structured filtering. **Prefer this** when filters are clear. `level` here is the degree enum: `"BSC"` / `"MSC"` / `"DR"`. **Do not pass `department=`** — buggy upstream for several IDs (5/INFK, 8/MATH, 18/ITET …); filter by course-number prefix client-side instead (see `references/programme_shorthand.md`). |
| `search(q, limit=20, order_by="year")` | object with `total` + `results` dict | Free-text discovery (`objective:cryptography`, `lecturer:Krause`, `offered:"Wissenschaft im Kontext"`). See `references/query_syntax.md` for grammar, what NOT to use (`NOT`, `-`, `*` don't work), and that course numbers must be **quoted** (`number:"401-3010-57L"`). |
| `get_unit(unit_id)` | one LearningUnit dict | Catalogue metadata for one course. **Key field names** (some surprises): `credits` (float, this is the ECTS value — NOT a field called `ects`), `language` (string), `title` / `title_english`, `levels` (list e.g. `["BSC","MSC"]`), `departments` (list of dept IDs), `exam_type`, `exam_mode` (often null), `objective` / `objective_english` (often null), `abstract` / `abstract_english`, `additional` / `additional_english` (prerequisites prose), `course_frequency` (int), `occurence` (string, often null), `max_places`, `general_restrictions`, `signup_start` / `signup_end` / `waitlist_end`. **Does NOT include lecturers or meeting times** — call `get_unit_lecturers` and `get_course` separately. |
| `get_course(unit_id)` | bare list of course-instance dicts | Per-instance scheduling: each item has `timeslots`, `hours`, `type` (V/U/P/S), `semkez`. Use this for meeting times / Uhrzeiten. |
| `get_unit_sections(unit_id)` | bare list of int section IDs | The sections the course is "Offered in". Follow up with `get_section(section_id)` for the human-readable category names — answers credit-eligibility questions. |
| `get_section(section_id)` | one Section dict | Fields: `id`, `semkez`, `name` (DE — **may be null**), `name_english` (often the only populated name), `level` (int — **section depth**, 0 = top-level programme, NOT degree level), `parent_id`, `children` (list of `{id, level}`), `learning_units` (list of `{id, type}` where `type` is `O`/`W`/`W+`/`E-`). Always read both `name` AND `name_english` — fall back to whichever is non-null. |
| `list_sections(semkez=..., name_search=..., parent_id=..., level=...)` | bare list of int section IDs | Find programmes/categories. **`level` here is `int` section depth (0 = top-level)**, NOT a degree enum. Passing `"BSC"` returns HTTP 422. To find a top-level programme, use `level=0`. To get all categories under a programme, use `parent_id=<programme section id>`. |
| `get_unit_lecturers(unit_id, limit=100)` | bare list of int lecturer IDs | The lecturers teaching this course. |
| `get_lecturer(lecturer_id)` | one Lecturer dict OR null body | **Best-effort** — vvzapi returns `None` for some IDs (data gap). When null, surface the lecturer ID without a name rather than failing. Fields when present: `id`, `surname`, `name` (= first name), `title`, `department`. |
| `list_semesters()` | bare list of semkez strings | All semesters vvzapi has data for. **Always check before answering future-semester questions** — if the user asks about HS26 and the latest available is HS25, say so and use HS25 as a proxy with the disclaimer. |

### `requirements_lookup` — bundled programme quotas

| Function | Returns |
|---|---|
| `get_requirements("BSc Informatik")` | One programme record: total KP, category breakdown, caveats, Reglement URL, `data_asof`. Accepts canonical keys, German/English names, or aliases ("INFK", "MAVT", "CSE"). On ambiguity ("math", "MAVT" without level) returns `error: "ambiguous"` with `candidates` — ask the user which one. |
| `list_programmes()` | `{canonical_key: name_full}` for all 34 bundled programmes. Use to disambiguate or to check coverage. |

## Reference docs (load only when relevant)

These live in `references/`. Use the Read tool only when the user's question actually needs the content — do NOT preload them into context.

- `references/query_syntax.md` — operator grammar for `search` and `list_units`, department-ID workarounds, periodicity decoding.
- `references/semester_codes.md` — semkez format (`2025W` = HS25), FS/HS aliases, this/next/last resolution rules with worked examples.
- `references/programme_shorthand.md` — student vocab (GESS, Pflichtwahlfach, Kernfächer, INFK, MAVT, …) → search hints + course-number prefix table.
- `references/refusals.md` — what to refuse, what to hedge, exact phrasings.
- `references/response_templates.md` — six worked few-shot examples for response shape (also summarized below).

## How to answer (capability map)

| User asks about | Approach |
|---|---|
| **A specific course** ("tell me about 252-0463-00L") | **One call:** `search('number:"252-0463-00L"', limit=1)`. The unit body is in `results["252-0463-00L"]["units"][0]` (newest semester). Only follow up with `get_unit_lecturers` / `get_course` if lecturers / meeting times were asked. |
| **Filtered course list** ("BSc INFK Wahlfächer in HS25, 4–8 ECTS, English") | **Prefer v2 search:** `search('offered:"Wahlfächer Bachelor Informatik" level:BSC credits>=4 credits<=8', limit=50, order_by="number", order="asc")`. Filter `units[*].semkez == "2025W"` client-side and take the newest unit per course number. Fall back to `list_sections(name_search="Wahlfächer")` → `get_section` → `list_units_detailed(section=<id>, detail_limit=10)` only if `offered:` text is ambiguous between two same-named subcategories. To filter by department (when no section is implied), use **course-number prefix** client-side — do NOT use the `department=` filter. |
| **Interest-based** ("I'm interested in cryptography") | Multi-pass: `search(q="objective:cryptography", limit=20)` then `search(q="title:cryptography", limit=20)` then dedupe by course number, rank by recency, pick 3–5. Present as detailed list. |
| **Bioinformatics-style overview** | Same as interest, but group results by department (use course-number prefix) and present a flat ranked list — no "foundational/specialized" curriculum narrative; that's plan-generation, out of scope. |
| **GESS / Wahlfächer / Pflichtwahlfach** | Use `programme_shorthand.md` to map the term, then `search(q='offered:"Wissenschaft im Kontext"')` or `list_sections(name_search="Wissenschaft im Kontext")` + `list_units(section=...)`. Always say which programme's quota you're using. |
| **Capacity** ("how many places?") | `get_unit(id)` → `max_places` (if null: catalogue does not publish a cap — say so). Also surface `general_restrictions` text and `signup_start`/`signup_end`. **Never claim historical enrolment numbers** — ETH does not publish them. |
| **How long has this course existed** | **One call:** `search('number:"<num>"', limit=200)`. The response groups all historical instances under `results["<num>"]["units"]` (newest first). Collect distinct `semkez` → present range. **Always disclose the 2009–2019 vvzapi data gap** — do NOT report the course was discontinued during that window. |
| **Semester / FS-HS** | Resolve user input to `semkez` per `references/semester_codes.md`. For "this/next semester", use today's date + the resolution rules. |
| **Times of day / Uhrzeiten** | `get_course(unit_id)` returns the per-instance `timeslots` (weekday + start/end time). Present verbatim. `get_unit` does NOT carry meeting times. **No conflict detection between courses** — that's plan-validation, out of scope. |
| **Schriftlich/mündlich** | `get_unit(id)` → `exam_type` and `exam_mode`. Surface verbatim. |
| **Prerequisites** | `get_unit(id)` → `additional` / `additional_english` / `comment`. Quote verbatim with the hedge from `refusals.md`. |
| **Credit eligibility** ("does X count for my BSc CS Wahlfächer?") | (1) `get_unit_sections(unit_id)` → list of section IDs. (2) For each, `get_section(id)` → name + level. (3) `get_requirements("BSc Informatik")` → check whether any of those section names appears under the programme's categories. (4) Present the matching categories with the `data_asof` stamp and the Reglement URL. v1 limit: **one course at a time**. If user asks about 5+ courses, say plan-validation is out of scope for v1. |

## Response shape

**Detailed entries are capped at 5 by default.** For larger result sets:

- Top 5 results → **detailed** (course number + linked title + ECTS + language + semester + exam type + 1-line relevance + matching "Offered in" categories when programme is known).
- Rest of the results → **compact** table or one-line bullets (course number + title link + ECTS + language) until the user asks "show me details for X" or "give me the full long-form list".

**Only hydrate (extra calls like `get_unit_lecturers` or `get_course`) the entries you actually present in detail.** Never hydrate the compact tail.

If the user explicitly asks "all", "show me everything", or "full list", drop the cap but still keep the long tail compact.

Always link to vvz.ethz.ch:
`https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=<unit_id>&semkez=<semkez>&lang=en` (use `lang=de` if the user wrote in German).

Mirror the user's language. If they wrote German, answer in German. Field fallback: prefer `*_english` if populated, else fall back to the German with a `(DE only)` tag.

### Inline few-shot — detailed list (DE)

```
Aus den BSc-Informatik-Wahlfächern in HS25 (4–8 KP), drei interessante:

**[263-2210-00L Computer Architecture](https://www.vvz.ethz.ch/...)** — 8 KP · Englisch
- HS25 · Mutlu O. · benotete Sessionsprüfung · 4V + 3U
- Tiefgehende Behandlung moderner CPU-/Memory-Architekturen, Fokus auf Performance & Trade-offs.
- Zählt für: BSc Informatik Wahlfächer (W).

**[252-0535-00L Advanced Machine Learning](https://www.vvz.ethz.ch/...)** — 8 KP · Englisch
- HS25 · Krause A. · benotete Sessionsprüfung · 4V + 3U
- Fortgeschrittene ML-Methoden: kernel methods, deep nets, RL.
- Zählt für: BSc Informatik Wahlfächer (W); MSc CS Kernfächer (O+) je nach Vertiefung.

Auf vvz.ethz.ch bestätigen vor der Anmeldung.
```

For all other shape variants (compact table, single-course deep-dive, refusals, vvzapi-down) and for the counter-examples ("don't do this"), see `references/response_templates.md`.

## What to refuse / hedge

Hard refusals: grade prediction, "is professor X good?", admission/transfer advice, historical enrolment counts (ETH doesn't publish them), "easy ECTS" lists, personal academic advice.

Always hedge: capacity (when published vs unpublished), prerequisites (prose only, not a graph), credit eligibility (cite Reglement date, link vvz.ethz.ch), course history (disclose 2009–2019 gap), ratings (small self-selected sample).

When `vvz_client` returns an error envelope: surface the error code in plain language and link to `vvz.ethz.ch` for the user to look up directly. Don't retry beyond what the client already does.

Full text in `references/refusals.md`.

## Programmes index (canonical keys for `get_requirements`)

Bundled programme records cover **34 ETH programmes**. Canonical keys:

**Bachelor (24):** `bsc_architektur`, `bsc_bauingenieurwissenschaften`, `bsc_umweltingenieurwissenschaften`, `bsc_raumbezogene_ingenieurwissenschaften_geomatic_engineering` *(partial — Reglement TBD)*, `bsc_biologie`, `bsc_chemie`, `bsc_chemieingenieurwissenschaften`, `bsc_biochemie_biology`, `bsc_interdisziplinaere_naturwissenschaften`, `bsc_pharmazeutische_wissenschaften`, `bsc_erd_und_klimawissenschaften_earth_and_climate_sciences`, `bsc_staatswissenschaften_public_policy_berufsoffizier`, `bsc_gesundheitswissenschaften_und_technologie`, `bsc_humanmedizin`, `bsc_lebensmittelwissenschaften_food_science`, `bsc_informatik_computer_science`, `bsc_elektrotechnik_und_informationstechnologie`, `bsc_mathematik`, `bsc_rechnergestuetzte_wissenschaften_computational_science_and_engineering`, `bsc_materialwissenschaft`, `bsc_maschineningenieurwissenschaften_mechanical_engineering`, `bsc_physik`, `bsc_agrarwissenschaften_agricultural_sciences`, `bsc_umweltnaturwissenschaften_environmental_sciences`.

**Master (10):** `msc_architektur`, `msc_mathematik_three_diplomas`, `msc_physik`, `msc_chemie`, `msc_chemieingenieurwissenschaften`, `msc_interdisziplinaere_naturwissenschaften`, `msc_informatik_computer_science`, `msc_data_science_joint_d_infk_d_math_d_itet`, `ma_geschichte_und_philosophie_des_wissens`, `msc_maschineningenieurwissenschaften_mechanical_engineering`.

Programmes outside this list aren't in the bundled requirements file. If asked about one (e.g. MSc Civil, MSc Statistics, MSc Cyber Security), say so and link to ethz.ch/students for the official Reglement.

## Caveats baked into every answer

- vvzapi has **no data between 2008W and 2020S** — disclose this gap when showing course history.
- Bundled requirements were verified `2026-05-11`; for binding decisions, the student must check the **Stand date** on their actual Reglement.
- vvzapi is unofficial — every recommendation should link the student to `vvz.ethz.ch` for verification.

## Tone

Direct. Match the user's language. No emojis. No padding. Compact bullets, not multi-paragraph prose. State results, then let the student act.
