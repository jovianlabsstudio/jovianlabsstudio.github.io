"""Extraction des lots non attribués dans un avis eForms (JSON issu du XML, format BOAMP « donnees »).

Fonctions pures, réutilisables dans l'Actor.
"""
import json

NO_AWARD_REASONS = {
    "no-rece": "aucune offre reçue",
    "all-rej": "toutes les offres rejetées",
    "chan-need": "changement de besoin",
    "ins-fun": "financement insuffisant",
    "oth-int": "autre raison d'intérêt général",
    "pro-err": "erreur de procédure",
    "un-cha": "conditions inchangées non applicables",
}
REASONS_EN = {
    "no-rece": "no tenders received",
    "all-rej": "all tenders rejected",
    "chan-need": "change of need",
    "ins-fun": "insufficient funds",
    "oth-int": "other public-interest reason",
    "pro-err": "procedure error",
}
OPPORTUNITY = {"no-rece", "all-rej"}   # besoins restés sans fournisseur


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def text(x):
    """Texte d'un nœud ({'#text': ...}, chaîne, ou liste de nœuds multilingues : on prend le premier)."""
    if x is None:
        return None
    if isinstance(x, list):
        x = x[0] if x else None
    if isinstance(x, dict):
        return x.get("#text")
    return str(x)


def find_all(obj, key, out=None):
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                out.append(v)
            find_all(v, key, out)
    elif isinstance(obj, list):
        for v in obj:
            find_all(v, key, out)
    return out


def num(x):
    try:
        return float(text(x))
    except (TypeError, ValueError):
        return None


def parse(donnees):
    """Retourne (infos_procédure, lots_non_attribués) à partir du champ `donnees` (str ou dict)."""
    d = json.loads(donnees) if isinstance(donnees, str) else donnees
    if "EFORMS" not in d:
        return None, []
    root = d["EFORMS"]
    lots = {}
    for lot in find_all(root, "cac:ProcurementProjectLot"):
        for L in as_list(lot):
            lid = text(L.get("cbc:ID"))
            pp = L.get("cac:ProcurementProject") or {}
            cpv = text((pp.get("cac:MainCommodityClassification") or {}).get("cbc:ItemClassificationCode"))
            val = num((pp.get("cac:RequestedTenderTotal") or {}).get("cbc:EstimatedOverallContractAmount"))
            cur = ((pp.get("cac:RequestedTenderTotal") or {}).get("cbc:EstimatedOverallContractAmount") or {})
            lots[lid] = dict(lot_id=lid, titre=text(pp.get("cbc:Name")), description=text(pp.get("cbc:Description")),
                             cpv=cpv, valeur_estimee=val if val else None,
                             devise=cur.get("@currencyID") if isinstance(cur, dict) else None,
                             nature=text(pp.get("cbc:ProcurementTypeCode")))
    proj = find_all(root, "cac:ProcurementProject")
    top = next((p for p in proj if isinstance(p, dict) and p.get("cbc:Name")), {}) if proj else {}
    proc = dict(titre=text(top.get("cbc:Name")), description=text(top.get("cbc:Description")),
                cpv=text((top.get("cac:MainCommodityClassification") or {}).get("cbc:ItemClassificationCode")),
                valeur_estimee=num((top.get("cac:RequestedTenderTotal") or {}).get("cbc:EstimatedOverallContractAmount")))
    out = []
    for res in find_all(root, "efac:LotResult"):
        for R in as_list(res):
            status = text(R.get("cbc:TenderResultCode"))
            reason = text((R.get("efac:DecisionReason") or {}).get("efbc:DecisionReasonCode")) if isinstance(R.get("efac:DecisionReason"), dict) else None
            if status != "clos-nw" and not reason:
                continue
            lid = text((R.get("efac:TenderLot") or {}).get("cbc:ID"))
            n_tenders = None
            for st in as_list(R.get("efac:ReceivedSubmissionsStatistics")):
                if text(st.get("efbc:StatisticsCode")) == "tenders":
                    n_tenders = num(st.get("efbc:StatisticsNumeric"))
            item = dict(lots.get(lid) or {"lot_id": lid})
            item.update(statut=status, motif=reason, offres_recues=n_tenders)
            out.append(item)
    return proc, out
