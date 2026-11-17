# Codex Görev Promptu — "Info check" CI hatasını kalıcı olarak kapat

Bu belgenin **1. bölümü** doğrudan Codex'e yapıştırılacak prompttur.
**2. bölüm** sana yönelik: sorunun neden oluştuğu ve tekrarlanmaması için ne yapılması gerektiği.

---

# 1. BÖLÜM — Codex'e yapıştırılacak prompt

```text
GÖREV: "Info check" CI akışını kalıcı olarak düzelt ve aynı sınıf hatanın tekrarını engelle.

Çalışma dizini: C:\Users\PC\Desktop\Thedivision2program
Çalışma dili: Türkçe. Kod, dosya adı ve komutlar özgün kalsın.
Bağlayıcı kurallar: önce AGENTS.md oku ve ona uy.

## Durum (doğrulanmış kanıt — tahmin değil)

CI'da "Info check" akışı sürekli patlıyor. Hata her push'ta değil, belirli
commit'lerde çıkıyor ve kim push ederse etsin oluyor (Feeds botunun kendi
push'unda da patladı). Gerçek hata:

  File "tests\test_knowledge.py", line 57, in <module>
    ok(st["y8s3-red-moon-unleashed"] == "live" and st["y8s3-vanguard-overdrive"] == "upcoming"
       and st["tu-y8s3-2"] == "news", "durumlar: canlı / yakında / haber")
  KeyError: 'y8s3-red-moon-unleashed'

KÖK NEDEN İKİ KATMANLI:

(1) tests/test_knowledge.py, meta/news_feed.json içindeki SABİT KODLANMIŞ haber
    kimliklerine bağlı. Bu dosyayı Feeds botu her gün otomatik güncelliyor.
    "y8s3-red-moon-unleashed" haberini bot 2026-11-06'da sildi (commit c2f7ebf,
    "news +0 -4"). O tarihten sonra bu testi içeren her commit patlıyor.

(2) Bu testin DOĞRU HÂLİ ZATEN YAZILMIŞ ama main dalına hiç girmemiş.
    v9.1.5.39 etiketindeki (commit 35d7e2dc) sürüm sabit kimlik yerine kendi
    fixture'ını kullanıyor ve geçiyor. Doğrulama:
      git merge-base --is-ancestor 35d7e2dc origin/main   → HAYIR, main'de yok
    Yani main'den kesilen her tag ve her merge, düzeltilmiş testin üstüne
    eski bozuk sürümü geri getiriyor.

Kanıt tablosu (gerçek CI koşuları):
  v9.1.5.37 (15:47) commit 061807c9  test düzeltilmiş  → BAŞARILI
  v9.1.5.39 (16:09) commit 35d7e2dc  test düzeltilmiş  → BAŞARILI
  v9.1.5.37 (19:51) commit 19849390  test BOZUK        → BAŞARISIZ
  v9.1.5.36         commit 25a91dae  test BOZUK        → BAŞARISIZ
  Feeds/main        commit 006c6f2   test BOZUK        → BAŞARISIZ

DİKKAT: v9.1.5.37 etiketi iki FARKLI commit'e işaret etmiş (061807c9 ve
19849390). Yani yayınlanmış bir etiket taşınmış. Bunu da raporla.

## Yapılacaklar

ADIM 0 — Durum tespiti (kod değiştirme)
  git status --short
  git fetch origin
  git log --oneline -5 origin/main
  git merge-base --is-ancestor 35d7e2dc origin/main; echo $LASTEXITCODE
  Çalışma ağacında kaydedilmemiş kullanıcı değişikliği varsa DOKUNMA, raporla ve dur.

ADIM 1 — Hatayı yerelde yeniden üret (düzeltmeden ÖNCE başarısızlığı göster)
  python -B tests\test_knowledge.py
  Beklenen: KeyError: 'y8s3-red-moon-unleashed'. Çıktıyı rapora koy.
  Bu adım hata vermezse DUR ve bildir — teşhis yanlış demektir.

ADIM 2 — Düzeltilmiş sürümü incele
  git show 35d7e2dc:tests/test_knowledge.py > %TEMP%\test_knowledge_fixed.py
  İki dosyayı karşılaştır. Düzeltme şu yaklaşımı kullanıyor: canlı
  news_feed.json yerine testin kendi oluşturduğu fixture listesi:

    status_fixture = [
        {"id": "fixture-live", "start": ..., "end": ..., "date": None},
        {"id": "fixture-upcoming", "start": ..., "end": None, "date": None},
        {"id": "fixture-news", "start": None, "end": None, "date": ...},
    ]
    st = {it["id"]: s for it, s in knowledge.news_sorted(status_fixture, t0)}
    ok(st == {"fixture-live": "live", "fixture-upcoming": "upcoming",
              "fixture-news": "news"}, "durumlar: canlı / yakında / haber")

ADIM 3 — Düzeltmeyi main üzerindeki dosyaya taşı
  Sadece canlı veriye bağlı assertion'ları fixture tabanlı hâle getir.
  main'deki diğer değişiklikleri (35d7e2dc'de olmayan satırları) KORU —
  dosyayı komple üzerine YAZMA, iki sürümü birleştir.
  Aynı sorunu taşıyan diğer satırları da düzelt: "biten etkinlik 3 gün sonra
  listeden düşer" testi de aynı sabit kimliği kullanıyor (satır ~61).

  YASAK: assertion'ı silerek, try/except ile susturarak, testi atlayarak veya
  .get() ile varsayılan döndürerek "geçer hâle getirme". Testin ölçtüğü
  davranış (canlı/yakında/haber sınıflandırması) aynen ölçülmeye devam etmeli,
  sadece veri kaynağı canlı akış yerine sabit fixture olmalı.

ADIM 4 — Aynı sınıf başka test var mı, tara
  tests\ altındaki TÜM dosyalarda, meta\ altındaki bot tarafından güncellenen
  JSON dosyalarından gelen sabit kimlik/metin kullanımı ara:
    meta\news_feed.json, meta\tasks_feed.json, meta\meta_builds.json,
    meta\game_data.json, meta\sources\*.json
  Bulduklarını listele. Aynı kırılganlığı taşıyanları da fixture'a çevir.
  Hiçbirini sessizce bırakma; düzeltmediklerini gerekçesiyle raporla.

ADIM 5 — Koruma testi ekle (tekrarı önleyen asıl iş)
  tests\test_project_structure.py dosyasına yeni bir kontrol ekle:
  tests\ altındaki her .py dosyasını oku; meta\news_feed.json ve
  meta\tasks_feed.json içindeki "id" değerlerini topla; bir test dosyası
  bu kimliklerden birini string literal olarak içeriyorsa testi BAŞARISIZ yap
  ve hangi dosya/satır olduğunu yaz.
  Mesaj şu olsun: "Test, bot tarafından güncellenen canlı veriye bağlı:
  <dosya>:<satır> '<kimlik>'. Fixture kullan."
  Bu kontrol, gelecekte aynı hatayı CI'da değil, yazıldığı anda yakalar.

ADIM 6 — Doğrula
  python -B tests\test_knowledge.py          → geçmeli
  python -B tests\test_project_structure.py  → geçmeli
  python -B tests\ui_info_test.py            → geçmeli (Info check akışı bunu da koşuyor)
  python -B tests\voice_diag.py              → geçmeli
  Her komutun gerçek çıktısını rapora koy. Çalıştırmadığın bir testi
  "geçti" diye yazma.

ADIM 7 — Commit ve push
  Sadece dokunduğun dosyaları ekle (git add -A KULLANMA).
  Commit mesajı Türkçe, kök nedeni açıklasın.
  main dalına push et.
  AGENTS.md madde 6: commit ve push serbest. Public Release/tag YAPMA —
  onun için ayrıca onay gerekir.

ADIM 8 — Rapor
  1. Yeniden üretilen hata (ADIM 1 çıktısı)
  2. Kök neden (iki katman: canlı veri bağımlılığı + düzeltmenin main'e girmemesi)
  3. Değiştirilen dosyalar ve satırlar
  4. ADIM 4'te bulunan diğer kırılgan testler
  5. Eklenen koruma testi ve nasıl çalıştığı
  6. Çalıştırılan testler ve GERÇEK sonuçları
  7. Taşınmış v9.1.5.37 etiketi hakkında gözlemin
  8. Kalan riskler / yapılmayanlar

## Kesin kurallar
- Test geçsin diye assertion zayıflatma, susturma, atlama YOK.
- meta\ altındaki canlı veri dosyalarını DÜZENLEME — sorun veride değil, testte.
- Büyük refactor YOK; yalnız bu görevin dosyalarına dokun.
- Kullanıcının kaydedilmemiş değişikliklerini ezme.
- git reset --hard, git checkout --, toplu silme YOK.
- Test edilmemiş bir şeyi "çalışıyor" diye raporlama.
- Emin olmadığın yerde tahmin etme; [Doğrulanmadı] diye işaretle.
```

---

# 2. BÖLÜM — Neden oldu ve bir daha olmaması için ne yapmalı

Bu olayın **iki ayrı** sebebi var. Yalnız testi düzeltmek birincisini çözer, ikincisi
devam ederse aynı hata başka bir dosyada geri gelir.

## Sebep 1: Test, kendi kendini güncelleyen veriye bağlanmış

`tests/test_knowledge.py` canlı `meta/news_feed.json` dosyasındaki bir haberin
kimliğini ezbere biliyordu. O haber oyunun gündeminden düşünce Feeds botu onu
sildi ve test çöktü. **Testin ölçmek istediği şey** (bir etkinliğin tarihine göre
"canlı / yakında / haber" diye sınıflandırılması) ile **kullandığı veri** (bugünkü
gerçek haber akışı) birbirine karışmış.

Kural: bir testin ölçtüğü davranış sabitse, verisi de sabit olmalı. Canlı veri
ancak "bu dosya geçerli JSON mu, her haberin kaynağı var mı" gibi **şema**
testlerinde kullanılır — nitekim aynı dosyadaki o testler bugün de geçiyor.

Bunun kalıcı korumasını **ADIM 5** sağlıyor: bir test dosyası canlı akıştan gelen
bir kimliği string olarak içerirse, `test_project_structure.py` bunu anında
yakalayacak. Böylece aynı hata bir daha CI'da değil, yazıldığı anda görülür.

## Sebep 2: Düzeltme bir dalda kalmış, main'e dönmemiş — asıl sorun bu

Daha önemlisi bu. Testin doğru hâli **zaten yazılmıştı** (`35d7e2dc`, `v9.1.5.39`),
ama `main`'e hiç birleştirilmedi:

```
git merge-base --is-ancestor 35d7e2dc origin/main  →  HAYIR
```

Sonuç: `main` hâlâ bozuk sürümü taşıyor. `main`'den kesilen her yeni tag, çözülmüş
bir hatayı geri getiriyor. Yani aynı hatayı **iki kez çözdünüz ve ikisi de kayboldu**.

Bu, `HANDOFF.md`'de işaretlediğim dal ayrışmasının somut bedeli. Aynı desen zaten
başka yerlerde de var: bulut deposu ile yerel `Thedivision2program` klasörü arasında
senkronize olmayan commit'ler, iki farklı Android imzalama secret şeması.

### Ne yapmalı

**a) Sürüm dalı her zaman main'e geri birleşsin.** Yayından sonra:

```powershell
git checkout main
git pull
git merge --no-ff codex/release-X.Y.Z
git push origin main
```

Birleştirmeyi atlamak, o daldaki her düzeltmeyi çöpe atmak demek.

**b) Yayınlanmış etiketi asla taşıma.** `v9.1.5.37` iki farklı commit'e işaret etmiş
(`061807c9` ve `19849390`). Bu, "aynı sürüm" adının iki farklı koda karşılık gelmesi
demek — hangi kullanıcının hangi kodu çalıştırdığı belirsizleşir ve CI sonuçları
anlamsızlaşır. Yanlış bir tag atıldıysa onu taşıma; bir üst yama sürümü aç.

**c) Tag push'unda bir "ata kontrolü" ekle.** CI'ya küçük bir adım: etiketin işaret
ettiği commit `main`'in atası veya torunu değilse uyar. Böylece main'den kopmuş bir
noktadan yayın yapıldığında anında görürsün.

**d) Feeds botu kendi değişikliğini test etsin.** Bot `meta/*.json` dosyalarını her
gün değiştiriyor ve bu dosyalara dokunan testler var. Bot commit etmeden önce ilgili
testleri koşsun; kırıyorsa commit etmeyip bildirsin. Aksi hâlde bot, farkında olmadan
CI'yı kırmaya devam eder — bugün olan tam olarak buydu.

**e) `AGENTS.md`'ye iki satır ekle.** Kuralın yazılı olmadığı yerde tekrarlanır:

```markdown
### Test verisi
- Testler `meta/` altındaki bot tarafından güncellenen dosyalardan sabit kimlik,
  başlık veya metin kullanamaz. Davranış testleri kendi fixture'ını oluşturur;
  canlı dosyalar yalnız şema/geçerlilik testlerinde kullanılır.

### Dal ve etiket hijyeni
- Her sürüm dalı yayından sonra `main`'e geri birleştirilir.
- Yayınlanmış bir etiket başka bir commit'e taşınmaz; gerekirse yeni yama sürümü açılır.
```

## Sıralama önerisi

1. Önce yukarıdaki promptu Codex'e ver — test düzelir, koruma testi eklenir.
2. Sonra (a) ve (b) alışkanlığa dönüşsün — asıl tekrarı önleyen bunlar.
3. (c) ve (d) CI tarafı; bir sonraki oturumda yapılabilir.
4. (e) hemen yapılsın, çünkü kuralı yazmak 2 dakika ve diğer her şeyi besliyor.

---

**Not:** "prompt master reposu" ile neyi kastettiğini çıkaramadım — `FEDERALTURK`
hesabındaki depoları bu oturumdan listeleyemiyorum (GitHub erişimim yalnız
`td2-loot-advisor` ve `td2-loot-advisor-reports` ile sınırlı). Projede bulduğum tek
Codex yapılandırması `.agents/` dizini (config.toml + skills) ve kök `AGENTS.md`.
Promptu ona göre yazdım. Başka bir prompt deposu/şablonu kastediyorsan adını ya da
bağlantısını ver, formatı ona uydururum.
