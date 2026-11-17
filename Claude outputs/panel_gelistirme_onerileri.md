# TD2 Rapor Paneli — Geliştirme Önerileri

**Tarih:** 2026-11-15
**İncelenen sürüm:** Panel 1.5.0 (`FEDERALTURK/td2-loot-advisor-reports`, HEAD `fd393de`)
**Kapsam:** `panel/` altındaki 1.883 satırın tamamı okundu (`panel.py` 739, `tasks_tab.py` 281,
`license_tab.py` 275, `dashboard_tab.py` 222, `selfupdate.py` 116, `lock.py` 95, `github_api.py` 94,
`tray.py` 60).

Aşağıdakilerin hepsi kodda okunan somut satırlara dayanıyor. Hiçbiri "şöyle yapılsa iyi olur"
türünden genel tavsiye değil; her maddede ne olduğu, nerede olduğu ve neyi değiştireceği yazıyor.

---

## Özet: önce bunlar

| # | Ne | Tür | Emek | Kazanç |
|---|---|---|---|---|
| 1 | İki zamanlayıcı aynı anda `refresh()` çağırıyor | **Hata** | 10 dk | API kullanımı yarıya iner, arayüz titremesi biter |
| 2 | Otomatik yenileme kullanıcının sıralamasını siliyor | **Hata** | 15 dk | 3 dakikada bir bozulan sıralama düzelir |
| 3 | `comments()` hataları sessizce yutuyor | **Hata** | 10 dk | "yorum yok" yalanı biter |
| 4 | 1000 rapordan sonrası sessizce kayboluyor | **Hata** | 10 dk | Veri kaybı algısı önlenir |
| 5 | Toplu işlem yok (çoklu seçim) | Özellik | 1-2 sa | Ayıklama süresi en çok düşen kalem |
| 6 | Hazır yanıt şablonları yok | Özellik | 1-2 sa | Aynı cevabı tekrar tekrar yazma biter |
| 7 | Aynı çökmeyi bildiren raporlar gruplanmıyor | Özellik | 3-4 sa | 10 rapor → 1 satır; asıl ölçeklenme sorunu |
| 8 | ETag/`since` yok — her yenileme tam çekim | Performans | 1 sa | Rapor sayısı arttıkça kritikleşir |
| 9 | "Hangi sürümde düzeltildi" bilgisi tutulmuyor | Özellik | 1-2 sa | Kullanıcıya otomatik "v9.1.6'da düzeltildi" |
| 10 | Yeni/okunmamış rapor listede işaretlenmiyor | UX | 30 dk | Panele girince ne değiştiği anında görünür |

---

## 1. İki zamanlayıcı aynı anda `refresh()` çağırıyor — **hata**

`panel.py:_unlocked()` iki ayrı zamanlayıcı kuruyor:

```python
self.root.after(5 * 60 * 1000, self._auto)    # 5 dakika
self.root.after(3 * 60 * 1000, self._poll)    # 3 dakika
```

Ve ikisi de aynı işi yapıyor:

```python
def _auto(self):
    if self.gh and not self.locked: self.refresh()      # ← tam çekim
    self.root.after(5 * 60 * 1000, self._auto)

def _poll(self, reschedule=True):
    if reschedule: self.root.after(3 * 60 * 1000, self._poll)
    ...
    if self.gh: self.refresh()                           # ← aynı tam çekim, tekrar
    self.dash.refresh(done=self._notify)
```

`refresh()` → `gh.issues("all")` → sayfa başına bir istek, en fazla 10 sayfa. Yani saatte
**20 (5 dk) + 20 (3 dk) = 40 tam çekim** yapılıyor; hepsi aynı veriyi getiriyor. Rapor sayısı
300'ü geçince (4 sayfa) bu saatte 160 API isteği demek. Üstelik her çekim `apply_filter()` ile
tüm Treeview'ı siler ve yeniden doldurur — seçili satır korunuyor ama liste gözle görülür şekilde
titriyor.

**Düzeltme:** `_auto`'yu tamamen kaldır, tek zamanlayıcı olarak `_poll` kalsın (3 dakika zaten
yeterli). Yaklaşık 4 satır siliniyor. Risk yok, davranış aynı kalıyor, API kullanımı yarıya iniyor.

---

## 2. Otomatik yenileme kullanıcının sıralamasını siliyor — **hata**

`sort()` listeyi yerinde sıralıyor:

```python
self.issues.sort(key=key, reverse=not rev); self._sort = None if rev else col
```

Ama `_loaded()` her yenilemede listeyi komple değiştiriyor:

```python
self.issues = data        # ← sıralama gitti, API'nin verdiği sıraya (created desc) döndü
```

`_sort` alanı korunuyor ama **uygulanmıyor**. Sonuç: "Sürüm" sütununa tıklayıp sıraladın, 3 dakika
sonra liste kendiliğinden tarihe göre sıralanmış hâle atlıyor. Uzun bir ayıklama oturumunda bu
gerçekten sinir bozucu.

**Düzeltme:** `sort()` içindeki sıralama anahtarını bir alanda sakla, `_loaded()`'da
`self.issues = data` sonrasında aynı anahtarla yeniden uygula. ~10 satır.

---

## 3. `comments()` hataları sessizce yutuyor — **hata**

`github_api.py`:

```python
def comments(self, number):
    ok, res = self._req("GET", f"/repos/{self.repo}/issues/{number}/comments?per_page=100")
    return res if ok and isinstance(res, list) else []      # ← hata = boş liste
```

Diğer tüm metotlar `(ok, değer)` döndürürken bu tek metot sözleşmeyi bozuyor. Ağ koptuğunda,
token süresi dolduğunda veya 403 yediğinde panel **"henüz yorum yok"** yazıyor — yani kullanıcıya
yanıt verdiğini sanıp vermediğin, ya da var olan yanıtları görmediğin bir durum oluşabiliyor.
`_render()` zaten `comments is None` durumunu "yükleniyor…" olarak ayırt ediyor, yani üçüncü bir
durum (hata) için yer var.

**Düzeltme:** `(ok, res)` döndür; `_render()`'da hata durumunda kırmızı "yorumlar yüklenemedi:
<sebep>" göster. ~8 satır.

Ayrıca: `comments()` sayfalama yapmıyor (`per_page=100`, tek sayfa). 100'den fazla yorumu olan bir
rapor olursa sessizce kesilir — şimdilik teorik ama aynı düzeltmeyle çözülebilir.

---

## 4. 1000 rapordan sonrası sessizce kayboluyor — **hata**

```python
def issues(self, state="all", label="report", max_pages=10):
```

10 sayfa × 100 = 1000 rapor. Sınıra ulaşıldığında döngü biter ve **hiçbir uyarı verilmez** —
panel "1000 rapor yüklendi" der, geri kalanı yokmuş gibi davranır. Şu an rapor sayısı düşük
olduğu için görünmüyor, ama program büyüdükçe bir gün sessizce yanlış sayılar göstermeye başlar.

**Düzeltme:** Son sayfa doluysa (yani `len(res) == 100` iken döngü `max_pages` yüzünden bittiyse)
bir bayrak döndür ve durum çubuğunda "⚠ ilk 1000 rapor gösteriliyor" yaz. ~6 satır.

---

## 5. Toplu işlem yok — **en çok zaman kazandıracak özellik**

```python
self.tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
```

`selectmode="browse"` = aynı anda tek satır. Durum değiştirme, kapatma ve yanıtlama metotlarının
hepsi (`set_status`, `toggle_state`, `send_reply`) `self.cur` üzerinden tek rapora çalışıyor.

Gerçek kullanımda en sık yapılan iş şu: aynı hatayı bildiren 8 raporu "Mükerrer" işaretleyip
kapatmak. Şu an bu 8 × (seç → Mükerrer → "kapatılsın mı?" → Evet) = 32 tıklama.

**Düzeltme:** `selectmode="extended"` yap; `set_status`/`toggle_state`'i seçili tüm satırlar
üzerinde çalışacak şekilde döngüye al; istekleri sırayla gönder ve durum çubuğunda ilerleme göster
(`3/8 güncellendi`). Onay sorusu toplu işlemde bir kez sorulsun. ~60-80 satır.

**Tamamlayıcı:** toplu "aynı yanıtı hepsine gönder" (6. maddeyle birleşince çok güçlü).

---

## 6. Hazır yanıt şablonları yok

`send_reply()` serbest metin gönderiyor. Pratikte tekrar tekrar yazılan birkaç cevap var:
"bu v9.1.6'da düzeltildi, güncelle", "ekran görüntüsü gönderir misin", "bu beklenen davranış".

**Düzeltme:** Ayarlarda düzenlenebilir bir şablon listesi (`settings.json` içinde
`reply_templates`), yanıt kutusunun üstünde bir açılır liste; seçince metni kutuya basar (gönderi
öncesi düzenlenebilir). `{sürüm}`, `{kullanıcı}`, `{no}` gibi yer tutucular desteklenirse daha da
işe yarar. ~70 satır + ayar penceresine bir alan.

---

## 7. Aynı çökmeyi bildiren raporlar gruplanmıyor — **asıl ölçeklenme sorunu**

Rapor gövdesindeki meta zaten zengin (`github_api.parse_meta`, `panel.py:_render`):

```python
m.get("system")   # dict — Windows sürümü, Python, ekran, GPU vb.
m.get("card")     # OCR'ın okuduğu eşya kartı
m.get("log")      # program kaydının son satırları
m.get("contact")
meta.app_version / meta.lang / meta.type
```

`m["log"]` içinde aynı istisna satırı olan 10 rapor, şu an listede 10 ayrı satır. Program
kullanıcı sayısı arttıkça aynı çökme onlarca kez bildirilecek ve liste okunamaz hâle gelecek.

**Düzeltme:** `log`'dan bir **imza** çıkar (son `Traceback` bloğundaki istisna türü + en derin
proje dosyası + satır numarası; yoksa son `ERROR` satırının normalize edilmiş hâli). Listede
"Grupla" düğmesi: aynı imzalı raporlar tek satırda toplanır, "×8" rozetiyle. Gruba tıklayınca
alt raporlar açılır; grup üzerinde toplu durum değiştirme (5. madde) doğrudan çalışır.

Bu, panelin asıl değer üreteceği yer: 100 rapor arasından **kaç farklı hata** olduğunu görmek.
~150-200 satır, tek yeni dosya (`cluster.py`) + listeye bir sütun.

---

## 8. Her yenileme tam çekim — ETag ve `since` kullanılmıyor

`_req()` koşullu istek başlığı göndermiyor; `issues()` her seferinde tüm sayfaları baştan çekiyor.
GitHub REST iki mekanizma sunuyor:

- **ETag:** yanıttaki `etag` saklanıp sonraki istekte `if-none-match` olarak gönderilirse, değişiklik
  yoksa `304` döner — **hız limitinden düşmez** ve gövde aktarılmaz.
- **`since=<ISO zaman>`:** yalnız o tarihten sonra güncellenen issue'lar döner.

1. maddedeki düzeltmeyle birlikte uygulanırsa, değişiklik olmayan bir yenileme neredeyse bedava
olur (tek 304 yanıtı).

**Düzeltme:** `_req()`'e `etag` parametresi ve 304 yakalama; `issues()`'da ETag'i sayfa bazında
sakla. ~40 satır. Not: `urllib.error.HTTPError` 304'ü hata olarak fırlatır, onu ayrıca yakalamak
gerekiyor.

---

## 9. "Hangi sürümde düzeltildi" bilgisi tutulmuyor

`set_status(i, "done")` yalnız `status:done` etiketini yazıyor. Kullanıcı programdaki
"Raporlarım" bölümünde raporunun kapandığını görüyor ama **hangi sürümde düzeldiğini** görmüyor —
yani güncelleme yapması gerektiğini anlamıyor. Bu, "düzelttim ama kullanıcı hâlâ şikâyet ediyor"
döngüsünün ana sebebi.

**Düzeltme:** "Tamamlandı" işaretlenince küçük bir pencere: "hangi sürümde düzeltildi?" (varsayılan
= ana depodaki en son sürüm, `fixed:vX.Y.Z` etiketi olarak yazılır) ve isteğe bağlı olarak otomatik
bir yorum: *"Bu sorun vX.Y.Z'de düzeltildi, güncelleyince geçecek."* ~50 satır.

---

## 10. Yeni/okunmamış rapor listede işaretlenmiyor

`_new_reports` sayacı var ama yalnız tepsi bildirimi için kullanılıyor (`_notify`). Listede yeni
gelen raporu gösteren hiçbir işaret yok; `status:new` etiketi var ama o senin verdiğin durum, "ben
bunu daha önce görmedim" demek değil.

**Düzeltme:** En son görülen issue numarasını `settings.json`'a yaz; listede ondan büyük numaralı
satırlara kalın yazı tipi veya sol kenarda turuncu bir çizgi. Panel açılınca "3 yeni rapor" yazan
tıklanabilir bir filtre. ~30 satır.

---

## Küçük notlar (hata değil, temizlik)

- **`_save_pin_state()` ve `_save_key()` neredeyse birebir aynı** (`panel.py`): ikisi de dosyayı
  okuyup tek anahtar değiştirip atomik yazıyor. Tek bir `_patch_setting(key)` fonksiyonuna
  indirilebilir — ~15 satır eksilir.
- **`sort()`'taki `_sort` mantığı yanıltıcı**: aynı sütuna ikinci tıklamada `_sort = None` oluyor,
  yani üçüncü tıklama yine azalan sıralama yapıyor. Beklenen davranış artan↔azalan geçişi.
  2. maddeyle birlikte düzeltilsin.
- **Demo kodu üretimde**: `_demo_run()` yalnız `TD2_PANEL_DEMO_REPLY` ile tetikleniyor, zararsız,
  ama video/test amaçlı olduğu yorumda yazıyor — kalması sorun değil, farkında ol.
- **`github_api.parse_meta` / `label_value` için birim testi yok.** Testlerin hepsi ekran görüntüsü
  tabanlı (`panel_shot.py`, `license_shot.py`…). Bozuk/eksik meta JSON'u gelen bir rapor panelde
  ne yapar, test edilmemiş. ~40 satırlık bir `tests/test_github_api.py` bu riski kapatır.

---

## Önerilen sıra

**Önce (bir oturumda biter, hepsi düşük riskli):** 1 → 3 → 4 → 2 → 10
Dördü hata düzeltmesi, biri 30 dakikalık UX kazancı. Toplam ~60 satır değişiklik, davranışı
bozma riski düşük, hepsi mevcut ekran görüntüsü testleriyle doğrulanabilir.

**Sonra (gerçek iş kazancı):** 5 → 6 → 9
Ayıklama süresini en çok bunlar düşürür. 5 ve 6 birlikte yapılırsa "8 mükerrer raporu seç → şablon
yanıtı gönder → hepsini kapat" tek akış olur.

**En son (ölçeklenme):** 7 → 8
Rapor sayısı birkaç yüzü geçmeden acil değil, ama geçtiğinde panelin kullanılabilirliği buna
bağlı olacak.

---

## Not

Bu belge yalnız inceleme sonucudur; **hiçbir kod değiştirilmedi.** Hangi maddeleri istediğini söyle,
`AGENTS.md` akışına göre (önce plan, sonra en küçük güvenli değişiklik, sonra test) uygularım.
Panel sürümü `panel/panel.py` içinde `VERSION = "1.5.0"`; değişiklik yapılırsa `panel/CHANGES.md`
de güncellenmeli, çünkü kendini güncelleme sürüm notlarını oradan okuyor.
