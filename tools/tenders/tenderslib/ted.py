"""EU TED (API v3, sans clé) : lots de marchés publics clôturés sans attributaire."""
import json
import time
import urllib.request

API = "https://api.ted.europa.eu/v3/notices/search"
UA = "jovianlabs-failed-tenders/1.0"
FIELDS = ["publication-number", "publication-date", "buyer-country", "buyer-name", "notice-title", "title-proc",
          "main-classification-proc", "BT-13713-LotResult", "BT-142-LotResult", "BT-144-LotResult",
          "BT-759-LotResult", "BT-760-LotResult", "procurement-relaunch", "identifier-lot", "title-lot",
          "main-classification-lot", "estimated-value-lot", "estimated-value-cur-lot",
          "estimated-value-proc", "estimated-value-cur-proc"]
REASONS = {
    "no-rece": "No tenders or requests to participate were received",
    "all-rej": "All tenders were rejected",
    "one-admis": "Only one admissible tender",
    "chan-need": "Change of need",
    "ins-fund": "Insufficient funds",
    "tch-pr-error": "Technical or procedural error",
    "no-signed": "Contract not signed",
    "other": "Other reason",
}


def _post(body, retries=5):
    data = json.dumps(body).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if attempt == retries - 1:
                raise RuntimeError(f"TED API error: {e}") from e
            time.sleep(3 * (attempt + 1))


def _lang_value(v, prefer=("eng", "fra")):
    """Valeur d'un champ multilingue {lang: str|list} : langue préférée sinon première."""
    if not isinstance(v, dict) or not v:
        return v
    for lang in prefer:
        if lang in v:
            return v[lang]
    return next(iter(v.values()))


def _first(v):
    if isinstance(v, list):
        return v[0] if v else None
    return v


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def build_query(since, reasons, countries=None, cpv_prefixes=None):
    q = f"publication-date>={since:%Y%m%d} AND BT-144-LotResult IN ({' '.join(reasons)})"
    if countries:
        q += f" AND buyer-country IN ({' '.join(countries)})"
    if cpv_prefixes:
        q += " AND (" + " OR ".join(f"classification-cpv={p}*" for p in cpv_prefixes) + ")"
    return q + " SORT BY publication-number DESC"


def lots_from_notice(n, keep_reasons=None):
    """Un élément par lot clôturé sans attributaire (BT-142 = clos-nw), avec motif aligné (BT-144)."""
    status = n.get("BT-142-LotResult") or []
    lot_refs = n.get("BT-13713-LotResult") or []
    reasons = n.get("BT-144-LotResult") or []
    relaunch = n.get("procurement-relaunch") or []
    closed_idx = [i for i, s in enumerate(status) if s == "clos-nw"]
    # nombre d'offres reçues : une statistique « tenders » par résultat de lot
    st_types, st_vals = n.get("BT-760-LotResult") or [], n.get("BT-759-LotResult") or []
    tenders = [_num(v) for t, v in zip(st_types, st_vals) if t == "tenders"]
    tenders = tenders if len(tenders) == len(status) else None
    ids = n.get("identifier-lot") or []
    titles = _lang_value(n.get("title-lot")) or []
    titles = titles if isinstance(titles, list) else [titles]
    cpvs = n.get("main-classification-lot") or []
    vals = n.get("estimated-value-lot") or []
    curs = n.get("estimated-value-cur-lot") or []
    lot_info = {}
    for i, lid in enumerate(ids):
        lot_info.setdefault(lid, dict(
            title=titles[i] if i < len(titles) and len(titles) == len(ids) else None,
            cpv=cpvs[i] if len(cpvs) == len(ids) else _first(n.get("main-classification-proc")),
            value=_num(vals[i]) if len(vals) == len(ids) else None,
            currency=(curs[i] if len(curs) == len(ids) else _first(curs)) if curs else None))
    pub = n.get("publication-number")
    notice_title = _lang_value(n.get("notice-title"))
    proc_title = _lang_value(n.get("title-proc"))
    buyer = _first(_lang_value(n.get("buyer-name")))
    out, seen = [], set()
    for k, i in enumerate(closed_idx):
        lid = lot_refs[i] if i < len(lot_refs) else None
        if lid in seen:          # plusieurs résultats pour un même lot : un seul élément
            continue
        seen.add(lid)
        reason = reasons[k] if len(reasons) == len(closed_idx) else (reasons[0] if len(set(reasons)) == 1 else None)
        if keep_reasons and reason not in keep_reasons:
            continue
        info = lot_info.get(lid, {})
        out.append(dict(
            source="TED",
            country=_first(n.get("buyer-country")),
            buyer=buyer,
            noticeId=pub,
            published=(n.get("publication-date") or "")[:10],
            noticeTitle=notice_title,
            procedureTitle=proc_title,
            lotId=lid,
            lotTitle=info.get("title"),
            cpv=info.get("cpv") or _first(n.get("main-classification-proc")),
            estimatedValue=info.get("value") if info.get("value") else None,
            currency=info.get("currency") if info.get("value") else None,
            reasonCode=reason,
            reason=REASONS.get(reason, reason),
            tendersReceived=tenders[i] if tenders else None,
            relaunchPlanned=(relaunch[k] if len(relaunch) == len(closed_idx) else None),
            url=f"https://ted.europa.eu/en/notice/-/detail/{pub}",
        ))
    return out


def failed_lots(since, reasons, countries=None, cpv_prefixes=None, page_size=100, log=None):
    """Générateur de lots non attribués, du plus récent au plus ancien."""
    body = {"query": build_query(since, reasons, countries, cpv_prefixes), "fields": FIELDS,
            "limit": page_size, "paginationMode": "ITERATION"}
    while True:
        d = _post(body)
        if log and "totalNoticeCount" in d and "iterationNextToken" not in body:
            log(f"TED: {d['totalNoticeCount']} notices match")
        for n in d.get("notices", []):
            yield from lots_from_notice(n, set(reasons))
        tok = d.get("iterationNextToken")
        if not tok or not d.get("notices"):
            return
        body["iterationNextToken"] = tok
        time.sleep(0.3)


# --------------------------------------------------------------------------- relances (toute l'UE)
import re as _re

_OPEN_FIELDS = ["publication-number", "publication-date", "buyer-country", "buyer-name", "buyer-identifier",
                "notice-title", "title-proc", "classification-cpv", "main-classification-proc",
                "deadline-receipt-tender-date-lot", "estimated-value-proc", "estimated-value-cur-proc"]
_FAILED_FIELDS = ["publication-number", "publication-date", "buyer-identifier", "classification-cpv",
                  "title-proc", "notice-title"]


def _title_text(n):
    t = _lang_value(n.get("title-proc"), prefer=()) or _lang_value(n.get("notice-title"), prefer=())
    t = " ".join(t) if isinstance(t, list) else (t or "")
    return _re.sub(r"^[^–]+–[^–]+– ", "", t)


def _tokens(text):
    return {w for w in _re.findall(r"\w{4,}", text.lower()) if not w.isdigit()}


def _iterate(query, fields, page_size=250):
    body = {"query": query, "fields": fields, "limit": page_size, "paginationMode": "ITERATION"}
    while True:
        d = _post(body)
        yield from d.get("notices", [])
        tok = d.get("iterationNextToken")
        if not tok or not d.get("notices"):
            return
        body["iterationNextToken"] = tok
        time.sleep(0.3)


def _filters(countries, cpv_prefixes):
    q = ""
    if countries:
        q += f" AND buyer-country IN ({' '.join(countries)})"
    if cpv_prefixes:
        q += " AND (" + " OR ".join(f"classification-cpv={p}*" for p in cpv_prefixes) + ")"
    return q


def relaunched_calls(today, countries=None, cpv_prefixes=None, failed_lookback_days=365, open_published_days=180,
                     min_similarity=0.5, log=None):
    """Appels ouverts (date limite >= aujourd'hui) qui relancent un marché raté du même acheteur.

    Appariement : même identifiant d'acheteur, au moins un code CPV identique, échec publié avant l'appel,
    et titres proches (indice de Jaccard sur les mots >= min_similarity).
    """
    import datetime as _dt
    since_fail = today - _dt.timedelta(days=failed_lookback_days)
    since_open = today - _dt.timedelta(days=open_published_days)
    flt = _filters(countries, cpv_prefixes)
    index = {}
    n_failed = 0
    for f in _iterate(f"publication-date>={since_fail:%Y%m%d} AND BT-144-LotResult IN (no-rece all-rej){flt}", _FAILED_FIELDS):
        n_failed += 1
        entry = (f["publication-date"][:10], f["publication-number"], _tokens(_title_text(f)))
        for b in f.get("buyer-identifier") or []:
            for c in set(f.get("classification-cpv") or []):
                index.setdefault((b, c), []).append(entry)
    if log:
        log(f"TED: {n_failed} failed procedures indexed for relaunch matching")
    q = (f"notice-type IN (cn-standard cn-social) AND deadline-receipt-tender-date-lot>={today:%Y%m%d} "
         f"AND publication-date>={since_open:%Y%m%d}{flt} SORT BY publication-number DESC")
    for n in _iterate(q, _OPEN_FIELDS):
        pub = n["publication-date"][:10]
        tk = _tokens(_title_text(n))
        best = None
        for b in n.get("buyer-identifier") or []:
            for c in set(n.get("classification-cpv") or []):
                for (fdate, fpub, ftk) in index.get((b, c), []):
                    if fdate > pub or fpub == n["publication-number"]:
                        continue
                    j = len(tk & ftk) / max(1, len(tk | ftk))
                    if j >= min_similarity and (best is None or j > best[0]):
                        best = (j, fpub, fdate)
        if not best:
            continue
        deadlines = sorted(d[:10] for d in (n.get("deadline-receipt-tender-date-lot") or []) if d[:10] >= f"{today:%Y-%m-%d}")
        pubnum = n["publication-number"]
        val = _num(_first(n.get("estimated-value-proc")))
        yield dict(
            source="TED",
            country=_first(n.get("buyer-country")),
            buyer=_first(_lang_value(n.get("buyer-name"))),
            noticeId=pubnum,
            published=pub,
            deadline=deadlines[0] if deadlines else None,
            noticeTitle=_lang_value(n.get("notice-title")),
            procedureTitle=_lang_value(n.get("title-proc")),
            lotId=None,
            lotTitle=None,
            cpv=_first(n.get("main-classification-proc")),
            estimatedValue=val if val else None,
            currency=_first(n.get("estimated-value-cur-proc")) if val else None,
            reasonCode="relaunch",
            reason="Open call that relaunches an earlier procedure of the same buyer that failed",
            relaunchConfidence="high" if best[0] >= 0.7 else "medium",
            previousNoticeId=best[1],
            previousPublished=best[2],
            tendersReceived=None,
            relaunchPlanned=None,
            url=f"https://ted.europa.eu/en/notice/-/detail/{pubnum}",
        )
