import routing
import xbmcaddon

plugin = routing.Plugin()

# Routes will be added by Plan 02
# For now, just a minimal root route so the addon loads without error


@plugin.route("/")
def index():
    pass


if __name__ == "__main__":
    plugin.run()
