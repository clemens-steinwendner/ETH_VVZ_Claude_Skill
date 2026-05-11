# Refusals & hedges

What the skill must NOT do, and how to respond when asked. The point is to be
useful where vvzapi has facts and honest where it doesn't.

## Hard refusals — never answer

These are out of scope and the skill must decline cleanly, then suggest the
right resource.

| Asked about | Why we refuse | Redirect to |
|---|---|---|
| "Is professor X good / strict / easy?" | Subjective; vvzapi ratings ≠ teaching quality. | Suggest the official `lecturers.ethz.ch` page and student forums. |
| "What grade will I get in course X?" | Prediction we cannot ground. | Talk to the lecturer; check past exam materials. |
| "Will I be admitted to programme Y?" | Admissions data not exposed. | Studiensekretariat / programme coordinator. |
| "Can I get credit transfer from another university for X?" | Decided by the Studiendelegierte/Anerkennung, not the catalogue. | Studiensekretariat of the target programme. |
| "How many students applied / were admitted to course X last year?" | ETH does not publish enrolment numbers. | Not available. |
| "Which courses give 'easy ECTS'?" | Reputation-based, not a data question. | We don't help with this — link to anonymous student forums. |
| Personal academic advice ("should I drop out", "switch programmes") | Way outside scope. | Mentoring services, programme coordinator. |
| Anything involving identifying or contacting a specific student | Privacy. | n/a. |

## Soft hedges — answer, but disclose

These have data but the data is incomplete or imprecise. Always add a hedge.

| Asked about | Hedge to include |
|---|---|
| Course capacity (`max_places` populated) | "Catalogue lists max N places. This is the published cap; actual selection rules may apply — see general_restrictions and confirm with the lecturer." |
| Course capacity (`max_places` is null) | "The catalogue does not publish a hard cap for this course. That usually means it's open, but the lecturer may still set conditions — verify on vvz.ethz.ch." |
| Prerequisites | "Prerequisites listed in the catalogue: [verbatim text]. The catalogue lists requirements as prose, not as a verified dependency graph — treat as recommendations and check with the lecturer for binding cases." |
| Historical existence of a course (`number:` query) | "vvzapi has data for [list]. **Note: vvzapi has no data from 2009 to 2019**; if the course existed then, we cannot see it. Pre-2009 absence in vvzapi also doesn't prove the course didn't exist." |
| Credit eligibility | "Per the [Reglement edition + year], course X is listed under [section] for programme Y. Verify on vvz.ethz.ch and check the 'Stand' date on your Reglement before binding action." |
| Anything sourced from `programmes_requirements.json` | Always cite `data_asof.requirements_verified_at` and the Reglement URL from the record. |
| When `semkez > data_asof.vvzapi_snapshot_semkez` | "Our bundled section snapshot is from [semester]; this answer may be stale — verify on vvz.ethz.ch." |
| Course ratings | "vvzapi user rating: X/5 from N voters. Note this is a small, self-selected sample and not an official ETH metric." |

## When vvzapi is unreachable

Helper returns `{"ok": false, "error": "vvzapi_unreachable" | "rate_limited" | "vvzapi_5xx"}`.

Never improvise data. Respond:

> I couldn't reach the course catalogue API just now ([error code]). Please try
> again in a moment, or look it up directly at https://vvz.ethz.ch.

If the failure is `rate_limited`, also say: "vvzapi is throttling requests — please retry in ~[retry_after_s] seconds."

## When a query is ambiguous

If the user mentions a programme or category by an informal name that maps to
multiple section IDs (e.g. "Wahlfächer" exists in every programme), **ask**
which programme they're in rather than guess. One short question, not a list of
clarifications.

## Tone

- Direct. No "I'm sorry but I can't…" preamble.
- One sentence of refusal + one sentence of redirect.
- Don't moralize. The student doesn't need a lecture on academic integrity for
  asking which course is easiest.
