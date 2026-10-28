"""Windows CI: Bilgi sekmesi uçtan uca — ansiklopedi (arama, ayrıntı, build'e ekleme), meta vitrini (kartlar, favori),
haberler ve sezon (sayaçlar, kartlar), yarışma (doğru/yanlış, XP), yükleme ekranı penceresi, ajan sesi (telsiz efekti).
    python tests/ui_info_test.py  → tests/.info_result.json + shots/info_*.png"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
os.environ["TD2_NO_WELCOME"] = "1"
import app  # noqa: E402
from PIL import ImageGrab  # noqa: E402
app.messagebox.askyesno = lambda *a, **k: False
app.messagebox.showinfo = app.messagebox.showwarning = lambda *a, **k: None
a = app.App()
res = {"steps": []}
def step(name, ok, **kw):
    res["steps"].append({"name": name, "ok": bool(ok), **kw}); print(("OK   " if ok else "FAIL ") + name, kw, flush=True)
def shot(name, w=None):
    w = w or a.root
    try:
        w.deiconify(); w.lift(); w.attributes("-topmost", True); w.update(); time.sleep(0.5); w.update()
        x, y = w.winfo_rootx(), w.winfo_rooty()
        ImageGrab.grab(bbox=(x, y, x + w.winfo_width(), y + w.winfo_height()), all_screens=True).save(SHOTS / f"info_{name}.png")
        w.attributes("-topmost", False)
    except Exception as e: print("shot failed", e)

def s1():
    a.nb.select(a.tab_keys.index("info")); a.info_nb.select(0)
    a.enc_q.set("striker")
    a.root.after(800, s2)
def s2():
    rows = [a.enc_tv.item(i, "values")[0] for i in a.enc_tv.get_children()]
    step("ansiklopedi araması", "Striker's Battlegear" in rows, n=len(rows), first=rows[:4])
    iid = next(i for i in a.enc_tv.get_children() if a.enc_tv.item(i, "values")[0] == "Striker's Battlegear")
    a.enc_tv.selection_set(iid); a.root.update()
    txt = a.enc_txt.get("1.0", "end")
    step("ayrıntı: bonuslar + parçalar + yetenek", "Striker's Gamble" in txt and "Striker's Pack" in txt, chars=len(txt))
    shot("01_encyclopedia")
    n0 = len(a.cfg["builds"]); a.enc_add_to_build()
    step("gear set'ten yeni build", len(a.cfg["builds"]) == n0 + 1 and a.cfg["builds"][-1]["sets_or_brands"] == ["Striker's Battlegear"],
         build=a.cfg["builds"][-1]["name"])
    a.enc_q.set(""); a.enc_cat.set(a._enc_cat_labels[1]); a._enc_fill()
    step("kategori filtresi: egzotik", len(a.enc_tv.get_children()) >= 70)
    a.info_nb.select(1); a.root.after(1200, s3)
def s3():
    cards = [w for w in a.mg_area.winfo_children()[0].winfo_children()] if a.mg_area.winfo_children() else []
    step("meta vitrini kartları", len(cards) >= 8, n=len(cards))
    feed = a.meta_feed_builds(); mid = feed["builds"][0]["meta_id"]
    a.meta_toggle_fav(mid)
    step("favori", mid in a.cfg["settings"]["meta_favs"])
    a.mg_favs.set(True); a.refresh_meta_gallery()
    n = len(a.mg_area.winfo_children()[0].winfo_children())
    step("yalnız favoriler filtresi", n == 1, n=n)
    a.mg_favs.set(False); a.refresh_meta_gallery()
    shot("02_meta")
    a.info_nb.select(2); a.root.after(1200, s4)
def s4():
    cards = a.news_area.winfo_children()
    step("haber kartları", len(cards) >= 5, n=len(cards))
    step("sezon başlığı + sayaçlar", "Red Horizon" in a.news_season.cget("text") and ":" in a.news_clock["daily"].cget("text"),
         season=a.news_season.cget("text"), daily=a.news_clock["daily"].cget("text"), weekly=a.news_clock["weekly"].cget("text"))
    shot("03_news")
    a.info_nb.select(3); a.root.after(1200, s5)
def s5():
    q = a._quiz_q
    step("yarışma sorusu üretildi", bool(q) and q["right"] in q["options"], kind=q and q["kind"])
    xp0 = a.cfg["settings"].get("quiz_xp", 0)
    btn = None
    for w in a._quiz_card.winfo_children():
        for b in getattr(w, "winfo_children", lambda: [])():
            if isinstance(b, app.tk.Button) and b.cget("text") == a._quiz_opt(q, q["right"]): btn = b
    btn.invoke(); a.root.update()
    step("doğru cevap XP verdi", a.cfg["settings"]["quiz_xp"] > xp0, xp=a.cfg["settings"]["quiz_xp"])
    shot("04_quiz")
    a.quiz_popup(); a.root.after(1200, s6)
def s6():
    pop = a._quiz_pop
    step("yükleme ekranı yarışma penceresi", pop.winfo_exists() and pop.winfo_ismapped())
    shot("05_quiz_popup", pop); pop.destroy()
    a.cfg["settings"].update(voice_pack="tactical", voice_radio=True)
    a.speaker.last_fx = None
    a.speak_verdict("KEEP", {"name": "Ninjabike", "rarity": ["EXOTIC"]}, [(92, "Striker (PvE)", None)], None)
    a.root.after(15000, s7)
def s7():
    fx = a.speaker.last_fx
    ok = bool(fx) and os.path.exists(fx) and os.path.getsize(fx) > 10000
    step("ajan sesi: telsiz efektli konuşma üretildi (CI'da ses aygıtı yok, çalma atlanır)", ok, fx=fx, size=os.path.getsize(fx) if fx and os.path.exists(fx) else 0, err=a.speaker.err)
    finish()
def finish():
    if res.get("done"): return
    res["done"] = True
    res["ok"] = all(s["ok"] for s in res["steps"]) and len(res["steps"]) >= 13
    (ROOT / "tests" / ".info_result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    a.on_close(force=True)
def guard(fn):
    def run():
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc(); step(fn.__name__ + " hata", False, e=repr(e)); finish()
    return run
for _n in ("s1", "s2", "s3", "s4", "s5", "s6", "s7"): globals()[_n] = guard(globals()[_n])
a.root.after(4000, s1)
a.root.after(120000, finish)
a.root.mainloop()
print("RESULT:", "PASS" if res.get("ok") else "FAIL"); sys.exit(0 if res.get("ok") else 1)
