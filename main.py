import routing
import urllib.parse
import xbmcaddon
import xbmcgui
import xbmcplugin

from lib.config import SERVERS, get_path_from_url
from lib.h5ai import fetch_directory, sort_items
from lib.search import search_single_server, search_all_servers

plugin = routing.Plugin()

# Icon mapping per file type (D-04)
ICON_MAP = {
    "folder": "DefaultFolder.png",
    "video": "DefaultVideo.png",
    "audio": "DefaultAudio.png",
    "image": "DefaultPicture.png",
    "archive": "DefaultFile.png",
    "document": "DefaultFile.png",
    "other": "DefaultFile.png",
}

# Playable file types for IsPlayable property (D-02)
PLAYABLE_TYPES = {"video", "audio", "image"}


@plugin.route("/")
def index():
    """Home screen: list all 9 media categories plus Search."""
    xbmcplugin.setContent(plugin.handle, "files")
    for i, server in enumerate(SERVERS):
        li = xbmcgui.ListItem(server["name"])
        li.setArt({"icon": "DefaultFolder.png"})
        path = get_path_from_url(server["url"], server["base_url"]).lstrip("/")
        url = plugin.url_for(browse, server_index=str(i), path=path)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=True)

    # Add Search entry per D-01
    search_item = xbmcgui.ListItem("Search")
    search_item.setArt({"icon": "DefaultFolder.png"})
    search_url = plugin.url_for(search)
    xbmcplugin.addDirectoryItem(plugin.handle, search_url, search_item, isFolder=True)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/browse/<path:path>")
def browse(path):
    """Browse folder contents with icons, file sizes, and sorting."""
    # server_index is passed as a query parameter because the routing module's
    # regex can't handle <normal_param> followed by <path:param> in one pattern.
    server_index = plugin.args.get("server_index", ["0"])[0]
    server = SERVERS[int(server_index)]
    base_url = server["base_url"]
    api_path = server["api_path"]

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Routing strips trailing slash and preserves percent-encoding.
    # Decode and restore trailing slash for h5ai directory lookups.
    path = urllib.parse.unquote(path)
    if not path.endswith("/"):
        path += "/"

    items = fetch_directory(path, base_url, api_path)
    items = sort_items(items)

    if not items:
        xbmcgui.Dialog().notification(
            "Dhaka Flix",
            "No items found or server unreachable",
            xbmcgui.NOTIFICATION_WARNING,
            3000,
        )
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=False)
        return

    xbmcplugin.setContent(plugin.handle, "files")

    for item in items:
        is_folder = item["type"] == "folder"

        # Build label: name for folders, 'name  [size]' for files (D-05)
        label = item["name"]
        if not is_folder and item.get("size"):
            label = "{}  [{}]".format(item["name"], item["size"])

        li = xbmcgui.ListItem(label)
        li.setArt({"icon": ICON_MAP.get(item["type"], "DefaultFile.png")})

        if is_folder:
            # Navigate into subfolder
            sub_path = item["path"].lstrip("/")
            url = plugin.url_for(browse, server_index=server_index, path=sub_path)
            xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=True)
        else:
            # Non-folder item
            url = item["url"]
            if item["type"] in PLAYABLE_TYPES:
                li.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=False)

    xbmcplugin.endOfDirectory(plugin.handle)


def display_search_results(results: list) -> None:
    """Display search results with name, source category, and type icon."""
    xbmcplugin.setContent(plugin.handle, "files")

    if not results:
        xbmcgui.Dialog().notification(
            "Dhaka Flix", "No results found", xbmcgui.NOTIFICATION_INFO, 3000
        )
        # An empty result set is still a successful directory listing.
        # Marking it as failed makes Kodi show "Error getting plugin://...".
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=True)
        return

    for item in results:
        is_folder = item.get("type") == "folder"
        name = item.get("name", "Unknown")
        source_category = item.get("source_category", "")
        item_type = item.get("type", "other")

        # Create label with source category as subtitle
        label = name
        if source_category:
            label = "{}  [{}]".format(name, source_category)

        li = xbmcgui.ListItem(label)
        li.setArt({"icon": ICON_MAP.get(item_type, "DefaultFile.png")})

        if is_folder:
            # Navigate into series folder
            sub_path = item.get("path", "").lstrip("/")
            server_idx = SERVERS.index(
                next(s for s in SERVERS if s["name"] == source_category)
            )
            url = plugin.url_for(browse, server_index=str(server_idx), path=sub_path)
            xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=True)
        else:
            # Playable media item
            url = item.get("url", "")
            if item_type in PLAYABLE_TYPES:
                li.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=False)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/search")
def search():
    """Search submenu: Global Search + per-category search targets."""
    xbmcplugin.setContent(plugin.handle, "files")

    # Global Search entry
    li = xbmcgui.ListItem("Global Search")
    li.setArt({"icon": "DefaultFolder.png"})
    url = plugin.url_for(search_global)
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=True)

    # Per-category search entries
    for i, server in enumerate(SERVERS):
        li = xbmcgui.ListItem(server["name"])
        li.setArt({"icon": "DefaultFolder.png"})
        url = plugin.url_for(search_category, server_index=str(i))
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=True)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/search/global")
def search_global():
    """Global search across all servers using h5ai search API."""
    dialog = xbmcgui.Dialog()
    query = dialog.input("Search Dhaka Flix", type=xbmcgui.INPUT_ALPHANUM)
    if not query:
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=False)
        return

    progress = xbmcgui.DialogProgress()
    progress.create("Searching", "Searching all servers...")
    try:
        results = search_all_servers(query)
    finally:
        progress.close()

    display_search_results(results)


@plugin.route("/search/category/<server_index>")
def search_category(server_index):
    """Search within a specific category using h5ai search API."""
    server = SERVERS[int(server_index)]

    dialog = xbmcgui.Dialog()
    query = dialog.input(
        "Search {}".format(server["name"]), type=xbmcgui.INPUT_ALPHANUM
    )
    if not query:
        # Treat cancel/empty input as a clean exit (no Kodi "Error getting plugin://...").
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=True)
        return

    results = search_single_server(query, server)
    display_search_results(results)


if __name__ == "__main__":
    plugin.run()
