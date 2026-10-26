"""Telefon / ikinci ekran: canlı çeviri akışı (yerel ağ, tarayıcı). Görüntü değil yazı gönderilir — ek yük yok denecek kadar az.

Sayfa yerel API'nin /tr yolunda (aynı belirteçle) açılır; olaylar WebSocket'ten gelir:
    {"type": "translate", "items": [{"en", "tr", "terms": [{"name","label","text"}]}], "time": ...}
Oyun özel tam ekranda olsa bile çalışır (çeviri kutusu görünmediğinde de okunur).
"""

PAGE = r"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0f1116"><title>TD2 · Canlı çeviri</title>
<style>
:root{--bg:#0f1116;--sf:#171a21;--sf2:#212530;--fg:#e8eaef;--mu:#8d95a5;--ac:#ff6d10;--fs:20px}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--fg);font-family:"Segoe UI",Roboto,system-ui,sans-serif;overflow-x:hidden}
header{position:sticky;top:0;z-index:2;display:flex;align-items:center;gap:6px;padding:10px 12px;background:var(--sf);
  border-bottom:2px solid var(--ac);flex-wrap:wrap}
header b{letter-spacing:.12em;font-size:13px;color:var(--ac)}header .sp{flex:1}
#dot{width:9px;height:9px;border-radius:50%;background:#ef4444}#dot.on{background:#22c55e}
button{background:var(--sf2);color:var(--fg);border:1px solid #2c313d;border-radius:8px;padding:6px 9px;font-size:14px;min-width:38px}
button.on{border-color:var(--ac);color:var(--ac)}
main{padding:12px 12px 40px;max-width:900px;width:100%;margin:0 auto}
.card{background:var(--sf);border-left:4px solid var(--ac);border-radius:10px;padding:12px 14px;margin:0 0 12px;animation:in .35s ease}
.card.old{opacity:.62;border-left-color:#2c313d}
.tr{font-size:var(--fs);line-height:1.38;white-space:pre-wrap;overflow-wrap:anywhere}.en{color:var(--mu);font-size:13px;margin-top:6px;white-space:pre-wrap;overflow-wrap:anywhere}
.terms{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{font-size:12.5px;padding:4px 9px;border-radius:999px;background:var(--sf2);color:var(--fg);border:1px solid #2c313d}
.chip i{font-style:normal;color:var(--ac);margin-right:4px}
.def{margin-top:8px;padding:9px 11px;border-radius:8px;background:var(--sf2);font-size:14px;line-height:1.4}
.def b{color:var(--ac)}
#empty{color:var(--mu);text-align:center;margin-top:18vh;line-height:1.6}
.t{color:var(--mu);font-size:11px;float:right}
@keyframes in{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
</style></head><body>
<header><span id="dot"></span><b>◆ CANLI ÇEVİRİ</b><span class="sp"></span>
<button id="sm">A−</button><button id="lg">A+</button><button id="en">EN</button><button id="say">🔊</button></header>
<main><div id="empty">Oyunda canlı çeviri açılınca çeviriler burada akar.<br>Ekranı açık tutmak için sayfa açık kalsın.</div><div id="list"></div></main>
<script>
const P=new URLSearchParams(location.search),L=document.getElementById("list"),E=document.getElementById("empty");
let fs=parseInt(localStorage.getItem("fs")||"20"),showEn=localStorage.getItem("en")!=="0",speak=localStorage.getItem("say")==="1";
function opts(){document.documentElement.style.setProperty("--fs",fs+"px");document.getElementById("en").classList.toggle("on",showEn);
 document.getElementById("say").classList.toggle("on",speak);document.querySelectorAll(".en").forEach(x=>x.style.display=showEn?"":"none")}
function save(){try{localStorage.setItem("fs",fs);localStorage.setItem("en",showEn?"1":"0");localStorage.setItem("say",speak?"1":"0")}catch(e){}}
sm.onclick=()=>{fs=Math.max(14,fs-2);save();opts()};lg.onclick=()=>{fs=Math.min(40,fs+2);save();opts()};
en.onclick=()=>{showEn=!showEn;save();opts()};say.onclick=()=>{speak=!speak;save();opts();if(speak)talk("Sesli okuma açık")};
function talk(t){try{const u=new SpeechSynthesisUtterance(t);u.lang="tr-TR";speechSynthesis.cancel();speechSynthesis.speak(u)}catch(e){}}
function theme(s){if(!s)return;const r=document.documentElement.style;for(const[k,v]of Object.entries(s))r.setProperty("--"+k,v)}
function el(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e}
let lastTr="";
function add(it,time){if(it.tr===lastTr)return;lastTr=it.tr;E.style.display="none";const c=el("div","card");
 const ts=el("span","t",new Date((time||Date.now()/1000)*1000).toLocaleTimeString().slice(0,5));c.appendChild(ts);
 c.appendChild(el("div","tr",it.tr));const e=el("div","en",it.en);if(!showEn)e.style.display="none";c.appendChild(e);
 if(it.terms&&it.terms.length){const w=el("div","terms");let d=null;
  for(const t of it.terms){const ch=el("span","chip");ch.appendChild(el("i",null,t.label||"•"));ch.appendChild(document.createTextNode(t.name));
   ch.onclick=()=>{if(d)d.remove();d=el("div","def");d.appendChild(el("b",null,t.name+"  "));d.appendChild(document.createTextNode(t.text||""));c.appendChild(d)};
   w.appendChild(ch)}c.appendChild(w)}
 L.prepend(c);[...L.children].forEach((x,i)=>{x.classList.toggle("old",i>2);if(i>60)x.remove()})}
let lock=null;async function wake(){try{lock=await navigator.wakeLock.request("screen")}catch(e){}}
document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")wake()});
function go(){const w=new WebSocket(`ws://${location.host}/ws?t=${encodeURIComponent(P.get("t")||"")}`);
 w.onopen=()=>dot.classList.add("on");
 w.onmessage=m=>{const e=JSON.parse(m.data);
  if(e.type==="hello"&&e.state&&e.state.translate){theme(e.state.translate.theme);(e.state.translate.recent||[]).forEach(x=>add(x,x.time))}
  if(e.type==="translate"){theme(e.theme);(e.items||[]).forEach(x=>add(x,e.time));if(speak&&e.items&&e.items.length)talk(e.items.map(x=>x.tr).join(". "))}};
 w.onclose=()=>{dot.classList.remove("on");setTimeout(go,2000)}}
opts();wake();go();
</script></body></html>"""
