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


# Bloc « Jeux » de l'accueil (les pages des jeux existent en anglais et en français ; les autres langues renvoient à l'anglais).
GAMES_HOME = {
    "en": dict(k="Games", h="Puzzle games by Jovian Labs", p="Short, honest puzzle games that run in any browser: nothing to download, no sign-up, and no difficulty tricks to sell ads. The newest, Monster Steps, is a turn-based Halloween escape in 33 levels.", b1="See our games", alt="Covers of Monster Steps, Counterpoise and Equipoise"),
    "fr": dict(k="Jeux", h="Les jeux de réflexion Jovian Labs", p="Des puzzles courts et honnêtes, jouables dans n'importe quel navigateur : rien à télécharger, pas d'inscription, aucune difficulté truquée pour vendre des pubs. Le dernier, Monster Steps, est une évasion d'Halloween au tour par tour en 33 niveaux.", b1="Voir nos jeux", alt="Couvertures de Monster Steps, Counterpoise et Equipoise"),
    "de": dict(k="Spiele", h="Denkspiele von Jovian Labs", p="Kurze, faire Puzzlespiele für jeden Browser: kein Download, keine Anmeldung und keine versteckten Schwierigkeitstricks für mehr Werbung. Das neueste, Monster Steps, ist eine rundenbasierte Halloween-Flucht mit 33 Levels.", b1="Zu unseren Spielen", alt="Cover von Monster Steps, Counterpoise und Equipoise"),
    "es": dict(k="Juegos", h="Juegos de lógica de Jovian Labs", p="Puzles cortos y honestos que funcionan en cualquier navegador: sin descargas, sin registro y sin trucos de dificultad para vender anuncios. El más nuevo, Monster Steps, es una huida de Halloween por turnos con 33 niveles.", b1="Ver nuestros juegos", alt="Portadas de Monster Steps, Counterpoise y Equipoise"),
    "it": dict(k="Giochi", h="I giochi di logica di Jovian Labs", p="Puzzle brevi e onesti che funzionano in qualsiasi browser: niente da scaricare, nessuna registrazione e nessun trucco sulla difficoltà per vendere pubblicità. L'ultimo, Monster Steps, è una fuga di Halloween a turni in 33 livelli.", b1="Scopri i nostri giochi", alt="Copertine di Monster Steps, Counterpoise ed Equipoise"),
    "ja": dict(k="ゲーム", h="Jovian Labs のパズルゲーム", p="ブラウザですぐ遊べる、短くて誠実なパズルゲーム。ダウンロードも登録も不要で、広告のために難易度を操作することもありません。最新作「Monster Steps」は全33ステージのターン制ハロウィン脱出パズルです。", b1="ゲーム一覧へ", alt="Monster Steps、Counterpoise、Equipoise のカバー画像"),
    "zh": dict(k="游戏", h="Jovian Labs 益智游戏", p="简短而诚实的益智游戏，任何浏览器都能玩：无需下载，无需注册，也不会为了卖广告暗中调整难度。最新作品《Monster Steps》是一款共 33 关的回合制万圣节逃脱解谜游戏。", b1="查看我们的游戏", alt="Monster Steps、Counterpoise 和 Equipoise 的封面"),
    "ko": dict(k="게임", h="Jovian Labs 퍼즐 게임", p="어떤 브라우저에서나 바로 즐기는 짧고 정직한 퍼즐 게임입니다. 다운로드도 가입도 필요 없고, 광고를 위해 난이도를 조작하지도 않습니다. 최신작 Monster Steps는 33개 레벨의 턴제 핼러윈 탈출 퍼즐입니다.", b1="게임 보기", alt="Monster Steps, Counterpoise, Equipoise 커버 이미지"),
}
MS_PAGE = {"en": "/games/monster-steps/", "fr": "/fr/jeux/monster-steps/"}


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
    g = GAMES_HOME[lang]
    games = f"""<div>
<div class="k">{esc(g['k'])}</div><h2>{esc(g['h'])}</h2><p>{esc(g['p'])}</p>
<p><a class="btn pro" href="{route('games', lang)}">{esc(g['b1'])}</a><a class="btn ghost" href="{MS_PAGE.get(lang, MS_PAGE['en'])}">Monster Steps</a></p>
</div><div class="media"><img src="/assets/img/home-games.jpg" width="800" height="681" alt="{esc(g['alt'])}" loading="lazy"></div>"""
    order = [metro, ai, alerts, games] if lang in ASIA else [alerts, metro, ai, games]
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
