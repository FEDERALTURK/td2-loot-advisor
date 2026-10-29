# Kütüphane denetimi — 9.1.2

Denetim tarihi: 2026-10-29

`meta/game_data.json` ve `builds.json` birlikte tarandı. Build kayıtları oyun kütüphanesindeki canonical adlar ve attribute anahtarlarıyla karşılaştırıldı.

## Mevcut kapsam

| Kategori | Kayıt |
|---|---:|
| Exotic | 87 |
| Named | 189 |
| Gear set | 28 |
| Marka | 40 |
| Silah | 387 |
| Silah modu | 255 |
| Ekipman modu | 17 |
| Skill varyantı | 43 |
| Prototype augment | 9 |
| Attribute | 44 |
| Türetilmiş talent | 414 |

## Sonuç

- 18 build tarandı.
- Build'lerde kullanılan attribute anahtarlarından kütüphanede olmayan kayıt: **0**.
- Build source/gear set referanslarında gerçek eksik kayıt bulunmadı. `Striker` kısa adı, kütüphanedeki `Striker's Battlegear` kaydına karşılık geliyor.
- Aynı eşyanın noktalama/boşluk farkıyla görünen dört Named ve iki silah varyantı bulundu; bunlar OCR eşleştirmesinde normalize ediliyor, yeni item olarak çoğaltılmıyor.
- Doğrulanamayan yeni sezon veya topluluk iddiaları kütüphaneye eklenmedi.

Bu rapor, kütüphanede doğrulanmış bir eksik olmadığını; kalan adayların yeni kaynak verisiyle teyit edilmesi gerektiğini gösterir.
