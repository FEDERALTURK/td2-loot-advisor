# Faz 2 — Yerel overlay sağlık testi

Kaynak sürüm için `scripts/overlay_health_check.bat` çalıştırılır. Python 3.13,
kurulu RapidOCR ve `models/en-tr` içindeki yerel model gereklidir. Model indirilmez.
JSON raporu benzersiz isimle Windows geçici klasörüne yazılır; GitHub'a gönderilmez.

Test sentetik İngilizce kartı masaüstünde gösterir, ekran yakalamasını gerçek OCR
ve yerel çeviri yolundan geçirir. Yakalama, OCR, çeviri, koordinatlar ve gerçek
ekran piksellerindeki metin ayrı raporlanır. Pencerenin yalnız var olması başarı değildir.
Görünürlük ölçümü sırasında yalnız test overlay'inin yakalamadan dışlanması ertelenir;
ardından dışlama etkinleştirilerek arka plandaki sentetik görüntüyle karşılaştırılır.

Yerinde overlay oluşturma/yerleşim hatasında çeviri panelde ve geçmişte kalır.
Başka bir overlay açılmaz. Başlatılırken hata veren native pencereler de temizlenir.
Bu geri dönüş, sürücünün sessizce çizmediği tüm durumları otomatik algıladığı anlamına gelmez.

## Doğrulama sınırları

- Foreground pencere korunması ve Windows click-through stil bitleri ölçülür.
- Tk ölçek değerleri 1.0, 1.5, 2.0 ile tekrar çizim yapılır.
- Gerçek fare tıklamasının alttaki oyuna geçmesi ve monitörler arasında DPI
  değişimi etkileşimli test gerektirir. Stil bitleri fiziksel tıklama kanıtı değildir.
- Sentetik masaüstü testi oyun/DX12, HDR veya tam ekran uyumluluğu kanıtlamaz.
- Test sırasında başka pencerelerin sentetik alanı kapatması ölçümü bozabilir.

## Regresyon testleri

Her dosya ayrı süreçte çalıştırılır:

```powershell
py -3.13 -B tests/test_translation_controls.py
py -3.13 -B tests/test_inplace_anchors.py
py -3.13 -B tests/test_overlay.py
py -3.13 -B tests/test_translation_reliability.py
py -3.13 -B tests/test_stability_widgets.py
```

Bu faz yerelde hazırlanır; yayın ve installer üretimi için ayrıca kullanıcı onayı gerekir.
