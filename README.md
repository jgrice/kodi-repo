# Justin's Kodi Repo

A personal Kodi repository that installs a lean POV-based setup (POV, Magneto, Arctic Horizon 2 with a POV home screen) on any device with one install.

## What's in it

| Add-on | What it does |
|---|---|
| `repository.jgrice` | Your repo. Your repo. Also points Kodi at kodifitzwell's repo (POV, Magneto) and Hooty's repo (Arctic Horizon 2 and its helpers), so they install and update straight from their sources. |
| `script.jgrice.pack.firestick` ("Justin's Pack (Fire Stick)") | Empty add-on whose `<requires>` list is the add-on set: **POV + Magneto + Arctic Horizon 2**. Setup sizes the cache to the stick's RAM (64 MB on 1 GB sticks, 128 MB on 2 GB), uses smaller artwork, 3 widget rows per menu, refresh-rate matching, English audio, subtitles off, and POV resume/next-episode prompts. Also has a TorBox / Trakt sign-in shortcut. |
| `script.jgrice.pack.pc` ("Justin's Pack (PC)") | Same add-on set for Windows: 512 MB cache, 5 widget rows per menu, same audio/subtitle/POV defaults. |

## One-time setup (GitHub Pages)

1. Create a public GitHub repo named `kodi-repo` and push this folder to it.
2. Run `python build.py` (generates `docs/`), commit and push.
3. In the repo's Settings > Pages, set source to **Deploy from branch**, branch `main`, folder `/docs`.
4. Check `https://jgrice.github.io/kodi-repo/` shows a link to the `repository.jgrice-x.y.z.zip`.

If you use a different repo name, change `site_url` in `config.json` and rebuild.

## Setting up a device (after base Kodi install)

1. Settings > System > Add-ons: turn on **Unknown sources**.
2. Settings > File manager > Add source: `https://jgrice.github.io/kodi-repo/`, name it `jgrice`.
3. Add-ons > Install from zip file > `jgrice` > `repository.jgrice-….zip`.
4. Add-ons > Install from repository > Justin's Kodi Repo > Program add-ons > **Justin's Pack (Fire Stick)** or **Justin's Pack (PC)** > Install. Kodi pulls in POV, Magneto and Arctic Horizon 2 with their dependencies.
5. A **Welcome** prompt appears right after the pack installs (and again at each Kodi start until setup is done). Choose **Set up**; or later, open the pack from Program add-ons and choose **Set up this device**. It applies the settings, installs the POV home screen and switches to Arctic Horizon 2 (answer **Yes** when Kodi asks to keep the skin).
6. After setup it offers to sign in; or open the pack and choose **Sign in to TorBox / Trakt**. This opens POV's My Services list: pick TorBox, scan the QR code with your phone (or enter the code at the address shown), then do the same for Trakt. No keys or tokens ship in the pack.

Choose **Reset home screen** any time to go back to the standard layout after experimenting. To sign a device out (e.g. a stick you're giving away), use the same menu and pick the signed-in service.

## Changing what devices get

Each pack lives in its own folder under `src/`:

- `addon.xml`: the `<import>` list is the add-on set for that device type. To add an add-on from a new source, also add that source's `<dir>` to `src/repository.jgrice/addon.xml`.
- `settings.json`: the device profile: Kodi settings, POV settings, add-ons to disable, optional `advancedsettings.xml` (documented at the top of `src/_shared/packlib.py`). When a pack update changes these, devices get a one-time prompt to apply them.
- `home/` (optional): files here replace the shared home layout files of the same name (the Fire Stick pack uses this for its 3-row widget lists).

`src/_shared/` is copied into every pack by `build.py`: `packlib.py` (setup logic), `default.py` (the pack menu), `service.py` (first-run Welcome prompt) and `home/` (the Arctic Horizon 2 home layout, as Skin Shortcuts files). Edit the `*.DATA.xml` files there to change the home menu items (`mainmenu`), their shortcut rows (`movies`, `tvshows`) and widget rows (`movies-1`, `tvshows-1`). Each item's `<action>` is a POV path.

1. Edit the pack you want to change (or both).
2. Bump `version=` in that pack's `addon.xml` (e.g. 1.0.0 to 1.0.1).
3. `python build.py`, commit, push.

Devices pick up the new pack version on their next add-on update check and install any newly listed add-ons. Removing an add-on from the list does not uninstall it from devices.

If you change `repository.jgrice` itself, bump its version too.

