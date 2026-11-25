"""Justin's Pack: apply recommended device settings once, from Program add-ons."""
import json
import xbmc
import xbmcgui

# Kodi 21 setting ids (Settings > Services > Caching, Settings > System > Add-ons)
SETTINGS = {
    "filecache.buffermode": 4,      # buffer all network filesystems (Kodi default)
    "filecache.memorysize": 128,    # MB of RAM for video buffer; safe for 1-2 GB sticks
    "filecache.readfactor": 600,    # 6x bitrate fill speed (value is x100)
    "addons.updatemode": 0,         # official add-ons only update from the official repo
}


def set_setting(setting, value):
    req = {"jsonrpc": "2.0", "id": 1, "method": "Settings.SetSettingValue",
           "params": {"setting": setting, "value": value}}
    resp = json.loads(xbmc.executeJSONRPC(json.dumps(req)))
    return resp.get("result") is True


def main():
    dialog = xbmcgui.Dialog()
    if not dialog.yesno("Justin's Pack", "Apply recommended settings for this device?\n"
                        "(128 MB cache, safe add-on update mode)"):
        return
    failed = [k for k, v in SETTINGS.items() if not set_setting(k, v)]
    if failed:
        dialog.ok("Justin's Pack", "Done, but these could not be set:\n" + ", ".join(failed))
    else:
        dialog.notification("Justin's Pack", "Settings applied", xbmcgui.NOTIFICATION_INFO, 4000)


main()
