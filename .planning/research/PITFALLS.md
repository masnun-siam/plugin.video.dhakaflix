# Domain Pitfalls

**Domain:** Kodi video plugin addon (plugin.video.dhakaflix) fetching from h5ai HTTP servers
**Researched:** 2026-03-27
**Confidence:** HIGH (multiple official Kodi sources + forum verification)

---

## Critical Pitfalls

Mistakes in this category cause Kodi to freeze, crash, or silently fail with no recoverable state.

---

### Pitfall 1: Not Calling endOfDirectory on Exception

**What goes wrong:** If an unhandled Python exception occurs before `xbmcplugin.endOfDirectory()` is called, Kodi freezes in a perpetual "loading" spinner. The plugin handle is never released. The user must forcefully close Kodi to recover.

**Why it happens:** Developers wrap only the happy path in the addon. A network timeout or a malformed JSON response from the h5ai API throws an exception mid-execution, skipping the `endOfDirectory` call entirely.

**Consequences:** Every network call to an h5ai server is a potential exception site. On a LAN, servers can be unreachable or slow to respond. Without protection, the first server hiccup permanently freezes the current directory.

**Prevention:**

Wrap the entire plugin body in try/except and always call `endOfDirectory` in the except branch with `succeeded=False`:

```python
def run():
    try:
        # all plugin logic here
        xbmcplugin.endOfDirectory(HANDLE, succeeded=True)
    except Exception as e:
        xbmc.log(f"[dhakaflix] Fatal error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("DhakaFlix", str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
```

**Detection:** If the Kodi UI spins indefinitely after navigating into a category, this pitfall is the first thing to check in `kodi.log`.

**Phase:** Foundation / Phase 1 — wire this in before any other logic.

---

### Pitfall 2: IsPlayable / IsFolder Mismatch Causes Black Screen or Wrong Navigation

**What goes wrong:** Setting conflicting or wrong `isFolder` and `IsPlayable` properties on a `ListItem` causes one of two symptoms: a folder item gets played (Kodi tries to resolve a plugin:// URL as a stream and produces a black screen), or a playable file opens a directory listing that goes nowhere.

**Why it happens:** There are three distinct scenarios in this addon:

| Item type | `isFolder` param | `ListItem.setProperty("IsPlayable", ...)` | Correct handler |
|-----------|-----------------|-------------------------------------------|----------------|
| Directory (h5ai folder) | `True` | not set (or `"false"`) | `addDirectoryItem` |
| Playable video file | `False` | `"true"` | `addDirectoryItem` with plugin:// URL, then `setResolvedUrl` |
| Immediate play (direct) | N/A | N/A | `xbmc.Player().play()` |

Mixing these up is extremely common. Many tutorials show the old pattern of calling `xbmcplugin.setResolvedUrl` at the top level, which only works when Kodi calls your plugin back *because* the user clicked a `IsPlayable=true` item.

**Consequences:** Silent failure. Kodi either shows a black screen (wrong stream resolution) or navigates into an empty directory (folder treated as file).

**Prevention:**
- For h5ai subdirectory items: `isFolder=True`, no `IsPlayable` property, URL is `plugin://plugin.video.dhakaflix/?path=...`
- For video file items: `isFolder=False`, `li.setProperty("IsPlayable", "true")`, URL is the direct `http://` stream URL
- Do not use `setResolvedUrl` for direct HTTP streams. Since the h5ai servers return bare HTTP URLs, use `setResolvedUrl` only if you need a two-step resolve. For a direct known URL, set the URL on the ListItem directly.

**Detection:** Black screen on video click, or "loading" spinner that immediately clears with empty listing.

**Phase:** Phase 1 (browse/navigate) for folder items; Phase 2 (playback) for video items.

---

### Pitfall 3: reuselanguageinvoker + Global State = Wrong Handle / Stale Data

**What goes wrong:** When `<reuselanguageinvoker>true</reuselanguageinvoker>` is set, Kodi reuses the Python interpreter instance across addon invocations. Any module-level global that stores `sys.argv[1]` (the plugin handle) will retain the value from the *first* invocation on every subsequent call, causing `addDirectoryItem` calls to target a stale, invalid handle.

**Why it happens:** A pattern like this at module level is the trap:

```python
# BAD — captured once, stale on every reuse
HANDLE = int(sys.argv[1])
```

On the second call, `HANDLE` still holds the integer from call #1. Kodi will log `"Attempt to use invalid handle -1"` or a stale positive integer, and directory items go nowhere.

**Consequences:** Directory navigation randomly fails. Items added successfully on first visit fail silently on revisit. The bug is intermittent, making it hard to diagnose.

**Prevention:**
- Read `sys.argv` inside the entry-point function, not at module scope
- Pass the handle explicitly to all functions that need it
- Set `<reuselanguageinvoker>false</reuselanguageinvoker>` during development; enable it only after verifying the entire addon works correctly without global state

**Detection:** Works on first launch, breaks on second or third navigation into the same directory. `kodi.log` shows `"Attempt to use invalid handle"`.

**Phase:** Foundation — architectural decision before writing routing logic.

---

### Pitfall 4: Missing `<provides>video</provides>` in addon.xml

**What goes wrong:** Without `<provides>video</provides>` in the `xbmc.python.pluginsource` extension point, Kodi categorises the addon as a Program, not a video plugin. It appears in "Programs" instead of "Video add-ons" and cannot be integrated into the Video section of the Kodi home menu.

**Why it happens:** Copying a generic addon template without knowing that `provides` controls Kodi's classification.

**Consequences:** The addon works technically but is invisible to users browsing Video add-ons. Skins and menus that filter by content type will not show it.

**Prevention:**

```xml
<extension point="xbmc.python.pluginsource" library="addon.py">
    <provides>video</provides>
</extension>
```

**Detection:** Addon appears under "Programs" menu rather than "Video add-ons".

**Phase:** Phase 1 — must be correct before first install test.

---

## Moderate Pitfalls

Mistakes that cause incorrect behaviour, user frustration, or maintenance headaches — but are recoverable without a rewrite.

---

### Pitfall 5: URL Encoding of h5ai `href` Paths in Plugin URLs

**What goes wrong:** h5ai returns `href` values like `/English Movies/Action/Film Title (2023)/film.mkv`. When this path is embedded into a Kodi plugin:// URL as a query parameter, unencoded spaces and parentheses corrupt the query string. The addon receives a truncated or mismatched path on the next invocation.

**Why it happens:** Developers use f-strings or naive string concatenation: `plugin://plugin.video.dhakaflix/?path={href}`. The resulting URL is malformed when `href` contains any character outside `[a-zA-Z0-9\-._~]`.

**Consequences:** Navigation into folders with spaces or special characters fails. Filenames with non-ASCII characters (e.g., Bengali, Japanese) in the h5ai index cause `KeyError` or silent empty listings.

**Prevention:**
- Always percent-encode the `href` parameter when building plugin:// URLs: `urllib.parse.quote(href, safe="")`
- When parsing incoming `sys.argv[2]`, use `urllib.parse.parse_qs` which handles decoding automatically
- Double-encode nested paths if a URL is passed inside another URL parameter

**Detection:** Navigating into any folder whose name contains a space or `()` returns an empty listing or a Python `KeyError` in `kodi.log`.

**Phase:** Phase 1 — the h5ai category folders use space-separated names (e.g., "English Movies") so this hits immediately.

---

### Pitfall 6: Fetching All Items for Search Blocks the UI Thread

**What goes wrong:** The search feature (described in the project) requires fetching top-level items from all 9 category folders across 4 server IPs. If done serially in the main plugin execution, this blocks Kodi's UI thread for the entire duration — potentially 5–30 seconds on a loaded LAN.

**Why it happens:** Simple serial `requests.post()` calls in a loop. Each h5ai API call has non-trivial latency even on LAN (TCP handshake + PHP render + JSON response).

**Consequences:** Kodi appears frozen while search runs. The Kodi watchdog may terminate the addon if execution exceeds its timeout threshold.

**Prevention:**
- Use Python's `concurrent.futures.ThreadPoolExecutor` or `multiprocessing.pool.ThreadPool` (both available in Kodi's embedded Python 3) to fire all category-fetch requests concurrently
- Show a `xbmcgui.DialogProgress` while fetching to signal activity
- Set explicit `timeout=` on every `requests.post()` call (recommend 5–8 seconds for LAN). Do not rely on the default (which is "wait forever")

**Detection:** Search causes a long freeze; `kodi.log` shows elapsed time > 5s for the plugin execution.

**Phase:** Phase 3 (search) — must design for concurrency from the start of that phase.

---

### Pitfall 7: Content Type Mismatch Breaks Skin Integration

**What goes wrong:** Calling `xbmcplugin.setContent(HANDLE, "movies")` when displaying a generic file browser (h5ai folders with mixed content types) causes Kodi skins to apply movie-specific scraping, artwork lookup, and sorting rules. The listing renders incorrectly and may trigger unwanted library scans.

**Why it happens:** Developers use "movies" because the addon has movie content. But `setContent("movies")` signals Kodi that every item in the list is a library movie object.

**Consequences:** Incorrect artwork, unexpected sort orders, Kodi treating folders as library items and trying to scrape them.

**Prevention:**
- For directory/folder listings: `setContent(HANDLE, "files")` — generic file browser, no special treatment
- For a leaf listing of video files: `setContent(HANDLE, "videos")` — signals video items without implying library metadata
- Only use `"movies"` or `"tvshows"` if the items have proper `setInfo("video", {...})` metadata populated

**Detection:** Kodi shows placeholder artwork or scraper dialogs when browsing folders.

**Phase:** Phase 1 (folder browse) — use `"files"` immediately. Revisit for Phase 2 if metadata is added.

---

### Pitfall 8: `xbmc.LOGNOTICE` is Removed in Kodi 19+

**What goes wrong:** Using `xbmc.log("msg", xbmc.LOGNOTICE)` or `xbmc.log("msg", xbmc.LOGSEVERE)` raises `AttributeError` in Kodi 21 (Omega), which uses the Python API from Kodi 19+. These constants were removed.

**Why it happens:** Copying logging code from older tutorials or pre-Kodi-19 addons.

**Consequences:** Every log call throws an `AttributeError`, which itself needs to be caught — the entire addon breaks at startup if logging is used at module level.

**Prevention:** Use only the current constants:
- `xbmc.LOGDEBUG`
- `xbmc.LOGINFO`
- `xbmc.LOGWARNING`
- `xbmc.LOGERROR`
- `xbmc.LOGFATAL`

**Detection:** `AttributeError: module 'xbmc' has no attribute 'LOGNOTICE'` in `kodi.log`.

**Phase:** Foundation — use correct constants from the first line written.

---

### Pitfall 9: Third-Party `requests` Library Requires Explicit Dependency Declaration

**What goes wrong:** `import requests` works when developing locally (system Python has it installed) but fails when the addon is installed on a fresh Kodi instance. Kodi's embedded Python interpreter does not include `requests` in its standard library.

**Why it happens:** The developer tests locally with a full Python environment. The `requests` library is silently available. On Kodi, `ModuleNotFoundError: No module named 'requests'` crashes the addon at startup.

**Consequences:** The addon fails on every machine that is not the developer's. Since this project uses `requests.post()` for h5ai API calls, the entire addon is non-functional.

**Prevention:** Add to `addon.xml`:

```xml
<requires>
    <import addon="xbmc.python" version="3.0.0"/>
    <import addon="script.module.requests" version="2.22.0"/>
</requires>
```

Kodi will automatically install `script.module.requests` when the addon is installed. Do **not** bundle a private copy of `requests` in the addon directory — it creates maintenance burden and version conflicts.

**Detection:** `ModuleNotFoundError: No module named 'requests'` in `kodi.log` on a clean install.

**Phase:** Foundation — declare this dependency before writing any API call code.

---

### Pitfall 10: Hardcoded Network Timeout = Silent Freezes on Unreachable Servers

**What goes wrong:** The project has 4 server IPs (`.7`, `.9`, `.12`, `.14`). If one server is offline or unreachable, a `requests.post()` call with no timeout will block indefinitely. This hangs the entire category listing for that server, and by extension blocks the UI if the search feature fetches all servers.

**Why it happens:** `requests.post(url, data=payload)` — no `timeout` argument. Default is `None` (wait forever).

**Consequences:** Browsing a category whose server is down causes permanent UI freeze (see Pitfall 1 above). The user cannot navigate away.

**Prevention:**
```python
try:
    response = requests.post(url, data=payload, timeout=6)
    response.raise_for_status()
except requests.exceptions.Timeout:
    xbmc.log(f"[dhakaflix] Timeout reaching {url}", xbmc.LOGWARNING)
    return []
except requests.exceptions.RequestException as e:
    xbmc.log(f"[dhakaflix] Network error: {e}", xbmc.LOGERROR)
    return []
```

6 seconds is a reasonable LAN timeout — fast enough to fail quickly on a downed server, long enough to survive a momentarily busy PHP process.

**Detection:** Navigating into a category hangs indefinitely; server IP unreachable.

**Phase:** Phase 1 (first h5ai API call) — set timeouts immediately.

---

## Minor Pitfalls

Annoyances that degrade UX but do not break core functionality.

---

### Pitfall 11: Addon Folder Name Must Match addon.xml id Exactly

**What goes wrong:** The filesystem directory containing the addon must be named exactly `plugin.video.dhakaflix` — the same string as the `id` attribute in `addon.xml`. A mismatch (different case, extra characters) causes Kodi to fail to load the addon or fail to find its profile/data directory.

**Prevention:** Name the directory `plugin.video.dhakaflix` from the start. Never rename it without also updating `addon.xml`.

**Detection:** Kodi shows "Add-on could not be loaded" or `xbmcaddon.Addon()` calls return wrong paths.

**Phase:** Foundation — file structure is set at project creation.

---

### Pitfall 12: Duplicate Query Parameter Keys Break Routing

**What goes wrong:** Kodi passes the query string via `sys.argv[2]`. Using `urllib.parse.parse_qs` (which handles duplicate keys by creating lists) instead of `urllib.parse.parse_qsl` can cause `params['mode']` to return `['browse']` instead of `'browse'`, breaking all `if mode == "browse"` comparisons.

**Prevention:** Access query string values consistently. Either use `parse_qs` and always index with `[0]`, or use a helper that normalises single-value params to strings.

```python
params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(sys.argv[2]).query))
# params['mode'] is now 'browse', not ['browse']
```

**Detection:** Routing never matches any mode, addon always falls through to root menu regardless of URL.

**Phase:** Phase 1 — URL routing is fundamental to all navigation.

---

### Pitfall 13: Keyboard Search Input Confirmation Must Be Checked

**What goes wrong:** Using the `xbmc.Keyboard` class for search input without checking `kb.isConfirmed()` before calling `kb.getText()` causes the addon to search with an empty string when the user presses Escape to cancel, returning every item on all servers.

**Prevention:**
```python
kb = xbmc.Keyboard("", "Search DhakaFlix")
kb.doModal()
if not kb.isConfirmed():
    return  # user cancelled, exit cleanly
query = kb.getText()
if not query.strip():
    return
```

**Detection:** Pressing Escape on the search keyboard triggers a full scan of all servers.

**Phase:** Phase 3 (search implementation).

---

### Pitfall 14: cacheToDisc=True Can Serve Stale Directory Listings

**What goes wrong:** `xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=True)` (the default) tells Kodi to cache the directory listing to disk. If the h5ai server contents change, users see stale file listings until the cache expires.

**Why it matters:** For a LAN media server, new content is added regularly. Showing a cached listing that omits newly added files is confusing.

**Prevention:** Use `cacheToDisc=False` for all h5ai directory listings. The LAN is fast enough that re-fetching is not a burden. Only enable caching for the static root category menu (which never changes).

**Detection:** Newly added files on the h5ai server do not appear in the Kodi listing even after navigating away and back.

**Phase:** Phase 1 — set the correct default in the `endOfDirectory` call pattern.

---

### Pitfall 15: `xbmc.log()` at DEBUG Level Is Silent Without Debug Mode

**What goes wrong:** `xbmc.log("message")` defaults to `xbmc.LOGDEBUG`. Unless the user has enabled debug logging in Kodi settings (or set it in `advancedsettings.xml`), nothing below `LOGINFO` appears in `kodi.log`. Debug output during development is invisible in a standard install.

**Prevention:** Use `LOGINFO` for informational messages that should be visible in normal installs (server connects, navigation events). Reserve `LOGDEBUG` for verbose tracing used only during development. Log errors at `LOGERROR`.

**Detection:** No addon output visible in `kodi.log` despite calls to `xbmc.log()`.

**Phase:** Foundation — establish a logging convention before writing any code.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| addon.xml manifest | Missing `<provides>video</provides>` (Pitfall 4) | Use correct extension point from templates |
| addon.xml manifest | Missing `script.module.requests` import (Pitfall 9) | Declare dependency before first API call |
| URL routing setup | `reuselanguageinvoker` global handle (Pitfall 3) | Read `sys.argv` inside entry function only |
| URL routing setup | `parse_qs` returning lists (Pitfall 12) | Use `parse_qsl` pattern consistently |
| h5ai API client | No timeout on `requests.post` (Pitfall 10) | Always pass `timeout=6` |
| h5ai API client | Path encoding in plugin:// URLs (Pitfall 5) | `urllib.parse.quote(href, safe="")` |
| Directory listing | No `endOfDirectory` on exception (Pitfall 1) | Global try/except wrapper from day one |
| Directory listing | Wrong `setContent` type (Pitfall 7) | Use `"files"` for folders, `"videos"` for file lists |
| Directory listing | `cacheToDisc` serving stale data (Pitfall 14) | `cacheToDisc=False` for all h5ai listings |
| Video playback | IsPlayable/IsFolder mismatch (Pitfall 2) | Direct HTTP URL on ListItem; no two-step resolve needed |
| Search feature | Serial fetches block UI (Pitfall 6) | `ThreadPoolExecutor` with timeout |
| Search feature | Empty query on Escape (Pitfall 13) | Check `kb.isConfirmed()` before `getText()` |
| Logging throughout | Using removed `LOGNOTICE` (Pitfall 8) | Use `LOGINFO`/`LOGWARNING`/`LOGERROR` only |

---

## Sources

- [Kodi Forum — setResolvedUrl vs xbmc.Player().play()](https://forum.kodi.tv/showthread.php?tid=216556)
- [Kodi Forum — Invalid handle -1 error](https://forum.kodi.tv/showthread.php?tid=257787)
- [Kodi Forum — IsPlayable & IsFolder confusion](https://forum.kodi.tv/showthread.php?tid=316042)
- [Kodi Forum — No Python requests module](https://forum.kodi.tv/showthread.php?tid=355131)
- [Kodi Dev Notes (pewpewnotes)](https://pewpewnotes.github.io/KodiAddonDev.html)
- [Addon.xml — Official Kodi Wiki](https://kodi.wiki/view/Addon.xml)
- [xbmcplugin — Kodistubs documentation](https://romanvm.github.io/Kodistubs/_autosummary/xbmcplugin.html)
- [GitHub — reuselanguageinvoker crash issue xbmc/xbmc #21653](https://github.com/xbmc/xbmc/issues/21653)
- [GitHub — LOGNOTICE removal PR xbmc/xbmc #18346](https://github.com/xbmc/xbmc/pull/18346)
- [GitHub — No URL encoding bug jellyfin/jellyfin-kodi #765](https://github.com/jellyfin/jellyfin-kodi/issues/765)
- [Kodi Wiki — Add-on unicode paths](https://kodi.wiki/view/Add-on_unicode_paths)
- [Kodi Wiki — Audio-video add-on tutorial](https://kodi.wiki/view/Audio-video_add-on_tutorial)
- [xbmc.github.io — xbmcplugin endOfDirectory](https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d1/d32/group__python__xbmcplugin.html)
