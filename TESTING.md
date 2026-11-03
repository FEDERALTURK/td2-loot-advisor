# Test Prosedürleri

Proje talimatlarının 9. ve 17. maddeleri kapsamında tutulan, gerçekten çalıştırılmış ve doğrulanmış test prosedürü.

## Ortam gereksinimleri

- **tkinter**: Bu sandbox'ta varsayılan `python3` (3.13) tkinter içermiyor. GUI'ye dokunan testler **`python3.12`** ile çalıştırılmalı (`python3-tk` kurulu).
- **Headless GUI (Linux sandbox)**: Windows masaüstü uygulaması olduğu için Linux'ta Tk penceresi açmak `Xvfb` gerektirir: `xvfb-run -a -s "-screen 0 1280x800x24" python3.12 ...`.
- **Gerçek Windows testi**: Bu geliştirme ortamı Linux'tur; `Xvfb` + Linux Tk ile doğrulanan davranış, gerçek Windows + DWM/DX12 render yolunu %100 garanti etmez (bkz. 9.1.5.10–9.1.5.17 arası Windows'a özgü render hataları — hepsi gerçek Windows'ta bulunup düzeltildi). Gerçek Windows doğrulaması, bağlı bir Windows bilgisayarı üzerinden ayrıca yapılmalı.
- **Framework**: Depodaki testler **karışık**: bazıları (`test_app_stability.py`, `test_diagnostics_center.py`, `test_project_structure.py` vb.) `unittest` tabanlı, bazıları (`test_core.py`, `test_regression_crash_patterns.py` çalıştırılabilir ama asıl `unittest.TestCase` olarak yazıldı) pytest-stili düz fonksiyon. **pytest kurulu olmalı** (`pip install pytest` veya `python3.12 -m pip install --break-system-packages pytest`) — aksi halde `test_core.py` gibi düz-fonksiyon test dosyaları `unittest discover` ile "NO TESTS RAN" verir.
- **Dev bağımlılıkları**: `pip install -r requirements-dev.txt` (openpyxl) olmadan `test_core.py::test_excel_library_in_sync` `ModuleNotFoundError` ile başarısız olur — bu beklenen bir ortam eksikliğidir, kod hatası değildir.

## Bu oturumda gerçekten çalıştırılan testler ve sonuçları

| Test | Komut | Sonuç |
|---|---|---|
| `py_compile` (tüm `.py` dosyaları) | `python3 -m py_compile $(git ls-files '*.py')` | Temiz, hata yok |
| `tests/test_app_stability.py` | `xvfb-run -a ... python3.12 -B -m unittest discover -s tests -p test_app_stability.py` | 17/17 PASS |
| `tests/test_translation_reliability.py` | aynı yöntem | 9/9 PASS |
| `tests/test_diagnostics_center.py` | aynı yöntem | PASS |
| `tests/test_project_structure.py` | aynı yöntem | 6/6 PASS |
| `tests/test_stability_widgets.py` | aynı yöntem (gerçek uygulama açılışı, 14 sayfa/6 sekme) | PASS, 0 callback hatası |
| `tests/test_core.py` | `xvfb-run -a ... python3.12 -B -m pytest tests/test_core.py -v` | **18/18 PASS** (önce `openpyxl` eksikken 17/18 — bkz. DEPENDENCIES.md) |
| `tests/test_regression_crash_patterns.py` (yeni, 9.1.5.19 sonrası eklendi) | `python3.12 -B -m unittest discover -s tests -p test_regression_crash_patterns.py -v` | 2/2 PASS |

## Statik analiz

```
pip install --break-system-packages ruff
ruff check . --select F,E9           # gerçek hata odaklı (tanımsız ad, kullanılmayan import, syntax)
ruff check . --select F,E9 --fix     # güvenli otomatik düzeltme
```

Daha geniş `--select B,F,E9` (bugbear stil kuralları) **kasıtlı olarak topluca uygulanmadı** — bu sandbox'ta tam Windows test matrisi çalıştırılamadığı için regresyon riski taşıyor. Tek tek değerlendirilmeli.

## Henüz eklenmemiş / eksik test kapsamı

- `webbrowser`/except-closure sınıfı hatalar artık `test_regression_crash_patterns.py` ile statik olarak korunuyor, ama **gerçek buton tıklamasıyla** (örn. Tk widget'ı bulup `invoke()` çağırarak) uçtan uca doğrulanmıyor.
- Android/iOS mobil companion (`mobile/`) için bu depoda otomatik test çalıştırılmadı (Flutter test aracı bu oturumda kullanılmadı); `mobile/test/` dizini var ama içeriği ayrıca incelenmeli.
- `server/test_*.mjs` (Node.js) testleri bu oturumda **çalıştırılmadı** — sadece dosya varlığı biliniyor.
