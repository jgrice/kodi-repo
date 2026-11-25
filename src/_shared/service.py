"""Justin's Pack first-run service.

Kodi starts this right after the pack is installed (and at every login). If this
device hasn't been set up yet, it waits for Kodi to be idle, then offers setup.
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


if not packlib.setup_done() and wait_until_idle():
    packlib.menu_first_run()
