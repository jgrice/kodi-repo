"""Justin's Pack: open from Program add-ons to apply device settings or sign in.

Settings come from settings.json in the pack folder (Kodi 21 setting ids):
  filecache.memorysize  MB of RAM for the video buffer
  filecache.readfactor  fill speed as a multiple of bitrate, x100 (600 = 6x)
  addons.updatemode     0 = official add-ons only update from the official repo
"""
import json
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()
NAME = ADDON.getAddonInfo("name")
PATH = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))


def set_setting(setting, value):
    req = {"jsonrpc": "2.0", "id": 1, "method": "Settings.SetSettingValue",
           "params": {"setting": setting, "value": value}}
    resp = json.loads(xbmc.executeJSONRPC(json.dumps(req)))
    return resp.get("result") is True


def apply_settings():
    with open(os.path.join(PATH, "settings.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    settings = cfg["settings"]
    summary = "\n".join(f"{k} = {v}" for k, v in settings.items())
    dialog = xbmcgui.Dialog()
    if not dialog.yesno(NAME, f"Apply recommended {cfg['label']} settings?\n{summary}"):
        return
    failed = [k for k, v in settings.items() if not set_setting(k, v)]
    if failed:
        dialog.ok(NAME, "Done, but these could not be set:\n" + ", ".join(failed))
    else:
        dialog.notification(NAME, "Settings applied", xbmcgui.NOTIFICATION_INFO, 4000)


def sign_in():
    # POV's own "My Services" screen: pick TorBox or Trakt, then scan the QR code
    # (or enter the code shown) on your phone. Pick an already-signed-in service to sign out.
    xbmc.executebuiltin("RunPlugin(plugin://plugin.video.pov/?mode=myservices)")


def main():
    choice = xbmcgui.Dialog().select(NAME, [
        "Sign in to TorBox / Trakt",
        "Apply device settings",
    ])
    if choice == 0:
        sign_in()
    elif choice == 1:
        apply_settings()


main()
