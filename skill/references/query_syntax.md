# vvzapi query syntax — cheatsheet

vvzapi exposes two query interfaces. **Prefer the typed v1 interface for structured
filters; use v2 free-text search for keyword discovery.**

---

## Typed: `GET /api/v1/unit/list`

Best for "show me courses matching these structured filters". All params optional.

| Param | Type | Example | Notes |
|---|---|---|---|
| `semkez` | string | `2026S`, `2025W` | Exactly one semester. **Always set this.** |
| `level` | enum | `BSC`, `MSC`, `DR` | Degree level. |
| `department` | int | `5` (Informatik), `8` (Mathematik) | See department table below. |
| `section` | int | `120203` | Section ID (programme/category). |
| `number` | string | `401-3010-57L` | Course number. |
| `title` | string | `Analysis` | Substring match against DE OR EN title. |
| `lecturer_id` | int | | |
| `lecturer_name` | string | `Andreas` | First name. |
| `lecturer_surname` | string | `Krause` | Surname. |
| `type` | string | `O`, `W`, `W+`, `E-`, `Z`, `Dr` | Compulsory / Wahlfach / etc. |
| `language` | string | `English`, `German` | Language of instruction. |
| `periodicity` | int | `0`=once, `1`=annual, `2`=every semester, `3`=biennial | Request param. **Note:** the corresponding *response* field on a unit is `course_frequency` (int) and/or `occurence` (string, often null) — *not* `periodicity`. |
| `ects_min` | float | `4` | Minimum ECTS. |
| `ects_max` | float | `8` | Maximum ECTS. |
| `content_search` | string | `cryptography` | Searches catalogue data (abstract / objective). |
| `limit` | int | up to `1000` | |
| `offset` | int | | |

### Department IDs

These IDs come from vvzapi's internal database (sourced from the openapi spec
at `https://vvzapi.ch/openapi.json`). They could in principle be renumbered
in a future vvzapi release — re-verify the table against the spec when
republishing the skill.

| ID | Department |
|---|---|
| 1 | D-ARCH (Architecture) |
| 2 | D-BAUG (Civil, Environmental & Geomatic Engineering) |
| 3 | D-MAVT (Mechanical & Process Engineering) |
| 5 | D-INFK (Computer Science) |
| 7 | D-MTEC (Management, Technology & Economics) |
| 8 | D-MATH (Mathematics) |
| 9 | D-PHYS (Physics) |
| 11 | D-BIOL (Biology) |
| 13 | D-ERDW (Earth & Planetary Sciences) |
| 17 | D-GESS (Humanities, Social & Political Sciences) |
| 18 | D-ITET (Information Technology & Electrical Engineering) |
| 19 | D-MATL (Materials) |
| 20 | D-CHAB (Chemistry & Applied Biosciences) |
| 23 | D-BSSE (Biosystems Science & Engineering) |
| 24 | D-HEST (Health Sciences & Technology) |
| 25 | D-USYS (Environmental Systems Science) |

### ⚠️ `department` filter is buggy in vvzapi

Empirically, the `department=N` query parameter does **not** reliably filter to units
of department N for at least these values: 1 (D-ARCH), 5 (D-INFK), 8 (D-MATH),
9 (D-PHYS), 13 (D-ERDW), 18 (D-ITET). Results are often a wrong department, or a
broad mixture. The filter only accepts the 16 spec'd values (everything else
returns HTTP 400), but the *semantics* are wrong for several of them.

**Workarounds** (in order of preference):

1. Filter by **course-number prefix** client-side:
   `252-` → D-INFK, `401-` → D-MATH, `227-` → D-ITET, `151-` → D-MAVT,
   `101-`/`102-`/`103-` → D-BAUG, `701-`/`751-`/`102-` → D-USYS / D-ERDW, etc.
2. Use the v2 search field `offered:"Departement Informatik"` (or similar
   department-name patterns from `programme_shorthand.md`).
3. Fetch the section tree for the department and use `list_units(section=...)`.

### Unit type codes

| Code | Meaning |
|---|---|
| `O` | Obligatorisch / compulsory |
| `W+` | Wahlpflichtfach / restricted elective (must take from this set) |
| `W` | Wahlfach / elective |
| `E-` | Wahlfach Erweiterung (recommended elective) |
| `Z` | Zusatzfach / additional |
| `Dr` | Doktoratsfach |

### Periodicity codes (decoded)

| Code | Decoded human string |
|---|---|
| `0` | One-time (single offering, may not repeat) |
| `1` | Annual (every year, in the same semester) |
| `2` | Every semester |
| `3` | Biennial (every two years) |

---

## Section endpoints: `GET /api/v1/section/list` and `/api/v1/section/{id}/get`

Sections are the "Offered in" hierarchy — programmes (top-level) and the
categories beneath them (Kernfächer, Wahlfächer, etc.).

| Param on `section/list` | Type | Notes |
|---|---|---|
| `semkez` | string | `2025W` etc. **Always set** to avoid history bleed-through. |
| `level` | int | **Section depth**, NOT a degree enum. `0` = top-level programme; `1`, `2`, `3` = nested categories. Passing `"BSC"` returns HTTP 422. |
| `parent_id` | int | Direct parent only (1 level deep). |
| `name_search` | string | Substring match against `name` and `name_english`. |
| `comment_search` | string | Substring match against `comment`. |
| `sort_lex` | bool | `true` = alphabetical; default `false` = sort by section ID. |

`section/list` returns a **bare list of integer IDs** — call
`section/{id}/get` for each one to read names, parents, children.

A `Section` response has: `id`, `parent_id`, `semkez`, `name` (DE — **may be null**),
`name_english` (often the only populated label — **always fall back**), `level`
(int depth), `children` (list of `{id, level}`), `learning_units`
(list of `{id, type}` where `type` ∈ `O`/`W`/`W+`/`E-`).

Section IDs are per-semester — the same programme has a different ID each
semester. To follow a programme across years, search by name.

## Free-text: `GET /api/v2/search`

Best for "I'm interested in <topic>" → keyword discovery across multiple fields.

### Working operators

- **Field:value** — `title:cryptography`, `objective:bioinformatics`, `lecturer:Krause`
- **Implicit AND** between space-separated tokens — `title:linear lecturer:Halbeisen`
- **Explicit `AND` / `OR`** — `title:cryptography OR title:security`
- **Parentheses for grouping** — `(title:crypto OR title:security) credits>=4`
- **Numeric comparisons** — `credits=6`, `credits>3`, `credits<8`, `credits>=4 credits<=8`
- **Quoted phrases** — `title:"linear algebra"` matches the exact phrase

### Searchable fields (v2)

- `title` — title (DE or EN substring)
- `objective` — learning objective text
- `content` — content/catalogue body
- `abstract` — abstract text (German abstract field)
- `lecturer` — lecturer name (free-text)
- `number` — course number
- `credits` — ECTS (numeric)
- `language` — language of instruction
- `examtype` — exam type description
- `offered` — programme/section name where course is offered (substring match)
- `level` — `BSC`, `MSC`, `DR`

### Result shape (v2)

The response is a dict:

```
{
  "total": <int>,
  "parsed_query": "<echo of what the parser interpreted>",
  "results": {
    "<course_number>": {
      "number": "<course_number>",
      "units": [
        {<full LearningUnit dict for newest semester>},
        {<full LearningUnit dict for an earlier semester>},
        ...
      ]
    },
    ...
  }
}
```

**Key fact:** v2 search aggregates **by course number**. Each entry's `units`
list contains every historical occurrence of that course, **newest first**.
So to filter by a specific semester, take `units[0]` (or any `u for u in units
if u["semkez"] == target`). The full LearningUnit body is inline — no
`get_unit` follow-up needed.

This makes `search()` strictly more efficient than `list_units` + N×`get_unit`
whenever the filters can be expressed in the search grammar.

### Ordering

- `order_by` ∈ `{title, title_german, title_english, number, credits, year, semester, lecturer, descriptions, level, department, language, offered, examtype, coursereview}`
- `order` ∈ `{asc, desc}` (default `desc`)
- Use `order_by=coursereview` to rank by user ratings.

### Limitations of v2 search — **do not use these:**

- ❌ `NOT title:...` — parsed as literal text token `'NOT'`, returns nothing useful.
- ❌ `-field:value` — silently dropped.
- ❌ `title:crypto*` — wildcards not supported.
- ❌ `semkez:` filter inside the `q=` query — **silently dropped** in v2 search. Use `/v1/unit/list` for semester filtering, or filter results client-side.
- ⚠️ Course numbers contain dashes (`401-3010-57L`). The Scryfall-style parser
  splits on dashes unless you **quote** the value. Always write
  `number:"401-3010-57L"` (with double quotes), not `number:401-3010-57L`.

---

## When to use which

| Goal | Endpoint |
|---|---|
| "All MSc Informatik courses in HS25 with 4–8 ECTS" | `/v1/unit/list?level=MSC&department=5&semkez=2025W&ects_min=4&ects_max=8` |
| "Courses about cryptography" | `/v2/search?q=objective:cryptography OR title:cryptography` |
| "Courses by Wattenhofer" | `/v1/unit/list?lecturer_surname=Wattenhofer` (then filter by `semkez` client-side) |
| "Find courses offered in 'Wahlfächer Bachelor Informatik'" | `/v2/search?q=offered:"Wahlfächer Bachelor Informatik"` |
| "How long has 401-0131-00L existed" | `/v2/search?q=number:401-0131-00L&limit=200` then collect distinct `semkez` |
| "Look up one specific course in detail" | `/v1/unit/{unit_id}/get` |
| "What programmes does course X count for" | `/v1/unit/{unit_id}/sections` then `/v1/section/{id}/get` for each |

## Known data gap

**No vvzapi data exists for semesters between 2008W and 2020S.** When showing course
history (`number:` searches across semesters), always disclose this gap. Do NOT
report "the course was discontinued from 2009–2019" — assume it continued.
