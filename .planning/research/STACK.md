# Technology Stack

**Project:** plugin.video.dhakaflix
**Researched:** 2026-03-27
**Research mode:** Ecosystem

---

## Recommended Stack

### Kodi API Layer (built-in, no install required)

| Module | Purpose | Notes |
|--------|---------|-------|
| `xbmcplugin` | Directory listings, content type, sort methods, playback resolution | Core plugin API — `addDirectoryItem`, `endOfDirectory`, `setContent`, `setResolvedUrl` |
| `xbmcgui` | ListItem creation, artwork, video metadata via `InfoTag` | `getVideoInfoTag()` is the current (Kodi 20+) approach — do NOT use the deprecated `setInfo()` dict-based API |
| `xbmcaddon` | Read addon settings, get addon info (id, path, version) | Used at startup to fetch addon handle metadata |
| `xbmcvfs` | Path translation (`translatePath`) for data/profile dirs | Do NOT use for HTTP — xbmcvfs.File() with http URLs was broken intentionally in Kodi 19+ |

**Confidence:** HIGH — Kodi official API docs confirm these modules, verified against romanvm/plugin.video.example and Kodistubs.

### URL Routing

| Library | Version | Addon ID | Purpose | Why |
|---------|---------|----------|---------|-----|
| `script.module.routing` | 0.2.3+matrix.1 | `script.module.routing` | URL-based function dispatch via decorator (`@plugin.route('/')`) | Eliminates manual `sys.argv` parsing; official Kodi repo package; works cleanly with folder-path routes including slashes via `<path:segment>` |

Declare in `addon.xml` as:
```xml
<import addon="script.module.routing" version="0.2.3"/>
```

**Confidence:** MEDIUM — Version 0.2.3+matrix.1 confirmed in Kodi Omega official repository (kodi.tv/addons/omega/script.module.routing/). The `+matrix.1` suffix is a packaging label, not a breaking change.

**Why not roll your own routing:** `sys.argv[2]` URL parsing via `urllib.parse.parse_qsl` works but becomes messy once you have 5+ routes. The routing module's decorator pattern is the community standard for any addon beyond trivial complexity.

### HTTP Client

| Approach | When to Use | Why |
|----------|------------|-----|
| Python stdlib `urllib.request` + `urllib.parse` + `json` | This project (h5ai POST API) | No external dependency needed. The h5ai API is a single POST endpoint returning JSON. Python 3's stdlib handles this cleanly. No auth, no TLS cert complexity (LAN). |
| `script.module.requests` | Only if HTTP complexity grows | `requests` is in the Omega repo but adds a Kodi module dependency for something stdlib handles fine. Overhead not justified for one LAN endpoint. |

**For this project:** use `urllib.request.urlopen` with a `urllib.request.Request` object for the POST body. Parse response with `json.loads`. Zero addon dependencies needed.

**Confidence:** HIGH — Python 3 stdlib, no uncertainty. Confirmed xbmcvfs cannot be used for HTTP.

### Development Tooling (not bundled with addon)

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| `Kodistubs` | Latest (aligns with Kodi target version) | IDE autocomplete and type hints for all `xbmc*` modules | `pip install Kodistubs` in venv |
| `pytest` | Latest stable | Unit testing helper functions (h5ai parser, URL builder, sort logic) | `pip install pytest` |
| `kodi-addon-checker` | Latest | Validates addon.xml structure and repo submission requirements | `pip install kodi-addon-checker` |

Kodistubs are stubs only — they do not execute. They enable PyCharm/VSCode to understand `xbmcgui.ListItem`, `xbmcplugin.addDirectoryItem`, etc. without Kodi running.

**Confidence:** MEDIUM — Kodistubs is the official recommendation from the Kodi wiki and the creator of the example plugin. kodi-addon-checker is maintained by Team Kodi.

---

## Addon Structure

Standard layout for a Kodi 21 Omega video plugin:

```
plugin.video.dhakaflix/
├── addon.xml               # Manifest (required)
├── main.py                 # Entry point (name referenced in addon.xml library= attribute)
├── resources/
│   ├── language/
│   │   └── resource.language.en_gb/
│   │       └── strings.po  # Localisation strings (optional but conventional)
│   ├── images/
│   │   ├── icon.png        # 256x256
│   │   └── fanart.jpg      # 1920x1080
│   └── settings.xml        # Addon settings UI (optional)
└── lib/                    # Internal Python modules
    ├── h5ai.py             # h5ai API client
    ├── servers.py          # Server/category config
    └── router.py           # Route handlers (if splitting main.py)
```

---

## addon.xml Template

Minimum viable `addon.xml` for Kodi 21 Omega:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<addon id="plugin.video.dhakaflix"
       version="1.0.0"
       name="Dhaka Flix"
       provider-name="siam">
  <requires>
    <import addon="xbmc.python" version="3.0.1"/>
    <import addon="script.module.routing" version="0.2.3"/>
  </requires>
  <extension point="xbmc.python.pluginsource" library="main.py">
    <provides>video</provides>
  </extension>
  <extension point="xbmc.addon.metadata">
    <summary lang="en_gb">Browse and play Dhaka Flix media servers</summary>
    <description lang="en_gb">Browse h5ai file servers on the Dhaka Flix LAN and play movies, TV series, and anime directly in Kodi.</description>
    <license>GPL-2.0-only</license>
    <platform>all</platform>
    <news>Initial release</news>
  </extension>
</addon>
```

Key points:
- `xbmc.python` version `3.0.1` is correct for Kodi 21 Omega (confirmed from Fossies/forum sources).
- `<provides>video</provides>` makes the addon appear in the Video Add-ons category.
- `library="main.py"` — this file must exist at the addon root.

**Confidence:** MEDIUM — Structure confirmed from official docs and example addons. xbmc.python 3.0.1 version confirmed for Omega 21 via forum/fossies sources, not directly from kodi.wiki (wiki pages returned empty during fetch).

---

## Python Version

Kodi 21 Omega embeds Python 3. Kodi added Python 3.12 build support in the Omega cycle. The embedded interpreter is managed by Kodi — you do not install or configure it. Write Python 3.8+ compatible code and it will run on any Kodi 21 installation.

**Do not use:**
- Any Python 2 syntax or `kodi_six` compatibility shims (Python 2 support ended at Kodi 18)
- f-strings beyond 3.6 syntax edge cases (wide compatibility)
- Type hints in runtime paths (stubs are dev-only, Kodi's interpreter may be 3.8)

**Confidence:** MEDIUM — Python 3.12 build support confirmed in Kodi changelogs. Exact minimum Python version of the embedded interpreter on all platforms is not stated in official docs.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Routing | `script.module.routing` | Manual `sys.argv` / `urllib.parse` dispatch | Manual approach produces spaghetti switch/if logic at 5+ routes |
| Routing | `script.module.routing` | `script.module.kodiutils` or `xbmcswift2` | `xbmcswift2` is unmaintained/abandoned; `script.module.routing` is the Omega official repo package |
| HTTP | `urllib.request` (stdlib) | `script.module.requests` | One LAN POST endpoint does not justify an addon dependency on requests |
| HTTP | `urllib.request` (stdlib) | `xbmcvfs.File()` with HTTP URL | Explicitly broken since Kodi 19 for HTTP/S URLs |
| IDE support | `Kodistubs` | `kodi.emulator.ascii` (retrospect) | Kodistubs is lighter and officially recommended; emulator is heavy and retrospect-specific |

---

## What NOT to Use

- **`setInfo()` dict API** — deprecated in Kodi 20, removed behavior in 21. Use `getVideoInfoTag()` methods instead (`setTitle()`, `setPlot()`, etc.).
- **`xbmcswift2`** — abandoned Python 2 wrapper, not in Omega repo, causes import errors on Kodi 19+.
- **`requests` as a vendored copy** — bundling third-party libraries inside the addon zip is against Kodi repo policy and causes version conflicts.
- **`os.path` for Kodi paths** — use `xbmcvfs.translatePath('special://userdata/...')` instead.
- **Global mutable state** — Kodi may invoke the addon entry point multiple times in a session; avoid module-level side effects beyond constants.

---

## Installation Reference

For the addon itself (no pip install — Kodi addons are zip-installed):

```bash
# Dev environment only (IDE support + testing)
python -m venv .venv
source .venv/bin/activate
pip install Kodistubs pytest kodi-addon-checker
```

Kodi dependencies (`script.module.routing`) are resolved automatically by Kodi when the addon is installed from a repo or zip that declares them in `addon.xml`.

---

## Sources

- Kodi official addon page for script.module.routing (Omega): https://kodi.tv/addons/omega/script.module.routing/
- Kodistubs GitHub (romanvm): https://github.com/romanvm/Kodistubs
- Example video plugin (romanvm): https://github.com/romanvm/plugin.video.example
- kodi-plugin-routing GitHub (tamland): https://github.com/tamland/kodi-plugin-routing
- Kodi Python migration guide: https://kodi.wiki/view/General_information_about_migration_to_Python_3
- Addon.xml wiki: https://kodi.wiki/view/Addon.xml
- xbmcplugin API docs: https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d1/d32/group__python__xbmcplugin.html
- xbmcgui API docs: https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python__xbmcgui.html
- kodi-addon-checker PyPI: https://pypi.org/project/kodi-addon-checker/
- Audio-video addon tutorial (Kodi wiki): https://kodi.wiki/view/Audio-video_add-on_tutorial
