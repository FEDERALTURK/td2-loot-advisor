# TD2 Loot Advisor

**EN** — A screen-reading (OCR) helper for *Tom Clancy's The Division 2*. It reads the item on screen,
compares it with your build rules and tells you **keep / consider / dismantle** in seconds. It never touches
game memory. 10 interface languages, anyone can add their own.

**TR** — *The Division 2* için ekran okuyan (OCR) yardımcı. Ekrandaki eşyayı okuyup build kurallarınla
karşılaştırır ve saniyeler içinde **sakla / düşün / kır** der. Oyunun belleğine dokunmaz. 10 dil.

## Install / Kurulum (Windows)

1. Install **Python 3.12 or 3.13** (python.org) and **Tesseract OCR**
   (UB Mannheim build, default path `C:\Program Files\Tesseract-OCR`).
2. Download this repository: **Code → Download ZIP**, extract it.
3. Run `scripts\run.bat`. It installs the required packages on first start and opens the app.
4. Optional: `scripts\build_exe.bat` builds a standalone `.exe`; `scripts\install_claude_code.bat`
   enables the assistant via a Claude subscription (no API key).

Full guide (Turkish): [`README.tr.md`](README.tr.md) · Tam kılavuz: [`README.tr.md`](README.tr.md)

**TR:** Python 3.12/3.13 ve Tesseract OCR kur → **Code → Download ZIP** ile indirip aç →
`scripts\run.bat` çalıştır. İlk açılışta gerekli paketleri kurar.

## Daily meta feed / Günlük meta akışı

`meta/meta_builds.json` is the central list of current meta and most-discussed builds. Every copy of the app
downloads it once a day at startup (with a jsDelivr CDN fallback) and merges it without touching the user's
own builds.

- Raw: `https://raw.githubusercontent.com/FEDERALTURK/td2-loot-advisor/main/meta/meta_builds.json`
- CDN: `https://cdn.jsdelivr.net/gh/FEDERALTURK/td2-loot-advisor@main/meta/meta_builds.json`

`meta/tasks_feed.json` carries the current daily/weekly projects, season journey, global events and
manhunt steps — already translated into all 10 languages — plus the official reset times (UTC), which the app
converts to each player's local time.

**Live wiki:** the app also reads [The Division Wiki](https://thedivision.fandom.com) directly from the player's
computer (MediaWiki API) — current season's Manhunt Scouts, Classified Assignments with puzzle tips and dated
seasonal projects — and follows the season infobox to the next season automatically (`wiki_sync.py`).
Wiki content is CC BY-SA; every task links back to its wiki section.

How the feeds are researched and scored: [`meta/UPDATER.md`](meta/UPDATER.md).

## Display, game settings & 3D / Ekran, oyun ayarları ve 3D

- **Resolution profiles** (1080p → 4K, 21:9 and 32:9): OCR scale, threshold and overlay size per resolution; detected automatically, DPI-aware (125 % / 150 % Windows scaling).
- **Game settings check (read only):** reads `Documents\My Games\Tom Clancy's The Division 2\state.cfg`, `graphic settings.cfg` and `ui config.cfg` (resolution, borderless/fullscreen, HDR, DX12, language, render scale, enlarge UI) and warns about anything that hurts screen reading. The game's memory and files are never written.
- **OCR fine tuning:** threshold slider, scale, PSM, multi-pass reading (the card is read with 2–3 thresholds, the best reading wins), *Auto calibrate* on the last card and a live *Preview* (original ↔ processed image + recognized stats).
- **Overlay next to the item card:** verdict, roll-quality bars and best build appear beside the tooltip (or in a fixed corner); opacity and size adjustable.
- **3D views:** a rotatable 3D agent in *Missing pieces* (green = owned, red = missing, click a piece to highlight its slot) and 3D build × slot score bars. Pure Tk canvas, no extra libraries.
- Ideas borrowed from d4lf, Diablo4Companion and RatScanner (resolution presets, in-game requirement checks, overlay tooltip).

**Recommended game settings:** English game language, HDR off, borderless window, game resolution = monitor resolution.

## Tasks / Görevler

- Tasks are shown **only in the interface language**, grouped (Journey · Mission 3, Manhunt · Scout 2, Classified Assignments, daily/weekly projects) with a short line each; duplicates from different sources are merged.
- **Double-click** a task for a detail window: header art, the full task, step-by-step how-to, source link, done toggle and pictures from The Division Wiki (cached).
- **Fetch with Claude** replaces the old ChatGPT screen macro: Claude Code (your Claude subscription, as in the Assistant tab) searches the web for the current season's Journey, Manhunt and project tasks and adds them in your language with a how-to.

## Build sheet, active build & effects / Build ayrıntısı, aktif build ve efektler

- **Build sheet (Builds → 📋):** every slot shows what to farm — gear-set piece / brand / named or exotic item, core attribute, attributes, chest/backpack talent, weapon type and talent — next to the piece you already have with ✔/✖ per requirement.
- **Active build:** chosen in Panel, Builds or Missing pieces (shared). Every scan is checked against the active build's slot requirements; fitting drops are recorded automatically and the app tells you when the build is complete.
- **Effects (Settings → ✨, all optional):** custom mouse cursor (generic sights and weapon silhouettes or your own image), mouse trail, animated menu transitions, and a silent background video behind the header. On first start the app renders its own original animated backgrounds (hex scan, radar, winter city, embers, tactical map, storm — drawn in code, no game footage) into `art/videos`; **Multiply videos** adds 6 more variations. Your own recordings work too. Needs the optional `av` package (run.bat installs it). `python bgvideo.py art/videos` renders them from the command line.
- **Any screen size:** resolution profiles from 240p to 4K resize the window and scale the text; changing the profile reopens the app in ~2 seconds.

## Game library / Oyun kütüphanesi

`meta/game_data.json` lists every gear set, brand, named and exotic item (with slot), weapon (with type), weapon and gear talents, gear mods and weapon mods, skills, specialization weapons and attribute max values. The app uses it to tell gear from weapons, mods, cosmetics and specialization weapons, to ignore expertise bonuses, and to merge scrolled (long) item cards.

Data sources: [The Division Wiki](https://thedivision.fandom.com) and [mx-division-builds](https://github.com/mxswat/mx-division-builds) by mxswat (data under CC BY-NC-SA 4.0 — non-commercial use with attribution).

## License

MIT — see [`LICENSE`](LICENSE).

*Not affiliated with or endorsed by Ubisoft. The Division is a trademark of Ubisoft Entertainment.*
