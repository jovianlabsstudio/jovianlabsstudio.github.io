"""En-tête, menu, choix de langue et pied de page communs à toutes les pages du site.

Chaque générateur importe ce module : le menu reste identique partout.
  sys.path.insert(0, str(ROOT / "tools" / "site")); from chrome import header, footer, hreflang_links
Langues : anglais par défaut ; au premier passage, la page bascule vers la langue du navigateur si elle existe pour cette page ;
le choix fait dans le menu de langue est retenu (localStorage) et peut toujours être changé.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://jovianlabsstudio.com"
MAIL = "contact@jovianlabsstudio.com"
LANGS = ["en", "fr", "de", "es", "it", "ja", "zh", "ko"]
LANG_NAMES = {"en": "English", "fr": "Français", "de": "Deutsch", "es": "Español", "it": "Italiano",
              "ja": "日本語", "zh": "中文", "ko": "한국어"}

# Adresse de chaque rubrique par langue ; une langue absente retombe sur l'anglais.
ROUTES = {
    "home": {l: ("/" if l == "en" else f"/{l}/") for l in LANGS},
    "pricing": {l: ("/pricing/" if l == "en" else f"/{l}/pricing/") for l in LANGS},
    "alerts": {"en": "/alerts/", "fr": "/fr/alertes/", "de": "/de/alerts/", "es": "/es/alerts/", "it": "/it/alerts/"},
    "tenders": {"en": "/tenders/", "fr": "/tenders/france/", "de": "/de/tenders/germany/", "es": "/es/tenders/spain/",
                "it": "/it/tenders/italy/"},
    "metrology": {"en": "/metrology/", "ja": "/ja/metrology/", "zh": "/zh/metrology/", "ko": "/ko/metrology/"},
    "ai-index": {"en": "/ai-index/"},
    "scale-check": {"en": "/metrology/scale-check/"},
    "games": {"en": "/games/", "fr": "/fr/jeux/"},
}
NAV_ORDER = ["tenders", "alerts", "metrology", "ai-index", "games", "pricing"]
NAV_LABELS = {
    "en": {"tenders": "Tenders", "alerts": "Alerts", "metrology": "Metrology", "ai-index": "AI Index", "games": "Games", "pricing": "Pricing"},
    "fr": {"tenders": "Appels d'offres", "alerts": "Alertes", "metrology": "Métrologie", "ai-index": "Index IA", "games": "Jeux", "pricing": "Tarifs"},
    "de": {"tenders": "Ausschreibungen", "alerts": "E-Mail-Alerts", "metrology": "Bildanalyse", "ai-index": "KI-Index", "games": "Spiele", "pricing": "Preise"},
    "es": {"tenders": "Licitaciones", "alerts": "Alertas", "metrology": "Metrología", "ai-index": "Índice IA", "games": "Juegos", "pricing": "Precios"},
    "it": {"tenders": "Gare", "alerts": "Avvisi", "metrology": "Metrologia", "ai-index": "Indice IA", "games": "Giochi", "pricing": "Prezzi"},
    "ja": {"tenders": "入札", "alerts": "アラート", "metrology": "画像計測", "ai-index": "AIインデックス", "games": "ゲーム", "pricing": "料金"},
    "zh": {"tenders": "招标", "alerts": "提醒", "metrology": "图像测量", "ai-index": "AI 指数", "games": "游戏", "pricing": "价格"},
    "ko": {"tenders": "입찰", "alerts": "알림", "metrology": "이미지 계측", "ai-index": "AI 지수", "games": "게임", "pricing": "가격"},
}

FOOT = {
    "en": dict(products="Products", free="Free", lang="Language",
               tagline="Small, reliable data tools. Every number comes with its method and, where it matters, its uncertainty.",
               links=[("alerts", "Tender alerts"), ("tenders", "Second-chance tenders"), ("metrology", "Microscope image analysis"),
                      ("pricing", "Pricing")],
               free_links=[("scale-check", "SEM scale-bar check"), ("ai-index", "AI Recommendation Index"), ("games", "Puzzle games")],
               legal="Independent; not affiliated with the EU Publications Office, DILA, Apify, Polar, Google or Perplexity."),
    "fr": dict(products="Produits", free="Gratuit", lang="Langue",
               tagline="De petits outils de données fiables. Chaque chiffre vient avec sa méthode et, quand ça compte, son incertitude.",
               links=[("alerts", "Alertes appels d'offres"), ("tenders", "Appels d'offres relancés"),
                      ("metrology", "Analyse d'images de microscopie"), ("pricing", "Tarifs")],
               free_links=[("scale-check", "Contrôle de barre d'échelle MEB"), ("ai-index", "Index des recommandations IA"), ("games", "Jeux de réflexion")],
               legal="Indépendant ; sans lien avec l'Office des publications de l'UE, la DILA, Apify, Polar, Google ou Perplexity."),
    "de": dict(products="Produkte", free="Kostenlos", lang="Sprache",
               tagline="Kleine, zuverlässige Datenwerkzeuge. Jede Zahl kommt mit ihrer Methode und, wo es zählt, mit ihrer Unsicherheit.",
               links=[("alerts", "Ausschreibungs-Alerts"), ("tenders", "Aufgehobene und neu ausgeschriebene Vergaben"),
                      ("metrology", "Mikroskopie-Bildanalyse"), ("pricing", "Preise")],
               free_links=[("scale-check", "REM-Maßstabsprüfung"), ("ai-index", "KI-Empfehlungsindex"), ("games", "Denkspiele")],
               legal="Unabhängig; nicht verbunden mit dem Amt für Veröffentlichungen der EU, DILA, Apify, Polar, Google oder Perplexity."),
    "es": dict(products="Productos", free="Gratis", lang="Idioma",
               tagline="Pequeñas herramientas de datos fiables. Cada cifra llega con su método y, cuando importa, con su incertidumbre.",
               links=[("alerts", "Alertas de licitaciones"), ("tenders", "Licitaciones desiertas y relanzadas"),
                      ("metrology", "Análisis de imágenes de microscopía"), ("pricing", "Precios")],
               free_links=[("scale-check", "Comprobación de barra de escala SEM"), ("ai-index", "Índice de recomendaciones IA"), ("games", "Juegos de lógica")],
               legal="Independiente; sin relación con la Oficina de Publicaciones de la UE, la DILA, Apify, Polar, Google ni Perplexity."),
    "it": dict(products="Prodotti", free="Gratis", lang="Lingua",
               tagline="Piccoli strumenti di dati affidabili. Ogni numero arriva con il suo metodo e, quando conta, con la sua incertezza.",
               links=[("alerts", "Avvisi sulle gare"), ("tenders", "Gare deserte e ripubblicate"),
                      ("metrology", "Analisi di immagini al microscopio"), ("pricing", "Prezzi")],
               free_links=[("scale-check", "Controllo della barra di scala SEM"), ("ai-index", "Indice delle raccomandazioni IA"), ("games", "Giochi di logica")],
               legal="Indipendente; nessun legame con l'Ufficio delle pubblicazioni dell'UE, la DILA, Apify, Polar, Google o Perplexity."),
    "ja": dict(products="製品", free="無料", lang="言語",
               tagline="小さく、信頼できるデータツール。すべての数値に手法を、必要な場合は不確かさを添えます。",
               links=[("metrology", "顕微鏡画像解析"), ("alerts", "入札アラート（EU）"), ("tenders", "不調・再公告の入札（EU）"),
                      ("pricing", "料金")],
               free_links=[("scale-check", "SEM スケールバー確認ツール"), ("ai-index", "AI 推薦インデックス"), ("games", "パズルゲーム")],
               legal="独立運営。EU 出版局、DILA、Apify、Polar、Google、Perplexity とは関係ありません。"),
    "zh": dict(products="产品", free="免费", lang="语言",
               tagline="小而可靠的数据工具。每个数字都附有方法，必要时附有不确定度。",
               links=[("metrology", "显微图像分析"), ("alerts", "招标提醒（欧盟）"), ("tenders", "流标与重新招标（欧盟）"),
                      ("pricing", "价格")],
               free_links=[("scale-check", "SEM 比例尺检查工具"), ("ai-index", "AI 推荐指数"), ("games", "益智游戏")],
               legal="独立运营；与欧盟出版办公室、DILA、Apify、Polar、Google 或 Perplexity 无关联。"),
    "ko": dict(products="제품", free="무료", lang="언어",
               tagline="작고 믿을 수 있는 데이터 도구. 모든 수치에 방법을, 필요한 경우 불확도를 함께 제공합니다.",
               links=[("metrology", "현미경 이미지 분석"), ("alerts", "입찰 알림 (EU)"), ("tenders", "유찰·재공고 입찰 (EU)"),
                      ("pricing", "가격")],
               free_links=[("scale-check", "SEM 스케일 바 확인 도구"), ("ai-index", "AI 추천 지수"), ("games", "퍼즐 게임")],
               legal="독립 운영; EU 출판국, DILA, Apify, Polar, Google, Perplexity와 관련이 없습니다."),
}

GLOBE = ('<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8">'
         '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.9 5.8 3.9 9s-1.3 6.2-3.9 9c-2.6-2.8-3.9-5.8-3.9-9S9.4 5.8 12 3z"/></svg>')

# Bascule automatique vers la langue du navigateur au premier passage (seulement si cette page existe dans cette langue),
# puis respect du choix fait dans le menu. La bascule automatique ne part que des pages anglaises : une page traduite n'est
# jamais redirigée vers l'anglais sans choix explicite (sinon Google, qui lit en anglais, ne l'indexerait pas).
AUTO = """<script>(function(){try{var A=%s,c=document.documentElement.lang,s=null;try{s=localStorage.getItem('jl_lang')}catch(e){}
if(s){if(s!==c&&A[s])location.replace(A[s]);}else if(c==='en'){var L=navigator.languages||[navigator.language||''];
for(var i=0;i<L.length;i++){var l=(L[i]||'').slice(0,2).toLowerCase();if(l===c)break;if(A[l]){location.replace(A[l]);break;}}}
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-lang]');
if(a){try{localStorage.setItem('jl_lang',a.getAttribute('data-lang'))}catch(e){}}});}catch(e){}})();</script>"""


def esc(s):
    return html.escape(str(s), quote=True)


def exists(path):
    """Vrai si la page existe déjà dans le dépôt (une traduction pas encore générée retombe sur l'anglais)."""
    return (ROOT / path.strip("/") / "index.html").exists() if path != "/" else True


def route(key, lang):
    r = ROUTES[key]
    p = r.get(lang)
    return p if p and exists(p) else r["en"]


def nav_label(key, lang):
    return NAV_LABELS.get(lang, NAV_LABELS["en"])[key]


def header(lang="en", active=None, alternates=None):
    """alternates : {"en": "/alerts/", "fr": "/fr/alertes/", ...} versions de CETTE page dans d'autres langues."""
    alternates = dict(alternates or {})
    alternates.setdefault(lang, None)
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{route(k, lang)}"{_cls(k, active)}{cur if k == active else ""}>{esc(nav_label(k, lang))}</a>'
                    for k in NAV_ORDER)
    items = []
    for code in LANGS:
        href = alternates.get(code) or route("home", code)
        if not exists(href):
            href = "/"
        on = ' class="on"' if code == lang else ""
        items.append(f'<a href="{href}" hreflang="{code}" lang="{code}" data-lang="{code}"{on}>{esc(LANG_NAMES[code])}</a>')
    menu = (f'<details class="langmenu"><summary aria-label="{esc(FOOT.get(lang, FOOT["en"])["lang"])}">{GLOBE}'
            f'<span>{lang.upper()}</span></summary><div>{"".join(items)}</div></details>')
    auto_map = {c: h for c, h in alternates.items() if h}
    script = AUTO % json.dumps(auto_map) if len(auto_map) > 1 else AUTO % "{}"
    return (f'{script}<header class="site"><a class="brand" href="{route("home", lang)}"><img src="/assets/logo.svg" alt="" width="30" height="30">'
            f'Jovian Labs</a><nav aria-label="Main">{links}</nav>{menu}</header>')


def _cls(key, active):
    c = []
    if key == active:
        c.append("on")
    if key == "alerts":
        c.append("navcta")
    return f' class="{" ".join(c)}"' if c else ""


def footer(lang="en", extra=""):
    t = FOOT.get(lang, FOOT["en"])
    col = lambda title, links: (f"<div><b>{esc(title)}</b>" + "".join(f'<a href="{route(k, lang)}">{esc(l)}</a>' for k, l in links) + "</div>")
    langs = " · ".join(f'<a href="{route("home", c)}" lang="{c}" data-lang="{c}">{esc(LANG_NAMES[c])}</a>' for c in LANGS)
    return (f'<footer class="site"><div class="fgrid"><div><b>Jovian Labs</b><p>{esc(t["tagline"])}</p>'
            f'<p><a href="mailto:{MAIL}">{MAIL}</a></p></div>{col(t["products"], t["links"])}{col(t["free"], t["free_links"])}</div>'
            f'<p class="small langs-foot">{esc(t["lang"])} : {langs}</p>'
            f'{f"<p class=small>{extra}</p>" if extra else ""}<p class="small">© 2026 Jovian Labs. {esc(t["legal"])}</p></footer>')


def hreflang_links(alternates):
    alts = {c: h for c, h in (alternates or {}).items() if h}
    if len(alts) < 2:
        return ""
    out = "".join(f'<link rel="alternate" hreflang="{c}" href="{SITE}{h}">' for c, h in alts.items())
    if "en" in alts:
        out += f'<link rel="alternate" hreflang="x-default" href="{SITE}{alts["en"]}">'
    return out


def fmt_int(n, lang):
    s = f"{n:,}"
    return {"fr": s.replace(",", " "), "de": s.replace(",", "."), "es": s.replace(",", "."), "it": s.replace(",", ".")}.get(lang, s)
