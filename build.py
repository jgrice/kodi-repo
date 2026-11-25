#!/usr/bin/env python3
"""Build the Kodi repository site from src/ into docs/ (served by GitHub Pages).

Usage:  python build.py
Then commit and push; GitHub Pages serves docs/ at site_url from config.json.
"""
import hashlib
import json
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text())
SITE = CFG["site_url"].rstrip("/") + "/"
# Where Kodi reads addons.xml / checksum / zips from. Kodi on Windows failed to read
# the checksum from GitHub Pages, so the repo data is served from raw.githubusercontent.com.
DATA = CFG.get("data_url", SITE).rstrip("/") + "/"
OUT = ROOT / CFG["output_dir"]
SRC = ROOT / "src"
SHARED = SRC / "_shared"  # copied into every pack (non-repository add-on)


def addon_xml(folder):
    return (folder / "addon.xml").read_text(encoding="utf-8").replace("{SITE_URL}", DATA)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    entries, repo_zip = [], None
    for folder in sorted(p for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("_")):
        xml = addon_xml(folder)
        root = ET.fromstring(xml.encode("utf-8"))
        aid, ver = root.get("id"), root.get("version")
        dest = OUT / aid
        dest.mkdir()
        zpath = dest / f"{aid}-{ver}.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            files = [(f, folder) for f in folder.rglob("*")]
            if not aid.startswith("repository.") and SHARED.exists():
                files += [(f, SHARED) for f in SHARED.rglob("*")]
            for f, base in sorted(files):
                if f.is_file() and "__pycache__" not in f.parts:
                    arc = f"{aid}/{f.relative_to(base).as_posix()}"
                    if f.name == "addon.xml":
                        z.writestr(arc, xml)
                    else:
                        z.write(f, arc)
        entries.append(re.sub(r"<\?xml[^>]*\?>\s*", "", xml).strip())
        if aid.startswith("repository."):
            repo_zip = zpath
        print(f"built {aid} {ver}")

    addons = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + \
        "\n".join(entries) + "\n</addons>\n"
    (OUT / "addons.xml").write_text(addons, encoding="utf-8")
    (OUT / "addons.xml.md5").write_text(hashlib.md5(addons.encode("utf-8")).hexdigest())

    # Kodi's File manager browses the site root, so put the repo zip there with a plain link page.
    shutil.copy(repo_zip, OUT / repo_zip.name)
    (OUT / "index.html").write_text(
        f'<!DOCTYPE html><html><body><a href="{repo_zip.name}">{repo_zip.name}</a></body></html>\n')
    (OUT / ".nojekyll").write_text("")
    print(f"site ready in {OUT}  ->  {SITE} (Kodi data from {DATA})")


if __name__ == "__main__":
    build()
