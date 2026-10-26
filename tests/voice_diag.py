"""Windows: pyttsx3 ile dosyaya konuşma üretimi çalışıyor mu? (telsiz efekti için)"""
import os, sys, tempfile, threading, time
import pyttsx3
out = os.path.join(tempfile.gettempdir(), "diag.wav")
def work():
    e = pyttsx3.init()
    print("voices:", [v.name for v in e.getProperty("voices")], flush=True)
    t0 = time.time(); e.save_to_file("Exotic detected. Recommend keeping it.", out); e.runAndWait()
    print("save_to_file done in %.1fs" % (time.time() - t0), os.path.exists(out) and os.path.getsize(out), flush=True)
    t0 = time.time(); e.say("test"); e.runAndWait(); print("say done %.1fs" % (time.time() - t0), flush=True)
    t0 = time.time(); e.save_to_file("Second line.", out); e.runAndWait()
    print("second save done %.1fs" % (time.time() - t0), os.path.getsize(out), flush=True)
th = threading.Thread(target=work, daemon=True); th.start(); th.join(60)
print("alive after 60s:", th.is_alive())
