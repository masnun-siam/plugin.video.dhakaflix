# Search Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an addon setting that enables detailed search logging for future troubleshooting without making normal Kodi logs noisy.

**Architecture:** Add a single boolean setting in Kodi settings, expose a tiny helper that reads the setting, and gate all search-specific log lines behind that helper. Keep the logging localized to search entrypoints and h5ai search transport so the toggle only affects search diagnostics.

**Tech Stack:** Python 3, Kodi `xbmcaddon`/`xbmc`, unittest, existing addon routing

---

### Task 1: Add a failing regression test for gated search logging

**Files:**
- Modify: `tests/test_h5ai_search.py`
- Test: `tests/test_h5ai_search.py`

- [ ] **Step 1: Write the failing test**

```python
def test_search_logging_only_writes_when_setting_enabled(self):
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -p 'test_*.py'`
Expected: FAIL because search logging helper/behavior does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def is_search_logging_enabled():
    ...

def log_search_debug(message: str):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s tests -p 'test_*.py'`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_h5ai_search.py lib/search.py
git commit -m "test: cover gated search logging"
```

### Task 2: Add the Kodi setting and wire logging through search flow

**Files:**
- Modify: `resources/settings.xml`
- Modify: `lib/search.py`
- Modify: `lib/h5ai.py`
- Modify: `main.py`
- Test: `tests/test_h5ai_search.py`

- [ ] **Step 1: Add the setting**

```xml
<setting id="search_debug_logging" type="boolean" label="Enable search debug logging" default="false" />
```

- [ ] **Step 2: Add minimal logging helper and instrumentation**

```python
log_search_debug("Global search query='{}'".format(query))
log_search_debug("Searching '{}' in {} (href={})".format(query, server["name"], href))
log_search_debug("Search response for {} returned {} items".format(server["name"], len(results)))
```

- [ ] **Step 3: Add transport-level search failure context**

```python
log_search_debug("POST {} with href={} pattern={!r}".format(api_url, href, pattern))
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `python3 -m unittest discover -s tests -p 'test_*.py'`
Expected: PASS

- [ ] **Step 5: Manual verification notes**

Run search once with setting off, then on, and inspect `~/Library/Logs/kodi.log`.
Expected: no extra search lines when off; query/server/result lines present when on.
