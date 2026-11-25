"""Justin's Pack service.

Kodi starts this right after the pack is installed or updated, and at every login.
- Device not set up yet: once Kodi is idle, offer setup.
- Pack updated since setup: offer to apply the new version's settings (asked once per version).
"""
import xbmc

import packlib

monitor = xbmc.Monitor()


def wait_until_idle():
    """Wait for install/skin-switch dialogs to close, then a short settle."""
    quiet = 0
    while not monitor.abortRequested() and quiet < 6:
        busy = xbmc.getCondVisibility("System.HasActiveModalDialog | Window.IsActive(busydialog) "
                                      "| Window.IsActive(busydialognocancel) | Window.IsActive(extendedprogressdialog)")
        quiet = 0 if busy else quiet + 1
        if monitor.waitForAbort(0.5):
            return False
    return True


if not packlib.setup_done():
    if wait_until_idle():
        packlib.menu_first_run()
elif packlib.applied_version() != packlib.VERSION and wait_until_idle():
    packlib.offer_updated_settings()
