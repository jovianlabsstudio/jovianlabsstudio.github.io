"""En-tête, menu et pied de page communs à toutes les pages du site (accueil, tarifs, appels d'offres, alertes,
métrologie, index IA). Chaque générateur importe ce module : le menu reste identique partout.

Usage : sys.path.insert(0, str(ROOT / "tools" / "site")); from chrome import header, footer
"""
import html

SITE = "https://jovianlabsstudio.com"
MAIL = "contact@jovianlabsstudio.com"

# (clé, lien, libellé) par langue. Une langue absente retombe sur l'anglais.
NAV = {
    "en": [("tenders", "/tenders/", "Tenders"), ("alerts", "/alerts/", "Alerts"), ("metrology", "/metrology/", "Metrology"),
           ("ai-index", "/ai-index/", "AI Index"), ("pricing", "/pricing/", "Pricing")],
    "fr": [("tenders", "/tenders/france/", "Appels d'offres"), ("alerts", "/fr/alertes/", "Alertes"),
           ("metrology", "/metrology/", "Métrologie"), ("ai-index", "/ai-index/", "Index IA"), ("pricing", "/pricing/", "Tarifs")],
}
LANG_NAMES = {"en": "English", "fr": "Français", "de": "Deutsch", "es": "Español", "it": "Italiano",
              "ja": "日本語", "zh": "中文", "ko": "한국어"}

FOOT = {
    "en": dict(products="Products", free="Free", company="Jovian Labs",
               tagline="Small, reliable data tools. Every number comes with its method and, where it matters, its uncertainty.",
               links=[("/alerts/", "Tender alerts"), ("/tenders/", "Second-chance tenders"), ("/metrology/", "Microscopy image analysis"),
                      ("/pricing/", "Pricing")],
               free_links=[("/metrology/scale-check/", "SEM scale-bar check"), ("/ai-index/", "AI Recommendation Index"),
                           ("/metrology/eu-nanomaterial-definition/", "EU nanomaterial definition guide")],
               legal="Independent; not affiliated with the EU Publications Office, DILA, Apify, Polar, Google or Perplexity."),
    "fr": dict(products="Produits", free="Gratuit", company="Jovian Labs",
               tagline="De petits outils de données fiables. Chaque chiffre vient avec sa méthode et, quand ça compte, son incertitude.",
               links=[("/fr/alertes/", "Alertes appels d'offres"), ("/tenders/france/", "Appels d'offres relancés"),
                      ("/metrology/", "Analyse d'images de microscopie"), ("/pricing/", "Tarifs")],
               free_links=[("/metrology/scale-check/", "Contrôle de barre d'échelle MEB"), ("/ai-index/", "Index des recommandations IA"),
                           ("/metrologie/definition-nanomateriau-ue/", "Guide de la définition UE des nanomatériaux")],
               legal="Indépendant ; sans lien avec l'Office des publications de l'UE, la DILA, Apify, Polar, Google ou Perplexity."),
}


def esc(s):
    return html.escape(str(s), quote=True)


def header(lang="en", active=None, alternates=None):
    """alternates : {"en": "/alerts/", "fr": "/fr/alertes/"} pour afficher le choix de langue."""
    items = NAV.get(lang, NAV["en"])
    cur = ' aria-current="page"'
    on = ' class="on"'
    links = "".join(f'<a href="{href}"{_cls(key, active)}{cur if key == active else ""}>{esc(label)}</a>'
                    for key, href, label in items)
    langs = ""
    if alternates and len(alternates) > 1:
        langs = '<div class="langs">' + "".join(
            f'<a href="{href}" hreflang="{code}" lang="{code}" title="{esc(LANG_NAMES.get(code, code))}"{on if code == lang else ""}>'
            f'{code.upper()}</a>' for code, href in alternates.items()) + "</div>"
    return (f'<header class="site"><a class="brand" href="/"><img src="/assets/logo.svg" alt="" width="30" height="30">Jovian Labs</a>'
            f'<nav aria-label="Main">{links}</nav>{langs}</header>')


def _cls(key, active):
    c = []
    if key == active:
        c.append("on")
    if key == "alerts":
        c.append("navcta")
    return f' class="{" ".join(c)}"' if c else ""


def footer(lang="en", extra=""):
    t = FOOT.get(lang, FOOT["en"])
    col = lambda title, links: (f"<div><b>{esc(title)}</b>" + "".join(f'<a href="{h}">{esc(l)}</a>' for h, l in links) + "</div>")
    return (f'<footer class="site"><div class="fgrid"><div><b>{esc(t["company"])}</b><p>{esc(t["tagline"])}</p>'
            f'<p><a href="mailto:{MAIL}">{MAIL}</a></p></div>{col(t["products"], t["links"])}{col(t["free"], t["free_links"])}</div>'
            f'{f"<p class=small>{extra}</p>" if extra else ""}<p class="small">© 2026 Jovian Labs. {esc(t["legal"])}</p></footer>')


def hreflang_links(alternates):
    if not alternates or len(alternates) < 2:
        return ""
    out = "".join(f'<link rel="alternate" hreflang="{c}" href="{SITE}{h}">' for c, h in alternates.items())
    if "en" in alternates:
        out += f'<link rel="alternate" hreflang="x-default" href="{SITE}{alternates["en"]}">'
    return out
