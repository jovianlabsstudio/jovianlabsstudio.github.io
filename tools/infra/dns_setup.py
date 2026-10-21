"""Configuration DNS de jovianlabsstudio.com chez Cloudflare (lancée par .github/workflows/infra.yml).

--pages   : enregistrements GitHub Pages (A et AAAA à la racine, CNAME www) en « DNS only », pour que GitHub délivre le certificat.
--resend  : ajoute le domaine dans Resend (région UE), recopie ses enregistrements (SPF, DKIM, MX de retour) chez Cloudflare,
            ajoute un DMARC de surveillance, puis demande la vérification.
--txt VAL : ajoute un TXT à la racine (vérification Google Search Console, par exemple).
Secrets lus dans l'environnement : CLOUDFLARE_API_TOKEN (obligatoire), RESEND_API_KEY (pour --resend). Rien n'est affiché.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request

DOMAIN = "jovianlabsstudio.com"
GH_A = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
GH_AAAA = ["2606:50c0:8000::153", "2606:50c0:8001::153", "2606:50c0:8002::153", "2606:50c0:8003::153"]
UA = "jovianlabs-infra/1.0"


def call(method, url, token, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {url.split('?')[0]} -> HTTP {e.code}: {e.read()[:400]!r}")


def cf(method, path, body=None):
    return call(method, "https://api.cloudflare.com/client/v4" + path, os.environ["CLOUDFLARE_API_TOKEN"], body)


def zone_id():
    zid = os.environ.get("CF_ZONE_ID")
    if zid:
        return zid
    res = cf("GET", f"/zones?name={DOMAIN}")["result"]
    if not res:
        raise SystemExit("zone not visible with this token: add CF_ZONE_ID")
    return res[0]["id"]


def ensure(zid, rtype, name, content, priority=None):
    fqdn = DOMAIN if name in ("@", "", DOMAIN) else (name if name.endswith(DOMAIN) else f"{name}.{DOMAIN}")
    existing = cf("GET", f"/zones/{zid}/dns_records?type={rtype}&name={fqdn}")["result"]
    norm = lambda s: str(s).strip('"').rstrip(".").lower()
    if any(norm(r["content"]) == norm(content) for r in existing):
        print(f"ok      {rtype:5s} {fqdn}")
        return
    body = {"type": rtype, "name": fqdn, "content": content, "ttl": 1, "proxied": False}
    if priority is not None:
        body["priority"] = int(priority)
    if rtype in ("TXT", "MX"):
        body.pop("proxied")
    cf("POST", f"/zones/{zid}/dns_records", body)
    print(f"created {rtype:5s} {fqdn}")


def setup_pages(zid):
    for ip in GH_A:
        ensure(zid, "A", "@", ip)
    for ip in GH_AAAA:
        ensure(zid, "AAAA", "@", ip)
    ensure(zid, "CNAME", "www", "jovianlabsstudio.github.io")


def setup_resend(zid):
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        raise SystemExit("RESEND_API_KEY missing")
    rs = lambda m, p, b=None: call(m, "https://api.resend.com" + p, key, b)
    doms = rs("GET", "/domains").get("data", [])
    dom = next((d for d in doms if d.get("name") == DOMAIN), None)
    if dom is None:
        dom = rs("POST", "/domains", {"name": DOMAIN, "region": "eu-west-1"})
        print("Resend: domain added")
    dom = rs("GET", f"/domains/{dom['id']}")
    for rec in dom.get("records", []):
        ensure(zid, rec["type"], rec["name"], rec["value"], rec.get("priority"))
    ensure(zid, "TXT", "_dmarc", "v=DMARC1; p=none")
    time.sleep(5)
    rs("POST", f"/domains/{dom['id']}/verify")
    print("Resend: verification requested (status:", rs("GET", f"/domains/{dom['id']}").get("status"), ")")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", action="store_true")
    ap.add_argument("--resend", action="store_true")
    ap.add_argument("--txt", default="")
    a = ap.parse_args()
    zid = zone_id()
    if a.pages:
        setup_pages(zid)
    if a.resend:
        setup_resend(zid)
    if a.txt:
        ensure(zid, "TXT", "@", a.txt)


if __name__ == "__main__":
    main()
