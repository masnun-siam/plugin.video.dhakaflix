# Dhaka Flix Kodi Addon

## What This Is

A Kodi video addon (`plugin.video.dhakaflix`) that lets users browse, search, and play media from the Dhaka Flix h5ai file servers on the local network. It mirrors the functionality of the existing Raycast extension but inside Kodi's native UI, providing a TV-friendly experience for accessing movies, TV series, and anime hosted on the Dhaka Flix LAN servers.

## Core Value

Users can discover and play any media file from the Dhaka Flix servers directly within Kodi without leaving the application.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Browse media servers by category (English Movies, Hindi Movies, TV Series, Anime, etc.)
- [ ] Navigate folder hierarchies within each server
- [ ] Search across all servers for media
- [ ] Play video files directly via HTTP URL in Kodi's built-in player
- [ ] Display file metadata (size, type icons)
- [ ] Sort files sensibly (folders first, then by type and name)

### Out of Scope

- Favorites/bookmarks — keep v1 minimal, add later if needed
- Watch history / resume playback — Kodi handles this natively for played items
- Download support — LAN streaming is fast enough, no need for local copies
- VPN/remote access — extension is LAN-only by design
- Subtitle management — Kodi handles subtitles natively
- User authentication — h5ai servers have no auth

## Context

**Dhaka Flix infrastructure:**
- Multiple h5ai file servers on a local network (172.16.50.x)
- 9 configured media categories across 4 server IPs (.7, .9, .12, .14)
- h5ai API endpoint: `/_h5ai/public/index.php` (POST, `action=get&items[href]=...&items[what]=1`)
- Returns JSON with `items[]` containing `href`, `time`, `size`, `managed`, `fetched`
- Media organized in folder hierarchies (e.g., TV Series → alphabetical category folders → series → seasons → episodes)

**Existing Raycast extension (reference implementation):**
- Located at `../dhaka-flix-extension/`
- TypeScript implementation with h5ai API client, server config, browse/search/player commands
- Search works by fetching all top-level series from category folders across all servers
- File type detection by extension (video, audio, image, archive, document)

**Kodi addon ecosystem:**
- Target: Kodi 21 (Omega)
- Python-based addons using `xbmcplugin`, `xbmcgui`, `xbmcaddon` APIs
- Addon structure: `addon.xml` manifest, Python entry point, resources folder
- URL routing via `sys.argv` parameters

## Constraints

- **Platform**: Kodi 21 (Omega) — Python 3 only
- **Network**: LAN-only (172.16.50.x subnet), no internet required
- **API**: h5ai POST API, no authentication needed
- **Addon ID**: `plugin.video.dhakaflix`
- **Language**: Python 3 (Kodi's embedded interpreter)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Kodi's native player for all media | Kodi already has excellent codec support and subtitle handling | -- Pending |
| Hardcode server configs (matching Raycast extension) | Servers are static LAN infrastructure, no need for dynamic discovery | -- Pending |
| Port h5ai API logic from TypeScript reference | Proven API contract, minimize guesswork | -- Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check -- still the right priority?
3. Audit Out of Scope -- reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-27 after initialization*
