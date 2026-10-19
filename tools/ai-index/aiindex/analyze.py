"""Extraction des entreprises recommandées, regroupement des variantes de noms, statistiques avec IC 95 %."""
import difflib
import math
import re
from collections import Counter, defaultdict
from urllib.parse import urlparse

DIRECTORIES = {"yelp", "angi", "angie's list", "angies list", "homeadvisor", "home advisor", "thumbtack", "google", "google maps",
               "bbb", "better business bureau", "nextdoor", "reddit", "zocdoc", "healthgrades", "yellow pages", "porch", "houzz",
               "facebook", "craigslist", "taskrabbit", "expertise.com", "expertise", "networx", "fixr", "bark"}
SUFFIXES = r"\b(llc|inc|co|corp|corporation|company|ltd|pllc|pc|dds|dmd|the)\b"

EXTRACT_PROMPT = """You will read an AI assistant's answer to the question: "{question}".
List every specific business (company or practice) that the answer names as an option for a {singular} in {city}, {state}.
Exclude directories and review sites (Yelp, Angi, Google, BBB, Thumbtack, Zocdoc, etc.), chains of tips, and generic advice.
Return only JSON: {{"businesses": ["Name 1", "Name 2", ...]}} in the order they appear. Return {{"businesses": []}} if none.

Answer:
\"\"\"{answer}\"\"\""""


def heuristic_names(text):
    """Repli sans LLM : noms en gras ou en tête d'éléments de liste."""
    names = re.findall(r"\*\*([^*]{3,80})\*\*", text)
    if not names:
        names = re.findall(r"^\s*(?:\d+[.)]|[-•])\s*([A-Z][\w&'’.\- ]{2,60}?)(?:\s[–—:-]|,|$)", text, re.M)
    out = []
    for n in names:
        n = n.strip(" :.-–—")
        if n and norm(n) not in DIRECTORIES and not norm(n).startswith(("tip", "note", "check", "how ", "why ")):
            out.append(n)
    return out


def norm(name):
    s = name.lower().replace("&", " and ").replace("’", "'")
    s = re.sub(r"[^\w' ]", " ", s)
    s = re.sub(SUFFIXES, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def cluster(names):
    """Regroupe les variantes d'un même nom ; renvoie {nom_normalisé: forme_affichée}."""
    counts = Counter(names)
    keys = []
    canon = {}
    for name, _ in counts.most_common():
        k = norm(name)
        if not k or k in DIRECTORIES:
            continue
        match = next((x for x in keys if x == k or difflib.SequenceMatcher(None, x, k).ratio() >= 0.88
                      or (len(k) > 6 and (k in x or x in k))), None)
        if match is None:
            keys.append(k)
            canon[name] = k
        else:
            canon[name] = match
    display = {}
    for name, n in counts.most_common():
        k = canon.get(name)
        if k and k not in display:
            display[k] = name
    return canon, display


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def domain(url):
    h = urlparse(url).netloc.lower()
    return h[4:] if h.startswith("www.") else h


def summarize(records, engines_labels):
    """records : [{"engine", "names": [...], "sources": [...]}] pour une catégorie × ville."""
    n = len(records)
    all_names = [nm for r in records for nm in r["names"]]
    canon, display = cluster(all_names)
    per_answer = [set(canon[nm] for nm in r["names"] if nm in canon) for r in records]
    mentions = Counter(k for s in per_answer for k in s)
    by_engine = defaultdict(lambda: [0, 0])
    eng_mentions = defaultdict(Counter)
    for r, s in zip(records, per_answer):
        by_engine[r["engine"]][1] += 1
        for k in s:
            eng_mentions[r["engine"]][k] += 1
    first = Counter(canon[r["names"][0]] for r in records if r["names"] and r["names"][0] in canon)
    rows = []
    for k, m in mentions.most_common():
        lo, hi = wilson(m, n)
        rows.append(dict(name=display.get(k, k), mentions=m, answers=n, rate=m / n, ci_low=lo, ci_high=hi,
                         first_rank=first.get(k, 0),
                         engines={e: (eng_mentions[e][k], by_engine[e][1]) for e in by_engine}))
    dom = Counter(d for r in records for d in {domain(u) for u in r["sources"]})
    no_name = sum(1 for s in per_answer if not s)
    top3 = {k for k, _ in mentions.most_common(3)}
    top3_share = sum(1 for s in per_answer if s & top3) / n if n else 0.0
    return dict(answers=n, rows=rows, engines={e: v[1] for e, v in by_engine.items()},
                engine_labels=engines_labels, top_domains=[(d, c, c / n) for d, c in dom.most_common(10)],
                answers_without_business=no_name, top3_share=top3_share, distinct_businesses=len(mentions))
