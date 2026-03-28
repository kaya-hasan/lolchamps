# LOLChamps

`LOLChamps`, League of Legends şampiyonlarını listelemek, detaylarını görüntülemek, yorum yapmak ve Riot verileriyle senkron çalışmak için geliştirilmiş bir Django projesidir.

## Özellikler

- Şampiyon listeleme, detay, oluşturma, güncelleme, silme
- Rol filtresi, arama, sıralama, sayfalama
- Kullanıcı yorumları (aynı kullanıcı birden fazla yorum yazabilir)
- Riot Data Dragon ile şampiyon verisi senkronu
- Riot Match-v5 ile şampiyon bazlı build/rün insight üretimi
- Şampiyon görselleri, rol ve tier gösterimi

## Teknolojiler

- Python 3
- Django 6
- SQLite (varsayılan)
- Riot API + Data Dragon

## Proje Yapısı

```text
LOLChamps/                 # Django proje ayarları
champs/                    # Uygulama (models, views, templates, commands)
manage.py
requirements.txt
render.yaml                # Render deploy ayarı
Procfile
```

## Kurulum (Lokal)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`.env` dosyası oluştur:

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=

RIOT_API_KEY=
RIOT_REGION=europe
RIOT_LOCALE=tr_TR
```

Veritabanını hazırla:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Sunucuyu başlat:

```bash
python manage.py runserver
```

## Riot Veri Senkronu

### 1) Şampiyonları çekme/güncelleme

```bash
python manage.py sync_champions --locale tr_TR --update-existing
```

Bu komut:

- Şampiyon adları ve lore bilgisini çeker
- Görsel URL’lerini doldurur
- Rol ve tier verisini günceller

### 2) Build / Rune insight üretme

Önce Riot hesabından `PUUID` alın (örnek `curl`):

```bash
curl -s -H "X-Riot-Token: $RIOT_API_KEY" \
"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/GAME_NAME/TAG_LINE"
```

Sonra komutu çalıştır:

```bash
python manage.py sync_champion_builds \
  --region europe \
  --champion Nautilus \
  --puuid "PUUID_DEGERI" \
  --matches-per-puuid 100 \
  --min-games 2
```

Insight sonucu şampiyon detay sayfasında görünür.

## Kullanıcı Rolleri / Erişim

- Giriş yapmadan şampiyon oluşturma/düzenleme/silme yapılamaz
- Girişsiz kullanıcı “Yeni Şampiyon”a tıklarsa login uyarı modalı açılır
- Çıkış işlemi navbar üzerinden yapılır

## Deploy (Render)

Bu proje `render.yaml` ve `Procfile` ile Render’a uygundur.

Render ortam değişkenleri:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=.onrender.com`
- `CSRF_TRUSTED_ORIGINS=https://*.onrender.com`
- `RIOT_API_KEY` (Riot komutları kullanacaksan)

Render build/start:

- Build: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
- Start: `gunicorn LOLChamps.wsgi:application`

## Sık Karşılaşılan Sorunlar

- `RIOT_API_KEY env değişkeni tanımlı değil`:
  - `.env` dosyasını shell’e yükleyin:
    ```bash
    set -a; source .env; set +a
    ```
- `Yetersiz örnek`:
  - `--matches-per-puuid` artırın veya `--min-games` düşürün
- `403 / 1010`:
  - Riot development key’in güncel olduğundan emin olun (24 saatlik)

## Lisans

Bu proje `MIT License` ile lisanslanmıştır.
