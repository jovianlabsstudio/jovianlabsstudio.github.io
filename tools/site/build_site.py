"""Pages générales du site : accueil (/), tarifs (/pricing/), page 404, sitemap-home.xml.

python tools/site/build_site.py   (depuis la racine du dépôt ; aucune connexion réseau)
Les chiffres viennent de tenders/stats.json ; les liens de paiement de tools/alerts/config.json.
"""
import datetime as dt
import json
from pathlib import Path

from chrome import MAIL, SITE, esc, footer, header

ROOT = Path(__file__).resolve().parents[2]
APIFY = dict(tenders="https://apify.com/jovianlabs/failed-public-tenders", ps="https://apify.com/jovianlabs/sem-tem-particle-size",
             po="https://apify.com/jovianlabs/porosity-analyzer", fi="https://apify.com/jovianlabs/fiber-diameter-analyzer")


def shell(path, title, desc, body, active=None, jsonld=None, noindex=False, image="/assets/img/home-alerts.jpg"):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    rb = '<meta name="robots" content="noindex">' if noindex else ""
    canon = "" if noindex else f'<link rel="canonical" href="{SITE}{path}">'
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">'
            f'{canon}{rb}'
            f'<link rel="icon" href="/assets/favicon.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">'
            f'<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{SITE}{image}">'
            f'<meta name="twitter:card" content="summary_large_image">'
            f'<link rel="stylesheet" href="/assets/style.css">{ld}</head><body>{header("en", active)}<main>{body}</main>{footer("en")}'
            f'</body></html>')


def write(path, text):
    out = ROOT / path.strip("/") / "index.html" if path != "/404" else ROOT / "404.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def home(stats):
    r = sum(v["relaunch"] for v in stats.values())
    f = sum(v["failed"] for v in stats.values())
    n = len(stats)
    body = f"""<section class="hero">
<h1>Data tools that find what others miss.</h1>
<p class="lede">Jovian Labs turns official data and microscope images into answers you can act on: which public contracts are
coming back with fewer bidders, how big the particles in an image really are, and which businesses AI assistants recommend.
Every number comes with its method and, where it matters, its uncertainty.</p>
<p><a class="btn pro" href="/alerts/">Get tender alerts, free</a><a class="btn" href="/metrology/">Analyse microscope images</a></p>
<ul class="facts"><li>{n} EU countries checked every week</li><li>{r:,} open calls relaunching a failed procedure right now</li>
<li>Methods validated on images with known truth</li><li>No account needed</li></ul>
</section>

<section class="prod">
<div>
<div class="k">Public procurement · {n} EU countries</div>
<h2>Second-chance tender alerts</h2>
<p>Every month, about {f:,} public procurement procedures in Europe end without a winner: nobody bid, or every bid was rejected.
Most come back, often with fewer competitors, and the buyer is sometimes allowed to negotiate directly. We find them and email you
the ones in your country and sector every Monday.</p>
<ul><li>Open calls that relaunch a failed procedure, with buyer and deadline</li>
<li>Procedures that failed this week, so you can contact the buyer early</li>
<li>Filters by country, sector and keywords; CSV file on Pro</li></ul>
<span class="price">Free · Pro €19 / month + VAT</span>
<p><a class="btn pro" href="/alerts/">Start free</a><a class="btn ghost" href="/tenders/">See this week's list</a></p>
<p class="small">Developers: the same data on demand through our <a href="{APIFY['tenders']}">Apify Actor</a>, $0.02 per result.</p>
</div>
<div class="media"><img src="/assets/img/home-alerts.jpg" width="760" height="640" alt="A Pro alert email listing open calls in Germany that relaunch failed procedures"></div>
</section>

<section class="prod flip">
<div>
<div class="k">Materials imaging · SEM, TEM, optical</div>
<h2>Microscope image analysis, with the uncertainty attached</h2>
<p>Send microscope images, get a measurement you can file: statistics with 95% confidence intervals, automatic quality checks,
a control image showing exactly what was measured, and a PDF report. No software to install.</p>
<ul><li><a href="/metrology/particle-size/">Particle size and EU nanomaterial screening</a></li>
<li><a href="/metrology/porosity/">Porosity of polished cross-sections</a> (additive manufacturing, castings, coatings)</li>
<li><a href="/metrology/fiber-diameter/">Fiber diameter</a> of electrospun mats and filters</li>
<li>Free: <a href="/metrology/scale-check/">check the scale bar and pixel size</a> of a whole folder, in your browser</li></ul>
<span class="price">$1 per image · free demo run</span>
<p><a class="btn pro" href="/metrology/">See the tools</a><a class="btn ghost" href="/metrology/examples/particle-size-demo-report.pdf">Example report (PDF)</a></p>
</div>
<div class="media"><img src="/assets/img/home-metrology.jpg" width="800" height="588" alt="Detected particles, pores and fibers on synthetic microscope images" loading="lazy"></div>
</section>

<section class="prod">
<div>
<div class="k">AI search · US cities</div>
<h2>AI Recommendation Index</h2>
<p>When someone asks an AI assistant for “the best plumber in Austin”, which businesses come up? We ask the same questions every
week, several times each, and publish who gets named, with confidence intervals and the sources the assistant cites.</p>
<span class="price">Free to read</span>
<p><a class="btn pro" href="/ai-index/">Read the index</a><a class="btn ghost" href="/ai-index/methodology/">Methodology</a></p>
</div>
<div class="media"><img src="/assets/img/home-ai-index.jpg" width="948" height="482" alt="Table of plumbers named by an AI assistant in Austin with confidence intervals" loading="lazy"></div>
</section>

<h2>How buying works</h2>
<div class="how">
<div><b>No account with us</b><p>Alerts are paid through Polar, our merchant of record: card payment, VAT handled, cancel in one click.</p></div>
<div><b>Pay per use for tools</b><p>Image analysis and tender data run on Apify. You pay only for what you process; demo runs are free.</p></div>
<div><b>Methods in the open</b><p>Every page explains how the numbers are made. Demo images are synthetic, so their true values are known.</p></div>
<div><b>Custom work</b><p>A signed report, another country, a bulk dataset? Write to <a href="mailto:{MAIL}">{MAIL}</a>.</p></div>
</div>
<p><a class="btn" href="/pricing/">See all prices</a></p>"""
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": "Jovian Labs", "url": f"{SITE}/",
          "logo": f"{SITE}/assets/apple-touch-icon.png", "email": MAIL,
          "sameAs": ["https://apify.com/jovianlabs", "https://huggingface.co/jovianlabs"]}
    write("/", shell("/", "Jovian Labs · Tender alerts, microscope image analysis and AI search data",
                     "Weekly alerts on failed and relaunched public tenders in 16 EU countries, microscope image analysis with confidence "
                     "intervals (particle size, nanomaterial screening, porosity, fiber diameter), and the AI Recommendation Index.",
                     body, jsonld=ld))


def pricing(cfg):
    links = cfg["checkout_links"]
    free, pro = links.get("free") or "/alerts/", links.get("pro") or "/alerts/"
    plan = lambda cls, k, name, amt, per, items, btn: (
        f'<div class="plan{cls}"><div class="k">{esc(k)}</div><h3>{esc(name)}</h3><div class="amt">{amt}</div><div class="per">{esc(per)}</div>'
        f'<ul>{"".join(f"<li>{i}</li>" for i in items)}</ul><p>{btn}</p></div>')
    body = f"""<h1>Pricing</h1>
<p class="lede">Simple prices and no account with us. Subscriptions are handled by Polar, our merchant of record (card payment, VAT,
receipts, cancellation). The analysis tools run on Apify and are billed per use.</p>

<h2>Second-chance tender alerts</h2>
<div class="plans">
{plan("", "Weekly email", "Free", "€0", "every Monday", ["The 5 most urgent open calls that relaunch a failed procedure", "Your country and sector", "Count of procedures that failed this week"], f'<a class="btn" href="{free}">Start free</a>')}
{plan(" best", "Weekly email", "Pro", "€19", "per month + VAT · cancel anytime", ["All open calls that relaunch a failed procedure", "All procedures that failed this week, with the reason", "Deadlines within 14 days", "CSV file attached", "Filters by country, sector and keywords"], f'<a class="btn pro" href="{pro}">Go Pro</a>')}
{plan("", "Data on demand", "Tenders API", "$0.02", "per opportunity · pay as you go", ["Same data on demand or on a schedule", "Export to CSV, Excel, JSON, Google Sheets", "Callable from code and AI agents"], f'<a class="btn" href="{APIFY["tenders"]}">Open on Apify</a>')}
</div>
<p class="small">You choose your country, sector and email language at checkout. Want to set them first? Use the
<a href="/alerts/">alerts page</a> (<a href="/fr/alertes/">version française</a>).</p>

<h2>Microscope image analysis</h2>
<div class="plans">
{plan("", "SEM / TEM", "Particle size & nano screening", "$1", "per image · demo free", ["D10, D50, D90 with 95% confidence intervals", "EU nanomaterial criterion (a) verdict", "Quality checks, control image, PDF report"], f'<a class="btn" href="{APIFY["ps"]}">Run on Apify</a>')}
{plan("", "Metallography", "Porosity", "$1", "per image · demo free", ["Area porosity with confidence interval and %RA", "Pore sizes, largest pores, pore types", "Control image and PDF report"], f'<a class="btn" href="{APIFY["po"]}">Run on Apify</a>')}
{plan("", "SEM · electrospinning", "Fiber diameter", "$1", "per image · demo free", ["Width at half maximum across each fiber", "Length-weighted distribution with confidence interval", "Beads and alignment index"], f'<a class="btn" href="{APIFY["fi"]}">Run on Apify</a>')}
{plan("", "In your browser", "Scale-bar & pixel-size check", "Free", "images never leave your computer", ["Reads Zeiss and Thermo Fisher metadata", "Measures the scale bar and cross-checks it", "Exports images with a clean scale bar"], '<a class="btn" href="/metrology/scale-check/">Open the tool</a>')}
</div>

<h2>Custom work</h2>
<div class="how"><div><b>On request</b><p>A report reviewed and signed by a materials imaging scientist, other countries for the alerts, a bulk
dataset or an integration: write to <a href="mailto:{MAIL}">{MAIL}</a> for a quote.</p></div></div>

<h2>Questions</h2>
<details><summary>How do I pay?</summary><p>Alerts: by card on Polar's secure checkout; we never see your card. Analysis tools: through your
Apify account, which bills per use.</p></details>
<details><summary>Is VAT included?</summary><p>Prices are shown before VAT. Polar adds the VAT of your country at checkout; businesses can
enter their VAT number there.</p></details>
<details><summary>Which currency will I see?</summary><p>Euros in Europe. Elsewhere, Polar may show the Pro plan in US dollars ($22 per month).</p></details>
<details><summary>How do I cancel?</summary><p>From the link at the bottom of every alert email (customer portal), in one click.</p></details>
<details><summary>Is the image analysis an accredited measurement?</summary><p>No. It is automated image analysis with its uncertainty
stated, not an ISO/IEC 17025 accredited measurement.</p></details>"""
    ld = {"@context": "https://schema.org", "@type": "Product", "name": "Second-chance tender alerts", "brand": "Jovian Labs",
          "description": "Weekly email alerts on failed and relaunched public procurement procedures in 16 EU countries.",
          "offers": [{"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "EUR", "url": f"{SITE}/alerts/"},
                     {"@type": "Offer", "name": "Pro", "price": "19.00", "priceCurrency": "EUR", "url": f"{SITE}/alerts/",
                      "priceSpecification": {"@type": "UnitPriceSpecification", "price": "19.00", "priceCurrency": "EUR",
                                             "unitText": "MONTH", "valueAddedTaxIncluded": False}}]}
    write("/pricing/", shell("/pricing/", "Pricing · Jovian Labs",
                             "Prices for second-chance tender alerts (Free, Pro €19/month), the tenders API and microscope image analysis "
                             "($1 per image, free demo).", body, active="pricing", jsonld=ld))


def not_found():
    body = ('<h1>Page not found</h1><p class="lede">This page does not exist or has moved.</p>'
            '<p><a class="btn pro" href="/">Home</a><a class="btn" href="/alerts/">Tender alerts</a>'
            '<a class="btn" href="/metrology/">Image analysis</a><a class="btn" href="/pricing/">Pricing</a></p>')
    write("/404", shell("/404", "Page not found · Jovian Labs", "Page not found.", body, noindex=True))


def sitemap_home(today):
    urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>" for p in ("/", "/pricing/"))
    (ROOT / "sitemap-home.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')


def main():
    stats = json.loads((ROOT / "tenders" / "stats.json").read_text())["stats"]
    cfg = json.loads((ROOT / "tools" / "alerts" / "config.json").read_text())
    home(stats)
    pricing(cfg)
    not_found()
    sitemap_home(dt.date.today().isoformat())
    print("site pages: /, /pricing/, 404, sitemap-home.xml")


if __name__ == "__main__":
    main()
