"""BOAMP (France, open data DILA via Opendatasoft) : appels d'offres ouverts qui relancent une procédure
infructueuse ou déclarée sans suite."""
import datetime as dt
import json
import time
import urllib.parse
import urllib.request

from .eforms import find_all, text

API = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
UA = "jovianlabs-failed-tenders/1.0"
TERMS = ['search("infructueux")', 'search("infructueuse")', 'search("infructuosité")', 'search("infructueuses")']


def _get(params, retries=5):
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if attempt == retries - 1:
                raise RuntimeError(f"BOAMP API error: {e}") from e
            time.sleep(3 * (attempt + 1))


def _cpv(donnees):
    try:
        d = json.loads(donnees) if isinstance(donnees, str) else (donnees or {})
    except ValueError:
        return None
    if "EFORMS" in d:
        for node in find_all(d, "cac:MainCommodityClassification"):
            for x in node if isinstance(node, list) else [node]:
                c = text(x.get("cbc:ItemClassificationCode")) if isinstance(x, dict) else None
                if c:
                    return c
        return None
    c = find_all(d, "classPrincipale")
    return text(c[0]) if c else None


def relaunched_calls(today=None, cpv_prefixes=None, page_size=100, log=None):
    """Appels d'offres encore ouverts (date limite >= aujourd'hui) qui relancent une procédure ratée."""
    today = today or dt.date.today()
    where = (f'nature="APPEL_OFFRE" and datelimitereponse>="{today:%Y-%m-%d}" and (' + " or ".join(TERMS) + ")")
    offset = 0
    while True:
        d = _get({"where": where, "limit": page_size, "offset": offset, "order_by": "dateparution desc"})
        if log and offset == 0:
            log(f"BOAMP: {d.get('total_count')} open relaunch calls")
        res = d.get("results") or []
        for r in res:
            cpv = _cpv(r.get("donnees"))
            if cpv_prefixes and not (cpv and any(cpv.startswith(p) for p in cpv_prefixes)):
                continue
            title = (r.get("objet") or "").replace("\n", " ").strip()
            yield dict(
                source="BOAMP",
                country="FRA",
                buyer=r.get("nomacheteur"),
                noticeId=r.get("idweb"),
                published=r.get("dateparution"),
                deadline=(r.get("datelimitereponse") or "")[:10] or None,
                noticeTitle=title,
                procedureTitle=title,
                lotId=None,
                lotTitle=None,
                cpv=cpv,
                estimatedValue=None,
                currency=None,
                reasonCode="relaunch",
                reason="Open call relaunching a procedure declared unsuccessful (no suitable tenders)",
                relaunchInTitle=any(w in title.lower() for w in ("infructu", "relance")),
                tendersReceived=None,
                relaunchPlanned=None,
                department=(r.get("code_departement") or [None])[0],
                contractType=(r.get("type_marche") or [None])[0],
                url=r.get("url_avis"),
            )
        offset += len(res)
        if not res or offset >= (d.get("total_count") or 0) or offset >= 9900:
            return
        time.sleep(0.2)
