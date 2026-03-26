import routing
import xbmcaddon
import xbmcgui
import xbmcplugin

from lib.config import SERVERS, get_path_from_url
from lib.h5ai import fetch_directory, sort_items

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


@plugin.route("/")
def index():
    """Home screen: list all 9 media categories."""
    xbmcplugin.setContent(plugin.handle, "files")
    for i, server in enumerate(SERVERS):
        li = xbmcgui.ListItem(server["name"])
        li.setArt({"icon": "DefaultFolder.png"})
        path = get_path_from_url(server["url"], server["base_url"])
        url = plugin.url_for(browse, server_index=str(i), path=path)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/browse/<server_index>/<path:path>")
def browse(server_index, path):
    """Browse folder contents with icons, file sizes, and sorting."""
    server = SERVERS[int(server_index)]
    base_url = server["base_url"]
    api_path = server["api_path"]

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    items = fetch_directory(path, base_url, api_path)
    items = sort_items(items)

    if not items:
        # Empty folder or error (already logged by h5ai.py)
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
            url = plugin.url_for(
                browse, server_index=str(server_index), path=item["path"]
            )
            xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=True)
        else:
            # Non-folder item: list it for now (Phase 2 adds playback)
            url = item["url"]
            xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=False)

    xbmcplugin.endOfDirectory(plugin.handle)


if __name__ == "__main__":
    plugin.run()
