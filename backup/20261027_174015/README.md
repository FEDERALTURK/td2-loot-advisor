# TD2 Loot Advisor

**EN** — A screen-reading (OCR) helper for *Tom Clancy's The Division 2*. Hover an item, press **F8**: the app reads
the tooltip, checks it against a full game library, compares it with your **active build** and says
**keep / consider / dismantle / check it** in seconds. It tracks missing build pieces and shows the current game
tasks in your language. It never touches game memory. 10 interface languages; anyone can add their own.

**TR** — *The Division 2* için ekran okuyan yardımcı: eşyayı okur, aktif build'inle karşılaştırır, saniyeler içinde
**sakla / düşün / kır** der; eksik parçaları ve görevleri takip eder. Oyunun belleğine dokunmaz.
Türkçe tam kılavuz: [`README.tr.md`](README.tr.md).

## Download

**[Latest release → Releases](https://github.com/FEDERALTURK/td2-loot-advisor/releases/latest)**:
`TD2LootAdvisor_Setup_<version>.exe` (installer, recommended) or `TD2LootAdvisor_<version>_portable.zip`.

## Updating

The app checks GitHub for the latest release at start (every 12 h) and asks; Settings → General → **Updates** checks on demand.
Installed copies download the new installer, verify SHA-256, install silently and restart; source copies replace only program
files (old ones go to `backup/`). Settings, builds, stash and `private/` are never touched.

## Install from source (Windows)

1. Install **Python 3.13** (3.12 works). The OCR engine (RapidOCR) is installed automatically by `run.bat`.
   **Tesseract OCR** is optional — only a fallback (UB Mannheim build, `C:\Program Files\Tesseract-OCR`).
2. **Code → Download ZIP**, extract.
3. Start with **`scripts\run.bat`** — it picks the right Python, installs the required packages and tries the optional
   ones (OCR: rapidocr, onnxruntime; voice: pyttsx3, sounddevice, faster-whisper; video: av).
4. **Installer:** double-click `scripts\build_installer.bat` → `installer\TD2LootAdvisor_Setup_<version>.exe` (no admin
   rights needed; your personal settings and license are never packaged). Optional: `scripts\build_exe.bat` builds a single `.exe`; `scripts\install_claude_code.bat` sets up Claude Code for
   the assistant and *Fetch with Claude* (uses a Claude subscription, no API key).

Recommended game settings: English game language, borderless window, HDR off, game resolution = monitor resolution
(Settings → Display & game checks this by reading the game's own settings file).

## Features

**Scanning & decisions**
- **RapidOCR (PP-OCR) engine**: reads the colour card directly, no threshold tuning. Measured on real cards
  (`tests/test_ocr.py`): all attributes right at 1440p, 1080p, 720p and 480p (8/8) versus 3/8 for Tesseract.
  Tesseract stays as a fallback and can be chosen in Settings → OCR.
- Colour hints: attribute icon colour (red = offensive, blue = defensive, yellow = skill) and the card's rarity stripe;
  if the card colour looks exotic the app never says "dismantle".
- Finds the item card anywhere on screen (21:9 and 32:9 included); multi-pass OCR; long scrolled cards are merged.
- Section-aware reading: core/attributes/mods only — expertise bonuses and set descriptions are ignored.
- Item kinds: gear, weapon, gear mod, weapon mod, skill mod, cosmetic, material, specialization weapon; exotics are never "dismantle".
- Slot-aware scoring: a gear-set piece is judged on 1 minor attribute, brand/named pieces on 2, talents only on chest/backpack.
- Overlay next to the item card with roll-quality bars and the best build.

**Builds**
- Active build shared by Panel, Builds and Missing pieces.
- Build sheet: per slot what to farm (set piece / brand / named or exotic item, core, attributes, talent, weapon type)
  and the piece you have, with ✔/✖ per requirement. Completed builds are announced.
- 3D agent and 3D build × slot score bars. Daily meta-build sync (`meta/meta_builds.json`).

**Stash** (new)
- Every scanned item is saved to your stash (`stash.json`); mark the ones you dismantle.
- **Optimize**: the best pieces you own for a build — gear-set pieces may sit in any slot, the 4-piece bonus is kept,
  named/exotic items stay in their slot — with fit % per slot, ✔/✖ requirements and the most valuable next drop.
- **Audit report**: what can be dismantled (verdict, better copy; never pieces your 5 closest builds use, never exotics),
  duplicates and items to add to the recalibration library first.
- Premium: recalibration advisor (which attribute from which item; gear and weapon libraries kept apart, exotics never
  donors), every build ranked against your stash, CSV export.

**Vendors, phone, sharing** (new)
- Weekly vendors and today's targeted loot matched against your builds and stash: "Cassie sells a Future Initiative
  glove that fits your healer build at 95%". Two sources: your own scans (Vendor mode: F8 on the vendor screen) and the
  community [hi-dep Division 2 Database](https://hidep-division2.pages.dev/?view=vendor), read directly from its public
  page on your computer (not copied into this repository). Refreshed once after the Tuesday reset. Premium.
- Phone companion: a read-only page on your home Wi-Fi (secret-key address + QR) with the last verdict, the active
  build and vendor matches. Premium.
- Build sharing: a build becomes a short code (`TD2B-…`) and QR; Builds → Paste code adds it. Free.

**Community and AI** (new)
- Anonymous drop statistics (opt-in, asked once): pick the activity you are playing on the Panel and every NEW item
  counts for it. Sent: item, slot, rarity, attribute types, best roll %, activity, random ID — never values, name, e-mail,
  license key or computer details; the server stores no IP. Premium: what drops most in each activity, where an item
  drops (per 1000 drops). Server: Cloudflare Workers + D1, see [`server/README.md`](server/README.md).
- Ask the assistant about the scanned item (with your active build's requirements for that slot).
- Read with Claude: when OCR fails, Claude Code reads the card picture (opt-in; tested on a real card: 5 s, all values right).
- Read wrong: saves the card and opens a prefilled GitHub issue so it can become a test case.

**Tasks**
- Interface-language only, grouped, duplicates merged; double-click for steps and The Division Wiki pictures.
- *Fetch with Claude* (Claude Code + web search), shared task feed (`meta/tasks_feed.json`) and a live wiki reader (`wiki_sync.py`).

**Display, OCR & effects**
- Resolution profiles 240p–4K (window and text scale; DPI-aware), game-settings check (read only).
- OCR engine choice, scale/passes (and threshold/PSM for Tesseract), auto calibration, live preview with detected lines.
  240p cards are physically too small to read (≈3 px letters); 480p is the practical minimum.
- Optional effects: custom cursor (generic sights/weapon silhouettes or your own image), mouse trail, menu transitions,
  full-window **agent-watch background** whose orange light follows the mouse (Windows, dark themes),
  original procedural header videos (`bgvideo.py`; animated WebP when `av` is not installed).

**Assistant**
- Chat and voice commands (F9) via Ollama, Claude Code, Claude API or OpenAI; voice diagnostics; Windows speech fallback.

## Free and premium

Scanning, builds, tasks, stash and the active-build optimizer are free. Premium features are listed in
Settings → Premium and in `features.py`. A license key is a small Ed25519-signed token checked on the computer
(no internet). Keys are issued with `scripts/license_tool.py` by the publisher; the private key is kept in `private/`,
which never goes to git. Because the app is open source, server-side features (community drop statistics,
cloud sync, vendor alerts) are where premium is really enforced.

## Game library

`meta/game_data.json` — gear sets, brands, named/exotic items with slots, weapons with types, weapon and gear talents
(chest/backpack), gear and weapon mods, skills, specialization weapons, attribute max values.
Sources: [The Division Wiki](https://thedivision.fandom.com) (CC BY-SA) and
[mx-division-builds](https://github.com/mxswat/mx-division-builds) by mxswat (data under CC BY-NC-SA 4.0 — non-commercial use with attribution).

## Daily feeds

- Raw: `https://raw.githubusercontent.com/FEDERALTURK/td2-loot-advisor/main/meta/meta_builds.json`
- CDN fallback: `https://cdn.jsdelivr.net/gh/FEDERALTURK/td2-loot-advisor@main/meta/meta_builds.json`
- How the feeds are researched and validated: [`meta/UPDATER.md`](meta/UPDATER.md).

## Project layout

| File | Purpose |
|---|---|
| `app.py` | UI and application |
| `engine.py` | Decision engine, build plan, card finder |
| `gamedata.py` | Item recognition against the game library |
| `ocr_backend.py` | OCR engines (RapidOCR / Tesseract), icon and rarity colour hints |
| `stash.py` | Stash, audit report, build optimizer, recalibration advisor |
| `vendor.py` | Weekly vendors, targeted loot, matching against builds |
| `companion.py` | Phone companion (local read-only web page + QR) |
| `share.py` | Build share codes |
| `dropstats.py` | Anonymous drop statistics client |
| `server/` | Community stats server (Cloudflare Worker + D1) |
| `features.py` | Free/premium features, license key check (Ed25519) |
| `tests/` | OCR test with real game cards (`tests/test_ocr.py`), license and optimizer tests (`tests/test_core.py`) |
| `display.py` | Resolution profiles, game settings reader |
| `fx.py`, `bgvideo.py`, `view3d.py`, `ui_art.py`, `ui_theme.py` | Effects, background videos, 3D, art, theme |
| `meta_sync.py`, `wiki_sync.py` | Daily feeds, live wiki reader |
| `i18n.py`, `lang/*.json` | Languages |

## Safety

Reads only the screen and the game's own settings file. Never reads or writes game memory or files and sends no input
to the game.

## License

MIT (`LICENSE`). Parts of the game data: CC BY-NC-SA 4.0 (mx-division-builds) and CC BY-SA (The Division Wiki).
The Division is a trademark of Ubisoft; this project is not affiliated with Ubisoft.
