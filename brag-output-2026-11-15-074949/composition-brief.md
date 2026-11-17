# Hyperframes Composition Brief: TD2 Loot Advisor

## Objective
Create a short launch-style brag video for TD2 Loot Advisor using its real product vocabulary and visual identity.

## Output
- Composition directory: `C:\Users\PC\Desktop\Thedivision2program\brag-output-2026-11-15-074949\composition\`
- Rendered video: `..\brag.mp4`
- Format: landscape — 1920x1080
- Duration: 20 seconds

## Source Material
- Project root: `C:\Users\PC\Desktop\Thedivision2program`
- Primary files read: `README.md`, `app.py`, `td2app/ui/ui_theme.py`, `meta/game_data.json`, `icon/td2.png`
- Product name: TD2 Loot Advisor
- Tagline / strongest claim: “A screen-reading (OCR) helper for Tom Clancy's The Division 2”; “It never touches game memory.”
- Key UI or visual moment to recreate: Panel item scan → build-aware verdict → Stash/Tasks breadth.
- Copy that must appear verbatim:
  - `HOVER → F8 → KNOW.`
  - `LOCAL OCR · NO GAME MEMORY.`
  - `TD2 LOOT ADVISOR · v9.1.5.35`

## Creative Direction
- Tone preset: cinematic
- Creative direction: restrained SHD field-terminal boot sequence with crisp evidence beats
- Interpretation: readable UI, dark graphite panels, cyan accent, restrained orange scan marks, no generic startup language.
- Angle: one hovered item becomes a build-aware decision through local OCR and explicit REVIEW safety.
- Hook: terminal boot + “HOVER → F8 → KNOW.” in the first three seconds.
- Outro / punchline: “KEEP YOUR BUILD. REVIEW THE UNKNOWN.”
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unverified performance numbers
  - Any claim of game-memory access or gameplay automation

## Visual Identity
- Background: `#0a0d12`
- Text: `#eef2f6`
- Accent: `#36e0c4`, with restrained orange scan accents grounded in the product’s TD2 visual language
- Display font: Segoe UI Semibold (or a close system fallback)
- Body font: Segoe UI
- Visual references from the project: dark Tk cards, teal selected states, cyan HUD brackets, OCR/build status rows, `icon/td2.png`.

## Storyboard
Use the storyboard in `brag-plan.md` as the creative contract.

Scene summary:
1. SHD boot / hook — 3.0s — scan line and readable hook.
2. OCR card read — 5.0s — item card and OCR rows.
3. Build-aware decision — 5.0s — requirement checks and KEEP/CONSIDER/REVIEW.
4. Stash / Tasks / local-first breadth — 4.0s — Builds, Stash, Tasks panels.
5. Lockup — 5.0s — icon, grounded safety line, version.

## Audio
- Audio role: cinematic support
- Audio arc: low terminal pulse → precise UI reveals → soft final impact and fade.
- Music: `assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`
- Music treatment: low 0.22–0.28 volume, short fade-in/out, duck under final lockup.
- Music cue guidance: `assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json`; major cues around 2.0s, 8.0s and 17.5s; sequential text should use every other beat for readability.
- Audio-reactive treatment: subtle; modulate existing scan halo/card presence from RMS or bass only, with no waveform graphics.
- Audio-coupled moments:
  - Scene 1 hook — UI tick and scan glow.
  - Scene 2 OCR rows — staggered soft reveals.
  - Scene 3 verdict — one restrained confirmation cue.
  - Scene 5 final logo — soft impact and halo settle.
- SFX selection guidance: prefer low/medium-HF interface clicks, drops and one soft impact; no weapon audio.
- SFX analysis guidance: use the brag skill’s `assets/sfx/sfx-analysis.md` if available.
- Exact SFX choice: Hyperframes should choose filenames, timestamps, density and volume based on the implemented animation.
- Audio files: music and cue metadata are already copied into `composition/assets/music/`.

## Hyperframes Instructions
Use the current Hyperframes composition contract, registry, media-use and CLI skills. Do not write a generic storyline or SPEC.md. Use the real product vocabulary above, keep all text readable, keep the total duration 15–25 seconds, run `npx hyperframes check` before render, and keep all creation/rendering local.
