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
from build import COUNTRIES, SECTORS, country_name, sector_name  # noqa: E402
sys.path.insert(0, str(ROOT / "tools" / "site"))
from chrome import fmt_int, footer as site_footer, header as site_header, hreflang_links  # noqa: E402

CFG = json.loads((HERE / "config.json").read_text())
SITE = CFG["site"]
LIVE = bool(CFG["checkout_links"].get("free") and CFG["checkout_links"].get("pro"))
COUNTRY_FR = {"FRA": "France", "DEU": "Allemagne", "ITA": "Italie", "ESP": "Espagne", "POL": "Pologne", "ROU": "Roumanie",
              "NLD": "Pays-Bas", "BEL": "Belgique", "AUT": "Autriche", "PRT": "Portugal", "CZE": "Tchéquie", "SWE": "Suède",
              "FIN": "Finlande", "DNK": "Danemark", "IRL": "Irlande", "GRC": "Grèce"}
MAIL = CFG.get("contact", "contact@jovianlabsstudio.com")

TXT = {
    "en": dict(
        path="alerts/", other="fr/alertes/", other_label="Version française",
        title="Second-chance public tender alerts: failed and relaunched contracts, every Monday | Jovian Labs",
        desc="Weekly email alerts on public procurement procedures that failed (no tenders, all rejected) and the open calls that "
             "relaunch them, by country and sector across 16 EU countries. Free plan, Pro at 19 EUR per month excl. VAT.",
        h1="Second-chance tender alerts, every Monday",
        lede=("Every week, public contracts close without a winner because nobody bid or every bid was rejected. Most come back, "
              "with fewer competitors, and the buyer is sometimes allowed to negotiate directly. We find them in {n} countries and "
              "email you the ones that match your sector."),
        stat="This week: <b>{r}</b> open calls relaunching a failed procedure and <b>{f}</b> procedures that failed in the last 30 days.",
        country="Country", sector="Sector", all="All sectors", keywords="Keywords (optional, comma-separated)",
        kw_ph="e.g. cleaning, software", lang="Email language", free_btn="Start free", pro_btn="Go Pro · €19 / month + VAT",
        soon="Subscriptions open in a few days.",
        plans=[("", "Free", "Pro · €19 / month + VAT"),
               ("Open calls relaunching a failed procedure", "5 most urgent", "All"),
               ("Procedures that failed this week (contact the buyer early)", "Count only", "All, with reason"),
               ("Deadlines within 14 days", "—", "Yes"),
               ("CSV file attached", "—", "Yes"),
               ("Filters: country, sector, keywords", "Yes", "Yes")],
        sample="A Pro email (Germany, all sectors, real data)", sample_img="/alerts/sample-email-en.png",
        faq=[("Where does the data come from?", "From TED, the EU's official tenders journal, and BOAMP, France's official bulletin. "
              "Relaunches are matched to the earlier failed procedure of the same buyer (same CPV code, similar title), or detected "
              "in the notice text."),
             ("Why do failed procedures matter?", "Under Directive 2014/24/EU (Article 32), when a procedure receives no tenders or no "
              "suitable tenders, the buyer may relaunch it or negotiate without prior publication. A supplier who knows early can "
              "position itself. This is not legal advice."),
             ("How do I cancel?", "In one click from the link at the bottom of every email (customer portal). No commitment."),
             ("Who handles the payment?", "Polar, our merchant of record, processes the payment and the VAT. Prices exclude VAT, which is added at checkout according to your country; businesses can enter their VAT number there. We never see your card."),
             ("What data do you keep?", "Your email address and your filters, stored by Polar for the subscription; emails are sent "
              "through Resend. Nothing is sold or shared.")],
        thanks_h1="You are subscribed", thanks=("Your first email arrives next Monday morning. You can change your filters or cancel "
                                                 "anytime from the link at the bottom of each email."),
    ),
    "fr": dict(
        path="fr/alertes/", other="alerts/", other_label="English version",
        title="Alertes appels d'offres infructueux et relancés, chaque lundi | Jovian Labs",
        desc="Alertes e-mail hebdomadaires sur les procédures de marchés publics infructueuses (aucune offre, offres rejetées) et les "
             "appels d'offres qui les relancent, par pays et secteur, dans 16 pays de l'UE. Offre gratuite, Pro à 19 € HT par mois.",
        h1="Alertes « seconde chance » sur les appels d'offres, chaque lundi",
        lede=("Chaque semaine, des marchés publics se terminent sans attributaire : aucune offre, ou toutes rejetées. La plupart "
              "reviennent, avec moins de concurrents, et l'acheteur peut parfois négocier directement. Nous les repérons dans {n} pays "
              "et vous envoyons ceux de votre secteur."),
        stat="Cette semaine : <b>{r}</b> appels ouverts qui relancent une procédure infructueuse et <b>{f}</b> procédures infructueuses sur 30 jours.",
        country="Pays", sector="Secteur", all="Tous secteurs", keywords="Mots-clés (facultatif, séparés par des virgules)",
        kw_ph="ex. nettoyage, logiciel", lang="Langue des e-mails", free_btn="Commencer gratuitement", pro_btn="Passer Pro · 19 € HT / mois",
        soon="Les abonnements ouvrent dans quelques jours.",
        plans=[("", "Gratuit", "Pro · 19 € HT / mois"),
               ("Appels ouverts qui relancent une procédure infructueuse", "Les 5 plus urgents", "Tous"),
               ("Procédures infructueuses de la semaine (se signaler tôt à l'acheteur)", "Nombre seulement", "Toutes, avec le motif"),
               ("Échéances à 14 jours", "—", "Oui"),
               ("Fichier CSV joint", "—", "Oui"),
               ("Filtres : pays, secteur, mots-clés", "Oui", "Oui")],
        sample="Un e-mail Pro (France · maintenance et réparation, données réelles)", sample_img="/alerts/sample-email.png",
        faq=[("D'où viennent les données ?", "De TED, le journal officiel des marchés de l'UE, et du BOAMP. Les relances sont rapprochées "
              "de la procédure infructueuse du même acheteur (même code CPV, titre proche) ou repérées dans le texte de l'avis."),
             ("Pourquoi les procédures infructueuses comptent ?", "Après un appel d'offres sans offre ou sans offre appropriée, l'acheteur "
              "peut relancer, ou passer un marché sans publicité ni mise en concurrence (article R2122-2 du code de la commande publique). "
              "Un fournisseur informé tôt peut se positionner. Ceci n'est pas un avis juridique."),
             ("Comment résilier ?", "En un clic, depuis le lien en bas de chaque e-mail (portail client). Sans engagement."),
             ("Qui gère le paiement ?", "Polar, notre revendeur officiel (merchant of record), encaisse et gère la TVA. Les prix sont hors taxes : "
              "la TVA de votre pays s'ajoute au paiement, et les entreprises peuvent y saisir leur numéro de TVA. Nous ne voyons "
              "jamais votre carte."),
             ("Quelles données gardez-vous ?", "Votre adresse e-mail et vos filtres, conservés par Polar pour l'abonnement ; les e-mails "
              "partent par Resend. Rien n'est vendu ni partagé.")],
        thanks_h1="Abonnement confirmé", thanks=("Votre premier e-mail arrive lundi matin. Vous pouvez changer vos filtres ou résilier à "
                                                 "tout moment depuis le lien en bas de chaque e-mail."),
    ),
    "de": dict(
        path="de/alerts/",
        title="Alerts zu aufgehobenen und neu ausgeschriebenen Vergaben, jeden Montag | Jovian Labs",
        desc="Wöchentliche E-Mail-Alerts zu gescheiterten Vergabeverfahren (kein Angebot, alle ausgeschlossen) und den Ausschreibungen, die "
             "sie neu auflegen, nach Land und Branche in 16 EU-Ländern. Kostenlos, Pro für 19 € pro Monat zzgl. MwSt.",
        h1="Ausschreibungs-Alerts für die zweite Chance, jeden Montag",
        lede=("Jede Woche enden öffentliche Aufträge ohne Zuschlag, weil niemand geboten hat oder alle Angebote ausgeschlossen wurden. Die "
              "meisten kommen zurück, mit weniger Wettbewerb, und manchmal darf der Auftraggeber direkt verhandeln. Wir finden sie in {n} "
              "Ländern und schicken Ihnen die, die zu Ihrer Branche passen."),
        stat="Diese Woche: <b>{r}</b> offene Ausschreibungen nach einem gescheiterten Verfahren und <b>{f}</b> gescheiterte Verfahren in den letzten 30 Tagen.",
        country="Land", sector="Branche", all="Alle Branchen", keywords="Stichwörter (optional, durch Komma getrennt)",
        kw_ph="z. B. Reinigung, Software", lang="Sprache der E-Mails", free_btn="Kostenlos starten", pro_btn="Pro wählen · 19 € / Monat zzgl. MwSt.",
        soon="Abonnements starten in wenigen Tagen.",
        plans=[("", "Kostenlos", "Pro · 19 € / Monat zzgl. MwSt."),
               ("Offene Ausschreibungen nach einem gescheiterten Verfahren", "Die 5 dringendsten", "Alle"),
               ("Diese Woche gescheiterte Verfahren (Auftraggeber früh ansprechen)", "Nur die Anzahl", "Alle, mit Grund"),
               ("Fristen in den nächsten 14 Tagen", "—", "Ja"),
               ("CSV-Datei im Anhang", "—", "Ja"),
               ("Filter: Land, Branche, Stichwörter", "Ja", "Ja")],
        sample="Eine Pro-E-Mail (Deutschland, alle Branchen, echte Daten)", sample_img="/alerts/sample-email-en.png",
        faq=[("Woher kommen die Daten?", "Aus TED, dem offiziellen Amtsblatt der EU für Ausschreibungen, und dem französischen BOAMP. "
              "Neuausschreibungen werden dem früheren gescheiterten Verfahren desselben Auftraggebers zugeordnet (gleicher CPV-Code, "
              "ähnlicher Titel) oder im Text der Bekanntmachung erkannt."),
             ("Warum sind gescheiterte Verfahren interessant?", "Nach Artikel 32 der Richtlinie 2014/24/EU darf ein Auftraggeber, dessen Verfahren "
              "keine oder keine geeigneten Angebote erhielt, neu ausschreiben oder ohne vorherige Bekanntmachung verhandeln. Wer früh davon "
              "weiß, kann sich positionieren. Dies ist keine Rechtsberatung."),
             ("Wie kündige ich?", "Mit einem Klick über den Link am Ende jeder E-Mail (Kundenportal). Ohne Mindestlaufzeit."),
             ("Wer wickelt die Zahlung ab?", "Polar, unser Händler (Merchant of Record), wickelt Zahlung und MwSt. ab. Die Preise verstehen sich "
              "zzgl. MwSt., die beim Bezahlen je nach Land aufgeschlagen wird; Unternehmen können dort ihre USt-IdNr. angeben. Ihre Karte sehen wir nie."),
             ("Welche Daten speichern Sie?", "Ihre E-Mail-Adresse und Ihre Filter, bei Polar für das Abonnement gespeichert; die E-Mails werden "
              "über Resend versendet. Nichts wird verkauft oder weitergegeben.")],
        thanks_h1="Abonniert", thanks=("Ihre erste E-Mail kommt am nächsten Montagmorgen. Filter ändern oder kündigen können Sie jederzeit "
                                       "über den Link am Ende jeder E-Mail."),
    ),
    "es": dict(
        path="es/alerts/",
        title="Alertas de licitaciones desiertas y relanzadas, cada lunes | Jovian Labs",
        desc="Alertas semanales por correo sobre procedimientos de contratación pública fallidos (sin ofertas, todas rechazadas) y las "
             "licitaciones que los relanzan, por país y sector en 16 países de la UE. Plan gratuito, Pro a 19 € al mes + IVA.",
        h1="Alertas de segunda oportunidad en licitaciones, cada lunes",
        lede=("Cada semana hay contratos públicos que terminan sin adjudicatario porque nadie se presentó o todas las ofertas fueron "
              "rechazadas. La mayoría vuelven a licitarse, con menos competidores, y a veces el comprador puede negociar directamente. "
              "Los buscamos en {n} países y le enviamos los de su sector."),
        stat="Esta semana: <b>{r}</b> licitaciones abiertas que relanzan un procedimiento fallido y <b>{f}</b> procedimientos fallidos en los últimos 30 días.",
        country="País", sector="Sector", all="Todos los sectores", keywords="Palabras clave (opcional, separadas por comas)",
        kw_ph="p. ej. limpieza, software", lang="Idioma del correo", free_btn="Empezar gratis", pro_btn="Pasar a Pro · 19 € / mes + IVA",
        soon="Las suscripciones abren en unos días.",
        plans=[("", "Gratis", "Pro · 19 € / mes + IVA"),
               ("Licitaciones abiertas que relanzan un procedimiento fallido", "Las 5 más urgentes", "Todas"),
               ("Procedimientos fallidos de la semana (contactar pronto al comprador)", "Solo el número", "Todos, con el motivo"),
               ("Plazos en los próximos 14 días", "—", "Sí"),
               ("Archivo CSV adjunto", "—", "Sí"),
               ("Filtros: país, sector, palabras clave", "Sí", "Sí")],
        sample="Un correo Pro (Alemania, todos los sectores, datos reales)", sample_img="/alerts/sample-email-en.png",
        faq=[("¿De dónde vienen los datos?", "De TED, el diario oficial de licitaciones de la UE, y del BOAMP francés. Las nuevas licitaciones "
              "se asocian al procedimiento fallido anterior del mismo comprador (mismo código CPV, título parecido) o se detectan en el texto del anuncio."),
             ("¿Por qué importan los procedimientos fallidos?", "Según el artículo 32 de la Directiva 2014/24/UE, si un procedimiento no recibe "
              "ofertas o ninguna adecuada, el comprador puede volver a licitar o negociar sin publicación previa. Quien lo sabe pronto puede "
              "posicionarse. Esto no es asesoramiento jurídico."),
             ("¿Cómo cancelo?", "Con un clic desde el enlace al final de cada correo (portal del cliente). Sin permanencia."),
             ("¿Quién gestiona el pago?", "Polar, nuestro revendedor oficial (merchant of record), gestiona el pago y el IVA. Los precios no incluyen "
              "IVA, que se añade al pagar según su país; las empresas pueden indicar allí su número de IVA. Nunca vemos su tarjeta."),
             ("¿Qué datos guardan?", "Su correo y sus filtros, guardados por Polar para la suscripción; los correos se envían con Resend. "
              "Nada se vende ni se comparte.")],
        thanks_h1="Suscripción confirmada", thanks=("Su primer correo llega el próximo lunes por la mañana. Puede cambiar sus filtros o "
                                                    "cancelar en cualquier momento desde el enlace al final de cada correo."),
    ),
    "it": dict(
        path="it/alerts/",
        title="Avvisi sulle gare deserte e ripubblicate, ogni lunedì | Jovian Labs",
        desc="Avvisi email settimanali sulle procedure d'appalto fallite (nessuna offerta, tutte escluse) e sulle gare che le ripropongono, "
             "per paese e settore in 16 paesi UE. Piano gratuito, Pro a 19 € al mese + IVA.",
        h1="Avvisi «seconda possibilità» sulle gare, ogni lunedì",
        lede=("Ogni settimana alcuni appalti pubblici si chiudono senza aggiudicatario perché nessuno ha presentato offerte o tutte sono "
              "state escluse. Quasi tutti tornano in gara, con meno concorrenti, e a volte la stazione appaltante può negoziare direttamente. "
              "Li troviamo in {n} paesi e le inviamo quelli del suo settore."),
        stat="Questa settimana: <b>{r}</b> gare aperte che ripropongono una procedura fallita e <b>{f}</b> procedure fallite negli ultimi 30 giorni.",
        country="Paese", sector="Settore", all="Tutti i settori", keywords="Parole chiave (facoltative, separate da virgole)",
        kw_ph="es. pulizie, software", lang="Lingua delle email", free_btn="Inizia gratis", pro_btn="Passa a Pro · 19 € / mese + IVA",
        soon="Gli abbonamenti aprono tra pochi giorni.",
        plans=[("", "Gratis", "Pro · 19 € / mese + IVA"),
               ("Gare aperte che ripropongono una procedura fallita", "Le 5 più urgenti", "Tutte"),
               ("Procedure fallite della settimana (contattare presto l'ente)", "Solo il numero", "Tutte, con il motivo"),
               ("Scadenze entro 14 giorni", "—", "Sì"),
               ("File CSV allegato", "—", "Sì"),
               ("Filtri: paese, settore, parole chiave", "Sì", "Sì")],
        sample="Un'email Pro (Germania, tutti i settori, dati reali)", sample_img="/alerts/sample-email-en.png",
        faq=[("Da dove vengono i dati?", "Da TED, la gazzetta ufficiale degli appalti dell'UE, e dal BOAMP francese. Le nuove gare vengono "
              "collegate alla procedura fallita precedente dello stesso ente (stesso codice CPV, titolo simile) o individuate nel testo dell'avviso."),
             ("Perché le procedure fallite contano?", "Secondo l'articolo 32 della direttiva 2014/24/UE, se una procedura non riceve offerte o "
              "nessuna offerta adeguata, la stazione appaltante può ripubblicare la gara o negoziare senza previa pubblicazione. Chi lo sa presto "
              "può posizionarsi. Non è una consulenza legale."),
             ("Come disdico?", "Con un clic dal link in fondo a ogni email (portale clienti). Senza vincoli."),
             ("Chi gestisce il pagamento?", "Polar, il nostro rivenditore ufficiale (merchant of record), gestisce pagamento e IVA. I prezzi sono "
              "IVA esclusa: l'IVA del suo paese si aggiunge al pagamento e le aziende possono indicare lì la partita IVA. Non vediamo mai la sua carta."),
             ("Quali dati conservate?", "Il suo indirizzo email e i suoi filtri, conservati da Polar per l'abbonamento; le email partono tramite "
              "Resend. Nulla viene venduto o condiviso.")],
        thanks_h1="Iscrizione confermata", thanks=("La prima email arriva lunedì mattina. Può cambiare i filtri o disdire in qualsiasi momento "
                                                   "dal link in fondo a ogni email."),
    ),
}
DEFAULT_COUNTRY = {"en": "DEU", "fr": "FRA", "de": "DEU", "es": "ESP", "it": "ITA"}
EXTRA = {"en": "Payments by Polar (merchant of record). Data: TED (EU Publications Office) and BOAMP (DILA).",
         "fr": "Paiements par Polar (revendeur officiel). Données : TED (Office des publications de l'UE) et BOAMP (DILA).",
         "de": "Zahlungen über Polar (Merchant of Record). Daten: TED (Amt für Veröffentlichungen der EU) und BOAMP (DILA).",
         "es": "Pagos a través de Polar (merchant of record). Datos: TED (Oficina de Publicaciones de la UE) y BOAMP (DILA).",
         "it": "Pagamenti tramite Polar (merchant of record). Dati: TED (Ufficio delle pubblicazioni dell'UE) e BOAMP (DILA)."}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def shell(lang, path, title, desc, body, noindex, alt=None):
    alternates = {h: "/" + p for h, p in (alt or {}).items()}
    rb = '<meta name="robots" content="noindex">' if noindex else ""
    extra = EXTRA.get(lang, EXTRA["en"])
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE}/{path}">'
            f'{hreflang_links(alternates)}{rb}'
            f'<link rel="icon" href="/assets/favicon.png"><link rel="stylesheet" href="/assets/style.css">'
            f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:image" content="{SITE}/alerts/sample-email{"" if lang == "fr" else "-en"}.png">'
            f'<style>.form{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:14px 0}}'
            f'.form label{{display:block;font-size:.86rem;color:var(--ink2);margin-bottom:4px}}'
            f'.form select,.form input{{width:100%;padding:8px 10px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit}}'
            f'</style></head><body>{site_header(lang, "alerts", alternates)}<main>{body}</main>{site_footer(lang, extra)}</body></html>')


def build():
    stats = json.loads((ROOT / "tenders" / "stats.json").read_text())["stats"]
    r = sum(v["relaunch"] for v in stats.values())
    f = sum(v["failed"] for v in stats.values())
    alt = {l: t["path"] for l, t in TXT.items()}
    urls = []
    for lang, t in TXT.items():
        default = DEFAULT_COUNTRY[lang]
        copt = "".join(f'<option value="{c}"{" selected" if c == default else ""}>{esc(country_name(c, lang))}</option>' for c in COUNTRIES)
        sopt = f'<option value="all">{esc(t["all"])}</option>' + "".join(
            f'<option value="{s[0]}">{esc(sector_name((s[0], s[1], s[2]), lang))}</option>' for s in SECTORS)
        lopt = "".join(f'<option value="{v}"{" selected" if v == lang else ""}>{n}</option>'
                       for v, n in (("en", "English"), ("fr", "Français"), ("de", "Deutsch"), ("es", "Español"), ("it", "Italiano")))
        dis = "" if LIVE else " disabled"
        rows = "".join(f"<tr>{''.join(f'<td>{esc(c)}</td>' if i else f'<td><b>{esc(c)}</b></td>' for i, c in enumerate(row))}</tr>"
                       for row in t["plans"][1:])
        head_row = "".join(f"<th>{esc(c)}</th>" for c in t["plans"][0])
        faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in t["faq"])
        links = json.dumps(CFG["checkout_links"])
        body = f"""<h1>{esc(t['h1'])}</h1>
<p class="lede">{esc(t['lede'].format(n=len(stats)))}</p>
<p>{t['stat'].format(r=fmt_int(r, lang), f=fmt_int(f, lang))}</p>
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
<h2>{esc(t['plans'][0][1])} · Pro</h2>
<div class="card"><table><thead><tr>{head_row}</tr></thead><tbody>{rows}</tbody></table></div>
<h2>{esc(t['sample'])}</h2>
<p><img src="{t['sample_img']}" alt="" loading="lazy" style="max-width:100%;height:auto;border:1px solid var(--line);border-radius:10px"></p>
<h2>FAQ</h2>{faq}
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
    thanks = (f"<h1>{esc(TXT['en']['thanks_h1'])}</h1>" + "".join(
        f"<p class='lede' lang='{l}'><b>{esc(t['thanks_h1'])}.</b> {esc(t['thanks'])}</p>" for l, t in TXT.items())
        + "<p><a class='btn' href='/'>Jovian Labs</a><a class='btn' href='/tenders/'>Tenders</a></p>")
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
