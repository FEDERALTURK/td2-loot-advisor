# Tanıtım videosu (TD2 Loot Advisor)

- `capture.py`: programın gerçek ekranları, Xvfb 3840x2160 üzerinde 2x ölçekle (Linux'ta; yazı tipi Windows'tan farklıdır).
- `gen_vo.py`: anlatım — Chatterbox Multilingual (Resemble AI, MIT lisansı). Ses tınısı için referans: `ref_voice.wav`,
  CC0 lisanslı Piper "en_US-joe-medium" sesiyle üretilmiş bir cümle. Her parça Whisper ile dinlenip metne en yakın deneme seçilir.
  Chatterbox çıktısına görünmez Perth filigranı ekler (yapay ses olduğunu belirtir).
- `music.py`: tamamen sentezlenmiş özgün müzik (örnek/kayıt yok).
- `render.py`: kurgu (Pillow + ffmpeg), 4K 30 fps; `--vertical` 1080x1920 altyazılı kesit; SRT altyazı.
- Yazı tipleri: Rajdhani (OFL), Inter (OFL).
- Oyunun kendi görüntüsü yok; çeviri sahnesindeki "COMMS LOG" paneli özgün tasarımdır, çeviriler programın yerel modelinin gerçek çıktısıdır.

