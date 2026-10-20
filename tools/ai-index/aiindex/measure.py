"""Mesure hebdomadaire : interroge les moteurs, extrait les entreprises citées, enregistre data/AAAA-Wss.json."""
import datetime as dt
import json
import sys
from pathlib import Path

from . import engines as E
from .analyze import EXTRACT_PROMPT, heuristic_names

ROOT = Path(__file__).resolve().parents[1]


def week_id(d=None):
    y, w, _ = (d or dt.date.today()).isocalendar()
    return f"{y}-W{w:02d}"


def run(config, mock=False, out_dir=None, only=None):
    eng = E.make(config["engines"], mock=mock, skip_missing=True)
    if not eng:
        raise SystemExit("No engine available: set GEMINI_API_KEY and/or PERPLEXITY_API_KEY.")
    extractor = next((e for e in eng if hasattr(e, "complete_json")), None)
    budget = config.get("max_calls_per_run", 700)
    calls, records, errors = 0, [], []
    for cat in config["categories"]:
        for city in config["cities"]:
            if only and f"{cat['slug']}/{city['slug']}" not in only:
                continue
            for tpl in config["prompts"]:
                q = tpl.format(singular=cat["singular"], plural=cat["plural"], city=city["name"], state=city["state"])
                for s in range(config.get("samples_per_prompt", 2)):
                    for e in eng:
                        if calls >= budget:
                            errors.append("budget reached")
                            break
                        try:
                            ans = e.ask(q)
                            calls += 1
                        except E.EngineError as ex:
                            errors.append(f"{e.name}: {ex}")
                            continue
                        names = None
                        if extractor is not None and calls < budget:
                            try:
                                js = extractor.complete_json(EXTRACT_PROMPT.format(
                                    question=q, singular=cat["singular"], city=city["name"], state=city["state"],
                                    answer=ans["text"][:6000]))
                                calls += 1
                                names = [str(x) for x in js.get("businesses", []) if str(x).strip()]
                            except Exception as ex:  # noqa: BLE001
                                errors.append(f"extract: {ex}")
                        if names is None:
                            names = heuristic_names(ans["text"])
                        records.append(dict(category=cat["slug"], city=city["slug"], prompt=q, sample=s,
                                            engine=ans["engine"], names=names[:15], sources=ans["sources"][:15]))
    if not records:
        raise SystemExit("No AI answer collected (" + "; ".join(errors[:5]) + "): nothing written.")
    wid = week_id()
    out = Path(out_dir or ROOT / "data")
    out.mkdir(parents=True, exist_ok=True)
    payload = dict(week=wid, date=dt.date.today().isoformat(), mock=mock, calls=calls,
                   engines={e.name: getattr(e, "label", e.name) for e in eng}, records=records, errors=errors[:50])
    path = out / f"{wid}{'-mock' if mock else ''}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    print(f"{len(records)} answers, {calls} calls, {len(errors)} errors -> {path}", file=sys.stderr)
    return path
