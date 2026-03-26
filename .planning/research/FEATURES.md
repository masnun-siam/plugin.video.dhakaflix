# Feature Landscape

**Domain:** Kodi video addon — h5ai file server media browser
**Researched:** 2026-03-27
**Reference implementation:** Raycast extension at `../dhaka-flix-extension/`

---

## Table Stakes

Features that every Kodi video addon of this type must have. Missing any of these and users will consider the addon broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Category list on launch | Entry point into the media hierarchy; without it there is nothing to do | Low | 9 hardcoded servers from `config.ts`: English Movies, Hindi Movies, South Movies Hindi Dubbed, Kolkata Bangla Movies, Animation Movies, Foreign Language Movies, TV Series, Korean TV and Web Series, Anime |
| Folder hierarchy navigation (browse) | Media is organized in nested folders; users must drill down to reach files | Low | h5ai `action=get` returns direct children only; each navigation step is a fresh API call |
| Playable video items | The whole reason the addon exists | Low | `li.setProperty('IsPlayable', 'true')` + pass HTTP URL; Kodi handles codecs natively for mkv/mp4/avi/mov/wmv/flv/webm/m4v |
| File type icons | Visual distinction between folders, video files, and other items | Low | Kodi `ListItem` supports `setArt({'icon': ...})`; use built-in Kodi icons for folder/video/audio/document types |
| File size display | Users judge which file to pick (1080p vs 720p copies) based on size | Low | h5ai `size` field is bytes; format as `formatBytes()` like the Raycast extension; show in ListItem label/info |
| Sorted listing (folders first, then by name) | Raw h5ai response ordering is unpredictable; users need a consistent, navigable list | Low | Sort priority: folder=0, video=1, audio=1, image=2, archive=3, document=3; then `localeCompare` with numeric sensitivity |
| Back navigation (up folder) | Users need to reverse course; Kodi's built-in back button must work correctly | Low | Handled automatically by Kodi's directory stack when each level is a proper plugin URL with its own handle |
| Loading state / spinner | Large folders take time over LAN; users need visual feedback that the addon is working | Low | `endOfDirectory(handle, succeeded=True)` with Kodi's default loading indicator is sufficient |
| Error handling on network failure | LAN servers can be unreachable (server off, IP conflict); addon must not crash | Low-Med | Catch HTTP exceptions, show empty list with `xbmcgui.Dialog().notification()` or set an empty listing gracefully |

---

## Differentiators

Features that are not expected but create meaningful value for this specific use case. Each adds complexity — only build what the user base will actually use.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Cross-server search | Dhaka Flix has 9 categories across 4 IPs; finding a specific title by browsing is tedious | High | Requires fetching all top-level series folders from every category (same pattern as `fetchAllSeries` in reference), then filtering by query string; for TV/Anime: walk category subfolders first. This is the highest-value feature after basic browsing. |
| Per-category search | Search within one server instead of all | Medium | Simpler version of cross-server search — fetch only the selected category's series list, then filter. Lower memory cost. |
| "Search" entry in category menu | Surface the search flow without the user knowing to dig for it | Low | Add a "Search" ListItem at the top of the category list that launches `xbmc.Keyboard` input |
| File date display | Useful for "what was added recently" scanning | Low | h5ai `time` is a Unix timestamp in milliseconds; divide by 1000, format as date string, attach to ListItem `setInfo('video', {'date': ...})` |
| Non-video file type filtering | Movie folders often contain `.nfo`, `.jpg`, `.srt` files alongside the video — hiding these declutters the listing | Low | Filter out items where `type` is image, document, or archive unless the parent folder has no video files at all |
| Plugin fanart / branding | Makes the addon look native within Kodi skins | Low | `xbmcplugin.setPluginFanart()` at directory level; one background image bundled in `resources/` |
| Category icons / art | Each category (English Movies, Anime, etc.) can have a distinct thumbnail | Low | Bundle one icon per category in `resources/media/`; set via `ListItem.setArt({'thumb': ...})` |
| Concurrent multi-server fetching | Search currently fetches servers serially (reference does this to avoid OOM); parallel fetching with a concurrency limit gives faster search results | Medium | Use `concurrent.futures.ThreadPoolExecutor` with `max_workers=3`; balance speed vs Kodi's Python memory constraints |
| Graceful per-server error display | If one of the 4 servers is unreachable, the others should still work | Low | Wrap each server fetch in try/except; show a disabled/grayed-out ListItem with "(Unavailable)" label for the failed category |

---

## Anti-Features

Features to explicitly NOT build. These are either out of scope by design (from `PROJECT.md`) or patterns that cause maintenance burden without user value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Favorites / bookmarks | Out of scope for v1; Kodi has no built-in plugin favorites API — implementing it requires writing to addon data files and maintaining a sync mechanism | Defer; add as a v2 feature after validating demand |
| Watch history / resume tracking | Kodi tracks watch state natively for any item played via `setResolvedUrl` or `setProperty('IsPlayable', 'true')`; duplicating this in the addon creates divergence | Let Kodi handle it natively — no work needed |
| Download to local storage | LAN streaming at 1Gbps makes local copies unnecessary; adds file management complexity | Rely on Kodi's streaming |
| Subtitle management | Kodi's built-in subtitle system handles `.srt`/`.ass` files in the same folder automatically | Do nothing; Kodi detects co-located subtitle files |
| Dynamic server discovery | Servers are static LAN infrastructure at known IPs; mDNS or ping-based discovery adds latency and complexity for no benefit | Hardcode the 9 server configs matching the Raycast extension |
| User authentication / login | h5ai servers have no auth; adding auth UI creates dead UI with no backend | Nothing to build |
| VPN / remote access configuration | The addon is explicitly LAN-only by design | Document the LAN requirement; no in-addon config |
| Metadata scraping (TMDB/IMDB enrichment) | Would require internet access + API keys + a separate scraper addon; mismatches on filenames are common and debugging is painful | Let users use Kodi's native library scraper if they want metadata enrichment — that is a separate concern from browsing |
| Custom video player UI | Kodi's built-in player has codec support, subtitles, OSD, and resume — building a custom player is regression | Pass HTTP URL and call `setResolvedUrl`; player handles the rest |
| Pagination / "load more" | LAN responses are fast; folder sizes stay manageable (hundreds of items at most) | Load full directory in one request; Kodi's list view handles large item counts fine |
| Settings UI for server configuration | Servers are infrastructure, not user-configurable; a settings form encourages misconfiguration | Hardcode config in Python; if servers change, the developer updates the addon |

---

## Feature Dependencies

```
Category list
    └── Folder hierarchy navigation
            └── File type detection (icon + filtering)
                    └── Playable video items
                            └── Kodi native player (no addon work)

Cross-server search
    └── Category list (server configs reused)
    └── File type detection (filter to folders/videos in search results)
    └── Playable video items (search result can be played directly)

Per-category search
    └── Category list (must select a category first)
    └── Cross-server search (shared search logic, scoped to one server)
```

---

## MVP Recommendation

Build in this order:

1. **Category list** — the entry point; no addon works without this
2. **Folder hierarchy navigation** — drilling into categories and subfolders
3. **File type detection + sorting** — correct icons, size display, folders-first sort
4. **Playable video items** — the core value; everything above is preamble
5. **Basic error handling** — graceful failure when a server is unreachable
6. **Search (per-category first, then cross-server)** — highest-impact differentiator; defer until navigation is solid

Defer:
- Fanart / branding: nice-to-have, do after core works
- Non-video file filtering: do after seeing real usage patterns
- Concurrent fetching: optimize only if search speed is a real complaint
- File date display: low priority, easy to add later

---

## Sources

- Kodi official documentation: [xbmcplugin API](https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d1/d32/group__python__xbmcplugin.html)
- Kodi official documentation: [ListItem API](https://alwinesch.github.io/group__python__xbmcgui__listitem.html)
- Reference implementation: `../dhaka-flix-extension/src/` (TypeScript/Raycast, HIGH confidence — same API, proven behavior)
- Kodi developer notes: [pewpewnotes KodiAddonDev](https://pewpewnotes.github.io/KodiAddonDev.html)
- Kodi forum: [Search implementation thread](https://forum.kodi.tv/showthread.php?tid=312476)
- Kodi forum: [h5ai + Kodi compatibility](https://forum.kodi.tv/showthread.php?tid=160147)
- PROJECT.md Out of Scope section (authoritative for this project)
