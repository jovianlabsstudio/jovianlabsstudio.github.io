"""Crée chez Polar les champs, les produits et les liens de paiement des alertes « seconde chance », puis met à jour
tools/alerts/config.json (identifiants de produits, liens de paiement, portail client). Idempotent : rien n'est créé en double.

Lancé par .github/workflows/polar-setup.yml avec le secret POLAR_TOKEN (jeton d'organisation Polar, saisi par le propriétaire).
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "tenders"))
from build import COUNTRIES, SECTORS  # noqa: E402

API = "https://api.polar.sh/v1"
TOKEN = os.environ["POLAR_TOKEN"]
SITE = "https://jovianlabsstudio.com"
CFG_PATH = ROOT / "tools" / "alerts" / "config.json"


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
                                          "Accept": "application/json", "User-Agent": "jovianlabs-infra/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path.split('?')[0]} -> HTTP {e.code}: {e.read()[:600]!r}")


FIELDS = [
    dict(type="select", slug="country", name="Country", properties=dict(
        form_label="Country / Pays", form_help_text="Country of the public buyers to watch.",
        options=[{"value": c, "label": n} for c, (n, _) in COUNTRIES.items()])),
    dict(type="select", slug="sector", name="Sector", properties=dict(
        form_label="Sector / Secteur", form_help_text="Pick one sector, or all sectors.",
        options=[{"value": "all", "label": "All sectors / Tous secteurs"}] +
                [{"value": s[0], "label": f"{s[2]} / {s[1]}"} for s in SECTORS])),
    dict(type="text", slug="keywords", name="Keywords", properties=dict(
        form_label="Keywords (optional) / Mots-clés (facultatif)",
        form_help_text="Comma-separated words that must appear in the title or buyer, e.g. cleaning, software. Leave empty for everything.",
        max_length=200)),
    dict(type="select", slug="language", name="Language", properties=dict(
        form_label="Email language / Langue des e-mails",
        options=[{"value": "en", "label": "English"}, {"value": "fr", "label": "Français"}, {"value": "de", "label": "Deutsch"},
                 {"value": "es", "label": "Español"}, {"value": "it", "label": "Italiano"}])),
]
REQUIRED = {"country": True, "sector": True, "keywords": False, "language": True}

PRODUCTS = {
    "free": dict(name="Second-chance tender alerts · Free", amount=0, description=(
        "Every Monday, the 5 most urgent open calls that relaunch a failed public procurement procedure in your country and sector. "
        "Chaque lundi, les 5 appels d'offres relancés les plus urgents dans votre pays et votre secteur.")),
    "pro": dict(name="Second-chance tender alerts · Pro", amount=1900, description=(
        "Every Monday: all new open calls that relaunch a failed procedure, all procedures that failed this week (no tenders or all "
        "rejected), deadlines within 14 days and a CSV file, filtered by country, sector and keywords. Cancel anytime. "
        "Chaque lundi : tous les appels relancés, les procédures infructueuses de la semaine, les échéances à 14 jours et un CSV.")),
}

# Prix dans la devise par défaut de l'organisation quand ce n'est pas l'euro (Polar l'exige) : 19 € ≈ 22 $.
OTHER_CURRENCY = {"usd": {"free": 0, "pro": 2200}}


def main():
    orgs = call("GET", "/organizations/?limit=10").get("items", [])
    slug = orgs[0]["slug"] if orgs else "jovianlabs"
    default_cur = ((orgs[0].get("default_presentment_currency") if orgs else None) or "usd").lower()
    print("organization:", slug, "| default currency:", default_cur)
    if default_cur != "eur" and default_cur not in OTHER_CURRENCY:
        raise SystemExit(f"Default currency {default_cur}: set it to EUR or USD in Polar (Settings) and run again.")
    existing = {f["slug"]: f for f in call("GET", "/custom-fields/?limit=100").get("items", [])}
    ids = {}
    for f in FIELDS:
        if f["slug"] in existing:
            cur = existing[f["slug"]]
            ids[f["slug"]] = cur["id"]
            want = f["properties"].get("options")
            have = (cur.get("properties") or {}).get("options")
            if want and [o["value"] for o in want] != [o.get("value") for o in (have or [])]:
                call("PATCH", f"/custom-fields/{cur['id']}", dict(type=f["type"], properties=f["properties"]))
                print("field updated", f["slug"])
            else:
                print("field ok     ", f["slug"])
        else:
            ids[f["slug"]] = call("POST", "/custom-fields/", f)["id"]
            print("field created", f["slug"])
    prods = {p["name"]: p for p in call("GET", "/products/?limit=100&is_archived=false").get("items", [])}
    cfg = json.loads(CFG_PATH.read_text())
    for plan, spec in PRODUCTS.items():
        p = prods.get(spec["name"])
        if p is None:
            p = call("POST", "/products/", dict(
                name=spec["name"], description=spec["description"], recurring_interval="month",
                prices=[dict(amount_type="fixed", price_amount=spec["amount"], price_currency="eur")] + (
                    [] if default_cur == "eur" else
                    [dict(amount_type="fixed", price_amount=OTHER_CURRENCY[default_cur][plan], price_currency=default_cur)]),
                attached_custom_fields=[dict(custom_field_id=ids[s], required=REQUIRED[s]) for s in ("country", "sector", "keywords", "language")],
                metadata=dict(plan=plan)))
            print("product created", plan)
        else:
            print("product ok     ", plan)
        cfg["products"][plan] = p["id"]
        links = [l for l in call("GET", f"/checkout-links/?limit=100&product_id={p['id']}").get("items", []) if l.get("label") == f"alerts-{plan}"]
        link = links[0] if links else call("POST", "/checkout-links/", dict(
            payment_processor="stripe", products=[p["id"]], label=f"alerts-{plan}", allow_discount_codes=True,
            success_url=f"{SITE}/alerts/thanks/?checkout_id={{CHECKOUT_ID}}", metadata=dict(plan=plan)))
        cfg["checkout_links"][plan] = link["url"]
        print("checkout link", plan, "ok")
    cfg["portal_url"] = f"https://polar.sh/{slug}/portal"
    CFG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    print("config updated; organization:", slug)


if __name__ == "__main__":
    main()
