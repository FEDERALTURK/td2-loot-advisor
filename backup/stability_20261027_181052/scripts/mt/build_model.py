"""Çeviri modelini hazırlar: Hugging Face'teki OPUS-MT (Helsinki-NLP, CC-BY 4.0) modelini CTranslate2 int8'e çevirir,
programın kullanacağı biçimde paketler ve örnek cümlelerle dener.
    python scripts/mt/build_model.py Helsinki-NLP/opus-mt-tc-big-en-tr out_dir [target_prefix]
"""
import json, os, shutil, subprocess, sys, time, hashlib, zipfile
from pathlib import Path

model, out = sys.argv[1], Path(sys.argv[2])
prefix = sys.argv[3] if len(sys.argv) > 3 else ""
from huggingface_hub import snapshot_download
src = snapshot_download(model)
ct2 = out / "model"
if ct2.exists(): shutil.rmtree(ct2)
subprocess.check_call(["ct2-transformers-converter", "--model", model, "--output_dir", str(ct2), "--quantization", "int8"])
for f in ("source.spm", "target.spm", "README.md", "LICENSE"):
    if (Path(src) / f).exists(): shutil.copy(Path(src) / f, ct2 / f)
(ct2 / "td2_model.json").write_text(json.dumps({"model": model, "pair": "en-tr", "target_prefix": prefix,
                                                "license": "CC-BY-4.0 (Helsinki-NLP / OPUS-MT)"}), encoding="utf-8")

import ctranslate2, sentencepiece as spm
tr = ctranslate2.Translator(str(ct2), device="cpu", compute_type="int8")
sps, spt = spm.SentencePieceProcessor(str(ct2 / "source.spm")), spm.SentencePieceProcessor(str(ct2 / "target.spm"))
samples = ["Agent, the Black Tusk have taken control of the Capitol Building.",
           "Head to the safe house and talk to the quartermaster.",
           "Your supplies are running low. Find a supply drop before the storm hits.",
           "Kill 20 enemies with headshots while using a Marksman Rifle.",
           "The settlement needs power. Restore the generator to unlock new projects.",
           "Rogue agent detected nearby. Proceed with caution.",
           "Weekly reset: new Targeted Loot locations are available.",
           "Complete the Manhunt to face the High Value Target."]
t0 = time.time()
samples += ["Agent, the ZQ0 have taken control of the ZQ1.", "Equip ZQ0 and head to ZQ1 to find ZQ2."]
toks = [([prefix] if prefix else []) + sps.encode(s, out_type=str) + ["</s>"] for s in samples]
res = tr.translate_batch(toks, beam_size=4, max_decoding_length=256, no_repeat_ngram_size=4, repetition_penalty=1.1)
dt = time.time() - t0
for s, r in zip(samples, res):
    print("EN:", s); print("TR:", spt.decode(r.hypotheses[0])); print()
print(f"TIME {dt:.2f}s for {len(samples)} sentences")
z = out / ("en-tr-" + model.split("/")[-1] + ".zip")
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in ct2.rglob("*"):
        if p.is_file(): zf.write(p, "en-tr/" + p.relative_to(ct2).as_posix())
h = hashlib.sha256(z.read_bytes()).hexdigest()
print("ZIP", z.name, z.stat().st_size, h)
(out / (z.name + ".sha256")).write_text(f"{h}  {z.name}\n")
