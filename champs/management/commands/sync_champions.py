from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from champs.models import Champion, Role, ChampionBuildInsight
from champs.services.riot_data_dragon import (
    DataDragonError,
    fetch_champion_full,
    fetch_champions,
    get_latest_version,
)


TAG_ROLE_MAP = {
    "Marksman": "ADC",
    "Support": "Support",
    "Assassin": "Mid",
    "Mage": "Mid",
    "Tank": "Top",
    "Fighter": "Top",
}

JUNGLE_CHAMPION_IDS = {
    "Amumu",
    "Belveth",
    "Briar",
    "Diana",
    "Ekko",
    "Elise",
    "Evelynn",
    "Fiddlesticks",
    "Gragas",
    "Graves",
    "Hecarim",
    "Ivern",
    "JarvanIV",
    "Karthus",
    "Kayn",
    "Khazix",
    "Kindred",
    "LeeSin",
    "Lillia",
    "MasterYi",
    "Nidalee",
    "Nocturne",
    "Nunu",
    "Olaf",
    "Poppy",
    "Rammus",
    "RekSai",
    "Rengar",
    "Sejuani",
    "Shaco",
    "Shyvana",
    "Skarner",
    "Taliyah",
    "Trundle",
    "Udyr",
    "Vi",
    "Viego",
    "Volibear",
    "Warwick",
    "Wukong",
    "XinZhao",
    "Zac",
}


def map_difficulty(value: int) -> int:
    if value <= 3:
        return 1
    if value <= 7:
        return 2
    return 3


def map_tier(info: dict) -> int:
    attack = int(info.get("attack", 0))
    defense = int(info.get("defense", 0))
    magic = int(info.get("magic", 0))
    raw_difficulty = int(info.get("difficulty", 5))

    # Data Dragon'daki genel güç sinyalini (attack/defense/magic) kullanıp
    # yüksek zorluğu bir miktar cezalıyoruz.
    power_score = attack + defense + magic - (raw_difficulty * 0.6)

    if power_score >= 18:
        return 1  # S
    if power_score >= 15:
        return 2  # A
    if power_score >= 12:
        return 3  # B
    if power_score >= 9:
        return 4  # C
    return 5  # D


def apply_win_rate_adjustment(base_tier: int, win_rate: float, sample_size: int) -> int:
    # Güvenilirlik için minimum örneklem.
    if sample_size < 5:
        return base_tier

    adjustment = 0
    if win_rate >= 60:
        adjustment = -2
    elif win_rate >= 56:
        adjustment = -1
    elif win_rate <= 42:
        adjustment = 2
    elif win_rate <= 46:
        adjustment = 1

    # Düşük örneklemde agresif değişimi sınırla.
    if sample_size < 10 and abs(adjustment) > 1:
        adjustment = -1 if adjustment < 0 else 1

    return max(1, min(5, base_tier + adjustment))


def pick_role(champion_id: str, tags: list[str]) -> str:
    if champion_id in JUNGLE_CHAMPION_IDS:
        return "Jungle"
    if not tags:
        return "Genel"
    for tag in tags:
        if tag in TAG_ROLE_MAP:
            return TAG_ROLE_MAP[tag]
    return tags[0]


class Command(BaseCommand):
    help = "Riot Data Dragon'dan şampiyonları çekip veritabanına senkronlar."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dd-version",
            type=str,
            default=None,
            help="Data Dragon sürümü (örn: 15.7.1). Boş bırakılırsa en son sürüm çekilir.",
        )
        parser.add_argument(
            "--locale",
            type=str,
            default="tr_TR",
            help="Dil/lokal (örn: tr_TR, en_US). Varsayılan: tr_TR",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Mevcut şampiyonlarda role/lore bilgisini de günceller.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        version = options["dd_version"] or self._safe_latest_version()
        locale = options["locale"]
        update_existing = options["update_existing"]

        try:
            payload = fetch_champions(version=version, locale=locale)
            full_payload = fetch_champion_full(version=version, locale=locale)
        except DataDragonError as exc:
            raise CommandError(str(exc)) from exc

        champions = payload.get("data", {})
        full_champions = full_payload.get("data", {})
        created = 0
        updated = 0
        skipped = 0
        build_insights = {
            insight.champion.riot_id: insight
            for insight in ChampionBuildInsight.objects.select_related("champion").exclude(champion__riot_id="")
        }

        for champ_data in champions.values():
            name = champ_data.get("name", "").strip()
            lore = champ_data.get("lore", "").strip()
            key = champ_data.get("id", "")
            tags = champ_data.get("tags", [])
            info = champ_data.get("info", {})
            difficulty = map_difficulty(int(info.get("difficulty", 5)))
            tier = map_tier(info)
            insight = build_insights.get(key)
            if insight:
                tier = apply_win_rate_adjustment(
                    base_tier=tier,
                    win_rate=float(insight.win_rate or 0),
                    sample_size=int(insight.sample_size or 0),
                )
            role_name = pick_role(key, tags)
            image_url = (
                f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{key}.png"
            )
            full_data = full_champions.get(key, {})
            passive = full_data.get("passive", {})
            passive_image = passive.get("image", {}).get("full", "")
            passive_image_url = (
                f"https://ddragon.leagueoflegends.com/cdn/{version}/img/passive/{passive_image}"
                if passive_image
                else ""
            )
            abilities = []
            for spell in full_data.get("spells", []):
                spell_image = spell.get("image", {}).get("full", "")
                spell_image_url = (
                    f"https://ddragon.leagueoflegends.com/cdn/{version}/img/spell/{spell_image}"
                    if spell_image
                    else ""
                )
                abilities.append(
                    {
                        "id": spell.get("id", ""),
                        "name": spell.get("name", ""),
                        "description": spell.get("description", ""),
                        "cooldown": spell.get("cooldownBurn", ""),
                        "cost": spell.get("costBurn", ""),
                        "range": spell.get("rangeBurn", ""),
                        "image_url": spell_image_url,
                    }
                )

            if not name:
                continue

            role_obj, _ = Role.objects.get_or_create(name=role_name)
            base_slug = slugify(name) or slugify(key) or "champion"
            slug = base_slug

            existing = Champion.objects.filter(name=name).first()
            if existing:
                if not update_existing:
                    skipped += 1
                    continue
                if Champion.objects.filter(slug=slug).exclude(pk=existing.pk).exists():
                    slug = f"{base_slug}-{slugify(key)}"

                existing.slug = slug
                existing.riot_id = key
                existing.role = role_obj
                existing.difficulty = difficulty
                existing.tier = tier
                existing.lore = lore
                existing.image_url = image_url
                existing.passive_name = passive.get("name", "")
                existing.passive_description = passive.get("description", "")
                existing.passive_image_url = passive_image_url
                existing.abilities = abilities
                existing.save(
                    update_fields=[
                        "slug",
                        "riot_id",
                        "role",
                        "difficulty",
                        "tier",
                        "lore",
                        "image_url",
                        "passive_name",
                        "passive_description",
                        "passive_image_url",
                        "abilities",
                    ]
                )
                updated += 1
                continue

            if Champion.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{slugify(key)}"

            Champion.objects.create(
                name=name,
                slug=slug,
                riot_id=key,
                role=role_obj,
                difficulty=difficulty,
                playing_freq=3,
                tier=tier,
                lore=lore,
                image_url=image_url,
                passive_name=passive.get("name", ""),
                passive_description=passive.get("description", ""),
                passive_image_url=passive_image_url,
                abilities=abilities,
                is_free=False,
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Sync tamamlandı | version={version}, locale={locale} | "
                    f"created={created}, updated={updated}, skipped={skipped}"
                )
            )
        )

    def _safe_latest_version(self) -> str:
        try:
            return get_latest_version()
        except DataDragonError as exc:
            raise CommandError(str(exc)) from exc
