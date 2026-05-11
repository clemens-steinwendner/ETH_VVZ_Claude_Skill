"""Probe vvzapi.ch from a claude.ai skill's code-execution sandbox."""
import json
import urllib.request
import urllib.error

URL = "https://vvzapi.ch/api/v2/search?q=Analysis&limit=1"

try:
    req = urllib.request.Request(URL, headers={"User-Agent": "vvzapi-skill-probe/0.1"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        body = resp.read().decode("utf-8")
    data = json.loads(body)
    first_id = next(iter(data.get("results", {})), None)
    first_title = None
    if first_id:
        units = data["results"][first_id].get("units", [])
        if units:
            first_title = units[0].get("title_english") or units[0].get("title")
    print(f"STATUS={status}")
    print(f"TOTAL={data.get('total')}")
    print(f"FIRST_ID={first_id}")
    print(f"FIRST_TITLE={first_title}")
    print("RESULT=ok" if status == 200 and first_id else "RESULT=unexpected_shape")
except urllib.error.URLError as e:
    print(f"RESULT=network_blocked")
    print(f"ERROR={type(e).__name__}: {e}")
except Exception as e:
    print(f"RESULT=other_error")
    print(f"ERROR={type(e).__name__}: {e}")
