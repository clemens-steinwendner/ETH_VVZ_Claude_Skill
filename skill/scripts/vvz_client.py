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
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://vvzapi.ch"
USER_AGENT = "vvz-eth-skill/0.1 (+https://github.com/anthropics/claude-code; polite-client)"
CACHE_DIR = "/tmp/vvz_cache"
MIN_INTERVAL_S = 1.0
MAX_RETRIES = 3
TIMEOUT_S = 15
LARGE_PAYLOAD_WARN_BYTES = 5_000_000

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
        try:
            with open(cache_file) as f:
                return _ok(json.load(f))
        except (OSError, json.JSONDecodeError):
            pass  # corrupted cache — refetch

    for attempt in range(MAX_RETRIES):
        elapsed = time.time() - _last_request_ts
        if elapsed < MIN_INTERVAL_S:
            time.sleep(MIN_INTERVAL_S - elapsed)

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            _last_request_ts = time.time()
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                body = resp.read()
            if len(body) > LARGE_PAYLOAD_WARN_BYTES:
                # not an error, but the model should be aware before stuffing into context
                pass
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
    print("smoke test — fetching a few endpoints...")

    r = list_semesters()
    print("list_semesters:", "ok" if r["ok"] else r,
          "count=", len(r["data"]) if r["ok"] else "-")

    r = list_units(semkez="2026S", department=5, level="BSC", ects_min=4, ects_max=8, limit=3)
    print("list_units(BSc Informatik 2026S 4-8 ECTS):",
          "ok" if r["ok"] else r,
          "ids=", r["data"][:3] if r["ok"] else "-")
    if r["ok"] and r["data"]:
        first = get_unit(r["data"][0])
        print("  -> get_unit(first):",
              first["data"].get("number") if first["ok"] else "?",
              "|",
              (first["data"].get("title_english") or first["data"].get("title"))
              if first["ok"] else first)

    r = search("objective:cryptography", limit=3)
    print("search(objective:cryptography):",
          "ok" if r["ok"] else r,
          "total=", r["data"].get("total") if r["ok"] else "-")

    r = get_unit(46593)
    print("get_unit(46593):",
          "ok" if r["ok"] else r,
          "title=", r["data"].get("title_english") if r["ok"] else "-")

    r = get_unit_sections(46593)
    print("get_unit_sections(46593):",
          "ok" if r["ok"] else r,
          "sections=", len(r["data"]) if r["ok"] else "-")

    print("done.")
