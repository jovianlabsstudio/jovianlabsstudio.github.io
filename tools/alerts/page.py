"""Pages d'inscription aux alertes « seconde chance » : /alerts/ (anglais), /fr/alertes/ (français), /alerts/thanks/.

Les boutons ouvrent le paiement Polar avec les choix du visiteur pré-remplis (champs personnalisés). Tant que les liens de
paiement ne sont pas dans config.json, la page affiche « bientôt » et n'est pas indexée.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools" / "tenders"))
from build import COUNTRIES, SECTORS  # noqa: E402

CFG = json.loads((HERE / "config.json").read_text())
SITE = CFG["site"]
LIVE = bool(CFG["checkout_links"].get("free") and CFG["checkout_links"].get("pro"))
COUNTRY_FR = {"FRA": "France", "DEU": "Allemagne", "ITA": "Italie", "ESP": "Espagne", "POL": "Pologne", "ROU": "Roumanie",
              "NLD": "Pays-Bas", "BEL": "Belgique", "AUT": "Autriche", "PRT": "Portugal", "CZE": "Tchéquie", "SWE": "Suède",
              "FIN": "Finlande", "DNK": "Danemark", "IRL": "Irlande", "GRC": "Grèce"}
MAIL = CFG.get("contact", "jovianlabsstudio@gmail.com")

TXT = {
    "en": dict(
        path="alerts/", other="fr/alertes/", other_label="Version française",
        title="Second-chance public tender alerts: failed and relaunched contracts, every Monday | Jovian Labs",
        desc="Weekly email alerts on public procurement procedures that failed (no tenders, all rejected) and the open calls that "
             "relaunch them, by country and sector across 16 EU countries. Free plan, Pro at 19 EUR per month.",
        h1="Second-chance tender alerts, every Monday",
        lede=("Every week, public contracts close without a winner because nobody bid or every bid was rejected. Most come back, "
              "with fewer competitors, and the buyer is sometimes allowed to negotiate directly. We find them in {n} countries and "
              "email you the ones that match your sector."),
        stat="This week: <b>{r}</b> open calls relaunching a failed procedure and <b>{f}</b> procedures that failed in the last 30 days.",
        country="Country", sector="Sector", all="All sectors", keywords="Keywords (optional, comma-separated)",
        kw_ph="e.g. cleaning, software", lang="Email language", free_btn="Start free", pro_btn="Go Pro · 19 € / month",
        soon="Subscriptions open in a few days.",
        plans=[("", "Free", "Pro · 19 € / month"),
               ("Open calls relaunching a failed procedure", "5 most urgent", "All"),
               ("Procedures that failed this week (contact the buyer early)", "Count only", "All, with reason"),
               ("Deadlines within 14 days", "—", "Yes"),
               ("CSV file attached", "—", "Yes"),
               ("Filters: country, sector, keywords", "Yes", "Yes")],
        sample="A Pro email (France · repair and maintenance, real data)",
        faq=[("Where does the data come from?", "From TED, the EU's official tenders journal, and BOAMP, France's official bulletin. "
              "Relaunches are matched to the earlier failed procedure of the same buyer (same CPV code, similar title), or detected "
              "in the notice text."),
             ("Why do failed procedures matter?", "Under Directive 2014/24/EU (Article 32), when a procedure receives no tenders or no "
              "suitable tenders, the buyer may relaunch it or negotiate without prior publication. A supplier who knows early can "
              "position itself. This is not legal advice."),
             ("How do I cancel?", "In one click from the link at the bottom of every email (customer portal). No commitment."),
             ("Who handles the payment?", "Polar, our merchant of record, processes the payment and the VAT. We never see your card."),
             ("What data do you keep?", "Your email address and your filters, stored by Polar for the subscription; emails are sent "
              "through Resend. Nothing is sold or shared.")],
        thanks_h1="You are subscribed", thanks=("Your first email arrives next Monday morning. You can change your filters or cancel "
                                                 "anytime from the link at the bottom of each email."),
    ),
    "fr": dict(
        path="fr/alertes/", other="alerts/", other_label="English version",
        title="Alertes appels d'offres infructueux et relancés, chaque lundi | Jovian Labs",
        desc="Alertes e-mail hebdomadaires sur les procédures de marchés publics infructueuses (aucune offre, offres rejetées) et les "
             "appels d'offres qui les relancent, par pays et secteur, dans 16 pays de l'UE. Offre gratuite, Pro à 19 € par mois.",
        h1="Alertes « seconde chance » sur les appels d'offres, chaque lundi",
        lede=("Chaque semaine, des marchés publics se terminent sans attributaire : aucune offre, ou toutes rejetées. La plupart "
              "reviennent, avec moins de concurrents, et l'acheteur peut parfois négocier directement. Nous les repérons dans {n} pays "
              "et vous envoyons ceux de votre secteur."),
        stat="Cette semaine : <b>{r}</b> appels ouverts qui relancent une procédure infructueuse et <b>{f}</b> procédures infructueuses sur 30 jours.",
        country="Pays", sector="Secteur", all="Tous secteurs", keywords="Mots-clés (facultatif, séparés par des virgules)",
        kw_ph="ex. nettoyage, logiciel", lang="Langue des e-mails", free_btn="Commencer gratuitement", pro_btn="Passer Pro · 19 € / mois",
        soon="Les abonnements ouvrent dans quelques jours.",
        plans=[("", "Gratuit", "Pro · 19 € / mois"),
               ("Appels ouverts qui relancent une procédure infructueuse", "Les 5 plus urgents", "Tous"),
               ("Procédures infructueuses de la semaine (se signaler tôt à l'acheteur)", "Nombre seulement", "Toutes, avec le motif"),
               ("Échéances à 14 jours", "—", "Oui"),
               ("Fichier CSV joint", "—", "Oui"),
               ("Filtres : pays, secteur, mots-clés", "Oui", "Oui")],
        sample="Un e-mail Pro (France · maintenance et réparation, données réelles)",
        faq=[("D'où viennent les données ?", "De TED, le journal officiel des marchés de l'UE, et du BOAMP. Les relances sont rapprochées "
              "de la procédure infructueuse du même acheteur (même code CPV, titre proche) ou repérées dans le texte de l'avis."),
             ("Pourquoi les procédures infructueuses comptent ?", "Après un appel d'offres sans offre ou sans offre appropriée, l'acheteur "
              "peut relancer, ou passer un marché sans publicité ni mise en concurrence (article R2122-2 du code de la commande publique). "
              "Un fournisseur informé tôt peut se positionner. Ceci n'est pas un avis juridique."),
             ("Comment résilier ?", "En un clic, depuis le lien en bas de chaque e-mail (portail client). Sans engagement."),
             ("Qui gère le paiement ?", "Polar, notre revendeur officiel (merchant of record), encaisse et gère la TVA. Nous ne voyons "
              "jamais votre carte."),
             ("Quelles données gardez-vous ?", "Votre adresse e-mail et vos filtres, conservés par Polar pour l'abonnement ; les e-mails "
              "partent par Resend. Rien n'est vendu ni partagé.")],
        thanks_h1="Abonnement confirmé", thanks=("Votre premier e-mail arrive lundi matin. Vous pouvez changer vos filtres ou résilier à "
                                                 "tout moment depuis le lien en bas de chaque e-mail."),
    ),
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def shell(lang, path, title, desc, body, noindex, alt=None):
    alts = "".join(f'<link rel="alternate" hreflang="{h}" href="{SITE}/{p}">' for h, p in (alt or {}).items())
    rb = '<meta name="robots" content="noindex">' if noindex else ""
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE}/{path}">{alts}{rb}'
            f'<link rel="icon" href="/assets/favicon.png"><link rel="stylesheet" href="/assets/style.css">'
            f'<style>.form{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:14px 0}}'
            f'.form label{{display:block;font-size:.86rem;color:var(--ink2);margin-bottom:4px}}'
            f'.form select,.form input{{width:100%;padding:8px 10px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink)}}'
            f'.btn{{display:inline-block;padding:10px 18px;border-radius:999px;border:1px solid var(--gold);background:var(--card);color:var(--ink);'
            f'font-weight:600;cursor:pointer;margin:4px 8px 4px 0}}.btn.pro{{background:var(--gold);color:#16173a}}.btn[disabled]{{opacity:.5;cursor:default}}'
            f'</style></head><body><header><a class="brand" href="/"><img src="/assets/logo.svg" alt="">Jovian Labs</a>'
            f'<nav><a href="/tenders/">Tenders</a><a href="/alerts/">Alerts</a><a href="/metrology/">Metrology</a><a href="/ai-index/">AI Index</a></nav>'
            f'</header><main>{body}</main><footer>Jovian Labs · <a href="mailto:{MAIL}">{MAIL}</a> · Payments by Polar (merchant of record). '
            f'Data: TED (EU Publications Office) and BOAMP (DILA). Independent; not affiliated with either.</footer></body></html>')


def build():
    stats = json.loads((ROOT / "tenders" / "stats.json").read_text())["stats"]
    r = sum(v["relaunch"] for v in stats.values())
    f = sum(v["failed"] for v in stats.values())
    alt = {"en": "alerts/", "fr": "fr/alertes/"}
    urls = []
    for lang, t in TXT.items():
        cnames = COUNTRY_FR if lang == "fr" else {c: n for c, (n, _) in COUNTRIES.items()}
        default = "FRA" if lang == "fr" else "DEU"
        copt = "".join(f'<option value="{c}"{" selected" if c == default else ""}>{esc(cnames[c])}</option>' for c in COUNTRIES)
        sopt = f'<option value="all">{esc(t["all"])}</option>' + "".join(
            f'<option value="{s[0]}">{esc(s[1] if lang == "fr" else s[2])}</option>' for s in SECTORS)
        lopt = "".join(f'<option value="{v}"{" selected" if v == lang else ""}>{n}</option>' for v, n in (("en", "English"), ("fr", "Français")))
        dis = "" if LIVE else " disabled"
        rows = "".join(f"<tr>{''.join(f'<td>{esc(c)}</td>' if i else f'<td><b>{esc(c)}</b></td>' for i, c in enumerate(row))}</tr>"
                       for row in t["plans"][1:])
        head_row = "".join(f"<th>{esc(c)}</th>" for c in t["plans"][0])
        faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in t["faq"])
        links = json.dumps(CFG["checkout_links"])
        body = f"""<h1>{esc(t['h1'])}</h1>
<p class="lede">{esc(t['lede'].format(n=len(stats)))}</p>
<p>{t['stat'].format(r=f'{r:,}'.replace(',', ' '), f=f'{f:,}'.replace(',', ' '))}</p>
<div class="card" style="padding:16px">
<div class="form">
<div><label for="c">{esc(t['country'])}</label><select id="c">{copt}</select></div>
<div><label for="s">{esc(t['sector'])}</label><select id="s">{sopt}</select></div>
<div><label for="k">{esc(t['keywords'])}</label><input id="k" maxlength="200" placeholder="{esc(t['kw_ph'])}"></div>
<div><label for="l">{esc(t['lang'])}</label><select id="l">{lopt}</select></div>
</div>
<button class="btn" data-plan="free"{dis}>{esc(t['free_btn'])}</button><button class="btn pro" data-plan="pro"{dis}>{esc(t['pro_btn'])}</button>
{'' if LIVE else f"<p class='small'>{esc(t['soon'])}</p>"}
</div>
<h2>Free · Pro</h2>
<div class="card"><table><thead><tr>{head_row}</tr></thead><tbody>{rows}</tbody></table></div>
<h2>{esc(t['sample'])}</h2>
<p><img src="/alerts/sample-email.png" alt="" style="max-width:100%;height:auto;border:1px solid var(--line);border-radius:10px"></p>
<h2>FAQ</h2>{faq}
<p class="small"><a href="{SITE}/{t['other']}">{esc(t['other_label'])}</a></p>
<script>
(function(){{var L={links};var q=function(i){{return document.getElementById(i).value}};
document.querySelectorAll('button[data-plan]').forEach(function(b){{b.addEventListener('click',function(){{var base=L[b.dataset.plan];if(!base)return;
var p=new URLSearchParams();p.set('custom_field_data.country',q('c'));p.set('custom_field_data.sector',q('s'));
var k=q('k').trim();if(k)p.set('custom_field_data.keywords',k);p.set('custom_field_data.language',q('l'));
window.location.href=base+(base.indexOf('?')<0?'?':'&')+p.toString();}});}});}})();
</script>"""
        out = ROOT / t["path"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(shell(lang, t["path"], t["title"], t["desc"], body, noindex=not LIVE, alt=alt), encoding="utf-8")
        urls.append(f"{SITE}/{t['path']}")
    en, fr = TXT["en"], TXT["fr"]
    thanks = (f"<h1>{esc(en['thanks_h1'])} · {esc(fr['thanks_h1'])}</h1><p class='lede'>{esc(en['thanks'])}</p>"
              f"<p class='lede'>{esc(fr['thanks'])}</p><p><a href='/tenders/'>Tenders</a> · <a href='/'>Jovian Labs</a></p>")
    tp = ROOT / "alerts" / "thanks" / "index.html"
    tp.parent.mkdir(parents=True, exist_ok=True)
    tp.write_text(shell("en", "alerts/thanks/", "Subscribed | Jovian Labs", "Subscription confirmed.", thanks, noindex=True), encoding="utf-8")
    if LIVE:
        sm = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
        (ROOT / "alerts" / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
        idx = ROOT / "sitemap.xml"
        s = idx.read_text()
        if "alerts/sitemap.xml" not in s:
            idx.write_text(s.replace("</sitemapindex>", f"<sitemap><loc>{SITE}/alerts/sitemap.xml</loc></sitemap></sitemapindex>"))
    print("alerts pages:", "live" if LIVE else "not live yet (noindex)", urls)


if __name__ == "__main__":
    build()
