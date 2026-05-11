"""vvzapi.ch client for the ETH VVZ Claude Skill.

Single-file module — no third-party deps, stdlib only, so it runs unchanged in the
claude.ai code-execution sandbox.

Design points:
  * Polite client: minimum 1.0 s gap between requests, exponential backoff on 429/5xx.
  * Per-session disk cache at /tmp/vvz_cache/*.json (confirmed to persist between
    code-exec invocations within a single chat session).
  * Every public function returns either a success dict or a structured error
    envelope: {"ok": False, "error": "<code>", "detail": "...", "retry_after_s": ...}.
  * Never raises — callers (and the model) get predictable shapes.

Public functions (the only API the SKILL.md prompt should call):

    search(q, *, limit=20, offset=0, order_by="year", order="desc")
    list_units(*, semkez=None, level=None, department=None, section=None,
               number=None, title=None, lecturer_id=None, lecturer_name=None,
               lecturer_surname=None, type=None, language=None, periodicity=None,
               ects_min=None, ects_max=None, content_search=None,
               limit=100, offset=0)
    get_unit(unit_id)
    get_unit_sections(unit_id)
    get_unit_lecturers(unit_id)
    get_section(section_id)
    list_sections(*, semkez=None, level=None, parent_id=None, name_search=None,
                  comment_search=None, sort_lex=False, limit=100, offset=0)
    get_lecturer(lecturer_id)
    list_semesters()

Run this file directly to smoke-test against vvzapi.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://vvzapi.ch"
USER_AGENT = (
    "eth-vvz-claude-skill/0.1 "
    "(+https://github.com/clemens-steinwendner/ETH_VVZ_Claude_Skill; polite-client)"
)
CACHE_DIR = "/tmp/vvz_cache"
CACHE_TTL_S = 6 * 60 * 60  # 6 hours — vvzapi data can shift mid-semester
MIN_INTERVAL_S = 1.0
MAX_RETRIES = 3
TIMEOUT_S = 15

_last_request_ts = 0.0


def _ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(url: str) -> str:
    key = hashlib.sha256(url.encode()).hexdigest()[:32]
    return os.path.join(CACHE_DIR, f"{key}.json")


def _err(code: str, detail: str = "", retry_after_s=None) -> dict:
    return {"ok": False, "error": code, "detail": detail, "retry_after_s": retry_after_s}


def _ok(data) -> dict:
    return {"ok": True, "data": data}


def _build_url(path: str, params: dict | None = None) -> str:
    url = BASE + path
    if params:
        cleaned = {k: v for k, v in params.items() if v is not None}
        if cleaned:
            url += "?" + urllib.parse.urlencode(cleaned, doseq=True)
    return url


def _request(url: str, *, use_cache: bool = True) -> dict:
    global _last_request_ts
    _ensure_cache()
    cache_file = _cache_path(url)
    if use_cache and os.path.exists(cache_file):
        age_s = time.time() - os.path.getmtime(cache_file)
        if age_s < CACHE_TTL_S:
            try:
                with open(cache_file) as f:
                    return _ok(json.load(f))
            except (OSError, json.JSONDecodeError):
                pass  # corrupted cache — refetch
        # else: expired, fall through to refetch

    for attempt in range(MAX_RETRIES):
        elapsed = time.time() - _last_request_ts
        if elapsed < MIN_INTERVAL_S:
            time.sleep(MIN_INTERVAL_S - elapsed)

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            _last_request_ts = time.time()
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                body = resp.read()
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                return _err("invalid_response", f"non-JSON body: {e}")
            try:
                with open(cache_file, "w") as f:
                    json.dump(data, f)
            except OSError:
                pass  # cache write failure is not fatal
            return _ok(data)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return _err("not_found", f"404 at {url}")
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", "5"))
                if attempt < MAX_RETRIES - 1:
                    time.sleep(retry_after)
                    continue
                return _err("rate_limited", "429 from vvzapi", retry_after_s=retry_after)
            if 500 <= e.code < 600:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                return _err("vvzapi_5xx", f"{e.code} from vvzapi after {MAX_RETRIES} attempts")
            if e.code == 400:
                return _err("invalid_query", f"400 at {url}")
            return _err("http_error", f"HTTP {e.code} at {url}")

        except urllib.error.URLError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return _err("vvzapi_unreachable", f"network error: {e.reason}")
        except TimeoutError:
            if attempt < MAX_RETRIES - 1:
                continue
            return _err("vvzapi_unreachable", "timeout")
    return _err("vvzapi_unreachable", "exhausted retries")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def search(q, *, limit=20, offset=0, order_by="year", order="desc"):
    """Free-text Scryfall-style search. See references/query_syntax.md."""
    return _request(_build_url("/api/v2/search", {
        "q": q, "limit": limit, "offset": offset, "order_by": order_by, "order": order,
    }))


def list_units(*, semkez=None, level=None, department=None, section=None,
               number=None, title=None, lecturer_id=None, lecturer_name=None,
               lecturer_surname=None, type=None, language=None, periodicity=None,
               ects_min=None, ects_max=None, content_search=None,
               limit=100, offset=0):
    """Typed unit search. Prefer this over `search` when filters are structured."""
    return _request(_build_url("/api/v1/unit/list", {
        "semkez": semkez, "level": level, "department": department, "section": section,
        "number": number, "title": title, "lecturer_id": lecturer_id,
        "lecturer_name": lecturer_name, "lecturer_surname": lecturer_surname,
        "type": type, "language": language, "periodicity": periodicity,
        "ects_min": ects_min, "ects_max": ects_max, "content_search": content_search,
        "limit": limit, "offset": offset,
    }))


def get_unit(unit_id):
    return _request(_build_url(f"/api/v1/unit/{int(unit_id)}/get"))


def get_unit_sections(unit_id):
    """Returns the list of section IDs the unit is 'Offered in'."""
    return _request(_build_url(f"/api/v1/unit/{int(unit_id)}/sections"))


def get_unit_lecturers(unit_id, *, limit=100, offset=0):
    return _request(_build_url(
        f"/api/v1/unit/{int(unit_id)}/lecturers",
        {"limit": limit, "offset": offset},
    ))


def get_course(unit_id):
    """Per-instance scheduling for a unit: meeting times, hours, types.

    Returns a list of course-instance records with `timeslots`, `hours`,
    `type` (V/U/P/S), `semkez`. Use this to answer "Uhrzeiten" questions —
    `get_unit` does NOT carry meeting times.
    """
    return _request(_build_url(f"/api/v1/course/get/{int(unit_id)}"))


def get_section(section_id):
    return _request(_build_url(f"/api/v1/section/{int(section_id)}/get"))


def list_sections(*, semkez=None, level=None, parent_id=None, name_search=None,
                  comment_search=None, sort_lex=False, limit=100, offset=0):
    return _request(_build_url("/api/v1/section/list", {
        "semkez": semkez, "level": level, "parent_id": parent_id,
        "name_search": name_search, "comment_search": comment_search,
        "sort_lex": str(sort_lex).lower(), "limit": limit, "offset": offset,
    }))


def get_lecturer(lecturer_id):
    return _request(_build_url(f"/api/v1/lecturer/get/{int(lecturer_id)}"))


def list_semesters():
    return _request(_build_url("/api/v1/misc/semesters"))


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    failures = []

    def _check(label, cond, detail=""):
        status = "ok" if cond else "FAIL"
        print(f"  {label:60s} {status} {detail}")
        if not cond:
            failures.append(label)

    print("smoke test — fetching a few endpoints...\n")

    r = list_semesters()
    _check("list_semesters returns ≥1 semester",
           r["ok"] and len(r["data"]) > 0,
           f"count={len(r['data']) if r['ok'] else r}")

    # NOTE: department= filter is buggy upstream for several IDs (see
    # references/query_syntax.md). Smoke-test relies on `level` + `title`
    # which DO filter correctly, then verifies via course-number prefix.
    r = list_units(semkez="2026S", level="BSC", title="Algorithms", limit=5)
    _check("list_units(BSc 2026S title=Algorithms) returns IDs",
           r["ok"] and isinstance(r["data"], list) and len(r["data"]) > 0,
           f"ids={r['data'][:3] if r['ok'] else r}")

    if r["ok"] and r["data"]:
        first = get_unit(r["data"][0])
        if first["ok"]:
            d = first["data"]
            _check("get_unit() exposes plural fields",
                   isinstance(d.get("levels"), list)
                   and isinstance(d.get("departments"), list),
                   f"levels={d.get('levels')} departments={d.get('departments')}")
            _check("get_unit() title contains 'algorith' (case-insensitive)",
                   "algorith" in (d.get("title_english") or d.get("title") or "").lower(),
                   f"number={d.get('number')} title={d.get('title_english') or d.get('title')}")

    r = search('objective:cryptography', limit=3)
    _check("search(objective:cryptography) returns >0 total",
           r["ok"] and r["data"].get("total", 0) > 0,
           f"total={r['data'].get('total') if r['ok'] else r}")

    r = get_unit_sections(46593)
    _check("get_unit_sections returns bare list of int IDs",
           r["ok"] and isinstance(r["data"], list)
           and all(isinstance(x, int) for x in r["data"]),
           f"sample={r['data'][:3] if r['ok'] else r}")

    r = get_course(46593)
    _check("get_course returns instance list with 'timeslots' key",
           r["ok"] and isinstance(r["data"], list)
           and (not r["data"] or "timeslots" in r["data"][0]),
           f"len={len(r['data']) if r['ok'] else r}")

    # list_sections: level is INT depth, not degree enum
    r = list_sections(semkez="2025W", level=0, limit=3)
    _check("list_sections(level=0 int) returns bare int IDs",
           r["ok"] and isinstance(r["data"], list)
           and all(isinstance(x, int) for x in r["data"]),
           f"sample={r['data'][:3] if r['ok'] else r}")

    # Confirm `level=BSC` (string) is correctly rejected — guards the doc claim
    r_bad = list_sections(semkez="2025W", level="BSC", limit=3)
    _check("list_sections(level='BSC') is rejected (proves docs)",
           not r_bad["ok"] and r_bad["error"] in {"invalid_query", "http_error"},
           f"error={r_bad.get('error')}")

    # Section name fallback: name often null, name_english populated
    if r["ok"] and r["data"]:
        sec = get_section(r["data"][0])
        if sec["ok"]:
            d = sec["data"]
            _check("get_section returns at least one of name/name_english",
                   d.get("name") or d.get("name_english"),
                   f"name={d.get('name')!r} name_english={d.get('name_english')!r}")

    # `credits` is the ECTS field on a unit
    r = get_unit(46593)
    if r["ok"]:
        _check("get_unit() exposes `credits` (float ECTS), not `ects`",
               isinstance(r["data"].get("credits"), (int, float)),
               f"credits={r['data'].get('credits')}")

    print()
    if failures:
        print(f"FAILED: {len(failures)} smoke test(s):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("all smoke tests passed.")
