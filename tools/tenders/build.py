"""Pages hebdomadaires « second-chance tenders » : appels relancés ouverts + lots infructueux récents.

python3 build.py [--out ../..] [--countries FRA DEU] [--days 30]
Sources : TED (API officielle, sans clé) et BOAMP (open data DILA). Aucune clé nécessaire.
"""
import argparse
import datetime as dt
import html
import itertools
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tenderslib import boamp, ted  # noqa: E402

SITE = "https://jovianlabsstudio.github.io"
ACTOR = "https://apify.com/jovianlabs/failed-public-tenders"
EMAIL = "jovianlabsstudio@gmail.com"

COUNTRIES = {"FRA": ("France", "france"), "DEU": ("Germany", "germany"), "ITA": ("Italy", "italy"), "ESP": ("Spain", "spain"),
             "POL": ("Poland", "poland"), "ROU": ("Romania", "romania"), "NLD": ("Netherlands", "netherlands"),
             "BEL": ("Belgium", "belgium"), "AUT": ("Austria", "austria"), "PRT": ("Portugal", "portugal"),
             "CZE": ("Czechia", "czechia"), "SWE": ("Sweden", "sweden"), "FIN": ("Finland", "finland"),
             "DNK": ("Denmark", "denmark"), "IRL": ("Ireland", "ireland"), "GRC": ("Greece", "greece")}

SECTORS = [  # (slug FR, libellé FR, libellé EN, préfixes CPV)
    ("travaux", "Travaux et bâtiment", "Construction works", ("45",)),
    ("sante", "Santé et médical", "Medical and pharma", ("33",)),
    ("nettoyage-dechets", "Nettoyage, déchets, environnement", "Cleaning, waste, environment", ("90", "77")),
    ("maintenance", "Maintenance et réparation", "Repair and maintenance", ("50",)),
    ("vehicules-transport", "Véhicules et transport", "Vehicles and transport", ("34", "60", "63")),
    ("alimentation", "Alimentation et restauration", "Food and catering", ("15", "55")),
    ("assurance-finance", "Assurance et finance", "Insurance and finance", ("66",)),
    ("ingenierie-etudes", "Ingénierie, études, contrôles", "Engineering, studies, testing", ("71", "73")),
    ("informatique", "Informatique et logiciels", "IT and software", ("48", "72", "30", "32")),
    ("services-entreprises", "Services aux entreprises", "Business services", ("79", "98", "64")),
    ("formation", "Formation et éducation", "Training and education", ("80",)),
    ("equipements", "Équipements, mobilier, fournitures", "Equipment, furniture, supplies", ("39", "38", "42", "44", "31", "37", "18", "22", "24", "35", "43", "09", "03", "16", "19", "14")),
]


KEYWORDS = [  # repli quand l'avis n'a pas de code CPV
    ("nettoyage-dechets", r"nettoyage|propret|déchet|dechet|espaces verts|élagage|elagage|arbres|cleaning|waste"),
    ("assurance-finance", r"assurance|insurance|financ"),
    ("informatique", r"logiciel|informatique|numérique|numerique|software|licen[cs]e|serveur|cloud"),
    ("formation", r"formation|training|enseignement"),
    ("alimentation", r"repas|restauration|denrée|denree|alimentaire|pain|viennoiser|food|catering"),
    ("vehicules-transport", r"véhicule|vehicule|transport|carburant|pneumati|bus\b"),
    ("maintenance", r"maintenance|entretien|réparation|reparation|repair"),
    ("travaux", r"travaux|construction|réhabilitation|rehabilitation|bâtiment|batiment|works"),
    ("sante", r"médical|medical|pharma|médicament|medicament|santé|sante|hospital|hôpital|hopital"),
    ("ingenierie-etudes", r"étude|etude|ingénierie|ingenierie|contrôle|controle|vérification|verification|audit|maîtrise d'oeuvre"),
    ("services-entreprises", r"intérim|interim|conseil|communication|impression|affranchissement|nettoyage"),
]


def sector_of(cpv, title=""):
    for slug, fr, en, pref in SECTORS:
        if cpv and cpv.startswith(pref):
            return slug, fr, en
    t = (title or "").lower()
    for slug, rx in KEYWORDS:
        if re.search(rx, t):
            fr, en = next((f, e) for s_, f, e, _ in SECTORS if s_ == slug)
            return slug, fr, en
    return "autres", "Autres", "Other"


def esc(x):
    return html.escape(html.unescape(str(x if x is not None else "")), quote=True)


def money(v, cur):
    if not v:
        return ""
    v = float(v)
    s = f"{v / 1e6:.1f} M" if v >= 1e6 else (f"{v / 1e3:.0f} k" if v >= 1e3 else f"{v:.0f}")
    return f"{s} {cur or ''}".strip()


def collect(code, today, days, log):
    since = today - dt.timedelta(days=days)
    relaunch = []
    if code == "FRA":
        relaunch += list(boamp.relaunched_calls(today=today, log=log))
    seen = {(x.get("deadline"), (x.get("procedureTitle") or "")[:40].lower()) for x in relaunch}
    for x in ted.relaunched_calls(today, [code], None, log=log):
        k = (x.get("deadline"), (x.get("procedureTitle") or "")[:40].lower())
        if k not in seen:
            seen.add(k)
            relaunch.append(x)
    failed = list(itertools.islice(ted.failed_lots(since, ["no-rece", "all-rej"], [code], None, log=log), 1500))
    # un avis = une ligne (les gros avis pharmaceutiques ont parfois des centaines de lots)
    by_notice = defaultdict(list)
    for f in failed:
        by_notice[f["noticeId"]].append(f)
    notices = []
    for nid, lots in by_notice.items():
        f0 = lots[0]
        val = sum(l["estimatedValue"] or 0 for l in lots)
        notices.append(dict(noticeId=nid, published=f0["published"], buyer=f0["buyer"], title=f0["procedureTitle"] or f0["noticeTitle"],
                            lots=[l["lotTitle"] for l in lots if l.get("lotTitle")][:3], n_lots=len(lots), cpv=f0["cpv"],
                            value=val or None, currency=f0["currency"], reasons=sorted({l["reasonCode"] for l in lots}),
                            relaunch_planned=any(l.get("relaunchPlanned") for l in lots), url=f0["url"]))
    relaunch.sort(key=lambda x: x.get("deadline") or "9999")
    notices.sort(key=lambda x: x["published"], reverse=True)
    return dict(relaunch=relaunch, failed=notices, n_failed_lots=len(failed))


L = {
    "en": dict(rel="Open calls that relaunch a failed procedure", fail="Recently failed procedures (no tenders or all rejected)",
               deadline="Deadline", buyer="Buyer", proc="Procedure", sector="Sector", value="Est. value", why="Why", notice="Notice",
               published="Published", lots="Lots", no_rece="no tenders", all_rej="all rejected", relaunch="relaunch",
               match_high="strong match", match_medium="likely match", boamp="mentions failure", open="open",
               more="more lots", planned="relaunch planned", none="Nothing this week.",
               cta="Get these opportunities for your sector every morning: run our Apify Actor with a daily schedule and send the results to email, Slack or Google Sheets.",
               cta_link="Failed & Relaunched Public Tenders on Apify", updated="Updated", sources="Sources: TED (EU Publications Office) and BOAMP (DILA, Licence Ouverte). Always check the official notice before acting.",
               nav_all="All countries"),
    "fr": dict(rel="Appels d'offres ouverts qui relancent une procédure infructueuse", fail="Procédures récentes infructueuses (aucune offre ou toutes rejetées)",
               deadline="Date limite", buyer="Acheteur", proc="Procédure", sector="Secteur", value="Valeur est.", why="Motif", notice="Avis",
               published="Publié", lots="Lots", no_rece="aucune offre", all_rej="offres rejetées", relaunch="relance",
               match_high="relance probable", match_medium="relance possible", boamp="mentionne l'infructuosité", open="ouvert",
               more="autres lots", planned="relance prévue", none="Rien cette semaine.",
               cta="Recevez ces opportunités pour votre secteur chaque matin : lancez notre Actor Apify avec une planification quotidienne et recevez les résultats par e-mail, Slack ou Google Sheets.",
               cta_link="Failed & Relaunched Public Tenders sur Apify", updated="Mise à jour", sources="Sources : TED (Office des publications de l'UE) et BOAMP (DILA, Licence Ouverte). Vérifiez toujours l'avis officiel avant d'agir.",
               nav_all="Tous les pays"),
}


def head(lang, title, desc, canonical, noindex=False):
    rb = '<meta name="robots" content="noindex">' if noindex else ""
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(canonical)}">{rb}'
            f'<link rel="icon" href="/assets/favicon.png"><link rel="stylesheet" href="/assets/style.css">'
            f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"></head><body>'
            f'<header><a class="brand" href="/"><img src="/assets/logo.svg" alt="">Jovian Labs</a>'
            f'<nav><a href="/tenders/">Tenders</a><a href="/tenders/france/">France</a><a href="/ai-index/">AI Index</a></nav></header><main>')


def foot(t):
    return (f'</main><footer>{esc(t["sources"])} Jovian Labs is independent and not affiliated with the EU Publications Office or DILA. '
            f'Contact: <a href="mailto:{EMAIL}">{EMAIL}</a></footer></body></html>')


def table_relaunch(items, t, lang, limit=250):
    if not items:
        return f"<p class='small'>{t['none']}</p>"
    rows = []
    for x in items[:limit]:
        conf = x.get("relaunchConfidence")
        tag = (f"<span class='tag hot'>{t['match_high']}</span>" if conf == "high" else
               f"<span class='tag'>{t['match_medium']}</span>" if conf == "medium" else f"<span class='tag hot'>{t['boamp']}</span>")
        sec = sector_of(x.get("cpv"), x.get("procedureTitle") or x.get("noticeTitle"))[1 if lang == "fr" else 2]
        rows.append(f"<tr><td class='num'>{esc(x.get('deadline'))}</td><td>{esc(x.get('buyer'))}</td>"
                    f"<td><a href='{esc(x.get('url'))}' rel='nofollow noopener' target='_blank'>{esc((x.get('procedureTitle') or x.get('noticeTitle') or '')[:160])}</a><div>{tag}</div></td>"
                    f"<td>{esc(sec)}</td><td class='num'>{esc(money(x.get('estimatedValue'), x.get('currency')))}</td></tr>")
    extra = (f"<p class='small'>+{len(items) - limit} — <a href='{ACTOR}'>{esc(t['cta_link'])}</a></p>" if len(items) > limit else "")
    return (f"<div class='card'><table><thead><tr><th>{t['deadline']}</th><th>{t['buyer']}</th><th>{t['proc']}</th><th>{t['sector']}</th>"
            f"<th>{t['value']}</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>{extra}")


def table_failed(items, t, lang, limit=150):
    if not items:
        return f"<p class='small'>{t['none']}</p>"
    rows = []
    for x in items[:limit]:
        why = ", ".join(t["no_rece"] if r == "no-rece" else t["all_rej"] for r in x["reasons"])
        lots = "; ".join(esc(l[:70]) for l in x["lots"])
        more = f" (+{x['n_lots'] - len(x['lots'])} {t['more']})" if x["n_lots"] > len(x["lots"]) else ""
        planned = f" <span class='tag hot'>{t['planned']}</span>" if x["relaunch_planned"] else ""
        sec = sector_of(x.get("cpv"), x.get("title"))[1 if lang == "fr" else 2]
        rows.append(f"<tr><td class='num'>{esc(x['published'])}</td><td>{esc(x['buyer'])}</td>"
                    f"<td><a href='{esc(x['url'])}' rel='nofollow noopener' target='_blank'>{esc((x['title'] or '')[:150])}</a>"
                    f"<div class='small'>{lots}{esc(more)}</div></td><td>{esc(sec)}</td><td class='num'>{esc(money(x['value'], x['currency']))}</td>"
                    f"<td><span class='tag'>{esc(why)}</span>{planned}</td></tr>")
    return (f"<div class='card'><table><thead><tr><th>{t['published']}</th><th>{t['buyer']}</th><th>{t['proc']} · {t['lots']}</th><th>{t['sector']}</th>"
            f"<th>{t['value']}</th><th>{t['why']}</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


def cta(t):
    return f"<div class='cta'><b>Alerts</b><p class='small'>{esc(t['cta'])} <a href='{ACTOR}'>{esc(t['cta_link'])}</a>.</p></div>"


def render_country(out, code, data, today, week, lang, sector=None):
    name, slug = COUNTRIES[code]
    t = L[lang]
    rel, fail = data["relaunch"], data["failed"]
    if sector:
        rel = [x for x in rel if sector_of(x.get("cpv"), x.get("procedureTitle") or x.get("noticeTitle"))[0] == sector[0]]
        fail = [x for x in fail if sector_of(x.get("cpv"), x.get("title"))[0] == sector[0]]
    if lang == "fr":
        scope = f" : {sector[1].lower()}" if sector else ""
        h1 = f"Appels d'offres relancés et infructueux en France{scope}"
        title = f"Appels d'offres infructueux et relancés en France{scope} (semaine {week})"
        desc = (f"{len(rel)} appels ouverts relançant une procédure infructueuse et {len(fail)} procédures sans offre ou aux offres rejetées "
                f"en France{scope}, mis à jour chaque semaine. Des marchés publics avec peu de concurrence.")
        lede = ("Quand un marché public ne reçoit aucune offre, il est souvent relancé, avec moins de concurrence. Après un appel d'offres infructueux, "
                "l'acheteur peut aussi, sous conditions, négocier directement. Voici les relances ouvertes et les échecs récents.")
    else:
        scope = f": {sector[2].lower()}" if sector else ""
        h1 = f"Second-chance public tenders in {name}{scope}"
        title = f"Failed and relaunched public tenders in {name}{scope} (week {week})"
        desc = (f"{len(rel)} open calls relaunching a failed procedure and {len(fail)} procedures with no tenders or all tenders rejected in {name}, "
                "updated weekly. Public contracts with little competition.")
        lede = ("When a public contract gets no tenders, it usually comes back, often with less competition. Under the EU directive, the buyer may even "
                "negotiate directly after an unsuccessful procedure. Here are the open relaunches and the recent failures.")
    path = f"tenders/{slug}/" + (f"{sector[0]}/" if sector else "")
    chips = ""
    if code == "FRA" and lang == "fr":
        chips = "<div class='chips'>" + "".join(
            f"<a href='/tenders/france/{s}/'>{esc(fr)}</a>" for s, fr, en, _ in SECTORS) + "<a href='/tenders/'>Autres pays</a></div>"
    body = (head(lang, title, desc, f"{SITE}/{path}") + f"<h1>{esc(h1)}</h1><p class='lede'>{esc(lede)}</p>{chips}"
            f"<div class='kpis'><div class='kpi'><b>{len(rel)}</b><span>{esc(t['rel'])}</span></div>"
            f"<div class='kpi'><b>{len(fail)}</b><span>{esc(t['fail'])}</span></div></div>"
            f"<p class='small'>{t['updated']} {today.isoformat()}.</p>"
            f"<h2>{esc(t['rel'])}</h2>{table_relaunch(rel, t, lang)}{cta(t)}"
            f"<h2>{esc(t['fail'])}</h2>{table_failed(fail, t, lang)}" + foot(t))
    p = out / path / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return f"{SITE}/{path}"


def render_hub(out, stats, today, week):
    t = L["en"]
    tiles = "".join(
        f"<a class='tile' href='/tenders/{COUNTRIES[c][1]}/'><div class='k'>{esc(c)}</div><div class='t'>{esc(COUNTRIES[c][0])}</div>"
        f"<div class='s'>{s['relaunch']} open relaunch calls · {s['failed']} failed procedures (30 days)</div></a>"
        for c, s in stats.items())
    total_r = sum(s["relaunch"] for s in stats.values())
    total_f = sum(s["failed"] for s in stats.values())
    title = f"Second-chance public tenders in Europe: failed and relaunched contracts (week {week})"
    desc = f"{total_r} open calls relaunching failed public procurement procedures and {total_f} recent failed procedures in {len(stats)} European countries, updated weekly."
    body = (head("en", title, desc, f"{SITE}/tenders/") +
            "<h1>Second-chance public tenders in Europe</h1>"
            "<p class='lede'>Every week, thousands of public procurement lots in Europe close without a winner because nobody bid or every bid was rejected. "
            "Most come back, with fewer competitors. We list the open calls that relaunch them and the recent failures, country by country.</p>"
            f"<div class='kpis'><div class='kpi'><b>{total_r}</b><span>open relaunch calls</span></div><div class='kpi'><b>{total_f}</b><span>failed procedures, last 30 days</span></div></div>"
            f"<p class='small'>{t['updated']} {today.isoformat()}. Version française : <a href='/tenders/france/'>appels d'offres infructueux et relancés en France</a>.</p>"
            f"<div class='grid'>{tiles}</div>{cta(t)}" + foot(t))
    (out / "tenders").mkdir(parents=True, exist_ok=True)
    (out / "tenders" / "index.html").write_text(body, encoding="utf-8")
    return f"{SITE}/tenders/"


def write_sitemaps(out, urls, today):
    sm = "".join(f"<url><loc>{esc(u)}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    (out / "tenders" / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    maps = [f"{SITE}/sitemap-home.xml", f"{SITE}/tenders/sitemap.xml"]
    if (out / "ai-index" / "sitemap.xml").exists():
        maps.append(f"{SITE}/ai-index/sitemap.xml")
    root = "".join(f"<sitemap><loc>{m}</loc><lastmod>{today}</lastmod></sitemap>" for m in maps)
    home = f"{SITE}/"
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{root}</sitemapindex>')
    (out / "sitemap-home.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{home}</loc><lastmod>{today}</lastmod></url></urlset>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE.parent.parent))
    ap.add_argument("--countries", nargs="*", default=list(COUNTRIES))
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    out = Path(a.out)
    today = dt.date.today()
    week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    stats, urls, failures = {}, [], []
    for code in a.countries:
        try:
            data = collect(code, today, a.days, log=lambda m: print(code, m, flush=True))
        except Exception as e:  # un pays en erreur ne bloque pas les autres
            print(code, "ERROR", e, flush=True)
            failures.append(code)
            continue
        stats[code] = dict(relaunch=len(data["relaunch"]), failed=len(data["failed"]))
        if code == "FRA":
            urls.append(render_country(out, code, data, today, week, "fr"))
            for sec in SECTORS:
                urls.append(render_country(out, code, data, today, week, "fr", sector=sec))
        else:
            urls.append(render_country(out, code, data, today, week, "en"))
        print(code, stats[code], flush=True)
    if not stats:
        raise SystemExit("no country could be built")
    urls.insert(0, render_hub(out, stats, today, week))
    write_sitemaps(out, urls, today.isoformat())
    (out / "tenders" / "stats.json").write_text(json.dumps(dict(date=today.isoformat(), stats=stats, failures=failures), indent=1))
    print("pages:", len(urls), "errors:", failures)


if __name__ == "__main__":
    main()
