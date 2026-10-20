"""Adaptateurs des moteurs d'IA (réponses avec recherche web) et moteur simulé pour les tests.

Chaque moteur renvoie {"engine", "text", "sources": [url, ...]}.
Les formats des API évoluent : les fonctions de lecture cherchent le texte et les URL de façon tolérante.
"""
import json
import os
import sys
import random
import re
import time
import urllib.error
import urllib.request

UA = "jovianlabs-ai-index/1.0"


class EngineError(RuntimeError):
    pass


class QuotaError(EngineError):
    """Quota épuisé ou absent (HTTP 429 « exceeded your current quota ») : inutile de réessayer."""


def _error_summary(code, raw):
    """Résumé lisible d'une erreur d'API : message et, pour Google, les quotas en cause (quotaId)."""
    try:
        err = json.loads(raw).get("error", {})
    except Exception:  # noqa: BLE001
        return f"HTTP {code}: {raw[:300]!r}"
    msg = str(err.get("message", ""))[:200]
    quotas = sorted({str(v.get("quotaId") or v.get("quotaMetric")) for d in err.get("details", []) or []
                     for v in d.get("violations", []) or [] if isinstance(v, dict)} - {"None"})
    return f"HTTP {code}: {msg}" + (f" [quota: {', '.join(quotas)}]" if quotas else "")


def _post(url, body, headers, retries=4, timeout=120):
    data = json.dumps(body).encode()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": UA, **headers})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raw = e.read()[:6000].decode("utf-8", "replace")
            last = _error_summary(e.code, raw)
            if e.code == 429 and ("exceeded your current quota" in raw.lower() or "limit: 0" in raw.lower()):
                raise QuotaError(f"{url}: {last}") from None
            if e.code in (400, 401, 403, 404):
                break
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(4 * (attempt + 1))
    raise EngineError(f"{url}: {last}")


def _walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _urls(resp):
    out = []
    for k, v in _walk(resp):
        if k in ("url", "uri") and isinstance(v, str) and v.startswith("http"):
            out.append(v)
        elif k == "citations" and isinstance(v, list):
            out += [x for x in v if isinstance(x, str) and x.startswith("http")]
    seen, res = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            res.append(u)
    return res


class Gemini:
    """Gemini avec « Grounding with Google Search » (API Interactions, repli sur generateContent)."""
    name = "gemini"
    label = "Google Gemini (with Google Search)"

    def __init__(self, model=None):
        self.key = os.environ.get("GEMINI_API_KEY")
        if not self.key:
            raise EngineError("GEMINI_API_KEY missing")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

    def ask(self, prompt):
        h = {"x-goog-api-key": self.key}
        try:
            r = _post("https://generativelanguage.googleapis.com/v1beta/interactions",
                      {"model": self.model, "input": prompt, "tools": [{"type": "google_search"}]}, h)
            text = r.get("output_text") or "\n".join(
                c.get("text", "") for s in r.get("steps", []) if s.get("type") == "model_output"
                for c in s.get("content", []) if isinstance(c, dict))
        except EngineError:
            r = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                      {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}]}, h)
            parts = (((r.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
            text = "\n".join(p.get("text", "") for p in parts)
        if not text.strip():
            raise EngineError("Gemini: empty answer")
        return {"engine": self.name, "text": text, "sources": _urls(r)}

    def complete_json(self, prompt):
        """Appel sans recherche, réponse JSON (pour l'extraction des noms)."""
        h = {"x-goog-api-key": self.key}
        model = os.environ.get("GEMINI_EXTRACT_MODEL", self.model)
        try:
            r = _post("https://generativelanguage.googleapis.com/v1beta/interactions", {"model": model, "input": prompt}, h)
            text = r.get("output_text") or json.dumps(r)
        except EngineError:
            r = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                      {"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"responseMimeType": "application/json"}}, h)
            parts = (((r.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
            text = "\n".join(p.get("text", "") for p in parts)
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}


class Perplexity:
    """Perplexity Sonar (réponse avec recherche web et sources)."""
    name = "perplexity"
    label = "Perplexity (Sonar)"

    def __init__(self, model=None):
        self.key = os.environ.get("PERPLEXITY_API_KEY")
        if not self.key:
            raise EngineError("PERPLEXITY_API_KEY missing")
        self.model = model or os.environ.get("PERPLEXITY_MODEL", "sonar")

    def ask(self, prompt):
        h = {"Authorization": f"Bearer {self.key}"}
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        last = None
        for url in ("https://api.perplexity.ai/v1/sonar", "https://api.perplexity.ai/chat/completions"):
            try:
                r = _post(url, body, h)
                text = ((r.get("choices") or [{}])[0].get("message") or {}).get("content") or r.get("output_text") or ""
                if text.strip():
                    return {"engine": self.name, "text": text, "sources": _urls(r)}
            except EngineError as e:
                last = e
        raise EngineError(f"Perplexity: {last}")


class Mock:
    """Moteur simulé déterministe : réponses réalistes pour tester tout le circuit sans API."""
    name = "mock"
    label = "Simulated engine (test)"

    POOL = ["{c} Rooter & Drain", "Blue Wrench {c}", "Mr. Fixit {c}", "ABC Home Services", "Lone Star Pros", "Rapid Response {c}",
            "{c} Family Services", "Precision Experts", "Summit Pro {c}", "Neighborly Care Co."]
    DOMAINS = ["yelp.com", "angi.com", "bbb.org", "google.com/maps", "thumbtack.com", "reddit.com", "nextdoor.com", "homeadvisor.com"]

    def __init__(self, seed=7, label_suffix=""):
        self.seed = seed
        self.name = f"mock{label_suffix}"

    def ask(self, prompt):
        rnd = random.Random(f"{self.seed}|{prompt}|{random.random()}")
        city = re.search(r"in ([A-Z][\w .]+),", prompt)
        c = city.group(1).split()[0] if city else "City"
        weights = [0.9, 0.7, 0.55, 0.4, 0.3, 0.25, 0.2, 0.12, 0.08, 0.05]
        names = [n.format(c=c) for n, w in zip(self.POOL, weights) if rnd.random() < w][:5]
        lines = ["Here are some well-reviewed options:"] + [f"{i + 1}. **{n}** – known for fast service and good reviews." for i, n in enumerate(names)]
        lines.append("Always check licenses and recent reviews before hiring.")
        srcs = [f"https://www.{d}/x{rnd.randint(1, 99)}" for d in rnd.sample(self.DOMAINS, 3)]
        return {"engine": self.name, "text": "\n".join(lines), "sources": srcs}


def make(names, mock=False, skip_missing=False):
    """Instancie les moteurs. Avec skip_missing, un moteur sans clé d'API est ignoré (on démarre avec les clés disponibles)."""
    if mock:
        return [Mock(seed=i, label_suffix=f"-{n}") for i, n in enumerate(names)]
    out = []
    for n in names:
        cls = {"gemini": Gemini, "perplexity": Perplexity}[n]
        try:
            out.append(cls())
        except EngineError as ex:
            if not skip_missing:
                raise
            print(f"engine {n} skipped: {ex}", file=sys.stderr)
    return out
