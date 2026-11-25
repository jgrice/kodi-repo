"""Justin's Pack: open from Program add-ons to set up this device or sign in.

Device settings come from settings.json in the pack folder (Kodi 21 setting ids):
  filecache.memorysize  MB of RAM for the video buffer
  filecache.readfactor  fill speed as a multiple of bitrate, x100 (600 = 6x)
  addons.updatemode     0 = official add-ons only update from the official repo

The home screen layout (Arctic Horizon 2 menus and widget rows pointing at POV)
comes from the home/ folder and is copied into Skin Shortcuts' data folder.
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
SKIN = "skin.arctic.horizon.2"
SHORTCUTS_DATA = "special://profile/addon_data/script.skinshortcuts/"


def jsonrpc(method, **params):
    req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    return json.loads(xbmc.executeJSONRPC(json.dumps(req)))


def load_config():
    with open(os.path.join(PATH, "settings.json"), encoding="utf-8") as f:
        return json.load(f)


def apply_settings(cfg):
    settings = cfg["settings"]
    return [k for k, v in settings.items()
            if jsonrpc("Settings.SetSettingValue", setting=k, value=v).get("result") is not True]


def install_home_layout():
    """Copy the POV home layout into Skin Shortcuts and force it to rebuild menus."""
    src = os.path.join(PATH, "home")
    xbmcvfs.mkdirs(SHORTCUTS_DATA)
    for name in os.listdir(src):
        xbmcvfs.copy(os.path.join(src, name), SHORTCUTS_DATA + name)
    # Deleting the hash makes Skin Shortcuts rebuild the menus on next home screen load.
    xbmcvfs.delete(SHORTCUTS_DATA + SKIN + ".hash")


def switch_to_skin():
    if xbmc.getSkinDir() == SKIN:
        xbmc.executebuiltin("ReloadSkin()")
        return True
    # Kodi asks "Keep this change?" after switching; the user confirms on screen.
    return jsonrpc("Settings.SetSettingValue", setting="lookandfeel.skin", value=SKIN).get("result") is True


def set_up_device():
    cfg = load_config()
    dialog = xbmcgui.Dialog()
    if not dialog.yesno(NAME, f"Set up this {cfg['label']}?\n"
                        "Applies cache and update settings, installs the POV home screen "
                        "and switches to Arctic Horizon 2. Replaces any custom home menu."):
        return
    failed = apply_settings(cfg)
    install_home_layout()
    if failed:
        dialog.ok(NAME, "These settings could not be set:\n" + ", ".join(failed))
    if not switch_to_skin():
        dialog.ok(NAME, "Couldn't switch skin. Pick Arctic Horizon 2 under Settings > Interface > Skin.")


def reset_home():
    if not xbmcgui.Dialog().yesno(NAME, "Reset the home screen to Justin's POV layout?\n"
                                  "Any changes you made to the home menu will be replaced."):
        return
    install_home_layout()
    switch_to_skin()


def sign_in():
    # POV's own "My Services" screen: pick TorBox or Trakt, then scan the QR code
    # (or enter the code shown) on your phone. Pick an already-signed-in service to sign out.
    xbmc.executebuiltin("RunPlugin(plugin://plugin.video.pov/?mode=myservices)")


def main():
    choice = xbmcgui.Dialog().select(NAME, [
        "Set up this device",
        "Sign in to TorBox / Trakt",
        "Reset home screen",
    ])
    if choice == 0:
        set_up_device()
    elif choice == 1:
        sign_in()
    elif choice == 2:
        reset_home()


main()
