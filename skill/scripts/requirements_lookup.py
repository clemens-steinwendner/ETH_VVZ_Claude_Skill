"""Lazy lookup into skill/data/programmes_requirements.json.

Public API (the only function the SKILL.md prompt should call):

    get_requirements(key_or_alias: str) -> dict

Returns one of:
    {"ok": True, "data": {... programme record ...}, "key": "<canonical_key>", "matched_via": "<alias>"}
    {"ok": False, "error": "not_found", "candidates": [...], "detail": "..."}
    {"ok": False, "error": "load_error", "detail": "..."}

Also exposes `list_programmes()` returning {canonical_key: name_full} for the
SKILL.md `programmes_index` table.

Designed to be cheap: loads the JSON once per process via lru_cache, returns
only the matched record (300-500 tokens), never dumps the whole file.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
REQUIREMENTS_PATH = os.path.join(DATA_DIR, "programmes_requirements.json")
ALIASES_PATH = os.path.join(DATA_DIR, "programme_aliases.json")

_UMLAUT_MAP = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _normalize(s: str) -> str:
    s = s.lower().strip().translate(_UMLAUT_MAP)
    s = re.sub(r"\s+", " ", s)
    return s


@lru_cache(maxsize=1)
def _load_data() -> dict:
    with open(REQUIREMENTS_PATH, encoding="utf-8") as f:
        reqs = json.load(f)
    with open(ALIASES_PATH, encoding="utf-8") as f:
        aliases_raw = json.load(f)

    # Build a normalized-alias -> canonical_key index.
    alias_index: dict[str, str] = {}
    for canonical, alias_list in aliases_raw.items():
        if canonical.startswith("_"):
            continue
        # canonical key itself is also a valid lookup
        alias_index[_normalize(canonical)] = canonical
        for a in alias_list:
            alias_index[_normalize(a)] = canonical

    return {"requirements": reqs, "alias_index": alias_index}


def list_programmes() -> dict[str, str]:
    """Return {canonical_key: name_full} for the bundle's known programmes."""
    try:
        d = _load_data()
    except (OSError, json.JSONDecodeError):
        return {}
    return {k: rec.get("name_full", k) for k, rec in d["requirements"]["programmes"].items()}


def get_requirements(key_or_alias: str) -> dict:
    """Look up one programme's requirements record."""
    try:
        d = _load_data()
    except OSError as e:
        return {"ok": False, "error": "load_error", "detail": f"could not open data file: {e}"}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": "load_error", "detail": f"data file corrupt: {e}"}

    needle = _normalize(key_or_alias)
    alias_index = d["alias_index"]
    programmes = d["requirements"]["programmes"]

    # 1. Exact match.
    canonical = alias_index.get(needle)
    if canonical and canonical in programmes:
        return {
            "ok": True,
            "key": canonical,
            "matched_via": "alias" if needle != canonical else "canonical_key",
            "data": programmes[canonical],
            "data_asof": d["requirements"]["data_asof"],
        }

    # 2. Substring fallback — find aliases containing the needle.
    candidates: list[tuple[str, str]] = []  # (canonical, matched_alias)
    for alias_norm, canonical in alias_index.items():
        if needle in alias_norm or alias_norm in needle:
            candidates.append((canonical, alias_norm))

    # Dedupe by canonical, keep first matched alias.
    seen = {}
    for canonical, alias_norm in candidates:
        seen.setdefault(canonical, alias_norm)

    if len(seen) == 1:
        canonical = next(iter(seen))
        return {
            "ok": True,
            "key": canonical,
            "matched_via": f"substring:{seen[canonical]}",
            "data": programmes[canonical],
            "data_asof": d["requirements"]["data_asof"],
        }

    if len(seen) > 1:
        return {
            "ok": False,
            "error": "ambiguous",
            "candidates": sorted(seen.keys()),
            "detail": f"'{key_or_alias}' matched {len(seen)} programmes — ask the user which one",
        }

    return {
        "ok": False,
        "error": "not_found",
        "detail": f"no programme matches '{key_or_alias}'",
        "hint": "call list_programmes() for the full set of canonical keys",
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for q in [
        "INFK bachelor",
        "BSc Informatik",
        "MAVT",
        "msc data science",
        "bsc cse",
        "Wahlfächer",  # should not match a programme — error
        "math",  # ambiguous between BSc & MSc
        "bsc_informatik_computer_science",  # canonical key
    ]:
        r = get_requirements(q)
        if r["ok"]:
            rec = r["data"]
            cats = ", ".join(f"{c['label'][:30]}…={c['kp']}" for c in rec["categories"][:3])
            print(f"  {q!r:35s} -> {r['key']:60s} (via {r['matched_via']})")
            print(f"      total={rec['total_kp']} cats[:3]: {cats}")
        else:
            print(f"  {q!r:35s} -> {r['error']}: {r.get('detail','')}")
            if r.get("candidates"):
                print(f"      candidates: {r['candidates']}")
    print()
    print(f"list_programmes() returns {len(list_programmes())} entries")
