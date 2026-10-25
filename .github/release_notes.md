## TD2 Loot Advisor — Windows

| Dosya | Ne |
|---|---|
| `TD2LootAdvisor_Setup_<sürüm>.exe` | **Kurulum dosyası** (önerilen). Yönetici izni gerekmez; kullanıcı klasörüne kurulur, Başlat menüsü ve masaüstü kısayolu, Programlar'dan kaldırma. |
| `TD2LootAdvisor_<sürüm>_portable.zip` | Kurulumsuz sürüm: bir klasöre çıkar, `TD2LootAdvisor.exe`'yi çalıştır. |
| Source code (zip / tar.gz) | Kaynak kod (Python). |

Windows "kişisel bilgisayarınızı korudu" derse: **Ek bilgi → Yine de çalıştır** (dosya henüz kod imzalı değil).

**5.0.8 — gerçekçi 3D ajanlar**
- **Eksik Parçalar sekmesindeki 3D ajan yenilendi:** beş özgün, gerçekçi ajan — Operatör, Keşifçi, Ağır Zırh, Şehir, Kutup. Her biri stüdyo ışığında render edilmiş 360° görüntülerden oluşuyor; fareyle sürükleyince döner, ◀ ▶ ile ajan değişir, seçimin kaydedilir.
- Eksik parçalar ajanın üzerinde kırmızı nabız gibi parlar, sahip olunanlar yeşil görünür; bir parçaya tıklayınca o yuva seçilir. Yuva adları ajanın iki yanında hizalı durur.
- Tasarımların tamamı özgündür (oyundan hiçbir model ya da doku kullanılmaz); insan bedeni MakeHuman'ın serbest (CC0) temel modelinden.
- Gerçekçi görüntüler bulunamazsa önceki çizim tabanlı ajan (5 model, kıyafet renkleri, ten seçimi) kullanılır.

**5.0.7 — hata bildirme ve istek menüsü**
- **Yeni: 🐞 Geri bildirim** (üst bant ve Yardım sekmesi). Hata, istek ya da soru doğrudan geliştiriciye gönderilir; GitHub hesabı gerekmez. İsteğe bağlı olarak sistem bilgisi, program kaydının son satırları ve son okunan eşya kartı eklenebilir; **Önizle** ile tam olarak ne gideceği görülür.
- Göndermeden önce kişisel bilgiler silinir: dosya yollarındaki Windows kullanıcı adı, lisans anahtarı, e-posta adresleri.
- **Raporlarım** sekmesi: gönderdiğin raporların durumu (Yeni, İncelendi, Üzerinde çalışılıyor, Tamamlandı…) ve geliştiricinin yanıtı burada görünür.
- İnternet yoksa rapor saklanır ve bağlantı gelince kendiliğinden gönderilir.
- "Yanlış okundu" düğmesi artık bu pencereyi kartın bilgileriyle doldurulmuş olarak açıyor.

**5.0.6 — menü geçişi ve kaydırılmış kartlar**
- Menü geçiş efekti yenilendi: seçili sekmenin altında kalıcı turuncu bir gösterge; sekme değişince eski sekmeden yenisine ~0,25 sn'de akıcı biçimde kayar. Sekmenin verisi animasyon bittikten sonra yenilendiği için geçiş takılmaz (eskiden pencere karartılıp açılıyor, arka plan saatiyle çakışıp titriyordu).
- Kart aşağı kaydırılınca eşyanın adı görünmüyordu: ad ve set/marka artık envanter listesindeki seçili (vurgulu) satırdan okunuyor (ör. "Striker's Pack · Striker's Battlegear"). Kaydırılan kart başka bir eşyayla birleştirilmiyor.
- Kartın başlığı ekranın en üstündeyse (uzun set açıklamasında) artık kırpılmıyor.
- Harita, projeler gibi eşya kartı olmayan ekranlardaki yazılar artık eşya sanılmıyor.

**5.0.5 — akıcılık ve fare düzeltmeleri**
- Menülere ve düğmelere tıklamak bazen algılanmıyordu (arka plandaki ajan saati görünsün diye şeffaf yapılan zemine düşen tıklamalar arka plana gidiyordu): artık bu tıklamalar programa iletiliyor; kaydırma ve sağ tıklama da.
- Pencere boşluklarında imleç Windows'un beyaz okuna dönüyordu: artık her yerde programın imleci.
- Kasma azaltıldı: arka plan saati şekilleri yeniden kullanıyor, program arka plandayken / fare hareketsizken yavaş çiziliyor, pencere sırası her karede değil saniyede bir eşitleniyor, fare izi hafifletildi.
- Oyun güncellemesi algılama: oyunun exe'si her yamada aynı sürüm numarasını (1.0.0.0) taşıdığı için yama artık dosyanın tarihi ve boyutundan da algılanıyor.

**5.0.4 — her bilgisayarda oyunla senkron**
- **Yeni: her açılışta güncelleme denetimi.** Program sürümü, eşya kütüphanesi ve oyunun kendi sürümü her açılışta denetlenir. Yenilik varsa tek pencerede gösterilir (ör. "Kütüphane: 3 yeni eşya — Fafnir, Iron Will …", "The Division 2 güncellendi 1.41 → 1.42"); seçilenler tek tıkla yüklenir, reddedilirse bir sonraki açılışta yine sorulur. Oyun bir yamayla güncellendiğinde program bunu fark edip yeni eşyaların kütüphanesini denetler (oyun yamasının kendisini Ubisoft Connect / Steam yükler).
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
