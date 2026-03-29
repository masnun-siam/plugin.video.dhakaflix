"""
Search module for querying media from h5ai servers via the native search API.
All searches are live — no caching.
"""

import xbmc

from lib.config import SERVERS, get_path_from_url
from lib.h5ai import search_directory
from lib.log_utils import log_search_debug


def search_single_server(query: str, server: dict) -> list:
    """
    Search a single server for items matching query using the h5ai search API.

    Args:
        query: Search string.
        server: A server dict from SERVERS (name, url, base_url, api_path).

    Returns:
        List of matching items with source_category set to server name.
    """
    href = get_path_from_url(server["url"], server["base_url"])
    log_search_debug(
        "query='{}' server='{}' href='{}'".format(query, server["name"], href)
    )
    results = search_directory(
        pattern=query,
        href=href,
        base_url=server["base_url"],
        api_path=server["api_path"],
    )
    log_search_debug(
        "server='{}' returned {} results".format(server["name"], len(results))
    )
    for item in results:
        item["source_category"] = server["name"]
    return results


def search_all_servers(query: str) -> list:
    """
    Search all servers for items matching query, merged with relevance ranking.

    Searches each server in SERVERS sequentially. Unreachable servers are skipped.
    Results are ranked: exact name match first, then prefix, then substring.

    Args:
        query: Search string.

    Returns:
        Combined list of matching items sorted by relevance then name.
    """
    query_lower = query.lower().strip()
    all_results = []

    for server in SERVERS:
        log_search_debug(
            "global query='{}' entering server='{}'".format(query, server["name"])
        )
        try:
            results = search_single_server(query, server)
            all_results.extend(results)
        except Exception as e:
            xbmc.log(
                "Dhaka Flix: Error searching {}: {}".format(server["name"], e),
                xbmc.LOGERROR,
            )

    # Relevance ranking: exact=0, prefix=1, substring=2
    for item in all_results:
        name_lower = item.get("name", "").lower().strip()
        if name_lower == query_lower:
            item["_rank"] = 0
        elif name_lower.startswith(query_lower):
            item["_rank"] = 1
        else:
            item["_rank"] = 2

    all_results.sort(key=lambda x: (x["_rank"], x.get("name", "")))

    for item in all_results:
        item.pop("_rank", None)

    xbmc.log(
        "Dhaka Flix: Global search '{}' found {} results".format(
            query, len(all_results)
        ),
        xbmc.LOGINFO,
    )
    log_search_debug(
        "global query='{}' total_results={}".format(query, len(all_results))
    )

    return all_results
