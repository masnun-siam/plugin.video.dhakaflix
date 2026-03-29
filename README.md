# Dhaka Flix Kodi Add-on

![Version](https://img.shields.io/badge/version-0.1.1-blue.svg)
![Kodi](https://img.shields.io/badge/kodi-matrix%20%2819%2B%29-blueviolet.svg)
![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)

A Kodi video add-on that lets you seamlessly browse and play media from Dhaka Flix LAN servers. It interfaces with the `h5ai` indexers on the Dhaka Flix network to provide a rich, native Kodi experience for accessing your media.

## Features

- **Multi-Category Browsing**: Access all major Dhaka Flix categories:
  - English Movies
  - Hindi Movies
  - South Indian Movies (Hindi Dubbed)
  - Kolkata Bangla Movies
  - Animation Movies
  - Foreign Language Movies
  - TV & Web Series
  - Korean TV & Web Series
  - Anime & Cartoon TV Series
- **Direct Playback**: Stream videos directly through Kodi's native player.
- **Global Search**: Search across all available servers and categories with a single query.
- **Category Search**: Narrow down your search to a specific media category.
- **Smart UI**: Displays file types, accurate file sizes, and uses caching for faster search results.

## Prerequisites

- **Kodi 19+ (Matrix, Nexus, Omega)** - Requires Python 3.
- **Local Network Access**: You must be connected to an ISP or network that has access to the Dhaka Flix `172.16.50.x` subnets in order for the streams to load.

## Installation

1. Navigate to the repository root.
2. Run the provided script to package the add-on:
   ```bash
   ./make-zip.sh
   ```
   _This will generate a `plugin.video.dhakaflix-0.1.1.zip` file._
3. Open **Kodi**.
4. Go to **Add-ons** > **Add-on Browser** (the open box icon) > **Install from zip file**.
5. Select the generated `plugin.video.dhakaflix-0.1.1.zip` file.
6. Once the installation notification appears, you can launch **Dhaka Flix** from your Video Add-ons menu.

## Usage

- **Browsing**: Launch the add-on and easily navigate the nested folders. Items that are recognized as playable media (videos, audio, images) will open in Kodi when selected.
- **Search**: Select the **Search** directory item at the top of the main menu to perform a global search. If you are inside a specific category, select **Search in [Category Name]** to limit the search scope.
- **Refresh Index**: If the contents on the server have updated, search index caching can be manually bypassed by refreshing via settings (if configured) or the `/search/refresh` route.

## Dependencies

- `xbmc.python` (v3.0.1+)
- `script.module.routing` (v0.2.3+)

_(These will be installed automatically by Kodi when installing from the zip file)._

## License

This project is licensed under the MIT License.
