"""Create the real Tk widgets with temporary settings; no desktop input or capture.

Run with an optional source root to measure the same hidden-widget startup on a
baseline. External services, recording, GPU warmup and visual effects are disabled.
This is not an in-game performance or visual layout test.
"""
from pathlib import Path
from contextlib import ExitStack
import ctypes
import importlib
import json
import logging
import os
import shutil
import sys
import tempfile
import time
from unittest.mock import patch


def memory_mb():
    if os.name != "nt": return None
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in
                    ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                     "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    c=Counters(); c.cb=ctypes.sizeof(c)
    if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb): return None
    return round(c.WorkingSetSize / 1024**2, 1)


def main():
    source=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(source)); os.environ["TD2_NO_WELCOME"]="1"
    started=time.perf_counter(); app=importlib.import_module("app")
    imported=time.perf_counter()
    errors=[]; result={"source":str(source),"import_ms":round((imported-started)*1000,1)}
    with tempfile.TemporaryDirectory(prefix="td2-widget-test-") as folder, ExitStack() as stack:
        data=Path(folder)
        shutil.copytree(source/"lang",data/"lang")
        cfg=json.loads((source/"scripts/default_builds.json").read_text(encoding="utf-8"))
        cfg.setdefault("settings",{}).update(language="tr",perf_mode="balanced",meta_sync=False,tasks_sync=False,wiki_sync=False,
            task_live=False,news=False,vendor_auto=False,update_check=False,svc_auto_run=False,svc_tray=False,api_on=False,
            sp_on=False,tr_on=False,sound=False,ui_sounds=False,fx_cursor=False,fx_trail=False,fx_video=False,
            fx_bgwatch=False,fx_transitions=False,bg_interval=0)
        (data/"builds.json").write_text(json.dumps(cfg),encoding="utf-8")
        paths={"BASE":data,"BUNDLE":source,"ART_DIR":data/"art","APPLOG_DIR":data/"logs","APPLOG_PATH":data/"logs/app.log",
               "REPORTS_DIR":data/"reports","CFG_PATH":data/"builds.json","LOG_PATH":data/"loot_log.csv",
               "DEBUG_PATH":data/"last_crop.png","PROG_PATH":data/"progress.json","STASH_PATH":data/"stash.json",
               "VENDOR_CACHE":data/"vendor_cache.json","DROPQ_PATH":data/"drop_queue.json","ACCOUNT_PATH":data/"account.dat",
               "SESSIONS_PATH":data/"sessions.json","SCREEN_PATH":data/"screen_states.json","TASKS_CACHE":data/"tasks_cache.json",
               "META_CACHE":data/"meta_cache.json","NEWS_CACHE":data/"news_cache.json","DESC_CACHE":data/"descriptions_cache.json"}
        paths["TASK_PATH"]=data/"tasks.json"
        stack.enter_context(patch.multiple(app,**paths))
        real_tk=app.tk.Tk
        def hidden_tk(*args,**kw):
            root=real_tk(*args,**kw);root.withdraw()
            root.report_callback_exception=lambda *exc: errors.append(str(exc[1]))
            return root
        stack.enter_context(patch.object(app.tk,"Tk",hidden_tk))
        class Speaker:
            def say(self,*a,**k): pass
            def close(self): pass
        stack.enter_context(patch.object(app,"Speaker",Speaker))
        stack.enter_context(patch.object(app.ui_art,"ensure_backgrounds",lambda folder: []))
        stack.enter_context(patch.object(app.App,"gpu_apply_cached",lambda self: True))
        for name in ("meta_sync_start","vendor_refresh","ask_drop_consent","check_new_pc","update_center","_drops_tick",
                     "gpu_check","account_startup","service_start","_news_poll","_info_badge","_task_live_poll"):
            stack.enter_context(patch.object(app.App,name,lambda *a,**k: None))
        for name in ("askyesno","askokcancel","showinfo","showwarning","showerror"):
            stack.enter_context(patch.object(app.messagebox,name,lambda *a,**k: False))
        stack.enter_context(patch.object(app.urllib.request,"urlopen",side_effect=AssertionError("network disabled in widget test")))
        obj=None
        try:
            init=time.perf_counter();obj=app.App();obj.root.update_idletasks()
            result["widgets_ms"]=round((time.perf_counter()-init)*1000,1)
            result["tabs"]=len(obj.tab_keys)
            assert result["tabs"]==13
            if hasattr(obj,"toggle_performance"):
                assert obj.lt_eng.get()=="local"
                assert "bilgisayarda" in obj.lt_privacy_lbl.cget("text")
                obj.perf_btn.invoke(); assert obj.cfg["settings"]["perf_mode"]=="game"
                assert "Oyun" in obj.perf_btn.cget("text")
                obj.perf_btn.invoke(); assert obj.cfg["settings"]["perf_mode"]=="balanced"
                obj.show_performance()
                obj._performance_tick();assert obj.root._td2_suspend_animations
                with patch.object(obj.root,"state",return_value="normal"),patch.object(app,"game_active",return_value=False):
                    obj._performance_tick();assert not obj.root._td2_suspend_animations
            obj.nb.select(obj.tabs["translate"]);obj.root.update()
            result["working_set_mb"]=memory_mb();result["callback_errors"]=errors
            assert not errors,errors
            result["ok"]=True
        finally:
            if obj is not None:
                obj.on_close(force=True)
            logging.shutdown()
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0


if __name__=="__main__": sys.exit(main())
