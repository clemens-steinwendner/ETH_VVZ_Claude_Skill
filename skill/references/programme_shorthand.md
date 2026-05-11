# Programme & category shorthand

How students at ETH talk vs. how to find it in vvzapi.

---

## Department shortcuts

When the user says "INFK", "Mech", "Math Bachelor", etc., map it to a course-number
prefix and/or section-name search. **Do not use the buggy `department=N` filter
in `/v1/unit/list`** — see `query_syntax.md`.

| User says | Department | Course-number prefix(es) | Section name pattern |
|---|---|---|---|
| ARCH, Architektur | D-ARCH | `051-` | `Architektur` |
| BAUG, Bauingenieur, Umwelting. | D-BAUG | `101-`, `102-`, `103-` | `Bauingenieur`, `Umweltingenieur`, `Geomatik` |
| MAVT, Mech, Maschbau | D-MAVT | `151-` | `Maschineningenieur` |
| INFK, CS, Informatik | D-INFK | `252-`, `263-`, `264-`, `262-` | `Informatik` |
| MTEC | D-MTEC | `363-` | `Management` |
| MATH | D-MATH | `401-` | `Mathematik` |
| PHYS, Physik | D-PHYS | `402-` | `Physik` |
| BIOL, Biologie | D-BIOL | `551-`, `701-`, `551-`*shared with USYS* | `Biologie` |
| ERDW, Earth Sciences | D-ERDW | `651-` | `Erdwissenschaften` |
| GESS *(as department)* | D-GESS | `851-`, `860-`, `862-` | `Geistes-` |
| ITET, EE | D-ITET | `227-`, `228-` | `Elektrotechnik` |
| MATL, Materials | D-MATL | `327-` | `Materialwissenschaft` |
| CHAB, Chemie, Pharma | D-CHAB | `529-`, `535-` | `Chemie`, `Pharmazeutische` |
| BSSE | D-BSSE | `636-` | `Biosystems` |
| HEST, HST | D-HEST | `376-` | `Gesundheitswissenschaften`, `Bewegungswissenschaften`, `Humanmedizin` |
| USYS, Umweltnaturwiss. | D-USYS | `701-`, `751-`, `121-` | `Umweltnaturwissenschaften`, `Agrarwissenschaften` |

> Course-number prefixes are the **most reliable** dept filter. Pull the candidate
> list with `list_units(semkez=...)` or `search(q="...")`, then filter
> `number.startswith("252-")` client-side.

---

## Category shorthand (within a programme)

Categories ("Bereiche" in VVZ) are the rows of a programme's section tree.
The user-typed name resolves via `list_sections(name_search=...)` or `search(q='offered:"<name>"')`.

### Common compulsory / elective categories

| User says | Resolves to (substring match) | Notes |
|---|---|---|
| "Kernfächer", "core courses", "Pflichtfächer" | `Kernfächer` (DE), `Core Courses` (EN) | Compulsory for the programme. Section's `learning_units` type = `O`. |
| "Grundlagenfächer", "Basics" | `Grundlagenfächer`, `Grundlagen` | Foundational compulsories, usually 1st-year. |
| "Wahlfächer", "electives", "freie Wahl" | `Wahlfächer`, `Electives` | Free electives. `learning_units` type = `W`. |
| "Pflichtwahlfächer", "Wahlpflichtfächer", "restricted electives" | `Pflichtwahlfach`, `Wahlpflicht` | Must choose from a set. `learning_units` type = `W+`. |
| "Erweiterung", "extension electives" | `Erweiterung` | `learning_units` type = `E-`. |
| "Praktika", "Labs" | `Praktikum`, `Laboratory` | Often capacity-capped. |
| "Seminar(e)" | `Seminar` | Often capacity-capped. |
| "Industriepraktikum", "Industry internship" | `Industriepraktikum`, `Industry` | Programme-specific. |

### Programme-specific work / thesis

| User says | Resolves to |
|---|---|
| "Bachelor-Arbeit", "BSc thesis" | `Bachelor-Arbeit`, `Bachelor's Thesis` (~10 KP typically) |
| "Master-Arbeit", "MSc thesis", "Master's thesis" | `Master-Arbeit`, `Master's Thesis` (25–30 KP) |
| "Semesterarbeit" | `Semesterarbeit`, `Semester Project` |
| "Studienarbeit", "Mentorierte Arbeit" | `Studienarbeit`, `Mentorierte` |

---

## Cross-cutting categories (apply to most programmes)

| User says | Where to find it | Quota source |
|---|---|---|
| "GESS", "Sci-Per", "SiP", "Science in Perspective", "Wissenschaft im Kontext" | Section names matching `Wissenschaft im Kontext` (DE) or `Science in Perspective` (EN). Also accessible via `search(q='offered:"Wissenschaft im Kontext"')`. | `programmes_requirements.json` per programme (BSc typically 6 KP, MSc typically 2 KP). |
| "Sprachkurse", "language courses" | `Sprachzentrum` units (course numbers `851-...`); count only inside the SiP quota, **capped at 3 KP across BSc + MSc combined**. | SiP Weisung. |
| "Sport credits" | `Akademischer Sportverband` / `ASVZ` sections; not all programmes credit sport. | Programme-specific. |
| "Basisprüfung" (BSc only) | First-year exam block, listed in each programme's section tree as `Basisprüfung`. | `programmes_requirements.json`. Some programmes pilot the "aufgeteilte Basisprüfung" — verify Stand date. |
| "Doktoratsfach", "Doctoral courses" | `learning_units` type = `Dr`. |  |
| "Lehrdiplom", "Teaching diploma" | `Lehrdiplom` sections, mostly D-INFK / D-MATH / D-PHYS. |  |

---

## Course-type vocabulary

vvzapi exposes these in `exam_type` (string) and via search field `examtype:`.

| User says | Maps to |
|---|---|
| "Vorlesung", "lecture", "V" | exam_type contains `Vorlesung` / typically `graded session examination` |
| "Übung", "tutorial", "U" | exam_type contains `Übung` |
| "Seminar", "S" | exam_type contains `Seminar`; commonly `ungraded semester performance` |
| "Praktikum", "lab", "P" | exam_type contains `Praktikum` |
| "Kolloquium" | exam_type contains `Kolloquium` |
| "Projektarbeit", "project" | exam_type contains `Projekt` or `Project` |

---

## Level shortcuts

| User says | `level=` value |
|---|---|
| "Bachelor", "BSc", "Undergrad" | `BSC` |
| "Master", "MSc", "Grad" | `MSC` |
| "Doktorat", "PhD", "Promotion" | `DR` |
| "weitere", "additional", "Lehrdiplom" | (varies — check section level field) |

---

## Disambiguation rules

- "Wahlfächer" alone is **always ambiguous** — every programme has its own
  Wahlfächer section. If the user hasn't named a programme yet, ask which one.
- "Math" / "Mathe" without level is ambiguous between BSc and MSc. Ask if it
  matters for the question (it often does — quota differs).
- "Statistik" can mean MSc Statistics (programme) OR the "Statistik" topic
  area in another programme. Default to topic; confirm if a recommendation
  hinges on it.
- For very short queries ("GESS?", "Wahlfach?") with no programme context, the
  skill should briefly ask which programme/level before answering.
