from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from champs.models import Champion, ChampionBuildInsight
from champs.services.riot_data_dragon import (
    DataDragonError,
    _get_json,
    get_latest_version,
)
from champs.services.riot_match_api import (
    RiotApiError,
    get_api_key,
    get_match,
    get_match_ids_by_puuid,
)


def _as_percent(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100, 2)


class Command(BaseCommand):
    help = (
        "Riot Match-v5 verisinden şampiyon bazlı eşya/rün önerilerini çıkarır "
        "ve ChampionBuildInsight tablosuna yazar."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--region",
            type=str,
            default="europe",
            help="Regional routing value: europe / americas / asia (varsayılan: europe)",
        )
        parser.add_argument(
            "--champion",
            type=str,
            required=True,
            help="Şampiyon slug veya riot_id (örn: lee-sin veya LeeSin)",
        )
        parser.add_argument(
            "--puuid",
            action="append",
            default=[],
            help="Match list çekmek için bir veya daha fazla PUUID. Birden çok kez verilebilir.",
        )
        parser.add_argument(
            "--match-id",
            action="append",
            default=[],
            help="Doğrudan analiz edilecek match id. Birden çok kez verilebilir.",
        )
        parser.add_argument(
            "--matches-per-puuid",
            type=int,
            default=20,
            help="Her PUUID için çekilecek maç sayısı (varsayılan: 20)",
        )
        parser.add_argument(
            "--min-games",
            type=int,
            default=5,
            help="Öneri üretmek için minimum champion maç örneği (varsayılan: 5)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        champion_query = options["champion"]
        region = options["region"]
        puuids = options["puuid"]
        direct_match_ids = options["match_id"]
        matches_per_puuid = options["matches_per_puuid"]
        min_games = options["min_games"]

        champion = (
            Champion.objects.filter(slug=champion_query).first()
            or Champion.objects.filter(riot_id=champion_query).first()
            or Champion.objects.filter(name__iexact=champion_query).first()
        )
        if not champion:
            raise CommandError(f"Şampiyon bulunamadı: {champion_query}")
        if not champion.riot_id:
            raise CommandError(
                "Seçilen şampiyonda riot_id boş. Önce sync_champions --update-existing çalıştırın."
            )

        if not puuids and not direct_match_ids:
            raise CommandError("En az bir --puuid veya --match-id vermelisiniz.")

        try:
            api_key = get_api_key()
        except RiotApiError as exc:
            raise CommandError(str(exc)) from exc

        match_ids = set(direct_match_ids)
        for puuid in puuids:
            try:
                ids = get_match_ids_by_puuid(
                    region=region,
                    puuid=puuid,
                    count=matches_per_puuid,
                    api_key=api_key,
                )
            except RiotApiError as exc:
                raise CommandError(str(exc)) from exc
            match_ids.update(ids)

        if not match_ids:
            raise CommandError("Analiz edilecek match id bulunamadı.")

        try:
            dd_version = get_latest_version()
            items_payload = _get_json(
                f"https://ddragon.leagueoflegends.com/cdn/{dd_version}/data/en_US/item.json"
            )
            runes_payload = _get_json(
                "https://ddragon.leagueoflegends.com/cdn/15.1.1/data/en_US/runesReforged.json"
            )
        except DataDragonError as exc:
            raise CommandError(str(exc)) from exc

        item_map = items_payload.get("data", {})
        style_map = {}
        perk_map = {}
        for style in runes_payload:
            style_map[style["id"]] = {
                "id": style["id"],
                "name": style["name"],
                "icon": f"https://ddragon.leagueoflegends.com/cdn/img/{style['icon']}",
            }
            for slot in style.get("slots", []):
                for rune in slot.get("runes", []):
                    perk_map[rune["id"]] = {
                        "id": rune["id"],
                        "name": rune["name"],
                        "icon": f"https://ddragon.leagueoflegends.com/cdn/img/{rune['icon']}",
                    }

        total_games = 0
        wins = 0
        item_counter = Counter()
        rune_page_counter = Counter()

        for match_id in match_ids:
            try:
                match = get_match(region=region, match_id=match_id, api_key=api_key)
            except RiotApiError:
                continue

            participants = match.get("info", {}).get("participants", [])
            for p in participants:
                if p.get("championName") != champion.riot_id:
                    continue

                total_games += 1
                if p.get("win"):
                    wins += 1

                build_items = []
                for i in range(0, 7):
                    item_id = int(p.get(f"item{i}", 0) or 0)
                    if item_id > 0:
                        build_items.append(item_id)

                for item_id in set(build_items):
                    item_counter[item_id] += 1

                styles = p.get("perks", {}).get("styles", [])
                if len(styles) >= 2:
                    primary_style = styles[0].get("style")
                    sub_style = styles[1].get("style")
                    selections = styles[0].get("selections", [])
                    keystone = selections[0].get("perk") if selections else None
                    rune_page_counter[(primary_style, sub_style, keystone)] += 1

        if total_games < min_games:
            raise CommandError(
                f"Yetersiz örnek: {total_games} maç bulundu, en az {min_games} gerekli."
            )

        recommended_items = []
        for item_id, count in item_counter.most_common(6):
            item_info = item_map.get(str(item_id), {})
            recommended_items.append(
                {
                    "item_id": item_id,
                    "name": item_info.get("name", f"Item {item_id}"),
                    "image_url": f"https://ddragon.leagueoflegends.com/cdn/{dd_version}/img/item/{item_id}.png",
                    "pick_rate": _as_percent(count, total_games),
                }
            )

        recommended_runes = []
        for (primary_style, sub_style, keystone), count in rune_page_counter.most_common(3):
            recommended_runes.append(
                {
                    "primary_style": style_map.get(primary_style, {"id": primary_style, "name": str(primary_style)}),
                    "sub_style": style_map.get(sub_style, {"id": sub_style, "name": str(sub_style)}),
                    "keystone": perk_map.get(keystone, {"id": keystone, "name": str(keystone)}),
                    "pick_rate": _as_percent(count, total_games),
                }
            )

        insight, _ = ChampionBuildInsight.objects.get_or_create(champion=champion)
        insight.source_region = region
        insight.sample_size = total_games
        insight.win_rate = _as_percent(wins, total_games)
        insight.recommended_items = recommended_items
        insight.recommended_runes = recommended_runes
        insight.save()

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Build sync tamamlandı | champion={champion.name} | "
                    f"games={total_games} | win_rate={insight.win_rate}% | "
                    f"items={len(recommended_items)} | rune_pages={len(recommended_runes)}"
                )
            )
        )
