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

## License

MIT — see [`LICENSE`](LICENSE).

*Not affiliated with or endorsed by Ubisoft. The Division is a trademark of Ubisoft Entertainment.*
