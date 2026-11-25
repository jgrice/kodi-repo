#!/usr/bin/env python3
"""Build the Kodi repository from src/ (and mirrored upstream add-ons) into docs/.

Usage:  python build.py
Then commit and push. GitHub Pages serves docs/ at site_url (install page + repo zip);
Kodi reads addons.xml, its checksum and the zips from data_url (raw.githubusercontent.com).

Mirroring: instead of pointing Kodi at whole upstream repos (which lists dozens of
unrelated add-ons), the add-ons named in config.json "mirror.addons" and their
dependencies are copied from the upstream repos into docs/. Anything not found
upstream (xbmc.*, script.module.requests, ...) comes from Kodi's official repo.
Re-running the build picks up new upstream versions; the GitHub Action does this daily.
"""
import hashlib
import json
import re
import shutil
import sys
import tempfile
import urllib.request
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


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kodi-repo-build"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def version_key(v):
    """Rough Kodi version ordering: 1.2.10 > 1.2.9; suffixes like ~omega / +matrix.1 ignored."""
    core = re.split(r"[~+]", v, 1)[0]
    return [int(p) if p.isdigit() else p for p in re.split(r"[.\-]", core)]


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


# ---------- mirrored upstream add-ons ----------

def upstream_index():
    """addon id -> (version, xml element, datadir), keeping the highest version across sources."""
    index = {}
    for src in CFG.get("mirror", {}).get("sources", []):
        root = ET.fromstring(fetch(src["info"]))
        for el in root.findall("addon"):
            aid, ver = el.get("id"), el.get("version")
            if aid not in index or version_key(ver) > version_key(index[aid][0]):
                index[aid] = (ver, el, src["datadir"].rstrip("/") + "/")
    return index


def resolve(index, wanted):
    """Wanted add-ons plus every non-optional dependency that the upstream repos provide."""
    todo, picked = list(wanted), {}
    while todo:
        aid = todo.pop()
        if aid in picked or aid not in index:
            continue
        picked[aid] = index[aid]
        for imp in index[aid][1].iter("import"):
            if imp.get("optional") != "true":
                todo.append(imp.get("addon"))
    missing = [a for a in wanted if a not in index]
    if missing:
        sys.exit(f"mirror: not found in any upstream source: {missing}")
    return picked


def build_mirror(out, previous):
    wanted = CFG.get("mirror", {}).get("addons", [])
    if not wanted:
        return []
    entries = []
    for aid, (ver, el, datadir) in sorted(resolve(upstream_index(), wanted).items()):
        name = f"{aid}-{ver}.zip"
        dest = out / aid
        dest.mkdir()
        old = previous / aid / name
        if old.exists():
            shutil.copy(old, dest / name)  # unchanged since last build: no re-download
            how = "kept"
        else:
            (dest / name).write_bytes(fetch(f"{datadir}{aid}/{name}"))
            how = "fetched"
        entries.append(strip_decl(ET.tostring(el, encoding="unicode")))
        print(f"{how:7} {aid} {ver}")
    return entries


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
            mirrored = build_mirror(OUT, previous)
        except BaseException:
            shutil.rmtree(OUT)  # leave the last good build in place on any failure
            shutil.move(str(previous), OUT)
            raise

    addons = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + \
        "\n".join(own + mirrored) + "\n</addons>\n"
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
