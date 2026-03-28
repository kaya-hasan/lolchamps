import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class RiotApiError(Exception):
    pass


def _get_json(url: str, api_key: str):
    req = Request(
        url,
        headers={
            "X-Riot-Token": api_key,
            "User-Agent": "LOLChamps/1.0 (contact: local-dev)",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://developer.riotgames.com",
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RiotApiError(f"HTTP {exc.code} for {url} - {body}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RiotApiError(f"Riot API request failed: {url} ({exc})") from exc


def get_api_key() -> str:
    api_key = os.getenv("RIOT_API_KEY", "").strip()
    if not api_key:
        raise RiotApiError("RIOT_API_KEY env değişkeni tanımlı değil.")
    return api_key


def get_match_ids_by_puuid(region: str, puuid: str, count: int, api_key: str) -> list[str]:
    url = (
        f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/"
        f"{puuid}/ids?start=0&count={count}"
    )
    data = _get_json(url, api_key)
    return data if isinstance(data, list) else []


def get_match(region: str, match_id: str, api_key: str) -> dict:
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    data = _get_json(url, api_key)
    if not isinstance(data, dict):
        raise RiotApiError(f"Beklenmeyen match payload: {match_id}")
    return data
