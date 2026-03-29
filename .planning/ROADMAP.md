# Roadmap: Dhaka Flix Kodi Addon

## Overview

Build a Kodi 21 video addon that browses, navigates, and plays media from Dhaka Flix h5ai LAN file servers. The addon starts with the structural foundation and a complete browse experience, then layers in video playback, and finishes with cross-server search. Each phase delivers a coherent, testable capability before the next begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Browse** - Installable addon with complete folder hierarchy navigation, file metadata display, and error handling
- [ ] **Phase 2: Playback** - Video files play directly in Kodi's built-in player
- [x] **Phase 3: Search** - Users can find media across all servers by name (completed 2026-03-26)

## Phase Details

### Phase 1: Foundation & Browse
**Goal**: Users can install the addon and browse any media category down to individual files with correct icons, sizes, and sort order
**Depends on**: Nothing (first phase)
**Requirements**: INFR-01, INFR-02, INFR-03, INFR-04, BRWS-01, BRWS-02, BRWS-03, BRWS-04, BRWS-05
**Success Criteria** (what must be TRUE):
  1. User installs the addon on Kodi 21 Omega and it appears in Video Add-ons without errors
  2. User opens the addon and sees all 9 media categories listed on the home screen
  3. User navigates into any category and drills down through folder levels to reach individual files
  4. Each item displays an appropriate icon (folder, video, audio, image, archive, document) and non-folder items show their file size
  5. Items are sorted with folders first, then by type, then alphabetically; unreachable servers show a graceful error rather than freezing Kodi
**Plans**: 2 plans
Plans:
- [x] 01-01-PLAN.md — Addon skeleton, server config, h5ai API client
- [x] 01-02-PLAN.md — Home screen categories, folder browse UI, icons, sizes, sorting
**UI hint**: yes

### Phase 2: Playback
**Goal**: Users can play any video file directly in Kodi's built-in player by clicking it in a browse listing
**Depends on**: Phase 1
**Requirements**: PLAY-01, PLAY-02
**Success Criteria** (what must be TRUE):
  1. User clicks a video file in any browse listing and it begins playing in Kodi's native player via its HTTP URL
  2. Folder items navigate into their directory; video items play; no item type causes a black screen or empty listing
**Plans**: 1 plan
Plans:
- [ ] 02-01-PLAN.md — Add IsPlayable property to video, audio, and image file types

### Phase 3: Search
**Goal**: Users can find media across all servers by typing a name, without knowing which server it lives on
**Depends on**: Phase 2
**Requirements**: SRCH-01, SRCH-02, SRCH-03
**Success Criteria** (what must be TRUE):
  1. User sees a "Search" entry on the addon home screen and can type a query via Kodi's keyboard dialog
  2. Search results list matching items from all servers with their source category shown
  3. User can navigate into a search result folder to browse its contents, or click a video result to play it directly
**Plans**:2 plans
Plans:
- [x] 03-01-PLAN.md — Search infrastructure: cache module, settings, search module
- [x] 03-02-PLAN.md — Search UI integration: routes, home entry, context menu

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Browse | 2/2 | Complete | 2026-03-26 |
| 2. Playback | 0/1 | Not started | - |
| 3. Search | 2/2 | Complete    | 2026-03-26 |
