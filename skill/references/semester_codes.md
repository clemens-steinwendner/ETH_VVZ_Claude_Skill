# Semester codes (`semkez`) — reference

ETH and vvzapi encode semesters as `YYYY` + a single letter:

| Code | Stands for | German | English | Months |
|---|---|---|---|---|
| `YYYYS` | Frühjahrssemester | FS *YY* | Spring semester | mid-Feb – early June |
| `YYYYW` | Herbstsemester | HS *YY* | Autumn / Fall semester | mid-Sept – late Dec |

The year is **the year the semester begins**. So:

- `2026S` = FS26 = Spring 2026 (Feb–Jun 2026)
- `2025W` = HS25 = Autumn 2025 (Sep–Dec 2025)
- `2025S` = FS25 = Spring 2025
- `2024W` = HS24 = Autumn 2024

## How students refer to semesters (and what to map them to)

| User says | Maps to |
|---|---|
| "FS26" | `2026S` |
| "HS25", "WS25", "HS 2025" | `2025W` |
| "Spring 2026", "Frühling 26" | `2026S` |
| "Fall 2025", "Autumn 2025", "Herbst 25" | `2025W` |
| "next semester" | depends on current date — see resolution rules below |
| "this semester" | depends on current date |
| "last semester" | the most recently completed semester |

## Resolution rules ("this", "next", "last")

Resolve relative semester names using **today's date** and the ETH academic calendar:

| Month today | Currently active semester | "Next semester" | "Last semester" |
|---|---|---|---|
| Jan | HS of previous year (still in exams) | FS of current year | FS of previous year |
| Feb (1–14) | exam period of HS prev. year | FS current year | FS prev. year |
| Feb 15 – May | FS current year | HS current year | HS prev. year |
| Jun – mid-Sep | between semesters / summer | HS current year | FS current year |
| Mid-Sep – Dec | HS current year | FS next year | FS current year |

Worked examples (today = **2026-05-11**, FS26 ongoing):

- "this semester" → `2026S`
- "next semester" → `2026W`
- "last semester" → `2025W`
- "next year" (HS) → `2026W`
- "in two semesters" → `2026W` (FS → next HS)
- "in one year" → `2027S`

## Listing available semesters in vvzapi

The endpoint `GET /api/v1/misc/semesters` returns the full list of semesters
the API has data for, e.g.:

```
["2001W","2002S",…,"2008W","2020S","2020W",…,"2025W","2026S"]
```

**Important gap:** there is no vvzapi data between `2008W` and `2020S`. When showing
historical course coverage, disclose this gap — do not claim courses were
discontinued during that window.

## Year boundary cases

- The German term *Studienjahr* runs HS → FS (e.g. HS25 + FS26 = "Studienjahr 2025/26").
- The Reglement / Wegleitung year refers to the **year the regulations took effect**,
  not the cohort year (e.g. "Reglement 2022" governs students who started under that
  edition, including future cohorts until it is replaced).
