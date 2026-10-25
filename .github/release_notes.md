## TD2 Loot Advisor — Windows

| Dosya | Ne |
|---|---|
| `TD2LootAdvisor_Setup_<sürüm>.exe` | **Kurulum dosyası** (önerilen). Yönetici izni gerekmez; kullanıcı klasörüne kurulur, Başlat menüsü ve masaüstü kısayolu, Programlar'dan kaldırma. |
| `TD2LootAdvisor_<sürüm>_portable.zip` | Kurulumsuz sürüm: bir klasöre çıkar, `TD2LootAdvisor.exe`'yi çalıştır. |
| Source code (zip / tar.gz) | Kaynak kod (Python). |

Windows "kişisel bilgisayarınızı korudu" derse: **Ek bilgi → Yine de çalıştır** (dosya henüz kod imzalı değil).

**5.0.3 — kendi kendine öğrenen eşya kütüphanesi**
- Program artık kendi uyarı penceresini okumuyor (önceki kararın yazıları yeni kartın adını kapatıyordu).
- Öğrenen kütüphane: kütüphanede olmayan marka / gear set / parça adı bir kez okununca kaydedilir (`learned_library.json`) ve hep tanınır. Örn. "Unmatched Backpack → Sırt çantası, Unit Alloys".
- "Brand Set / Gear Set" satırından marka ve set her zaman okunur; zırh kartları artık silah sanılmıyor.
- Unit Alloys markası eklendi. M16A2 / LVOA-C gibi tüfekler artık sniper build'leriyle eşleşmiyor.

**5.0.2 — kararlılık düzeltmeleri**
- Set parçaları yanlış yuvaya yazılıyordu (dizlik / holster / sırt çantası "eldiven" görünüyordu): düzeltildi.
- Kaydırılmış kart birleştirme artık farklı eşyaları (ör. maske + silah, eldiven + dizlik) birleştirmiyor.
- Skill build'leri "Assault Turret" yüzünden tüfeklerle eşleşiyordu: düzeltildi.
- Tanı için son 200 kart okuması `logs/ocr_history/` altında tutulur (yalnız kart metni).

**Öne çıkanlar:** yeni OCR motoru (RapidOCR; 480p'ye kadar doğru okuma, Tesseract gerekmez) · Sandık: envanter, build optimize edici,
denetim raporu, satıcı eşleştirme · telefon arkadaşı · build paylaşım kodları · gönüllü ve anonim topluluk düşüş istatistikleri ·
Asistana sor / Claude ile oku · 10 dil. Oyunun belleğine dokunmaz, yalnızca ekranı okur.

Bu dosyalar GitHub Actions'ta otomatik derlendi; kurulum dosyası Windows'ta sessizce kurulup program açılarak test edildi.
