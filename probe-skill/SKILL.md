---
name: vvzapi-probe
description: Throwaway connectivity probe — tests whether a claude.ai skill can reach https://vvzapi.ch. Use only when the user asks to "run the vvzapi probe" or "test vvzapi connectivity".
---

# vvzapi probe

Goal: confirm that this skill, running on claude.ai, can reach `https://vvzapi.ch`. Two independent paths, run both:

## Path 1 — code execution (preferred)

Run `probe.py` (bundled in this skill folder) via the code execution tool. Report:
- Whether the script ran at all (network enabled?).
- The HTTP status code it printed.
- The title of the first course in the JSON response (proves we got real data back, not a captive portal).

## Path 2 — web_fetch fallback

If code execution isn't available, call `web_fetch` on this exact URL (do not modify it):

`https://vvzapi.ch/api/v2/search?q=Analysis&limit=1`

Report whether the call succeeded, the status, and whether the JSON contains a `results` field.

## Output

A 3-line report:
1. Path 1 result (code-exec): success / failure + status code + sample title, or the error.
2. Path 2 result (web_fetch): success / failure + whether `results` field present, or the error.
3. One-line conclusion: "vvzapi is reachable from this skill via [code-exec / web_fetch / both / neither]."

Do not do anything else. This is a connectivity test, nothing more.
