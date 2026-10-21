"""Alertes e-mail hebdomadaires « seconde chance » (appels d'offres relancés et procédures infructueuses).

Abonnés : abonnements actifs Polar (produits « free » et « pro » de config.json, champs personnalisés country / sector /
keywords / language). Envoi : API Resend. Nouveautés : éléments jamais vus (state/seen.json, mis à jour après envoi).

python alerts.py --preview FRA --sector informatique --lang fr --plan pro   -> preview/*.html (aucun envoi)
python alerts.py --test-to adresse@exemple.com --country FRA --plan pro      -> envoi d'un seul e-mail de test
python alerts.py                                                            -> envoi à tous les abonnés (POLAR_TOKEN, RESEND_API_KEY)
"""
import argparse
import base64
import csv
import datetime as dt
import html
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "config.json").read_text())
sys.path.insert(0, str(HERE.parent / "tenders"))
from build import COUNTRIES, SECTORS  # noqa: E402

UA = "jovianlabs-alerts/1.0"
SECTOR_LABEL = {s[0]: (s[1], s[2]) for s in SECTORS}
SECTOR_LABEL["autres"] = ("Autres", "Other")
COUNTRY_FR = {"FRA": "France", "DEU": "Allemagne", "ITA": "Italie", "ESP": "Espagne", "POL": "Pologne", "ROU": "Roumanie",
              "NLD": "Pays-Bas", "BEL": "Belgique", "AUT": "Autriche", "PRT": "Portugal", "CZE": "Tchéquie", "SWE": "Suède",
              "FIN": "Finlande", "DNK": "Danemark", "IRL": "Irlande", "GRC": "Grèce"}

T = {
    "fr": dict(subj="Seconde chance · {n} appel(s) relancé(s), {m} échec(s) · {where}",
               subj_none="Seconde chance · rien de nouveau cette semaine · {where}",
               hello="Voici les nouveautés de la semaine pour {where}.",
               rel="Appels d'offres ouverts qui relancent une procédure infructueuse",
               fail="Procédures infructueuses publiées cette semaine (aucune offre ou toutes rejetées)",
               soon="Toujours ouverts, date limite dans les 14 jours",
               none="Rien de nouveau cette semaine dans vos critères.",
               deadline="Date limite", buyer="Acheteur", proc="Procédure", value="Valeur est.", published="Publié", why="Motif",
               no_rece="aucune offre", all_rej="offres rejetées", high="relance probable", medium="relance possible",
               text="l'avis mentionne l'infructuosité",
               tip=("Une procédure infructueuse peut être relancée, ou passée en procédure négociée sans publication (article "
                    "R2122-2 du code de la commande publique, article 32 de la directive 2014/24/UE) : un fournisseur qui se signale "
                    "tôt auprès de l'acheteur a sa chance."),
               free_more="+ {k} autre(s) appel(s) relancé(s) et {m} procédure(s) infructueuse(s) dans vos critères cette semaine.",
               upgrade="Recevez la liste complète, les procédures infructueuses et le fichier CSV : passer à l'abonnement Pro",
               csv="Le fichier CSV joint contient toutes les lignes.",
               manage="Gérer ou résilier mon abonnement", why_get="Vous recevez cet e-mail car vous êtes abonné aux alertes « seconde chance » de Jovian Labs.",
               daily="Besoin d'un suivi quotidien ou de plusieurs pays ? Notre Actor Apify fait la même recherche à la demande.",
               sources="Sources : TED (Office des publications de l'UE) et BOAMP (DILA, Licence Ouverte). Vérifiez toujours l'avis officiel."),
    "en": dict(subj="Second chance · {n} relaunched call(s), {m} failure(s) · {where}",
               subj_none="Second chance · nothing new this week · {where}",
               hello="Here is what is new this week for {where}.",
               rel="Open calls that relaunch a failed procedure",
               fail="Procedures that failed this week (no tenders or all rejected)",
               soon="Still open, deadline within 14 days",
               none="Nothing new this week for your criteria.",
               deadline="Deadline", buyer="Buyer", proc="Procedure", value="Est. value", published="Published", why="Why",
               no_rece="no tenders", all_rej="all rejected", high="strong match", medium="likely match", text="notice mentions the failure",
               tip=("Under Directive 2014/24/EU (Article 32), a buyer whose procedure received no suitable tenders may relaunch it or "
                    "negotiate without prior publication: a supplier who contacts the buyer early has a real chance."),
               free_more="+ {k} more relaunched call(s) and {m} failed procedure(s) for your criteria this week.",
               upgrade="Get the full list, the failed procedures and the CSV file: upgrade to Pro",
               csv="The attached CSV file contains every row.",
               manage="Manage or cancel my subscription", why_get="You receive this email because you subscribed to the Jovian Labs second-chance alerts.",
               daily="Need daily monitoring or several countries? Our Apify Actor runs the same search on demand.",
               sources="Sources: TED (EU Publications Office) and BOAMP (DILA, Licence Ouverte). Always check the official notice."),
}


# --------------------------------------------------------------------------- données
def load_items(codes):
    items = []
    for c in codes:
        f = HERE / "data" / f"{c}.json"
        if f.exists():
            items += json.loads(f.read_text())["items"]
    return items


def load_seen():
    f = HERE / "state" / "seen.json"
    return json.loads(f.read_text()) if f.exists() else {}


def save_seen(seen, today):
    cutoff = (today - dt.timedelta(days=180)).isoformat()
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    (HERE / "state").mkdir(exist_ok=True)
    (HERE / "state" / "seen.json").write_text(json.dumps(seen, sort_keys=True, indent=0))


def is_new(item, seen, today):
    if seen:  # régime normal : jamais vu auparavant
        return item["key"] not in seen
    # premier envoi : seulement ce qui a été publié dans les 7 derniers jours
    return (item.get("published") or "") >= (today - dt.timedelta(days=7)).isoformat()


def matches(item, sub):
    if item["country"] != sub["country"]:
        return False
    if sub.get("sector") and sub["sector"] not in ("all", "") and item.get("sector") != sub["sector"]:
        return False
    kws = [k.strip().lower() for k in (sub.get("keywords") or "").split(",") if k.strip()]
    if kws:
        text = f"{item.get('title') or ''} {item.get('buyer') or ''}".lower()
        return any(k in text for k in kws)
    return True


# --------------------------------------------------------------------------- rendu
def esc(x):
    return html.escape(str(x if x is not None else ""))


def money(v, cur):
    if not v:
        return ""
    return f"{v:,.0f} {cur or ''}".replace(",", " ").strip()


def where_label(sub, lang):
    c = COUNTRY_FR.get(sub["country"]) if lang == "fr" else COUNTRIES.get(sub["country"], (sub["country"],))[0]
    sec = sub.get("sector")
    if sec and sec not in ("all", ""):
        c += " · " + SECTOR_LABEL.get(sec, (sec, sec))[0 if lang == "fr" else 1]
    if (sub.get("keywords") or "").strip():
        c += " · « " + sub["keywords"].strip() + " »" if lang == "fr" else " · “" + sub["keywords"].strip() + "”"
    return c


TD = "padding:7px 8px;border-bottom:1px solid #e4e2da;vertical-align:top;font-size:14px"
TH = "padding:7px 8px;border-bottom:2px solid #e4e2da;text-align:left;font-size:12px;color:#55566e;text-transform:uppercase"


def table_rel(items, t):
    rows = []
    for x in items:
        tag = t.get(x.get("confidence") or "medium", t["medium"])
        rows.append(f"<tr><td style='{TD};white-space:nowrap'>{esc(x.get('deadline'))}</td><td style='{TD}'>{esc(x.get('buyer'))}</td>"
                    f"<td style='{TD}'><a href='{esc(x.get('url'))}' style='color:#2a2e78'>{esc((x.get('title') or '')[:180])}</a>"
                    f"<div style='font-size:12px;color:#c98f2c'>{esc(tag)}</div></td>"
                    f"<td style='{TD};white-space:nowrap'>{esc(money(x.get('value'), x.get('currency')))}</td></tr>")
    return (f"<table style='border-collapse:collapse;width:100%'><tr><th style='{TH}'>{t['deadline']}</th><th style='{TH}'>{t['buyer']}</th>"
            f"<th style='{TH}'>{t['proc']}</th><th style='{TH}'>{t['value']}</th></tr>{''.join(rows)}</table>")


def table_fail(items, t):
    rows = []
    for x in items:
        why = ", ".join(t.get(r.replace("-", "_"), r) for r in (x.get("reasons") or []))
        rows.append(f"<tr><td style='{TD};white-space:nowrap'>{esc(x.get('published'))}</td><td style='{TD}'>{esc(x.get('buyer'))}</td>"
                    f"<td style='{TD}'><a href='{esc(x.get('url'))}' style='color:#2a2e78'>{esc((x.get('title') or '')[:180])}</a></td>"
                    f"<td style='{TD}'>{esc(why)}</td></tr>")
    return (f"<table style='border-collapse:collapse;width:100%'><tr><th style='{TH}'>{t['published']}</th><th style='{TH}'>{t['buyer']}</th>"
            f"<th style='{TH}'>{t['proc']}</th><th style='{TH}'>{t['why']}</th></tr>{''.join(rows)}</table>")


def csv_attachment(rel, fail):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["type", "country", "deadline", "published", "buyer", "title", "cpv", "sector", "estimated_value", "currency",
                "match", "reasons", "url"])
    for x in rel:
        w.writerow(["relaunch", x["country"], x.get("deadline"), x.get("published"), x.get("buyer"), x.get("title"), x.get("cpv"),
                    x.get("sector"), x.get("value"), x.get("currency"), x.get("confidence"), "", x.get("url")])
    for x in fail:
        w.writerow(["failed", x["country"], "", x.get("published"), x.get("buyer"), x.get("title"), x.get("cpv"), x.get("sector"),
                    x.get("value"), x.get("currency"), "", " ".join(x.get("reasons") or []), x.get("url")])
    return buf.getvalue().encode("utf-8-sig")


def compose(sub, items, seen, today):
    """Renvoie (sujet, html, texte, pièce jointe CSV ou None) pour un abonné."""
    lang = sub.get("language") if sub.get("language") in T else ("fr" if sub["country"] == "FRA" else "en")
    t = T[lang]
    tomorrow = (today + dt.timedelta(days=1)).isoformat()
    # un appel qui se clôt aujourd'hui n'est plus utile : on garde les dates limites à partir de demain
    mine = [x for x in items if matches(x, sub) and (x["kind"] != "relaunch" or (x.get("deadline") or "9999") >= tomorrow)]
    new = [x for x in mine if is_new(x, seen, today)]
    rel = sorted([x for x in new if x["kind"] == "relaunch"], key=lambda x: x.get("deadline") or "9999")
    fail = sorted([x for x in new if x["kind"] == "failed"], key=lambda x: x.get("published") or "", reverse=True)
    soon_limit = (today + dt.timedelta(days=14)).isoformat()
    soon = sorted([x for x in mine if x["kind"] == "relaunch" and x not in rel and today.isoformat() <= (x.get("deadline") or "") <= soon_limit],
                  key=lambda x: x.get("deadline"))[:10]
    where = where_label(sub, lang)
    pro = sub.get("plan") == "pro"
    subject = (t["subj"].format(n=len(rel), m=len(fail), where=where) if (rel or fail) else t["subj_none"].format(where=where))
    parts = [f"<p style='font-size:15px'>{esc(t['hello'].format(where=where))}</p>"]
    if not rel and not fail:
        parts.append(f"<p style='color:#55566e'>{t['none']}</p>")
    shown_rel = rel if pro else rel[:CFG["free_top"]]
    if shown_rel:
        parts.append(f"<h3 style='font-size:16px;margin:22px 0 8px'>{t['rel']} ({len(rel)})</h3>" + table_rel(shown_rel, t))
    if pro and fail:
        parts.append(f"<h3 style='font-size:16px;margin:22px 0 8px'>{t['fail']} ({len(fail)})</h3>" + table_fail(fail[:150], t))
    if pro and soon:
        parts.append(f"<h3 style='font-size:16px;margin:22px 0 8px'>{t['soon']}</h3>" + table_rel(soon, t))
    if not pro:
        more_rel = max(0, len(rel) - len(shown_rel))
        if more_rel or fail:
            parts.append(f"<p style='color:#55566e'>{esc(t['free_more'].format(k=more_rel, m=len(fail)))}</p>")
        link = checkout_link("pro", sub)
        if link:
            parts.append(f"<p><a href='{esc(link)}' style='display:inline-block;background:#c98f2c;color:#16173a;padding:9px 16px;"
                         f"border-radius:999px;text-decoration:none;font-weight:600'>{esc(t['upgrade'])}</a></p>")
    parts.append(f"<p style='font-size:13px;color:#55566e;margin-top:22px'>{esc(t['tip'])}</p>")
    if pro and (rel or fail):
        parts.append(f"<p style='font-size:13px;color:#55566e'>{esc(t['csv'])}</p>")
    parts.append(f"<p style='font-size:13px;color:#55566e'>{esc(t['daily'])} <a href='{CFG['apify_actor']}'>Apify</a></p>")
    foot = (f"<hr style='border:0;border-top:1px solid #e4e2da;margin:24px 0 10px'><p style='font-size:12px;color:#8a8aa0'>"
            f"{esc(t['why_get'])} <a href='{CFG['portal_url']}'>{esc(t['manage'])}</a>.<br>{esc(t['sources'])}<br>"
            f"Jovian Labs · <a href='{CFG['site']}/tenders/'>{CFG['site'].replace('https://', '')}</a></p>")
    body = (f"<div style='font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#16173a;max-width:760px;margin:0 auto'>"
            f"<p style='font-weight:700;font-size:16px;margin:0 0 12px'>Jovian Labs · Second chance</p>{''.join(parts)}{foot}</div>")
    lines = [t["hello"].format(where=where), ""]
    for x in shown_rel:
        lines.append(f"- {x.get('deadline')} · {x.get('buyer')} · {(x.get('title') or '')[:120]} · {x.get('url')}")
    if pro:
        for x in fail[:150]:
            lines.append(f"- [{t['fail'][:12]}] {x.get('published')} · {x.get('buyer')} · {(x.get('title') or '')[:120]} · {x.get('url')}")
    lines += ["", t["why_get"], f"{t['manage']}: {CFG['portal_url']}", t["sources"]]
    att = csv_attachment(rel, fail) if (pro and (rel or fail)) else None
    return subject, body, "\n".join(lines), att, len(rel), len(fail)


def checkout_link(plan, sub):
    base = CFG["checkout_links"].get(plan)
    if not base:
        return None
    f = CFG["custom_fields"]
    q = {f"custom_field_data.{f['country']}": sub["country"], f"custom_field_data.{f['sector']}": sub.get("sector") or "all",
         "customer_email": sub.get("email", "")}
    if sub.get("keywords"):
        q[f"custom_field_data.{f['keywords']}"] = sub["keywords"]
    if sub.get("language"):
        q[f"custom_field_data.{f['language']}"] = sub["language"]
    return base + ("&" if "?" in base else "?") + urllib.parse.urlencode(q)


# --------------------------------------------------------------------------- abonnés (Polar) et envoi (Resend)
def polar_subscribers(token):
    plan_of = {v: k for k, v in CFG["products"].items() if v}
    f = CFG["custom_fields"]
    subs, page = [], 1
    while True:
        url = f"https://api.polar.sh/v1/subscriptions/?status=active&limit=100&page={page}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        for s in d.get("items", []):
            pid = (s.get("product") or {}).get("id") or s.get("product_id")
            if pid not in plan_of:
                continue
            cf = s.get("custom_field_data") or {}
            email = (s.get("customer") or {}).get("email")
            country = (cf.get(f["country"]) or "").upper()
            if not email or country not in COUNTRIES:
                continue
            subs.append(dict(email=email, plan=plan_of[pid], country=country, sector=cf.get(f["sector"]) or "all",
                             keywords=cf.get(f["keywords"]) or "", language=cf.get(f["language"]) or ""))
        if page >= (d.get("pagination") or {}).get("max_page", 1):
            break
        page += 1
    return subs


def resend_send(key, to, subject, html_body, text, att):
    payload = {"from": CFG["from"], "to": [to], "reply_to": CFG["reply_to"], "subject": subject, "html": html_body, "text": text,
               "headers": {"List-Unsubscribe": f"<{CFG['portal_url']}>"}}
    if att:
        payload["attachments"] = [{"filename": "second-chance.csv", "content": base64.b64encode(att).decode()}]
    req = urllib.request.Request("https://api.resend.com/emails", data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", metavar="COUNTRY", help="écrire un aperçu HTML sans rien envoyer")
    ap.add_argument("--test-to", help="envoyer un seul e-mail de test à cette adresse")
    ap.add_argument("--country", default="FRA")
    ap.add_argument("--sector", default="all")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--lang", default="")
    ap.add_argument("--plan", default="pro", choices=["free", "pro"])
    a = ap.parse_args()
    today = dt.date.today()
    seen = load_seen()
    items = load_items(list(COUNTRIES))
    if a.preview or a.test_to:
        sub = dict(email=a.test_to or "preview@example.com", plan=a.plan, country=(a.preview or a.country).upper(), sector=a.sector,
                   keywords=a.keywords, language=a.lang)
        subject, body, text, att, n, m = compose(sub, items, seen, today)
        if a.preview:
            out = HERE / "preview"
            out.mkdir(exist_ok=True)
            p = out / f"{sub['country']}_{sub['sector']}_{sub['plan']}.html"
            p.write_text(f"<!doctype html><meta charset='utf-8'><title>{esc(subject)}</title>{body}", encoding="utf-8")
            print(f"{subject}\n-> {p} ({n} relaunched, {m} failed, CSV {'yes' if att else 'no'})")
            return
        key = os.environ.get("RESEND_API_KEY")
        if not key:
            raise SystemExit("RESEND_API_KEY missing")
        print("sent", resend_send(key, a.test_to, "[TEST] " + subject, body, text, att))
        return
    key, token = os.environ.get("RESEND_API_KEY"), os.environ.get("POLAR_TOKEN")
    if not key or not token:
        print("RESEND_API_KEY or POLAR_TOKEN missing: nothing sent.")
        return
    subs = polar_subscribers(token)
    print(f"{len(subs)} active subscriber(s)")
    sent = 0
    for sub in subs:
        if sent >= CFG["daily_send_cap"]:
            print("daily cap reached: the rest will be sent next run")
            break
        subject, body, text, att, n, m = compose(sub, items, seen, today)
        try:
            resend_send(key, sub["email"], subject, body, text, att)
            sent += 1
            print(f"sent {sub['plan']} {sub['country']}/{sub['sector']}: {n} relaunched, {m} failed")
        except Exception as e:  # noqa: BLE001
            print(f"send failed for a subscriber: {e}")
        time.sleep(0.6)
    for x in items:
        seen.setdefault(x["key"], today.isoformat())
    save_seen(seen, today)
    print(f"{sent} email(s) sent")


if __name__ == "__main__":
    main()
