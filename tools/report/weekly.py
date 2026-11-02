"""Rapport du lundi : un e-mail de synthèse sur l'activité de Jovian Labs, sans IA et sans jeton.

Sources :
- Apify Store (API publique, sans clé) : utilisateurs et lancements de nos Actors, avec l'écart sur 7 jours ;
- Polar (POLAR_TOKEN) : abonnés actifs Free / Pro, nouveaux et résiliés sur 7 jours, revenu mensuel estimé ;
- le dépôt : chiffres des appels d'offres, index IA, nombre de pages publiées ;
- GitHub Actions (GITHUB_TOKEN) : santé des automatisations sur 7 jours.

Envoi par Resend (RESEND_API_KEY) à l'adresse de contact. Les journaux du dépôt sont publics : on n'y écrit
aucun chiffre de Polar ; seul l'historique public d'Apify est enregistré dans tools/report/history.json.

python tools/report/weekly.py [--dry-run]   (--dry-run écrit tools/report/preview.html sans rien envoyer)
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
HIST = HERE / "history.json"
TO = "contact@jovianlabsstudio.com"
FROM = "Jovian Labs <report@jovianlabsstudio.com>"
SITE = "https://jovianlabsstudio.com"
REPO = os.environ.get("GITHUB_REPOSITORY", "jovianlabsstudio/jovianlabsstudio.github.io")
UA = "jovianlabs-report/1.0"
PRO_EUR = 19


def get(url, token=None, timeout=60):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return json.load(r)


def esc(x):
    return html.escape(str(x))


# --------------------------------------------------------------------------- collecte
def apify():
    d = get("https://api.apify.com/v2/store?username=jovianlabs&limit=50")["data"]["items"]
    out = {}
    for it in d:
        s = it.get("stats") or {}
        out[it["name"]] = dict(title=it.get("title") or it["name"], users=s.get("totalUsers") or 0,
                               users7=s.get("totalUsers7Days") or 0, users30=s.get("totalUsers30Days") or 0,
                               runs=s.get("totalRuns") or 0, rating=it.get("actorReviewRating") or 0,
                               reviews=it.get("actorReviewCount") or 0)
    return out


def polar(token, products):
    if not token:
        return None
    plan_of = {v: k for k, v in products.items()}
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7))

    def subs(status, extra=""):
        res, page = [], 1
        while True:
            d = get(f"https://api.polar.sh/v1/subscriptions/?status={status}&limit=100&page={page}{extra}", token)
            res += d.get("items", [])
            if page >= (d.get("pagination") or {}).get("max_page", 1):
                return res
            page += 1

    active = subs("active")
    cancelled = subs("canceled", "&canceled_at_after=" + urllib.parse.quote(since.isoformat()))
    plan = lambda s: plan_of.get((s.get("product") or {}).get("id") or s.get("product_id"), "other")
    started = lambda s: (s.get("started_at") or s.get("created_at") or "")
    count = {"free": 0, "pro": 0, "other": 0}
    new = {"free": 0, "pro": 0, "other": 0}
    countries = {}
    for s in active:
        p = plan(s)
        count[p] += 1
        if started(s) >= since.isoformat():
            new[p] += 1
        c = ((s.get("custom_field_data") or {}).get("country") or "?").upper()
        countries[c] = countries.get(c, 0) + 1
    lost = {"free": 0, "pro": 0, "other": 0}
    for s in cancelled:
        lost[plan(s)] += 1
    ending = sum(1 for s in active if s.get("cancel_at_period_end"))
    return dict(count=count, new=new, lost=lost, ending=ending, countries=countries, mrr=count["pro"] * PRO_EUR)


def site():
    stats = json.loads((ROOT / "tenders" / "stats.json").read_text())
    st = stats["stats"]
    top = sorted(st.items(), key=lambda kv: -kv[1]["relaunch"])[:5]
    ai = sorted((ROOT / "tools" / "ai-index" / "data").glob("20*-W*.json"))
    ai_last = json.loads(ai[-1].read_text()) if ai else {}
    pages = 0
    for sm in ROOT.glob("**/sitemap*.xml"):
        if ".git" in sm.parts or sm.name == "sitemap.xml" and sm.parent == ROOT:
            continue
        pages += len(re.findall(r"<loc>", sm.read_text(errors="ignore")))
    return dict(date=stats.get("date"), relaunch=sum(v["relaunch"] for v in st.values()),
                failed=sum(v["failed"] for v in st.values()), top=top, failures=stats.get("failures") or [],
                ai_week=ai_last.get("week"), ai_answers=len(ai_last.get("records", [])), ai_errors=len(ai_last.get("errors", [])),
                pages=pages)


def actions(token):
    if not token:
        return None
    since = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    d = get(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=100&created=%3E%3D{since}", token)
    runs = [r for r in d.get("workflow_runs", []) if "pages" not in (r.get("name") or "").lower()]
    by = {}
    for r in runs:
        w = by.setdefault(r["name"], {"success": 0, "failure": 0, "other": 0, "last": ""})
        c = r.get("conclusion")
        w["success" if c == "success" else "failure" if c in ("failure", "timed_out") else "other"] += 1
        w["last"] = max(w["last"], r.get("created_at") or "")
    return by


# --------------------------------------------------------------------------- historique public (Apify)
def history_delta(ap, today):
    hist = json.loads(HIST.read_text()) if HIST.exists() else {}
    prev_key = max((k for k in hist if k < today), default=None)
    prev = hist.get(prev_key, {})
    hist[today] = {k: dict(users=v["users"], runs=v["runs"]) for k, v in ap.items()}
    keep = sorted(hist)[-60:]
    HIST.write_text(json.dumps({k: hist[k] for k in keep}, indent=1, sort_keys=True))
    return prev, prev_key


# --------------------------------------------------------------------------- rendu
def render(ap, prev, prev_key, po, si, ac, today, week, wt=None):
    TD = "padding:6px 8px;border-bottom:1px solid #e4e2da;font-size:14px;vertical-align:top"
    TH = "padding:6px 8px;border-bottom:2px solid #e4e2da;font-size:12px;color:#55566e;text-align:left;text-transform:uppercase"
    table = lambda head, rows: (f"<table style='border-collapse:collapse;width:100%'><tr>{''.join(f'<th style={chr(39)}{TH}{chr(39)}>{esc(h)}</th>' for h in head)}</tr>"
                                + "".join("<tr>" + "".join(f"<td style='{TD}'>{c}</td>" for c in r) + "</tr>" for r in rows) + "</table>")
    sign = lambda n: f"+{n}" if n > 0 else str(n)
    parts = []
    # 1. argent
    if po:
        c, n, l = po["count"], po["new"], po["lost"]
        parts.append(f"<h3>1. Abonnements aux alertes (Polar)</h3>" + table(
            ["", "Actifs", "Nouveaux (7 j)", "Résiliés (7 j)"],
            [["Pro (19 € HT/mois)", c["pro"], n["pro"], l["pro"]], ["Free", c["free"], n["free"], l["free"]]])
            + f"<p>Revenu mensuel estimé : <b>{po['mrr']} € HT</b> (avant frais Polar, environ −10 %)."
            + (f" {po['ending']} abonnement(s) s'arrêteront à la fin de la période payée." if po["ending"] else "")
            + (" Pays : " + ", ".join(f"{k} {v}" for k, v in sorted(po["countries"].items(), key=lambda kv: -kv[1])) if po["countries"] else "")
            + "</p>")
    else:
        parts.append("<h3>1. Abonnements aux alertes</h3><p>Polar non lu (jeton absent).</p>")
    # 2. Apify
    rows, tot_new_users, tot_new_runs = [], 0, 0
    for name, v in sorted(ap.items(), key=lambda kv: -kv[1]["runs"]):
        p = prev.get(name, {})
        du, dr = v["users"] - p.get("users", v["users"]), v["runs"] - p.get("runs", v["runs"])
        tot_new_users += du
        tot_new_runs += dr
        rows.append([f"<a href='https://apify.com/jovianlabs/{esc(name)}'>{esc(v['title'])}</a>", f"{v['users']} ({sign(du)})",
                     v["users30"], f"{v['runs']} ({sign(dr)})", f"{v['rating']:.1f} ({v['reviews']})" if v["reviews"] else "—"])
    since = f"depuis le {prev_key}" if prev_key else "premier relevé"
    parts.append(f"<h3>2. Actors Apify</h3><p class='s'>Écarts {since}. Les comptes Jovian Labs eux-mêmes comptent comme 1 utilisateur.</p>"
                 + table(["Actor", "Utilisateurs", "Sur 30 j", "Lancements", "Note"], rows)
                 + "<p>Revenus Apify : voir Apify Console → Insights (non lisible sans clé).</p>")
    # 3. site
    top = ", ".join(f"{k} {v['relaunch']}" for k, v in si["top"])
    parts.append(f"<h3>3. Site et données</h3><ul>"
                 f"<li>Appels d'offres ({si['date']}) : <b>{si['relaunch']}</b> appels relancés ouverts, {si['failed']} échecs sur 30 jours. Top : {top}."
                 + (f" <b>Pays en erreur : {', '.join(si['failures'])}</b>." if si["failures"] else "") + "</li>"
                 f"<li>Index IA ({si['ai_week']}) : {si['ai_answers']} réponses, {si['ai_errors']} erreur(s).</li>"
                 f"<li>Pages publiées dans les sitemaps : {si['pages']}.</li>"
                 f"<li>Trafic Google : Search Console (pas encore relié au rapport).</li></ul>")
    # 4. automatisations
    if ac is not None:
        rows = [[esc(n), w["success"], (f"<b style='color:#b3261e'>{w['failure']}</b>" if w["failure"] else "0"), esc(w["last"][:16].replace("T", " "))]
                for n, w in sorted(ac.items())]
        bad = sum(w["failure"] for w in ac.values())
        parts.append(f"<h3>4. Automatisations (7 jours)</h3>" + (table(["Workflow", "Réussis", "Échecs", "Dernier (UTC)"], rows) if rows else "<p>Aucun lancement.</p>")
                     + ("<p><b>Au moins un échec : à regarder.</b></p>" if bad else "<p>Tout est passé.</p>"))
    # 5. à faire
    todo = []
    if po and po["count"]["pro"] == 0:
        todo.append("Aucun abonné Pro : priorité à la diffusion (posts, Show HN, forums), pas à de nouvelles fonctions.")
    if tot_new_users <= 0:
        todo.append("Aucun nouvel utilisateur Apify cette semaine.")
    if ac and any(w["failure"] for w in ac.values()):
        todo.append("Un workflow a échoué : ouvrir l'onglet Actions du dépôt.")
    if si["failures"]:
        todo.append("Des pays n'ont pas pu être mis à jour cette semaine.")
    parts.append("<h3>5. À retenir</h3><ul>" + "".join(f"<li>{esc(t)}</li>" for t in todo or ["Rien d'anormal."]) + "</ul>")
    # 6. veille
    if wt is not None:
        found, errs = wt
        label = {"metrology": "microscopie", "tenders": "appels d'offres"}
        rows = [[esc(it["date"]), esc(it["source"]), f"<a href='{esc(it['url'])}'>{esc(it['title'][:110])}</a>",
                 esc(label.get(it["topic"], it["topic"]))] for it in found]
        parts.append("<h3>6. Conversations où nos outils peuvent aider (7 jours)</h3>"
                     "<p class='s'>Lecture seule de sources publiques. Réponds toi-même, seulement si la réponse aide vraiment la personne ; "
                     "copie-moi le fil pour que je rédige la réponse.</p>"
                     + (table(["Date", "Source", "Sujet", "Domaine"], rows) if rows else "<p>Rien de pertinent cette semaine.</p>")
                     + (f"<p class='s'>Sources indisponibles : {esc(', '.join(errs))}.</p>" if errs else ""))
    body = (f"<div style='font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#16173a;max-width:760px;margin:0 auto'>"
            f"<p style='font-weight:700;font-size:16px;margin:0 0 4px'>Jovian Labs · rapport du lundi · {week}</p>"
            f"<p style='color:#55566e;margin:0 0 16px'>{today} · <a href='{SITE}'>{SITE.replace('https://', '')}</a></p>"
            + "".join(parts).replace("<h3>", "<h3 style='font-size:16px;margin:22px 0 8px'>").replace("<p class='s'>", "<p style='color:#55566e;font-size:13px'>")
            + "<p style='color:#8a8aa0;font-size:12px;margin-top:24px'>Envoyé automatiquement chaque lundi par le workflow report.yml.</p></div>")
    pro = po["count"]["pro"] if po else "?"
    subject = f"Rapport du lundi {week} · {pro} Pro · Apify {sign(tot_new_users)} utilisateur(s), {sign(tot_new_runs)} lancement(s)"
    return subject, body


def send(subject, body):
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        raise SystemExit("RESEND_API_KEY missing")
    payload = {"from": FROM, "to": [TO], "subject": subject, "html": body}
    req = urllib.request.Request("https://api.resend.com/emails", data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("id")


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--dry-run", action="store_true")
    a = ap_.parse_args()
    today = dt.date.today()
    week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    products = json.loads((ROOT / "tools" / "alerts" / "config.json").read_text())["products"]
    ap = apify()
    prev, prev_key = history_delta(ap, today.isoformat())
    po = polar(os.environ.get("POLAR_TOKEN"), products)
    si = site()
    ac = actions(os.environ.get("GITHUB_TOKEN"))
    try:
        from watch import watch
        wt = watch()
    except Exception as e:  # noqa: BLE001 — la veille ne doit jamais bloquer le rapport
        wt = ([], [f"veille: {type(e).__name__}"])
    subject, body = render(ap, prev, prev_key, po, si, ac, today.isoformat(), week, wt)
    if a.dry_run:
        (HERE / "preview.html").write_text(f"<!doctype html><meta charset='utf-8'><title>{esc(subject)}</title>{body}", encoding="utf-8")
        print(subject)
        return
    send(subject, body)
    # journal public : aucun chiffre Polar
    print("report sent;", len(ap), "actors;", si["pages"], "pages")


if __name__ == "__main__":
    main()
