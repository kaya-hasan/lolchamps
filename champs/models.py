# Adom 1 - Şampiyonları oluşturacağımız bir model dosyası
# İsim alanı olsun, unique, maks 100, açıklama, title döndürsün, alfabetik sıralasın


# champions/models.py
from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.description}"



class Champion(models.Model):
    Difficulty_Chosing = [
        (1, "Kolay"),
        (2, "Orta"),
        (3, "Zor"),
    ]
    PlayingFreq_Chosing = [
        (1, "Çok Düşük"),
        (2, "Düşük"),
        (3, "Orta"),
        (4, "Yüksek"),
        (5, "Çok Yüksek"),
    ]
    Tier_Chosing = [
        (1, "S"),
        (2, "A"),
        (3, "B"),
        (4, "C"),
        (5, "D"),
    ]
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    riot_id = models.CharField(max_length=100, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='champions')
    difficulty = models.IntegerField(choices=Difficulty_Chosing, default=1)
    playing_freq = models.IntegerField(choices=PlayingFreq_Chosing, default=1)
    tier = models.IntegerField(choices=Tier_Chosing, default=1)
    lore = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.role.name}"


class ChampionBuildInsight(models.Model):
    champion = models.OneToOneField(Champion, on_delete=models.CASCADE, related_name="build_insight")
    source_region = models.CharField(max_length=20, blank=True)
    sample_size = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.0)
    recommended_items = models.JSONField(default=list, blank=True)
    recommended_runes = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Build Insight - {self.champion.name} ({self.sample_size} games)"


class Review(models.Model):
    champion = models.ForeignKey(Champion, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.champion.name} ({self.rating})"
