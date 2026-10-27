"""Pre-render fixed TR/EN notifications. Runtime playback is fully offline.

Build-only dependencies: edge-tts, av. Only the fixed phrases below are sent to
the speech service; no user settings, game text or personal data are read.
"""
import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]
VOICES = {
    "natural_tr": ("tr", "Türkçe — Doğal", "tr-TR-EmelNeural", {
        "keep": "Bu eşyayı sakla. İşine yarayabilir.",
        "consider": "Bu eşya değerlendirilmeye değer. Bir göz at.",
        "dismantle": "Mevcut tercihlerine göre bu eşyayı parçalayabilirsin.",
        "review": "Bu eşyayı elle kontrol etmeni öneriyorum.",
        "exotic": "Egzotik bir eşya bulundu. Saklamayı unutma.",
        "named": "Özel isimli bir eşya bulundu.",
        "build": "Seçili diziliminle uyumlu bir eşya.",
        "fills_gap": "Bu parça eksik bir yuvayı tamamlıyor.",
        "upgrade": "Güzel bir gelişme. Mevcut parçandan daha iyi görünüyor.",
        "demo": "Merhaba ajan. Eşyalarını birlikte değerlendirelim. Hazırım, başlayabiliriz."}),
    "natural_en": ("en", "English — Natural", "en-US-AriaNeural", {
        "keep": "Keep this item. It could be useful.",
        "consider": "This item is worth a closer look.",
        "dismantle": "Based on your current preferences, you can dismantle this item.",
        "review": "I recommend checking this item yourself.",
        "exotic": "Exotic item detected. Make sure to keep it safe.",
        "named": "A named item has been found.",
        "build": "This item matches your selected build.",
        "fills_gap": "This piece fills an empty slot in your build.",
        "upgrade": "A nice upgrade. This looks better than your current piece.",
        "demo": "Hello, agent. Let's take a look at your gear. I'm ready when you are."}),
}


def pcm(src, dest):
    import av
    with av.open(str(src)) as container, wave.open(str(dest), "wb") as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(24000)
        resampler = av.AudioResampler(format="s16", layout="mono", rate=24000)
        for frame in container.decode(audio=0):
            for result in resampler.resample(frame):
                output.writeframes(result.to_ndarray().tobytes())
        for result in resampler.resample(None):
            output.writeframes(result.to_ndarray().tobytes())


async def main():
    import edge_tts
    live = await edge_tts.list_voices()
    available = {v["ShortName"] for v in live}
    manifest = {"schema": 1, "engine": "Microsoft Edge Neural via edge-tts", "runtime": "offline PCM WAV", "packs": {}}
    for pack, (lang, title, voice, phrases) in VOICES.items():
        if voice not in available: raise RuntimeError("Voice unavailable: " + voice)
        directory = ROOT / "meta/voices" / pack
        directory.mkdir(parents=True, exist_ok=True)
        events = {}
        for event, text in phrases.items():
            target = directory / (event + ".wav")
            import sys
            if "--resume" in sys.argv and target.exists():
                with wave.open(str(target)) as wav:
                    duration = wav.getnframes() / wav.getframerate()
                if duration > .3:
                    events[event] = {"file": f"voices/{pack}/{event}.wav", "text": text,
                                     "seconds": round(duration, 3), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
                    print(pack, event, "verified existing", flush=True)
                    continue
            for attempt in range(3):
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        mp3 = Path(tmp) / "speech.mp3"
                        await edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz",
                                                   connect_timeout=10, receive_timeout=15).save(str(mp3))
                        if mp3.stat().st_size < 1000: raise RuntimeError("Empty speech")
                        pcm(mp3, target)
                    with wave.open(str(target)) as wav:
                        duration = wav.getnframes() / wav.getframerate()
                    if duration < .3: raise RuntimeError("Invalid duration")
                    events[event] = {"file": f"voices/{pack}/{event}.wav", "text": text,
                                     "seconds": round(duration, 3), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
                    print(pack, event, round(duration, 2), flush=True)
                    break
                except Exception:
                    if attempt == 2: raise
                    await asyncio.sleep(1)
        manifest["packs"][pack] = {"language": lang, "title": title, "voice": voice, "events": events}
    (ROOT / "meta/voice_packs.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
