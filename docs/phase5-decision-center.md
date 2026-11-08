# Faz 5 — Akıllı karar merkezi

PC tarafına kişisel hedef ile son taranan eşyayı karşılaştıran güvenli bir karar katmanı eklendi. Bu katman yalnızca `KEEP`, `REVIEW` ve hedef eşleşmesi üretir; hiçbir durumda `DISMANTLE` önermez.

Exotic, Named, Prototype veya kilitli kayıtlar tam eşleşse bile `REVIEW` olarak kalır. Düşük OCR güveni, eski kaynak veya eksik alanlar da incelemeye yönlendirilir.

Mobil tarafındaki Faz 5 güncelleme denetimi, haber/görev yenileme ve bildirim izinleri mevcut `CompanionModel` akışında korunur. Mobil mağaza yayını için gerçek cihaz, imza, Play Console ve iOS/macOS adımları hâlâ ayrı çıkış koşullarıdır.
