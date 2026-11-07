# Faz 3 — OCR laboratuvarı ve inceleme kuyruğu

Settings → OCR içindeki **Motorları karşılaştır** düğmesi son kaydedilen kartı
RapidOCR, Windows OCR ve kurulu Tesseract yollarına aynı girdide verir. Her yol
için süre, satır sayısı, ortalama güven, metin benzerliği ve `review` işareti
raporlanır. Rapor yalnız yerel `logs/ocr_lab_latest.json` dosyasına yazılır.

OCR laboratuvarı motoru otomatik değiştirmez. En uzun/ortalama güveni yüksek
sonuç yalnız kıyaslama kazananıdır; oyun kartlarıyla ayrıca doğrulanmadan kalıcı
motor seçimi yapılmaz.

Düşük güvenli, kısmi veya geçersiz eşya okumaları yerel
`logs/ocr_review_queue.jsonl` kuyruğuna eklenir. Kayıt zorla `REVIEW` olur ve
aynı kart tekrar görülürse çoğaltılmaz. `Exotic`, `Named`, `Prototype` veya
kilitli eşyalar için bu kuyruk dışında otomatik silme/kırma yolu yoktur.

Kapsam sınırı: laboratuvar ekran görüntüsü ve yerel motorları ölçer; oyun
belleği, DLL injection, ağ tabanlı OCR ve gerçek oyun içi anti-cheat/DX12
uyumluluğu kapsam dışıdır.
