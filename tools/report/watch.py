"""Veille : conversations publiques des 7 derniers jours où nos outils peuvent aider quelqu'un.

Lecture seule, sources ouvertes, sans compte : Hacker News (API Algolia), Stack Overflow (API Stack Exchange),
forum image.sc (Discourse), Reddit (flux RSS publics ; ignoré si Reddit refuse la connexion).
Rien n'est publié automatiquement : la liste arrive dans le rapport du lundi, et c'est un humain qui répond.

python tools/report/watch.py   -> affiche la liste (contenu public, sans risque dans les journaux)
"""
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "jovianlabs-watch/1.0 (weekly read-only digest; contact@jovianlabsstudio.com)"

# (sujet, requêtes) ; chaque sujet renvoie à une page du site
TOPICS = {
    "metrology": ["SEM scale bar", "SEM pixel size", "particle size SEM", "TEM particle size", "nanoparticle size distribution ImageJ",
                  "porosity ImageJ", "porosity cross section image analysis", "fiber diameter SEM", "electrospun fiber diameter",
                  "DiameterJ", "nanomaterial definition"],
    "tenders": ["failed tender", "tender no bids", "public procurement relaunch", "TED tenders API", "BOAMP"],
}
PAGE = {"metrology": "https://jovianlabsstudio.com/metrology/", "tenders": "https://jovianlabsstudio.com/tenders/"}
REDDIT = {"metrology": ["microscopy", "materials", "labrats", "ImageJ", "electronmicroscopy"],
          "tenders": ["procurement", "govcontracting"]}
SO_TAGS = {"metrology": "imagej;scikit-image;opencv", "tenders": None}


def _get(url, timeout=30, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, application/rss+xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if raw else json.loads(data)


def hn(q, since):
    url = ("https://hn.algolia.com/api/v1/search_by_date?" +
           urllib.parse.urlencode({"query": q, "tags": "(story,comment)", "numericFilters": f"created_at_i>{int(since.timestamp())}",
                                   "hitsPerPage": 10}))
    out = []
    for h in _get(url).get("hits", []):
        title = h.get("title") or h.get("story_title") or (h.get("comment_text") or "")[:90]
        out.append(dict(source="Hacker News", title=re.sub("<[^>]+>", "", title), date=(h.get("created_at") or "")[:10],
                        url=f"https://news.ycombinator.com/item?id={h.get('objectID')}"))
    return out


def stackoverflow(q, since, tags):
    params = {"order": "desc", "sort": "creation", "q": q, "site": "stackoverflow", "fromdate": int(since.timestamp()), "pagesize": 10}
    if tags:
        params["tagged"] = tags
    d = _get("https://api.stackexchange.com/2.3/search/advanced?" + urllib.parse.urlencode(params))
    return [dict(source="Stack Overflow", title=re.sub("&#39;", "'", i.get("title", "")),
                 date=dt.datetime.fromtimestamp(i.get("creation_date", 0), dt.timezone.utc).date().isoformat(), url=i.get("link"))
            for i in d.get("items", [])]


def imagesc(q, since):
    d = _get("https://forum.image.sc/search.json?" + urllib.parse.urlencode({"q": f"{q} after:{since.date().isoformat()}"}))
    return [dict(source="image.sc", title=t.get("title", ""), date=(t.get("created_at") or "")[:10],
                 url=f"https://forum.image.sc/t/{t.get('slug')}/{t.get('id')}") for t in d.get("topics", [])]


def reddit(sub, q, since):
    url = (f"https://www.reddit.com/r/{sub}/search.rss?" +
           urllib.parse.urlencode({"q": q, "restrict_sr": 1, "sort": "new", "t": "week"}))
    root = ET.fromstring(_get(url, raw=True))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in root.findall("a:entry", ns):
        date = (e.findtext("a:updated", default="", namespaces=ns) or "")[:10]
        link = e.find("a:link", ns)
        if date >= since.date().isoformat() and link is not None:
            out.append(dict(source=f"Reddit r/{sub}", title=e.findtext("a:title", default="", namespaces=ns), date=date,
                            url=link.get("href")))
    return out


def watch(days=7, limit=20):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    items, errors = [], set()
    for topic, queries in TOPICS.items():
        for q in queries:
            for name, fn in (("hn", lambda: hn(q, since)), ("so", lambda: stackoverflow(q, since, SO_TAGS[topic])),
                             ("imagesc", lambda: imagesc(q, since) if topic == "metrology" else [])):
                try:
                    items += [dict(it, topic=topic, query=q) for it in fn()]
                except Exception as e:  # noqa: BLE001 — une source en panne ne bloque pas les autres
                    errors.add(f"{name}: {type(e).__name__}")
        for sub in REDDIT[topic]:
            for q in queries[:4]:
                try:
                    items += [dict(it, topic=topic, query=q) for it in reddit(sub, q, since)]
                except Exception as e:  # noqa: BLE001
                    errors.add(f"reddit: {type(e).__name__}")
                    break
    seen, uniq = set(), []
    for it in sorted(items, key=lambda x: x["date"], reverse=True):
        if it["url"] and it["url"] not in seen:
            seen.add(it["url"])
            uniq.append(it)
    return uniq[:limit], sorted(errors)


if __name__ == "__main__":
    found, errs = watch()
    for it in found:
        print(f"{it['date']} [{it['source']}] ({it['topic']}: {it['query']}) {it['title'][:90]} -> {it['url']}")
    print(len(found), "items; errors:", errs or "none")
