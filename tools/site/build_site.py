"""Pages générales du site, dans toutes les langues : accueil (/, /fr/, /de/, …), tarifs (/pricing/, /de/pricing/, …), 404,
sitemap-home.xml.

python tools/site/build_site.py   (depuis la racine du dépôt ; aucune connexion réseau)
Textes : tools/site/i18n_site.py. Chiffres : tenders/stats.json. Liens de paiement : tools/alerts/config.json.
"""
import datetime as dt
import json
from pathlib import Path

from chrome import LANGS, MAIL, SITE, esc, exists, fmt_int, footer, header, hreflang_links, route
from i18n_site import HOME, PRICING

ROOT = Path(__file__).resolve().parents[2]
APIFY = dict(tenders="https://apify.com/jovianlabs/failed-public-tenders", ps="https://apify.com/jovianlabs/sem-tem-particle-size",
             po="https://apify.com/jovianlabs/porosity-analyzer", fi="https://apify.com/jovianlabs/fiber-diameter-analyzer")
ASIA = ("ja", "zh", "ko")
HOME_PATH = {l: ("/" if l == "en" else f"/{l}/") for l in LANGS}
PRICING_PATH = {l: ("/pricing/" if l == "en" else f"/{l}/pricing/") for l in LANGS}


def shell(lang, path, title, desc, body, active=None, jsonld=None, noindex=False, alternates=None,
          image="/assets/img/home-alerts.jpg"):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    rb = '<meta name="robots" content="noindex">' if noindex else ""
    canon = "" if noindex else f'<link rel="canonical" href="{SITE}{path}">'
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{canon}{hreflang_links(alternates)}{rb}'
            f'<link rel="icon" href="/assets/favicon.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">'
            f'<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{SITE}{image}">'
            f'<meta name="twitter:card" content="summary_large_image">'
            f'<link rel="stylesheet" href="/assets/style.css">{ld}</head><body>{header(lang, active, alternates)}<main>{body}</main>'
            f'{footer(lang)}</body></html>')


def write(path, text):
    out = ROOT / "404.html" if path == "/404" else ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def metro_link(tool, lang):
    p = f"/{lang}/metrology/{tool}/"
    return p if lang in ASIA and exists(p) else f"/metrology/{tool}/"


def home(lang, stats):
    t = HOME[lang]
    n = len(stats)
    r = fmt_int(sum(v["relaunch"] for v in stats.values()), lang)
    f = fmt_int(sum(v["failed"] for v in stats.values()), lang)
    links = dict(ps=metro_link("particle-size", lang), po=metro_link("porosity", lang), fi=metro_link("fiber-diameter", lang),
                 sc="/metrology/scale-check/")
    li = lambda items: "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
    alerts = f"""<div>
<div class="k">{esc(t['a_k'].format(n=n))}</div><h2>{esc(t['a_h'])}</h2><p>{esc(t['a_p'].format(f=f))}</p>
{li(esc(x) for x in t['a_li'])}<span class="price">{esc(t['a_price'])}</span>
<p><a class="btn pro" href="{route('alerts', lang)}">{esc(t['a_b1'])}</a><a class="btn ghost" href="{route('tenders', lang)}">{esc(t['a_b2'])}</a></p>
<p class="small">{esc(t['a_dev']).replace('{actor}', f'<a href="{APIFY["tenders"]}">{esc(t["actor"])}</a>')}</p>
</div><div class="media"><img src="/assets/img/home-alerts.jpg" width="760" height="640" alt="{esc(t['a_alt'])}" loading="lazy"></div>"""
    metro = f"""<div>
<div class="k">{esc(t['m_k'])}</div><h2>{esc(t['m_h'])}</h2><p>{esc(t['m_p'])}</p>
{li(x.format(**links) for x in t['m_li'])}<span class="price">{esc(t['m_price'])}</span>
<p><a class="btn pro" href="{route('metrology', lang)}">{esc(t['m_b1'])}</a><a class="btn ghost" href="/metrology/examples/particle-size-demo-report.pdf">{esc(t['m_b2'])}</a></p>
</div><div class="media"><img src="/assets/img/home-metrology.jpg" width="800" height="588" alt="{esc(t['m_alt'])}" loading="lazy"></div>"""
    ai = f"""<div>
<div class="k">{esc(t['i_k'])}</div><h2>{esc(t['i_h'])}</h2><p>{esc(t['i_p'])}</p><span class="price">{esc(t['i_price'])}</span>
<p><a class="btn pro" href="/ai-index/">{esc(t['i_b1'])}</a><a class="btn ghost" href="/ai-index/methodology/">{esc(t['i_b2'])}</a></p>
</div><div class="media"><img src="/assets/img/home-ai-index.jpg" width="948" height="482" alt="{esc(t['i_alt'])}" loading="lazy"></div>"""
    order = [metro, ai, alerts] if lang in ASIA else [alerts, metro, ai]
    sections = "".join(f'<section class="prod{" flip" if i % 2 else ""}">{s}</section>' for i, s in enumerate(order))
    if lang in ASIA:
        b1, b2 = (route("metrology", lang), t["b_alerts"]), (route("pricing", lang), t["b_metro"])
    else:
        b1, b2 = (route("alerts", lang), t["b_alerts"]), (route("metrology", lang), t["b_metro"])
    mail = f'<a href="mailto:{MAIL}">{MAIL}</a>'
    how = "".join(f"<div><b>{esc(a)}</b><p>{esc(b).replace('{mail}', mail)}</p></div>" for a, b in t["how"])
    body = f"""<section class="hero"><h1>{esc(t['h1'])}</h1><p class="lede">{esc(t['lede'])}</p>
<p><a class="btn pro" href="{b1[0]}">{esc(b1[1])}</a><a class="btn" href="{b2[0]}">{esc(b2[1])}</a></p>
<ul class="facts">{"".join(f"<li>{esc(x.format(n=n, r=r))}</li>" for x in t['facts'])}</ul></section>
{sections}
<h2>{esc(t['how_h'])}</h2><div class="how">{how}</div>
<p><a class="btn" href="{route('pricing', lang)}">{esc(t['all_prices'])}</a></p>"""
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": "Jovian Labs", "url": f"{SITE}/",
          "logo": f"{SITE}/assets/apple-touch-icon.png", "email": MAIL,
          "sameAs": ["https://apify.com/jovianlabs", "https://huggingface.co/jovianlabs"]}
    image = "/assets/img/home-metrology.jpg" if lang in ASIA else "/assets/img/home-alerts.jpg"
    write(HOME_PATH[lang], shell(lang, HOME_PATH[lang], t["title"], t["desc"], body, jsonld=ld, alternates=HOME_PATH, image=image))


def pricing(lang, cfg):
    t = PRICING[lang]
    links = cfg["checkout_links"]
    free, pro = links.get("free") or route("alerts", lang), links.get("pro") or route("alerts", lang)

    def plan(spec, href, best=False, primary=False):
        k, name, amt, per, items, btn = spec
        return (f'<div class="plan{" best" if best else ""}"><div class="k">{esc(k)}</div><h3>{esc(name)}</h3><div class="amt">{esc(amt)}</div>'
                f'<div class="per">{esc(per)}</div><ul>{"".join(f"<li>{esc(i)}</li>" for i in items)}</ul>'
                f'<p><a class="btn{" pro" if primary else ""}" href="{href}">{esc(btn)}</a></p></div>')
    alerts_block = (f'<h2>{esc(t["s_alerts"])}</h2><div class="plans">{plan(t["free"], free)}{plan(t["pro"], pro, True, True)}'
                    f'{plan(t["api"], APIFY["tenders"])}</div><p class="small">{t["note"].format(alerts=route("alerts", lang))}</p>')
    micro_block = (f'<h2>{esc(t["s_micro"])}</h2><div class="plans">{plan(t["ps"], APIFY["ps"], lang in ASIA, lang in ASIA)}'
                   f'{plan(t["po"], APIFY["po"])}{plan(t["fi"], APIFY["fi"])}{plan(t["sc"], "/metrology/scale-check/")}</div>')
    blocks = micro_block + alerts_block if lang in ASIA else alerts_block + micro_block
    mail = f'<a href="mailto:{MAIL}">{MAIL}</a>'
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in t["faq"])
    body = (f'<h1>{esc(t["h1"])}</h1><p class="lede">{esc(t["lede"])}</p>{blocks}'
            f'<h2>{esc(t["custom_h"])}</h2><div class="how"><div><b>{esc(t["custom_k"])}</b><p>{esc(t["custom_t"]).replace("{mail}", mail)}</p></div></div>'
            f'<h2>{esc(t["faq_h"])}</h2>{faq}')
    ld = {"@context": "https://schema.org", "@type": "Product", "name": "Second-chance tender alerts", "brand": "Jovian Labs",
          "description": "Weekly email alerts on failed and relaunched public procurement procedures in 16 EU countries.",
          "offers": [{"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "EUR", "url": f"{SITE}/alerts/"},
                     {"@type": "Offer", "name": "Pro", "price": "19.00", "priceCurrency": "EUR", "url": f"{SITE}/alerts/",
                      "priceSpecification": {"@type": "UnitPriceSpecification", "price": "19.00", "priceCurrency": "EUR",
                                             "unitText": "MONTH", "valueAddedTaxIncluded": False}}]}
    write(PRICING_PATH[lang], shell(lang, PRICING_PATH[lang], t["title"], t["desc"], body, active="pricing", jsonld=ld,
                                    alternates=PRICING_PATH))


def not_found():
    body = ('<h1>Page not found</h1><p class="lede">This page does not exist or has moved.</p>'
            '<p><a class="btn pro" href="/">Home</a><a class="btn" href="/alerts/">Tender alerts</a>'
            '<a class="btn" href="/metrology/">Image analysis</a><a class="btn" href="/pricing/">Pricing</a></p>')
    write("/404", shell("en", "/404", "Page not found · Jovian Labs", "Page not found.", body, noindex=True))


def sitemap_home(today):
    paths = list(HOME_PATH.values()) + list(PRICING_PATH.values())
    urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>" for p in paths)
    (ROOT / "sitemap-home.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')


def main():
    stats = json.loads((ROOT / "tenders" / "stats.json").read_text())["stats"]
    cfg = json.loads((ROOT / "tools" / "alerts" / "config.json").read_text())
    for _ in range(2):  # 2 passes: les liens vers les pages traduites n'existent qu'après la 1re écriture
        for lang in LANGS:
            home(lang, stats)
            pricing(lang, cfg)
    not_found()
    sitemap_home(dt.date.today().isoformat())
    print("site pages:", ", ".join(HOME_PATH.values()), "+ pricing, 404, sitemap-home.xml")


if __name__ == "__main__":
    main()
