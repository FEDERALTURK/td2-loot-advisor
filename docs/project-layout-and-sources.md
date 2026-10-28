# Navigation, project layout, and news sources

## Application navigation

The home window groups the existing pages into six top-level sections: Home, Gear, Intel, Tools, Settings, and More. The Gear, Intel, Tools, and More sections keep their existing pages as nested tabs. This reduces the top-level tab row without changing the page identifiers used for app navigation or saved last-page state.

Settings are grouped into Basics, Capture, Display, and Services. All six global application shortcuts live on Settings > Basics > Shortcuts. The keyboard capture button fills a shortcut field; Save rejects invalid or conflicting bindings before applying them.

## Source tree

- Python entry points and application modules remain in the repository root because the launcher, frozen build, imports, and updater use these paths.
- meta/agents/ contains the curated agent/item image set; meta/sources/ contains reference data; meta/voices/ contains offline voice clips.
- meta JSON, CSV, and XLSX files contain versioned game data and app feeds. They are not disposable build output.
- docs/ contains maintained user and engineering notes; tests/ contains isolated and runtime probes.
- Personal settings, task completion state, caches, logs, and generated reports are kept outside the public source checkout or ignored. They should not be moved into tracked feeds.

The image and voice collections are intentionally kept in their established paths for the runtime and installer. Moving hundreds of assets would change packaging contracts without reducing the user's visible menu clutter.

## The Division 2 task information

The task page combines the versioned meta/tasks_feed.json, live Wiki-derived guides, and the optional community task endpoint. Community tasks are accepted only after distinct-player reports meet the server threshold. Expired task entries are removed by the existing synchronization logic. The task sync page links directly to Ubisoft's official Division news and to community-maintained project guidance; the app labels each task with its source.

Seasonal task details change faster than static application releases. The official Ubisoft articles establish what is announced; the current live game screen and validated community feed help confirm active objectives. Treat third-party guides as how-to references, not official schedules.

## The Division 3 information page

meta/division3_feed.json is a small, reviewed source list and timeline shown in the Intel > The Division 3 page. Its status text is based on Ubisoft's 2023 announcement and the current Massive Entertainment job listing. The page does not infer a release date, platforms, or gameplay from job descriptions. Update the checked date and cited items only after reviewing a direct Ubisoft source.

Primary references:

- [Ubisoft News: Division 3 development announcement](https://news.ubisoft.com/en-au/article/18oNmwEFQzGDu0TYVOAcJN/julian-gerighty-appointed-executive-producer-for-the-division-brand)
- [Ubisoft Careers: Senior AI Game Designer, The Division 3](https://www.ubisoft.com/en-us/company/careers/search/744000127417779-senior-ai-game-designer-tom-clancy-s-the-division-3-)
- [Ubisoft's Division news index](https://www.ubisoft.com/en-gb/game/the-division/news-updates)
