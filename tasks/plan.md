# Faz 4 — Kişisel hedef ve farm planı

## Amaç
Kullanıcının eşya/slot/attribute/talent/Prototype Augment hedeflerini yerel olarak saklamak ve mevcut görev, satıcı ve hedef-loot verileriyle güvenli biçimde eşleştirmek.

## Sınırlar
- Yalnızca yerel JSON ve mevcut veri sağlayıcılarının çıktıları kullanılır.
- Oyun belleği, DLL injection, anti-cheat ve oyun dosyası değişikliği yoktur.
- Düşük güvenli veya eski kaynaklar `REVIEW` olarak raporlanır.
- Exotic, Named, Prototype ve kilitli eşyalar için silme/kırma kararı üretilmez.

## Dilimler
1. Hedef kayıt sözleşmesi ve normalizasyonu — doğrulama testleri.
2. Görev/satıcı/hedef-loot kaynaklarını eşleştiren saf farm-plan motoru — stale/uncertain testleri.
3. Yerel `targets.json` kalıcılığı ve güvenli atomik yazma.
4. Uygulamadaki mevcut Ekipman → Sandık → Komuta Merkezi yüzeyine salt-okunur plan özeti ekleme.
5. İlgili regresyon testleri ve derleme doğrulaması.
