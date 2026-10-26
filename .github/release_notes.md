## TD2 Loot Advisor — Windows

| Dosya | Ne |
|---|---|
| `TD2LootAdvisor_Setup_<sürüm>.exe` | **Kurulum dosyası** (önerilen). Yönetici izni gerekmez; kullanıcı klasörüne kurulur, Başlat menüsü ve masaüstü kısayolu, Programlar'dan kaldırma. |
| `TD2LootAdvisor_<sürüm>_portable.zip` | Kurulumsuz sürüm: bir klasöre çıkar, `TD2LootAdvisor.exe`'yi çalıştır. |
| Source code (zip / tar.gz) | Kaynak kod (Python). |

Windows "kişisel bilgisayarınızı korudu" derse: **Ek bilgi → Yine de çalıştır** (dosya henüz kod imzalı değil).

**5.1.6 — 🌐 Canlı oyun çevirisi ve canlı haber akışı**
- **Yeni sekme: 🌐 Canlı çeviri (İngilizce → Türkçe).** Program ekrandaki İngilizce yazıyı eşya kartı okur gibi okur ve Türkçe çevirisini oyunun üstünde gösterir: altyazılar ve telsiz konuşmaları, istihbarat ve görev metinleri, menüler.
  - **Ne çevrilsin:** Altyazılar (oyun penceresinin alt kısmı), Seçili alan (bir kez seçersin) ya da Tüm oyun penceresi (yan panelde).
  - **Yazı değişince kendiliğinden çevirir**; ayrıca **F7** ile anında çeviri. Yazı boyutu, saydamlık ve gizlenme süresi ayarlanabilir.
  - **Motorlar:** *Yerel sinir ağı modeli* — OPUS-MT (Helsinki-NLP, CC-BY 4.0), bilgisayarında internetsiz ve ücretsiz çalışır, cümle başına ~0,1–0,3 sn; bir kerelik ~210 MB indirme. *Gelişmiş yapay zekâ* — Asistan'da seçtiğin Claude / OpenAI / Ollama ile, oyun bağlamını bilerek.
  - Oyun içi adlar (Black Tusk, Eagle Bearer, Striker's Battlegear, Dark Zone…) çevrilmez, Türkçe eklerle korunur ("Black Tusk'ı").
  - Yalnız ekran okunur; oyuna dokunulmaz. Kaplamanın görünmesi için oyunu kenarlıksız ya da pencere modunda oyna.
- **Canlı haber akışı:** program açıkken 30 dakikada bir yeni haber var mı diye bakar, sayfayı yeniden başlatmadan günceller; Bilgi sekmesinde okunmamış haber sayısı (●3) görünür. Yeni sezon, bakım, yeni içerik ve etkinliklerde tepside bildirim; telefon bildirimlerinde yeni "Haberler ve etkinlikler" seçeneği. Haber akışı artık günde 4 kez güncelleniyor.
- **Ansiklopedi açıklamaları Türkçe:** 300 açıklamanın Türkçesi eklendi (ilk sürüm makine çevirisi; günlük görev gözden geçirip diğer dilleri de ekleyecek). Altında İngilizce özgün metin de görünür.
- **Programa eklenen diğer diller için:** Asistan'da bir yapay zekâ seçiliyse haberler ve açıklamalar o dile bilgisayarında çevrilip saklanır.

**5.1.5 — 📚 Bilgi sekmesi ve ajan sesi**
- **Yeni sekme: 📚 Bilgi.** Dört bölüm:
  - **Ansiklopedi:** 80 egzotik, 170 adlı eşya, 29 gear set, 39 marka ve 240'tan fazla yetenek tek yerde, aranabilir. Set bonusları, parçalar, yetenek açıklamaları ve ilgili girişler; tek tıkla **build'e ekle** (gear set/marka → yeni build, egzotik/yetenek → etkin build). Premium: "Nerede düşer?" topluluk istatistiğinden.
  - **Meta build vitrini:** günlük güncellenen popüler build'ler kartlar halinde — PvE/PvP/solo/grup/son oyun ve rol etiketleri, popülerlik çubuğu, ▲ yükselişte / ▼ düşüşte / ✦ yeni işaretleri, favoriler, "build'lerimde göster / gizle", kaynak bağlantıları.
  - **Haberler ve sezon:** günlük ve haftalık sıfırlamaya geri sayım, açık görev sayısı, canlı / yakında etkinlikler ve yama notları (kalan süreyle, kaynak bağlantılı, 10 dilde). Her gün otomatik güncellenir.
  - **Bilgi yarışması:** oyun kütüphanesinden üretilen sorular (egzotiğin yuvası, marka bonusu, set yeteneği, silah türü, yetenek açıklaması…), XP, seviye ve seri. İsteğe bağlı olarak yükleme ekranlarında küçük bir soru penceresi.
- **Ajan sesi:** kararlar artık özgün "taktik asistan" cümleleriyle söyleniyor ("Egzotik tespit edildi. Saklaman önerilir."). Üç paket (Taktik asistan, Sakin operatör, Kısa ve net) + Klasik, 10 dilde; isteğe bağlı **telsiz efekti**. Asistan → ayarlar → Ses paketi.

**5.1.4 — güncelleme düzeltmesi**
- Otomatik güncellemede program artık sistem tepsisine küçülmüyor, tamamen kapanıyor; kurulum dosyaları değiştirip programı yeniden açabiliyor. Kurulum da başlamadan önce tepside açık kalmış bir programı kapatıyor (kaldırırken de).

**5.1.3 — düzeltme**
- Discord ile giriş yapınca (ya da premium açılıp kapanınca) program kendiliğinden yeniden başlıyor ve aynı sekmeye, hesap penceresiyle dönüyor. Önceden girişten sonra menüler ve pencere boyutu bozuk kalabiliyordu; kapatıp açmak gerekmiyor.

**5.1.2 — hesap, oyunla entegre hizmet**
- **Yeni: isteğe bağlı hesap — Discord ile giriş.** Program girişsiz de tamamen ücretsiz çalışır. Hesap; premium anahtarını, davet / hediye kodunu ya da satın alımı bilgisayarına bağlar. Şifre yok: kim olduğunu Discord doğrular, oturum bilgisayarında Windows'un kendi şifrelemesiyle (DPAPI) saklanır. İlk açılışta karşılama penceresi çıkar ("Girişsiz devam et" ile geçilebilir); üst banttaki **👤 Giriş yap** her zaman orada.
- **Kod kullan:** `TD2K-…` lisans anahtarı, `TD2I-…` davet kodu ya da satın alma anahtarı tek kutuya yazılır. Bir lisans bir bilgisayarda çalışır; premium 7 gün internetsiz geçerlidir ve kendiliğinden yenilenir. Eski `TD2P-` anahtarlar çalışmaya devam eder.
- **Yeni: 🛰 Hizmet (Ayarlar).** Oyun açılınca tarama kendiliğinden başlar, kapanınca durur; oturum özeti (okunan, saklanan, kırılan, egzotik) kaydedilir. Sistem tepsisi simgesi, "pencereyi kapatınca tepside kalsın", **Windows ile başlat**.
- **Akıllı tarama:** program menü / sahada / yükleme ekranlarını tanır; sahadayken ve yükleme ekranında boşuna okuma yapmaz. Sabit metin aramaz — bir kart her başarıyla okunduğunda o ekranı kendisi öğrenir, her dilde ve çözünürlükte çalışır. Üst bantta oyunun durumu görünür (🎮 Menüde).
- **Discord durumu:** isteğe bağlı olarak Discord'da "TD2 Loot Advisor — Envanteri düzenliyor · 23 eşya · 2 egzotik" gösterir (bilgisayardaki Discord uygulamasıyla; sunucumuza bir şey gitmez).
- **Premium — yerel API:** OBS için şeffaf canlı karar kartı (Tarayıcı Kaynağı), Stream Deck düğmeleri (başlat / durdur / tara) ve WebSocket. Varsayılan yalnız bu bilgisayar; her adres gizli bir anahtar içerir.
- **Premium — telefon bildirimleri:** egzotik / adlı "SAKLA", build yükseltmesi, satıcı eşleşmesi ve oturum özeti telefona gelir — ücretsiz **ntfy** uygulaması (QR ile abone ol) ya da kendi Discord sunucuna webhook.
- Hiçbiri oyunun belleğine, dosyalarına ya da ağ trafiğine dokunmaz; oyun yalnız pencere adından tanınır, durum yalnız ekrandan okunur.

**5.1.0 — ekran kartıyla okuma**
- **Yeni: ekran kartıyla OCR (DirectML).** Kart okuma artık ekran kartında çalışabiliyor (DirectX 12 destekleyen her ekran kartı: NVIDIA, AMD, Intel). İlk açılışta program bunu ayrı bir süreçte güvenle dener: sonuç işlemciyle aynıysa ve daha hızlıysa açar, değilse işlemcide kalır. Sürücü sorunu olsa bile program etkilenmez.
- Ayarlar → OCR'da yeni satır: **Ekran kartıyla hızlandır** (Otomatik / Açık / Kapalı) ve bu bilgisayardaki ölçüm ("işlemci 1350 ms → ekran kartı 400 ms" gibi).
- **Ondalık onarımı:** OCR noktayı kaçırdığında ("+60%" Kritik Şans) değer atılmıyor, oyunun sınırlarına göre onarılıyor (6.0%). Onarılan değerler "şüpheli" sayılır ve kart bir kez daha okunur.

**5.0.9 — hız**
- **Eşya tanıma 2–15 kat hızlı:** okunan yazıyı eşya kütüphanesiyle eşleştirme, ilk okumada yaklaşık 2 kat, aynı taramadaki tekrarlarda 13–15 kat hızlandı (Windows ölçümü: kart başına 360–630 ms → 27–47 ms). Sonuçlar eskisiyle birebir aynı (200.000 karşılaştırmada fark yok).
- **Gereksiz okumalar kaldırıldı:** hızlı bilgisayarlarda her kart 3 kez okunuyordu. İlk okuma eşyayı tam güvenle tanıdıysa ve rakamlar net okunduysa ek okuma yapılmıyor; kart başına 1,5–4,5 sn tasarruf. Kaydırılmış/eksik kartlarda eskisi gibi çoklu okuma yapılır.
- **Otomatik taramada daha az işlemci:** "ekran değişti mi?" denetimi tam görüntü üretmeden ham piksellerden yapılıyor ve yakalayıcı her seferinde yeniden açılmıyor (3440×1440'ta tur başına 64 ms → 8 ms; 1024×768'de 32 → 16 ms).
- Son okunan kartın görüntüsü diske arka planda yazılıyor (tarama beklemiyor).
- Açılış: yedek OCR motoru (Tesseract) yalnız kuruluysa yükleniyor, RapidOCR'ın varlığı yüklenmeden denetleniyor — özellikle bilgisayar yeni açıldığında daha hızlı başlangıç.

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
