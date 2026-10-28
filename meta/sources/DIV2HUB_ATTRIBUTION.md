# Division 2 Community Data Hub attribution

The CSV snapshot in `meta/sources/div2hub/` is from [div2hub/game-data](https://github.com/div2hub/game-data), commit `8d5e75b2fb9eb93118e3958a0b49cbf78e71b0a0` (2026-10-17).

The source compilation is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Its license and source README are included alongside the snapshot. The game content itself belongs to Ubisoft and Massive Entertainment; the community dataset does not claim otherwise.

The application catalog imports weapon and gear names, fixed item talents, slot definitions, talent compatibility/descriptions, weapon-mod compatibility/effects, gear-mod ranges, attributes, skill variants, and Prototype Augments from this snapshot. The project retains its previous records where the snapshot has no matching entry and records the import version in `meta/game_data.json`.

The snapshot does not contain a complete loot Skill Mod catalog. Skill Mods have variant-specific gameplay effects and variable rolls; this project does not invent those records.
