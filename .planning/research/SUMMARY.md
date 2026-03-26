# Project Research Summary

**Project:** plugin.video.dhakaflix
**Domain:** Kodi video addon — LAN h5ai file server media browser
**Researched:** 2026-03-27
**Confidence:** HIGH

## Executive Summary

plugin.video.dhakaflix is a Kodi 21 Omega video plugin that browses 9 h5ai file server categories across 4 LAN IP addresses and plays video files directly in Kodi. Experts build this type of addon as a stateless Python script invoked once per user navigation, rendering directory listings via the `xbmcplugin` API and resolving playback via `setResolvedUrl`. The established pattern is a thin entry-point router in `main.py` backed by a pure-Python h5ai API client in `lib/h5ai.py`. A working TypeScript reference implementation (the Raycast dhaka-flix-extension) already encodes the h5ai API contract, server config, and sort/filter logic — porting this to Python is the primary implementation task.

The recommended stack is all Kodi built-ins plus Python stdlib: `xbmcplugin`, `xbmcgui`, `xbmcaddon`, `xbmcvfs` for the Kodi layer, and `urllib.request` + `json` for all HTTP calls. No external dependencies are required for v1. The routing module `script.module.routing` is available but unnecessary for an addon with only 4 actions — manual `sys.argv` + `urllib.parse` dispatch is simpler and removes a dependency. The `InfoTagVideo` setter API (`getVideoInfoTag()`) must be used for metadata — the deprecated `setInfo()` dict approach generates warnings and will break in future Kodi versions.

The highest risks are infrastructure-level pitfalls that must be wired in before any feature work: always calling `endOfDirectory` even on exceptions (prevents permanent Kodi freezes), reading `sys.argv` inside the entry function not at module scope (prevents stale handle bugs with `reuselanguageinvoker`), and always percent-encoding h5ai `href` paths in plugin:// URLs (required because LAN folder names contain spaces). These are mechanical patterns, not design decisions — they should be established in Phase 1 and never revisited.

## Key Findings

### Recommended Stack

The Kodi plugin API is stable and well-documented. All required modules (`xbmcplugin`, `xbmcgui`, `xbmcaddon`) are built into Kodi — no installation required. The only external dependency worth considering is `script.module.routing`, but with 4 routes (root, browse, play, search), manual dispatch in ~15 lines of Python is cleaner. Python stdlib `urllib.request` covers all h5ai API calls — Kodi's embedded Python 3 does not include `requests` and `xbmcvfs` was intentionally broken for HTTP in Kodi 19+.

**Core technologies:**
- `xbmcplugin`: Directory listing API — `addDirectoryItem`, `endOfDirectory`, `setContent`, `setResolvedUrl`
- `xbmcgui.ListItem` + `getVideoInfoTag()`: Item creation and metadata — use InfoTagVideo setters, never `setInfo()`
- `urllib.request` (stdlib): h5ai POST API client — zero addon dependencies for one LAN endpoint
- `xbmcaddon.Addon()`: Addon settings and path resolution
- `xbmcvfs.translatePath()`: Kodi path translation for data directories (not HTTP)
- `Kodistubs` + `pytest` + `kodi-addon-checker`: Dev-only tooling for IDE hints, unit tests, repo validation

### Expected Features

**Must have (table stakes):**
- Category list on launch — 9 hardcoded servers (English Movies, Hindi Movies, South Movies Hindi Dubbed, Kolkata Bangla Movies, Animation Movies, Foreign Language Movies, TV Series, Korean TV and Web Series, Anime)
- Folder hierarchy navigation — each level is a fresh h5ai API call
- Playable video items — `IsPlayable=true` + direct HTTP URL; Kodi handles codec/subtitle/resume natively
- File type icons — visual distinction between folders and video files
- File size display — h5ai `size` field in bytes, formatted for the listing label
- Sorted listings — folders first, then by type, then natural name sort (port from reference TypeScript)
- Back navigation — automatic via Kodi's directory stack; no addon work needed
- Error handling on network failure — catch HTTP exceptions, call `endOfDirectory(succeeded=False)`, show notification

**Should have (differentiators):**
- Cross-server search — highest-value feature after basic browsing; fetch all top-level series/movie folders across all 9 categories and filter by query
- Per-category search — scoped version; lower complexity, good intermediate step
- Non-video file filtering — hide `.nfo`, `.jpg`, `.srt` clutter from video-only folders
- Graceful per-server unavailability — show disabled "(Unavailable)" item rather than crashing when one of 4 servers is down
- Plugin fanart and category icons — visual branding; low effort, improves Kodi skin integration

**Defer (v2+):**
- Favorites / bookmarks — no Kodi native API; requires addon-managed persistence
- File date display — low user value, easy to add incrementally
- Concurrent multi-server search fetching — optimize only if serial search speed becomes a real complaint
- Settings UI for server configuration — servers are infrastructure, not user-configurable

Anti-features to never build: watch history (Kodi native), download to local storage, metadata scraping (TMDB/IMDB), dynamic server discovery, authentication, pagination.

### Architecture Approach

The addon is a stateless Python script invoked once per user navigation with `sys.argv` carrying the plugin:// URL. Each invocation either renders a directory listing or resolves a playback URL, then exits. There is no long-running process or persistent in-memory state. The architecture separates the h5ai API client (`lib/h5ai.py`, pure Python, no Kodi imports) from the Kodi UI layer in `main.py`. Server config lives in `lib/config.py` as a static list of 9 dicts. The `main.py` entry point handles routing, calls the h5ai client, and translates results into Kodi `ListItem` objects.

**Major components:**
1. `main.py` (Entry Point / Router): Parse `sys.argv`, dispatch to view functions, own all `xbmcplugin`/`xbmcgui` API calls
2. `lib/h5ai.py` (API Client): POST to h5ai endpoint, parse JSON response, classify file types, apply sort order, return `list[MediaItem]` — no Kodi imports
3. `lib/config.py` (Server Config): Static list of 9 server dicts (name, base_url, path, api_path) — read-only data module
4. `addon.xml` (Manifest): Declare plugin ID, `xbmc.python 3.0.1`, `<provides>video</provides>` extension point
5. `resources/` (Assets): `icon.png` (256x256), `fanart.jpg` (1920x1080), optional `settings.xml`

**Key boundary rule:** `lib/h5ai.py` must never import xbmc* modules. All Kodi API calls are in `main.py` only.

### Critical Pitfalls

1. **endOfDirectory never called on exception** — Kodi freezes in permanent loading spinner. Wrap entire plugin body in `try/except`; call `endOfDirectory(handle, succeeded=False)` in except branch. Wire this in before any other logic.
2. **Stale plugin handle from reuselanguageinvoker** — navigation randomly fails on second visit. Always read `sys.argv[1]` inside the entry function, never at module scope. Pass handle explicitly to all functions.
3. **h5ai href paths not percent-encoded in plugin:// URLs** — folder names with spaces or parentheses corrupt query strings; navigating into any LAN category fails immediately. Use `urllib.parse.quote(href, safe="")` when embedding paths in plugin:// URL parameters.
4. **IsPlayable / isFolder mismatch** — black screen on video click or empty listing on folder click. Folders: `isFolder=True`, no IsPlayable; video files: `isFolder=False`, `li.setProperty("IsPlayable", "true")`, direct `http://` URL.
5. **No HTTP timeout** — unreachable server blocks UI forever. Always pass `timeout=6` (or 10) to `urlopen`. Return empty list on `URLError`/`TimeoutError`.

Additional traps: using removed `xbmc.LOGNOTICE` (raises `AttributeError` at startup), using `setInfo()` dict API (deprecated Kodi 20, remove Kodi 21), using `parse_qs` instead of `parse_qsl` (routing never matches), setting `cacheToDisc=True` (serves stale directory listings), wrong `setContent` type (use `"files"` for folder listings, not `"movies"`).

## Implications for Roadmap

Based on research, the build order has clear dependency constraints and the components are small enough that 3 phases are sufficient.

### Phase 1: Foundation and Browse

**Rationale:** Everything depends on a working directory browser. The h5ai client can be tested standalone (pure Python + LAN) before any Kodi API work. All critical pitfalls (handle management, endOfDirectory, URL encoding, logging constants) must be established here — retrofitting them is dangerous.

**Delivers:** A fully navigable addon — category list on launch, drill-down into any h5ai folder hierarchy, correct icons and file sizes, sorted listings, graceful error handling when a server is unreachable.

**Addresses (from FEATURES.md):** Category list, folder hierarchy navigation, file type icons, file size display, sorted listings, back navigation, loading feedback, error handling.

**Avoids (from PITFALLS.md):** Pitfall 1 (endOfDirectory on exception), Pitfall 2 (IsPlayable/isFolder for folders), Pitfall 3 (reuselanguageinvoker), Pitfall 4 (missing provides tag), Pitfall 5 (URL encoding), Pitfall 7 (wrong setContent), Pitfall 8 (LOGNOTICE removed), Pitfall 10 (no timeout), Pitfall 11 (folder name mismatch), Pitfall 12 (parse_qs), Pitfall 14 (cacheToDisc stale), Pitfall 15 (log level defaults).

**Build sub-order:** `lib/config.py` → `lib/h5ai.py` (+ standalone tests) → `addon.xml` → `main.py` browse routing → error handling wrappers.

### Phase 2: Playback

**Rationale:** Playback is a small addition to browse (one new route, one `setResolvedUrl` call, `IsPlayable` property on video ListItems) but warrants its own phase to validate the IsPlayable/isFolder table from PITFALLS.md Pitfall 2. Separating this from browse makes it easy to verify each item type works correctly.

**Delivers:** Users can click any video file and it plays in Kodi's built-in player. Resume, subtitles, and watch state are handled natively by Kodi — no addon work.

**Addresses (from FEATURES.md):** Playable video items.

**Avoids:** Pitfall 2 (IsPlayable/isFolder mismatch), confirmed direct `http://` URL approach without two-step resolve.

**Note:** Non-video file filtering (hide `.nfo`, `.srt`, `.jpg` from listings) fits naturally at the end of this phase — it makes video-only folders cleaner and the implementation is a one-line filter in `h5ai.py`.

### Phase 3: Search

**Rationale:** Search depends on a working browse implementation (search results are rendered as a browse listing) and requires the most careful design due to multi-server bulk HTTP fetching. Per-category search should be built first as it is a scoped, simpler version of cross-server search with shared infrastructure.

**Delivers:** A "Search" entry in the category menu; per-category search; cross-server search across all 9 servers. Users can find a specific title without knowing which server it lives on.

**Addresses (from FEATURES.md):** Search entry in category menu, per-category search, cross-server search.

**Avoids:** Pitfall 6 (serial fetches block UI — use `ThreadPoolExecutor` with concurrency limit), Pitfall 13 (check `kb.isConfirmed()` before `getText()`).

**Design note:** The reference Raycast implementation uses serial chunked fetching to avoid OOM. For Kodi, `concurrent.futures.ThreadPoolExecutor(max_workers=3)` with a `DialogProgress` is the right approach — gives speed without excessive parallelism.

### Phase 4: Polish (Optional)

**Rationale:** Visual and UX improvements that are low-risk and can be done in any order after Phase 3. None are blocking.

**Delivers:** Plugin fanart, per-category icons, graceful "(Unavailable)" items for downed servers, file date display in listings.

**Addresses (from FEATURES.md):** Plugin fanart/branding, category icons, graceful per-server error display, file date display.

### Phase Ordering Rationale

- `lib/config.py` and `lib/h5ai.py` have no Kodi dependencies and can be written and unit-tested with plain Python before Kodi is involved — this reduces the feedback loop for the core data logic.
- Browse must precede playback because `IsPlayable` applies only to items rendered via the browse flow.
- Browse must precede search because search reuses browse's listing renderer.
- All critical pitfalls cluster in Phase 1 — establishing them early means they never need to be retrofitted.
- Polish deferred to Phase 4 ensures functional correctness is validated before cosmetic work begins.

### Research Flags

Phases with well-documented patterns (skip research-phase):
- **Phase 1 (Foundation/Browse):** Fully covered by reference implementation + official Kodi docs. h5ai API contract is known from working TypeScript code. Standard patterns apply.
- **Phase 2 (Playback):** `setResolvedUrl` pattern is straightforward; single function addition. No research needed.
- **Phase 4 (Polish):** Pure Kodi UI, no complexity.

Phases that may benefit from targeted research during planning:
- **Phase 3 (Search):** The concurrent multi-server fetch with `ThreadPoolExecutor` inside Kodi's embedded Python deserves a quick validation pass — specifically whether `concurrent.futures` behaves correctly under Kodi's watchdog timeout and whether `DialogProgress` cancellation works cleanly mid-fetch.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations verified against official Kodi docs, Kodistubs, and the romanvm reference plugin. One caveat: exact Python version in Kodi 21 Omega's embedded interpreter is not officially documented — write 3.8-safe code. |
| Features | HIGH | Feature list derived from a working reference implementation (Raycast extension) using the same h5ai API. Anti-features explicitly confirmed against project scope doc. |
| Architecture | HIGH | Architecture pattern verified from official Kodi wiki HOW-TO, Kodistubs API docs, and romanvm/plugin.video.example reference addon. h5ai API contract is from working TypeScript code. |
| Pitfalls | HIGH | 15 pitfalls documented from official Kodi forum threads, GitHub issues, and Kodi changelog entries. Most have exact error messages for detection. |

**Overall confidence:** HIGH

### Gaps to Address

- **Exact Python version in Kodi 21 Omega:** Official docs do not state the minimum embedded Python version. Write Python 3.8-compatible code universally; do not use 3.9+ syntax (walrus operators in complex expressions, `dict|dict` merge, etc.). Validate on actual Kodi 21 install.
- **`reuselanguageinvoker` behavior in practice:** Research recommends disabling it during development and leaving it unset (disabled by default) for v1. If it is ever enabled, the `sys.argv` reading pattern must be validated carefully. Not blocking for v1.
- **`concurrent.futures` in Kodi's Python sandbox:** ThreadPoolExecutor is in stdlib and expected to work, but the interaction with Kodi's plugin watchdog on long-running parallel requests should be verified during Phase 3 rather than assumed.
- **h5ai response format edge cases:** The API contract is known from the reference implementation. Verify the direct-children-only filter logic handles edge cases (paths with trailing slashes, percent-encoded vs decoded hrefs) on real LAN data during Phase 1 testing.

## Sources

### Primary (HIGH confidence)
- Raycast reference implementation (`../dhaka-flix-extension/`) — h5ai API contract, server config, file classification, sort order (working code)
- [xbmcplugin API docs](https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d1/d32/group__python__xbmcplugin.html) — addDirectoryItem, endOfDirectory, setResolvedUrl, setContent, addSortMethod
- [Kodistubs documentation](https://romanvm.github.io/Kodistubs/) — all xbmc* module signatures
- [romanvm/plugin.video.example](https://github.com/romanvm/plugin.video.example) — reference minimal video addon (Kodi 20+, Python 3)
- [Kodi Wiki: HOW-TO:Video addon](https://kodi.wiki/view/HOW-TO:Video_addon) — canonical addon tutorial
- [Kodi Wiki: Addon.xml](https://kodi.wiki/view/Addon.xml) — manifest schema

### Secondary (MEDIUM confidence)
- [Kodi Forum — IsPlayable & IsFolder confusion](https://forum.kodi.tv/showthread.php?tid=316042) — Pitfall 2 validation
- [Kodi Forum — Invalid handle -1 error](https://forum.kodi.tv/showthread.php?tid=257787) — Pitfall 3 validation
- [GitHub — reuselanguageinvoker crash issue](https://github.com/xbmc/xbmc/issues/21653) — Pitfall 3 source
- [GitHub — LOGNOTICE removal PR](https://github.com/xbmc/xbmc/pull/18346) — Pitfall 8 source
- [script.module.routing Omega page](https://kodi.tv/addons/omega/script.module.routing/) — version 0.2.3+matrix.1 confirmed
- [ListItem.setInfo() deprecation discussion](https://forum.kodi.tv/showthread.php?tid=369255) — InfoTagVideo setters confirmed for Kodi 20+

### Tertiary (LOW confidence)
- xbmc.python version 3.0.1 for Kodi 21 Omega — confirmed via forum/fossies sources, not directly from kodi.wiki (wiki pages returned empty during research). Treat as likely correct; validate on first install.

---
*Research completed: 2026-03-27*
*Ready for roadmap: yes*
