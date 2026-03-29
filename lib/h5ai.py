"""
h5ai API client for fetching directory listings from Dhaka Flix servers.
Uses only Python stdlib (urllib.request, json) — no external dependencies.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request

import xbmc


# File type extensions (expanded per D-06)
VIDEO_EXTS = {
    "mkv",
    "mp4",
    "avi",
    "mov",
    "wmv",
    "flv",
    "webm",
    "m4v",
    "ts",
    "mpg",
    "mpeg",
    "m2ts",
    "vob",
    "divx",
    "3gp",
}
AUDIO_EXTS = {
    "mp3",
    "wav",
    "flac",
    "aac",
    "ogg",
    "m4a",
    "opus",
    "wma",
    "ape",
    "dts",
    "ac3",
}
IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff", "tif"}
ARCHIVE_EXTS = {"zip", "rar", "7z", "tar", "gz", "iso", "bz2", "xz"}
DOCUMENT_EXTS = {"pdf", "doc", "docx", "txt", "md", "nfo", "srt", "sub", "ass", "idx"}

# Sort priority (folder first, then video/audio, then image, then archive/document, then other)
TYPE_PRIORITY = {
    "folder": 0,
    "video": 1,
    "audio": 1,
    "image": 2,
    "archive": 3,
    "document": 3,
    "other": 3,
}


def _get_file_type(href: str) -> str:
    """Detect file type from href extension."""
    if href.endswith("/"):
        return "folder"

    ext_match = re.search(r"\.([^./]+)$", href.lower())
    if not ext_match:
        return "other"

    ext = ext_match.group(1)
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in ARCHIVE_EXTS:
        return "archive"
    if ext in DOCUMENT_EXTS:
        return "document"
    return "other"


def _natural_sort_key(name: str):
    """
    Generate a sort key that handles numeric segments naturally.
    Splits name into text/number segments so "Movie 2" sorts before "Movie 10".
    E.g., "Movie 2" -> ("movie ", 2), "Movie 10" -> ("movie ", 10)
    """
    parts = re.split(r"(\d+)", name.lower())
    # Convert numeric parts to int for proper numeric comparison
    return [p.isdigit() and int(p) or p for p in parts]


def sort_items(items: list) -> list:
    """
    Sort items by type priority (folders first, video/audio, image, etc.),
    then by name using natural sorting.
    """

    def sort_key(item):
        priority = TYPE_PRIORITY.get(item.get("type", "other"), 3)
        name = item.get("name", "")
        return (priority, _natural_sort_key(name))

    return sorted(items, key=sort_key)


def format_bytes(size_bytes: int | None, decimals: int = 2) -> str | None:
    """
    Format byte size as human-readable string.
    Uses 1024 base with units: Bytes, KB, MB, GB, TB.
    Returns None if size_bytes is None or 0.
    """
    if size_bytes is None or size_bytes == 0:
        return None

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    if i == 0:
        return f"{int(size)} Bytes"
    return f"{size:.{decimals}f} {units[i]}"


def fetch_directory(path: str, base_url: str, api_path: str) -> list:
    """
    Fetch directory listing from h5ai server.

    Args:
        path: The folder path to fetch (e.g., /DHAKA-FLIX-7/English Movies/)
        base_url: The server base URL (e.g., http://172.16.50.7)
        api_path: The h5ai API path (e.g., /_h5ai/public/index.php)

    Returns:
        List of MediaItem dicts with keys: name, path, type, size, url
        Returns empty list on error.
    """
    try:
        # Build the API URL
        api_url = f"{base_url}{api_path}"

        # Build the POST body
        # items[href] must be form-encoded as items%5Bhref%5D
        # Use quote_via=quote to encode spaces as %20 instead of +
        post_data = urllib.parse.urlencode(
            {"action": "get", "items[href]": path, "items[what]": "1"},
            quote_via=urllib.parse.quote,
        )

        # Create request
        request = urllib.request.Request(
            api_url,
            data=post_data.encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            method="POST",
        )

        # Fetch with 10-second timeout
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        # Parse items
        raw_items = data.get("items", [])

        items = []
        # Encode path for comparison since API returns URL-encoded hrefs
        encoded_path = urllib.parse.quote(path, safe="/")

        for item in raw_items:
            href = item.get("href", "")

            # Ensure the item is within the requested path (compare with encoded path)
            if not href.startswith(encoded_path):
                continue

            # Exclude the directory itself
            if href == encoded_path:
                continue

            # We only want direct children
            rel_path = href[len(encoded_path) :]
            parts = [p for p in rel_path.split("/") if p]
            if len(parts) != 1:
                continue

            # Extract name (URL-decode the last path segment)
            name = urllib.parse.unquote(parts[0])

            # Determine file type
            file_type = _get_file_type(href)

            # Format size
            size = item.get("size")
            formatted_size = (
                format_bytes(size) if isinstance(size, (int, float)) else None
            )

            # Build full URL
            item_url = f"{base_url}{href}"

            items.append(
                {
                    "name": name,
                    "path": href,
                    "type": file_type,
                    "size": formatted_size,
                    "url": item_url,
                }
            )

        # Sort items by priority then name
        return sort_items(items)

    except urllib.error.URLError as e:
        xbmc.log(f"Dhaka Flix: Network error fetching {path}: {e}", xbmc.LOGERROR)
        return []
    except json.JSONDecodeError as e:
        xbmc.log(f"Dhaka Flix: Invalid JSON response from {path}: {e}", xbmc.LOGERROR)
        return []
    except Exception as e:
        xbmc.log(f"Dhaka Flix: Unexpected error fetching {path}: {e}", xbmc.LOGERROR)
        return []
