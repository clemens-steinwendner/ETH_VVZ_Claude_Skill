# Test cases — manual verification fixtures

Run these against the installed skill on claude.ai before each release. Not
automated — claude.ai skill testing currently requires copying queries into a
chat and reading the response. Asserting *structural* properties (presence of
fields, no refusal-violation) is the contract, not exact wording.

Mark each as: ✅ PASS · ⚠️ DEGRADED · ❌ FAIL · — N/A.

## Smoke (5 cases — must pass)

| # | Query | Must contain | Must NOT contain |
|---|---|---|---|
| S1 | "Tell me about course 252-0463-00L" | Course number, title with vvz.ethz.ch link, ECTS, language, exam type, lecturer name | grade prediction, "easy/hard" claims |
| S2 | "List MSc Informatik courses in HS25 with 4–8 ECTS" | At least 3 results, each with number + title link + ECTS + language; HS25 semester tag | non-INFK course numbers as the main result (filter must apply) |
| S3 | "Does 252-0463-00L count toward BSc Informatik Wahlfächer?" | Yes/no answer with cited section name, link to vvz.ethz.ch, data_asof or Reglement reference | invented programme/category names |
| S4 | "Force vvzapi to fail" *(disable network in claude.ai settings)* | "vvzapi unreachable" or similar error code; fallback link to vvz.ethz.ch | improvised course data |
| S5 | "Is Prof. Wattenhofer a good lecturer?" | Refusal + redirect to course evaluations / student forums | any qualitative judgment about teaching quality |

## Question-type regression (one per capability map row)

| # | Query | Capability tested | Must contain |
|---|---|---|---|
| Q1 | "Welche Vorlesungen gibts in FS26 vom Krause?" | semester + lecturer filter, German query | results from semkez=2026S, lecturer surname match, **German response** |
| Q2 | "Show me 401-0131-00L meeting times" | Uhrzeiten | weekly time slots (Mo/Di/Mi/Do/Fr + HH:MM); no "I'll check your calendar" |
| Q3 | "What are the prerequisites for 263-2400-00L?" | prerequisites | verbatim catalogue text + hedge ("not a verified graph, check with lecturer") |
| Q4 | "Which D-INFK courses have an oral exam this semester?" | exam_mode filter | results with `exam_mode=oral` or equivalent text; current semester resolved |
| Q5 | "I want to learn about quantum computing — what should I take?" | nach Interesse | 3-5 ranked recommendations using `objective:` + `title:` search; each linked |
| Q6 | "What courses are there for bioinformatics?" | für Überblick | flat ranked list grouped by department; **no** "foundational/specialized/project" framing |
| Q7 | "Which seminars are offered next semester?" | examtype filter | results with seminar exam_type; "next semester" resolved correctly |
| Q8 | "How many places does 252-5256-00L have?" | Capacity (capped course) | `max_places` value + restrictions text; hedge about real selection process |
| Q9 | "How many places does 401-0131-00L have?" | Capacity (uncapped) | explicit "no published cap" statement; no invented number |
| Q10 | "How long has 401-0131-00L existed at ETH?" | History | range of semesters + **explicit 2009–2019 gap disclosure** |
| Q11 | "Show me GESS courses I can take" | Cross-cutting category | uses `Wissenschaft im Kontext` / `Science in Perspective`; asks for programme if not given |
| Q12 | "How many GESS credits do I need for my BSc?" | Requirements lookup + cross-cut | asks for which BSc programme; uses `get_requirements`; cites SiP quota + data_asof |

## Refusal & hedge cases

| # | Query | Must contain |
|---|---|---|
| R1 | "Which lecturer gives the easiest grades in INFK?" | Refusal + redirect |
| R2 | "Will I get admitted to MSc Data Science if my GPA is 5.2?" | Refusal — admission decision out of scope |
| R3 | "How many students applied to AI Center last year?" | Refusal — ETH doesn't publish enrolment numbers |
| R4 | "Recommend 'easy ECTS' courses" | Refusal + redirect |
| R5 | "Which course has the smallest workload for 6 ECTS?" | Refusal — no objective workload data |

## DE/EN consistency

| # | Query (paired) | Must contain |
|---|---|---|
| D1a | "Welche Wahlfächer für BSc Informatik in HS25?" | German response, German category name, German hedge text |
| D1b | "What electives for BSc CS in HS25?" | English response, English category name, English hedge text — same underlying courses as D1a |

## Disambiguation

| # | Query | Must contain |
|---|---|---|
| A1 | "How many credits for MAVT?" | Clarification question ("Bachelor or Master?") — not a guess |
| A2 | "I have a question about math" | Clarification: BSc vs MSc; topic vs programme |
| A3 | "What about Wahlfächer?" *(no programme given)* | Clarification: which programme/level |

## Out-of-scope cases (graceful "not v1")

| # | Query | Must contain |
|---|---|---|
| O1 | "Plan my next 4 semesters" | "Plan generation is out of scope for v1" + offer to answer course-by-course |
| O2 | "Do these 8 courses satisfy my MSc INFK Kernfächer?" | "Bulk eligibility is out of scope; ask one course at a time" |
| O3 | "Schedule conflicts between courses A, B, C, D?" | "Weekly-grid conflict detection out of scope; here are the meeting times for each" |
| O4 | "What's the workload of 263-2400-00L?" | Refers to ECTS as the only workload signal; refuses subjective estimate |

## Network / runtime smoke

| # | Scenario | Must |
|---|---|---|
| N1 | First query in a fresh chat | Imports succeed, vvzapi reachable, response within ~30s |
| N2 | Repeated question (same chat) | `/tmp/vvz_cache` hit visible in code-exec output; faster than N1 |
| N3 | User has network access disabled | Skill produces a clear error: "vvzapi unreachable — please enable cross-domain network in claude.ai settings" |

## How to score a release

Block the release on any of:
- Any **smoke** case ❌
- Any **refusal** case ❌
- Any **disambiguation** case ❌ (asks the user instead of guessing wrong)
- More than **2 of 12** regression cases ❌

Ship if all smoke + refusal + disambiguation pass and regression ≥ 10/12.
