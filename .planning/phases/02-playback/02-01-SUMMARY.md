---
plan: 02-01
phase: 02-playback
status: complete
completed: 2026-03-27
---

## Summary

**What was built:** Added IsPlayable property to playable file types (video, audio, image) in the browse listing, enabling users to click and play media files in Kodi's native player.

**How it works:** 
- Added `PLAYABLE_TYPES = {"video", "audio", "image"}` constant at module level
- Modified the `browse()` function's non-folder branch to set `IsPlayable='true'` property on ListItem for playable types
- Archive, document, and other file types remain non-clickable (no IsPlayable property)

**Artifacts created/modified:**
| File | Change |
|------|--------|
| main.py | Added PLAYABLE_TYPES constant + IsPlayable property logic |

## Tasks Executed

| # | Task | Status |
|---|------|--------|
| 1 | Add IsPlayable property to playable file types | ✓ Complete |

## Decisions

- Used setProperty('IsPlayable', 'true') - the standard Kodi pattern for playable items
- Kept direct URL approach - the URL from h5ai is already a complete HTTP URL
- Non-playable types (archive, document, other) intentionally lack IsPlayable to prevent accidental clicks

## Verification

**Automated checks (all passed):**
- `grep "PLAYABLE_TYPES" main.py` → 1 match (definition)
- `grep -E "setProperty.*IsPlayable" main.py` → 1 match (property setting)

**Manual verification:**
- Install addon in Kodi 21
- Browse to a folder with video files
- Click a video file - should play in Kodi's native player
- Click an archive file - should do nothing (non-clickable)

## Issues

None.

---
