"""Windows: SAPI ile dosyaya konuşma + telsiz efekti çalışıyor mu?"""
import os, sys, tempfile, threading, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import voicepack
d = tempfile.gettempdir()
def work():
    for i in range(2):
        t0 = time.time(); raw = os.path.join(d, f"diag{i}.wav")
        ok = voicepack.sapi_to_wav("Exotic detected. Recommend keeping it.", raw, 185, ["zira"])
        fx = voicepack.radio_fx(raw, os.path.join(d, f"diag{i}_fx.wav"))
        print(f"run {i}: ok={ok} raw={os.path.getsize(raw)} fx={os.path.getsize(fx)} {time.time()-t0:.1f}s", flush=True)
th = threading.Thread(target=work, daemon=True); th.start(); th.join(60)
print("alive after 60s:", th.is_alive())
