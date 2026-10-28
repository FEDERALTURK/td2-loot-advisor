# TD2 Loot Advisor tanıtım videosu

- `td2-loot-advisor-tanitim-tr-emelneural.mp4`: 2:22, 1920×1080, H.264 video, AAC ses. Daha konuşma diline yaklaştırılmış Türkçe metin ve Neural Emel anlatımı kullanır. Altyazılar görüntüye işlenmiştir.
- `td2-loot-advisor-seslendirme-tr-emelneural.mp3`: Neural Emel anlatımının ayrı ses dosyası.
- `td2-loot-advisor-tanitim-tr-emelneural.srt`: düzenleme ve alternatif altyazı için bölüm altyazıları.
- `td2-loot-advisor-tanitim-tr.mp4` ve `td2-loot-advisor-seslendirme-tr.mp3`: önceki, Microsoft Tolga ile üretilmiş sürüm.
- `narration_tr.json`: seslendirme metni ve sahne akışı.
- `build_promo.py`: sahneleri, altyazıları ve videoyu yerelde yeniden üretir.

Her sürümün gerçek ses motoru kendi `voiceover-info-*.txt` dosyasında kayıtlıdır. Oluşturulan ekranlar programın özelliklerini anlatan temsili hareketli grafiklerdir; gerçek oyun veya uygulama ekran kaydı değildir.

Yerel üretim için Pillow, NumPy ve `imageio-ffmpeg` gerekir. Betik `tr-TR-EmelNeural` Edge TTS'yi dener; servis ses üretmezse Windows'taki Microsoft Tolga sesine döner. Neural ses zorunlu tutularak üretmek için `TD2_PROMO_REQUIRE_NEURAL=1` ortam değişkeni kullanılabilir.
