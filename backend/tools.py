"""
Tool/API Actions for World Cup 2026 Prediction Workflow

Implements: fetch_fifa_rankings, fetch_player_stats, fetch_historical_data,
calculate_predictions, generate_report, save_to_file, create_visualization.
Uses Wikipedia for team/player context where applicable.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class Tools:
    """Tool/API actions for the workflow. Data from team DB + optional Wikipedia."""

    # Weights for team winner: FIFA 25%, Historical 20%, Recent form 25%, Squad 20%, Home 10%
    WEIGHTS_TEAM = {"fifa_ranking": 0.25, "historical": 0.20, "recent_form": 0.25, "squad_strength": 0.20, "home_advantage": 0.10}

    WORLD_CUP_TEAMS = {
        "Argentina": {"code": "ARG", "confederation": "CONMEBOL", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Flag_of_Argentina.svg/50px-Flag_of_Argentina.svg.png", "fifa_points": 1851, "world_cup_wins": 3, "world_cup_appearances": 18, "last_world_cup": "2022 (Winners)", "key_players": ["Lionel Messi", "Julian Alvarez", "Enzo Fernandez"], "squad_size": 26, "ovr_rating": 87},
        "France": {"code": "FRA", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/50px-Flag_of_France.svg.png", "fifa_points": 1842, "world_cup_wins": 2, "world_cup_appearances": 16, "last_world_cup": "2022 (Finalists)", "key_players": ["Kylian Mbappe", "Antoine Griezmann", "Aurelien Tchouameni"], "squad_size": 26, "ovr_rating": 86},
        "Brazil": {"code": "BRA", "confederation": "CONMEBOL", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/50px-Flag_of_Brazil.svg.png", "fifa_points": 1830, "world_cup_wins": 5, "world_cup_appearances": 22, "last_world_cup": "2022 (Quarter-Finals)", "key_players": ["Vinicius Jr", "Richarlison", "Casemiro"], "squad_size": 26, "ovr_rating": 85},
        "England": {"code": "ENG", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Flag_of_England.svg/50px-Flag_of_England.svg.png", "fifa_points": 1797, "world_cup_wins": 1, "world_cup_appearances": 16, "last_world_cup": "2022 (Quarter-Finals)", "key_players": ["Harry Kane", "Jude Bellingham", "Phil Foden"], "squad_size": 26, "ovr_rating": 85},
        "Spain": {"code": "ESP", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Flag_of_Spain.svg/50px-Flag_of_Spain.svg.png", "fifa_points": 1775, "world_cup_wins": 1, "world_cup_appearances": 16, "last_world_cup": "2022 (Round of 16)", "key_players": ["Pedri", "Rodri", "Lamine Yamal"], "squad_size": 26, "ovr_rating": 84},
        "Germany": {"code": "GER", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/50px-Flag_of_Germany.svg.png", "fifa_points": 1753, "world_cup_wins": 4, "world_cup_appearances": 20, "last_world_cup": "2022 (Group Stage)", "key_players": ["Jamal Musiala", "Florian Wirtz", "Ilkay Gundogan"], "squad_size": 26, "ovr_rating": 84},
        "Netherlands": {"code": "NED", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/50px-Flag_of_the_Netherlands.svg.png", "fifa_points": 1710, "world_cup_wins": 0, "world_cup_appearances": 11, "last_world_cup": "2022 (Quarter-Finals)", "key_players": ["Virgil van Dijk", "Memphis Depay", "Frenkie de Jong"], "squad_size": 26, "ovr_rating": 83},
        "Portugal": {"code": "POR", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Flag_of_Portugal.svg/50px-Flag_of_Portugal.svg.png", "fifa_points": 1697, "world_cup_wins": 0, "world_cup_appearances": 8, "last_world_cup": "2022 (Quarter-Finals)", "key_players": ["Cristiano Ronaldo", "Bruno Fernandes", "Bernardo Silva"], "squad_size": 26, "ovr_rating": 83},
        "Belgium": {"code": "BEL", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Flag_of_Belgium.svg/50px-Flag_of_Belgium.svg.png", "fifa_points": 1684, "world_cup_wins": 0, "world_cup_appearances": 14, "last_world_cup": "2022 (Group Stage)", "key_players": ["Kevin De Bruyne", "Romelu Lukaku", "Jeremy Doku"], "squad_size": 26, "ovr_rating": 82},
        "Italy": {"code": "ITA", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/50px-Flag_of_Italy.svg.png", "fifa_points": 1731, "world_cup_wins": 4, "world_cup_appearances": 18, "last_world_cup": "2022 (Did not qualify)", "key_players": ["Gianluigi Donnarumma", "Federico Chiesa", "Nicolo Barella"], "squad_size": 26, "ovr_rating": 82},
        "Croatia": {"code": "CRO", "confederation": "UEFA", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Flag_of_Croatia.svg/50px-Flag_of_Croatia.svg.png", "fifa_points": 1664, "world_cup_wins": 0, "world_cup_appearances": 6, "last_world_cup": "2022 (Third Place)", "key_players": ["Luka Modric", "Mateo Kovacic", "Josko Gvardiol"], "squad_size": 26, "ovr_rating": 82},
        "Uruguay": {"code": "URU", "confederation": "CONMEBOL", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Flag_of_Uruguay.svg/50px-Flag_of_Uruguay.svg.png", "fifa_points": 1644, "world_cup_wins": 2, "world_cup_appearances": 14, "last_world_cup": "2022 (Quarter-Finals)", "key_players": ["Darwin Nunez", "Federico Valverde", "Rodrigo Bentancur"], "squad_size": 26, "ovr_rating": 81},
        "USA": {"code": "USA", "confederation": "CONCACAF", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Flag_of_the_United_States.svg/50px-Flag_of_the_United_States.svg.png", "fifa_points": 1611, "world_cup_wins": 0, "world_cup_appearances": 11, "last_world_cup": "2022 (Round of 16)", "key_players": ["Christian Pulisic", "Tyler Adams", "Josh Sargent"], "squad_size": 26, "ovr_rating": 79, "home_advantage": True},
        "Mexico": {"code": "MEX", "confederation": "CONCACAF", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Flag_of_Mexico.svg/50px-Flag_of_Mexico.svg.png", "fifa_points": 1597, "world_cup_wins": 0, "world_cup_appearances": 17, "last_world_cup": "2022 (Group Stage)", "key_players": ["Hirving Lozano", "Edson Alvarez", "Santiago Jimenez"], "squad_size": 26, "ovr_rating": 79, "home_advantage": True},
        "Japan": {"code": "JPN", "confederation": "AFC", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Flag_of_Japan.svg/50px-Flag_of_Japan.svg.png", "fifa_points": 1586, "world_cup_wins": 0, "world_cup_appearances": 7, "last_world_cup": "2022 (Round of 16)", "key_players": ["Daizen Maeda", "Takehiro Tomiyasu", "Wataru Endo"], "squad_size": 26, "ovr_rating": 79},
        "South Korea": {"code": "KOR", "confederation": "AFC", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Flag_of_South_Korea.svg/50px-Flag_of_South_Korea.svg.png", "fifa_points": 1575, "world_cup_wins": 0, "world_cup_appearances": 11, "last_world_cup": "2022 (Group Stage)", "key_players": ["Son Heung-min", "Kim Min-jae", "Lee Kang-in"], "squad_size": 26, "ovr_rating": 78},
        "Morocco": {"code": "MAR", "confederation": "CAF", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Flag_of_Morocco.svg/50px-Flag_of_Morocco.svg.png", "fifa_points": 1553, "world_cup_wins": 0, "world_cup_appearances": 6, "last_world_cup": "2022 (Semi-Finals)", "key_players": ["Achraf Hakimi", "Youssef En-Nesyri", "Sofyan Amrabat"], "squad_size": 26, "ovr_rating": 80},
        "Senegal": {"code": "SEN", "confederation": "CAF", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Flag_of_Senegal.svg/50px-Flag_of_Senegal.svg.png", "fifa_points": 1542, "world_cup_wins": 0, "world_cup_appearances": 3, "last_world_cup": "2022 (Round of 16)", "key_players": ["Sadio Mane", "Idrissa Gueye", "Nicolas Jackson"], "squad_size": 26, "ovr_rating": 78},
        "Colombia": {"code": "COL", "confederation": "CONMEBOL", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Flag_of_Colombia.svg/50px-Flag_of_Colombia.svg.png", "fifa_points": 1624, "world_cup_wins": 0, "world_cup_appearances": 6, "last_world_cup": "2018 (Group Stage)", "key_players": ["James Rodriguez", "Luis Diaz", "Juan Cuadrado"], "squad_size": 26, "ovr_rating": 79},
        "Australia": {"code": "AUS", "confederation": "AFC", "flag": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Flag_of_Australia_%28converted%29.svg/50px-Flag_of_Australia_%28converted%29.svg.png", "fifa_points": 1564, "world_cup_wins": 0, "world_cup_appearances": 6, "last_world_cup": "2022 (Round of 16)", "key_players": ["Mathew Leckie", "Aaron Mooy", "Miloš Degenek"], "squad_size": 26, "ovr_rating": 77},
    }

    CONFEDERATION_STRENGTH = {"CONMEBOL": 1.12, "UEFA": 1.10, "CONCACAF": 0.95, "AFC": 0.88, "CAF": 0.88, "OFC": 0.75}

    # Players for awards (forwards/midfielders for Golden Ball/Boot; goalkeepers for Glove; U21 for Young Player)
    PLAYERS_FORWARDS = [
        {"name": "Kylian Mbappe", "team": "France", "position": "Forward", "goals": 45, "assists": 28, "rating": 92},
        {"name": "Harry Kane", "team": "England", "position": "Forward", "goals": 58, "assists": 18, "rating": 90},
        {"name": "Vinicius Jr", "team": "Brazil", "position": "Forward", "goals": 22, "assists": 18, "rating": 89},
        {"name": "Lionel Messi", "team": "Argentina", "position": "Forward", "goals": 38, "assists": 35, "rating": 88},
        {"name": "Julian Alvarez", "team": "Argentina", "position": "Forward", "goals": 18, "assists": 12, "rating": 85},
    ]
    PLAYERS_MIDFIELDERS = [
        {"name": "Jude Bellingham", "team": "England", "position": "Midfielder", "goals": 14, "assists": 12, "rating": 89},
        {"name": "Kevin De Bruyne", "team": "Belgium", "position": "Midfielder", "goals": 12, "assists": 22, "rating": 90},
        {"name": "Rodri", "team": "Spain", "position": "Midfielder", "goals": 8, "assists": 10, "rating": 89},
        {"name": "Luka Modric", "team": "Croatia", "position": "Midfielder", "goals": 4, "assists": 8, "rating": 87},
        {"name": "Bruno Fernandes", "team": "Portugal", "position": "Midfielder", "goals": 15, "assists": 14, "rating": 88},
    ]
    PLAYERS_GOALKEEPERS = [
        {"name": "Thibaut Courtois", "team": "Belgium", "position": "Goalkeeper", "clean_sheets": 18, "saves": 95, "rating": 90},
        {"name": "Emiliano Martinez", "team": "Argentina", "position": "Goalkeeper", "clean_sheets": 15, "saves": 88, "rating": 88},
        {"name": "Gianluigi Donnarumma", "team": "Italy", "position": "Goalkeeper", "clean_sheets": 14, "saves": 82, "rating": 87},
        {"name": "Alisson Becker", "team": "Brazil", "position": "Goalkeeper", "clean_sheets": 16, "saves": 90, "rating": 89},
        {"name": "Marc-Andre ter Stegen", "team": "Germany", "position": "Goalkeeper", "clean_sheets": 12, "saves": 78, "rating": 86},
    ]
    U21_PLAYERS = [
        {"name": "Lamine Yamal", "team": "Spain", "position": "Forward", "age": 19, "goals": 8, "assists": 12, "rating": 86},
        {"name": "Warren Zaire-Emery", "team": "France", "position": "Midfielder", "age": 19, "goals": 2, "assists": 8, "rating": 84},
        {"name": "Endrick", "team": "Brazil", "position": "Forward", "age": 19, "goals": 6, "assists": 4, "rating": 83},
        {"name": "Pau Cubarsi", "team": "Spain", "position": "Defender", "age": 18, "goals": 0, "assists": 2, "rating": 82},
    ]

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def fetch_fifa_rankings(self) -> Dict[str, Any]:
        """Get current team rankings (from team database)."""
        teams = []
        for i, (team_name, info) in enumerate(self.WORLD_CUP_TEAMS.items(), 1):
            teams.append({
                "rank": i, "team": team_name, "points": info.get("fifa_points", 1500),
                "confederation": info.get("confederation", "UEFA"), "crest": info.get("flag", ""),
                "shortName": info.get("code", team_name[:3].upper()),
            })
        return {"result": f"Retrieved rankings for {len(teams)} qualified teams", "data": teams}

    def fetch_player_stats(self, position: str) -> Dict[str, Any]:
        """Get player statistics by position (forwards, midfielders, goalkeepers, young)."""
        position = (position or "forwards").lower()
        if position == "goalkeepers":
            players = list(self.PLAYERS_GOALKEEPERS)
        elif position == "midfielders":
            players = list(self.PLAYERS_MIDFIELDERS)
        elif position == "young" or position == "u21":
            players = list(self.U21_PLAYERS)
        else:
            players = list(self.PLAYERS_FORWARDS)
        for p in players:
            p.setdefault("team", p.get("nationality", ""))
            team_info = self.WORLD_CUP_TEAMS.get(p["team"], {})
            p["crest"] = team_info.get("flag", "")
        return {"result": f"Retrieved {len(players)} {position}", "data": players}

    def fetch_historical_data(self, tournament: str = "World Cup") -> Dict[str, Any]:
        """Get past World Cup results (from built-in data)."""
        historical = {
            "2022": {"winner": "Argentina", "runner_up": "France", "third": "Croatia", "fourth": "Morocco", "host": "Qatar", "top_scorer": "Kylian Mbappe", "golden_ball": "Lionel Messi", "golden_glove": "Emiliano Martinez"},
            "2018": {"winner": "France", "runner_up": "Croatia", "third": "Belgium", "fourth": "England", "host": "Russia", "top_scorer": "Harry Kane", "golden_ball": "Luka Modric", "golden_glove": "Thibaut Courtois"},
            "2014": {"winner": "Germany", "runner_up": "Argentina", "third": "Netherlands", "fourth": "Brazil", "host": "Brazil", "top_scorer": "James Rodriguez", "golden_ball": "Lionel Messi", "golden_glove": "Manuel Neuer"},
        }
        return {"result": "Processed data from 2014, 2018, 2022 tournaments", "data": historical}

    def analyze_team_form(self, teams: List[str]) -> Dict[str, Any]:
        """Analyze recent form from last World Cup performance (mock from team data)."""
        if not teams:
            teams = list(self.WORLD_CUP_TEAMS.keys())[:10]
        form_data = {}
        for name in teams:
            info = self.WORLD_CUP_TEAMS.get(name, {})
            last = info.get("last_world_cup", "")
            if "Winner" in last or "Final" in last:
                form = "Excellent"
            elif "Semi" in last or "Third" in last:
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
        """
        ML-like prediction: Team winner uses FIFA 25%, Historical 20%, Recent form 25%, Squad 20%, Home 10%.
        Returns top 5 with probability-like scores (percentages).
        """
        weights = weights or self.WEIGHTS_TEAM
        teams = data.get("teams") or data.get("data") or []
        if not teams and isinstance(data, list):
            teams = data
        if not teams:
            teams = [{"team": name, "rank": i, "points": info.get("fifa_points", 1500), "world_cup_wins": info.get("world_cup_wins", 0), "ovr_rating": info.get("ovr_rating", 80), "home_advantage": info.get("home_advantage", False), "last_world_cup": info.get("last_world_cup", "")} for i, (name, info) in enumerate(self.WORLD_CUP_TEAMS.items(), 1)]
        scores = []
        max_rank = max((t.get("rank") or 0) for t in teams) or 32
        for t in teams:
            name = t.get("team", "Unknown")
            info = self.WORLD_CUP_TEAMS.get(name, {})
            rank = t.get("rank") or 0
            points = t.get("points") or info.get("fifa_points", 1500)
            wc_wins = t.get("world_cup_wins") if "world_cup_wins" in t else info.get("world_cup_wins", 0)
            squad = t.get("ovr_rating") or t.get("squad_rating") or info.get("ovr_rating", 80)
            home = t.get("home_advantage") if "home_advantage" in t else info.get("home_advantage", False)
            last_wc = t.get("last_world_cup") or info.get("last_world_cup", "")
            fifa_score = (1 - (rank - 1) / max(max_rank, 1)) * 100
            hist_score = min(100, wc_wins * 20 + 20)
            form_score = 80 if "Winner" in last_wc or "Final" in last_wc else 60 if "Semi" in last_wc else 40 if "Quarter" in last_wc else 20
            squad_score = (squad - 70) * 2.5
            home_score = 100 if home else 0
            total = fifa_score * weights.get("fifa_ranking", 0.25) + hist_score * weights.get("historical", 0.20) + form_score * weights.get("recent_form", 0.25) + squad_score * weights.get("squad_strength", 0.20) + home_score * weights.get("home_advantage", 0.10)
            total = max(0, min(100, total * 0.35))
            scores.append({"team": name, "score": round(total, 1), "crest": info.get("flag", t.get("crest", "")), "shortName": info.get("code", name[:3].upper()), "factors": {"fifa": fifa_score, "historical": hist_score, "form": form_score, "squad": squad_score, "home": home_score}})
        scores.sort(key=lambda x: x["score"], reverse=True)
        total_sum = sum(s["score"] for s in scores[:5])
        if total_sum > 0:
            for s in scores[:5]:
                s["probability"] = round(100 * s["score"] / total_sum, 1)
        result = {str(i + 1): scores[i] for i in range(min(5, len(scores)))}
        return {"result": "Computed weighted scores for all teams", "data": result, "top5": scores[:5]}

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
        """Score players for Golden Ball / Golden Boot / Golden Glove / Young Player. Returns top 5 with probability."""
        if not players:
            return {"result": "No players to score", "data": {}, "top5": []}
        scored = []
        for p in players:
            name = p.get("name", "Unknown")
            team = p.get("team", p.get("nationality", ""))
            crest = (p.get("crest") or "") or (self.WORLD_CUP_TEAMS.get(team, {}).get("flag", "") if team else "")
            if award_type == "golden_ball":
                s = p.get("rating", 80) * 0.4 + (p.get("goals", 0) or 0) * 0.3 + (p.get("assists", 0) or 0) * 0.3
            elif award_type == "golden_boot":
                s = (p.get("goals", 0) or 0) * 0.8 + p.get("rating", 80) * 0.2
            elif award_type == "golden_glove":
                s = (p.get("clean_sheets", 0) or 0) * 0.5 + p.get("rating", 80) * 0.5
            else:
                s = (p.get("rating", 80) * 0.5 + (p.get("goals", 0) or 0) * 0.3 + (p.get("assists", 0) or 0) * 0.2)
            scored.append({"name": name, "team": team, "score": round(s, 1), "crest": crest or "", "shortName": team[:3].upper() if team else "?"})
        scored.sort(key=lambda x: x["score"], reverse=True)
        top5 = scored[:5]
        total = sum(x["score"] for x in top5) or 1
        for x in top5:
            x["probability"] = round(100 * x["score"] / total, 1)
        data = {str(i + 1): top5[i] for i in range(len(top5))}
        return {"result": f"Computed {award_type} scores", "data": data, "top5": top5}
