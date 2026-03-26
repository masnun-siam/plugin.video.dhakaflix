# Architecture Patterns

**Domain:** Kodi video addon (plugin.video.*) — file-browser style, HTTP directory listing backend
**Researched:** 2026-03-27
**Overall confidence:** HIGH (Kodi patterns from official docs + reference code; h5ai API from working implementation)

---

## Recommended Architecture

A Kodi plugin.video addon is a stateless Python script invoked repeatedly by Kodi, once per "page" the user navigates to. Each invocation receives a plugin:// URL via `sys.argv`, renders a directory listing or triggers playback, then exits. There is no long-running process.

```
plugin://plugin.video.dhakaflix/          → list all 9 categories (home screen)
plugin://plugin.video.dhakaflix/?action=browse&server_id=0&path=/DHAKA-FLIX-7/English%20Movies/
                                          → list folder contents from h5ai
plugin://plugin.video.dhakaflix/?action=browse&server_id=0&path=/DHAKA-FLIX-7/English%20Movies/Avengers/
                                          → one level deeper
plugin://plugin.video.dhakaflix/?action=play&url=http%3A%2F%2F172.16.50.7%2F...%2Fmovie.mkv
                                          → resolve to playable URL
plugin://plugin.video.dhakaflix/?action=search
                                          → show search dialog, list results
```

### Invocation Model

```
Kodi (user navigates / plays)
  └─> Python runtime: python3 main.py
        sys.argv[0] = "plugin://plugin.video.dhakaflix/"
        sys.argv[1] = <handle int>          ← addon_handle for xbmcplugin calls
        sys.argv[2] = "?action=browse&..."  ← query string with routing params
```

---

## File Layout

```
plugin.video.dhakaflix/
├── addon.xml                  ← manifest: ID, version, deps, extension point
├── main.py                    ← entry point, router, view renderers
├── resources/
│   ├── settings.xml           ← user-configurable settings (optional for v1)
│   └── images/
│       ├── icon.png           ← 256x256, required by Kodi repo
│       └── fanart.jpg         ← 1280x720 or 1920x1080, optional
└── lib/
    ├── h5ai.py                ← h5ai API client (port from TypeScript)
    └── config.py              ← server definitions (port from config.ts)
```

**Why `lib/` not inlined:** Keeps main.py to routing + view logic only; h5ai and config are independently testable; mirrors how well-structured Kodi addons separate API from presentation.

---

## Component Boundaries

| Component | File | Responsibility | Communicates With |
|-----------|------|---------------|-------------------|
| Entry Point / Router | `main.py` | Parse sys.argv, dispatch to correct view function, call xbmcplugin/xbmcgui APIs | h5ai client, config, Kodi API |
| h5ai API Client | `lib/h5ai.py` | POST to `/_h5ai/public/index.php`, parse JSON, return MediaItem list | HTTP (urllib), no Kodi API |
| Server Config | `lib/config.py` | Static list of 9 servers with name/url/baseUrl/apiPath | Read-only by router + h5ai client |
| Kodi UI Layer | `main.py` view functions | Build ListItem objects, call addDirectoryItem / endOfDirectory / setResolvedUrl | Kodi xbmcplugin, xbmcgui modules |
| addon.xml | `addon.xml` | Declare plugin ID, Python version, extension point, dependencies | Read by Kodi at install time |

**Key boundary rule:** `lib/h5ai.py` must never import xbmc* modules. It is pure Python. The router in `main.py` owns all Kodi API calls.

---

## Data Flow

### Browse flow

```
User clicks category or folder
  → Kodi calls main.py with ?action=browse&server_id=N&path=/some/path/
  → router() parses params
  → h5ai.fetch_directory(path, baseUrl, apiPath)
      → urllib POST to http://172.16.50.x/_h5ai/public/index.php
        body: action=get&items[href]=/some/path/&items[what]=1
      → parse JSON: { items: [{href, time, size, managed, fetched}] }
      → filter to direct children only (no nested paths)
      → classify file type by extension
      → sort: folders first, then by type, then natural name sort
      → return list[MediaItem]
  → view_browse() iterates MediaItem list
      → for folders: xbmcgui.ListItem(name) + addDirectoryItem(isFolder=True, url=next_plugin_url)
      → for videos:  xbmcgui.ListItem(name) + addDirectoryItem(isFolder=False, url=play_plugin_url)
  → xbmcplugin.endOfDirectory(handle)
  → Kodi renders the list
```

### Playback flow

```
User clicks a video file
  → Kodi calls main.py with ?action=play&url=http://172.16.50.x/path/to/movie.mkv
  → router() parses params
  → play_video(url):
      → listitem = xbmcgui.ListItem(path=url)
      → xbmcplugin.setResolvedUrl(handle, succeeded=True, listitem=listitem)
  → Kodi passes HTTP URL to built-in player
  → Player streams directly from LAN server
```

### Search flow

```
User selects Search from home screen
  → Kodi calls main.py with ?action=search
  → show_search():
      → xbmcgui.Dialog().input("Search") → query string
      → for each server: h5ai.fetch_all_top_level(server)
          → fetch root folder → get category subfolders → fetch each category
          → collect all direct children (series/movie folders) from every category
      → filter results where name contains query (case-insensitive)
      → render as browse listing (folders link into ?action=browse)
  → xbmcplugin.endOfDirectory(handle)
```

---

## addon.xml Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<addon id="plugin.video.dhakaflix"
       name="Dhaka Flix"
       version="1.0.0"
       provider-name="your-name">

  <requires>
    <import addon="xbmc.python" version="3.0.1"/>
  </requires>

  <extension point="xbmc.python.pluginsource" library="main.py">
    <provides>video</provides>
  </extension>

  <extension point="xbmc.addon.metadata">
    <summary lang="en_GB">Browse and play Dhaka Flix LAN media servers</summary>
    <description lang="en_GB">...</description>
    <platform>all</platform>
  </extension>

</addon>
```

Key fields:
- `xbmc.python` version `3.0.1` — correct for Kodi 21 Omega (Python 3)
- `xbmc.python.pluginsource` with `<provides>video</provides>` — marks this as a video plugin, appears under Video Add-ons
- `library="main.py"` — the Python file Kodi executes

---

## URL Routing Pattern

The recommended pattern for this addon is manual query-string parsing (no third-party routing library). The addon is simple enough (4 actions) that the routing library `script.module.routing` would add a dependency without meaningful benefit.

```python
# main.py

import sys
from urllib.parse import parse_qsl, urlencode

PLUGIN_URL = sys.argv[0]          # "plugin://plugin.video.dhakaflix/"
ADDON_HANDLE = int(sys.argv[1])   # int handle for xbmcplugin calls
PARAMS = dict(parse_qsl(sys.argv[2][1:]))  # strip leading '?', parse

def build_url(**kwargs) -> str:
    return PLUGIN_URL + '?' + urlencode(kwargs)

def router():
    action = PARAMS.get('action')
    if action is None:
        list_categories()
    elif action == 'browse':
        browse_folder(PARAMS['server_id'], PARAMS['path'])
    elif action == 'play':
        play_video(PARAMS['url'])
    elif action == 'search':
        show_search()

if __name__ == '__main__':
    router()
```

---

## Key API Decisions (Kodi 21 Omega)

### ListItem metadata — use InfoTagVideo, not setInfo()

`ListItem.setInfo('video', {...})` is deprecated as of Kodi 20 and will generate log warnings. For Kodi 21, use:

```python
li = xbmcgui.ListItem(name)
tag = li.getVideoInfoTag()
tag.setTitle(name)
tag.setMediaType('video')    # or 'movie', 'tvshow', 'episode'
```

For a file browser addon where metadata is minimal (just name + size), `setTitle` and `setMediaType` are sufficient. Do not try to scrape TMDB/IMDB metadata in v1.

### Content type

Set `xbmcplugin.setContent(ADDON_HANDLE, 'files')` for generic folder listings. Use `'movies'` only if all items in the listing are known movies (e.g., browsing the English Movies root). This affects how Kodi applies skins and sort options.

### Sort methods

Call `xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)` to let Kodi sort by label client-side. The h5ai client already pre-sorts (folders first, natural name), so Kodi's default will match.

### HTTP requests — use urllib, not requests

Kodi's embedded Python 3 interpreter does not include `requests`. Use `urllib.request` for the h5ai POST. This is a hard constraint.

```python
import urllib.request
import urllib.parse

data = urllib.parse.urlencode({
    'action': 'get',
    'items[href]': path,
    'items[what]': '1'
}).encode('utf-8')

req = urllib.request.Request(api_url, data=data,
      headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read().decode('utf-8'))
```

---

## h5ai API Contract (from reference implementation)

**Endpoint:** `POST http://{baseUrl}/_h5ai/public/index.php`

**Request body (form-encoded):**
```
action=get&items[href]=/DHAKA-FLIX-7/English%20Movies/&items[what]=1
```

**Response:**
```json
{
  "items": [
    {
      "href": "/DHAKA-FLIX-7/English%20Movies/",
      "time": 1707500000,
      "size": null,
      "managed": true,
      "fetched": true
    },
    {
      "href": "/DHAKA-FLIX-7/English%20Movies/Avengers (2012)/",
      "time": 1707400000,
      "size": null,
      "managed": false,
      "fetched": false
    }
  ]
}
```

**Direct-children-only filter (critical):** The response includes the requested directory itself as the first item and may include items at arbitrary depths if not filtered. Filter rule: relative path from requested path must have exactly one non-empty segment when split on `/`.

**File classification by extension:**
- video: mkv, mp4, avi, mov, wmv, flv, webm, m4v
- image: jpg, jpeg, png, gif, bmp, webp, svg
- audio: mp3, wav, flac, aac, ogg, m4a
- archive: zip, rar, 7z, tar, gz, iso
- document: pdf, doc, docx, txt, md, nfo, srt
- folder: href ends with `/`

---

## Server Configuration (9 servers, 4 IPs)

```python
# lib/config.py
SERVERS = [
    {"name": "English Movies",              "base_url": "http://172.16.50.7",
     "path": "/DHAKA-FLIX-7/English%20Movies/",            "api_path": "/_h5ai/public/index.php"},
    {"name": "Hindi Movies",                "base_url": "http://172.16.50.14",
     "path": "/DHAKA-FLIX-14/Hindi%20Movies/",             "api_path": "/_h5ai/public/index.php"},
    {"name": "South Movies Hindi Dubbed",   "base_url": "http://172.16.50.14",
     "path": "/DHAKA-FLIX-14/SOUTH%20INDIAN%20MOVIES/Hindi%20Dubbed/", "api_path": "/_h5ai/public/index.php"},
    {"name": "Kolkata Bangla Movies",       "base_url": "http://172.16.50.7",
     "path": "/DHAKA-FLIX-7/Kolkata%20Bangla%20Movies/",   "api_path": "/_h5ai/public/index.php"},
    {"name": "Animation Movies",            "base_url": "http://172.16.50.14",
     "path": "/DHAKA-FLIX-14/Animation%20Movies/",         "api_path": "/_h5ai/public/index.php"},
    {"name": "Foreign Language Movies",     "base_url": "http://172.16.50.7",
     "path": "/DHAKA-FLIX-7/Foreign%20Language%20Movies/", "api_path": "/_h5ai/public/index.php"},
    {"name": "TV Series",                   "base_url": "http://172.16.50.12",
     "path": "/DHAKA-FLIX-12/TV-WEB-Series/",              "api_path": "/_h5ai/public/index.php"},
    {"name": "Korean TV and Web Series",    "base_url": "http://172.16.50.14",
     "path": "/DHAKA-FLIX-14/KOREAN%20TV%20%26%20WEB%20Series/", "api_path": "/_h5ai/public/index.php"},
    {"name": "Anime",                       "base_url": "http://172.16.50.9",
     "path": "/DHAKA-FLIX-9/Anime%20%26%20Cartoon%20TV%20Series/", "api_path": "/_h5ai/public/index.php"},
]
```

`server_id` passed in plugin URLs is the index into this list. The path stored in the URL is the h5ai `href` path (not the full URL).

---

## Suggested Build Order

Components have clear dependencies. Build bottom-up:

```
1. lib/config.py        — no deps, pure data
        ↓
2. lib/h5ai.py          — depends on config shapes; pure Python + urllib
        ↓
3. addon.xml            — no code deps; required to install/test in Kodi
        ↓
4. main.py (browse)     — depends on h5ai + config + Kodi APIs; list categories → browse folder
        ↓
5. main.py (playback)   — small addition: parse play action, call setResolvedUrl
        ↓
6. main.py (search)     — depends on browse working; adds Dialog input + multi-server fetch
        ↓
7. resources/           — icon.png, fanart.jpg last; not needed for functional testing
```

**Rationale for this order:**
- h5ai client can be tested standalone (just Python + LAN access) before touching Kodi APIs
- Browse must work before search (search reuses browse listing rendering)
- Playback is a one-function addition after browse, not a separate phase
- Assets (icon/fanart) are cosmetic; defer until everything works

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Long-running HTTP fetches blocking the UI thread
**What goes wrong:** Kodi's plugin runner is synchronous. If `fetchDirectory` takes >5s, Kodi shows a spinner but cannot be cancelled cleanly.
**Prevention:** Set a timeout on `urlopen` (10s). For search's multi-server bulk fetch, add a `xbmc.Monitor().waitForAbort()` check between server iterations.

### Anti-Pattern 2: Storing state between invocations in module globals
**What goes wrong:** Each Kodi plugin call spawns a fresh interpreter. Module-level variables do not persist between navigations. Any "cache" stored in a Python variable is silently lost.
**Prevention:** Use `xbmcaddon.Addon().setSetting()` or write to a file in `xbmc.translatePath('special://temp/')` for any state that must persist.

### Anti-Pattern 3: Using `requests` or any non-stdlib HTTP library
**What goes wrong:** Kodi's embedded Python 3 does not include pip-installed packages. The addon will crash with `ModuleNotFoundError`.
**Prevention:** Use only `urllib.request` for HTTP. All needed functionality (POST, headers, timeout) is available in stdlib.

### Anti-Pattern 4: Calling `setInfo('video', {...})` on Kodi 21
**What goes wrong:** Generates deprecation warnings that flood the Kodi log; may break in a future release.
**Prevention:** Use `listitem.getVideoInfoTag()` setters as documented above.

### Anti-Pattern 5: Passing full HTTP URLs as `server_id` in plugin URLs
**What goes wrong:** Plugin URLs have a length limit and special characters in HTTP URLs require double-encoding, leading to parsing bugs.
**Prevention:** Pass `server_id` (int index) + `path` (h5ai href, already URL-safe) as separate parameters. Reconstruct full URL in Python from the config list.

---

## Scalability Considerations

This is a LAN-only addon. The concern is not internet scale but LAN responsiveness:

| Concern | At normal use | Mitigation |
|---------|--------------|------------|
| Directory listing latency | h5ai responds in ~100-500ms on LAN | Kodi shows a loading spinner; acceptable |
| Search bulk fetch (9 servers, 2 levels deep) | ~18-27 HTTP requests | Fetch sequentially per server to avoid OOM; reference impl uses chunks of 5 |
| Large folder with 200+ items | Kodi handles natively | No pagination needed; xbmcplugin handles large lists |
| Concurrent playback | Single user, Kodi streams directly | No addon involvement after setResolvedUrl |

---

## Sources

- [Official Kodi Wiki: HOW-TO:Video addon](https://kodi.wiki/view/HOW-TO:Video_addon) — canonical addon tutorial
- [Official Kodi Wiki: Add-on structure](https://kodi.wiki/view/Add-on_structure) — file layout, resources/, addon.xml
- [Official Kodi Wiki: Addon.xml](https://kodi.wiki/view/Addon.xml) — manifest schema
- [Kodistubs: xbmcplugin](https://romanvm.github.io/Kodistubs/_autosummary/xbmcplugin.html) — addDirectoryItem, endOfDirectory, setResolvedUrl, setContent, addSortMethod signatures (HIGH confidence)
- [romanvm/plugin.video.example](https://github.com/romanvm/plugin.video.example) — reference minimal video addon (Kodi 20+, Python 3); 3-tier browse/play architecture (HIGH confidence)
- [kodi-plugin-routing README](https://github.com/tamland/kodi-plugin-routing) — alternative decorator-based routing; not recommended for this addon due to external dependency overhead
- [ListItem.setInfo() deprecation discussion](https://forum.kodi.tv/showthread.php?tid=369255) — confirms InfoTagVideo setters are correct for Kodi 20+ (MEDIUM confidence)
- Raycast reference implementation at `../dhaka-flix-extension/` — exact h5ai API contract, server config, file classification, sort order (HIGH confidence — working code)
