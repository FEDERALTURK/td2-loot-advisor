# TD2 Loot Advisor — Project Structure

The project keeps launch and extension compatibility at the root while new
implementation is grouped by responsibility under `td2app/`.

## Entry points

- `app.py` — Windows desktop application entry point and composition root.
- `scripts/run.bat` — user-facing local launcher.
- `scripts/launch.py` — lightweight dependency check and launcher.
- `TD2LootAdvisor.spec` — Windows package definition.

## Application packages

- `td2app/ui/` — theme, visual HUD, opening animation, UI artwork, 3D view,
  animated background and cursor/transition effects.
- Root compatibility modules such as `ui_theme.py` and `fx.py` forward to the
  package so existing tests, scripts and third-party local extensions do not
  break while the codebase is reorganized.

## Planned source groups

The remaining root modules are deliberately migrated in small, testable
groups rather than with a disruptive one-shot rename:

| Group | Current modules | Target package |
| --- | --- | --- |
| Core decisions | `engine`, `gamedata`, `itempolicy`, `stash` | `td2app/core` |
| Screen and OCR | `capture`, `display`, `ocr_backend`, `winocr` | `td2app/vision` |
| Translation and speech | `livetranslate`, `overlay`, `speech`, `voicepack`, `terms`, `trscreen` | `td2app/translation` |
| Services and sync | `localapi`, `service`, `syncer`, `updater`, `reports`, `notify` | `td2app/services` |
| Game and community data | `gameinfo`, `meta_sync`, `wiki_sync`, `vendor`, `tasks_live` | `td2app/data` |

This staged layout preserves the stable `app.py` entry point and allows each
group to be covered by its existing tests before it is moved.
