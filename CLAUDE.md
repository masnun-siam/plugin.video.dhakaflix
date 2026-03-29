<!-- GSD:project-start source:PROJECT.md -->
## Project

**Dhaka Flix Kodi Addon**

A Kodi video addon (`plugin.video.dhakaflix`) that lets users browse, search, and play media from the Dhaka Flix h5ai file servers on the local network. It mirrors the functionality of the existing Raycast extension but inside Kodi's native UI, providing a TV-friendly experience for accessing movies, TV series, and anime hosted on the Dhaka Flix LAN servers.

**Core Value:** Users can discover and play any media file from the Dhaka Flix servers directly within Kodi without leaving the application.

### Constraints

- **Platform**: Kodi 21 (Omega) — Python 3 only
- **Network**: LAN-only (172.16.50.x subnet), no internet required
- **API**: h5ai POST API, no authentication needed
- **Addon ID**: `plugin.video.dhakaflix`
- **Language**: Python 3 (Kodi's embedded interpreter)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Kodi API Layer (built-in, no install required)
| Module | Purpose | Notes |
|--------|---------|-------|
| `xbmcplugin` | Directory listings, content type, sort methods, playback resolution | Core plugin API — `addDirectoryItem`, `endOfDirectory`, `setContent`, `setResolvedUrl` |
| `xbmcgui` | ListItem creation, artwork, video metadata via `InfoTag` | `getVideoInfoTag()` is the current (Kodi 20+) approach — do NOT use the deprecated `setInfo()` dict-based API |
| `xbmcaddon` | Read addon settings, get addon info (id, path, version) | Used at startup to fetch addon handle metadata |
| `xbmcvfs` | Path translation (`translatePath`) for data/profile dirs | Do NOT use for HTTP — xbmcvfs.File() with http URLs was broken intentionally in Kodi 19+ |
### URL Routing
| Library | Version | Addon ID | Purpose | Why |
|---------|---------|----------|---------|-----|
| `script.module.routing` | 0.2.3+matrix.1 | `script.module.routing` | URL-based function dispatch via decorator (`@plugin.route('/')`) | Eliminates manual `sys.argv` parsing; official Kodi repo package; works cleanly with folder-path routes including slashes via `<path:segment>` |
### HTTP Client
| Approach | When to Use | Why |
|----------|------------|-----|
| Python stdlib `urllib.request` + `urllib.parse` + `json` | This project (h5ai POST API) | No external dependency needed. The h5ai API is a single POST endpoint returning JSON. Python 3's stdlib handles this cleanly. No auth, no TLS cert complexity (LAN). |
| `script.module.requests` | Only if HTTP complexity grows | `requests` is in the Omega repo but adds a Kodi module dependency for something stdlib handles fine. Overhead not justified for one LAN endpoint. |
### Development Tooling (not bundled with addon)
| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| `Kodistubs` | Latest (aligns with Kodi target version) | IDE autocomplete and type hints for all `xbmc*` modules | `pip install Kodistubs` in venv |
| `pytest` | Latest stable | Unit testing helper functions (h5ai parser, URL builder, sort logic) | `pip install pytest` |
| `kodi-addon-checker` | Latest | Validates addon.xml structure and repo submission requirements | `pip install kodi-addon-checker` |
## Addon Structure
## addon.xml Template
- `xbmc.python` version `3.0.1` is correct for Kodi 21 Omega (confirmed from Fossies/forum sources).
- `<provides>video</provides>` makes the addon appear in the Video Add-ons category.
- `library="main.py"` — this file must exist at the addon root.
## Python Version
- Any Python 2 syntax or `kodi_six` compatibility shims (Python 2 support ended at Kodi 18)
- f-strings beyond 3.6 syntax edge cases (wide compatibility)
- Type hints in runtime paths (stubs are dev-only, Kodi's interpreter may be 3.8)
## Alternatives Considered
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Routing | `script.module.routing` | Manual `sys.argv` / `urllib.parse` dispatch | Manual approach produces spaghetti switch/if logic at 5+ routes |
| Routing | `script.module.routing` | `script.module.kodiutils` or `xbmcswift2` | `xbmcswift2` is unmaintained/abandoned; `script.module.routing` is the Omega official repo package |
| HTTP | `urllib.request` (stdlib) | `script.module.requests` | One LAN POST endpoint does not justify an addon dependency on requests |
| HTTP | `urllib.request` (stdlib) | `xbmcvfs.File()` with HTTP URL | Explicitly broken since Kodi 19 for HTTP/S URLs |
| IDE support | `Kodistubs` | `kodi.emulator.ascii` (retrospect) | Kodistubs is lighter and officially recommended; emulator is heavy and retrospect-specific |
## What NOT to Use
- **`setInfo()` dict API** — deprecated in Kodi 20, removed behavior in 21. Use `getVideoInfoTag()` methods instead (`setTitle()`, `setPlot()`, etc.).
- **`xbmcswift2`** — abandoned Python 2 wrapper, not in Omega repo, causes import errors on Kodi 19+.
- **`requests` as a vendored copy** — bundling third-party libraries inside the addon zip is against Kodi repo policy and causes version conflicts.
- **`os.path` for Kodi paths** — use `xbmcvfs.translatePath('special://userdata/...')` instead.
- **Global mutable state** — Kodi may invoke the addon entry point multiple times in a session; avoid module-level side effects beyond constants.
## Installation Reference
# Dev environment only (IDE support + testing)
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **plugin.video.dhakaflix** (108 symbols, 224 relationships, 20 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/plugin.video.dhakaflix/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/plugin.video.dhakaflix/context` | Codebase overview, check index freshness |
| `gitnexus://repo/plugin.video.dhakaflix/clusters` | All functional areas |
| `gitnexus://repo/plugin.video.dhakaflix/processes` | All execution flows |
| `gitnexus://repo/plugin.video.dhakaflix/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
