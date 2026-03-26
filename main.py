import routing
import xbmcaddon
import xbmcgui
import xbmcplugin

from lib.config import SERVERS, get_path_from_url
from lib.h5ai import fetch_directory, sort_items

plugin = routing.Plugin()


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
    """Browse folder contents (implemented in Task 2)."""
    pass


if __name__ == "__main__":
    plugin.run()
