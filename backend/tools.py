"""
Tool/API Actions for World Cup 2026 Prediction Workflow

All data is API-driven from Wikipedia: qualified teams, rosters, historical results, FIFA rankings.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from . import wikipedia as wiki
except ImportError:
    wiki = None

# Confederations for qualified teams (aligned with 2026 qualification zones)
CONFEDERATION_BY_TEAM: Dict[str, str] = {
    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Uruguay": "CONMEBOL", "Colombia": "CONMEBOL",
    "Ecuador": "CONMEBOL", "Paraguay": "CONMEBOL", "USA": "CONCACAF", "Mexico": "CONCACAF",
    "Canada": "CONCACAF", "Panama": "CONCACAF", "Haiti": "CONCACAF", "Curaçao": "CONCACAF",
    "France": "UEFA", "England": "UEFA", "Spain": "UEFA", "Germany": "UEFA", "Netherlands": "UEFA",
    "Portugal": "UEFA", "Belgium": "UEFA", "Croatia": "UEFA", "Norway": "UEFA", "Austria": "UEFA",
    "Switzerland": "UEFA", "Scotland": "UEFA", "Italy": "UEFA",
    "Japan": "AFC", "South Korea": "AFC", "Australia": "AFC", "Iran": "AFC", "Uzbekistan": "AFC",
    "Jordan": "AFC", "Saudi Arabia": "AFC", "Qatar": "AFC", "New Zealand": "OFC",
    "Morocco": "CAF", "Senegal": "CAF", "Tunisia": "CAF", "Egypt": "CAF", "Algeria": "CAF",
    "Ghana": "CAF", "Cape Verde": "CAF", "South Africa": "CAF", "Ivory Coast": "CAF",
}
HOSTS_2026 = {"USA", "Mexico", "Canada"}

# Fallback Golden Ball candidates (name -> team) when rosters are empty.
GOLDEN_BALL_FALLBACK_NAMES = [
    ("Lionel Messi", "Argentina"), ("Kylian Mbappe", "France"), ("Jude Bellingham", "England"),
    ("Vinicius Jr", "Brazil"), ("Harry Kane", "England"), ("Kevin De Bruyne", "Belgium"),
    ("Rodri", "Spain"), ("Phil Foden", "England"), ("Luka Modric", "Croatia"),
    ("Bruno Fernandes", "Portugal"), ("Antoine Griezmann", "France"), ("Julian Alvarez", "Argentina"),
    ("Jamal Musiala", "Germany"), ("Pedri", "Spain"), ("Cristiano Ronaldo", "Portugal"),
]
# Golden Boot: forwards with high goal totals.
GOLDEN_BOOT_FALLBACK_NAMES = [
    ("Cristiano Ronaldo", "Portugal"), ("Lionel Messi", "Argentina"), ("Harry Kane", "England"),
    ("Kylian Mbappe", "France"), ("Romelu Lukaku", "Belgium"), ("Darwin Nunez", "Uruguay"),
    ("Julian Alvarez", "Argentina"), ("Son Heung-min", "South Korea"), ("Christian Pulisic", "USA"),
    ("Cody Gakpo", "Netherlands"), ("Memphis Depay", "Netherlands"), ("Alvaro Morata", "Spain"),
]
# Golden Glove: top goalkeepers.
GOLDEN_GLOVE_FALLBACK_NAMES = [
    ("Emiliano Martinez", "Argentina"), ("Thibaut Courtois", "Belgium"), ("Alisson Becker", "Brazil"),
    ("Mike Maignan", "France"), ("Dominik Livakovic", "Croatia"), ("Jordan Pickford", "England"),
    ("Gianluigi Donnarumma", "Italy"), ("Marc-Andre ter Stegen", "Germany"), ("Diogo Costa", "Portugal"),
    ("Unai Simon", "Spain"),
]
# Young Player: U21 / emerging stars.
YOUNG_PLAYER_FALLBACK_NAMES = [
    ("Lamine Yamal", "Spain"), ("Jude Bellingham", "England"), ("Jamal Musiala", "Germany"),
    ("Warren Zaire-Emery", "France"), ("Endrick", "Brazil"), ("Pau Cubarsi", "Spain"),
    ("Florian Wirtz", "Germany"), ("Pedri", "Spain"), ("Alejandro Garnacho", "Argentina"),
    ("Gavi", "Spain"), ("Eduardo Camavinga", "France"), ("Nico Williams", "Spain"),
]


class Tools:
    """Tool/API actions. All team and player data from Wikipedia."""

    WEIGHTS_TEAM = {"fifa_ranking": 0.25, "historical": 0.20, "recent_form": 0.25, "squad_strength": 0.20, "home_advantage": 0.10}

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._teams_list: Optional[List[Dict[str, Any]]] = None
        self._teams_by_name: Optional[Dict[str, Dict[str, Any]]] = None

    def _ensure_teams(self) -> None:
        """Build team list and lookup from Wikipedia (qualified teams + FIFA ranking + 2022 result)."""
        if self._teams_list is not None:
            return
        if not wiki:
            self._teams_list = []
            self._teams_by_name = {}
            return
        qualified = wiki.get_qualified_teams_2026()
        if not qualified:
            self._teams_list = []
            self._teams_by_name = {}
            return
        last_wc = wiki.get_historical_world_cup(2022)
        fifa_rows = wiki.get_fifa_rankings_wiki()
        fifa_by_team: Dict[str, Dict[str, Any]] = {}
        for r in fifa_rows:
            name = (r.get("team") or "").strip()
            if name:
                fifa_by_team[name] = {"rank": r.get("rank", 99), "points": r.get("points", 1200)}
        # Normalize FIFA team names to match qualified (e.g. "United States" -> "USA")
        for k, v in list(fifa_by_team.items()):
            if k == "United States":
                fifa_by_team["USA"] = v
            if k == "Korea Republic" or k == "South Korea":
                fifa_by_team["South Korea"] = fifa_by_team.get("South Korea") or v
            if k == "Côte d'Ivoire":
                fifa_by_team["Ivory Coast"] = fifa_by_team.get("Ivory Coast") or v

        teams_list = []
        for i, t in enumerate(qualified):
            name = t.get("name") or ""
            code = t.get("code") or name[:3].upper()
            info = wiki.get_team_info(name)
            flag = info.get("flag") or wiki.FLAG_BY_CODE.get(code, "")
            conf = CONFEDERATION_BY_TEAM.get(name, "UEFA")
            home = name in HOSTS_2026
            wc_wins = wiki.WORLD_CUP_WINS.get(name, 0)
            # last_world_cup from 2022 result
            if last_wc.get("winner") == name:
                last_str = "2022 (Winners)"
            elif last_wc.get("runner_up") == name:
                last_str = "2022 (Finalists)"
            elif last_wc.get("third") == name:
                last_str = "2022 (Third Place)"
            elif last_wc.get("fourth") == name:
                last_str = "2022 (Fourth Place)"
            else:
                last_str = "2022 (Group Stage)"
            fifa = fifa_by_team.get(name) or {}
            rank = fifa.get("rank", i + 1)
            points = fifa.get("points", max(0, 1800 - rank * 25))
            ovr = max(70, min(90, 88 - (rank - 1) * 0.4))
            rec = {
                "name": name, "code": code, "flag": flag, "fifa_rank": rank, "fifa_points": points,
                "world_cup_wins": wc_wins, "last_world_cup": last_str, "home_advantage": home,
                "confederation": conf, "ovr_rating": round(ovr, 0),
            }
            teams_list.append(rec)
        # Sort by FIFA rank then by order
        teams_list.sort(key=lambda x: (x.get("fifa_rank", 99), -x.get("fifa_points", 0)))
        self._teams_list = teams_list
        self._teams_by_name = {t["name"]: t for t in teams_list}

    @property
    def WORLD_CUP_TEAMS(self) -> Dict[str, Dict[str, Any]]:
        """Dynamic team lookup from Wikipedia (for backward compatibility with workflow)."""
        self._ensure_teams()
        return self._teams_by_name or {}

    def get_team_names(self) -> List[str]:
        """List of qualified team names."""
        self._ensure_teams()
        return [t["name"] for t in (self._teams_list or [])]

    def fetch_fifa_rankings(self) -> Dict[str, Any]:
        """Get current team rankings from Wikipedia (qualified teams + FIFA ranking data)."""
        self._ensure_teams()
        teams = []
        for i, t in enumerate(self._teams_list or [], 1):
            teams.append({
                "rank": t.get("fifa_rank", i),
                "team": t["name"],
                "points": t.get("fifa_points", 1500),
                "confederation": t.get("confederation", "UEFA"),
                "crest": t.get("flag", ""),
                "shortName": t.get("code", t["name"][:3].upper()),
            })
        return {"result": f"Retrieved rankings for {len(teams)} qualified teams", "data": teams}

    def fetch_player_stats(self, position: str, for_golden_ball: bool = False) -> Dict[str, Any]:
        """Get player statistics by position from Wikipedia rosters (forwards, midfielders, goalkeepers, young).
        If for_golden_ball=True, only forwards+midfielders are fetched (no per-position filter) for later enrichment."""
        position = (position or "forwards").lower()
        self._ensure_teams()
        names = self.get_team_names()
        if not names or not wiki:
            return {"result": f"Retrieved 0 {position}", "data": []}
        all_players = wiki.get_all_rosters(names, with_positions=True)
        # Assign default stats for scoring (overwritten by individual Wikipedia pages when enriching)
        for p in all_players:
            pos = (p.get("position") or "Midfielder").lower()
            p.setdefault("goals", 4 if "forward" in pos else 2 if "mid" in pos else 0)
            p.setdefault("assists", 3 if "forward" in pos or "mid" in pos else 0)
            p.setdefault("rating", 82 if "goalkeeper" in pos else 81 if "forward" in pos else 79)
            p.setdefault("clean_sheets", 12 if "goalkeeper" in pos else 0)
            p.setdefault("saves", 80 if "goalkeeper" in pos else 0)
            p.setdefault("age", 26)
            team_info = self.WORLD_CUP_TEAMS.get(p.get("team", ""), {})
            p["crest"] = team_info.get("flag", "")
        if for_golden_ball:
            # Return forwards + midfielders only (Golden Ball typically goes to attackers/playmakers)
            players = [p for p in all_players if "goalkeeper" not in (p.get("position") or "").lower()]
            return {"result": f"Retrieved {len(players)} candidates for Golden Ball", "data": players}
        if position == "goalkeepers":
            players = [p for p in all_players if "goalkeeper" in (p.get("position") or "").lower()]
        elif position == "midfielders":
            players = [p for p in all_players if "midfielder" in (p.get("position") or "").lower()]
        elif position in ("young", "u21"):
            players = [p for p in all_players if (p.get("age") or 22) < 22]
            if not players:
                players = all_players[:20]
        else:
            players = [p for p in all_players if "forward" in (p.get("position") or "").lower()]
        return {"result": f"Retrieved {len(players)} {position}", "data": players}

    def fetch_historical_data(self, tournament: str = "World Cup") -> Dict[str, Any]:
        """Get past World Cup results from Wikipedia (2014, 2018, 2022)."""
        if not wiki:
            return {"result": "No Wikipedia client", "data": {}}
        historical = {
            "2022": wiki.get_historical_world_cup(2022),
            "2018": wiki.get_historical_world_cup(2018),
            "2014": wiki.get_historical_world_cup(2014),
        }
        return {"result": "Processed data from 2014, 2018, 2022 tournaments", "data": historical}

    def analyze_team_form(self, teams: List[str]) -> Dict[str, Any]:
        """Analyze recent form from last World Cup performance (using Wikipedia historical data)."""
        self._ensure_teams()
        if not teams:
            teams = self.get_team_names()[:15]
        form_data = {}
        for name in teams:
            info = self.WORLD_CUP_TEAMS.get(name, {})
            last = info.get("last_world_cup", "")
            if "Winner" in last or "Final" in last:
                form = "Excellent"
            elif "Semi" in last or "Third" in last or "Fourth" in last:
                form = "Very Good"
            elif "Quarter" in last:
                form = "Good"
            elif "Round of 16" in last:
                form = "Average"
            else:
                form = "Poor"
            form_data[name] = {"form": form, "last_world_cup": last}
        return {"result": f"Analyzed form for {len(teams)} teams", "data": form_data}

    def calculate_predictions(self, data: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Team winner prediction using FIFA, historical, form, squad, home. Returns top 5 with probabilities."""
        weights = weights or self.WEIGHTS_TEAM
        teams = data.get("teams") or data.get("data") or []
        if not teams and isinstance(data, list):
            teams = data
        if not teams:
            self._ensure_teams()
            teams = [
                {"team": t["name"], "rank": t.get("fifa_rank", i), "points": t.get("fifa_points", 1500),
                 "world_cup_wins": t.get("world_cup_wins", 0), "ovr_rating": t.get("ovr_rating", 80),
                 "home_advantage": t.get("home_advantage", False), "last_world_cup": t.get("last_world_cup", "")}
                for i, t in enumerate(self._teams_list or [], 1)
            ]
        max_rank = max((t.get("rank") or 0) for t in teams) or 32
        scores = []
        for t in teams:
            name = t.get("team", "Unknown")
            info = self.WORLD_CUP_TEAMS.get(name, {})
            rank = t.get("rank") or info.get("fifa_rank", 0)
            points = t.get("points") or info.get("fifa_points", 1500)
            wc_wins = t.get("world_cup_wins") if "world_cup_wins" in t else info.get("world_cup_wins", 0)
            squad = t.get("ovr_rating") or t.get("squad_rating") or info.get("ovr_rating", 80)
            home = t.get("home_advantage") if "home_advantage" in t else info.get("home_advantage", False)
            last_wc = t.get("last_world_cup") or info.get("last_world_cup", "")
            fifa_score = (1 - (rank - 1) / max(max_rank, 1)) * 100
            hist_score = min(100, wc_wins * 20 + 20)
            form_score = 80 if "Winner" in last_wc or "Final" in last_wc else 60 if "Semi" in last_wc or "Third" in last_wc or "Fourth" in last_wc else 40 if "Quarter" in last_wc else 20
            squad_score = max(0, min(100, (squad - 70) * 2.5))
            home_score = 100 if home else 0
            total = fifa_score * weights.get("fifa_ranking", 0.25) + hist_score * weights.get("historical", 0.20) + form_score * weights.get("recent_form", 0.25) + squad_score * weights.get("squad_strength", 0.20) + home_score * weights.get("home_advantage", 0.10)
            total = max(0, min(100, total * 0.35))
            crest = info.get("flag", t.get("crest", ""))
            scores.append({"team": name, "score": round(total, 1), "crest": crest, "shortName": info.get("code", name[:3].upper()), "factors": {"fifa": fifa_score, "historical": hist_score, "form": form_score, "squad": squad_score, "home": home_score}})
        scores.sort(key=lambda x: x["score"], reverse=True)
        total_sum = sum(s["score"] for s in scores[:5]) or 1
        for i, s in enumerate(scores[:5]):
            s["probability"] = round(100 * s["score"] / total_sum, 1)
            s["description"], s["reason"] = self._team_prediction_description_reason(s, i + 1)
        result = {str(i + 1): scores[i] for i in range(min(5, len(scores)))}
        return {"result": "Computed weighted scores for all teams", "data": result, "top5": scores[:5]}

    def _team_prediction_description_reason(self, s: Dict[str, Any], rank: int) -> tuple:
        """Return (description, reason) for a team prediction (interpretable)."""
        name = s.get("team", "Unknown")
        info = self.WORLD_CUP_TEAMS.get(name, {})
        last_wc = info.get("last_world_cup", "")
        wc_wins = info.get("world_cup_wins", 0)
        fifa_rank = info.get("fifa_rank", rank)
        f = s.get("factors") or {}
        prob = s.get("probability", 0)
        desc = f"{name} – {last_wc}; {wc_wins} World Cup wins, FIFA rank #{fifa_rank}."
        reason = f"FIFA rank (25%): {f.get('fifa', 0):.0f}, Historical (20%): {f.get('historical', 0):.0f}, Recent form (25%): {f.get('form', 0):.0f}, Squad (20%): {f.get('squad', 0):.0f}, Home (10%): {f.get('home', 0):.0f}. Weighted total → {prob}%."
        return desc, reason

    def generate_report(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Create formatted output for display and file."""
        top5 = predictions.get("top5") or list(predictions.get("data", predictions).values())[:5] if isinstance(predictions.get("data"), dict) else []
        if not top5 and isinstance(predictions, dict):
            top5 = [predictions.get(k) for k in sorted(predictions.keys())[:5] if isinstance(predictions.get(k), dict)]
        report = {
            "predictions": {str(i + 1): top5[i] for i in range(len(top5))},
            "key_factors": ["FIFA ranking (25%)", "Historical performance (20%)", "Recent form (25%)", "Squad strength (20%)", "Home advantage (10%)"],
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return {"result": "Report generated", "data": report}

    def save_to_file(self, filename: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Write results to a JSON file in predictions/."""
        out_dir = Path("predictions")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
        return {"result": f"Report saved to {path}", "data": {"filename": str(path)}}

    def create_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple chart/table data for UI."""
        top5 = data.get("top5") or []
        if not top5 and isinstance(data.get("predictions"), dict):
            top5 = list(data["predictions"].values())
        labels = [item.get("team", item.get("name", "?")) for item in top5[:5]]
        values = [item.get("probability", item.get("score", 0)) for item in top5[:5]]
        return {"result": "Visualization data ready", "data": {"labels": labels, "values": values, "type": "bar"}}

    def calculate_player_predictions(self, players: List[Dict], award_type: str) -> Dict[str, Any]:
        """Score players for Golden Ball / Golden Boot / Golden Glove / Young Player. Returns top 5 with probability, description, reason. Crest from team flag."""
        if not players or len(players) < 5:
            if award_type == "golden_ball" and wiki:
                players = self._golden_ball_fallback_candidates()
            elif award_type == "golden_boot" and wiki:
                players = self._golden_boot_fallback_candidates()
            elif award_type == "golden_glove" and wiki:
                players = self._golden_glove_fallback_candidates()
            elif award_type == "young_player" and wiki:
                players = self._young_player_fallback_candidates()
        if not players:
            return {"result": "No players to score", "data": {}, "top5": []}
        if award_type == "golden_ball" and wiki:
            players = wiki.enrich_players_for_golden_ball(players, max_players=60)
        elif award_type == "golden_boot" and wiki:
            players = wiki.enrich_players_for_golden_ball(players, max_players=60)
        elif award_type == "golden_glove" and wiki:
            players = self._enrich_goalkeepers(players)
        elif award_type == "young_player" and wiki:
            players = self._enrich_young_players(players)
        scored = []
        for p in players:
            name = p.get("name", "Unknown")
            team = p.get("team", p.get("nationality", ""))
            crest = (self.WORLD_CUP_TEAMS.get(team, {}).get("flag", "") if team else "") or (p.get("crest") or "")
            if award_type == "golden_ball":
                s = self._score_golden_ball(p)
            elif award_type == "golden_boot":
                s = self._score_golden_boot(p)
            elif award_type == "golden_glove":
                s = self._score_golden_glove(p)
            else:
                s = self._score_young_player(p)
            extra = {}
            if award_type == "golden_boot":
                extra["goals"] = p.get("goals") or p.get("national_goals")
            elif award_type == "golden_glove":
                extra["clean_sheets"] = p.get("clean_sheets")
                extra["saves"] = p.get("saves")
            elif award_type == "young_player":
                extra["age"] = p.get("age")
                extra["goals"] = p.get("goals")
            scored.append({"name": name, "team": team, "score": round(s, 1), "crest": crest or "", "shortName": (team[:3].upper() if team else "?"), **extra})
        scored.sort(key=lambda x: x["score"], reverse=True)
        top5 = scored[:5]
        total = sum(x["score"] for x in top5) or 1
        for i, x in enumerate(top5):
            x["probability"] = round(100 * x["score"] / total, 1)
            x["description"], x["reason"] = self._player_prediction_description_reason(x, award_type, i + 1)
        data = {str(i + 1): top5[i] for i in range(len(top5))}
        return {"result": f"Computed {award_type} scores", "data": data, "top5": top5}

    def _golden_ball_fallback_candidates(self) -> List[Dict[str, Any]]:
        """Return list of known star players when rosters are empty."""
        self._ensure_teams()
        teams = self.WORLD_CUP_TEAMS
        return [{"name": n, "team": t, "crest": teams.get(t, {}).get("flag", "")} for n, t in GOLDEN_BALL_FALLBACK_NAMES if t in teams]

    def _golden_boot_fallback_candidates(self) -> List[Dict[str, Any]]:
        self._ensure_teams()
        teams = self.WORLD_CUP_TEAMS
        return [{"name": n, "team": t, "crest": teams.get(t, {}).get("flag", "")} for n, t in GOLDEN_BOOT_FALLBACK_NAMES if t in teams]

    def _golden_glove_fallback_candidates(self) -> List[Dict[str, Any]]:
        self._ensure_teams()
        teams = self.WORLD_CUP_TEAMS
        return [{"name": n, "team": t, "crest": teams.get(t, {}).get("flag", "")} for n, t in GOLDEN_GLOVE_FALLBACK_NAMES if t in teams]

    def _young_player_fallback_candidates(self) -> List[Dict[str, Any]]:
        self._ensure_teams()
        teams = self.WORLD_CUP_TEAMS
        return [{"name": n, "team": t, "crest": teams.get(t, {}).get("flag", "")} for n, t in YOUNG_PLAYER_FALLBACK_NAMES if t in teams]

    def _enrich_goalkeepers(self, players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge known keeper stats (clean_sheets, saves, rating) from Wikipedia module."""
        if not wiki:
            return players
        known = getattr(wiki, "KNOWN_GOLDEN_GLOVE_PLAYERS", {})
        out = []
        for p in players:
            p = dict(p)
            info = known.get(p.get("name", ""))
            if info:
                p["clean_sheets"] = info.get("clean_sheets", 12)
                p["saves"] = info.get("saves", 80)
                p["rating"] = info.get("rating_estimate", 85)
            p.setdefault("clean_sheets", 12)
            p.setdefault("saves", 80)
            p.setdefault("rating", 85)
            p["crest"] = (self.WORLD_CUP_TEAMS.get(p.get("team", ""), {}).get("flag", "") or p.get("crest", ""))
            out.append(p)
        return out

    def _enrich_young_players(self, players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge known young player stats (age, goals, assists, rating) from Wikipedia module."""
        if not wiki:
            return players
        known = getattr(wiki, "KNOWN_YOUNG_PLAYERS", {})
        out = []
        for p in players:
            p = dict(p)
            info = known.get(p.get("name", ""))
            if info:
                p["age"] = info.get("age", 21)
                p["goals"] = info.get("goals", 2)
                p["assists"] = info.get("assists", 4)
                p["rating"] = info.get("rating_estimate", 84)
            p.setdefault("age", 21)
            p.setdefault("goals", 2)
            p.setdefault("assists", 4)
            p.setdefault("rating", 84)
            p["crest"] = (self.WORLD_CUP_TEAMS.get(p.get("team", ""), {}).get("flag", "") or p.get("crest", ""))
            out.append(p)
        return out

    def _player_prediction_description_reason(self, item: Dict[str, Any], award_type: str, rank: int) -> tuple:
        """Return (description, reason) for a player prediction (interpretable)."""
        name = item.get("name", "Unknown")
        team = item.get("team", "")
        prob = item.get("probability", 0)
        score = item.get("score", 0)
        if award_type == "golden_ball":
            desc = f"{name} – {team}. Ballon d'Or / World Cup Golden Ball pedigree, top international goals and caps."
            reason = f"Ranked #{rank}: honours + rating + goals/assists. Score {score:.1f} → {prob}%."
        elif award_type == "golden_boot":
            goals = item.get("goals", "")
            desc = f"{name} – {team}. Elite forward" + (f", {goals} international goals." if goals is not None else ", high goal tally.")
            reason = f"Goals-based: international goals (80% weight), rating (20%). Score {score:.1f} → {prob}%."
        elif award_type == "golden_glove":
            cs = item.get("clean_sheets", "")
            sv = item.get("saves", "")
            desc = f"{name} – {team} goalkeeper" + (f". {cs} clean sheets, {sv} saves." if cs is not None and sv is not None else ". Strong record.")
            reason = f"Clean sheets (50%) + rating (50%). Score {score:.1f} → {prob}%."
        else:
            age = item.get("age", "")
            desc = f"{name} – {team}" + (f". Age {age}, high potential." if age is not None else ". Young standout, U21.")
            reason = f"Age (U21 bonus) + rating + goals/assists. Score {score:.1f} → {prob}%."
        return desc, reason

    def _score_golden_ball(self, p: Dict[str, Any]) -> float:
        """Score a player for Golden Ball using Wikipedia-enriched data: honours, caps, goals, rating."""
        honours = p.get("honours") or []
        rating = p.get("rating") or p.get("rating_estimate") or 80
        goals = p.get("goals") or p.get("national_goals") or 0
        caps = p.get("national_caps") or 0
        assists = p.get("assists") or 0
        honour_score = 0
        if "Ballon d'Or winner" in honours:
            honour_score = 95
        elif "World Cup Golden Ball" in honours or "Ballon d'Or" in honours:
            honour_score = 90
        elif "FIFA Best" in honours or "UEFA Best Player" in honours:
            honour_score = 85
        elif "Golden Boot" in honours:
            honour_score = 82
        elif "World Cup winner" in honours or "Champions League winner" in honours:
            honour_score = 78
        if honour_score > 0:
            return honour_score * 0.5 + rating * 0.25 + min(30, (goals or 0) * 0.3 + (assists or 0) * 0.2)
        return rating * 0.4 + (goals or 0) * 0.3 + (assists or 0) * 0.3

    def _score_golden_boot(self, p: Dict[str, Any]) -> float:
        """Score for Golden Boot: goals (80%), rating (20%). Uses national_goals when enriched."""
        goals = p.get("goals") or p.get("national_goals") or 0
        rating = p.get("rating") or p.get("rating_estimate") or 80
        return (goals or 0) * 0.8 + (rating or 80) * 0.2

    def _score_golden_glove(self, p: Dict[str, Any]) -> float:
        """Score for Golden Glove: clean_sheets (50%), rating (50%)."""
        cs = p.get("clean_sheets") or 0
        rating = p.get("rating") or p.get("rating_estimate") or 80
        return (cs or 0) * 0.5 + (rating or 80) * 0.5

    def _score_young_player(self, p: Dict[str, Any]) -> float:
        """Score for Young Player: age bonus (younger = higher) + rating + goals/assists."""
        age = p.get("age") or 22
        rating = p.get("rating") or p.get("rating_estimate") or 80
        goals = p.get("goals") or 0
        assists = p.get("assists") or 0
        age_bonus = max(0, (22 - age) * 3)  # U21: 3 pts per year under 22
        return age_bonus + (rating or 80) * 0.4 + (goals or 0) * 0.3 + (assists or 0) * 0.2
