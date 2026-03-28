# Yapılacaklar
# Listdis isim alanı gözüksün, searchFields iletişim alanında arama yapabilsin
# ListFilter ile role, difc tierlist playing req isfree bakılabilsin
# name ve lore'a göre arama yapabilelim
# slugdan direkt isim çekme özelliği olsun, is free açılıp kapatılabilsin
# review yazalım
# 1. Role modelini admin paneline ekle
# 2. Champion modelini admin paneline ekle
# 3. Review modelini admin paneline ekle


from django.contrib import admin
from .models import Role, Champion, Review, ChampionBuildInsight

# Register your models here.

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    list_filter = ('name', 'description')
    ordering = ("name",)

@admin.register(Champion)
class ChampionAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'riot_id', 'difficulty', 'playing_freq', 'tier', 'is_free')
    search_fields = ('name', 'lore')
    list_filter = ('role', 'difficulty', 'playing_freq', 'tier', 'is_free')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_free', 'difficulty', 'playing_freq', 'tier')
    ordering = ("name",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'champion', 'rating', 'comment')
    search_fields = ('user__username', 'champion__name', 'comment')
    list_filter = ('user', 'champion', 'rating')
    raw_id_fields = ('user', 'champion')
    ordering = ("-created_at",)


@admin.register(ChampionBuildInsight)
class ChampionBuildInsightAdmin(admin.ModelAdmin):
    list_display = ("champion", "source_region", "sample_size", "win_rate", "updated_at")
    search_fields = ("champion__name", "champion__riot_id")
    list_filter = ("source_region",)
    ordering = ("-updated_at",)
