# Python 3.14 OCR beta — 9.1.5-beta.2

Bu beta, TD2 Loot Advisor'ın Python 3.14.10 ve Windows x64 OCR zincirini doğrulamak için hazırlanmıştır. Üretim sürümü olan 9.1.4'ün yerine geçmez.

## Wheel uyumluluk ön kontrolü

PyPI'den CPython 3.14 / Windows x64 binary paketleri görüldü:

- `onnxruntime 1.31.0` — `cp314-win_amd64`
- `onnxruntime-directml 1.24.4` — `cp314-win_amd64`
- `rapidocr 3.10.0` — pure Python wheel
- `ctranslate2 4.8.4` — `cp314-win_amd64`
- `sentencepiece 0.2.2` — `cp314-win_amd64`
- `faster-whisper 1.2.1` — pure Python wheel
- `Pillow 13.0.0` — `cp314-win_amd64`
- `mss 10.2.0` — pure Python wheel
- `av 19.0.2` — `cp312-abi3-win_amd64`

Bu liste paketlerin dağıtılabildiğini gösterir; OCR'nin gerçek DirectML sonucu verdiğini tek başına kanıtlamaz.

## Beta kabul kriterleri

GitHub Actions Windows çalıştırıcısı Python 3.14 ile aşağıdakileri kontrol eder:

1. RapidOCR motor importu ve gerçek örnek görüntü taraması.
2. ONNX Runtime sağlayıcılarında DirectML ve CPU'nun görünmesi.
3. CPU/DirectML OCR çıktılarının benzerliği.
4. CTranslate2 ve faster-whisper importu.
5. Tkinter arayüzünün açılması ve `UI ready` kaydı.
6. PyInstaller EXE, kurulum ve güncelleme testleri.

Bu kontrollerden biri başarısız olursa beta, Python 3.13 üretim ortamına geri alınmalıdır.
