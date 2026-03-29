import xbmc
import xbmcaddon


ADDON_ID = "plugin.video.dhakaflix"


def is_search_debug_logging_enabled() -> bool:
    try:
        return xbmcaddon.Addon(ADDON_ID).getSettingBool("search_debug_logging")
    except Exception:
        return False


def log_search_debug(message: str) -> None:
    if is_search_debug_logging_enabled():
        xbmc.log(f"Dhaka Flix [search]: {message}", xbmc.LOGINFO)
