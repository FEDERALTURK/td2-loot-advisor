# TD2 Loot Advisor

**EN** — A screen-reading (OCR) helper for *Tom Clancy's The Division 2*. Hover an item, press **F8**: the app reads
the tooltip, checks it against a full game library, compares it with your **active build** and says
**keep / consider / dismantle / check it** in seconds. It tracks missing build pieces and shows the current game
tasks in your language. It never touches game memory. 10 interface languages; anyone can add their own.

**TR** — *The Division 2* için ekran okuyan yardımcı: eşyayı okur, aktif build'inle karşılaştırır, saniyeler içinde
**sakla / düşün / kır** der; eksik parçaları ve görevleri takip eder. Oyunun belleğine dokunmaz.
Türkçe tam kılavuz: [`README.tr.md`](README.tr.md).

## Install (Windows)

1. Install **Python 3.13** (3.12 works). The OCR engine (RapidOCR) is installed automatically by `run.bat`.
   **Tesseract OCR** is optional — only a fallback (UB Mannheim build, `C:\Program Files\Tesseract-OCR`).
2. **Code → Download ZIP**, extract.
3. Start with **`scripts\run.bat`** — it picks the right Python, installs the required packages and tries the optional
   ones (OCR: rapidocr, onnxruntime; voice: pyttsx3, sounddevice, faster-whisper; video: av).
4. Optional: `scripts\build_exe.bat` builds a single `.exe`; `scripts\install_claude_code.bat` sets up Claude Code for
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
