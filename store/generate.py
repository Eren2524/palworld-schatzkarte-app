#!/usr/bin/env python3
"""Baut aus store.json, news.json und den GitHub-Releases die Store-Quellen.

  python3 store/generate.py build --out _site     -> _site/apps.json, apps-beta.json + Webseite
  python3 store/generate.py notes 2.1              -> Changelog-Abschnitt fuer Version 2.1
  python3 store/generate.py version                -> MARKETING_VERSION aus project.yml

Releases werden mit `gh api` geladen (in GitHub Actions ist GH_TOKEN gesetzt).
Zum lokalen Testen: --releases datei.json (Liste im Format der GitHub-API).
"""
import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "store"
BUILD_RE = re.compile(r"<!--\s*build:\s*([\w.]+)\s*-->")


def marketing_version():
    m = re.search(r'MARKETING_VERSION:\s*"?([\w.]+)"?', (ROOT / "project.yml").read_text())
    return m.group(1) if m else "1.0"


def changelog_section(version):
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    parts = re.split(r"^## +", text, flags=re.M)
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        if head.strip() == version:
            return body.strip()
    return ""


def load_releases(repo, cache):
    if repo in cache:
        return cache[repo]
    out = subprocess.run(["gh", "api", "--paginate", f"repos/{repo}/releases?per_page=100", "--jq", ".[]"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        print(f"Warnung: Releases von {repo} nicht lesbar: {out.stderr.strip()}", file=sys.stderr)
        cache[repo] = []
    else:
        cache[repo] = [json.loads(l) for l in out.stdout.splitlines() if l.strip()]
    return cache[repo]


def absolute(base, path):
    return path if path.startswith("http") else base + path


def clean_notes(body):
    body = BUILD_RE.sub("", body or "").strip()
    return body or "Fehlerbehebungen und Verbesserungen."


def versions_for(app, releases, beta):
    out = []
    for r in releases:
        if r.get("draft") or not r["tag_name"].startswith(app["tagPrefix"]):
            continue
        if r.get("prerelease") and not beta:
            continue
        asset = next((a for a in r.get("assets", []) if a["name"] == app["asset"]), None)
        if not asset:
            continue
        tag_ver = r["tag_name"][len(app["tagPrefix"]):]
        ver = tag_ver.split("-beta")[0]
        m = BUILD_RE.search(r.get("body") or "")
        notes = clean_notes(r.get("body"))
        if r.get("prerelease"):
            notes = "Beta: " + notes
        out.append({
            "version": ver,
            "buildVersion": m.group(1) if m else ver,
            "date": r.get("published_at") or r.get("created_at"),
            "localizedDescription": notes,
            "downloadURL": asset["browser_download_url"],
            "size": asset["size"],
            "minOSVersion": app.get("minOSVersion", "16.0"),
            "_tag": r["tag_name"],
            "_beta": bool(r.get("prerelease")),
            "_downloads": asset.get("download_count", 0),
        })
    out.sort(key=lambda v: v["date"] or "", reverse=True)
    return out


def build_source(cfg, news, cache, beta):
    base = cfg["baseURL"]
    apps, all_news = [], list(news)
    for app in cfg["apps"]:
        vers = versions_for(app, load_releases(app["repo"], cache), beta)
        entry = {k: app[k] for k in ("name", "bundleIdentifier", "developerName", "subtitle",
                                     "localizedDescription", "category", "tintColor") if k in app}
        entry["iconURL"] = absolute(base, app["iconURL"])
        entry["screenshots"] = [absolute(base, s) for s in app.get("screenshots", [])]
        entry["appPermissions"] = {"entitlements": [], "privacy": {}}
        entry["versions"] = [{k: v for k, v in x.items() if not k.startswith("_")} for x in vers]
        if vers:  # Felder fuer aeltere AltStore/SideStore-Versionen
            latest = entry["versions"][0]
            entry.update({"version": latest["version"], "versionDate": latest["date"],
                          "versionDescription": latest["localizedDescription"],
                          "downloadURL": latest["downloadURL"], "size": latest["size"]})
        apps.append(entry)
        for i, v in enumerate(vers):
            if i >= 3:
                break
            first = v["localizedDescription"].replace("Beta: ", "").lstrip("- ").splitlines()[0]
            all_news.append({
                "identifier": "release-" + v["_tag"],
                "title": f'{app["name"]} {v["version"]}{" Beta" if v["_beta"] else ""} ist da',
                "caption": first[:140],
                "date": (v["date"] or "")[:10],
                "tintColor": app.get("tintColor", cfg["tintColor"]),
                "imageURL": absolute(base, app["screenshots"][0]) if app.get("screenshots") else None,
                "appID": app["bundleIdentifier"],
                "notify": i == 0,
            })
    for n in all_news:
        if n.get("imageURL") is None:
            n.pop("imageURL", None)
        if n.get("imageURL") and not n["imageURL"].startswith("http"):
            n["imageURL"] = absolute(base, n["imageURL"])
    all_news.sort(key=lambda n: n.get("date", ""), reverse=True)
    name = cfg["name"] + (" (Beta)" if beta else "")
    return {
        "name": name,
        "identifier": "io.github.eren2524.store" + (".beta" if beta else ""),
        "subtitle": cfg["subtitle"],
        "description": cfg["description"],
        "iconURL": absolute(base, cfg["iconURL"]),
        "headerURL": absolute(base, cfg["headerURL"]),
        "website": cfg["website"],
        "tintColor": cfg["tintColor"],
        "featuredApps": cfg.get("featuredApps", []),
        "apps": apps,
        "news": all_news,
    }


def cmd_build(args):
    cfg = json.loads((STORE / "store.json").read_text(encoding="utf-8"))
    news = json.loads((STORE / "news.json").read_text(encoding="utf-8"))
    cache = {}
    if args.releases:
        rel = json.loads(Path(args.releases).read_text())
        for app in cfg["apps"]:
            cache[app["repo"]] = rel
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STORE / "site", out)
    stable = build_source(cfg, news, cache, beta=False)
    beta = build_source(cfg, news, cache, beta=True)
    for fn, data in (("apps.json", stable), ("apps-beta.json", beta)):
        (out / fn).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # Zusatzinfos nur fuer die Webseite (Empfehlungen, Repos fuer den Download-Zaehler)
    site = {"recommended": cfg.get("recommended", []),
            "apps": {a["bundleIdentifier"]: {"repo": a["repo"], "tagPrefix": a["tagPrefix"]} for a in cfg["apps"]}}
    (out / "site.json").write_text(json.dumps(site, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    n = sum(len(a["versions"]) for a in stable["apps"])
    print(f"Store gebaut: {len(stable['apps'])} App(s), {n} Version(en) stabil, "
          f"{sum(len(a['versions']) for a in beta['apps'])} inkl. Beta -> {out}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--out", default="_site"); b.add_argument("--releases")
    n = sub.add_parser("notes"); n.add_argument("version")
    sub.add_parser("version")
    a = p.parse_args()
    if a.cmd == "build":
        cmd_build(a)
    elif a.cmd == "notes":
        print(changelog_section(a.version))
    else:
        print(marketing_version())


if __name__ == "__main__":
    main()
