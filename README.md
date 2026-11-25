# Justin's Kodi Repo

A personal Kodi repository that installs a lean POV-based add-on set on any device with one install.

## What's in it

| Add-on | What it does |
|---|---|
| `repository.jgrice` | Your repo. Also points Kodi at kodifitzwell's repo, so POV and Magneto install and update from the source. |
| `script.jgrice.pack` ("Justin's Pack") | Empty add-on whose `<requires>` list is the add-on set: **POV + Magneto**. Running it from Program add-ons applies Fire Stick settings (128 MB cache, 6x read factor, safe update mode). |

## One-time setup (GitHub Pages)

1. Create a public GitHub repo named `kodi-repo` and push this folder to it.
2. Run `python build.py` (generates `docs/`), commit and push.
3. In the repo's Settings > Pages, set source to **Deploy from branch**, branch `main`, folder `/docs`.
4. Check `https://jgrice.github.io/kodi-repo/` shows a link to `repository.jgrice-1.0.0.zip`.

If you use a different repo name, change `site_url` in `config.json` and rebuild.

## Setting up a device (after base Kodi install)

1. Settings > System > Add-ons: turn on **Unknown sources**.
2. Settings > File manager > Add source: `https://jgrice.github.io/kodi-repo/`, name it `jgrice`.
3. Add-ons > Install from zip file > `jgrice` > `repository.jgrice-1.0.0.zip`.
4. Add-ons > Install from repository > Justin's Kodi Repo > Program add-ons > **Justin's Pack** > Install. Kodi pulls in POV and Magneto.
5. Open Justin's Pack once from Program add-ons and accept the settings prompt.
6. Open POV and sign in to Real-Debrid / TorBox / Trakt on that device (no tokens ship in the pack).

## Changing what every device gets

1. Edit the `<import>` list in `src/script.jgrice.pack/addon.xml` (Otaku is there commented out, along with its repo in `src/repository.jgrice/addon.xml`).
2. Bump `version=` in that file (e.g. 1.0.0 to 1.0.1).
3. `python build.py`, commit, push.

Devices pick up the new pack version on their next add-on update check and install any newly listed add-ons. Removing an add-on from the list does not uninstall it from devices.

If you change `repository.jgrice` itself, bump its version too.
