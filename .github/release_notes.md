## TD2 Loot Advisor — Windows

| Dosya | Ne |
|---|---|
| `TD2LootAdvisor_Setup_<sürüm>.exe` | **Kurulum dosyası** (önerilen). Yönetici izni gerekmez; kullanıcı klasörüne kurulur, Başlat menüsü ve masaüstü kısayolu, Programlar'dan kaldırma. |
| `TD2LootAdvisor_<sürüm>_portable.zip` | Kurulumsuz sürüm: bir klasöre çıkar, `TD2LootAdvisor.exe`'yi çalıştır. |
| Source code (zip / tar.gz) | Kaynak kod (Python). |

Windows "kişisel bilgisayarınızı korudu" derse: **Ek bilgi → Yine de çalıştır** (dosya henüz kod imzalı değil).

**5.0.4 — her bilgisayarda oyunla senkron**
- **Yeni: PC ve oyun senkronizasyon aracı** (üst banttaki 🔄 *PC senkron* düğmesi ya da Ayarlar → Ekran ve oyun). Bilgisayarı (monitörler, Windows ölçeklendirmesi, işlemci, bellek, ekran kartı) ve oyunun ayarlarını tarar, bu PC'de bir eşya kartını okuma hızını ve doğruluğunu ölçer, programın ayarlarını bu PC'ye göre kurar ve bir rapor gösterir (HDR açık, özel tam ekran gibi oyun ayarı önerileriyle). Program yeni bir bilgisayarda, monitör düzeni ya da oyun çözünürlüğü değiştiğinde açılırsa senkronizasyonu kendisi önerir. Oyunun dosyalarına ve belleğine dokunulmaz.
- Program artık ana monitörü değil, oyunun penceresini okuyor: oyun hangi monitörde, hangi modda (tam ekran / kenarlıksız / pencere) ve boyutta olursa olsun yalnız oyunun alanı okunur. Pencerenin yeri Windows'tan sorulur; oyunun belleğine dokunulmaz.
- Okuma ayarları oyunun gerçek boyutundan hesaplanır: hazır listede olmayan her çözünürlük ve en-boy oranı (1680×1050, 2560×1600, dizüstü ekranlar …) desteklenir. Oyunun boyutu değişince program kendini uyarlar.
- Başka bilgisayardan kalmış ya da monitöre uymayan profil ve sabit okuma eşiği artık okumayı bozmaz: otomatiğe dönülür.
- Okuma sayısı bilgisayarın hızına göre ayarlanır (Ayarlar → OCR → Geçiş: otomatik): yavaş işlemcide kararlar gecikmez.
- Kalibrasyon ve görev bölgesi seçimi oyunun bulunduğu monitörde yapılır.

**5.0.3 — kendi kendine öğrenen eşya kütüphanesi**
- Program artık kendi uyarı penceresini okumuyor (önceki kararın yazıları yeni kartın adını kapatıyordu).
- Öğrenen kütüphane: kütüphanede olmayan marka / gear set / parça adı bir kez okununca kaydedilir (`learned_library.json`) ve hep tanınır. Örn. "Unmatched Backpack → Sırt çantası, Unit Alloys".
- "Brand Set / Gear Set" satırından marka ve set her zaman okunur; zırh kartları artık silah sanılmıyor.
- Tam eşya kütüphanesi: 39 markanın ve 29 gear set'in tüm parça adları (Unmatched Backpack, Umbra Plate Carrier, Burdenless Pack …) — ekipman kaydı 92 → 521. Silah varyantları (Black Market, Classic, Replica …) artık doğru adıyla tanınıyor.
- Son sezonların eşyaları: Red Horizon (Fafnir, Iron Will, Loaded for Bear, Ember Engine, Trick Shot, Rushdown, Melon Baller, Keeper, Teapot, Steamer), Into the Dark ve Rise Up (Caduceus, Underboss, Nurse's Kneepads, Agitator, Investor, Whiplash, Interchange, Insult to Injury …), yeni talent'ler.
- Kütüphane düzeltmeleri: ilk oyuna (TD1) ait 14 exotic çıkarıldı; Fafnir (pompalı), Whiplash (tabanca), Bulldog (holster), Royal Works bonusları düzeltildi. Aynı adı taşıyan ekipman ve silah ("Robin") karttan ayırt edilir.
- Tüm kütüphane Excel'de: `meta/TD2_Kutuphane.xlsx` (markalar, setler, exotic, named, silahlar, talent'ler, modlar, sezon yenilikleri). Excel'deki düzeltmeler `scripts/import_library_excel.py` ile programa işlenir.
- M16A2 / LVOA-C gibi tüfekler artık sniper build'leriyle eşleşmiyor.

**5.0.2 — kararlılık düzeltmeleri**
- Set parçaları yanlış yuvaya yazılıyordu (dizlik / holster / sırt çantası "eldiven" görünüyordu): düzeltildi.
- Kaydırılmış kart birleştirme artık farklı eşyaları (ör. maske + silah, eldiven + dizlik) birleştirmiyor.
- Skill build'leri "Assault Turret" yüzünden tüfeklerle eşleşiyordu: düzeltildi.
- Tanı için son 200 kart okuması `logs/ocr_history/` altında tutulur (yalnız kart metni).

**Öne çıkanlar:** yeni OCR motoru (RapidOCR; 480p'ye kadar doğru okuma, Tesseract gerekmez) · Sandık: envanter, build optimize edici,
denetim raporu, satıcı eşleştirme · telefon arkadaşı · build paylaşım kodları · gönüllü ve anonim topluluk düşüş istatistikleri ·
Asistana sor / Claude ile oku · 10 dil. Oyunun belleğine dokunmaz, yalnızca ekranı okur.

Bu dosyalar GitHub Actions'ta otomatik derlendi; kurulum dosyası Windows'ta sessizce kurulup program açılarak test edildi.
