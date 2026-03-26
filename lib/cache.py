"""
Cache module for search index storage and staleness detection.
Uses xbmcvfs for platform-agnostic file operations.
"""

import json
import os

import xbmc
import xbmcaddon
import xbmcvfs


ADDON_ID = "plugin.video.dhakaflix"
CACHE_FILENAME = "search_index.json"


def get_cache_path() -> str:
    """
    Get the path to the search index cache file.
    Creates the addon data directory if it doesn't exist.

    Returns:
        Absolute path to search_index.json in addon data directory.
    """
    # Get addon data directory
    addon_data_dir = xbmcvfs.translatePath(
        "special://profile/addon_data/{}/".format(ADDON_ID)
    )

    # Ensure directory exists (may need recursive parent creation)
    if not xbmcvfs.exists(addon_data_dir):
        # Try to create the directory
        # Note: xbmcvfs.mkdir doesn't support parents, so we check and create
        if not xbmcvfs.exists(addon_data_dir):
            # Try to create - may fail if parent doesn't exist
            try:
                xbmcvfs.mkdir(addon_data_dir)
            except Exception:
                # Directory might already exist or parent doesn't exist
                pass

    return os.path.join(addon_data_dir, CACHE_FILENAME)


def load_cache() -> list | None:
    """
    Load the search index from cache file.

    Returns:
        List of cached items, or None if cache doesn't exist or is invalid.
    """
    cache_path = get_cache_path()

    if not xbmcvfs.exists(cache_path):
        xbmc.log("Dhaka Flix: Cache file does not exist", xbmc.LOGDEBUG)
        return None

    try:
        with xbmcvfs.File(cache_path, "r") as f:
            data = json.load(f)

        xbmc.log(
            "Dhaka Flix: Loaded {} items from cache".format(len(data)), xbmc.LOGDEBUG
        )
        return data

    except json.JSONDecodeError as e:
        xbmc.log("Dhaka Flix: Invalid JSON in cache: {}".format(e), xbmc.LOGERROR)
        return None
    except Exception as e:
        xbmc.log("Dhaka Flix: Error loading cache: {}".format(e), xbmc.LOGERROR)
        return None


def save_cache(data: list) -> None:
    """
    Save the search index to cache file.

    Args:
        data: List of items to cache.
    """
    cache_path = get_cache_path()

    try:
        with xbmcvfs.File(cache_path, "w") as f:
            json.dump(data, f, ensure_ascii=False)

        xbmc.log("Dhaka Flix: Saved {} items to cache".format(len(data)), xbmc.LOGDEBUG)

    except Exception as e:
        xbmc.log("Dhaka Flix: Error saving cache: {}".format(e), xbmc.LOGERROR)


def is_cache_stale() -> bool:
    """
    Check if the cache file is stale based on settings.

    Returns:
        True if cache doesn't exist or age exceeds staleness threshold.
    """
    cache_path = get_cache_path()

    # Check if cache file exists
    if not xbmcvfs.exists(cache_path):
        xbmc.log("Dhaka Flix: Cache doesn't exist, marking as stale", xbmc.LOGDEBUG)
        return True

    # Get staleness threshold from settings (default: 24 hours)
    try:
        addon = xbmcaddon.Addon(ADDON_ID)
        staleness_str = addon.getSetting("cache_staleness_hours")
        staleness_hours = float(staleness_str) if staleness_str else 24.0
    except Exception:
        staleness_hours = 24.0

    # Get file modification time
    try:
        stat_result = xbmcvfs.Stat(cache_path)
        mtime = stat_result.st_mtime()

        # Calculate age in seconds
        import time

        age_seconds = time.time() - mtime
        staleness_seconds = staleness_hours * 3600

        is_stale = age_seconds > staleness_seconds

        xbmc.log(
            "Dhaka Flix: Cache age = {:.1f} hours, threshold = {} hours, stale = {}".format(
                age_seconds / 3600, staleness_hours, is_stale
            ),
            xbmc.LOGDEBUG,
        )

        return is_stale

    except Exception as e:
        xbmc.log(
            "Dhaka Flix: Error checking cache staleness: {}".format(e), xbmc.LOGERROR
        )
        # If we can't check, assume stale
        return True
