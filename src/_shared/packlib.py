"""Justin's Pack shared code: device setup, home layout, sign-in.

settings.json in each pack folder describes the device profile:
  label             shown in prompts ("Fire Stick", "PC")
  cache_by_ram      pick filecache.memorysize from the device's RAM (Fire Stick)
  settings          Kodi settings (Kodi 21 ids), applied via JSON-RPC
  pov               POV add-on settings (non-secret only)
  disable_addons    add-ons to turn off (e.g. version check, useless on Android)
  advancedsettings  written to userdata/advancedsettings.xml if none exists yet
  alternatives      fallback values for settings whose valid values vary by Kodi build

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


def total_ram_mb():
    """Total RAM from Kodi, e.g. '1888MB' -> 1888. 0 if unknown."""
    label = xbmc.getInfoLabel("System.Memory(total)")
    digits = "".join(c for c in label if c.isdigit())
    return int(digits) if digits else 0


def cache_size_for_ram(ram_mb):
    if ram_mb and ram_mb <= 1200:   # 1 GB sticks (Lite, 3rd gen, older 4K)
        return 64
    if ram_mb and ram_mb <= 2400:   # 1.5-2 GB (4K Max, Cube)
        return 128
    return 256


def device_settings(cfg):
    settings = dict(cfg.get("settings", {}))
    if cfg.get("cache_by_ram"):
        settings["filecache.memorysize"] = cache_size_for_ram(total_ram_mb())
    return settings


def set_kodi_setting(key, value, alternatives):
    for candidate in [value] + alternatives.get(key, []):
        if jsonrpc("Settings.SetSettingValue", setting=key, value=candidate).get("result") is True:
            return True
    return False


def apply_settings(cfg):
    """Apply Kodi, POV and add-on settings. Returns a list of things that failed."""
    failed = []
    alternatives = cfg.get("alternatives", {})
    for key, value in device_settings(cfg).items():
        if not set_kodi_setting(key, value, alternatives):
            failed.append(key)
    pov = cfg.get("pov", {})
    if pov:
        try:
            addon = xbmcaddon.Addon("plugin.video.pov")
            for key, value in pov.items():
                addon.setSetting(key, str(value))
        except RuntimeError:
            failed.append("POV settings (POV not installed)")
    for addon_id in cfg.get("disable_addons", []):
        jsonrpc("Addons.SetAddonEnabled", addonid=addon_id, enabled=False)
    return failed


def write_advancedsettings(cfg):
    """Returns True if a new advancedsettings.xml was written (needs a Kodi restart)."""
    content = cfg.get("advancedsettings")
    path = "special://profile/advancedsettings.xml"
    if not content or xbmcvfs.exists(path):
        return False
    f = xbmcvfs.File(path, "w")
    f.write(content)
    f.close()
    return True


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


def set_up_device(confirm=True):
    cfg = load_config()
    dialog = xbmcgui.Dialog()
    if confirm and not dialog.yesno(NAME, f"Set up this {cfg['label']}?\n"
                        "Applies cache and update settings, installs the POV home screen "
                        "and switches to Arctic Horizon 2. Replaces any custom home menu."):
        return False
    failed = apply_settings(cfg)
    needs_restart = write_advancedsettings(cfg)
    install_home_layout()
    if failed:
        dialog.ok(NAME, "These settings could not be set:\n" + ", ".join(failed))
    mark_setup_done()
    if not switch_to_skin():
        dialog.ok(NAME, "Couldn't switch skin. Pick Arctic Horizon 2 under Settings > Interface > Skin.")
    if needs_restart:
        wait_for_quiet()
        dialog.ok(NAME, "Restart Kodi once when you're done to finish setup (smaller artwork for faster scrolling).")
    return True


def reset_home():
    if not xbmcgui.Dialog().yesno(NAME, "Reset the home screen to Justin's POV layout?\n"
                                  "Any changes you made to the home menu will be replaced."):
        return
    install_home_layout()
    switch_to_skin()


SERVICES = (("TorBox", "tb.token"), ("Trakt", "trakt.token"))


def signed_in():
    """Which of TorBox / Trakt POV has a token for (read fresh each time)."""
    pov = xbmcaddon.Addon("plugin.video.pov")
    return {name: bool(pov.getSetting(key)) for name, key in SERVICES}


def run_my_services():
    """Open POV's My Services list and wait until its dialogs (list, QR code, notices) close.
    POV handles one service per opening, so sign_in() calls this once per service."""
    xbmc.executebuiltin("RunPlugin(plugin://plugin.video.pov/?mode=myservices)")
    monitor = xbmc.Monitor()
    for _ in range(40):  # up to 20 s for the list to appear
        if xbmc.getCondVisibility("System.HasActiveModalDialog") or monitor.abortRequested():
            break
        monitor.waitForAbort(0.5)
    wait_for_quiet(4)


def sign_in():
    """Walk through TorBox and Trakt in turn, reopening POV's list until both are signed in.
    Picking an already-signed-in service in the list signs it out (for a stick you give away)."""
    run_my_services()
    while True:
        status = signed_in()
        missing = [name for name, ok in status.items() if not ok]
        if not missing:
            xbmcgui.Dialog().notification(NAME, "TorBox and Trakt are signed in", xbmcgui.NOTIFICATION_INFO, 4000)
            return
        done = [name for name, ok in status.items() if ok]
        text = ("%s is signed in. " % " and ".join(done) if done else "") + \
            "Sign in to %s now?\nPick it in the list, then scan the QR code with your phone." % " and ".join(missing)
        if not xbmcgui.Dialog().yesno(NAME, text, nolabel="Later", yeslabel="Sign in"):
            return
        run_my_services()


FIRST_RUN_MARKER = "special://profile/addon_data/%s/setup_done" % ADDON.getAddonInfo("id")


VERSION = ADDON.getAddonInfo("version")


def mark_setup_done():
    """Record which pack version's settings this device has."""
    xbmcvfs.mkdirs("special://profile/addon_data/%s/" % ADDON.getAddonInfo("id"))
    f = xbmcvfs.File(FIRST_RUN_MARKER, "w")
    f.write(VERSION)
    f.close()


def applied_version():
    if not xbmcvfs.exists(FIRST_RUN_MARKER):
        return None
    f = xbmcvfs.File(FIRST_RUN_MARKER)
    v = f.read().strip()
    f.close()
    return v


def setup_done():
    # Devices set up before the first-run marker existed already have the layout files.
    return xbmcvfs.exists(FIRST_RUN_MARKER) or xbmcvfs.exists(SHORTCUTS_DATA + SKIN + "-mainmenu.DATA.xml")


def menu():
    choice = xbmcgui.Dialog().select(NAME, [
        "Set up this device",
        "Sign in to TorBox / Trakt",
        "Reset home screen",
    ])
    if choice == 0:
        if set_up_device():
            offer_sign_in()
    elif choice == 1:
        sign_in()
    elif choice == 2:
        reset_home()


def wait_for_quiet(seconds=3):
    """Let a skin reload / 'keep skin?' prompt finish before showing another dialog."""
    monitor = xbmc.Monitor()
    quiet = 0
    while quiet < seconds * 2 and not monitor.abortRequested():
        quiet = 0 if xbmc.getCondVisibility("System.HasActiveModalDialog") else quiet + 1
        monitor.waitForAbort(0.5)


def offer_sign_in():
    wait_for_quiet()
    if all(signed_in().values()):
        return
    if xbmcgui.Dialog().yesno(NAME, "Sign in to TorBox and Trakt now?\n"
                              "You'll scan a QR code with your phone for each, one after the other."):
        sign_in()


def menu_first_run():
    """Shown automatically once after install. 'Not now' asks again next time Kodi starts."""
    label = load_config()["label"]
    if not xbmcgui.Dialog().yesno(NAME, f"Welcome! Set up this {label} now?\n"
                                  "Applies cache settings and the POV home screen on Arctic Horizon 2. "
                                  "You can also do this later from Program add-ons.",
                                  nolabel="Not now", yeslabel="Set up"):
        return
    if set_up_device(confirm=False):
        offer_sign_in()


def offer_updated_settings():
    """After a pack update: offer to apply the new version's settings (not the home layout)."""
    if applied_version() == VERSION:
        return
    if xbmcgui.Dialog().yesno(NAME, f"{NAME} was updated to {VERSION}.\n"
                              "Apply its latest recommended settings? Your home screen is left as is.",
                              nolabel="Not now", yeslabel="Apply"):
        failed = apply_settings(load_config())
        needs_restart = write_advancedsettings(load_config())
        if failed:
            xbmcgui.Dialog().ok(NAME, "These settings could not be set:\n" + ", ".join(failed))
        if needs_restart:
            xbmcgui.Dialog().ok(NAME, "Restart Kodi once to finish applying the update.")
    mark_setup_done()  # ask once per version either way
