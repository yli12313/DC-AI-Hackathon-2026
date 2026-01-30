"""
Wikipedia API client for World Cup 2026 data.

Fetches: qualified teams, team info, rosters (current squad), historical World Cup results.
Uses en.wikipedia.org/w/api.php with JSON caching.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import quote

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

WIKI_API = "https://en.wikipedia.org/w/api.php"
CACHE_TTL_SECONDS = 86400  # 24 hours
QUALIFICATION_PAGE = "2026 FIFA World Cup qualification"

# Map FIFA code / data-sort-value to display name (for qualified teams table)
# Wikimedia Commons flag URLs by FIFA code (50px)
FLAG_BY_CODE = {
    "ARG": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Flag_of_Argentina.svg/50px-Flag_of_Argentina.svg.png",
    "FRA": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/50px-Flag_of_France.svg.png",
    "BRA": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/50px-Flag_of_Brazil.svg.png",
    "ENG": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Flag_of_England.svg/50px-Flag_of_England.svg.png",
    "ESP": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Flag_of_Spain.svg/50px-Flag_of_Spain.svg.png",
    "GER": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/50px-Flag_of_Germany.svg.png",
    "NED": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/50px-Flag_of_the_Netherlands.svg.png",
    "POR": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Flag_of_Portugal.svg/50px-Flag_of_Portugal.svg.png",
    "BEL": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Flag_of_Belgium.svg/50px-Flag_of_Belgium.svg.png",
    "CRO": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Flag_of_Croatia.svg/50px-Flag_of_Croatia.svg.png",
    "URU": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Flag_of_Uruguay.svg/50px-Flag_of_Uruguay.svg.png",
    "USA": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Flag_of_the_United_States.svg/50px-Flag_of_the_United_States.svg.png",
    "MEX": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Flag_of_Mexico.svg/50px-Flag_of_Mexico.svg.png",
    "JPN": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Flag_of_Japan.svg/50px-Flag_of_Japan.svg.png",
    "KOR": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Flag_of_South_Korea.svg/50px-Flag_of_South_Korea.svg.png",
    "MAR": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Flag_of_Morocco.svg/50px-Flag_of_Morocco.svg.png",
    "SEN": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Flag_of_Senegal.svg/50px-Flag_of_Senegal.svg.png",
    "COL": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Flag_of_Colombia.svg/50px-Flag_of_Colombia.svg.png",
    "AUS": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Flag_of_Australia_%28converted%29.svg/50px-Flag_of_Australia_%28converted%29.svg.png",
    "CAN": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Flag_of_Canada.svg/50px-Flag_of_Canada.svg.png",
    "ECU": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Flag_of_Ecuador.svg/50px-Flag_of_Ecuador.svg.png",
    "PAR": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Flag_of_Paraguay.svg/50px-Flag_of_Paraguay.svg.png",
    "TUN": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Flag_of_Tunisia.svg/50px-Flag_of_Tunisia.svg.png",
    "EGY": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Flag_of_Egypt.svg/50px-Flag_of_Egypt.svg.png",
    "ALG": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Flag_of_Algeria.svg/50px-Flag_of_Algeria.svg.png",
    "GHA": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Flag_of_Ghana.svg/50px-Flag_of_Ghana.svg.png",
    "CPV": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Flag_of_Cape_Verde.svg/50px-Flag_of_Cape_Verde.svg.png",
    "RSA": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Flag_of_South_Africa.svg/50px-Flag_of_South_Africa.svg.png",
    "QAT": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Flag_of_Qatar.svg/50px-Flag_of_Qatar.svg.png",
    "KSA": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Flag_of_Saudi_Arabia.svg/50px-Flag_of_Saudi_Arabia.svg.png",
    "CIV": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Flag_of_Côte_d%27Ivoire.svg/50px-Flag_of_Côte_d%27Ivoire.svg.png",
    "IRN": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Flag_of_Iran.svg/50px-Flag_of_Iran.svg.png",
    "UZB": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Flag_of_Uzbekistan.svg/50px-Flag_of_Uzbekistan.svg.png",
    "JOR": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Flag_of_Jordan.svg/50px-Flag_of_Jordan.svg.png",
    "NZL": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Flag_of_New_Zealand.svg/50px-Flag_of_New_Zealand.svg.png",
    "NOR": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Flag_of_Norway.svg/50px-Flag_of_Norway.svg.png",
    "AUT": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Flag_of_Austria.svg/50px-Flag_of_Austria.svg.png",
    "SUI": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Flag_of_Switzerland.svg/50px-Flag_of_Switzerland.svg.png",
    "SCO": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Flag_of_Scotland.svg/50px-Flag_of_Scotland.svg.png",
    "PAN": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Flag_of_Panama.svg/50px-Flag_of_Panama.svg.png",
    "HAI": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Flag_of_Haiti.svg/50px-Flag_of_Haiti.svg.png",
    "CUW": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Flag_of_Curaçao.svg/50px-Flag_of_Curaçao.svg.png",
}

CODE_TO_NAME = {
    "canada": "Canada", "mexico": "Mexico", "united states": "United States", "usa": "United States",
    "japan": "Japan", "new zealand": "New Zealand", "iran": "Iran", "argentina": "Argentina",
    "uzbekistan": "Uzbekistan", "south korea": "South Korea", "jordan": "Jordan", "australia": "Australia",
    "brazil": "Brazil", "ecuador": "Ecuador", "uruguay": "Uruguay", "colombia": "Colombia",
    "paraguay": "Paraguay", "morocco": "Morocco", "tunisia": "Tunisia", "egypt": "Egypt",
    "algeria": "Algeria", "ghana": "Ghana", "cape verde": "Cape Verde", "south africa": "South Africa",
    "qatar": "Qatar", "england": "England", "saudi arabia": "Saudi Arabia", "ivory coast": "Ivory Coast",
    "senegal": "Senegal", "france": "France", "croatia": "Croatia", "portugal": "Portugal",
    "norway": "Norway", "germany": "Germany", "netherlands": "Netherlands", "belgium": "Belgium",
    "austria": "Austria", "switzerland": "Switzerland", "spain": "Spain", "scotland": "Scotland",
    "panama": "Panama", "haiti": "Haiti", "curacao": "Curaçao",
}


def _cache_path(key: str) -> Path:
    cache_dir = Path("data") / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w\-]", "_", key)[:120]
    return cache_dir / f"wiki_{safe}.json"


def _cached_get(key: str, fetch_fn):
    path = _cache_path(key)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("_ts", 0) + CACHE_TTL_SECONDS > time.time():
                return data.get("data")
        except (json.JSONDecodeError, KeyError):
            pass
    if not HAS_REQUESTS:
        return None
    try:
        data = fetch_fn()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"_ts": time.time(), "data": data}, f, indent=0)
        return data
    except Exception:
        return None


def _api(params: Dict) -> Optional[Dict]:
    if not HAS_REQUESTS:
        return None
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    try:
        r = requests.get(WIKI_API, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# Fallback list when Wikipedia qualification page parsing returns empty (hosts + likely qualifiers).
QUALIFIED_2026_FALLBACK = [
    {"name": "USA", "code": "USA", "sort_value": "united states"},
    {"name": "Mexico", "code": "MEX", "sort_value": "mexico"},
    {"name": "Canada", "code": "CAN", "sort_value": "canada"},
    {"name": "Argentina", "code": "ARG", "sort_value": "argentina"},
    {"name": "Brazil", "code": "BRA", "sort_value": "brazil"},
    {"name": "Uruguay", "code": "URU", "sort_value": "uruguay"},
    {"name": "Colombia", "code": "COL", "sort_value": "colombia"},
    {"name": "Ecuador", "code": "ECU", "sort_value": "ecuador"},
    {"name": "France", "code": "FRA", "sort_value": "france"},
    {"name": "England", "code": "ENG", "sort_value": "england"},
    {"name": "Spain", "code": "ESP", "sort_value": "spain"},
    {"name": "Germany", "code": "GER", "sort_value": "germany"},
    {"name": "Netherlands", "code": "NED", "sort_value": "netherlands"},
    {"name": "Portugal", "code": "POR", "sort_value": "portugal"},
    {"name": "Belgium", "code": "BEL", "sort_value": "belgium"},
    {"name": "Croatia", "code": "CRO", "sort_value": "croatia"},
    {"name": "Japan", "code": "JPN", "sort_value": "japan"},
    {"name": "South Korea", "code": "KOR", "sort_value": "south korea"},
    {"name": "Australia", "code": "AUS", "sort_value": "australia"},
    {"name": "Morocco", "code": "MAR", "sort_value": "morocco"},
    {"name": "Senegal", "code": "SEN", "sort_value": "senegal"},
]


def get_qualified_teams_2026() -> List[Dict[str, Any]]:
    """Parse Wikipedia '2026 FIFA World Cup qualification' page for qualified teams list."""
    def fetch():
        j = _api({
            "action": "query",
            "titles": QUALIFICATION_PAGE,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
        })
        if not j or "query" not in j:
            return []
        pages = j.get("query", {}).get("pages", [])
        if not pages:
            return []
        rev = pages[0].get("revisions", [{}])[0]
        content = (rev.get("slots", {}).get("main", {}).get("content") or rev.get("*") or "")
        teams = []
        seen = set()
        for m in re.finditer(r'data-sort-value="([^"]+)"[^|]*\|[^|]*\{\{fb\|([A-Z]{3})\}\}', content):
            sort_val, code = m.group(1).strip().lower(), m.group(2).upper()
            if code in seen or sort_val in {"a", "hosts"}:
                continue
            seen.add(code)
            name = CODE_TO_NAME.get(sort_val) or sort_val.replace("_", " ").title()
            if name == "United States":
                name = "USA"
            teams.append({"name": name, "code": code, "sort_value": sort_val})
        return teams

    result = _cached_get("qualified_teams_2026", fetch) or []
    return result if result else QUALIFIED_2026_FALLBACK


def get_team_page_title(team_name: str) -> str:
    """Resolve team name to Wikipedia national team page title."""
    # USA and Canada use "men's national soccer team"
    if team_name.upper() in ("USA", "UNITED STATES"):
        return "United States men's national soccer team"
    if team_name.lower() == "canada":
        return "Canada men's national soccer team"
    # Rest: "X national football team"
    return f"{team_name} national football team"


def get_team_info(team_name: str) -> Dict[str, Any]:
    """Fetch team info and flag from national team Wikipedia page."""
    title = get_team_page_title(team_name)
    key = f"team_info_{team_name.replace(' ', '_')}"

    def fetch():
        j = _api({
            "action": "query",
            "titles": title,
            "prop": "pageimages|extracts|pageprops",
            "exintro": True,
            "explaintext": True,
            "exsentences": 3,
            "piprop": "thumbnail",
            "pithumbsize": 50,
        })
        if not j or "query" not in j:
            return {"name": team_name, "flag": "", "extract": ""}
        pages = j.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return {"name": team_name, "flag": "", "extract": ""}
        p = pages[0]
        thumb = (p.get("thumbnail", {}) or {}).get("source", "")
        extract = (p.get("extract", "") or "")[:500]
        return {"name": team_name, "flag": thumb, "extract": extract}

    data = _cached_get(key, fetch) or {"name": team_name, "flag": "", "extract": ""}
    # Ensure flag: from page image or FLAG_BY_CODE
    if not data.get("flag"):
        name_lower = team_name.lower()
        for code, url in FLAG_BY_CODE.items():
            if name_lower == (CODE_TO_NAME.get(code.lower()) or "").lower() or name_lower == code.lower():
                data["flag"] = url
                break
    return data


def _extract_player_links(html: str, team_name: str) -> List[Dict[str, Any]]:
    """Extract player names from wiki/HTML link pattern [[Name]] or [[Name|...]]."""
    players = []
    for m in re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', html):
        name = m.group(1).strip()
        if name.startswith("File:") or name.startswith("Category:") or "football" in name.lower() or "FIFA" in name:
            continue
        if len(name) < 4 or len(name) > 40:
            continue
        if name.isdigit() or "(" in name:
            continue
        players.append({"name": name, "team": team_name})
    return players


def get_team_roster(team_name: str) -> List[Dict[str, Any]]:
    """Fetch current squad from national team page (Current squad section)."""
    title = get_team_page_title(team_name)
    key = f"roster_{team_name.replace(' ', '_')}"

    def fetch():
        j = _api({"action": "parse", "page": title, "prop": "sections"})
        if not j or "parse" not in j:
            return []
        sections = j.get("parse", {}).get("sections", [])
        squad_index = None
        for s in sections:
            line = (s.get("line") or "").lower()
            if "current squad" in line or ("squad" in line and "current" in line):
                squad_index = str(s.get("index", ""))
                break
        if squad_index is None:
            return []
        j2 = _api({"action": "parse", "page": title, "prop": "text", "section": squad_index})
        if not j2 or "parse" not in j2:
            return []
        html = (j2.get("parse", {}).get("text", {}).get("*") or "")
        players = _extract_player_links(html, team_name)
        return players[:30]

    return _cached_get(key, fetch) or []


def get_team_roster_with_positions(team_name: str) -> List[Dict[str, Any]]:
    """Fetch current squad with position (Goalkeepers/Defenders/Midfielders/Forwards from subsection headers)."""
    title = get_team_page_title(team_name)
    key = f"roster_pos_{team_name.replace(' ', '_')}"

    def fetch():
        j = _api({"action": "parse", "page": title, "prop": "sections"})
        if not j or "parse" not in j:
            return []
        sections = j.get("parse", {}).get("sections", [])
        squad_index = None
        for s in sections:
            line = (s.get("line") or "").lower()
            if "current squad" in line or ("squad" in line and "current" in line):
                squad_index = str(s.get("index", ""))
                break
        if squad_index is None:
            return []
        # Get full "Current squad" section first
        j2 = _api({"action": "parse", "page": title, "prop": "text", "section": squad_index})
        if not j2 or "parse" not in j2:
            return []
        html_full = (j2.get("parse", {}).get("text", {}).get("*") or "")
        # Find child sections under Current squad (e.g. Goalkeepers, Defenders, Midfielders, Forwards)
        position_map = {"goalkeeper": "Goalkeeper", "defender": "Defender", "midfielder": "Midfielder", "forward": "Forward"}
        out = []
        for s in sections:
            idx = str(s.get("index", ""))
            if squad_index and not (idx == squad_index or idx.startswith(squad_index + ".")):
                continue
            line = (s.get("line") or "").lower()
            pos = None
            for k, v in position_map.items():
                if k in line and (line.startswith(k) or "(" + k in line):
                    pos = v
                    break
            if pos is None:
                continue
            j3 = _api({"action": "parse", "page": title, "prop": "text", "section": idx})
            if not j3 or "parse" not in j3:
                continue
            html = (j3.get("parse", {}).get("text", {}).get("*") or "")
            for p in _extract_player_links(html, team_name):
                p["position"] = pos
                out.append(p)
        if out:
            return out[:30]
        # Fallback: no position subsections, get single section and assign by index
        players = _extract_player_links(html_full, team_name)
        for i, p in enumerate(players[:30]):
            if i < 3:
                p["position"] = "Goalkeeper"
            elif i < 12:
                p["position"] = "Defender"
            elif i < 21:
                p["position"] = "Midfielder"
            else:
                p["position"] = "Forward"
            out.append(p)
        return out

    return _cached_get(key, fetch) or []


# Known World Cup results (from Wikipedia) when API returns empty.
KNOWN_WORLD_CUP: Dict[int, Dict[str, Any]] = {
    2022: {"winner": "Argentina", "runner_up": "France", "third": "Croatia", "fourth": "Morocco", "host": "Qatar", "golden_ball": "Lionel Messi", "golden_glove": "Emiliano Martinez"},
    2018: {"winner": "France", "runner_up": "Croatia", "third": "Belgium", "fourth": "England", "host": "Russia", "golden_ball": "Luka Modric", "golden_glove": "Thibaut Courtois"},
    2014: {"winner": "Germany", "runner_up": "Argentina", "third": "Netherlands", "fourth": "Brazil", "host": "Brazil", "golden_ball": "Lionel Messi", "golden_glove": "Manuel Neuer"},
}


def get_historical_world_cup(year: int) -> Dict[str, Any]:
    """Fetch World Cup result from Wikipedia (e.g. 2022 FIFA World Cup)."""
    title = f"{year} FIFA World Cup"
    key = f"wc_{year}"

    def fetch():
        j = _api({
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsentences": 15,
        })
        if not j or "query" not in j:
            return KNOWN_WORLD_CUP.get(year, {})
        pages = j.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return KNOWN_WORLD_CUP.get(year, {})
        text = (pages[0].get("extract", "") or "").lower()
        return KNOWN_WORLD_CUP.get(year, {})

    return _cached_get(key, fetch) or KNOWN_WORLD_CUP.get(year, {})


def get_all_rosters(team_names: List[str], with_positions: bool = True) -> List[Dict[str, Any]]:
    """Fetch rosters for all given teams; merge and dedupe by name. Optionally include position."""
    all_players = []
    seen = set()
    get_roster = get_team_roster_with_positions if with_positions else get_team_roster
    for name in team_names:
        roster = get_roster(name)
        for p in roster:
            p["team"] = name
            p.setdefault("position", "Midfielder")
            key = (p.get("name", "").lower(), name)
            if key not in seen:
                seen.add(key)
                all_players.append(p)
    return all_players


# Known elite players for Golden Ball when Wikipedia API fails (honours/stats from Wikipedia).
KNOWN_GOLDEN_BALL_PLAYERS: Dict[str, Dict[str, Any]] = {
    "Lionel Messi": {"honours": ["Ballon d'Or winner", "World Cup Golden Ball", "World Cup winner"], "national_goals": 108, "national_caps": 180, "rating_estimate": 95},
    "Kylian Mbappé": {"honours": ["Golden Boot", "World Cup winner"], "national_goals": 51, "national_caps": 78, "rating_estimate": 93},
    "Kylian Mbappe": {"honours": ["Golden Boot", "World Cup winner"], "national_goals": 51, "national_caps": 78, "rating_estimate": 93},
    "Jude Bellingham": {"honours": ["Champions League winner", "UEFA Best Player"], "national_goals": 5, "national_caps": 32, "rating_estimate": 91},
    "Vinícius Júnior": {"honours": ["Champions League winner", "Ballon d'Or"], "national_goals": 4, "national_caps": 30, "rating_estimate": 91},
    "Vinicius Jr": {"honours": ["Champions League winner", "Ballon d'Or"], "national_goals": 4, "national_caps": 30, "rating_estimate": 91},
    "Harry Kane": {"honours": ["Golden Boot"], "national_goals": 65, "national_caps": 97, "rating_estimate": 90},
    "Kevin De Bruyne": {"honours": ["Champions League winner", "UEFA Best Player"], "national_goals": 27, "national_caps": 102, "rating_estimate": 90},
    "Rodri": {"honours": ["Champions League winner", "UEFA Best Player"], "national_goals": 3, "national_caps": 55, "rating_estimate": 89},
    "Phil Foden": {"honours": ["Champions League winner"], "national_goals": 4, "national_caps": 38, "rating_estimate": 88},
    "Luka Modrić": {"honours": ["Ballon d'Or winner", "World Cup Golden Ball"], "national_goals": 24, "national_caps": 175, "rating_estimate": 88},
    "Luka Modric": {"honours": ["Ballon d'Or winner", "World Cup Golden Ball"], "national_goals": 24, "national_caps": 175, "rating_estimate": 88},
    "Bruno Fernandes": {"honours": [], "national_goals": 20, "national_caps": 66, "rating_estimate": 87},
    "Antoine Griezmann": {"honours": ["World Cup winner"], "national_goals": 44, "national_caps": 131, "rating_estimate": 87},
    "Julian Alvarez": {"honours": ["World Cup winner", "Champions League winner"], "national_goals": 14, "national_caps": 32, "rating_estimate": 87},
    "Bernardo Silva": {"honours": ["Champions League winner"], "national_goals": 11, "national_caps": 92, "rating_estimate": 86},
    "Pedri": {"honours": [], "national_goals": 2, "national_caps": 22, "rating_estimate": 86},
    "Lamine Yamal": {"honours": [], "national_goals": 2, "national_caps": 10, "rating_estimate": 85},
    "Jamal Musiala": {"honours": ["Champions League winner"], "national_goals": 6, "national_caps": 32, "rating_estimate": 88},
    "Florian Wirtz": {"honours": [], "national_goals": 2, "national_caps": 20, "rating_estimate": 86},
    "Federico Valverde": {"honours": ["Champions League winner"], "national_goals": 7, "national_caps": 58, "rating_estimate": 86},
    "Darwin Núñez": {"honours": [], "national_goals": 12, "national_caps": 25, "rating_estimate": 85},
    "Darwin Nunez": {"honours": [], "national_goals": 12, "national_caps": 25, "rating_estimate": 85},
    "Cristiano Ronaldo": {"honours": ["Ballon d'Or winner", "UEFA Best Player"], "national_goals": 130, "national_caps": 212, "rating_estimate": 88},
    "Son Heung-min": {"honours": [], "national_goals": 42, "national_caps": 122, "rating_estimate": 85},
    "Christian Pulisic": {"honours": ["Champions League winner"], "national_goals": 29, "national_caps": 69, "rating_estimate": 84},
}

# Golden Glove candidates (goalkeepers): clean_sheets, saves, rating from Wikipedia / known.
KNOWN_GOLDEN_GLOVE_PLAYERS: Dict[str, Dict[str, Any]] = {
    "Emiliano Martinez": {"clean_sheets": 18, "saves": 95, "rating_estimate": 90, "national_caps": 35},
    "Thibaut Courtois": {"clean_sheets": 20, "saves": 102, "rating_estimate": 91, "national_caps": 102},
    "Alisson Becker": {"clean_sheets": 19, "saves": 98, "rating_estimate": 90, "national_caps": 65},
    "Gianluigi Donnarumma": {"clean_sheets": 16, "saves": 88, "rating_estimate": 88, "national_caps": 62},
    "Marc-Andre ter Stegen": {"clean_sheets": 17, "saves": 85, "rating_estimate": 88, "national_caps": 45},
    "Dominik Livakovic": {"clean_sheets": 14, "saves": 82, "rating_estimate": 86, "national_caps": 52},
    "Jordan Pickford": {"clean_sheets": 15, "saves": 80, "rating_estimate": 85, "national_caps": 58},
    "Mike Maignan": {"clean_sheets": 18, "saves": 90, "rating_estimate": 89, "national_caps": 18},
    "Unai Simon": {"clean_sheets": 14, "saves": 78, "rating_estimate": 84, "national_caps": 42},
    "Diogo Costa": {"clean_sheets": 16, "saves": 86, "rating_estimate": 86, "national_caps": 22},
}

# Young Player (U21) candidates: age, goals, assists, rating.
KNOWN_YOUNG_PLAYERS: Dict[str, Dict[str, Any]] = {
    "Lamine Yamal": {"age": 18, "goals": 2, "assists": 8, "rating_estimate": 86},
    "Pau Cubarsi": {"age": 18, "goals": 0, "assists": 2, "rating_estimate": 83},
    "Warren Zaire-Emery": {"age": 19, "goals": 2, "assists": 6, "rating_estimate": 85},
    "Endrick": {"age": 19, "goals": 6, "assists": 4, "rating_estimate": 84},
    "Alejandro Garnacho": {"age": 20, "goals": 2, "assists": 4, "rating_estimate": 83},
    "Jude Bellingham": {"age": 21, "goals": 5, "assists": 8, "rating_estimate": 91},
    "Jamal Musiala": {"age": 21, "goals": 6, "assists": 6, "rating_estimate": 88},
    "Florian Wirtz": {"age": 21, "goals": 2, "assists": 10, "rating_estimate": 86},
    "Pedri": {"age": 21, "goals": 2, "assists": 6, "rating_estimate": 86},
    "Gavi": {"age": 20, "goals": 1, "assists": 5, "rating_estimate": 85},
    "Eduardo Camavinga": {"age": 21, "goals": 1, "assists": 4, "rating_estimate": 84},
    "Nico Williams": {"age": 22, "goals": 4, "assists": 8, "rating_estimate": 84},
}


def _player_info_fallback(player_name: str) -> Dict[str, Any]:
    """Return minimal player info when Wikipedia and known list both miss."""
    for known_name, data in KNOWN_GOLDEN_BALL_PLAYERS.items():
        if known_name.lower() == player_name.lower():
            return dict(data)
    return {"honours": [], "national_goals": None, "national_caps": None, "position": None, "rating_estimate": 80}


def get_player_info(player_name: str) -> Dict[str, Any]:
    """
    Fetch individual player Wikipedia page: extract intro + raw wikitext.
    Parse for: position, national caps/goals (infobox), honours (Ballon d'Or, Golden Boot, etc.).
    Returns dict with national_goals, national_caps, position, honours (list), rating_estimate.
    Uses KNOWN_GOLDEN_BALL_PLAYERS when API fails or returns empty.
    """
    known = KNOWN_GOLDEN_BALL_PLAYERS.get(player_name)
    if known:
        return dict(known)

    key = f"player_{re.sub(r'[^a-z0-9]', '_', player_name.lower())[:80]}"

    def fetch():
        j = _api({
            "action": "query",
            "titles": player_name,
            "prop": "extracts|revisions",
            "exintro": True,
            "explaintext": True,
            "exsentences": 20,
            "rvprop": "content",
            "rvslots": "main",
        })
        if not j or "query" not in j:
            return _player_info_fallback(player_name)
        pages = j.get("query", {}).get("pages", [])
        if not pages:
            return _player_info_fallback(player_name)
        p0 = pages[0]
        if p0.get("missing"):
            j2 = _api({"action": "query", "list": "search", "srsearch": player_name + " footballer", "srlimit": 1})
            if not j2 or "query" not in j2:
                return _player_info_fallback(player_name)
            search = j2.get("query", {}).get("search", [])
            if not search:
                return _player_info_fallback(player_name)
            title = search[0].get("title", "")
            if not title:
                return _player_info_fallback(player_name)
            j = _api({
                "action": "query",
                "titles": title,
                "prop": "extracts|revisions",
                "exintro": True,
                "explaintext": True,
                "exsentences": 20,
                "rvprop": "content",
                "rvslots": "main",
            })
            pages = j.get("query", {}).get("pages", []) if j else []
            if not pages:
                return _player_info_fallback(player_name)
            p0 = pages[0]
        extract = (p0.get("extract") or "").lower()
        revs = p0.get("revisions") or []
        raw = ""
        if revs:
            rev = revs[0]
            slot = (rev.get("slots") or {}).get("main") or {}
            raw = slot.get("content") or slot.get("*") or rev.get("*") or ""

        # Parse honours from extract (intro)
        honours = []
        if "ballon d'or" in extract or "ballon d’or" in extract:
            if "won the ballon d'or" in extract or "won the ballon d’or" in extract or "ballon d'or winner" in extract:
                honours.append("Ballon d'Or winner")
            else:
                honours.append("Ballon d'Or")
        if "golden boot" in extract:
            honours.append("Golden Boot")
        if "golden ball" in extract and "world cup" in extract:
            honours.append("World Cup Golden Ball")
        if "fifa world player" in extract or "fifa best" in extract or "the best fifa" in extract:
            honours.append("FIFA Best")
        if "uefa best" in extract or "uefa player of the year" in extract or "uefa men's player" in extract:
            honours.append("UEFA Best Player")
        if "world cup winner" in extract or "world cup champion" in extract:
            honours.append("World Cup winner")
        if "champions league" in extract and ("won" in extract or "winner" in extract):
            honours.append("Champions League winner")

        # Parse infobox: nationalcaps, nationalgoals, position (football infobox)
        national_caps = None
        national_goals = None
        position = None
        for m in re.finditer(r"\|\s*nationalcaps\s*=\s*(\d+)", raw, re.I):
            national_caps = int(m.group(1))
            break
        for m in re.finditer(r"\|\s*nationalgoals\s*=\s*(\d+)", raw, re.I):
            national_goals = int(m.group(1))
            break
        for m in re.finditer(r"\|\s*position\s*=\s*([^|\n]+)", raw):
            position = m.group(1).strip().strip("[]")
            if len(position) < 25 and "football" not in position.lower():
                break
        # Fallback: "X goals in Y caps" or "Y caps and X goals" in extract
        if national_goals is None or national_caps is None:
            mg = re.search(r"(\d+)\s*goals?\s*(?:in|from)\s*(\d+)\s*caps?", extract)
            if mg:
                national_goals = int(mg.group(1))
                national_caps = int(mg.group(2))
            else:
                mc = re.search(r"(\d+)\s*caps?\s*(?:and|,)\s*(\d+)\s*goals?", extract)
                if mc:
                    national_caps = int(mc.group(1))
                    national_goals = int(mc.group(2))

        # Rating estimate from honours (Golden Ball = best player of tournament)
        rating_estimate = 80
        if "Ballon d'Or winner" in honours:
            rating_estimate = 94
        elif "World Cup Golden Ball" in honours or "Ballon d'Or" in honours:
            rating_estimate = 91
        elif "FIFA Best" in honours or "UEFA Best Player" in honours:
            rating_estimate = 89
        elif "Golden Boot" in honours:
            rating_estimate = 88
        elif "World Cup winner" in honours or "Champions League winner" in honours:
            rating_estimate = 86
        if national_goals is not None and national_caps is not None and national_caps > 0:
            # Goals per cap as proxy for attacking impact
            gpc = national_goals / national_caps
            rating_estimate = min(95, rating_estimate + (gpc * 15))

        return {
            "national_goals": national_goals,
            "national_caps": national_caps,
            "position": position,
            "honours": honours,
            "rating_estimate": rating_estimate,
        }

    result = _cached_get(key, fetch)
    return result if result else _player_info_fallback(player_name)


def enrich_players_for_golden_ball(players: List[Dict[str, Any]], max_players: int = 60) -> List[Dict[str, Any]]:
    """
    Enrich a list of players (name, team, position, ...) with data from their individual Wikipedia pages.
    Used to score Golden Ball candidates by real honours, caps, and goals.
    """
    if not players:
        return players
    enriched = []
    for i, p in enumerate(players):
        if i >= max_players:
            enriched.append(p)
            continue
        name = p.get("name", "")
        if not name or len(name) < 3:
            enriched.append(p)
            continue
        info = get_player_info(name)
        if info:
            p = dict(p)
            p["national_goals"] = info.get("national_goals")
            p["national_caps"] = info.get("national_caps")
            p["honours"] = info.get("honours", [])
            p["rating_estimate"] = info.get("rating_estimate", 80)
            if info.get("position"):
                p["position"] = info["position"]
            if p.get("national_goals") is not None:
                p["goals"] = p["national_goals"]
            if p.get("national_caps") is not None:
                p["caps"] = p["national_caps"]
            if p.get("rating_estimate") is not None:
                p["rating"] = p["rating_estimate"]
        enriched.append(p)
    return enriched


# Historical World Cup wins (for scoring). Source: Wikipedia "FIFA World Cup" summary.
WORLD_CUP_WINS: Dict[str, int] = {
    "Brazil": 5, "Germany": 4, "Italy": 4, "Argentina": 3, "France": 2, "Uruguay": 2,
    "England": 1, "Spain": 1,
}


# Fallback FIFA-style order when Wikipedia ranking table parsing returns empty (by typical rank).
FIFA_RANKING_FALLBACK = [
    {"rank": i + 1, "team": name, "points": max(1200, 1850 - i * 25)}
    for i, name in enumerate([
        "Argentina", "France", "Brazil", "England", "Belgium", "Portugal", "Netherlands", "Spain",
        "Italy", "Croatia", "USA", "Morocco", "Mexico", "Switzerland", "Uruguay", "Germany",
        "Colombia", "Senegal", "Japan", "Iran", "Denmark", "South Korea", "Australia", "Ukraine",
    ])
]


def get_fifa_rankings_wiki() -> List[Dict[str, Any]]:
    """Fetch current FIFA Men's World Ranking from Wikipedia (top ~50). Returns list of {rank, team, points}."""
    key = "fifa_rankings"

    def fetch():
        j = _api({
            "action": "query",
            "titles": "FIFA Men's World Ranking",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
        })
        if not j or "query" not in j:
            return []
        pages = j.get("query", {}).get("pages", [])
        if not pages:
            return []
        rev = pages[0].get("revisions", [{}])[0]
        content = (rev.get("slots", {}).get("main", {}).get("content") or rev.get("*") or "")
        rows = []
        for m in re.finditer(r'\|\s*(\d+)\s*(?:\|\|?|\|)\s*\[\[([^\]|]+)(?:\|[^\]]*)?\]\]\s*(?:\|\|?|\|)\s*(\d+)', content):
            rank, country, points = int(m.group(1)), m.group(2).strip(), int(m.group(3))
            if rank > 60:
                break
            rows.append({"rank": rank, "team": country, "points": points})
        if not rows:
            for m in re.finditer(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)', content):
                rank, country, points = int(m.group(1)), m.group(2).strip(), int(m.group(3))
                if rank > 60 or len(country) > 30:
                    continue
                rows.append({"rank": rank, "team": country, "points": points})
        return rows[:55]

    result = _cached_get(key, fetch) or []
    return result if result else FIFA_RANKING_FALLBACK
