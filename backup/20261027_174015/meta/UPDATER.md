# Günlük meta güncelleyici — talimat

Bu dosya, `meta/meta_builds.json` akışını her gün güncelleyen otomatik görevin (ve elle
güncelleyen kişinin) izlediği kurallardır. Uygulamanın tüm kullanıcıları bu akışı açılışta
indirir; bu yüzden **doğruluk hızdan önemlidir**.

## Akış
1. Güncel sezonu ve son yamayı belirle (Ubisoft yama notları, resmî forum/Discord duyuruları).
2. Meta ve çok etkileşim alan build'leri topla. Kaynak türleri:
   - Build rehberi siteleri (en az 2 farklı site).
   - Son 30 günün YouTube build videoları (görüntülenme sayısı herkese açık).
   - r/thedivision ve Steam tartışmaları (oy/yorum sayısı).
3. Her build için **popülerlik (0-100)** hesapla:
   - Kaç bağımsız kaynakta geçiyor (ağırlık %50),
   - Herkese açık etkileşim — görüntülenme, oy, yorum (ağırlık %35),
   - Güncellik — son yamadan sonra mı yayımlandı (ağırlık %15).
   Ölçemediğin sinyali uydurma; sadece ölçtüklerinle hesapla.
4. En fazla 15 build seç. Rolleri dengeli tut (DPS, yakın mesafe, keskin nişancı, skill,
   şifacı, tank, PvP).
5. Var olan build'in `id` değerini **asla değiştirme** (kullanıcıların kilit/gizleme kayıtları
   ona bağlı). Yeni build'e yeni, kalıcı bir `id` ver (küçük harf, tire).
6. `version` alanını `YYYY-MM-DD.N` olarak artır, `updated` alanını UTC zamanla yaz.
7. Dosyayı JSON olarak doğrula (aşağıdaki şema), sonra depoya gönder. Değişiklik yoksa
   gönderme.

## Şema (schema: 1)
```json
{
  "schema": 1,
  "version": "2026-10-24.1",
  "updated": "2026-10-24T00:00:00Z",
  "season": "Year 8 Season 3 – Red Horizon",
  "builds": [{
    "id": "st-elmos-striker",
    "name": "St. Elmo's Striker (PvE)",
    "mode": "PvE / Legendary",
    "role": "dps | close | precision | skill | pulse | tank",
    "sets_or_brands": ["Striker's Battlegear", "Striker"],
    "set_bonus": 15,
    "slots": ["Mask", "Chest"],
    "attributes": {"weapon_damage": {"weight": 3, "good_at": 10}},
    "talents": {"Obliterate": 4},
    "popularity": 95,
    "summary": {"tr": "…", "en": "…"},
    "sources": [{"title": "…", "url": "https://…"}]
  }]
}
```
- `attributes` anahtarları yalnızca `builds.json` → `attributes` listesindekiler olabilir
  (weapon_damage, crit_chance, crit_damage, headshot_damage, rate_of_fire, weapon_handling,
  reload_speed, magazine_size, optimal_range, damage_to_armor, damage_to_health,
  damage_to_elites, armor, health, armor_regen, hazard_protection, explosive_resist,
  pulse_resistance, skill_damage, skill_haste, skill_duration, skill_health, repair_skills,
  status_effects, skill_tier). Bilinmeyen anahtarı uygulama atar.
- `weight` 0-5, `talents` değerleri 0-10. Set/talent adlarını oyundaki İngilizce adla yaz.
- `talents` YALNIZCA talent adı içerir (Obliterate, Glass Cannon, Perfect Fast Hands …). Named/egzotik
  EŞYA adları (Equalizer, Chainkiller, Kingbreaker, Catharsis, St. Elmo's Engine …) `items` listesine yazılır.
  Her adı `meta/game_data.json` içindeki `gear_talents` / `weapon_talents` / `named` / `exotics` ile karşılaştır;
  listede olmayan bir ad yazma (uygulama bilinmeyen talent'leri yok sayar).
- `summary` en az `en` içermeli; `tr` de yazılması önerilir. Diğer diller isteğe bağlı.
- Kaynak bağlantıları yalnızca `https://`. Metin kopyalama; kısa, kendi cümlenle özetle.

## Yapma
- Resmî logo/görsel ekleme, sitelerin metnini kopyalama.
- Tek bir kaynağa dayanan build'e 60'tan yüksek popülerlik verme.
- Dosyayı 512 KB'tan büyük yapma.

---

# Görev akışı — `meta/tasks_feed.json`

Aynı günlük görev bu dosyayı da günceller. Uygulama açılışta ve her oyun sıfırlamasından sonra
indirir; görevler kullanıcının dilinde gösterilir.

## Ne girer
Kategoriler oyundaki menülerle birebir aynıdır (başka kategori kullanma):
- **projects** — oyundaki *Projeler* ekranı. `kind`: `daily` (günlük), `weekly` (haftalık),
  `settlement` (yerleşim projeleri), `seasonal` (etkinlik/sezon projeleri).
  **Sadece doğrulayabildiğini yaz**; kaynak bulamazsan günlük/haftalığı boş bırak.
  `until` = bir sonraki sıfırlamanın UTC zamanı (günlük 08:00, haftalık Salı 08:00).
- **journey** — sezon sekmesindeki *Yolculuk* (Journey) görevleri; Classified Assignment da buraya.
- **manhunt** — sezonun Scout/HVT adımları (kısa, ipucu metnini kopyalamadan; ne yapılacağını yaz).
- Global Event ve "diğer" kategorisi yok: sezon değiştiricileri sisteminde Global Event çalışmıyor.
- En fazla 80 görev. Bitmiş/süresi dolmuş görevleri çıkar.

## Şema (schema: 1)
```json
{
  "schema": 1, "version": "2026-10-24.1", "updated": "…Z",
  "season": "Year 8 Season 3 – Red Horizon",
  "resets": {"daily_hour_utc": 8, "weekly_weekday": 1, "weekly_hour_utc": 8},
  "tasks": [{
    "id": "y8s3-scout1-cleaners",
    "cat": "projects | journey | manhunt",
    "kind": "daily | weekly | settlement | seasonal   (yalnız projects için)",
    "text": {"en": "…", "tr": "…", "de": "…", "fr": "…", "es": "…", "it": "…",
             "pt": "…", "ru": "…", "pl": "…", "nl": "…"},
    "until": "2026-10-27T08:00Z",
    "source": {"url": "https://…"}
  }]
}
```
- `text` **10 dilin hepsini** içermeli (en zorunlu). Oyun içi özel adları (Control Point, Cleaners,
  bölge adları) İngilizce bırak; cümleyi çevir. Her metin en fazla 300 karakter.
- `id` kalıcıdır: aynı görevin kimliğini değiştirme (kullanıcıların "yapıldı" işareti ona bağlı).
- `weekly_weekday`: 0 = Pazartesi … 6 = Pazar. Resmî saat değişirse `resets`'i güncelle.
- `until` boş = sezon boyunca geçerli.

## "Nasıl yapılır" alanları
- Her görevde isteğe bağlı `"how": {10 dil}` — nerede/nasıl yapılır, en fazla 500 karakter, kendi cümlenle.
  Kaynak rehberin adresi `source.url`'de dursun (uygulamada "Kaynağı aç" butonu).
- `"guides": [{"id", "match": [anahtar kelimeler, küçük harf, birkaç dilde], "tip": {10 dil}, "source"}]` —
  oyuncunun ekrandan okuduğu günlük/haftalık projelere türüne göre ipucu eşler (kontrol noktası, bounty,
  Countdown, Summit, Dark Zone, bağış…). En fazla 60. Yeni proje türü görürsen ekle; mevcut `id`'leri koru.
- Her hafta yeni Manhunt Scout/HVT adımlarını `how` ile ekle; sezon yolculuğu görevlerini (journey) bulunca ekle.

## Wiki bağlantısı
- Uygulama The Division Wiki'yi (thedivision.fandom.com) **kullanıcının bilgisayarından** canlı okur
  (`wiki_sync.py`): sezon sayfasındaki Manhunt Scout'ları, Classified Assignment'lar ve tarihli proje
  zincirleri 📚 işaretiyle eklenir. Wiki İngilizcedir; uygulama yapay zekâ seçiliyse çevirir.
- `"wiki": {"season_page": "Red Horizon"}` — wiki okuyucunun başlayacağı sezon sayfası. Yeni sezon
  başlayınca güncelle (uygulama infobox'taki `next=` ile kendisi de ilerler).
- Ortak listede 10 dilde ayrıntılı yazdığın bir görev wiki'de de varsa `"wiki_id"` ver; uygulama o wiki
  görevini tekrar göstermez. Biçim: `wiki-<sezon-slug>-scout-<n>`, `wiki-ca-<görev-slug>`
  (ör. `wiki-red-horizon-scout-9`, `wiki-ca-georgetown-dead-zone`).
- Bulut ortamı fandom.com'a doğrudan erişemeyebilir; o durumda wiki içeriğini başka kaynaklardan doğrula.

---

# Oyun verisi — `meta/game_data.json`
- Eşya tanıma sözlüğü: `gear_sets`, `brands`, `exotics`, `named`, `gear_talents`, `weapon_talents`,
  `attributes` (`aliases`, `max`, `core`, `unit`), `weapon_types`, `slots`, `prototype_multiplier`.
- Yeni sezonda gelen egzotik/named/set/talent'i ekle (wiki "Red Horizon" sayfasındaki *New Weapons, Gear,
  and Talents* bölümü iyi bir kaynak). Mevcut adları silme; `version`'ı artır.
- `max` değerlerini yalnızca resmî yama notu bir değişiklik söylerse güncelle.
- v3 alanları (2026-10-24.5): `items` (named/egzotik ekipman → `slot`, `quality`, `brand`, `talent`),
  `weapon_index` (silah adı → `type`, `quality`; uzmanlık tabancaları `quality: specialization`, `spec`),
  `specialization_weapons`, `weapon_mods`, `gear_mods`, `skills`, `item_kinds`, `ui_words`.
  Yeni named/egzotik eklerken `items` / `weapon_index` içine de yuva/tür ile ekle. Dosyayı baştan YAZMA:
  mevcut JSON'u oku, yalnızca ekle, `version`'ı artır (ör. 2026-10-25.1). Hiçbir listeden kayıt silme.
