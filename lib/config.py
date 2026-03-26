SERVERS = [
    {
        "name": "English Movies",
        "url": "http://172.16.50.7/DHAKA-FLIX-7/English%20Movies/",
        "base_url": "http://172.16.50.7",
        "api_path": "/_h5ai/public/index.php",
    },
    {
        "name": "Hindi Movies",
        "url": "http://172.16.50.14/DHAKA-FLIX-14/Hindi%20Movies/",
        "base_url": "http://172.16.50.14",
        "api_path": "/_h5ai/public/index.php",
    },
    {
        "name": "South Movies Hindi Dubbed",
        "url": "http://172.16.50.14/DHAKA-FLIX-14/SOUTH%20INDIAN%20MOVIES/Hindi%20Dubbed/",
        "base_url": "http://172.16.50.14",
        "api_path": "/_h5ai/public/index.php",
    },
    {
        "name": "Kolkata Bangla Movies",
        "url": "http://172.16.50.7/DHAKA-FLIX-7/Kolkata%20Bangla%20Movies/",
        "base_url": "http://172.16.50.7",
        "api_path": "/_h5ai/public/index.php",
    },
    {
        "name": "Animation Movies",
        "url": "http://172.16.50.14/DHAKA-FLIX-14/Animation%20Movies/",
        "base_url": "http://172.16.50.14",
        "api_path": "/_h5ai/public/index.php",
    },
    {
        "name": "Foreign Language Movies",
        "url": "http://172.16.50.7/DHAKA-FLIX-7/Foreign%20Language%20Movies/",
        "base_url": "http://172.16.50.7",
        "api_path": "/_h5ai/public/index.php",
    },
    {
        "name": "TV Series",
        "url": "http://172.16.50.12/DHAKA-FLIX-12/TV-WEB-Series/",
        "base_url": "http://172.16.50.12",
        "api_path": "/_h5ai/public/index.php",
    },
    {
        "name": "Korean TV and Web Series",
        "url": "http://172.16.50.14/DHAKA-FLIX-14/KOREAN%20TV%20%26%20WEB%20Series/",
        "base_url": "http://172.16.50.14",
        "api_path": "/_h5ai/public/index.php",
    },
    {
        "name": "Anime",
        "url": "http://172.16.50.9/DHAKA-FLIX-9/Anime%20%26%20Cartoon%20TV%20Series/",
        "base_url": "http://172.16.50.9",
        "api_path": "/_h5ai/public/index.php",
    },
]


def get_path_from_url(url, base_url):
    """Extract the path portion from a full URL given its base."""
    if not url.startswith(base_url):
        return url
    return url[len(base_url) :]
