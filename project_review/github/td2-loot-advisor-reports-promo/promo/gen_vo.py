"""Tek anlatım parçası üretir (Chatterbox Multilingual, MIT). En çok 4 deneme; Whisper ile dinlenip metne en yakın olan seçilir.
    python gen_vo.py <lang> <index> <out_dir>
Referans ses: ref_voice.wav (CC0 lisanslı Piper 'joe' sesiyle üretilmiş İngilizce bir cümle; yalnız ses tınısı için)."""
import difflib, json, re, shutil, sys
from pathlib import Path
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from faster_whisper import WhisperModel

lang, idx, out = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
here = Path(__file__).parent
sub, say = json.loads((here / "script.json").read_text(encoding="utf-8"))[lang][idx]
say = say or sub
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
asr = WhisperModel("small", device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[^\w ]", " ", s.lower().replace("ı", "i").replace("td2", "td 2")).split()
ref_txt = re.sub(r"Ti Di Tu, Lut Edvayzır|T D 2 Loot Advisor", "", say).replace("bild", "build")
best = None
for take in range(4):
    w = m.generate(say, language_id=lang, audio_prompt_path=str(here / "ref_voice.wav"), exaggeration=0.4,
                   cfg_weight=0.0 if lang == "tr" else 0.5, temperature=0.7)
    p = out / f"{lang}_{idx}_t{take}.wav"; ta.save(str(p), w, m.sr)
    segs, info = asr.transcribe(str(p), beam_size=5, language=lang)
    heard = " ".join(s.text for s in segs)
    heard_cmp = re.sub(r"(?i)t\s*d\s*2?\s*\S*\s*(loot|lut|lute|lüt)\s*\S*", "", heard)
    sim = difflib.SequenceMatcher(None, norm(ref_txt), norm(heard_cmp)).ratio()
    dur = w.shape[1] / m.sr
    print(f"{lang} {idx} take{take} sim={sim:.3f} dur={dur:.1f} | {heard.strip()}", flush=True)
    if best is None or sim > best[0]: best = (sim, p)
    if sim >= 0.95: break
shutil.copy(best[1], out / f"{lang}_{idx}.wav")
print("BEST", lang, idx, best, flush=True)

