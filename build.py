#!/usr/bin/env python3
"""Build the Kodi repository from src/ into docs/.

Usage:  python build.py
Then commit and push. GitHub Pages serves docs/ at site_url (install page + repo zip);
Kodi reads addons.xml, its checksum and the zips from data_url (raw.githubusercontent.com).
POV, Magneto and Arctic Horizon 2 are not copied here: repository.jgrice points Kodi
at their own repos.
"""
import hashlib
import json
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text())
SITE = CFG["site_url"].rstrip("/") + "/"
# Kodi on Windows failed to read the checksum from GitHub Pages, so Kodi's data comes
# from raw.githubusercontent.com; Pages only hosts the File manager install page.
DATA = CFG.get("data_url", SITE).rstrip("/") + "/"
OUT = ROOT / CFG["output_dir"]
SRC = ROOT / "src"
SHARED = SRC / "_shared"  # copied into every pack (non-repository add-on)
FIXED_TIME = (2020, 1, 1, 0, 0, 0)  # deterministic zips: no diff when nothing changed




def strip_decl(xml):
    return re.sub(r"<\?xml[^>]*\?>\s*", "", xml).strip()


# ---------- our own add-ons (src/) ----------

def build_own(out):
    entries, repo_zip = [], None
    for folder in sorted(p for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("_")):
        xml = (folder / "addon.xml").read_text(encoding="utf-8").replace("{SITE_URL}", DATA)
        root = ET.fromstring(xml.encode("utf-8"))
        aid, ver = root.get("id"), root.get("version")
        dest = out / aid
        dest.mkdir()
        zpath = dest / f"{aid}-{ver}.zip"
        files = [(f, folder) for f in folder.rglob("*")]
        if not aid.startswith("repository.") and SHARED.exists():
            files += [(f, SHARED) for f in SHARED.rglob("*")]
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f, base in sorted(files):
                if f.is_file() and "__pycache__" not in f.parts:
                    info = zipfile.ZipInfo(f"{aid}/{f.relative_to(base).as_posix()}", FIXED_TIME)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    z.writestr(info, xml if f.name == "addon.xml" else f.read_bytes())
        entries.append(strip_decl(xml))
        if aid.startswith("repository."):
            repo_zip = zpath
        print(f"built   {aid} {ver}")
    return entries, repo_zip


def build():
    with tempfile.TemporaryDirectory() as tmp:
        previous = Path(tmp) / "previous"
        if OUT.exists():
            shutil.move(str(OUT), previous)
        else:
            previous.mkdir()
        OUT.mkdir()
        try:
            own, repo_zip = build_own(OUT)
        except BaseException:
            shutil.rmtree(OUT)  # leave the last good build in place on any failure
            shutil.move(str(previous), OUT)
            raise

    addons = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + \
        "\n".join(own) + "\n</addons>\n"
    (OUT / "addons.xml").write_text(addons, encoding="utf-8")
    (OUT / "addons.xml.md5").write_text(hashlib.md5(addons.encode("utf-8")).hexdigest())

    # Kodi's File manager browses the Pages site root, so put the repo zip there with a link page.
    shutil.copy(repo_zip, OUT / repo_zip.name)
    (OUT / "index.html").write_text(
        f'<!DOCTYPE html><html><body><a href="{repo_zip.name}">{repo_zip.name}</a></body></html>\n')
    (OUT / ".nojekyll").write_text("")
    print(f"site ready in {OUT}  ->  {SITE} (Kodi data from {DATA})")


if __name__ == "__main__":
    build()
