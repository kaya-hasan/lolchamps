import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


DATA_DRAGON_BASE = "https://ddragon.leagueoflegends.com"


class DataDragonError(Exception):
    pass


def _get_json(url: str) -> dict | list:
    try:
        with urlopen(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise DataDragonError(f"Data Dragon request failed: {url} ({exc})") from exc


def get_latest_version() -> str:
    versions = _get_json(f"{DATA_DRAGON_BASE}/api/versions.json")
    if not versions:
        raise DataDragonError("No version found in Data Dragon versions endpoint.")
    return versions[0]


def fetch_champions(version: str, locale: str) -> dict:
    payload = _get_json(
        f"{DATA_DRAGON_BASE}/cdn/{version}/data/{locale}/champion.json"
    )
    if "data" not in payload:
        raise DataDragonError("Champion payload has no 'data' key.")
    return payload
