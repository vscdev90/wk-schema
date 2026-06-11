#!/usr/bin/env python3
"""
WK 2026 Schedule Auto-Updater
Fetches live match data from football-data.org and updates index.html.

Requires env var: FOOTBALL_DATA_API_KEY
Free API key: https://www.football-data.org/client/register
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

API_BASE = "https://api.football-data.org/v4"
COMPETITION = "WC"
HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")
CEST = timezone(timedelta(hours=2))

# ── English API team name → Dutch display name ──────────────────────────────
DUTCH_NAMES = {
    "Mexico": "Mexico",
    "South Africa": "Zuid-Afrika",
    "Korea Republic": "Zuid-Korea",
    "Republic of Korea": "Zuid-Korea",
    "South Korea": "Zuid-Korea",
    "Czechia": "Tsjechië",
    "Czech Republic": "Tsjechië",
    "Canada": "Canada",
    "Bosnia and Herzegovina": "Bosnië-Herz.",
    "United States": "VS",
    "United States of America": "VS",
    "USA": "VS",
    "Paraguay": "Paraguay",
    "Qatar": "Qatar",
    "Switzerland": "Zwitserland",
    "Brazil": "Brazilië",
    "Morocco": "Marokko",
    "Haiti": "Haïti",
    "Scotland": "Schotland",
    "Australia": "Australië",
    "Türkiye": "Turkije",
    "Turkey": "Turkije",
    "Germany": "Duitsland",
    "Curaçao": "Curaçao",
    "Curacao": "Curaçao",
    "Ecuador": "Ecuador",
    "Côte d'Ivoire": "Ivoorkust",
    "Ivory Coast": "Ivoorkust",
    "Netherlands": "Nederland",
    "Japan": "Japan",
    "Sweden": "Zweden",
    "Tunisia": "Tunesië",
    "Spain": "Spanje",
    "Cape Verde": "Kaapverdië",
    "Belgium": "België",
    "Egypt": "Egypte",
    "Saudi Arabia": "Saudi-Arabië",
    "Uruguay": "Uruguay",
    "Iran": "Iran",
    "Islamic Republic of Iran": "Iran",
    "New Zealand": "Nieuw-Zeeland",
    "France": "Frankrijk",
    "Senegal": "Senegal",
    "Iraq": "Irak",
    "Norway": "Noorwegen",
    "Argentina": "Argentinië",
    "Algeria": "Algerije",
    "Austria": "Oostenrijk",
    "Jordan": "Jordanië",
    "Portugal": "Portugal",
    "DR Congo": "DR Congo",
    "Congo DR": "DR Congo",
    "Democratic Republic of Congo": "DR Congo",
    "Uzbekistan": "Oezbekistan",
    "Colombia": "Colombia",
    "England": "Engeland",
    "Croatia": "Kroatië",
    "Ghana": "Ghana",
    "Panama": "Panama",
}

# ── Flag emoji by TLA (FIFA 3-letter code) ──────────────────────────────────
FLAGS_BY_TLA = {
    "MEX": "🇲🇽", "RSA": "🇿🇦", "KOR": "🇰🇷", "CZE": "🇨🇿",
    "CAN": "🇨🇦", "BIH": "🇧🇦", "USA": "🇺🇸", "PAR": "🇵🇾",
    "QAT": "🇶🇦", "SUI": "🇨🇭", "BRA": "🇧🇷", "MAR": "🇲🇦",
    "HAI": "🇭🇹", "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "AUS": "🇦🇺", "TUR": "🇹🇷",
    "GER": "🇩🇪", "CUW": "🇨🇼", "ECU": "🇪🇨", "CIV": "🇨🇮",
    "NED": "🇳🇱", "JPN": "🇯🇵", "SWE": "🇸🇪", "TUN": "🇹🇳",
    "ESP": "🇪🇸", "CPV": "🇨🇻", "BEL": "🇧🇪", "EGY": "🇪🇬",
    "KSA": "🇸🇦", "SAU": "🇸🇦", "URU": "🇺🇾", "IRN": "🇮🇷",
    "NZL": "🇳🇿", "FRA": "🇫🇷", "SEN": "🇸🇳", "IRQ": "🇮🇶",
    "NOR": "🇳🇴", "ARG": "🇦🇷", "ALG": "🇩🇿", "AUT": "🇦🇹",
    "JOR": "🇯🇴", "POR": "🇵🇹", "COD": "🇨🇩", "UZB": "🇺🇿",
    "COL": "🇨🇴", "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "CRO": "🇭🇷", "GHA": "🇬🇭",
    "PAN": "🇵🇦",
}

FLAGS_BY_NAME = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "Korea Republic": "🇰🇷",
    "Republic of Korea": "🇰🇷", "South Korea": "🇰🇷", "Czechia": "🇨🇿",
    "Czech Republic": "🇨🇿", "Canada": "🇨🇦",
    "Bosnia and Herzegovina": "🇧🇦", "United States": "🇺🇸",
    "United States of America": "🇺🇸", "USA": "🇺🇸", "Paraguay": "🇵🇾",
    "Qatar": "🇶🇦", "Switzerland": "🇨🇭", "Brazil": "🇧🇷",
    "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Australia": "🇦🇺", "Türkiye": "🇹🇷", "Turkey": "🇹🇷",
    "Germany": "🇩🇪", "Curaçao": "🇨🇼", "Curacao": "🇨🇼",
    "Ecuador": "🇪🇨", "Côte d'Ivoire": "🇨🇮", "Ivory Coast": "🇨🇮",
    "Netherlands": "🇳🇱", "Japan": "🇯🇵", "Sweden": "🇸🇪",
    "Tunisia": "🇹🇳", "Spain": "🇪🇸", "Cape Verde": "🇨🇻",
    "Belgium": "🇧🇪", "Egypt": "🇪🇬", "Saudi Arabia": "🇸🇦",
    "Uruguay": "🇺🇾", "Iran": "🇮🇷", "Islamic Republic of Iran": "🇮🇷",
    "New Zealand": "🇳🇿", "France": "🇫🇷", "Senegal": "🇸🇳",
    "Iraq": "🇮🇶", "Norway": "🇳🇴", "Argentina": "🇦🇷",
    "Algeria": "🇩🇿", "Austria": "🇦🇹", "Jordan": "🇯🇴",
    "Portugal": "🇵🇹", "DR Congo": "🇨🇩", "Congo DR": "🇨🇩",
    "Democratic Republic of Congo": "🇨🇩", "Uzbekistan": "🇺🇿",
    "Colombia": "🇨🇴", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Croatia": "🇭🇷",
    "Ghana": "🇬🇭", "Panama": "🇵🇦",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_flag(team: dict) -> str:
    tla  = team.get("tla") or ""
    name = team.get("name") or ""
    short = team.get("shortName") or ""
    return (FLAGS_BY_TLA.get(tla)
            or FLAGS_BY_NAME.get(name)
            or FLAGS_BY_NAME.get(short)
            or "🏳️")


def dutch_name(team: dict) -> str:
    name  = team.get("name") or ""
    short = team.get("shortName") or ""
    return (DUTCH_NAMES.get(name)
            or DUTCH_NAMES.get(short)
            or name
            or "?")


def parse_group(raw: str) -> str:
    """'GROUP_A' → 'A',  'Group A' → 'A',  'A' → 'A'"""
    raw = raw.strip()
    if raw.startswith("GROUP_"):
        return raw[6:]
    if raw.startswith("Group "):
        return raw[6:]
    return raw


# ── API ───────────────────────────────────────────────────────────────────────

def fetch_matches() -> list | None:
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "")
    if not api_key:
        print("ERROR: FOOTBALL_DATA_API_KEY environment variable not set.", file=sys.stderr)
        print("Get a free key at https://www.football-data.org/client/register", file=sys.stderr)
        return None

    url = f"{API_BASE}/competitions/{COMPETITION}/matches"
    req = urllib.request.Request(url, headers={"X-Auth-Token": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get("matches", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace") if e.fp else ""
        print(f"HTTP {e.code} from API: {e.reason}. Body: {body[:200]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error fetching from API: {e}", file=sys.stderr)
        return None


# ── Conversion ────────────────────────────────────────────────────────────────

def convert_match(m: dict, idx: int) -> dict:
    utc_dt  = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
    cest_dt = utc_dt.astimezone(CEST)

    date_str = cest_dt.strftime("%Y-%m-%d")
    time_str = cest_dt.strftime("%H:%M")

    group_raw = m.get("group") or ""
    group     = parse_group(group_raw) if group_raw else "?"
    matchday  = m.get("matchday") or 1

    home_team  = m.get("homeTeam") or {}
    away_team  = m.get("awayTeam") or {}
    home_dutch = dutch_name(home_team)
    away_dutch = dutch_name(away_team)
    home_flag  = get_flag(home_team)
    away_flag  = get_flag(away_team)

    is_nl = home_dutch == "Nederland" or away_dutch == "Nederland"
    # MD3 per-group matches are played simultaneously
    sim   = (matchday >= 3)

    score_data = m.get("score") or {}
    ft         = score_data.get("fullTime") or {}
    h_score    = ft.get("home")
    a_score    = ft.get("away")

    status_api = m.get("status", "SCHEDULED")
    # Map API statuses to our simple model used in matchStatus():
    # We store api_status so the JS can cross-check if needed (optional).

    venue = (m.get("venue") or "").strip()

    entry: dict = {
        "id":    m.get("id") or idx,
        "date":  date_str,
        "time":  time_str,
        "home":  home_dutch,
        "away":  away_dutch,
        "hf":    home_flag,
        "af":    away_flag,
        "group": group,
        "venue": venue,
        "md":    matchday,
    }
    if is_nl:
        entry["nl"] = True
    if sim:
        entry["sim"] = True
    if h_score is not None and a_score is not None:
        entry["score"] = {"home": h_score, "away": a_score}

    return entry


# ── JS array serialisation ────────────────────────────────────────────────────

def _js_str(v) -> str:
    """Escape a string for a single-quoted JS literal."""
    return v.replace("\\", "\\\\").replace("'", "\\'")


def generate_js_array(matches: list[dict]) -> str:
    lines = ["// MATCHES_DATA_START", "const MATCHES = ["]
    for m in matches:
        parts = [
            f"  {{id:{m['id']},",
            f"date:\"{m['date']}\",time:\"{m['time']}\",",
            f"home:\"{_js_str(m['home'])}\",away:\"{_js_str(m['away'])}\",",
            f"hf:\"{m['hf']}\",af:\"{m['af']}\",",
            f"group:\"{m['group']}\",venue:\"{_js_str(m['venue'])}\",md:{m['md']}",
        ]
        extras = ""
        if m.get("nl"):
            extras += ",nl:true"
        if m.get("sim"):
            extras += ",sim:true"
        if "score" in m:
            s = m["score"]
            extras += f",score:{{home:{s['home']},away:{s['away']}}}"
        parts.append(extras + "},")
        lines.append("".join(parts))
    lines.append("];")
    lines.append("// MATCHES_DATA_END")
    return "\n".join(lines)


# ── HTML patching ─────────────────────────────────────────────────────────────

MARKER_RE = re.compile(
    r"// MATCHES_DATA_START.*?// MATCHES_DATA_END",
    re.DOTALL,
)


def update_html(new_block: str) -> bool:
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        original = f.read()

    if not MARKER_RE.search(original):
        print("ERROR: Markers // MATCHES_DATA_START / // MATCHES_DATA_END not found in index.html",
              file=sys.stderr)
        sys.exit(1)

    updated = MARKER_RE.sub(new_block, original)

    if updated == original:
        print("No data changes detected – index.html is already up to date.")
        return False

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(updated)

    print("index.html successfully updated.")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Fetching WK 2026 match data from football-data.org …")
    raw_matches = fetch_matches()
    if raw_matches is None:
        sys.exit(1)

    # Keep only group stage matches
    group_matches = [
        m for m in raw_matches
        if m.get("stage") == "GROUP_STAGE"
    ]
    group_matches.sort(key=lambda m: m.get("utcDate", ""))
    print(f"Found {len(group_matches)} group stage matches.")

    if not group_matches:
        print("WARNING: No group stage matches returned by API. Keeping existing data.",
              file=sys.stderr)
        sys.exit(0)

    converted  = [convert_match(m, i + 1) for i, m in enumerate(group_matches)]
    js_block   = generate_js_array(converted)
    changed    = update_html(js_block)

    # Signal to GitHub Actions whether a commit is needed
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
    else:
        print(f"changed={'true' if changed else 'false'}")


if __name__ == "__main__":
    main()
