"""
Search module for fetching and filtering series across all servers.
Uses cache for index storage and staleness detection.
"""

import xbmc

from lib import cache
from lib.config import SERVERS, get_path_from_url
from lib.h5ai import fetch_directory


def fetch_all_servers_series() -> list:
    """
    Fetch all series from all servers by iterating over SERVERS.

    Returns:
        List of dicts: {name, path, type, size, url, source_category}
    """
    all_series = []
    total_servers = len(SERVERS)

    xbmc.log(
        "Dhaka Flix: Starting to fetch series from {} servers".format(total_servers),
        xbmc.LOGINFO,
    )

    for idx, server in enumerate(SERVERS):
        server_name = server["name"]
        server_url = server["url"]
        base_url = server["base_url"]
        api_path = server["api_path"]

        xbmc.log(
            "Dhaka Flix: [{}/{}] Fetching {} ({})".format(
                idx + 1, total_servers, server_name, base_url
            ),
            xbmc.LOGINFO,
        )

        # Derive the path portion from the full URL (fetch_directory requires a path, not a URL)
        root_path = get_path_from_url(server_url, base_url)

        try:
            # Level 1: fetch the category root
            root_items = fetch_directory(root_path, base_url, api_path)

            for item in root_items:
                if item.get("type") != "folder":
                    continue

                # Level 2: fetch the subfolder to determine if it is a category group or a series
                sub_path = item.get("path")
                xbmc.log(
                    "Dhaka Flix: [{}/{}] Fetching sub-folder '{}' in {}".format(
                        idx + 1, total_servers, item.get("name"), server_name
                    ),
                    xbmc.LOGINFO,
                )
                try:
                    sub_items = fetch_directory(sub_path, base_url, api_path)
                except Exception as sub_e:
                    xbmc.log(
                        "Dhaka Flix: Error fetching sub-folder '{}' in {}: {}".format(
                            item.get("name"), server_name, sub_e
                        ),
                        xbmc.LOGERROR,
                    )
                    sub_items = []

                sub_folders = [x for x in sub_items if x.get("type") == "folder"]

                if sub_folders:
                    # This root item is a category grouping (e.g. A-L, M-Z, #)
                    # Index its child folders as the actual series/movies
                    for sub_item in sub_folders:
                        series_item = {
                            "name": sub_item.get("name"),
                            "path": sub_item.get("path"),
                            "type": sub_item.get("type"),
                            "size": sub_item.get("size"),
                            "url": sub_item.get("url"),
                            "source_category": server_name,
                        }
                        all_series.append(series_item)
                        xbmc.log(
                            "Dhaka Flix: Found series '{}' (via category '{}') in {}".format(
                                sub_item.get("name"), item.get("name"), server_name
                            ),
                            xbmc.LOGDEBUG,
                        )
                else:
                    # No sub-folders — the root item itself is a direct series/movie folder
                    series_item = {
                        "name": item.get("name"),
                        "path": item.get("path"),
                        "type": item.get("type"),
                        "size": item.get("size"),
                        "url": item.get("url"),
                        "source_category": server_name,
                    }
                    all_series.append(series_item)
                    xbmc.log(
                        "Dhaka Flix: Found series '{}' in {}".format(
                            item.get("name"), server_name
                        ),
                        xbmc.LOGDEBUG,
                    )

        except Exception as e:
            xbmc.log(
                "Dhaka Flix: Error fetching from {}: {}".format(server_name, e),
                xbmc.LOGERROR,
            )
            continue

    xbmc.log(
        "Dhaka Flix: Completed fetching {} series from {} servers".format(
            len(all_series), total_servers
        ),
        xbmc.LOGINFO,
    )

    return all_series


def build_search_index() -> list:
    """
    Build the search index by fetching all series and normalizing for search.

    Returns:
        List of indexed items with search-optimized fields.
    """
    xbmc.log("Dhaka Flix: Building search index...", xbmc.LOGINFO)

    # Fetch all series from all servers
    series_list = fetch_all_servers_series()

    # Normalize series names for search (lowercase, trim)
    index = []
    for item in series_list:
        name = item.get("name", "")
        index_item = {
            "name": name,
            "name_lower": name.lower().strip(),
            "path": item.get("path"),
            "type": item.get("type"),
            "url": item.get("url"),
            "source_category": item.get("source_category"),
        }
        index.append(index_item)

    # Save to cache
    cache.save_cache(index)

    xbmc.log(
        "Dhaka Flix: Built search index with {} items".format(len(index)), xbmc.LOGINFO
    )

    return index


def search_series(query: str) -> list:
    """
    Search for series matching the query.

    If cache is None or stale, builds a new index first.
    Filters by case-insensitive substring match on name_lower.
    Returns matches sorted by relevance (exact match first, then prefix, then substring).

    Args:
        query: Search string.

    Returns:
        List of matching items.
    """
    query_lower = query.lower().strip()

    # Load cache or check staleness
    index = cache.load_cache()

    if index is None or cache.is_cache_stale():
        xbmc.log(
            "Dhaka Flix: Cache is None or stale, building new index...", xbmc.LOGINFO
        )
        index = build_search_index()

    # Filter by query (case-insensitive substring match)
    matches = []
    for item in index:
        name_lower = item.get("name_lower", "")

        # Exact match
        if name_lower == query_lower:
            item["_rank"] = 0
            matches.append(item)
        # Prefix match
        elif name_lower.startswith(query_lower):
            item["_rank"] = 1
            matches.append(item)
        # Substring match
        elif query_lower in name_lower:
            item["_rank"] = 2
            matches.append(item)

    # Sort by relevance (rank first, then by name)
    matches.sort(key=lambda x: (x["_rank"], x.get("name", "")))

    # Remove rank field from results
    for item in matches:
        item.pop("_rank", None)

    xbmc.log(
        "Dhaka Flix: Search '{}' found {} matches".format(query, len(matches)),
        xbmc.LOGDEBUG,
    )

    return matches
