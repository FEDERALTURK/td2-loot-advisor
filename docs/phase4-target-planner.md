# Faz 4 — Kişisel hedef ve farm planı

Komuta Merkezi içindeki hedef alanı, kullanıcı hedeflerini yalnızca yerel `targets.json` dosyasına kaydeder. Hedefler eşya adı, yuva, attribute, talent, Prototype Augment ve öncelik alanlarını destekler.

Farm eşleştirme motoru satıcı ve hedef-loot önbelleklerini kaynak olarak kullanır. Kaynağın tarihi cadence'e göre geçmişse veya güveni düşükse sonuç `REVIEW` olur; veri yoksa `NO_MATCH` gösterilir. Sonuçlar planlama bilgisidir, otomatik silme/kırma veya oyun değişikliği yapmaz.

Doğrulama:

```powershell
python -m unittest -v tests/test_target_planner.py
python -B tests/test_stability_widgets.py
python -m py_compile target_planner.py app.py
```
