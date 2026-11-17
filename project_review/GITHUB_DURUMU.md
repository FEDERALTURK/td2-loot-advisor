# GitHub durumu

27 Ekim 2026 tarihinde bağlı GitHub hesabıyla doğrudan sorgulandı.

## Depolar ve dallar

| Depo | Görünürlük | Dal / ref | Dosya |
|---|---|---|---:|
| [Ana uygulama](https://github.com/FEDERALTURK/td2-loot-advisor) | public | main 74ffcc660bb9ad87860bf5eec63f7a5a82d86a00 | 675 |
| Ana uygulama | public | feat/version-counter 1fc2553b8769f10d8aaeaf785cb4c79752e33914 | main'in yayın kodu; daha yeni feed commitleri main'de |
| [Özel panel/raporlar](https://github.com/FEDERALTURK/td2-loot-advisor-reports) | private | main fd393de7265f124113b9e6863bdbfd0e620e23ea | 28 |
| Özel panel/raporlar | private | promo 436394359e41fb53e595bb19e56666ae025dedf5 | 83 |

İlgili erişilebilir depo araması bu iki depoyu döndürdü. Ayrı üçüncü bir arşiv deposu varsayılmadı.
Özel promo ve main'deki ortak dosyaların blob kimlikleri aynı. Promo dalı ek video kaynaklarını taşır; promo.yml çalıştırıcısı main dalındadır.
Ana dalın 175 commit kaydı, özel main'in 16 ve promo'nun 18 commit kaydı listelendi. Her eski commit'in tüm diff'leri tek tek okunmadı; güncel kaynak ve önemli değişim kayıtları incelendi.

## Yayınlar

- Ana depoda dört release kaydı: v6.0.1, v6.0.0, v5.1.9 ve model paketi mt-models.
- [v6.0.1](https://github.com/FEDERALTURK/td2-loot-advisor/releases/tag/v6.0.1): 26 Ekim 2026 14:18 İstanbul; installer, portable ZIP ve SHA256SUMS.sha256 mevcut.
- Özel depoda panel-v1.5.0 ve 18 eski uygulama sürümü arşivi (toplam 19 release).
- Ana ve özel depolarda açık PR yok; alınan tüm-durum PR listeleri de boş.
- Ana depoda issue yok. Özel depodaki üç raporun üçü de kapalı; bunlar açık geliştirme backlog'u sayılmaz.
- Release dosyalarının adları/boyutları/URL'leri kaydedildi; EXE/ZIP/model ikili dosyaları indirilip incelenmedi.

## Actions kayıtları

Ana depoda 198, özel depoda 27 çalışma kaydı alındı.
Aşağıdaki public kontrollerin en son kayıtları başarıyla bitmiş. Farklı commit'lerde çalıştıkları özellikle korunmuştur.

| İş akışı | Commit | Başlama zamanı (UTC) | Sonuç |
|---|---|---|---|
| [Community tasks feed](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40473035827) | 74ffcc66 | 2026-10-27T08:22:23Z | success |
| [Translate check](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40433822033) | 74ffcc66 | 2026-10-27T01:39:04Z | success |
| [Info check](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40333116575) | 7feb2b47 | 2026-10-26T13:43:38Z | success |
| [Build Windows installer](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40313460850) | 1fc2553b | 2026-10-26T11:13:33Z | success |
| [Account check](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40312663896) | 1fc2553b | 2026-10-26T11:07:23Z | success |
| [retire-releases](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40309339323) | a4af2d78 | 2026-10-26T10:41:15Z | success |
| [Service check](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40301101392) | 69834825 | 2026-10-26T09:38:23Z | success |
| [Sync check (Windows)](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40300257837) | 23cee8d0 | 2026-10-26T09:31:46Z | success |
| [OCR engines check (Windows)](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40300248995) | 23cee8d0 | 2026-10-26T09:31:41Z | success |
| [UI check (Windows screenshot)](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40300245414) | 23cee8d0 | 2026-10-26T09:31:40Z | success |
| [Build translation model](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40267181457) | ce8c86af | 2026-10-26T04:04:36Z | success |
| [Perf check (Windows)](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40238743789) | fdad171c | 2026-10-25T22:07:58Z | success |
| [Agent 3D video (Windows)](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40236422617) | ce65b981 | 2026-10-25T21:38:20Z | success |
| [Render agents](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40234161050) | 263c6135 | 2026-10-25T21:09:35Z | success |
| [Feedback flow video (Windows)](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40226369495) | ab723f32 | 2026-10-25T19:30:40Z | success |
| [Build report panel](https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/40226202262) | a98e7b45 | 2026-10-25T19:28:33Z | success |

Mevcut public workflow dosyası 14'tür. Tarihsel Actions listesindeki panel/video işleri daha sonra özel depoya taşınmış olabilir; eski run adı güncel workflow dosyasının bulunduğunu kanıtlamaz.
Son main 74ffcc66 üzerinde Translate check ve Community tasks feed başarılı. Hesap ve installer kontrolü 6.0.1 yayın commit'i 1fc2553'te; UI/OCR/sync ve performans daha eski commit'lerde.
GitHub'daki başarılı kayıtlar bu incelemede testlerin yeniden çalıştırıldığı anlamına gelmez.

## Tanıtım videoları

[Son promo çalışması](https://github.com/FEDERALTURK/td2-loot-advisor-reports/actions/runs/40446774714) başarılı; dört artifact mevcut ve sorguda süresi dolmamış:

| Çıktı | Artifact |
|---|---|
| İngilizce yatay | video-en-main |
| Türkçe yatay | video-tr-main |
| İngilizce dikey | video-en-vertical |
| Türkçe dikey | video-tr-vertical |

Kaynak render.py varsayılanı 3840x2160 / 30 fps; dikey mod 1080x1920. Video dosyaları bu incelemede oynatılmadı; süre/çözünürlükleri yeni bir ffprobe çalıştırmasıyla doğrulanmadı.
Üretim: gerçek uygulama ekranlarını kopya üzerinde yakalama -> Chatterbox ses parçaları ve Whisper benzerlik seçimi -> özgün sentez müziği -> Pillow/ffmpeg kurgu -> SRT ve önizleme kareleri.
Ekrandaki çeviri tanıtım sahnesi özgün tasarımdır; gerçek oyun görüntüsü olarak sunulmamalı.

## Kaynak ve erişim sınırı

Bağlı hesabın eriştiği kod, branch, release, commit, issue ve Actions metaverisi incelendi. GitHub secrets değerleri, private anahtarlar, Cloudflare D1 hesap verileri ve sunucunun canlı dağıtım kodu okunmadı. Canlı sunucu dağıtımı, GitHub main ile eşit varsayılmadı.
Tam makine kaydı GITHUB_SNAPSHOT.json, ref/dosya kaydı GITHUB_FILE_INVENTORY.csv içindedir.

