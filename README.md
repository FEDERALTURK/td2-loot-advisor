# TD2 Loot Advisor

**EN** — A screen-reading (OCR) helper for *Tom Clancy's The Division 2*. It reads the item on screen,
compares it with your build rules and tells you **keep / consider / dismantle** in seconds. It never touches
game memory. 10 interface languages, anyone can add their own.

**TR** — *The Division 2* için ekran okuyan (OCR) yardımcı. Ekrandaki eşyayı okuyup build kurallarınla
karşılaştırır ve saniyeler içinde **sakla / düşün / kır** der. Oyunun belleğine dokunmaz. 10 dil.

## Daily meta feed / Günlük meta akışı

`meta/meta_builds.json` is the central list of current meta and most-discussed builds. Every copy of the app
downloads it once a day at startup (with a jsDelivr CDN fallback) and merges it without touching the user's
own builds.

- Raw: `https://raw.githubusercontent.com/FEDERALTURK/td2-loot-advisor/main/meta/meta_builds.json`
- CDN: `https://cdn.jsdelivr.net/gh/FEDERALTURK/td2-loot-advisor@main/meta/meta_builds.json`

How the feed is researched and scored: [`meta/UPDATER.md`](meta/UPDATER.md).

*Not affiliated with or endorsed by Ubisoft. The Division is a trademark of Ubisoft Entertainment.*
