"""The Division Wiki (thedivision.fandom.com) canlı okuyucu.

Programın kendisi, kullanıcının bilgisayarından wiki'nin herkese açık MediaWiki API'sini okur
(anahtar gerekmez). Günde bir kez:

1. Güncel sezon sayfasını bulur: ortak listedeki başlangıç sayfasından (ör. "Red Horizon")
   başlar; sezon kutusundaki "next=" sayfası wiki'de varsa ve başlangıç tarihi geldiyse ona geçer.
   Böylece yeni sezon açıldığında program kendiliğinden yeni sayfaya geçer.
2. O sayfadan şunları çıkarır:
   - Manhunt Scout'ları (her Scout'un adı + ne yapıldığı)        → Manhunt
   - Classified Assignment'lar (açıklama, çıkış tarihi, bulmaca ipuçları) → Journey
   - Tarihli proje zincirleri ("Project Chain from … to …")       → Projeler / Sezonluk
3. Görevleri ortak görev listesiyle aynı biçimde döndürür; uygulama bunları 📚 işaretiyle ekler.

Wiki metni İngilizcedir; uygulama bir yapay zekâ seçiliyse görevleri kullanıcının diline çevirir.
İçerik CC BY-SA lisanslıdır: her görev wiki sayfasına bağlantı verir.
Ek kütüphane gerektirmez.
"""
import json
import logging
import re
import ssl
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

log = logging.getLogger("td2")

API = "https://thedivision.fandom.com/api.php"
WIKI = "https://thedivision.fandom.com/wiki/"
TIMEOUT_S = 12
DEFAULT_SEASON = "Red Horizon"
ORDINALS = {w: i for i, w in enumerate(
    "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth "
    "fourteenth fifteenth".split(), 1)}
MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)}


# ---------------------------------------------------------------- erişim
def _get(params, app_version=""):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": f"TD2-Loot-Advisor/{app_version} (https://github.com/FEDERALTURK/td2-loot-advisor)",
        "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S, context=ssl.create_default_context()) as r:
        return json.loads(r.read(2_000_000).decode("utf-8"))


def wikitext(title, app_version=""):
    """(gerçek başlık, wikitext) ya da sayfa yoksa (None, "")."""
    d = _get({"action": "parse", "page": title, "prop": "wikitext", "redirects": "1"}, app_version)
    if "parse" not in d:
        return None, ""
    return d["parse"]["title"], d["parse"]["wikitext"]


def page_url(title, section=""):
    u = WIKI + urllib.parse.quote(title.replace(" ", "_"))
    return u + ("#" + urllib.parse.quote(section.replace(" ", "_")) if section else "")


# ---------------------------------------------------------------- wikitext → düz metin
def _strip_templates(s):
    for _ in range(10):                      # iç içe {{…}} şablonlarını içten dışa sil
        n = re.sub(r"\{\{[^{}]*\}\}", "", s)
        if n == s: break
        s = n
    return s


def clean(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = _strip_templates(s)
    s = re.sub(r"\{\|.*?\|\}", "", s, flags=re.S)                       # tablolar
    s = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", s, flags=re.I)
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", s)
    s = re.sub(r"\[https?://\S+\]", "", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"</?[a-z][^>]*>", "", s)
    s = s.replace("&nbsp;", " ")
    return re.sub(r"[ \t]+", " ", s).strip()


def sections(text):
    """[(seviye, başlık, gövde)] — gövde alt başlıklar hariç."""
    out, cur = [], [1, "", []]
    for line in text.splitlines():
        m = re.match(r"^(={2,6})\s*(.*?)\s*\1\s*$", line)
        if m:
            out.append((cur[0], cur[1], "\n".join(cur[2])))
            cur = [len(m.group(1)), clean(m.group(2)), []]
        else:
            cur[2].append(line)
    out.append((cur[0], cur[1], "\n".join(cur[2])))
    return out


def children(secs, parent_pred):
    """parent_pred'e uyan bölümün doğrudan alt bölümleri."""
    res, lvl = [], None
    for level, title, body in secs:
        if lvl is None:
            if parent_pred(level, title): lvl = level
            continue
        if level <= lvl: break
        if level == lvl + 1: res.append((title, body))
    return res


def infobox(text, field):
    m = re.search(r"\|\s*" + re.escape(field) + r"\s*=\s*([^|}\n]*)", text)
    return clean(m.group(1)) if m else ""


def link_target(raw):
    m = re.search(r"\[\[([^\]|]+)", raw or "")
    return m.group(1).strip() if m else ""


def parse_date(s, default_year=None):
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?", s or "")
    if not m or m.group(1).lower() not in MONTHS: return None
    y = int(m.group(3) or default_year or datetime.now(timezone.utc).year)
    return datetime(y, MONTHS[m.group(1).lower()], int(m.group(2)), tzinfo=timezone.utc)


def first_sentences(s, n=2, limit=300):
    parts = re.split(r"(?<=[.!?])\s+", s.strip())
    return " ".join(parts[:n])[:limit].strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


# ---------------------------------------------------------------- sezon
def resolve_season(start, app_version="", now=None):
    """Başlangıç sayfasından 'next=' zinciriyle güncel sezona ilerler. (başlık, wikitext)."""
    now = now or datetime.now(timezone.utc)
    title, text = wikitext(start or DEFAULT_SEASON, app_version)
    if not title:
        title, text = wikitext(DEFAULT_SEASON, app_version)
    for _ in range(3):
        nxt = link_target(re.search(r"\|\s*next\s*=\s*([^|}\n]*)", text).group(1)
                          if re.search(r"\|\s*next\s*=", text) else "")
        if not nxt: break
        t2, x2 = wikitext(nxt, app_version)
        start_d = parse_date(infobox(x2, "start_date")) if t2 else None
        if not (t2 and start_d and start_d <= now): break
        title, text = t2, x2
    return title, text


# ---------------------------------------------------------------- ayrıştırıcılar
def parse_scouts(season, text):
    """Manhunt Storyline altındaki her Scout → görev."""
    secs = sections(text)
    tasks = []
    for name, body in children(secs, lambda l, t: l == 2 and "manhunt" in t.lower()):
        b = clean(body)
        if "wip" in name.lower() or len(re.sub(r"[-\s]", "", b)) < 20:   # wiki'de henüz yazılmamış bölümler
            continue
        m = re.search(r"For the (\w+) Scout, Division agents (?:focused (?:their )?(?:objectives? )?on |)(.+?)\.(?:\s|$)", b)
        n = ORDINALS.get(m.group(1).lower()) if m else None
        what = (m.group(2) if m else first_sentences(b, 1)).strip()
        what = what[:1].upper() + what[1:]
        label = f"Manhunt Scout {n} – {name}" if n else f"Manhunt – {name}"
        tasks.append({"feed_id": f"wiki-{slug(season)}-scout-{n or slug(name)}", "cat": "manhunt", "kind": "",
                      "texts": {"en": f"{label}: {what}"[:300]},
                      "how": {"en": "Activate the Scout in the Seasons menu, solve the clue for each of its 3 activities "
                                    "and complete them; finished Scouts stay available all season."},
                      "until": "", "source": page_url(season, name), "n": n or 99})
    tasks.sort(key=lambda x: x.pop("n"))
    return tasks


def parse_classified(season, text, app_version="", now=None):
    """Sezon sayfasındaki Classified Assignment'lar → Journey görevleri (sayfalarından açıklama + bulmaca ipuçları)."""
    now = now or datetime.now(timezone.utc)
    secs = sections(text)
    names = [n for n, _ in children(secs, lambda l, t: l == 2 and t.lower().startswith("classified assignments:"))]
    tasks = []
    for name in names[:6]:
        try:
            title, ptxt = wikitext(name, app_version)
        except Exception as e:
            log.debug("Wiki page %s failed: %s", name, e)
            title, ptxt = None, ""
        desc = infobox(ptxt, "description") if title else ""
        if title and not desc:
            d = [b for n, b in children(sections(ptxt), lambda l, t: False)] or \
                [b for _, t, b in sections(ptxt) if t.lower() == "description"]
            desc = first_sentences(clean(d[0]), 1, 160) if d else ""
        rel = parse_date((re.search(r"released on ([A-Z][a-z]+ \d{1,2},? \d{4})", clean(ptxt)) or [None, ""])[1]) if title else None
        if rel and rel > now:
            continue                                                 # henüz çıkmadı
        hows = []
        if title:
            for pname, pbody in children(sections(ptxt), lambda l, t: l == 2 and t.lower() == "puzzles"):
                txt = first_sentences(clean(pbody), 2, 220)
                if txt: hows.append(f"{pname}: {txt}")
        text_en = f"Classified Assignment: {name}" + (f" – {desc}" if desc else "") + \
                  (f" (released {rel:%b %d})" if rel else "")
        tasks.append({"feed_id": f"wiki-ca-{slug(name)}", "cat": "journey", "kind": "",
                      "texts": {"en": text_en[:300]},
                      "how": {"en": (" ".join(hows) or "Start it from the map's Classified Assignments list.")[:500]},
                      "until": "", "source": page_url(title or name)})
    return tasks


def parse_project_events(season, text, now=None):
    """'Project Chain from September 8 to September 22' gibi tarihli proje etkinlikleri → Projeler/Sezonluk."""
    now = now or datetime.now(timezone.utc)
    year = (parse_date(infobox(text, "start_date")) or now).year
    tasks = []
    for title, body in [(t, b) for _, t, b in sections(text)]:
        b = clean(body)
        for m in re.finditer(r"([^.]*?\bProject(?: Chain)?\b[^.]*?\bfrom ([A-Z][a-z]+ \d{1,2}) to ([A-Z][a-z]+ \d{1,2})[^.]*\.)", b):
            start, end = parse_date(m.group(2), year), parse_date(m.group(3), year)
            if not end: continue
            end = end + timedelta(hours=8)                            # resmî sıfırlama saati
            if end <= now: continue
            tasks.append({"feed_id": f"wiki-proj-{slug(title)}-{end:%m%d}", "cat": "projects", "kind": "seasonal",
                          "texts": {"en": f"{title} – special project chain ({m.group(2)} – {m.group(3)})"[:300]},
                          "how": {"en": first_sentences(b, 3, 480)},
                          "until": end.isoformat(timespec="minutes"), "source": page_url(season, title)})
    return tasks


# ---------------------------------------------------------------- toplu çalıştırma
def run(start_page, app_version="", now=None):
    """Arka plan iş parçacığında çağrılır. Ortak görev akışıyla aynı biçimde sonuç döner."""
    season, text = resolve_season(start_page, app_version, now)
    if not season:
        raise RuntimeError("season page not found on wiki")
    tasks = parse_scouts(season, text) + parse_classified(season, text, app_version, now) + \
        parse_project_events(season, text, now)
    return {"version": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "season": season,
            "season_url": page_url(season), "tasks": tasks, "guides": [], "resets": None}
